"""Tests for household transitions."""

import pytest
import pandas as pd
import numpy as np
from psid.transitions import (
    TransitionType,
    get_household_transitions,
    _classify_transition,
    compute_transition_rates,
    summarize_transitions,
)
from psid.panel import Panel


class TestClassifyTransition:
    def test_same_household(self):
        result = _classify_transition(
            hh_from=1001, hh_to=1001,
            rel_from=1, rel_to=1,
            marital_from=1, marital_to=1,
            age_from=35, age_to=37,
        )
        assert result == TransitionType.SAME_HOUSEHOLD

    def test_marriage(self):
        # Was never married (2), now married (1), different household
        result = _classify_transition(
            hh_from=1001, hh_to=2002,
            rel_from=1, rel_to=2,  # Was head, now spouse
            marital_from=2, marital_to=1,
            age_from=28, age_to=30,
        )
        assert result == TransitionType.MARRIAGE

    def test_divorce(self):
        # Was married (1), now divorced (4), different household
        result = _classify_transition(
            hh_from=1001, hh_to=3003,
            rel_from=2, rel_to=1,  # Was spouse, now head
            marital_from=1, marital_to=4,
            age_from=40, age_to=42,
        )
        assert result == TransitionType.DIVORCE

    def test_widowhood(self):
        result = _classify_transition(
            hh_from=1001, hh_to=3003,
            rel_from=2, rel_to=1,
            marital_from=1, marital_to=3,  # Married -> Widowed
            age_from=65, age_to=67,
        )
        assert result == TransitionType.WIDOWHOOD

    def test_leave_parental(self):
        # Was child (3), now head (1) of different household
        result = _classify_transition(
            hh_from=1001, hh_to=4004,
            rel_from=3, rel_to=1,
            marital_from=2, marital_to=2,
            age_from=22, age_to=24,
        )
        assert result == TransitionType.LEAVE_PARENTAL

    def test_splitoff(self):
        # Non-child, non-head becoming head of new household
        result = _classify_transition(
            hh_from=1001, hh_to=5005,
            rel_from=7, rel_to=1,  # Other relative -> Head
            marital_from=2, marital_to=2,
            age_from=25, age_to=27,
        )
        assert result == TransitionType.SPLITOFF

    def test_join_household(self):
        # Was head, now not head (e.g., moved in with someone)
        result = _classify_transition(
            hh_from=1001, hh_to=6006,
            rel_from=1, rel_to=8,  # Head -> Nonrelative
            marital_from=2, marital_to=2,
            age_from=30, age_to=32,
        )
        assert result == TransitionType.JOIN_HOUSEHOLD


class TestGetHouseholdTransitions:
    @pytest.fixture
    def sample_panel(self):
        """Create sample panel data with known transitions."""
        data = pd.DataFrame({
            "person_id": [1, 1, 1, 2, 2, 2, 3, 3],
            "year": [2017, 2019, 2021, 2017, 2019, 2021, 2019, 2021],
            "interview_number": [100, 100, 200, 101, 102, 102, 103, 104],
            "relationship": [3, 3, 1, 1, 1, 1, 1, 2],  # Person 1 leaves home
            "marital_status": [2, 2, 2, 1, 1, 4, 2, 1],  # Person 2 divorces, 3 marries
        })
        return Panel(data=data, id_col="person_id", time_col="year")

    def test_detects_transitions(self, sample_panel):
        trans = get_household_transitions(
            sample_panel,
            interview_col="interview_number",
            relationship_col="relationship",
            marital_col="marital_status",
        )

        # Should have transitions
        assert len(trans) > 0

        # Person 1: household changes in 2019->2021
        p1_trans = trans[trans["person_id"] == 1]
        assert len(p1_trans) == 2  # Two transitions (2017->2019, 2019->2021)

        # Check that household change is detected
        hh_changes = trans[trans["hh_changed"]]
        assert len(hh_changes) > 0


class TestComputeTransitionRates:
    def test_basic_rates(self):
        transitions = pd.DataFrame({
            "person_id": [1, 2, 3, 4, 5],
            "type": ["marriage", "divorce", "same_household", "same_household", "marriage"],
            "age_from": [25, 40, 35, 50, 28],
        })

        rates = compute_transition_rates(transitions)

        # No grouping returns counts and rates by type
        assert "count" in rates.columns
        assert "rate" in rates.columns
        assert rates.loc["marriage", "count"] == 2
        assert rates.loc["divorce", "count"] == 1

    def test_rates_by_age(self):
        transitions = pd.DataFrame({
            "person_id": range(10),
            "type": ["marriage"] * 3 + ["same_household"] * 7,
            "age_from": [25, 25, 25, 50, 50, 50, 50, 50, 50, 50],
        })

        rates = compute_transition_rates(transitions, by=["age_from"])

        assert len(rates) == 2  # Two age groups


class TestSummarizeTransitions:
    def test_summary(self):
        transitions = pd.DataFrame({
            "person_id": [1, 2, 3, 4, 5],
            "type": ["marriage", "divorce", "same_household", "same_household", "marriage"],
            "hh_changed": [True, True, False, False, True],
            "age_from": [25, 40, 35, 50, 28],
        })

        summary = summarize_transitions(transitions)

        assert "count" in summary.columns
        assert "pct_of_total" in summary.columns
        assert summary["count"].sum() == 5
