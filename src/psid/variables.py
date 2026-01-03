"""PSID variable crosswalk and specification.

PSID variables have different names in each survey year. For example,
"total family income" might be called:
- ER77448 in 2019
- ER81775 in 2021

This module provides tools to:
1. Specify variables with year-specific names
2. Look up variable names from a crosswalk
3. Search for variables by topic
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
import json
from pathlib import Path


@dataclass
class VariableSpec:
    """Specification for a single variable across years.

    Attributes:
        friendly_name: User-friendly name (e.g., "income")
        year_codes: Mapping of year -> PSID variable code
        description: Human-readable description
        category: Variable category (income, wealth, demographics, etc.)
    """
    friendly_name: str
    year_codes: Dict[int, str]
    description: str = ""
    category: str = "other"

    def get_code(self, year: int) -> Optional[str]:
        """Get PSID variable code for a specific year."""
        return self.year_codes.get(year)

    def available_years(self) -> List[int]:
        """Years where this variable is available."""
        return sorted(self.year_codes.keys())


class FamilyVars:
    """Family-level variable specifications.

    Example:
        >>> fam_vars = FamilyVars({
        ...     "income": {2019: "ER77448", 2021: "ER81775"},
        ...     "wealth": {2019: "ER71426", 2021: "ER77450"},
        ... })
        >>> fam_vars.get_codes(2019)
        {'income': 'ER77448', 'wealth': 'ER71426'}
    """

    def __init__(self, specs: Dict[str, Dict[int, str]]):
        """Initialize from variable specification dict.

        Args:
            specs: Mapping of friendly_name -> {year: code}
        """
        self.specs = {
            name: VariableSpec(friendly_name=name, year_codes=codes)
            for name, codes in specs.items()
        }

    def get_codes(self, year: int) -> Dict[str, str]:
        """Get all variable codes for a year.

        Args:
            year: Survey year

        Returns:
            Dict mapping friendly_name -> PSID code
        """
        return {
            name: spec.get_code(year)
            for name, spec in self.specs.items()
            if spec.get_code(year) is not None
        }

    def get_columns(self, year: int) -> List[str]:
        """Get list of PSID column names for a year."""
        return list(self.get_codes(year).values())

    @property
    def names(self) -> List[str]:
        """All friendly variable names."""
        return list(self.specs.keys())


class IndividualVars:
    """Individual-level variable specifications.

    Similar to FamilyVars but for the individual file.
    Common variables include survey weights and demographics.
    """

    def __init__(self, specs: Dict[str, Dict[int, str]]):
        self.specs = {
            name: VariableSpec(friendly_name=name, year_codes=codes)
            for name, codes in specs.items()
        }

    def get_codes(self, year: int) -> Dict[str, str]:
        return {
            name: spec.get_code(year)
            for name, spec in self.specs.items()
            if spec.get_code(year) is not None
        }

    def get_columns(self, year: int) -> List[str]:
        return list(self.get_codes(year).values())

    @property
    def names(self) -> List[str]:
        return list(self.specs.keys())


# Common variables with crosswalk (subset - full crosswalk from PSID website)
COMMON_VARIABLES = {
    # Core IDs (these are consistent)
    "interview_number": {
        "description": "Interview number (family ID for year)",
        "category": "id",
        "codes": {
            # ER30001 pattern for individual file
            # Interview number in family file varies
        }
    },
    # Income variables
    "total_family_income": {
        "description": "Total family money income",
        "category": "income",
        "codes": {
            2021: "ER81775",
            2019: "ER77448",
            2017: "ER71426",
            2015: "ER65349",
            2013: "ER58152",
            2011: "ER52343",
            2009: "ER46935",
            2007: "ER41027",
            2005: "ER28037",
            2003: "ER24099",
            2001: "ER20456",
            1999: "ER16462",
            1997: "ER12079",
            1996: "ER9244",
            1995: "ER6993",
            1994: "ER4153",
            1993: "V23322",
            1992: "V22406",
            1991: "V21481",
            1990: "V20651",
            1989: "V17533",
            1988: "V16144",
            1987: "V14670",
            1986: "V13623",
            1985: "V12371",
            1984: "V11022",
            1983: "V10419",
            1982: "V8689",
            1981: "V8065",
            1980: "V7412",
            1979: "V6766",
            1978: "V6173",
            1977: "V5626",
            1976: "V5029",
            1975: "V4379",
            1974: "V3676",
            1973: "V3051",
            1972: "V2408",
            1971: "V1904",
            1970: "V1514",
            1969: "V1196",
            1968: "V81",
        }
    },
    "head_labor_income": {
        "description": "Head's labor income",
        "category": "income",
        "codes": {
            2021: "ER81711",
            2019: "ER77384",
            2017: "ER71330",
            2015: "ER65253",
            2013: "ER58056",
            2011: "ER52247",
        }
    },
    "wife_labor_income": {
        "description": "Wife's labor income",
        "category": "income",
        "codes": {
            2021: "ER81743",
            2019: "ER77416",
            2017: "ER71362",
            2015: "ER65285",
            2013: "ER58088",
            2011: "ER52279",
        }
    },
    # Wealth variables (available 1984, 1989, 1994, 1999, 2001+)
    "total_wealth": {
        "description": "Total family wealth (assets - debts)",
        "category": "wealth",
        "codes": {
            2021: "ER81850",
            2019: "ER77511",
            2017: "ER71485",
            2015: "ER65408",
            2013: "ER58211",
            2011: "ER52394",
            2009: "ER46970",
            2007: "ER46938",
            2005: "S817",
            2003: "S617",
            2001: "S417",
            1999: "S317",
            1994: "S117",
            1989: "S117",
            1984: "S117",
        }
    },
    # Demographics
    "age_head": {
        "description": "Age of head",
        "category": "demographics",
        "codes": {
            2021: "ER81394",
            2019: "ER77069",
            2017: "ER71017",
            2015: "ER64943",
            2013: "ER57739",
            2011: "ER51904",
            2009: "ER46543",
            2007: "ER40565",
            2005: "ER27393",
            2003: "ER23426",
            2001: "ER19989",
            1999: "ER15928",
            1997: "ER11760",
        }
    },
    "family_size": {
        "description": "Number of persons in family unit",
        "category": "demographics",
        "codes": {
            2021: "ER81389",
            2019: "ER77064",
            2017: "ER71012",
            2015: "ER64938",
            2013: "ER57734",
            2011: "ER51899",
            2009: "ER46538",
            2007: "ER40560",
            2005: "ER27388",
            2003: "ER23421",
            2001: "ER19984",
            1999: "ER15923",
            1997: "ER11755",
        }
    },
    "marital_status": {
        "description": "Marital status of head",
        "category": "demographics",
        "codes": {
            2021: "ER81395",
            2019: "ER77070",
            2017: "ER71018",
            2015: "ER64944",
            2013: "ER57740",
            2011: "ER51905",
            2009: "ER46544",
            2007: "ER40566",
            2005: "ER27394",
            2003: "ER23427",
            2001: "ER19990",
            1999: "ER15929",
            1997: "ER11761",
        }
    },
    # Weights
    "family_weight": {
        "description": "Family weight",
        "category": "weight",
        "codes": {
            2021: "ER81856",
            2019: "ER77516",
            2017: "ER71538",
            2015: "ER65462",
            2013: "ER58257",
            2011: "ER52436",
            2009: "ER47012",
            2007: "ER41069",
            2005: "ER28078",
            2003: "ER24180",
            2001: "ER20459",
            1999: "ER16519",
            1997: "ER12223",
        }
    },
}


def get_crosswalk(
    variable: str,
    years: Optional[List[int]] = None,
) -> Dict[int, str]:
    """Get variable code crosswalk for a variable.

    Args:
        variable: Friendly variable name
        years: Optional list of years to include

    Returns:
        Dict mapping year -> PSID code

    Example:
        >>> get_crosswalk("total_family_income", years=[2019, 2021])
        {2019: 'ER77448', 2021: 'ER81775'}
    """
    if variable not in COMMON_VARIABLES:
        raise ValueError(f"Variable '{variable}' not in crosswalk. "
                        f"Use search_variables() to find available variables.")

    codes = COMMON_VARIABLES[variable]["codes"]

    if years is not None:
        codes = {y: c for y, c in codes.items() if y in years}

    return codes


def search_variables(
    keyword: str = "",
    category: Optional[str] = None,
) -> List[str]:
    """Search for variables by keyword or category.

    Args:
        keyword: Search term (searches name and description)
        category: Filter by category (income, wealth, demographics, weight, id)

    Returns:
        List of matching variable names
    """
    matches = []
    keyword = keyword.lower()

    for name, info in COMMON_VARIABLES.items():
        # Filter by category
        if category and info.get("category") != category:
            continue

        # Filter by keyword
        if keyword:
            searchable = f"{name} {info.get('description', '')}".lower()
            if keyword not in searchable:
                continue

        matches.append(name)

    return sorted(matches)


def describe(variable: str) -> dict:
    """Get full information about a variable.

    Args:
        variable: Variable name

    Returns:
        Dict with description, category, and year codes
    """
    if variable not in COMMON_VARIABLES:
        raise ValueError(f"Variable '{variable}' not found")

    info = COMMON_VARIABLES[variable].copy()
    info["name"] = variable
    info["available_years"] = sorted(info["codes"].keys())
    return info
