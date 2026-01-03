"""Load PSID data files.

PSID distributes data in several formats:
- ASCII fixed-width with SAS/Stata scripts
- SAS transport files
- Stata .dta files

This module supports loading from:
1. Stata .dta files (recommended - easiest)
2. ASCII fixed-width text + .do dictionary files
3. Parquet (if pre-converted)

File naming conventions:
- Family files: FAM{YEAR}ER.dta or fam{year}er.dta or FAM{YEAR}ER.txt
- Individual file: IND{YEAR}ER.dta (cumulative, includes all years)
- Wealth files: WLT{YEAR}ER.dta
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import re

import pandas as pd
import numpy as np


def parse_stata_infix(do_file: Path) -> List[Tuple[str, int, int]]:
    """Parse Stata .do file to extract fixed-width column specifications.

    Args:
        do_file: Path to .do file containing infix specifications

    Returns:
        List of (column_name, start_pos, end_pos) tuples (1-indexed)
    """
    content = do_file.read_text()

    # Find the infix section
    infix_match = re.search(r'infix\s+(.*?)using', content, re.DOTALL | re.IGNORECASE)
    if not infix_match:
        raise ValueError(f"Could not find infix specification in {do_file}")

    infix_section = infix_match.group(1)

    # Parse column specs: [long] VARNAME start - end
    # Pattern matches: optional "long", variable name, start position, "-", end position
    pattern = r'(?:long\s+)?(\w+)\s+(\d+)\s*-\s*(\d+)'

    columns = []
    for match in re.finditer(pattern, infix_section):
        var_name = match.group(1)
        start = int(match.group(2))
        end = int(match.group(3))
        columns.append((var_name, start, end))

    return columns


def load_fixed_width(
    txt_file: Path,
    do_file: Path,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Load PSID fixed-width text file using Stata .do dictionary.

    Args:
        txt_file: Path to .txt data file
        do_file: Path to .do file with column specifications
        columns: Optional list of columns to load (loads all if None)

    Returns:
        DataFrame with loaded data
    """
    col_specs = parse_stata_infix(do_file)

    # Convert to pandas fwf format (0-indexed, [start, end) tuples)
    colspecs = [(start - 1, end) for _, start, end in col_specs]
    names = [name for name, _, _ in col_specs]

    # Filter columns if specified
    if columns:
        columns_upper = [c.upper() for c in columns]
        indices = [i for i, name in enumerate(names) if name.upper() in columns_upper]
        colspecs = [colspecs[i] for i in indices]
        names = [names[i] for i in indices]

    df = pd.read_fwf(
        txt_file,
        colspecs=colspecs,
        names=names,
        dtype=str,  # Read as string first to avoid overflow
    )

    # Convert numeric columns
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


# PSID file patterns (order matters - .dta preferred over .txt)
FILE_PATTERNS = {
    "family": [
        "FAM{year}ER.dta",
        "fam{year}er.dta",
        "F{year}.dta",
        "FAM{year}.dta",
        "FAM{year}ER.txt",  # Fixed-width text format
        "fam{year}er.txt",
    ],
    "individual": [
        "IND{year}ER.dta",
        "ind{year}er.dta",
        "J{year}.dta",
        "IND{year}ER.txt",  # Fixed-width text format
        "ind{year}er.txt",
    ],
    "wealth": [
        "WLT{year}ER.dta",
        "wlt{year}er.dta",
        "WLT{year}ER.txt",
        "wlt{year}er.txt",
    ],
}


def find_file(data_dir: Path, file_type: str, year: int) -> Optional[Path]:
    """Find PSID file matching expected patterns.

    Args:
        data_dir: Directory containing PSID files
        file_type: "family", "individual", or "wealth"
        year: Survey year

    Returns:
        Path to file if found, None otherwise
    """
    patterns = FILE_PATTERNS.get(file_type, [])

    for pattern in patterns:
        filename = pattern.format(year=year)
        path = data_dir / filename
        if path.exists():
            return path

        # Try lowercase
        path = data_dir / filename.lower()
        if path.exists():
            return path

    return None


def load_family(
    year: int,
    data_dir: str = "./data",
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Load PSID family file for a specific year.

    The family file contains one record per family (interview) per year.
    Key columns:
    - Interview number (links to individual file)
    - Family-level income, wealth, and demographics

    Args:
        year: Survey year
        data_dir: Directory containing PSID files
        columns: Specific columns to load (None = all)

    Returns:
        DataFrame with family-level data

    Example:
        >>> df = load_family(2019, columns=["ER77448", "ER77511"])
    """
    data_path = Path(data_dir)

    # Find family file
    file_path = find_file(data_path, "family", year)
    if file_path is None:
        raise FileNotFoundError(
            f"PSID family file for {year} not found in {data_dir}. "
            f"Expected patterns: {FILE_PATTERNS['family']}"
        )

    # Load based on file type
    if file_path.suffix.lower() == ".dta":
        df = pd.read_stata(file_path, columns=columns)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path, columns=columns)
    elif file_path.suffix.lower() == ".txt":
        # Find corresponding .do file for column definitions
        do_file = file_path.with_suffix(".do")
        if not do_file.exists():
            raise FileNotFoundError(
                f"Dictionary file {do_file} not found. "
                f"PSID text files require the corresponding .do file."
            )
        df = load_fixed_width(file_path, do_file, columns=columns)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    # Normalize column names to uppercase
    df.columns = df.columns.str.upper()

    # Add year column
    df["year"] = year

    return df


def load_individual(
    data_dir: str = "./data",
    years: Optional[List[int]] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Load PSID individual file.

    The individual file is cumulative - it contains all individuals
    ever observed in PSID with their characteristics across all years.

    Key columns:
    - ER30001: 1968 Interview Number (family ID in 1968)
    - ER30002: Person Number (sequence within 1968 family)
    - ER30001 * 1000 + ER30002 = unique person ID

    For each year, there are columns for:
    - Interview number that year
    - Relationship to head
    - Age, sex, etc.

    Args:
        data_dir: Directory containing PSID files
        years: Years to include (filters columns)
        columns: Specific columns to load

    Returns:
        DataFrame with individual-level data
    """
    data_path = Path(data_dir)

    # Find most recent individual file (prefer .dta, then .parquet, then .txt)
    ind_files = list(data_path.glob("*[Ii][Nn][Dd]*.[Dd][Tt][Aa]"))
    if not ind_files:
        ind_files = list(data_path.glob("*[Ii][Nn][Dd]*.parquet"))
    if not ind_files:
        ind_files = list(data_path.glob("*[Ii][Nn][Dd]*.[Tt][Xx][Tt]"))

    if not ind_files:
        raise FileNotFoundError(
            f"PSID individual file not found in {data_dir}. "
            f"Expected patterns: {FILE_PATTERNS['individual']}"
        )

    # Use most recent file
    file_path = sorted(ind_files)[-1]

    # Load
    if file_path.suffix.lower() == ".dta":
        df = pd.read_stata(file_path, columns=columns)
    elif file_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(file_path, columns=columns)
    elif file_path.suffix.lower() == ".txt":
        # Find corresponding .do file for column definitions
        do_file = file_path.with_suffix(".do")
        if not do_file.exists():
            # Try uppercase
            do_file = file_path.with_name(file_path.stem.upper() + ".do")
        if not do_file.exists():
            raise FileNotFoundError(
                f"Dictionary file not found for {file_path}. "
                f"PSID text files require the corresponding .do file."
            )
        df = load_fixed_width(file_path, do_file, columns=columns)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    # Normalize column names
    df.columns = df.columns.str.upper()

    # Create unique person ID: 1968_id * 1000 + person_number
    if "ER30001" in df.columns and "ER30002" in df.columns:
        df["person_id"] = df["ER30001"] * 1000 + df["ER30002"]

    return df


def load_wealth(
    year: int,
    data_dir: str = "./data",
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Load PSID wealth supplement file.

    Wealth data is available for:
    - 1984, 1989, 1994 (every 5 years)
    - 1999, 2001, 2003, ... (every 2 years, linked to main survey)

    Args:
        year: Survey year
        data_dir: Directory containing PSID files
        columns: Specific columns to load

    Returns:
        DataFrame with wealth data
    """
    data_path = Path(data_dir)

    file_path = find_file(data_path, "wealth", year)
    if file_path is None:
        raise FileNotFoundError(
            f"PSID wealth file for {year} not found in {data_dir}. "
            f"Wealth supplements available: 1984, 1989, 1994, 1999, 2001+"
        )

    if file_path.suffix == ".dta":
        df = pd.read_stata(file_path, columns=columns)
    elif file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path, columns=columns)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    df.columns = df.columns.str.upper()
    df["year"] = year

    return df


def get_interview_number_column(year: int) -> str:
    """Get the interview number column name for a specific year.

    The interview number links family and individual files.
    Column names follow patterns like ER30020 (individual file)
    and vary by year in the family file.

    Args:
        year: Survey year

    Returns:
        Column name for interview number in individual file
    """
    # Individual file interview number columns (approximate - verify with codebook)
    interview_cols = {
        2021: "ER34501",
        2019: "ER34301",
        2017: "ER34101",
        2015: "ER33901",
        2013: "ER33701",
        2011: "ER33501",
        2009: "ER33401",
        2007: "ER33301",
        2005: "ER33201",
        2003: "ER33101",
        2001: "ER33001",
        1999: "ER32001",
        1997: "ER30806",
        1996: "ER30733",
        1995: "ER30657",
        1994: "ER30570",
        1993: "ER30498",
        1992: "ER30429",
        1991: "ER30373",
        1990: "ER30313",
        1989: "ER30246",
        1988: "ER30188",
        1987: "ER30138",
        1986: "ER30091",
        1985: "ER30052",
        1984: "ER30020",
        1983: "V9071",
        1982: "V8691",
        1981: "V8351",
        1980: "V7971",
        1979: "V7571",
        1978: "V7171",
        1977: "V6771",
        1976: "V6171",
        1975: "V5571",
        1974: "V4671",
        1973: "V4171",
        1972: "V3171",
        1971: "V2571",
        1970: "V1971",
        1969: "V1471",
        1968: "ER30001",  # Same as 1968 family ID
    }

    return interview_cols.get(year, f"ER{30000 + (year - 1968) * 100 + 1}")


def get_sequence_number_column(year: int) -> str:
    """Get the sequence/person number column for a year.

    The sequence number indicates position within the family.
    1 = head, 2 = spouse/partner, 3+ = others.
    """
    seq_cols = {
        2021: "ER34502",
        2019: "ER34302",
        2017: "ER34102",
        2015: "ER33902",
        2013: "ER33702",
        2011: "ER33502",
        2009: "ER33402",
        2007: "ER33302",
        2005: "ER33202",
        2003: "ER33102",
        2001: "ER33002",
        1999: "ER32002",
        1997: "ER30807",
    }

    return seq_cols.get(year, "")


def get_relationship_column(year: int) -> str:
    """Get the relationship to head column for a year."""
    rel_cols = {
        2021: "ER34503",
        2019: "ER34303",
        2017: "ER34103",
        2015: "ER33903",
        2013: "ER33703",
        2011: "ER33503",
        2009: "ER33403",
        2007: "ER33303",
        2005: "ER33203",
        2003: "ER33103",
        2001: "ER33003",
        1999: "ER32003",
        1997: "ER30808",
    }

    return rel_cols.get(year, "")
