"""Tests for PSID download functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from psid.download import (
    PSIDDownloader,
    download_psid,
    get_file_number,
    PSID_FILE_NUMBERS,
    PSID_LOGIN_URL,
)


class TestFileNumbers:
    """Test file number lookups."""

    def test_family_file_numbers_exist(self):
        """Test that family file numbers are defined for common years."""
        assert 2021 in PSID_FILE_NUMBERS["family"]
        assert 2019 in PSID_FILE_NUMBERS["family"]
        assert 1968 in PSID_FILE_NUMBERS["family"]

    def test_individual_file_numbers_exist(self):
        """Test that individual file numbers are defined."""
        assert 2021 in PSID_FILE_NUMBERS["individual"]

    def test_wealth_file_numbers_exist(self):
        """Test that wealth file numbers are defined."""
        assert 2021 in PSID_FILE_NUMBERS["wealth"]
        assert 2019 in PSID_FILE_NUMBERS["wealth"]

    def test_get_file_number_family(self):
        """Test getting family file number."""
        num = get_file_number("family", 2021)
        assert num == 1277

    def test_get_file_number_invalid_year(self):
        """Test error for invalid year."""
        with pytest.raises(ValueError, match="not available"):
            get_file_number("family", 1950)

    def test_get_file_number_invalid_type(self):
        """Test error for invalid file type."""
        with pytest.raises(ValueError, match="Unknown file type"):
            get_file_number("invalid", 2021)


class TestPSIDDownloader:
    """Test PSIDDownloader class."""

    def test_init_with_credentials(self):
        """Test initialization with provided credentials."""
        downloader = PSIDDownloader(username="user", password="pass")
        assert downloader.username == "user"
        assert downloader.password == "pass"
        assert not downloader._logged_in

    def test_init_without_credentials(self):
        """Test initialization without credentials."""
        downloader = PSIDDownloader()
        assert downloader.username is None
        assert downloader.password is None

    def test_extract_field(self):
        """Test extracting hidden form field from HTML."""
        downloader = PSIDDownloader()
        html = '<input type="hidden" id="__VIEWSTATE" value="abc123" />'
        assert downloader._extract_field(html, "__VIEWSTATE") == "abc123"

    def test_extract_field_not_found(self):
        """Test extracting non-existent field returns None."""
        downloader = PSIDDownloader()
        html = '<input type="hidden" id="other" value="xyz" />'
        assert downloader._extract_field(html, "__VIEWSTATE") is None

    @patch("psid.download.requests.Session")
    def test_login_success(self, mock_session_class):
        """Test successful login."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock GET response (login page)
        mock_get_response = Mock()
        mock_get_response.text = '''
            <input id="__VIEWSTATE" value="viewstate123" />
            <input id="__VIEWSTATEGENERATOR" value="gen123" />
            <input id="__EVENTVALIDATION" value="valid123" />
        '''
        mock_get_response.raise_for_status = Mock()

        # Mock POST response (after login)
        mock_post_response = Mock()
        mock_post_response.text = "Welcome to PSID. Logout"
        mock_post_response.raise_for_status = Mock()

        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response

        downloader = PSIDDownloader(username="user", password="pass")
        result = downloader.login()

        assert result is True
        assert downloader._logged_in is True
        mock_session.post.assert_called_once()

    @patch("psid.download.requests.Session")
    def test_login_failure_invalid_credentials(self, mock_session_class):
        """Test login failure with invalid credentials."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_response = Mock()
        mock_get_response.text = '''
            <input id="__VIEWSTATE" value="viewstate123" />
            <input id="__VIEWSTATEGENERATOR" value="gen123" />
            <input id="__EVENTVALIDATION" value="valid123" />
        '''
        mock_get_response.raise_for_status = Mock()

        mock_post_response = Mock()
        mock_post_response.text = "Your login attempt was not successful"
        mock_post_response.raise_for_status = Mock()

        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response

        downloader = PSIDDownloader(username="bad", password="creds")

        with pytest.raises(RuntimeError, match="Invalid username or password"):
            downloader.login()

    @patch("psid.download.requests.Session")
    def test_download_file_auto_login(self, mock_session_class):
        """Test that download_file calls login if not logged in."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock login
        mock_get_response = Mock()
        mock_get_response.text = '''
            <input id="__VIEWSTATE" value="viewstate123" />
            <input id="__VIEWSTATEGENERATOR" value="gen123" />
            <input id="__EVENTVALIDATION" value="valid123" />
        '''
        mock_get_response.raise_for_status = Mock()

        mock_post_response = Mock()
        mock_post_response.text = "Welcome Logout"
        mock_post_response.raise_for_status = Mock()

        # Mock download
        mock_download_response = Mock()
        mock_download_response.headers = {
            "Content-Disposition": 'attachment; filename="FAM2021ER.dta"',
            "content-length": "1000",
        }
        mock_download_response.iter_content = Mock(return_value=[b"data"])
        mock_download_response.raise_for_status = Mock()

        mock_session.get.side_effect = [mock_get_response, mock_download_response]
        mock_session.post.return_value = mock_post_response

        downloader = PSIDDownloader(username="user", password="pass")

        with patch("builtins.open", create=True):
            with patch.object(Path, "mkdir"):
                # Should auto-login
                downloader.download_file(1277, Path("/tmp/test"))

        assert downloader._logged_in is True


class TestDownloadPsid:
    """Test download_psid convenience function."""

    @patch("psid.download.PSIDDownloader")
    def test_download_psid_calls_downloader(self, mock_downloader_class):
        """Test that download_psid creates and uses downloader."""
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_family.return_value = Path("/tmp/FAM2021ER.dta")
        mock_downloader.download_individual.return_value = Path("/tmp/IND2021ER.dta")

        result = download_psid(
            years=[2021],
            data_dir="/tmp/psid",
            username="user",
            password="pass",
        )

        mock_downloader.login.assert_called_once()
        mock_downloader.download_family.assert_called_once_with(2021, "/tmp/psid")
        mock_downloader.download_individual.assert_called_once_with(2021, "/tmp/psid")
        assert "family" in result
        assert "individual" in result

    @patch("psid.download.PSIDDownloader")
    def test_download_psid_multiple_years(self, mock_downloader_class):
        """Test downloading multiple years."""
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_family.return_value = Path("/tmp/test.dta")
        mock_downloader.download_individual.return_value = Path("/tmp/ind.dta")

        download_psid(
            years=[2019, 2021],
            data_dir="/tmp/psid",
            username="user",
            password="pass",
        )

        # Should download family for both years
        assert mock_downloader.download_family.call_count == 2

        # Should download individual only once (most recent)
        assert mock_downloader.download_individual.call_count == 1

    @patch("psid.download.PSIDDownloader")
    def test_download_psid_with_wealth(self, mock_downloader_class):
        """Test downloading wealth supplements."""
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.download_family.return_value = Path("/tmp/fam.dta")
        mock_downloader.download_individual.return_value = Path("/tmp/ind.dta")
        mock_downloader.download_wealth.return_value = Path("/tmp/wlt.dta")

        result = download_psid(
            years=[2021],
            data_dir="/tmp/psid",
            username="user",
            password="pass",
            include_wealth=True,
        )

        mock_downloader.download_wealth.assert_called_once_with(2021, "/tmp/psid")
        assert "wealth" in result


class TestBuildPanelDownload:
    """Test build_panel auto-download integration."""

    @patch("psid.panel._download_missing_files")
    @patch("psid.panel.load_individual")
    def test_build_panel_calls_download(self, mock_load_ind, mock_download):
        """Test that build_panel checks for missing files."""
        from psid.panel import build_panel

        mock_load_ind.side_effect = FileNotFoundError("No files")

        with pytest.raises(FileNotFoundError):
            build_panel("./data", years=[2021])

        mock_download.assert_called_once()

    @patch("psid.panel._download_missing_files")
    @patch("psid.panel.load_individual")
    def test_build_panel_skip_download(self, mock_load_ind, mock_download):
        """Test that build_panel can skip download."""
        from psid.panel import build_panel

        mock_load_ind.side_effect = FileNotFoundError("No files")

        with pytest.raises(FileNotFoundError):
            build_panel("./data", years=[2021], download=False)

        mock_download.assert_not_called()
