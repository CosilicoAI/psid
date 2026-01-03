# Variable Crosswalk

PSID variables have different codes each year. This document lists common variables with their year-specific codes.

## Using the Crosswalk

```python
import psid

# Get codes for specific years
codes = psid.get_crosswalk("total_family_income", years=[2019, 2021])
# {2019: 'ER77448', 2021: 'ER81775'}

# Search for variables
psid.search_variables("income")
# ['total_family_income', 'head_labor_income', 'wife_labor_income']

# Filter by category
psid.search_variables(category="wealth")
# ['total_wealth']

# Get full info
info = psid.describe("total_family_income")
# {'name': 'total_family_income',
#  'description': 'Total family money income',
#  'category': 'income',
#  'available_years': [1968, 1969, ..., 2021]}
```

## Income Variables

### Total Family Income

Total money income of all family members.

| Year | Code | Year | Code |
|------|------|------|------|
| 2021 | ER81775 | 1992 | V22406 |
| 2019 | ER77448 | 1991 | V21481 |
| 2017 | ER71426 | 1990 | V20651 |
| 2015 | ER65349 | 1989 | V17533 |
| 2013 | ER58152 | 1988 | V16144 |
| 2011 | ER52343 | 1987 | V14670 |
| 2009 | ER46935 | 1986 | V13623 |
| 2007 | ER41027 | 1985 | V12371 |
| 2005 | ER28037 | 1984 | V11022 |
| 2003 | ER24099 | 1983 | V10419 |
| 2001 | ER20456 | 1982 | V8689 |
| 1999 | ER16462 | 1981 | V8065 |
| 1997 | ER12079 | 1980 | V7412 |
| 1996 | ER9244 | 1979 | V6766 |
| 1995 | ER6993 | 1978 | V6173 |
| 1994 | ER4153 | 1977 | V5626 |
| 1993 | V23322 | 1976 | V5029 |

### Head's Labor Income

Labor income of household head.

| Year | Code |
|------|------|
| 2021 | ER81711 |
| 2019 | ER77384 |
| 2017 | ER71330 |
| 2015 | ER65253 |
| 2013 | ER58056 |
| 2011 | ER52247 |

### Wife/Partner's Labor Income

Labor income of spouse/partner.

| Year | Code |
|------|------|
| 2021 | ER81743 |
| 2019 | ER77416 |
| 2017 | ER71362 |
| 2015 | ER65285 |
| 2013 | ER58088 |
| 2011 | ER52279 |

## Wealth Variables

### Total Wealth

Total family wealth (assets minus debts).

| Year | Code |
|------|------|
| 2021 | ER81850 |
| 2019 | ER77511 |
| 2017 | ER71485 |
| 2015 | ER65408 |
| 2013 | ER58211 |
| 2011 | ER52394 |
| 2009 | ER46970 |
| 2007 | ER46938 |
| 2005 | S817 |
| 2003 | S617 |
| 2001 | S417 |
| 1999 | S317 |
| 1994 | S117 |
| 1989 | S117 |
| 1984 | S117 |

Note: Wealth supplements before 2005 have different variable naming.

## Demographics

### Age of Head

| Year | Code |
|------|------|
| 2021 | ER81394 |
| 2019 | ER77069 |
| 2017 | ER71017 |
| 2015 | ER64943 |
| 2013 | ER57739 |
| 2011 | ER51904 |
| 2009 | ER46543 |
| 2007 | ER40565 |
| 2005 | ER27393 |
| 2003 | ER23426 |
| 2001 | ER19989 |
| 1999 | ER15928 |
| 1997 | ER11760 |

### Family Size

Number of persons in family unit.

| Year | Code |
|------|------|
| 2021 | ER81389 |
| 2019 | ER77064 |
| 2017 | ER71012 |
| 2015 | ER64938 |
| 2013 | ER57734 |
| 2011 | ER51899 |
| 2009 | ER46538 |
| 2007 | ER40560 |
| 2005 | ER27388 |
| 2003 | ER23421 |
| 2001 | ER19984 |
| 1999 | ER15923 |
| 1997 | ER11755 |

### Marital Status of Head

| Year | Code |
|------|------|
| 2021 | ER81395 |
| 2019 | ER77070 |
| 2017 | ER71018 |
| 2015 | ER64944 |
| 2013 | ER57740 |
| 2011 | ER51905 |
| 2009 | ER46544 |
| 2007 | ER40566 |
| 2005 | ER27394 |
| 2003 | ER23427 |
| 2001 | ER19990 |
| 1999 | ER15929 |
| 1997 | ER11761 |

Marital status codes:
- 1 = Married
- 2 = Never married
- 3 = Widowed
- 4 = Divorced
- 5 = Separated

## Weights

### Family Weight

| Year | Code |
|------|------|
| 2021 | ER81856 |
| 2019 | ER77516 |
| 2017 | ER71538 |
| 2015 | ER65462 |
| 2013 | ER58257 |
| 2011 | ER52436 |
| 2009 | ER47012 |
| 2007 | ER41069 |
| 2005 | ER28078 |
| 2003 | ER24180 |
| 2001 | ER20459 |
| 1999 | ER16519 |
| 1997 | ER12223 |

## Individual File Columns

These columns are in the **individual file** and have different patterns.

### Interview Number (links to family file)

| Year | Code | Year | Code |
|------|------|------|------|
| 2021 | ER34501 | 1985 | ER30052 |
| 2019 | ER34301 | 1984 | ER30020 |
| 2017 | ER34101 | 1983 | V9071 |
| 2015 | ER33901 | 1982 | V8691 |
| 2013 | ER33701 | 1981 | V8351 |
| 2011 | ER33501 | 1980 | V7971 |
| 2009 | ER33401 | 1979 | V7571 |
| 2007 | ER33301 | 1978 | V7171 |
| 2005 | ER33201 | 1977 | V6771 |
| 2003 | ER33101 | 1976 | V6171 |
| 2001 | ER33001 | 1975 | V5571 |
| 1999 | ER32001 | 1974 | V4671 |
| 1997 | ER30806 | 1973 | V4171 |
| 1996 | ER30733 | 1972 | V3171 |
| 1995 | ER30657 | 1971 | V2571 |
| 1994 | ER30570 | 1970 | V1971 |
| 1993 | ER30498 | 1969 | V1471 |
| 1992 | ER30429 | 1968 | ER30001 |
| 1991 | ER30373 | | |
| 1990 | ER30313 | | |
| 1989 | ER30246 | | |
| 1988 | ER30188 | | |
| 1987 | ER30138 | | |
| 1986 | ER30091 | | |

### Core ID Columns (unchanging)

| Column | Description |
|--------|-------------|
| ER30001 | 1968 Interview Number |
| ER30002 | Person Number (sequence in 1968 family) |

## Adding Custom Variables

For variables not in the built-in crosswalk:

```python
# 1. Look up codes in PSID Data Center
#    https://simba.isr.umich.edu/

# 2. Create FamilyVars with your codes
my_vars = psid.FamilyVars({
    "food_stamps": {
        2019: "ER77599",
        2021: "ER81924",
    },
    "house_value": {
        2019: "ER77100",
        2021: "ER81425",
    },
})

# 3. Use in build_panel
panel = psid.build_panel(
    data_dir="./data",
    years=[2019, 2021],
    family_vars=my_vars,
)
```

## PSID Data Center

For complete variable documentation:

1. Go to https://simba.isr.umich.edu/
2. Use "Variable Search" or browse by topic
3. The "Cross-Year Index" shows codes across years
4. Download codebook PDFs for detailed definitions
