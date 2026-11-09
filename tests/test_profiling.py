"""Pengujian Data Profiling."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyvault.services.profiling import observed_categories, profile


ROWS = [
    {"id": "C001", "name": "A", "category": "Regular", "balance": 1000000},
    {"id": "C002", "name": "B", "category": "Regular", "balance": 2000000},
    {"id": "C003", "name": "C", "category": "Premium", "balance": 3000000},
    {"id": "C004", "name": "D", "category": "Premium", "balance": 5000000},
]


def test_overall_statistics_are_correct():
    result = profile(ROWS)["overall"]
    assert result["count"] == 4
    assert result["mean"] == 2750000
    assert result["median"] == 2500000
    assert result["min"] == 1000000
    assert result["max"] == 5000000


def test_standard_deviation_uses_sample_formula():
    # Sampel (n-1) dari [1, 2, 3, 5] juta:
    # mean = 2.75 juta, varian = 8.75 / 3, akar = 1.707825 juta.
    result = profile(ROWS)["overall"]
    assert abs(result["sd"] - 1707825.13) < 1


def test_quantiles_are_between_min_and_max():
    overall = profile(ROWS)["overall"]
    assert overall["min"] <= overall["q1"] <= overall["q3"] <= overall["max"]


def test_profile_per_category():
    result = profile(ROWS)
    assert result["categories"] == ["Premium", "Regular"]
    assert result["count_by_category"] == {"Premium": 2, "Regular": 2}
    assert result["by_category"]["Regular"]["mean"] == 1500000


def test_profile_handles_empty_dataset():
    result = profile([])
    assert result["overall"]["count"] == 0
    assert result["overall"]["mean"] == 0
    assert result["categories"] == []


def test_observed_categories_returns_sorted_unique():
    assert observed_categories(ROWS) == ["Premium", "Regular"]


def test_non_numeric_values_are_skipped():
    rows = list(ROWS) + [{"id": "C005", "name": "E", "category": "Basic", "balance": "abc"}]
    assert profile(rows)["overall"]["count"] == 4
