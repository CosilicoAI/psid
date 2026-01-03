# PSID Data Structure

Understanding how PSID organizes its data is crucial for effective use.

## Survey Design

PSID is the longest-running longitudinal household survey:

- **Started**: 1968
- **Frequency**: Annual (1968-1996), Biennial (1997-present)
- **Sample**: ~5,000 families in 1968, now ~10,000 families
- **Following rule**: Follows original 1968 families AND all "splitoffs"

### What Makes PSID Special

Unlike cross-sectional surveys (CPS) or short panels (SIPP ~4 years), PSID:

1. **Follows people for life** - Someone born in 1968 can be tracked to present
2. **Follows splitoffs** - When children leave home, they become new sample families
3. **Tracks household changes** - Marriage, divorce, cohabitation all recorded

## File Types

### Family File (`FAM{YEAR}ER.dta`)

One record per **interview** (family unit) per year.

```
Interview  Year  Income    Wealth    FamilySize
1001       2019  $75,000   $150,000  4
1002       2019  $45,000   $25,000   2
1003       2019  $120,000  $500,000  3
```

Key characteristics:
- Interview number changes when household composition changes
- Contains household-level aggregates
- Links to individuals via interview number

### Individual File (`IND{YEAR}ER.dta`)

One record per **person** ever in PSID, with columns for each year.

```
ID1968  PerNum  IntNum2017  IntNum2019  IntNum2021  Seq2019  Rel2019
1001    1       1001        1001        1001        1        1 (Head)
1001    2       1001        1001        1001        2        2 (Spouse)
1001    3       1001        1001        5005        1        1 (Head)  <- Splitoff!
1002    1       1002        1002        0           0        0         <- Attrition
```

Key columns:
- `ER30001`: 1968 Interview Number (baseline family ID)
- `ER30002`: Person Number within 1968 family
- `ER3XXXX`: Interview number for year XXXX
- Sequence and relationship codes for each year

### Wealth Supplement (`WLT{YEAR}ER.dta`)

Detailed asset/debt data, available:
- 1984, 1989, 1994 (every 5 years)
- 1999, 2001, 2003, ... (every 2 years with main survey)

## Person Identification

### The Person ID Formula

```python
person_id = ER30001 * 1000 + ER30002
```

Where:
- `ER30001` = 1968 Interview Number (which family in 1968)
- `ER30002` = Person Number (position within that family)

This ID is **permanent** - it never changes regardless of:
- Moving to new household
- Getting married/divorced
- Family "splitting off"

### Example

```
1968: Family 1001 has 4 members
  - Person 1001001: Head (age 35)
  - Person 1001002: Spouse (age 33)
  - Person 1001003: Child (age 10)
  - Person 1001004: Child (age 8)

2021: Same people, now in 3 households
  - Household A: 1001001 (age 88) - original head, now widowed
  - Household B: 1001003 (age 63) + spouse - child grew up, married
  - Household C: 1001004 (age 61) - other child, divorced

All still tracked with same person_id!
```

## Linking Files

### Family → Individual

```python
# For year 2019
individual_interview_col = "ER34301"  # Interview number in 2019

# Merge
merged = individual.merge(
    family_2019,
    left_on=individual_interview_col,
    right_on="interview_number"
)
```

### Across Years

The individual file already has interview numbers for all years:

```python
# Track person across years
person_history = individual[
    ["ER30001", "ER30002",  # ID
     "ER34101", "ER34301", "ER34501",  # Interview 2017, 2019, 2021
     "ER34102", "ER34302", "ER34502",  # Sequence 2017, 2019, 2021
    ]
]
```

## Relationship Codes

PSID tracks each person's relationship to the household head:

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
| 9 | Husband of head (rare) |

### Detecting Transitions

```python
# Person was child (3), now head (1) = left parental home
if rel_2019 == 3 and rel_2021 == 1:
    transition = "leave_parental"

# Person was head (1), now spouse (2) = joined partner's household
if rel_2019 == 1 and rel_2021 == 2:
    transition = "join_household"
```

## Sequence Numbers

Sequence indicates position within household:

| Sequence | Typical Meaning |
|----------|-----------------|
| 1 | Head |
| 2 | Spouse/Partner |
| 3+ | Children, others |

Sequence = 0 means **not in a PSID family that year** (attrition, institution, etc.)

## Sample Types

PSID has multiple sample components:

| Sample | Description |
|--------|-------------|
| SRC | Survey Research Center - original 1968 national sample |
| SEO | Survey of Economic Opportunity - low-income oversample |
| Immigrant | Added in 1997, 1999, 2017 to maintain representativeness |

For nationally representative analysis, use `heads_only=True` and apply weights.

## Common Gotchas

### 1. Interview Numbers Change

A person's interview number changes when:
- They move to a new household
- Household composition changes significantly
- They become head of a "splitoff" family

**Solution**: Always use `person_id` (ER30001 * 1000 + ER30002) for tracking.

### 2. Variable Names Change Every Year

`ER77448` in 2019 is `ER81775` in 2021 (both = total family income).

**Solution**: Use the crosswalk or `FamilyVars` specification.

### 3. Biennial Data Since 1997

Transitions span 2 years, not 1. A "divorce" in the 2019→2021 transition could have happened in 2019, 2020, or 2021.

**Solution**: Be aware of timing uncertainty in transition analysis.

### 4. Weights

Different weights for different analyses:
- Family weight: For household-level statistics
- Individual weight: For person-level statistics
- Longitudinal weight: For panel analysis

**Solution**: Check PSID documentation for appropriate weights.

## Memory Management

PSID files can be large (individual file ~500MB+). Tips:

```python
# Only load needed columns
family = psid.load_family(2019, columns=["ER77448", "ER77511"])

# Use parquet for faster repeated loading
df.to_parquet("family_2019.parquet")
df = pd.read_parquet("family_2019.parquet")
```
