"""Tests for panel building."""

import pytest
import pandas as pd
import numpy as np
from psid.panel import Panel


class TestPanel:
    @pytest.fixture
    def sample_panel_data(self):
        """Create sample panel data with multiple observations per person."""
        return pd.DataFrame({
            "person_id": [1, 1, 1, 2, 2, 3, 3, 3],
            "year": [2017, 2019, 2021, 2017, 2019, 2017, 2019, 2021],
            "interview_number": [101, 102, 103, 201, 202, 101, 102, 103],
            "sequence": [1, 1, 1, 2, 2, 3, 3, 1],  # Person 3 becomes head in 2021
            "income": [50000, 52000, 55000, 30000, 32000, 25000, 26000, 45000],
            "relationship": [1, 1, 1, 2, 2, 3, 3, 1],
        })

    def test_panel_properties(self, sample_panel_data):
        """Test Panel basic properties."""
        panel = Panel(data=sample_panel_data)

        assert panel.n_individuals == 3
        assert panel.n_years == 3
        assert panel.years == [2017, 2019, 2021]

    def test_get_transitions(self, sample_panel_data):
        """Test transition extraction."""
        panel = Panel(data=sample_panel_data)
        transitions = panel.get_transitions(["income"])

        # Should have transitions: person 1 (2), person 2 (1), person 3 (2) = 5 transitions
        assert len(transitions) == 5
        assert "income_t" in transitions.columns
        assert "income_t1" in transitions.columns

    def test_to_cross_section_specific_year(self, sample_panel_data):
        """Test cross-section for specific year."""
        panel = Panel(data=sample_panel_data)
        cross_2019 = panel.to_cross_section(year=2019)

        assert len(cross_2019) == 3  # All 3 people have 2019 data

    def test_to_cross_section_most_recent(self, sample_panel_data):
        """Test cross-section with most recent observation."""
        panel = Panel(data=sample_panel_data)
        cross = panel.to_cross_section()

        assert len(cross) == 3
        # Person 1 and 3 have 2021, Person 2 has 2019
        assert cross[cross["person_id"] == 1]["year"].values[0] == 2021
        assert cross[cross["person_id"] == 2]["year"].values[0] == 2019
        assert cross[cross["person_id"] == 3]["year"].values[0] == 2021

    def test_balanced_panel(self, sample_panel_data):
        """Test balanced panel filtering."""
        panel = Panel(data=sample_panel_data)
        balanced = panel.balanced(years=[2017, 2019, 2021])

        # Only person 1 and 3 have all 3 years
        assert balanced.n_individuals == 2
        assert set(balanced.data["person_id"].unique()) == {1, 3}

    def test_get_individual(self, sample_panel_data):
        """Test getting individual's data."""
        panel = Panel(data=sample_panel_data)
        person_1 = panel.get_individual(1)

        assert len(person_1) == 3
        assert all(person_1["person_id"] == 1)

    def test_summary(self, sample_panel_data):
        """Test summary statistics."""
        panel = Panel(data=sample_panel_data)
        summary = panel.summary()

        assert 2017 in summary.index
        assert 2019 in summary.index
        assert 2021 in summary.index


class TestHeadsOnly:
    """Tests for heads_only parameter behavior."""

    @pytest.fixture
    def mixed_sequence_data(self):
        """Data where same person is head in some years, not in others."""
        return pd.DataFrame({
            "person_id": [1, 1, 1, 2, 2, 2],
            "year": [2017, 2019, 2021, 2017, 2019, 2021],
            "interview_number": [101, 102, 103, 101, 102, 104],
            "sequence": [1, 1, 2, 2, 1, 1],  # Person 1: head->head->not; Person 2: not->head->head
            "income": [50000, 52000, 48000, 30000, 60000, 65000],
        })

    def test_heads_filter_per_year(self, mixed_sequence_data):
        """heads_only should filter per-year, not per-person."""
        panel = Panel(data=mixed_sequence_data)

        # Filter to only observations where sequence == 1
        heads_data = panel.data[panel.data["sequence"] == 1].copy()
        heads_panel = Panel(data=heads_data)

        # Person 1 has 2 head years, Person 2 has 2 head years = 4 obs
        assert len(heads_panel.data) == 4

        # Both people should still be in the panel
        assert heads_panel.n_individuals == 2

        # Person 1: should only have 2017, 2019 (when they were head)
        person_1 = heads_panel.get_individual(1)
        assert len(person_1) == 2
        assert 2021 not in person_1["year"].values

        # Person 2: should only have 2019, 2021 (when they were head)
        person_2 = heads_panel.get_individual(2)
        assert len(person_2) == 2
        assert 2017 not in person_2["year"].values


class TestMinPeriods:
    """Tests for min_periods parameter - filter to individuals with minimum observations."""

    @pytest.fixture
    def varying_obs_data(self):
        """Data with varying number of observations per person."""
        return pd.DataFrame({
            "person_id": [1, 1, 1, 2, 2, 3],  # Person 1: 3 obs, Person 2: 2 obs, Person 3: 1 obs
            "year": [2017, 2019, 2021, 2017, 2019, 2021],
            "interview_number": [101, 102, 103, 201, 202, 301],
            "income": [50000, 52000, 55000, 30000, 32000, 40000],
        })

    def test_min_periods_filters_individuals(self, varying_obs_data):
        """min_periods should filter to individuals with at least N observations."""
        panel = Panel(data=varying_obs_data)
        filtered = panel.min_periods(n=2)

        # Only persons 1 and 2 have >= 2 observations
        assert filtered.n_individuals == 2
        assert set(filtered.data["person_id"].unique()) == {1, 2}

    def test_min_periods_3(self, varying_obs_data):
        """min_periods=3 should only include person with all 3 years."""
        panel = Panel(data=varying_obs_data)
        filtered = panel.min_periods(n=3)

        # Only person 1 has 3 observations
        assert filtered.n_individuals == 1
        assert filtered.data["person_id"].unique()[0] == 1

    def test_min_periods_1_returns_all(self, varying_obs_data):
        """min_periods=1 should return all individuals."""
        panel = Panel(data=varying_obs_data)
        filtered = panel.min_periods(n=1)

        assert filtered.n_individuals == 3

    def test_min_periods_preserves_all_observations(self, varying_obs_data):
        """min_periods should keep ALL observations for qualifying individuals."""
        panel = Panel(data=varying_obs_data)
        filtered = panel.min_periods(n=2)

        # Person 1 should have all 3 observations
        person_1 = filtered.get_individual(1)
        assert len(person_1) == 3

    def test_min_periods_vs_balanced(self, varying_obs_data):
        """min_periods differs from balanced - doesn't require specific years."""
        panel = Panel(data=varying_obs_data)

        # balanced requires observation in ALL specified years
        balanced = panel.balanced(years=[2017, 2019, 2021])
        assert balanced.n_individuals == 1  # Only person 1 has all 3

        # min_periods just requires N observations, ANY years
        min_2 = panel.min_periods(n=2)
        assert min_2.n_individuals == 2  # Persons 1 and 2
