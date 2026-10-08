"""Supplier entity resolution: one firm, many spellings, one key.

Recalls and operator records spell the same firm differently ("DOLE FRESH VEGETABLES INC" vs
"Dole Fresh Vegetables, Inc."). Every join on a firm goes through normalize_firm so a spelling
difference can never silently return zero exposed sites.
"""
import difflib
import re

# Stripped only from the END of a name, so "CO OP FOODS" keeps its "CO".
_LEGAL_SUFFIXES = {"INC", "INCORPORATED", "LLC", "CO", "COMPANY", "CORP", "CORPORATION",
                   "LTD", "LIMITED", "LP", "LLP", "PLC"}


def normalize_firm(name):
    """Canonical key: uppercase, punctuation to spaces, collapsed whitespace, trailing legal
    suffixes removed. Empty or missing names return ""."""
    words = re.sub(r"[^A-Z0-9]+", " ", (name or "").upper()).split()
    while words and words[-1] in _LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


def resolve_firm(name, known_keys, cutoff=0.88):
    """Resolve a firm name against the operator's known supplier keys.

    matched   - the normalized key is a known supplier
    ambiguous - not known, but close to one (a likely typo); needs a human, never auto-merged
    no_match  - not a supplier of this operator
    """
    key = normalize_firm(name)
    known = sorted(set(known_keys))
    if key and key in known:
        return {"status": "matched", "key": key, "candidates": [key]}
    near = difflib.get_close_matches(key, known, n=3, cutoff=cutoff) if key else []
    if near:
        return {"status": "ambiguous", "key": key, "candidates": near}
    return {"status": "no_match", "key": key, "candidates": []}
