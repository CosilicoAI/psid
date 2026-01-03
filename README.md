# psid

Python package for working with PSID (Panel Study of Income Dynamics) data.

PSID is the longest-running longitudinal household survey in the world, following families since 1968. This package provides tools to build panels and analyze household transitions—the key feature that makes PSID valuable for dynamic microsimulation.

## Installation

```bash
pip install psid
```

## Data Access

PSID data requires free registration at https://psidonline.isr.umich.edu

1. Create an account at the link above
2. That's it! The package will download data automatically

## Quick Start

```python
import psid

# Define variables to extract (codes vary by year)
family_vars = psid.FamilyVars({
    "income": {2019: "ER77448", 2021: "ER81775"},
    "wealth": {2019: "ER77511", 2021: "ER81850"},
    "family_size": {2019: "ER77064", 2021: "ER81389"},
})

# Build panel - auto-downloads missing files!
panel = psid.build_panel(
    data_dir="./psid_data",
    years=[2019, 2021],
    family_vars=family_vars,
)
# Will prompt for PSID username/password if files not found locally

print(f"{panel.n_individuals} individuals × {panel.n_years} years")
# 9,000 individuals × 2 years

# Get transitions for modeling
transitions = panel.get_transitions(["income", "wealth"])
```

## Downloading Data

The package can automatically download PSID data files:

```python
import psid

# Download specific years (prompts for credentials)
psid.download(
    years=[2019, 2021],
    data_dir="./psid_data",
)

# Or provide credentials directly
psid.download(
    years=[2019, 2021],
    data_dir="./psid_data",
    username="your_username",
    password="your_password",
    include_wealth=True,  # Also download wealth supplements
)

# build_panel also auto-downloads if files are missing
panel = psid.build_panel("./psid_data", years=[2019, 2021])

# Skip auto-download (use local files only)
panel = psid.build_panel("./psid_data", years=[2019], download=False)
```

## Household Transitions

The key feature of this package is extracting household transition events:

```python
# Extract all household transitions
transitions = psid.get_household_transitions(panel)

# Filter by type
marriages = transitions[transitions["type"] == "marriage"]
divorces = transitions[transitions["type"] == "divorce"]
splitoffs = transitions[transitions["type"] == "leave_parental"]

# Compute transition rates by age
rates = psid.compute_transition_rates(
    transitions,
    by=["age_from"]
)

# Summary statistics
print(psid.summarize_transitions(transitions))
```

### Transition Types

| Type | Description |
|------|-------------|
| `same_household` | No household change |
| `marriage` | Person married and joined/formed household |
| `divorce` | Person divorced and left household |
| `widowhood` | Spouse died |
| `leave_parental` | Child left parental home |
| `splitoff` | Other family member left to form new household |
| `join_household` | Person joined existing household |

## Variable Crosswalk

PSID variables have different codes each year. Use the crosswalk:

```python
# Look up a variable
psid.get_crosswalk("total_family_income", years=[2019, 2021])
# {2019: 'ER77448', 2021: 'ER81775'}

# Search for variables
psid.search_variables("income")
# ['total_family_income', 'head_labor_income', 'wife_labor_income']

psid.search_variables(category="wealth")
# ['total_wealth']

# Get full variable info
psid.describe("total_family_income")
# {'name': 'total_family_income',
#  'description': 'Total family money income',
#  'category': 'income',
#  'available_years': [1968, 1969, ..., 2021]}
```

## Panel Data Utilities

```python
# Get cross-section (one row per person)
cross_2021 = panel.to_cross_section(year=2021)
latest = panel.to_cross_section()  # Most recent observation

# Filter to balanced panel
balanced = panel.balanced(years=[2017, 2019, 2021])

# Get individual trajectory
person = panel.get_individual(person_id=1001002)

# Summary by year
panel.summary()
```

## Data Structure

### Person ID

PSID tracks individuals using a stable person ID:

```
person_id = ER30001 * 1000 + ER30002
```

Where:
- `ER30001` = 1968 Interview Number (baseline family ID)
- `ER30002` = Person Number within that family

This ID remains stable even when:
- Person moves to new household
- Person gets married/divorced
- Family "splits off" (child leaves home)

### File Types

| File | Description |
|------|-------------|
| Family (`FAM{YEAR}ER.dta`) | Household-level data, one row per interview |
| Individual (`IND{YEAR}ER.dta`) | Person-level, cumulative across all years |
| Wealth (`WLT{YEAR}ER.dta`) | Wealth supplement (1984, 1989, 1994, 1999+) |

## Comparison to psidr (R)

This package is inspired by [psidR](https://github.com/floswald/psidR) but designed for Python workflows, with a focus on:

1. **Household transitions** - First-class support for extracting and classifying transition events
2. **Variable crosswalk** - Built-in mapping of common variables across years
3. **Panel utilities** - Get transitions, balanced panels, cross-sections
4. **Modern Python** - Type hints, dataclasses, pandas integration

## Use Cases

### Dynamic Microsimulation

PSID's longitudinal structure enables modeling:
- Marriage/divorce rates by age and income
- Household formation (children leaving home)
- Income and wealth transitions

```python
# Get transition probabilities for microsimulation
transitions = psid.get_household_transitions(panel)

# Compute P(marriage | age, income) by fitting a model
from sklearn.linear_model import LogisticRegression
X = transitions[["age_from", "income_from"]]
y = (transitions["type"] == "marriage").astype(int)
model = LogisticRegression().fit(X, y)
```

### Wealth Dynamics

```python
# Track wealth changes over time
wealth_transitions = panel.get_transitions(["wealth"])
wealth_transitions["wealth_change"] = (
    wealth_transitions["wealth_t1"] - wealth_transitions["wealth_t"]
)
```

## License

MIT
