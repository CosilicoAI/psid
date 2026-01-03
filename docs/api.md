# API Reference

## Panel Building

### `build_panel()`

Build longitudinal panel from PSID data files.

```python
psid.build_panel(
    data_dir: str,
    years: List[int],
    family_vars: Optional[FamilyVars] = None,
    individual_vars: Optional[IndividualVars] = None,
    heads_only: bool = False,
    balanced: bool = False,
    sample: Optional[Union[str, SampleType, List]] = None,
) -> Panel
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `data_dir` | str | Directory containing PSID files |
| `years` | List[int] | Survey years to include |
| `family_vars` | FamilyVars | Family-level variables to extract |
| `individual_vars` | IndividualVars | Individual-level variables |
| `heads_only` | bool | Only include household heads |
| `balanced` | bool | Only include individuals in all years |
| `sample` | str/SampleType/List | Sample type(s): "SRC", "SEO", "IMMIGRANT" |

**Returns:** `Panel` object

**Example:**
```python
panel = psid.build_panel(
    data_dir="./data",
    years=[2017, 2019, 2021],
    family_vars=family_vars,
    heads_only=True,
)
```

---

### `Panel` class

Panel data container with convenience methods.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `data` | DataFrame | Raw panel data |
| `n_individuals` | int | Number of unique individuals |
| `n_years` | int | Number of survey years |
| `years` | List[int] | Survey years in panel |
| `columns` | List[str] | Value columns (excluding ID/time) |

**Methods:**

#### `get_transitions(cols)`

Get transition data (current → next observation).

```python
panel.get_transitions(cols: List[str] = None) -> DataFrame
```

Returns DataFrame with: `person_id`, `year_t`, `year_t1`, `{col}_t`, `{col}_t1`

#### `to_cross_section(year)`

Get cross-section (one row per person).

```python
panel.to_cross_section(year: int = None) -> DataFrame
```

If `year` is None, returns most recent observation per person.

#### `get_individual(person_id)`

Get all observations for one individual.

```python
panel.get_individual(person_id: int) -> DataFrame
```

#### `balanced(years)`

Filter to individuals observed in all specified years.

```python
panel.balanced(years: List[int] = None) -> Panel
```

#### `min_periods(n)`

Filter to individuals with at least N observations (any years).

```python
panel.min_periods(n: int) -> Panel
```

Unlike `balanced()` which requires specific years, this just requires a minimum count.

#### `summary()`

Summary statistics by year.

```python
panel.summary() -> DataFrame
```

---

## Variable Specification

### `FamilyVars` class

Specify family-level variables across years.

```python
FamilyVars(specs: Dict[str, Dict[int, str]])
```

**Example:**
```python
family_vars = psid.FamilyVars({
    "income": {2019: "ER77448", 2021: "ER81775"},
    "wealth": {2019: "ER77511", 2021: "ER81850"},
})
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_codes(year)` | Dict[str, str] | Friendly name → PSID code |
| `get_columns(year)` | List[str] | List of PSID column names |
| `names` | List[str] | All friendly variable names |

### `IndividualVars` class

Specify individual-level variables. Same interface as `FamilyVars`.

---

### `get_crosswalk()`

Get variable code crosswalk.

```python
psid.get_crosswalk(
    variable: str,
    years: List[int] = None,
) -> Dict[int, str]
```

**Example:**
```python
psid.get_crosswalk("total_family_income", years=[2019, 2021])
# {2019: 'ER77448', 2021: 'ER81775'}
```

---

### `search_variables()`

Search for variables by keyword or category.

```python
psid.search_variables(
    keyword: str = "",
    category: str = None,
) -> List[str]
```

**Categories:** `income`, `wealth`, `demographics`, `weight`, `id`

**Example:**
```python
psid.search_variables("income")
# ['total_family_income', 'head_labor_income', 'wife_labor_income']

psid.search_variables(category="wealth")
# ['total_wealth']
```

---

### `describe()`

Get full information about a variable.

```python
psid.describe(variable: str) -> dict
```

**Returns:** Dict with `name`, `description`, `category`, `codes`, `available_years`

---

## Data Loading

### `load_family()`

Load PSID family file for a specific year.

```python
psid.load_family(
    year: int,
    data_dir: str = "./data",
    columns: List[str] = None,
) -> DataFrame
```

---

### `load_individual()`

Load PSID individual file.

```python
psid.load_individual(
    data_dir: str = "./data",
    years: List[int] = None,
    columns: List[str] = None,
) -> DataFrame
```

---

### `load_wealth()`

Load PSID wealth supplement.

```python
psid.load_wealth(
    year: int,
    data_dir: str = "./data",
    columns: List[str] = None,
) -> DataFrame
```

---

## Household Transitions

### `get_household_transitions()`

Extract household transition events from panel.

```python
psid.get_household_transitions(
    panel: Panel,
    interview_col: str = "interview_number",
    relationship_col: str = "relationship",
    marital_col: str = None,
    age_col: str = None,
) -> DataFrame
```

**Returns:** DataFrame with columns:
- `person_id`, `year_from`, `year_to`
- `type` (transition type)
- `hh_from`, `hh_to` (interview numbers)
- `relationship_from`, `relationship_to`
- `marital_from`, `marital_to`
- `age_from`, `age_to`
- `hh_changed` (boolean)

---

### `TransitionType` enum

Types of household transitions:

```python
class TransitionType(Enum):
    SAME_HOUSEHOLD = "same_household"
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    WIDOWHOOD = "widowhood"
    LEAVE_PARENTAL = "leave_parental"
    SPLITOFF = "splitoff"
    JOIN_HOUSEHOLD = "join_household"
    DEATH = "death"
    BIRTH = "birth"
    OTHER = "other"
```

---

### `compute_transition_rates()`

Compute transition rates by type.

```python
psid.compute_transition_rates(
    transitions_df: DataFrame,
    by: List[str] = None,
) -> DataFrame
```

If `by` is None, returns overall counts and rates.
If `by` is specified, returns rates grouped by those columns.

---

### `summarize_transitions()`

Summary statistics of transitions by type.

```python
psid.summarize_transitions(transitions_df: DataFrame) -> DataFrame
```

**Returns:** DataFrame with `count`, `pct_hh_changed`, `mean_age`, `pct_of_total`

---

### Helper Functions

```python
psid.get_marriage_events(transitions_df) -> DataFrame
psid.get_divorce_events(transitions_df) -> DataFrame
psid.get_splitoff_events(transitions_df) -> DataFrame
```

---

## Constants

### `COMMON_VARIABLES`

Dictionary of common PSID variables with crosswalk codes.

```python
psid.COMMON_VARIABLES["total_family_income"]
# {'description': 'Total family money income',
#  'category': 'income',
#  'codes': {2021: 'ER81775', 2019: 'ER77448', ...}}
```

Available variables:
- `total_family_income`
- `head_labor_income`
- `wife_labor_income`
- `total_wealth`
- `age_head`
- `family_size`
- `marital_status`
- `family_weight`

---

## Sample Filtering

PSID has multiple sample types determined by ER30001 (1968 Interview Number):
- **SRC**: Survey Research Center (original 1968 national probability sample)
- **SEO**: Survey of Economic Opportunity (low-income oversample)
- **IMMIGRANT**: Refresher samples (1997, 1999, 2017)

### `SampleType` enum

```python
class SampleType(Enum):
    SRC = "SRC"
    SEO = "SEO"
    IMMIGRANT = "IMMIGRANT"
    LATINO = "LATINO"
    UNKNOWN = "UNKNOWN"
```

### `get_sample_type()`

Determine sample type from ER30001.

```python
psid.get_sample_type(er30001: int) -> SampleType
```

**Example:**
```python
psid.get_sample_type(1500)  # SampleType.SRC
psid.get_sample_type(5500)  # SampleType.SEO
```

### `filter_by_sample()`

Filter DataFrame by sample type.

```python
psid.filter_by_sample(
    df: DataFrame,
    sample: Optional[Union[str, SampleType, List]] = None,
    er30001_col: str = "ER30001",
    add_column: bool = True,
) -> DataFrame
```

**Example:**
```python
# Filter to nationally representative SRC sample
filtered = psid.filter_by_sample(df, sample="SRC")

# Multiple samples
filtered = psid.filter_by_sample(df, sample=["SRC", "SEO"])
```

### `SAMPLE_RANGES`

Dictionary of ER30001 ranges for each sample type.

```python
psid.SAMPLE_RANGES
# {SampleType.SRC: [(1, 2999)],
#  SampleType.SEO: [(5001, 6872)],
#  SampleType.IMMIGRANT: [(3001, 3511), (4001, 4462), (7001, 9308)]}
```
