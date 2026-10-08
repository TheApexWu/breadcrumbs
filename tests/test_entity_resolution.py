"""Supplier entity resolution: one firm, many spellings, one key.

Run: python3 -m pytest tests/test_entity_resolution.py
"""
import pytest

from db.entity import normalize_firm, resolve_firm

# Same firm, different spellings: every pair must normalize to the same key.
MUST_MATCH = [
    ("DOLE FRESH VEGETABLES INC", "Dole Fresh Vegetables, Inc."),
    ("TAYLOR FARMS RETAIL INC", "Taylor Farms Retail, Inc"),
    ("BALDOR SPECIALTY FOODS INC", "Baldor Specialty Foods, Inc."),
    ("FRESH EXPRESS INCORPORATED", "Fresh  Express,  Inc"),
    ("SYSCO CORPORATION", "Sysco Corp."),
]

# Different firms with similar names: these must NOT collapse into one key.
MUST_NOT_MATCH = [
    ("DOLE FRESH VEGETABLES INC", "DOLE FRESH FRUIT COMPANY"),
    ("TAYLOR FARMS RETAIL INC", "TAYLOR FARMS FOODSERVICE LLC"),
    ("CO OP FOODS INC", "OP FOODS INC"),  # a leading "CO" is part of the name, not a suffix
]

KNOWN = [normalize_firm(f) for f in ("DOLE FRESH VEGETABLES INC", "BALDOR SPECIALTY FOODS INC")]


@pytest.mark.parametrize("a,b", MUST_MATCH)
def test_variants_resolve_to_one_key(a, b):
    assert normalize_firm(a) == normalize_firm(b)


@pytest.mark.parametrize("a,b", MUST_NOT_MATCH)
def test_distinct_firms_stay_distinct(a, b):
    assert normalize_firm(a) != normalize_firm(b)


def test_missing_name_is_empty_not_a_crash():
    assert normalize_firm(None) == "" and normalize_firm("  ,. ") == ""


def test_spelling_variant_is_matched():
    assert resolve_firm("Dole Fresh Vegetables, Inc.", KNOWN)["status"] == "matched"


def test_typo_is_flagged_ambiguous_not_dropped():
    r = resolve_firm("DOLE FRSH VEGETABLES INC", KNOWN)
    assert r["status"] == "ambiguous" and r["candidates"] == ["DOLE FRESH VEGETABLES"]


def test_unrelated_firm_is_no_match():
    assert resolve_firm("TYSON FOODS INC", KNOWN)["status"] == "no_match"


def test_sibling_firm_is_not_matched():
    assert resolve_firm("DOLE FRESH FRUIT COMPANY", KNOWN)["status"] != "matched"
