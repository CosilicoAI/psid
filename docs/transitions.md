# Household Transitions Guide

Detecting and analyzing household transitions is a key feature of the `psid` package—and the main value-add over psidR.

## Why Transitions Matter

PSID's longitudinal design allows tracking when people:
- Get married or divorced
- Leave their parents' home
- Move in with others
- Experience widowhood

These transitions are crucial for:
- **Dynamic microsimulation**: Model P(marriage | age, income)
- **Life course research**: Understand timing of life events
- **Policy analysis**: Effects of policies on family formation

## Quick Start

```python
import psid

# Build panel
panel = psid.build_panel(
    data_dir="./data",
    years=[2017, 2019, 2021],
    family_vars=family_vars,
)

# Extract transitions
transitions = psid.get_household_transitions(panel)

# Summary
print(psid.summarize_transitions(transitions))
```

Output:
```
                    count  pct_hh_changed  mean_age  pct_of_total
type
same_household      15234           0.00      45.2         0.847
marriage              412           1.00      28.5         0.023
divorce               289           1.00      42.1         0.016
leave_parental        567           1.00      22.4         0.032
splitoff              198           1.00      31.2         0.011
...
```

## Transition Types

| Type | Description | Detection |
|------|-------------|-----------|
| `same_household` | No change | `hh_t == hh_t1` |
| `marriage` | Got married | Unmarried → married + new HH |
| `divorce` | Got divorced | Married → divorced + new HH |
| `widowhood` | Spouse died | Married → widowed + new HH |
| `leave_parental` | Left parents | Child → head of new HH |
| `splitoff` | Other splitoff | Non-head → head of new HH |
| `join_household` | Joined existing | Head → non-head in new HH |
| `other` | Unknown | HH changed, reason unclear |

## Filtering Transitions

```python
# By type
marriages = transitions[transitions["type"] == "marriage"]
divorces = transitions[transitions["type"] == "divorce"]

# By age
young_adult_transitions = transitions[
    (transitions["age_from"] >= 18) & (transitions["age_from"] <= 30)
]

# By year
recent = transitions[transitions["year_from"] >= 2015]

# Household changes only
hh_changes = transitions[transitions["hh_changed"]]
```

## Helper Functions

```python
# Pre-built filters
marriages = psid.get_marriage_events(transitions)
divorces = psid.get_divorce_events(transitions)
splitoffs = psid.get_splitoff_events(transitions)  # Includes leave_parental
```

## Computing Transition Rates

### Overall Rates

```python
rates = psid.compute_transition_rates(transitions)
print(rates)
```

```
                    count      rate
type
same_household      15234    0.8469
marriage              412    0.0229
divorce               289    0.0161
leave_parental        567    0.0315
...
```

### Rates by Group

```python
# By age group
transitions["age_group"] = (transitions["age_from"] // 10) * 10
rates_by_age = psid.compute_transition_rates(transitions, by=["age_group"])

# By year
rates_by_year = psid.compute_transition_rates(transitions, by=["year_from"])

# By multiple factors
rates_detailed = psid.compute_transition_rates(
    transitions,
    by=["age_group", "year_from"]
)
```

## Use in Microsimulation

### Training Transition Models

```python
from sklearn.linear_model import LogisticRegression

# Prepare features
X = transitions[["age_from", "income_from"]].dropna()
y = (transitions.loc[X.index, "type"] == "marriage").astype(int)

# Train model
model = LogisticRegression()
model.fit(X, y)

# Predict probability
def p_marriage(age, income):
    return model.predict_proba([[age, income]])[0, 1]

# Use in simulation
p_marriage(25, 50000)  # Probability of marriage for 25-year-old earning $50k
```

### Full Microsimulation Integration

```python
class HouseholdTransitionModel:
    """Model household transitions for microsimulation."""

    def __init__(self):
        self.models = {}

    def fit(self, transitions):
        """Train models for each transition type."""
        for event_type in ["marriage", "divorce", "leave_parental"]:
            X = transitions[["age_from", "income_from", "family_size"]].dropna()
            y = (transitions.loc[X.index, "type"] == event_type).astype(int)

            self.models[event_type] = LogisticRegression()
            self.models[event_type].fit(X, y)

    def predict_probs(self, person_state):
        """Predict transition probabilities for a person."""
        X = [[
            person_state["age"],
            person_state["income"],
            person_state["family_size"],
        ]]
        return {
            event: model.predict_proba(X)[0, 1]
            for event, model in self.models.items()
        }

# Usage
model = HouseholdTransitionModel()
model.fit(transitions)

probs = model.predict_probs({
    "age": 25,
    "income": 50000,
    "family_size": 1,
})
# {'marriage': 0.15, 'divorce': 0.0, 'leave_parental': 0.02}
```

## Working with Columns

The transitions DataFrame includes:

| Column | Description |
|--------|-------------|
| `person_id` | Stable person identifier |
| `year_from` | Starting year |
| `year_to` | Ending year |
| `type` | Transition type |
| `hh_from` | Interview number (HH) before |
| `hh_to` | Interview number (HH) after |
| `relationship_from` | Relationship to head before |
| `relationship_to` | Relationship to head after |
| `marital_from` | Marital status before |
| `marital_to` | Marital status after |
| `age_from` | Age at start |
| `age_to` | Age at end |
| `hh_changed` | Boolean: did household change? |

## Marital Status Codes

| Code | Meaning |
|------|---------|
| 1 | Married |
| 2 | Never married |
| 3 | Widowed |
| 4 | Divorced |
| 5 | Separated |

## Relationship Codes

| Code | Meaning |
|------|---------|
| 1 | Head |
| 2 | Spouse/Partner |
| 3 | Child |
| 4 | Sibling |
| 5 | Parent |
| 6 | Grandchild |
| 7 | Other relative |
| 8 | Nonrelative |

## Advanced: Custom Classification

Override the default classification logic:

```python
def my_classify_transition(row):
    """Custom transition classification."""
    if row["hh_from"] == row["hh_to"]:
        return "same"

    # Custom logic for cohabitation
    if (row["relationship_from"] != 2 and
        row["relationship_to"] == 2 and
        row["marital_to"] != 1):  # Partner, not married
        return "cohabitation"

    # Fall back to defaults
    return psid.transitions._classify_transition(
        row["hh_from"], row["hh_to"],
        row["relationship_from"], row["relationship_to"],
        row["marital_from"], row["marital_to"],
        row["age_from"], row["age_to"],
    ).value

# Apply
transitions["my_type"] = transitions.apply(my_classify_transition, axis=1)
```

## Limitations

### Timing Uncertainty

PSID is biennial since 1997. A transition observed between 2019 and 2021
could have occurred in 2019, 2020, or 2021.

For annual transitions, consider:
- Using pre-1997 data (annual)
- Interpolation/modeling
- Combining with other data sources

### Classification Uncertainty

Some transitions are ambiguous:
- Multiple events between waves (marriage then divorce)
- Data quality issues (missing codes)
- Complex household changes

Check the `other` category for cases that don't fit standard patterns.

### Sample Size

Transition events are relatively rare. For reliable rate estimates:
- Use multiple years
- Aggregate age groups
- Consider pooling similar transitions
