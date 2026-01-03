# psid Documentation

Python package for working with PSID (Panel Study of Income Dynamics) data.

## Guides

| Guide | Description |
|-------|-------------|
| [Quickstart](quickstart.md) | Get started in 5 minutes |
| [Data Structure](data_structure.md) | Understanding PSID's file format |
| [Variable Crosswalk](crosswalk.md) | Finding variable codes across years |
| [Household Transitions](transitions.md) | Detecting life events (marriage, divorce, etc.) |

## Reference

| Reference | Description |
|-----------|-------------|
| [API Reference](api.md) | Complete function documentation |
| [Comparison with psidR](comparison_psidr.md) | Feature comparison with R package |

## Quick Links

- **GitHub**: https://github.com/CosilicoAI/psid
- **PSID Website**: https://psidonline.isr.umich.edu
- **PSID Data Center**: https://simba.isr.umich.edu

## Installation

```bash
pip install psid
```

## Example

```python
import psid

# Define variables
family_vars = psid.FamilyVars({
    "income": psid.get_crosswalk("total_family_income", years=[2019, 2021]),
    "wealth": psid.get_crosswalk("total_wealth", years=[2019, 2021]),
})

# Build panel
panel = psid.build_panel(
    data_dir="./data",
    years=[2019, 2021],
    family_vars=family_vars,
)

# Analyze household transitions
transitions = psid.get_household_transitions(panel)
print(psid.summarize_transitions(transitions))
```

## Key Features

### 1. Built-in Variable Crosswalk

PSID codes vary by year. We include a crosswalk:

```python
psid.get_crosswalk("total_family_income", years=[2019, 2021])
# {2019: 'ER77448', 2021: 'ER81775'}

psid.search_variables("income")
# ['total_family_income', 'head_labor_income', 'wife_labor_income']
```

### 2. Household Transition Detection

Track life events - the main value-add over psidR:

```python
transitions = psid.get_household_transitions(panel)

marriages = transitions[transitions["type"] == "marriage"]
divorces = transitions[transitions["type"] == "divorce"]
```

### 3. Stable Person IDs

Consistent tracking across 50+ years:

```python
person_id = ER30001 * 1000 + ER30002  # Never changes
```

### 4. Panel Utilities

```python
# Cross-sections
cross_2021 = panel.to_cross_section(year=2021)

# Balanced panel
balanced = panel.balanced(years=[2017, 2019, 2021])

# Income transitions
trans = panel.get_transitions(["income"])
```

## Why psid over psidR?

| Feature | psid (Python) | psidR (R) |
|---------|--------------|-----------|
| Household transitions | ✅ | ❌ |
| Built-in crosswalk | ✅ | ❌ |
| Variable search | ✅ | ❌ |
| Sample filtering (SRC/SEO/Immigrant) | ✅ | ✅ |
| Minimum periods filtering | ✅ | ✅ |
| Stata .dta support | ✅ | ❌ |
| Direct download | ❌ | ✅ |

See [full comparison](comparison_psidr.md).
