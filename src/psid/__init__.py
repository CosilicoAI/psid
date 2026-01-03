"""psid: Python package for working with PSID (Panel Study of Income Dynamics) data.

PSID is the longest-running longitudinal household survey in the world,
following families since 1968. This package provides tools to:

1. Load PSID data files (family, individual, wealth)
2. Build longitudinal panels with consistent person IDs
3. Handle the variable name crosswalk across years
4. Track household transitions (marriage, divorce, splitoffs)

Note: PSID data requires registration at https://psidonline.isr.umich.edu
You must download data files manually and provide the path to this package.

Example:
    >>> import psid
    >>>
    >>> # Define variables to extract (names vary by year)
    >>> family_vars = psid.FamilyVars({
    ...     "income": {2019: "ER77448", 2021: "ER81775"},
    ...     "wealth": {2019: "ER71426", 2021: "ER77450"},
    ... })
    >>>
    >>> # Build panel
    >>> panel = psid.build_panel(
    ...     data_dir="./psid_data",
    ...     years=[2019, 2021],
    ...     family_vars=family_vars,
    ... )
    >>>
    >>> # Get transitions for modeling
    >>> transitions = panel.get_transitions(["income", "wealth"])
"""

from psid.variables import (
    FamilyVars,
    IndividualVars,
    get_crosswalk,
    search_variables,
    COMMON_VARIABLES,
)
from psid.load import load_family, load_individual, load_wealth
from psid.panel import build_panel, Panel
from psid.transitions import get_household_transitions, TransitionType
from psid.sample import (
    SampleType,
    get_sample_type,
    filter_by_sample,
    SAMPLE_RANGES,
)

__version__ = "0.1.0"

__all__ = [
    # Variable specification
    "FamilyVars",
    "IndividualVars",
    "get_crosswalk",
    "search_variables",
    "COMMON_VARIABLES",
    # Loading
    "load_family",
    "load_individual",
    "load_wealth",
    # Panel building
    "build_panel",
    "Panel",
    # Transitions
    "get_household_transitions",
    "TransitionType",
    # Sample filtering
    "SampleType",
    "get_sample_type",
    "filter_by_sample",
    "SAMPLE_RANGES",
]
