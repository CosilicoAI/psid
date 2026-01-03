# Comparison with psidR (R package)

This document compares the Python `psid` package with the R `psidR` package.

## Feature Comparison

| Feature | psid (Python) | psidR (R) | Notes |
|---------|--------------|-----------|-------|
| **Panel Building** |
| Build panel from files | ✅ | ✅ | Core feature |
| Merge family + individual files | ✅ | ✅ | Via interview number |
| Stable person ID | ✅ | ✅ | `ER30001 * 1000 + ER30002` |
| Multiple years | ✅ | ✅ | |
| **Data Input** |
| Stata .dta files | ✅ | ❌ | psidR uses .rda/.RData |
| R .rda/.RData files | ❌ | ✅ | |
| Parquet files | ✅ | ❌ | Python ecosystem |
| ASCII fixed-width | ❌ | ✅ | Via SAScii |
| Direct download from PSID | ❌ | ✅ | Requires credentials |
| **Variable Specification** |
| Year-specific codes | ✅ | ✅ | Both require crosswalk |
| Built-in crosswalk | ✅ | ❌ | psidR relies on user lookup |
| Variable search | ✅ | ❌ | `search_variables()` |
| **Sample Selection** |
| Heads only | ✅ | ✅ | `heads.only` parameter |
| Current heads only | ❌ | ✅ | Distinguishes movers |
| Sample type (SRC/SEO) | ❌ | ✅ | Filter by sample origin |
| Immigrant sample | ❌ | ✅ | |
| **Panel Design** |
| Balanced panel | ✅ | ✅ | All years required |
| Unbalanced panel | ✅ | ✅ | Any observations |
| Minimum periods | ❌ | ✅ | Integer design option |
| **Output** |
| pandas DataFrame | ✅ | N/A | |
| data.table | N/A | ✅ | |
| **Additional Features** |
| Household transitions | ✅ | ❌ | **Unique to psid** |
| Transition classification | ✅ | ❌ | Marriage, divorce, etc. |
| Transition rates | ✅ | ❌ | By age, year, etc. |
| Cross-section extraction | ✅ | ❌ | `to_cross_section()` |
| Individual trajectory | ✅ | ❌ | `get_individual()` |
| Wealth supplements | ✅ | ⚠️ | Disabled in recent psidR |

### Legend
- ✅ Supported
- ❌ Not supported
- ⚠️ Partial/deprecated

## Key Differences

### 1. Data Download

**psidR**: Can download directly from PSID servers (requires credentials)
```r
build.panel(datadir="~/data", ...)  # Downloads if not present
```

**psid**: Requires manual download from PSID website
```python
# User must download from psidonline.isr.umich.edu first
panel = psid.build_panel(data_dir="./data", ...)
```

**Why**: PSID requires agreeing to terms of use. We chose not to automate this.

### 2. File Format

**psidR**: Uses R-native formats (.rda, .RData), downloads ASCII and converts
**psid**: Uses Stata .dta (most common download format) or Parquet

### 3. Variable Crosswalk

**psidR**: User must look up codes in PSID documentation
```r
fam.vars <- data.frame(
  year = c(2019, 2021),
  income = c("ER77448", "ER81775")  # User looks these up
)
```

**psid**: Built-in crosswalk for common variables
```python
# Automatic lookup
codes = psid.get_crosswalk("total_family_income", years=[2019, 2021])
# Or search
psid.search_variables("income")
```

### 4. Household Transitions (psid only)

**psid** adds transition detection not available in psidR:

```python
transitions = psid.get_household_transitions(panel)

# Classify transitions
marriages = transitions[transitions["type"] == "marriage"]
divorces = transitions[transitions["type"] == "divorce"]
splitoffs = transitions[transitions["type"] == "leave_parental"]

# Compute rates
rates = psid.compute_transition_rates(transitions, by=["age_from"])
```

This is the main value-add for dynamic microsimulation use cases.

### 5. Sample Selection

**psidR**: Comprehensive sample filtering
```r
build.panel(..., sample="SRC", heads.only=TRUE, current.heads.only=TRUE)
```

**psid**: Basic filtering (heads only)
```python
psid.build_panel(..., heads_only=True)
```

We don't yet support:
- `sample` filtering (SRC vs SEO vs immigrant)
- `current.heads.only` (distinguishes movers from always-heads)

## Migration from psidR

If you're migrating from psidR:

### 1. Convert data files

```python
# Option A: Use Stata files directly (recommended)
# Download .dta from PSID, use as-is

# Option B: Convert .rda to parquet (one-time)
# In R:
library(arrow)
load("family2019.rda")
write_parquet(family2019, "family2019.parquet")
```

### 2. Translate variable specification

```r
# psidR
fam.vars <- data.frame(
  year = c(2019, 2021),
  income = c("ER77448", "ER81775"),
  wealth = c("ER77511", "ER81850")
)
```

```python
# psid
family_vars = psid.FamilyVars({
    "income": {2019: "ER77448", 2021: "ER81775"},
    "wealth": {2019: "ER77511", 2021: "ER81850"},
})
```

### 3. Translate build call

```r
# psidR
panel <- build.panel(
  datadir = "~/data",
  fam.vars = fam.vars,
  heads.only = TRUE,
  design = "balanced"
)
```

```python
# psid
panel = psid.build_panel(
    data_dir="./data",
    years=[2019, 2021],
    family_vars=family_vars,
    heads_only=True,
    balanced=True,
)
```

## Roadmap: Planned Features

Features we plan to add for full parity:

1. **Sample filtering** - `sample="SRC"` option
2. **Current heads only** - Distinguish current from former heads
3. **Minimum periods** - `design=3` for at least 3 consecutive years
4. **Direct download** - Authenticated download from PSID (optional)

Contributions welcome at https://github.com/CosilicoAI/psid
