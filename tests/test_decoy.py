"""Pengujian generator decoy (Random dan Adaptive)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyvault.services.decoy import (
    METHOD_ADAPTIVE,
    METHOD_RANDOM,
    generate_decoy,
    resolve_bounds,
)
from honeyvault.services.identity import DECOY_ID_PREFIX

ROWS = [
    {"id": "C001", "name": "Andi Pratama", "category": "Regular", "balance": 8000000},
    {"id": "C002", "name": "Budi Santoso", "category": "Regular", "balance": 8200000},
    {"id": "C003", "name": "Citra Lestari", "category": "Premium", "balance": 9000000},
    {"id": "C004", "name": "Deni Kurniawan", "category": "Regular", "balance": 8400000},
    {"id": "C005", "name": "Eka Putri", "category": "Premium", "balance": 9200000},
]


def test_generates_requested_number_of_decoys():
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=7, seed=1)
    assert len(result) == 7


def test_decoy_ids_do_not_collide_with_customer_ids():
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=5, seed=1)
    for row in result:
        assert row["id"].startswith(DECOY_ID_PREFIX + "-")
        assert row["id"] not in {r["id"] for r in ROWS}


def test_decoy_names_never_copy_customer_names():
    # Ini adalah regresi untuk bug lama: nama pelanggan asli pernah disalin
    # ke dalam data umpan.
    original_names = {r["name"] for r in ROWS}
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=25, seed=3)
    for row in result:
        assert row["name"] not in original_names


def test_decoy_names_are_unique_within_a_run():
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=25, seed=3)
    names = [row["name"] for row in result]
    assert len(set(names)) == len(names)


def test_balances_respect_dataset_bounds():
    low, high = resolve_bounds(ROWS)
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=30, seed=5)
    for row in result:
        assert low <= row["balance"] <= high


def test_random_decoy_also_respects_bounds():
    low, high = resolve_bounds(ROWS)
    result = generate_decoy(ROWS, method=METHOD_RANDOM, count=30, seed=5)
    for row in result:
        assert low <= row["balance"] <= high


def test_same_seed_reproduces_same_result():
    first = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=10, seed=42)
    second = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=10, seed=42)
    assert first == second


def test_different_seed_produces_different_result():
    first = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=10, seed=1)
    second = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=10, seed=2)
    assert first != second


def test_adaptive_categories_come_from_observed_categories():
    observed = {r["category"] for r in ROWS}
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=20, seed=9)
    for row in result:
        assert row["category"] in observed


def test_random_decoy_categories_come_from_observed_categories():
    observed = {r["category"] for r in ROWS}
    result = generate_decoy(ROWS, method=METHOD_RANDOM, count=20, seed=9)
    for row in result:
        assert row["category"] in observed


def test_empty_dataset_returns_empty_list():
    assert generate_decoy([], method=METHOD_ADAPTIVE, count=5, seed=1) == []


def test_count_is_capped():
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=9999, seed=1)
    assert len(result) == 200


def test_balances_are_rounded_to_thousands():
    result = generate_decoy(ROWS, method=METHOD_ADAPTIVE, count=10, seed=11)
    for row in result:
        assert row["balance"] % 1000 == 0
