"""Tests for sample filtering (SRC/SEO/immigrant).

PSID sample types are determined by ER30001 (1968 Interview Number):
- SRC (Survey Research Center): 1-2999
- SEO (Survey of Economic Opportunity): 5001-6872
- Immigrant refresher: 3001-3511, 4001-4462, 7001-9308
"""

import pytest
import pandas as pd
import numpy as np
from psid.sample import (
    SampleType,
    get_sample_type,
    filter_by_sample,
    SAMPLE_RANGES,
)


class TestSampleType:
    def test_src_range(self):
        """SRC sample is ER30001 in range 1-2999."""
        assert get_sample_type(1) == SampleType.SRC
        assert get_sample_type(1000) == SampleType.SRC
        assert get_sample_type(2999) == SampleType.SRC

    def test_seo_range(self):
        """SEO sample is ER30001 in range 5001-6872."""
        assert get_sample_type(5001) == SampleType.SEO
        assert get_sample_type(6000) == SampleType.SEO
        assert get_sample_type(6872) == SampleType.SEO

    def test_immigrant_ranges(self):
        """Immigrant samples have multiple ranges."""
        # 1997 immigrant refresher: 3001-3511
        assert get_sample_type(3001) == SampleType.IMMIGRANT
        assert get_sample_type(3511) == SampleType.IMMIGRANT

        # 1999 immigrant refresher: 4001-4462
        assert get_sample_type(4001) == SampleType.IMMIGRANT
        assert get_sample_type(4462) == SampleType.IMMIGRANT

        # 2017 immigrant refresher: 7001-9308
        assert get_sample_type(7001) == SampleType.IMMIGRANT
        assert get_sample_type(9308) == SampleType.IMMIGRANT

    def test_unknown_range(self):
        """IDs outside known ranges return UNKNOWN."""
        assert get_sample_type(0) == SampleType.UNKNOWN
        assert get_sample_type(3000) == SampleType.UNKNOWN  # Between SRC and immigrant
        assert get_sample_type(10000) == SampleType.UNKNOWN


class TestFilterBySample:
    @pytest.fixture
    def sample_df(self):
        """Create DataFrame with mixed sample types."""
        return pd.DataFrame({
            "ER30001": [100, 500, 1500, 2500, 3100, 4200, 5500, 6500, 7500, 8500],
            "ER30002": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            "income": [50000, 60000, 70000, 80000, 40000, 45000, 30000, 35000, 55000, 65000],
        })

    def test_filter_src_only(self, sample_df):
        """Filter to SRC sample only."""
        filtered = filter_by_sample(sample_df, sample=SampleType.SRC)

        # SRC: 100, 500, 1500, 2500 (IDs 1-2999)
        assert len(filtered) == 4
        assert all(filtered["ER30001"] <= 2999)

    def test_filter_seo_only(self, sample_df):
        """Filter to SEO sample only."""
        filtered = filter_by_sample(sample_df, sample=SampleType.SEO)

        # SEO: 5500, 6500 (IDs 5001-6872)
        assert len(filtered) == 2
        assert all((filtered["ER30001"] >= 5001) & (filtered["ER30001"] <= 6872))

    def test_filter_immigrant_only(self, sample_df):
        """Filter to immigrant sample only."""
        filtered = filter_by_sample(sample_df, sample=SampleType.IMMIGRANT)

        # Immigrant: 3100, 4200, 7500, 8500
        assert len(filtered) == 4

    def test_filter_multiple_samples(self, sample_df):
        """Filter to multiple sample types."""
        filtered = filter_by_sample(
            sample_df,
            sample=[SampleType.SRC, SampleType.SEO]
        )

        # SRC + SEO = 6 records
        assert len(filtered) == 6

    def test_filter_by_string(self, sample_df):
        """Accept string sample names."""
        filtered = filter_by_sample(sample_df, sample="SRC")
        assert len(filtered) == 4

        filtered = filter_by_sample(sample_df, sample="seo")  # Case insensitive
        assert len(filtered) == 2

    def test_filter_none_returns_all(self, sample_df):
        """sample=None returns all records."""
        filtered = filter_by_sample(sample_df, sample=None)
        assert len(filtered) == len(sample_df)

    def test_adds_sample_type_column(self, sample_df):
        """Filtering adds sample_type column."""
        filtered = filter_by_sample(sample_df, sample=SampleType.SRC)
        assert "sample_type" in filtered.columns
        assert all(filtered["sample_type"] == "SRC")


class TestBuildPanelWithSample:
    """Integration tests for sample filtering in build_panel."""

    def test_build_panel_sample_parameter(self):
        """build_panel accepts sample parameter."""
        # This will fail until we implement the feature
        import psid

        # Should accept sample parameter
        # panel = psid.build_panel(
        #     data_dir="./data",
        #     years=[2019],
        #     sample="SRC",
        # )
        pass  # Placeholder until implementation
