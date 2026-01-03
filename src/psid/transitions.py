"""Household transition detection and analysis.

PSID tracks individuals as they move between households, enabling
analysis of life events like:
- Marriage (joining spouse's household or forming new)
- Divorce (leaving household)
- Leaving parental home
- Death of household member
- New household formation ("splitoff")

This is the key feature that makes PSID valuable for dynamic
microsimulation modeling.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class TransitionType(Enum):
    """Types of household transitions."""

    # No change
    SAME_HOUSEHOLD = "same_household"

    # Family formation/dissolution
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    WIDOWHOOD = "widowhood"

    # Residential mobility
    LEAVE_PARENTAL = "leave_parental"
    SPLITOFF = "splitoff"  # Child/other leaves to form new household
    JOIN_HOUSEHOLD = "join_household"
    MOVE_WITH_FAMILY = "move_with_family"

    # Life events
    DEATH = "death"
    BIRTH = "birth"  # New person appears

    # Unknown/other
    OTHER = "other"


@dataclass
class Transition:
    """A single household transition event."""

    person_id: int
    year_from: int
    year_to: int
    transition_type: TransitionType

    # Household info
    hh_id_from: int
    hh_id_to: int

    # Context
    relationship_from: Optional[int] = None
    relationship_to: Optional[int] = None
    marital_status_from: Optional[int] = None
    marital_status_to: Optional[int] = None

    # Person characteristics
    age_from: Optional[int] = None
    age_to: Optional[int] = None


def get_household_transitions(
    panel: "Panel",
    interview_col: str = "interview_number",
    relationship_col: str = "relationship",
    marital_col: Optional[str] = None,
    age_col: Optional[str] = None,
) -> pd.DataFrame:
    """Extract household transition events from panel data.

    Args:
        panel: Panel object with person-year data
        interview_col: Column with interview/household number
        relationship_col: Column with relationship to head
        marital_col: Column with marital status (optional)
        age_col: Column with age (optional)

    Returns:
        DataFrame with transition events

    Example:
        >>> transitions = get_household_transitions(panel)
        >>> marriage_events = transitions[transitions["type"] == "marriage"]
        >>> print(f"{len(marriage_events)} marriages observed")
    """
    df = panel.data.copy()
    df = df.sort_values([panel.id_col, panel.time_col])

    # Identify transitions
    transitions = []

    for person_id, group in df.groupby(panel.id_col):
        if len(group) < 2:
            continue

        group = group.sort_values(panel.time_col)

        for i in range(len(group) - 1):
            row_t = group.iloc[i]
            row_t1 = group.iloc[i + 1]

            year_from = row_t[panel.time_col]
            year_to = row_t1[panel.time_col]

            hh_from = row_t.get(interview_col, None)
            hh_to = row_t1.get(interview_col, None)

            rel_from = row_t.get(relationship_col, None)
            rel_to = row_t1.get(relationship_col, None)

            marital_from = row_t.get(marital_col) if marital_col else None
            marital_to = row_t1.get(marital_col) if marital_col else None

            age_from = row_t.get(age_col) if age_col else None
            age_to = row_t1.get(age_col) if age_col else None

            # Classify transition
            transition_type = _classify_transition(
                hh_from, hh_to,
                rel_from, rel_to,
                marital_from, marital_to,
                age_from, age_to,
            )

            transitions.append({
                "person_id": person_id,
                "year_from": year_from,
                "year_to": year_to,
                "type": transition_type.value,
                "hh_from": hh_from,
                "hh_to": hh_to,
                "relationship_from": rel_from,
                "relationship_to": rel_to,
                "marital_from": marital_from,
                "marital_to": marital_to,
                "age_from": age_from,
                "age_to": age_to,
                "hh_changed": hh_from != hh_to,
            })

    return pd.DataFrame(transitions)


def _classify_transition(
    hh_from: int,
    hh_to: int,
    rel_from: Optional[int],
    rel_to: Optional[int],
    marital_from: Optional[int],
    marital_to: Optional[int],
    age_from: Optional[int],
    age_to: Optional[int],
) -> TransitionType:
    """Classify a household transition.

    PSID relationship codes (approximate):
    1 = Head
    2 = Spouse/Partner
    3 = Child
    4 = Sibling
    5 = Parent
    6 = Grandchild
    7 = Other relative
    8 = Nonrelative
    9 = Other

    PSID marital status codes (approximate):
    1 = Married
    2 = Never married
    3 = Widowed
    4 = Divorced
    5 = Separated
    """
    # Same household
    if hh_from == hh_to:
        return TransitionType.SAME_HOUSEHOLD

    # Marriage: became married + joined new household
    if marital_from is not None and marital_to is not None:
        was_unmarried = marital_from in (2, 4, 5)  # Never married, divorced, separated
        now_married = marital_to == 1
        if was_unmarried and now_married:
            return TransitionType.MARRIAGE

        # Divorce: was married, now divorced/separated
        was_married = marital_from == 1
        now_unmarried = marital_to in (4, 5)
        if was_married and now_unmarried:
            return TransitionType.DIVORCE

        # Widowhood
        if marital_from == 1 and marital_to == 3:
            return TransitionType.WIDOWHOOD

    # Leave parental home: was child, now head of own household
    if rel_from is not None and rel_to is not None:
        was_child = rel_from == 3
        now_head = rel_to == 1
        if was_child and now_head:
            return TransitionType.LEAVE_PARENTAL

        # General splitoff: non-head becomes head
        was_not_head = rel_from != 1
        if was_not_head and now_head:
            return TransitionType.SPLITOFF

    # Join household: was head, now not head
    if rel_from is not None and rel_to is not None:
        was_head = rel_from == 1
        now_not_head = rel_to != 1
        if was_head and now_not_head:
            return TransitionType.JOIN_HOUSEHOLD

    # Changed household but unclear why
    return TransitionType.OTHER


def compute_transition_rates(
    transitions_df: pd.DataFrame,
    by: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute transition rates by type and optional grouping.

    Args:
        transitions_df: Output from get_household_transitions
        by: Columns to group by (e.g., ["age_from", "year_from"])

    Returns:
        DataFrame with transition counts and rates
    """
    if by is None or len(by) == 0:
        # No grouping - just count by type
        counts = transitions_df["type"].value_counts()
        total = len(transitions_df)
        rates = counts / total

        result = pd.DataFrame({
            "count": counts,
            "rate": rates,
        })
        result.index.name = "type"
        return result

    # Total person-years in each group
    total = transitions_df.groupby(by + ["type"]).size().unstack(fill_value=0)

    # Compute rates
    group_totals = transitions_df.groupby(by).size()

    rates = total.div(group_totals, axis=0)

    return pd.concat([
        total.add_suffix("_count"),
        rates.add_suffix("_rate"),
    ], axis=1)


def get_marriage_events(transitions_df: pd.DataFrame) -> pd.DataFrame:
    """Extract marriage events with spouse matching info."""
    return transitions_df[transitions_df["type"] == TransitionType.MARRIAGE.value]


def get_divorce_events(transitions_df: pd.DataFrame) -> pd.DataFrame:
    """Extract divorce events."""
    return transitions_df[transitions_df["type"] == TransitionType.DIVORCE.value]


def get_splitoff_events(transitions_df: pd.DataFrame) -> pd.DataFrame:
    """Extract splitoff events (child leaving home, etc.)."""
    splitoff_types = {
        TransitionType.LEAVE_PARENTAL.value,
        TransitionType.SPLITOFF.value,
    }
    return transitions_df[transitions_df["type"].isin(splitoff_types)]


def summarize_transitions(transitions_df: pd.DataFrame) -> pd.DataFrame:
    """Summary statistics of transitions by type."""
    summary = transitions_df.groupby("type").agg({
        "person_id": "count",
        "hh_changed": "mean",
        "age_from": ["mean", "min", "max"],
    })
    summary.columns = ["count", "pct_hh_changed", "mean_age", "min_age", "max_age"]
    summary["pct_of_total"] = summary["count"] / summary["count"].sum()
    return summary.sort_values("count", ascending=False)
