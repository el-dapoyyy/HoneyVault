"""Pengujian modul evaluasi kuantitatif."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyvault.services.evaluation import (
    classifier_accuracy,
    compare_methods,
    evaluate_method,
    histogram_overlap,
    ks_statistic,
    wasserstein_distance,
)

REAL = [
    {"id": "C{:03d}".format(i), "name": "N{}".format(i),
     "category": "Regular", "balance": 8000000 + i * 10000}
    for i in range(1, 41)
]

IDENTICAL = [
    {"id": "D{:03d}".format(i), "name": "M{}".format(i),
     "category": "Regular", "balance": 8000000 + i * 10000}
    for i in range(1, 41)
]

FAR_AWAY = [
    {"id": "F{:03d}".format(i), "name": "K{}".format(i),
     "category": "Basic", "balance": 500000 + i * 1000}
    for i in range(1, 41)
]


def test_identical_distributions_have_zero_distance():
    assert wasserstein_distance(
        [r["balance"] for r in REAL], [r["balance"] for r in IDENTICAL]
    ) == 0


def test_wasserstein_grows_with_separation():
    near = wasserstein_distance(
        [r["balance"] for r in REAL], [r["balance"] for r in IDENTICAL]
    )
    far = wasserstein_distance(
        [r["balance"] for r in REAL], [r["balance"] for r in FAR_AWAY]
    )
    assert far > near


def test_ks_statistic_returns_statistic_and_pvalue():
    stat, pvalue = ks_statistic(
        [r["balance"] for r in REAL], [r["balance"] for r in IDENTICAL]
    )
    assert stat == 0
    assert 0 <= pvalue <= 1


def test_histogram_overlap_is_one_for_identical_distributions():
    overlap = histogram_overlap(
        [r["balance"] for r in REAL], [r["balance"] for r in IDENTICAL]
    )
    assert abs(overlap - 1.0) < 0.01


def test_histogram_overlap_is_low_for_separated_distributions():
    overlap = histogram_overlap(
        [r["balance"] for r in REAL], [r["balance"] for r in FAR_AWAY]
    )
    assert overlap < 0.5


def test_classifier_finds_easy_separation():
    result = classifier_accuracy(
        [r["balance"] for r in REAL], [r["balance"] for r in FAR_AWAY], seed=1
    )
    assert result["test_accuracy"] > 0.9


def test_classifier_cannot_separate_identical_distributions():
    result = classifier_accuracy(
        [r["balance"] for r in REAL], [r["balance"] for r in IDENTICAL], seed=1
    )
    assert result["test_accuracy"] < 0.75


def test_classifier_uses_train_test_split():
    result = classifier_accuracy(
        [r["balance"] for r in REAL], [r["balance"] for r in FAR_AWAY],
        seed=1, test_ratio=0.3
    )
    assert result["train_size"] + result["test_size"] == 80


def test_evaluate_method_returns_expected_keys():
    metrics = evaluate_method(REAL, IDENTICAL)
    for key in ("mean_difference", "sd_difference", "histogram_overlap",
                "wasserstein_distance", "ks_statistic", "classifier",
                "real_mean", "decoy_mean"):
        assert key in metrics


def test_compare_methods_picks_the_closer_distribution():
    report = compare_methods(REAL, FAR_AWAY, IDENTICAL)
    assert report["winner"] == "adaptive"
    assert report["adaptive"]["wasserstein_distance"] < \
        report["random"]["wasserstein_distance"]
