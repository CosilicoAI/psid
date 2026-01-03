"""Download PSID data files from the PSID server.

This module provides functionality to authenticate with the PSID website
and download data files programmatically, similar to psidR's get.psid().

PSID requires registration at https://psidonline.isr.umich.edu

Example:
    >>> from psid.download import download_psid
    >>>
    >>> # Download family and individual files for 2019, 2021
    >>> download_psid(
    ...     years=[2019, 2021],
    ...     data_dir="./psid_data",
    ...     username="your_username",
    ...     password="your_password",
    ... )
"""

import getpass
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests


# Environment variable names for credentials
PSID_USERNAME_ENV = "PSID_USERNAME"
PSID_PASSWORD_ENV = "PSID_PASSWORD"

# PSID server URLs
PSID_BASE_URL = "https://simba.isr.umich.edu"
PSID_LOGIN_URL = f"{PSID_BASE_URL}/u/Login.aspx"
PSID_DOWNLOAD_URL = f"{PSID_BASE_URL}/Zips/GetFile.aspx"

# File numbers for each dataset type and year
# These are the numeric IDs used by PSID's download system
# Source: https://psidonline.isr.umich.edu/Guide/FileStructure.pdf
PSID_FILE_NUMBERS: Dict[str, Dict[int, int]] = {
    "family": {
        2021: 1277,
        2019: 1253,
        2017: 1229,
        2015: 1205,
        2013: 1181,
        2011: 1157,
        2009: 1133,
        2007: 1109,
        2005: 1085,
        2003: 1058,
        2001: 1054,
        1999: 1052,
        1997: 1048,
        1996: 1044,
        1995: 1040,
        1994: 1036,
        1993: 1032,
        1992: 1028,
        1991: 1024,
        1990: 1020,
        1989: 1016,
        1988: 1012,
        1987: 1008,
        1986: 1004,
        1985: 1000,
        1984: 1063,
        1983: 1059,
        1982: 1055,
        1981: 1051,
        1980: 1047,
        1979: 1043,
        1978: 1039,
        1977: 1035,
        1976: 1031,
        1975: 1027,
        1974: 1023,
        1973: 1019,
        1972: 1015,
        1971: 1011,
        1970: 1007,
        1969: 1003,
        1968: 1056,
    },
    "individual": {
        # Individual file is cumulative - use most recent year's file
        2021: 1278,
        2019: 1254,
        2017: 1230,
        2015: 1206,
        2013: 1182,
        2011: 1158,
        2009: 1134,
    },
    "wealth": {
        2021: 1279,
        2019: 1255,
        2017: 1231,
        2015: 1207,
        2013: 1183,
        2011: 1159,
        2009: 1135,
        2007: 1111,
        2005: 1087,
        2003: 1060,
        2001: 1057,
        1999: 1053,
        1994: 1037,
        1989: 1017,
        1984: 1064,
    },
}


class PSIDDownloader:
    """Client for downloading PSID data files.

    Handles authentication and file downloads from the PSID server.

    Example:
        >>> downloader = PSIDDownloader(username="user", password="pass")
        >>> downloader.login()
        >>> downloader.download_family(2021, "./psid_data")
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize downloader.

        Args:
            username: PSID username (will prompt if not provided)
            password: PSID password (will prompt if not provided)
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._logged_in = False

    def _get_credentials(self) -> tuple:
        """Get credentials from args, env vars, or prompt.

        Priority:
        1. Credentials passed to __init__
        2. Environment variables (PSID_USERNAME, PSID_PASSWORD)
        3. Interactive prompt
        """
        username = self.username
        password = self.password

        # Try environment variables
        if username is None:
            username = os.environ.get(PSID_USERNAME_ENV)
        if password is None:
            password = os.environ.get(PSID_PASSWORD_ENV)

        # Fall back to prompt
        if username is None:
            username = input("PSID username: ")
        if password is None:
            password = getpass.getpass("PSID password: ")

        return username, password

    def login(self) -> bool:
        """Authenticate with PSID server.

        Returns:
            True if login successful

        Raises:
            RuntimeError: If login fails
        """
        username, password = self._get_credentials()

        # Get login page to extract tokens
        response = self.session.get(PSID_LOGIN_URL)
        response.raise_for_status()

        # Extract ASP.NET security tokens
        viewstate = self._extract_field(response.text, "__VIEWSTATE")
        viewstate_gen = self._extract_field(response.text, "__VIEWSTATEGENERATOR")
        event_validation = self._extract_field(response.text, "__EVENTVALIDATION")

        if not viewstate:
            raise RuntimeError("Could not extract security tokens from login page")

        # Submit login form
        login_data = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_gen,
            "__EVENTVALIDATION": event_validation,
            "ctl00$ContentPlaceHolder1$Login1$UserName": username,
            "ctl00$ContentPlaceHolder1$Login1$Password": password,
            "ctl00$ContentPlaceHolder1$Login1$LoginButton": "Log In",
        }

        response = self.session.post(
            PSID_LOGIN_URL,
            data=login_data,
            allow_redirects=True,
        )
        response.raise_for_status()

        # Check if login succeeded (look for logout link or error message)
        if "Logout" in response.text or "Welcome" in response.text:
            self._logged_in = True
            return True
        elif "Your login attempt was not successful" in response.text:
            raise RuntimeError("Login failed: Invalid username or password")
        else:
            # Check cookies for authentication
            if any("ASPXAUTH" in c.name for c in self.session.cookies):
                self._logged_in = True
                return True
            raise RuntimeError("Login failed: Unknown error")

    def _extract_field(self, html: str, field_name: str) -> Optional[str]:
        """Extract hidden form field value from HTML."""
        pattern = rf'id="{field_name}".*?value="([^"]*)"'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return match.group(1)
        return None

    def download_file(
        self,
        file_number: int,
        output_dir: Path,
        file_type: str = "stata",
    ) -> Path:
        """Download a specific PSID file by file number.

        Args:
            file_number: PSID file ID number
            output_dir: Directory to save file
            file_type: "stata" for .dta, "sas" for SAS format

        Returns:
            Path to downloaded file
        """
        if not self._logged_in:
            self.login()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build download URL
        # Format: stata or sas
        fmt = "stata" if file_type == "stata" else "sas"
        download_url = f"{PSID_DOWNLOAD_URL}?file={file_number}&type={fmt}"

        print(f"  Downloading file {file_number}...")

        response = self.session.get(download_url, stream=True)
        response.raise_for_status()

        # Get filename from Content-Disposition header
        content_disp = response.headers.get("Content-Disposition", "")
        filename_match = re.search(r'filename="?([^";\s]+)"?', content_disp)
        if filename_match:
            filename = filename_match.group(1)
        else:
            filename = f"psid_{file_number}.zip"

        output_path = output_dir / filename

        # Download with progress
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    print(f"\r  Progress: {pct:.1f}%", end="", flush=True)
        print()  # Newline after progress

        # If it's a zip file, extract it
        if output_path.suffix == ".zip":
            import zipfile
            with zipfile.ZipFile(output_path, "r") as zf:
                zf.extractall(output_dir)
            # Find extracted .dta file
            dta_files = list(output_dir.glob("*.dta"))
            if dta_files:
                output_path = dta_files[-1]

        print(f"  Saved: {output_path}")
        return output_path

    def download_family(
        self,
        year: int,
        output_dir: str = "./data",
    ) -> Path:
        """Download family file for a specific year.

        Args:
            year: Survey year
            output_dir: Directory to save file

        Returns:
            Path to downloaded file
        """
        if year not in PSID_FILE_NUMBERS["family"]:
            raise ValueError(f"Family file not available for year {year}")

        file_num = PSID_FILE_NUMBERS["family"][year]
        return self.download_file(file_num, Path(output_dir))

    def download_individual(
        self,
        year: int = 2021,
        output_dir: str = "./data",
    ) -> Path:
        """Download individual file.

        The individual file is cumulative - it contains all years up to
        the specified year. You typically only need the most recent one.

        Args:
            year: Latest year to include (default: 2021)
            output_dir: Directory to save file

        Returns:
            Path to downloaded file
        """
        # Find the closest available year
        available_years = sorted(PSID_FILE_NUMBERS["individual"].keys(), reverse=True)
        target_year = None
        for y in available_years:
            if y <= year:
                target_year = y
                break

        if target_year is None:
            target_year = available_years[-1]

        file_num = PSID_FILE_NUMBERS["individual"][target_year]
        return self.download_file(file_num, Path(output_dir))

    def download_wealth(
        self,
        year: int,
        output_dir: str = "./data",
    ) -> Path:
        """Download wealth supplement file.

        Args:
            year: Survey year (wealth available: 1984, 1989, 1994, 1999+)
            output_dir: Directory to save file

        Returns:
            Path to downloaded file
        """
        if year not in PSID_FILE_NUMBERS["wealth"]:
            available = sorted(PSID_FILE_NUMBERS["wealth"].keys())
            raise ValueError(
                f"Wealth file not available for year {year}. "
                f"Available years: {available}"
            )

        file_num = PSID_FILE_NUMBERS["wealth"][year]
        return self.download_file(file_num, Path(output_dir))


def download_psid(
    years: List[int],
    data_dir: str = "./data",
    username: Optional[str] = None,
    password: Optional[str] = None,
    include_wealth: bool = False,
) -> Dict[str, List[Path]]:
    """Download PSID data files for specified years.

    This is the main entry point for downloading PSID data.

    Args:
        years: List of survey years to download
        data_dir: Directory to save files
        username: PSID username (will prompt if not provided)
        password: PSID password (will prompt if not provided)
        include_wealth: Whether to download wealth supplements

    Returns:
        Dict mapping file type to list of downloaded paths

    Example:
        >>> paths = download_psid(
        ...     years=[2019, 2021],
        ...     data_dir="./psid_data",
        ... )
        >>> print(paths["family"])
        [PosixPath('psid_data/FAM2019ER.dta'), PosixPath('psid_data/FAM2021ER.dta')]
    """
    print(f"Downloading PSID data for years: {years}")
    print(f"Data directory: {data_dir}")

    downloader = PSIDDownloader(username=username, password=password)
    downloader.login()
    print("Login successful!")

    result = {"family": [], "individual": [], "wealth": []}

    # Download family files for each year
    for year in years:
        print(f"\nDownloading family file for {year}...")
        try:
            path = downloader.download_family(year, data_dir)
            result["family"].append(path)
        except Exception as e:
            print(f"  Warning: Could not download family {year}: {e}")

    # Download individual file (only need most recent)
    max_year = max(years)
    print(f"\nDownloading individual file (up to {max_year})...")
    try:
        path = downloader.download_individual(max_year, data_dir)
        result["individual"].append(path)
    except Exception as e:
        print(f"  Warning: Could not download individual file: {e}")

    # Download wealth files if requested
    if include_wealth:
        for year in years:
            if year in PSID_FILE_NUMBERS["wealth"]:
                print(f"\nDownloading wealth file for {year}...")
                try:
                    path = downloader.download_wealth(year, data_dir)
                    result["wealth"].append(path)
                except Exception as e:
                    print(f"  Warning: Could not download wealth {year}: {e}")

    print(f"\nDownload complete!")
    print(f"  Family files: {len(result['family'])}")
    print(f"  Individual files: {len(result['individual'])}")
    print(f"  Wealth files: {len(result['wealth'])}")

    return result


def get_file_number(file_type: str, year: int) -> int:
    """Get the PSID file number for a specific dataset.

    Args:
        file_type: "family", "individual", or "wealth"
        year: Survey year

    Returns:
        File number for PSID download system
    """
    if file_type not in PSID_FILE_NUMBERS:
        raise ValueError(f"Unknown file type: {file_type}")
    if year not in PSID_FILE_NUMBERS[file_type]:
        available = sorted(PSID_FILE_NUMBERS[file_type].keys())
        raise ValueError(
            f"{file_type} file not available for {year}. Available: {available}"
        )
    return PSID_FILE_NUMBERS[file_type][year]
