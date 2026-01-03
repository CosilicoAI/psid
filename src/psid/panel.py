"""Build longitudinal panels from PSID data.

The key challenge with PSID is constructing consistent person IDs
and linking family-level data to individuals across years.

Person ID construction:
    person_id = ER30001 * 1000 + ER30002

Where:
- ER30001 is the 1968 Interview Number (baseline family)
- ER30002 is the Person Number within that family

This ID is stable across all waves, even when:
- Person moves to new household
- Person gets married/divorced
- Family "splits off" (child leaves home)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd

from psid.load import (
    load_family,
    load_individual,
    find_file,
    get_interview_number_column,
    get_sequence_number_column,
    get_relationship_column,
)
from psid.variables import FamilyVars, IndividualVars, get_crosswalk
from psid.sample import filter_by_sample, SampleType
from typing import Union


@dataclass
class Panel:
    """PSID panel data with convenient accessors.

    Attributes:
        data: DataFrame in person-year format
        id_col: Person identifier column
        time_col: Time period column (year)
    """
    data: pd.DataFrame
    id_col: str = "person_id"
    time_col: str = "year"
    _value_cols: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self._value_cols:
            exclude = {self.id_col, self.time_col, "interview_number", "sequence"}
            self._value_cols = [c for c in self.data.columns if c not in exclude]

    @property
    def n_individuals(self) -> int:
        """Number of unique individuals."""
        return self.data[self.id_col].nunique()

    @property
    def n_years(self) -> int:
        """Number of survey years."""
        return self.data[self.time_col].nunique()

    @property
    def years(self) -> List[int]:
        """List of survey years."""
        return sorted(self.data[self.time_col].unique())

    @property
    def columns(self) -> List[str]:
        """Value columns (excluding ID/time)."""
        return self._value_cols

    def get_transitions(
        self,
        cols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Get transition data (current year -> next observed year).

        Unlike SIPP which is monthly, PSID is biennial (since 1997),
        so transitions span 2 years.

        Args:
            cols: Columns to include (default: all value columns)

        Returns:
            DataFrame with: person_id, year_t, year_t1, [col]_t, [col]_t1
        """
        cols = cols or self._value_cols

        df = self.data.copy()
        df = df.sort_values([self.id_col, self.time_col])

        result_cols = [self.id_col, self.time_col]
        for col in cols:
            if col not in df.columns:
                continue
            df[f"{col}_t1"] = df.groupby(self.id_col)[col].shift(-1)
            result_cols.extend([col, f"{col}_t1"])

        # Add next year
        df["year_t1"] = df.groupby(self.id_col)[self.time_col].shift(-1)
        result_cols.insert(2, "year_t1")

        # Drop rows without next observation
        result = df[result_cols].dropna(subset=["year_t1"])

        # Rename current values
        rename = {col: f"{col}_t" for col in cols if col in df.columns}
        rename[self.time_col] = "year_t"
        result = result.rename(columns=rename)

        return result

    def to_cross_section(self, year: Optional[int] = None) -> pd.DataFrame:
        """Get cross-section (one row per person).

        Args:
            year: Specific year (default: most recent per person)

        Returns:
            DataFrame with one row per individual
        """
        if year is not None:
            return self.data[self.data[self.time_col] == year].copy()

        # Most recent observation per person
        idx = self.data.groupby(self.id_col)[self.time_col].idxmax()
        return self.data.loc[idx].reset_index(drop=True)

    def get_individual(self, person_id: int) -> pd.DataFrame:
        """Get all observations for one individual."""
        return self.data[self.data[self.id_col] == person_id].copy()

    def balanced(self, years: Optional[List[int]] = None) -> "Panel":
        """Filter to individuals observed in all specified years.

        Args:
            years: Years to require (default: all years in panel)

        Returns:
            Panel with balanced observations
        """
        years = years or self.years
        n_required = len(years)

        counts = self.data[self.data[self.time_col].isin(years)].groupby(
            self.id_col
        )[self.time_col].nunique()

        valid_ids = counts[counts == n_required].index
        filtered = self.data[self.data[self.id_col].isin(valid_ids)]

        return Panel(
            data=filtered.reset_index(drop=True),
            id_col=self.id_col,
            time_col=self.time_col,
        )

    def min_periods(self, n: int) -> "Panel":
        """Filter to individuals with at least N observations.

        Unlike `balanced()` which requires specific years, this just
        requires a minimum number of observations regardless of which years.

        Args:
            n: Minimum number of observations required

        Returns:
            Panel with only individuals having >= n observations

        Example:
            >>> # Keep only individuals observed at least twice
            >>> filtered = panel.min_periods(n=2)
        """
        counts = self.data.groupby(self.id_col)[self.time_col].count()
        valid_ids = counts[counts >= n].index
        filtered = self.data[self.data[self.id_col].isin(valid_ids)]

        return Panel(
            data=filtered.reset_index(drop=True),
            id_col=self.id_col,
            time_col=self.time_col,
        )

    def summary(self) -> pd.DataFrame:
        """Summary statistics by year."""
        numeric_cols = [c for c in self._value_cols
                       if self.data[c].dtype in ['int64', 'float64']]
        return self.data.groupby(self.time_col)[numeric_cols].agg(
            ["count", "mean", "std", "min", "max"]
        )


def build_panel(
    data_dir: str,
    years: List[int],
    family_vars: Optional[FamilyVars] = None,
    individual_vars: Optional[IndividualVars] = None,
    heads_only: bool = False,
    balanced: bool = False,
    sample: Optional[Union[str, SampleType, List[Union[str, SampleType]]]] = None,
) -> Panel:
    """Build longitudinal panel from PSID data files.

    This is the main function for constructing PSID panels. It:
    1. Loads the individual file (for person IDs and demographics)
    2. Loads family files for each year
    3. Merges family data to individuals via interview number
    4. Creates consistent person_id across all years

    Note: PSID data must be downloaded manually from https://psidonline.isr.umich.edu
    See the README for download instructions.

    Args:
        data_dir: Directory containing PSID files (downloaded manually)
        years: Survey years to include
        family_vars: Family-level variables to extract
        individual_vars: Individual-level variables to extract
        heads_only: Only include household heads
        balanced: Only include individuals in all years
        sample: Sample type(s) to include: "SRC", "SEO", "IMMIGRANT",
            or list of these. None includes all samples.

    Returns:
        Panel object with person-year data

    Example:
        >>> family_vars = FamilyVars({
        ...     "income": {2019: "ER77448", 2021: "ER81775"},
        ... })
        >>> panel = build_panel("./data", years=[2019, 2021], family_vars=family_vars)
        >>> print(f"{panel.n_individuals} individuals × {panel.n_years} years")

        # For nationally representative sample, use SRC only:
        >>> panel = build_panel("./data", years=[2019, 2021], sample="SRC")
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    # Load individual file
    print("Loading individual file...")
    ind = load_individual(data_dir)

    # Ensure we have core ID columns
    if "ER30001" not in ind.columns or "ER30002" not in ind.columns:
        raise ValueError("Individual file missing core ID columns (ER30001, ER30002)")

    # Apply sample filter if specified
    if sample is not None:
        print(f"Filtering to sample: {sample}")
        ind = filter_by_sample(ind, sample=sample, er30001_col="ER30001")
        print(f"  {len(ind)} individuals after sample filter")

    # Create person_id
    ind["person_id"] = ind["ER30001"] * 1000 + ind["ER30002"]

    # Build panel year by year
    all_years = []

    for year in sorted(years):
        print(f"Processing {year}...")

        # Get interview number column for this year
        interview_col = get_interview_number_column(year)
        seq_col = get_sequence_number_column(year)
        rel_col = get_relationship_column(year)

        # Extract individual-year data
        ind_cols = ["person_id", "ER30001", "ER30002"]
        if interview_col in ind.columns:
            ind_cols.append(interview_col)
        if seq_col and seq_col in ind.columns:
            ind_cols.append(seq_col)
        if rel_col and rel_col in ind.columns:
            ind_cols.append(rel_col)

        ind_year = ind[ind_cols].copy()
        ind_year = ind_year.rename(columns={
            interview_col: "interview_number",
            seq_col: "sequence" if seq_col else None,
            rel_col: "relationship" if rel_col else None,
        })

        # Filter to those with valid interview (in sample this year)
        ind_year = ind_year[ind_year["interview_number"] > 0]

        if heads_only and "sequence" in ind_year.columns:
            ind_year = ind_year[ind_year["sequence"] == 1]

        # Load family file
        fam_cols = None
        if family_vars:
            fam_cols = family_vars.get_columns(year)
            # Always include interview number (first column in family file)
            # Family files use different interview number names

        try:
            fam = load_family(year, data_dir, columns=fam_cols)
        except FileNotFoundError as e:
            print(f"  Warning: {e}")
            continue

        # The first column of family file is typically the interview number
        fam_interview_col = fam.columns[0]  # Usually like ER30000 pattern
        fam = fam.rename(columns={fam_interview_col: "fam_interview"})

        # Merge individual to family
        merged = ind_year.merge(
            fam,
            left_on="interview_number",
            right_on="fam_interview",
            how="inner",
        )

        # Rename family variables to friendly names
        if family_vars:
            code_to_name = {v: k for k, v in family_vars.get_codes(year).items()}
            merged = merged.rename(columns={
                c.upper(): code_to_name.get(c.upper(), c)
                for c in merged.columns
            })

        merged["year"] = year
        all_years.append(merged)

        print(f"  {len(merged)} person-year records")

    if not all_years:
        raise ValueError("No data loaded. Check file paths and years.")

    # Combine all years
    panel_data = pd.concat(all_years, ignore_index=True)

    # Clean up columns
    drop_cols = ["fam_interview", "ER30001", "ER30002"]
    panel_data = panel_data.drop(
        columns=[c for c in drop_cols if c in panel_data.columns]
    )

    # Create panel object
    panel = Panel(data=panel_data, id_col="person_id", time_col="year")

    if balanced:
        panel = panel.balanced(years)

    print(f"\nPanel: {panel.n_individuals} individuals × {panel.n_years} years")
    print(f"Years: {panel.years}")

    return panel
