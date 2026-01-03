"""Sample type filtering for PSID data.

PSID has multiple sample components determined by ER30001 (1968 Interview Number):
- SRC (Survey Research Center): Original 1968 national probability sample
- SEO (Survey of Economic Opportunity): Low-income oversample from 1968
- Immigrant: Refresher samples added in 1997, 1999, 2017 to maintain representativeness

For nationally representative analysis, typically use SRC sample with weights.
"""

from enum import Enum
from typing import List, Optional, Union

import pandas as pd


class SampleType(Enum):
    """PSID sample types."""

    SRC = "SRC"  # Survey Research Center (original national sample)
    SEO = "SEO"  # Survey of Economic Opportunity (low-income oversample)
    IMMIGRANT = "IMMIGRANT"  # Immigrant refresher samples
    LATINO = "LATINO"  # Latino sample (subset of immigrant)
    UNKNOWN = "UNKNOWN"  # Outside known ranges


# ER30001 ranges for each sample type
# Source: PSID documentation
SAMPLE_RANGES = {
    SampleType.SRC: [(1, 2999)],
    SampleType.SEO: [(5001, 6872)],
    SampleType.IMMIGRANT: [
        (3001, 3511),  # 1997 immigrant refresher
        (4001, 4462),  # 1999 immigrant refresher
        (7001, 9308),  # 2017 immigrant refresher
    ],
}


def get_sample_type(er30001: int) -> SampleType:
    """Determine sample type from ER30001 (1968 Interview Number).

    Args:
        er30001: The 1968 Interview Number

    Returns:
        SampleType enum value

    Example:
        >>> get_sample_type(1500)
        SampleType.SRC
        >>> get_sample_type(5500)
        SampleType.SEO
    """
    for sample_type, ranges in SAMPLE_RANGES.items():
        for low, high in ranges:
            if low <= er30001 <= high:
                return sample_type

    return SampleType.UNKNOWN


def _parse_sample_arg(
    sample: Optional[Union[str, SampleType, List[Union[str, SampleType]]]]
) -> Optional[List[SampleType]]:
    """Parse sample argument to list of SampleType.

    Args:
        sample: String, SampleType, or list of either

    Returns:
        List of SampleType or None if sample is None
    """
    if sample is None:
        return None

    if isinstance(sample, str):
        return [SampleType[sample.upper()]]

    if isinstance(sample, SampleType):
        return [sample]

    if isinstance(sample, list):
        result = []
        for s in sample:
            if isinstance(s, str):
                result.append(SampleType[s.upper()])
            else:
                result.append(s)
        return result

    raise ValueError(f"Invalid sample type: {sample}")


def filter_by_sample(
    df: pd.DataFrame,
    sample: Optional[Union[str, SampleType, List[Union[str, SampleType]]]] = None,
    er30001_col: str = "ER30001",
    add_column: bool = True,
) -> pd.DataFrame:
    """Filter DataFrame by PSID sample type.

    Args:
        df: DataFrame with ER30001 column
        sample: Sample type(s) to include. Can be:
            - String: "SRC", "SEO", "IMMIGRANT"
            - SampleType enum
            - List of strings or SampleType
            - None to include all
        er30001_col: Column name for 1968 Interview Number
        add_column: Add 'sample_type' column to output

    Returns:
        Filtered DataFrame

    Example:
        >>> filtered = filter_by_sample(df, sample="SRC")
        >>> filtered = filter_by_sample(df, sample=["SRC", "SEO"])
    """
    df = df.copy()

    # Add sample type column
    if add_column or sample is not None:
        df["sample_type"] = df[er30001_col].apply(
            lambda x: get_sample_type(int(x)).value
        )

    # Filter if sample specified
    sample_types = _parse_sample_arg(sample)
    if sample_types is not None:
        sample_values = [s.value for s in sample_types]
        df = df[df["sample_type"].isin(sample_values)]

    return df
