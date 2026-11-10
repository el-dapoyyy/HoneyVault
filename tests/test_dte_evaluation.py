"""Pengujian evaluasi kualitas DTE sebagai sumber data umpan."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from honeyvault.crypto.dte_evaluation import (
    dte_consistency_check,
    dte_distribution_report,
    evaluate_dte_quality,
    generate_dte_decoys,
)
from honeyvault.services.synthetic_dataset import build_dataset


@pytest.fixture(scope="module")
def rows():
    return build_dataset(150)


def test_generates_requested_number_of_decoys(rows):
    decoys = generate_dte_decoys(rows, count=25, seed=1)
    assert len(decoys) == 25


def test_decoy_ids_are_synthetic(rows):
    decoys = generate_dte_decoys(rows, count=10, seed=1)
    for decoy in decoys:
        assert decoy["id"].startswith("DEC-")


def test_decoy_categories_come_from_observed_categories(rows):
    observed = {row["category"] for row in rows}
    for decoy in generate_dte_decoys(rows, count=40, seed=2):
        assert decoy["category"] in observed


def test_same_seed_gives_identical_decoys(rows):
    first = generate_dte_decoys(rows, count=20, seed=5)
    second = generate_dte_decoys(rows, count=20, seed=5)
    assert first == second


def test_different_seed_gives_different_decoys(rows):
    first = generate_dte_decoys(rows, count=20, seed=5)
    second = generate_dte_decoys(rows, count=20, seed=6)
    assert first != second


def test_decoy_balances_stay_within_dataset_range(rows):
    low = min(float(row["balance"]) for row in rows)
    high = max(float(row["balance"]) for row in rows)
    for decoy in generate_dte_decoys(rows, count=60, seed=3):
        assert low <= decoy["balance"] <= high


def test_consistency_check_passes(rows):
    result = dte_consistency_check(rows, count=40, seed=9)
    assert result["consistent"] is True
    assert result["mismatches"] == 0


def test_distribution_frequencies_match_observed(rows):
    report = dte_distribution_report(rows, count=1000, seed=42)
    # Selisih maksimum dibatasi 0.05 karenaicu penghitungan diskret.
    assert report["max_frequency_difference"] < 0.05


def test_dte_decoys_are_hard_to_distinguish(rows):
    """Data DTE seharusnya hampir tidak dapat dibedakan dari data asli."""
    quality = evaluate_dte_quality(rows, count=300, seed=42)
    assert quality["wasserstein_distance"] < 5_000_000
    assert quality["histogram_overlap"] > 0.7
    # Akurasi classifier dekat 0.5 berarti tidak ada daya pembeda.
    assert quality["classifier"]["test_accuracy"] < 0.7


def test_ks_pvalue_does_not_reject_identical_distributions(rows):
    """p-value KS yang tinggi berarti sebaran tidak bisa dibedakan."""
    quality = evaluate_dte_quality(rows, count=300, seed=42)
    assert quality["ks_pvalue"] > 0.05
