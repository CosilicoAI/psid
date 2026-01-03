# Quickstart Guide

This guide walks through the basics of using the `psid` package to work with Panel Study of Income Dynamics data.

## Installation

```bash
pip install psid
```

## Step 1: Get PSID Data

PSID data requires free registration:

1. Go to https://psidonline.isr.umich.edu
2. Create an account (institutional email recommended)
3. Use the **Data Center** to select variables
4. Download as **Stata (.dta)** format

### Recommended Downloads

For panel analysis, you'll need:

| File | Description |
|------|-------------|
| `FAM{YEAR}ER.dta` | Family file for each year (e.g., FAM2019ER.dta) |
| `IND{YEAR}ER.dta` | Individual file (cumulative, one file covers all years) |
| `WLT{YEAR}ER.dta` | Wealth supplement (optional, available 1984+) |

Place files in a `data/` directory.

## Step 2: Define Variables

PSID variables have different codes each year. Use `FamilyVars` to specify:

```python
import psid

# Define variables with year-specific codes
family_vars = psid.FamilyVars({
    "income": {
        2017: "ER71426",
        2019: "ER77448",
        2021: "ER81775",
    },
    "wealth": {
        2017: "ER71485",
        2019: "ER77511",
        2021: "ER81850",
    },
    "family_size": {
        2017: "ER71012",
        2019: "ER77064",
        2021: "ER81389",
    },
})
```

### Finding Variable Codes

Use the built-in crosswalk for common variables:

```python
# Look up codes
psid.get_crosswalk("total_family_income", years=[2019, 2021])
# {2019: 'ER77448', 2021: 'ER81775'}

# Search for variables
psid.search_variables("income")
# ['total_family_income', 'head_labor_income', 'wife_labor_income']

# Get full info
psid.describe("total_family_income")
```

For variables not in the crosswalk, use PSID's online codebook.

## Step 3: Build Panel

```python
panel = psid.build_panel(
    data_dir="./data",
    years=[2017, 2019, 2021],
    family_vars=family_vars,
    heads_only=False,  # Include all family members
    balanced=False,    # Include all observations
)

print(f"{panel.n_individuals} individuals × {panel.n_years} years")
# 9,000 individuals × 3 years
```

### Panel Options

| Option | Description |
|--------|-------------|
| `heads_only=True` | Only household heads (sequence number = 1) |
| `balanced=True` | Only individuals observed in all years |

## Step 4: Analyze Data

### Cross-Section

```python
# Get single year
cross_2021 = panel.to_cross_section(year=2021)

# Most recent observation per person
latest = panel.to_cross_section()
```

### Transitions

```python
# Income changes between waves
transitions = panel.get_transitions(["income", "wealth"])

# Returns: person_id, year_t, year_t1, income_t, income_t1, wealth_t, wealth_t1
transitions["income_change"] = transitions["income_t1"] - transitions["income_t"]
```

### Individual Trajectories

```python
# Get one person's full history
person = panel.get_individual(person_id=1001002)
print(person[["year", "income", "wealth"]])
```

## Step 5: Household Transitions

The key feature - detect when people change households:

```python
# Extract all transitions
transitions = psid.get_household_transitions(panel)

# Filter by type
marriages = transitions[transitions["type"] == "marriage"]
divorces = transitions[transitions["type"] == "divorce"]
splitoffs = transitions[transitions["type"] == "leave_parental"]

# Summary
print(psid.summarize_transitions(transitions))
```

### Transition Types

| Type | Description |
|------|-------------|
| `same_household` | No change |
| `marriage` | Got married, joined/formed household |
| `divorce` | Got divorced, left household |
| `widowhood` | Spouse died |
| `leave_parental` | Child left parental home |
| `splitoff` | Other family member left |
| `join_household` | Moved into existing household |

## Complete Example

```python
import psid
import pandas as pd

# 1. Define variables
family_vars = psid.FamilyVars({
    "income": psid.get_crosswalk("total_family_income", years=[2017, 2019, 2021]),
    "wealth": psid.get_crosswalk("total_wealth", years=[2017, 2019, 2021]),
})

# 2. Build panel
panel = psid.build_panel(
    data_dir="./data",
    years=[2017, 2019, 2021],
    family_vars=family_vars,
)

# 3. Get transitions
hh_trans = psid.get_household_transitions(panel)
inc_trans = panel.get_transitions(["income"])

# 4. Analyze
# Marriage rate by age
hh_trans["age_group"] = (hh_trans["age_from"] // 10) * 10
marriage_rates = (
    hh_trans[hh_trans["type"] == "marriage"]
    .groupby("age_group")
    .size()
    / hh_trans.groupby("age_group").size()
)

# Income mobility
inc_trans["quintile_t"] = pd.qcut(inc_trans["income_t"], 5, labels=False)
inc_trans["quintile_t1"] = pd.qcut(inc_trans["income_t1"], 5, labels=False)
mobility_matrix = pd.crosstab(
    inc_trans["quintile_t"],
    inc_trans["quintile_t1"],
    normalize="index"
)
```

## Next Steps

- [Data Structure](data_structure.md) - Understanding PSID's file format
- [Variable Crosswalk](crosswalk.md) - Complete list of common variables
- [Household Transitions](transitions.md) - Detailed transition analysis
- [API Reference](api.md) - Full function documentation
