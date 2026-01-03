"""Tests for variable crosswalk."""

import pytest
from psid.variables import (
    FamilyVars,
    IndividualVars,
    get_crosswalk,
    search_variables,
    describe,
    COMMON_VARIABLES,
)


class TestFamilyVars:
    def test_basic_creation(self):
        specs = {
            "income": {2019: "ER77448", 2021: "ER81775"},
            "wealth": {2019: "ER77511", 2021: "ER81850"},
        }
        fam_vars = FamilyVars(specs)

        assert fam_vars.names == ["income", "wealth"]
        assert fam_vars.get_codes(2019) == {"income": "ER77448", "wealth": "ER77511"}
        assert fam_vars.get_codes(2021) == {"income": "ER81775", "wealth": "ER81850"}

    def test_missing_year(self):
        specs = {"income": {2019: "ER77448"}}
        fam_vars = FamilyVars(specs)

        assert fam_vars.get_codes(2019) == {"income": "ER77448"}
        assert fam_vars.get_codes(2021) == {}  # Not available

    def test_get_columns(self):
        specs = {"income": {2019: "ER77448", 2021: "ER81775"}}
        fam_vars = FamilyVars(specs)

        assert fam_vars.get_columns(2019) == ["ER77448"]
        assert fam_vars.get_columns(2021) == ["ER81775"]


class TestCrosswalk:
    def test_get_crosswalk_all_years(self):
        codes = get_crosswalk("total_family_income")
        assert len(codes) > 40  # Available since 1968
        assert 1968 in codes
        assert 2021 in codes

    def test_get_crosswalk_specific_years(self):
        codes = get_crosswalk("total_family_income", years=[2019, 2021])
        assert codes == {2019: "ER77448", 2021: "ER81775"}

    def test_unknown_variable(self):
        with pytest.raises(ValueError, match="not in crosswalk"):
            get_crosswalk("unknown_variable")


class TestSearch:
    def test_search_by_keyword(self):
        results = search_variables("income")
        assert "total_family_income" in results
        assert "head_labor_income" in results

    def test_search_by_category(self):
        results = search_variables(category="wealth")
        assert "total_wealth" in results
        assert "total_family_income" not in results

    def test_search_combined(self):
        results = search_variables("labor", category="income")
        assert "head_labor_income" in results
        assert "total_family_income" not in results


class TestDescribe:
    def test_describe_variable(self):
        info = describe("total_family_income")

        assert info["name"] == "total_family_income"
        assert info["category"] == "income"
        assert "description" in info
        assert "available_years" in info
        assert 2021 in info["available_years"]

    def test_describe_unknown(self):
        with pytest.raises(ValueError, match="not found"):
            describe("unknown_variable")
