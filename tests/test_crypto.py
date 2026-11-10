"""Pengujian DTE (Distribution-Transforming Encoder).

Sifat yang diuji:

1. Round-trip: ``decode(encode(pesan)) == pesan`` untuk seluruh pesan sah.
2. Distribusi sampling sesuai model probabilitas.
3. Perilaku seed di luar ruang pesan valid.
4. Konsistensi encoding dan decoding.
"""

import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from honeyvault.crypto.dte import DTESpace
from honeyvault.crypto.honeyvault_space import (
    BALANCE_TIERS,
    balance_tier,
    build_message_space,
    decode_profile,
    encode_profile,
)
from honeyvault.services.synthetic_dataset import build_dataset

ENTRIES = [
    (("A", "low"), 50),
    (("B", "mid"), 30),
    (("C", "high"), 20),
]


@pytest.fixture(scope="module")
def rows():
    return build_dataset(150)


@pytest.fixture(scope="module")
def space_and_cells(rows):
    return build_message_space(rows)


@pytest.fixture(scope="module")
def space(space_and_cells):
    return space_and_cells[0]


@pytest.fixture(scope="module")
def cells(space_and_cells):
    return space_and_cells[1]


# -- Round-trip ---------------------------------------------------------------

def test_round_trip_for_every_message(space):
    """decode(encode(pesan)) == pesan untuk seluruh pesan yang sah."""
    rng = random.Random(1)
    for message in space.messages:
        for _ in range(50):
            seed = space.encode(message, rng=rng)
            assert space.decode(seed) == message


def test_round_trip_generic_space():
    rng = random.Random(7)
    space = DTESpace(ENTRIES, seed_bits=32)
    for message, _ in ENTRIES:
        seed = space.encode(message, rng=rng)
        assert space.decode(seed) == message


def test_encode_is_deterministic_with_same_rng_seed():
    space = DTESpace(ENTRIES, seed_bits=32)
    first = space.encode(("A", "low"), rng=random.Random(99))
    second = space.encode(("A", "low"), rng=random.Random(99))
    assert first == second


def test_encode_produces_different_seeds_for_same_message():
    space = DTESpace(ENTRIES, seed_bits=32)
    rng = random.Random(3)
    seeds = {space.encode(("A", "low"), rng=rng) for _ in range(50)}
    assert len(seeds) > 1


# -- Distribusi ---------------------------------------------------------------

def test_sampling_follows_probability_model():
    space = DTESpace(ENTRIES, seed_bits=32)
    rng = random.Random(11)
    total = 40000
    counts = Counter(space.sample(rng) for _ in range(total))
    for message, weight in ENTRIES:
        expected = weight / sum(w for _, w in ENTRIES)
        observed = counts[message] / total
        assert abs(expected - observed) < 0.01


def test_honeyvault_space_uses_observed_categories(space, rows):
    observed = {row["category"] for row in rows}
    for message in space.messages:
        assert message[0] in observed


def test_honeyvault_space_probability_matches_observed_frequency(space, rows):
    """Probabilitas tiap pesan harus sama dengan frekuensi observasinya."""
    observed = Counter(
        (row["category"], balance_tier(float(row["balance"]))) for row in rows)
    total = len(rows)
    for message, count in observed.items():
        assert space.probability(message) == pytest.approx(count / total)


# -- Seed di luar ruang pesan -------------------------------------------------

def test_decode_rejects_seed_out_of_range(space):
    with pytest.raises(ValueError):
        space.decode(-1)
    with pytest.raises(ValueError):
        space.decode(space.scale)


def test_decode_rejects_non_integer_seed(space):
    with pytest.raises(TypeError):
        space.decode("bukan bilangan")


def test_decode_rejects_boolean_seed(space):
    # bool adalah subclass int, tetapi bukan seed yang sah.
    with pytest.raises(TypeError):
        space.decode(True)


def test_encode_rejects_unknown_message(space):
    with pytest.raises(KeyError):
        space.encode(("Tidak", "Ada"))


def test_probability_rejects_unknown_message(space):
    with pytest.raises(KeyError):
        space.probability(("Tidak", "Ada"))


# -- Validasi konstruksi ------------------------------------------------------

def test_empty_space_is_rejected():
    with pytest.raises(ValueError):
        DTESpace([])


def test_non_positive_weight_is_rejected():
    with pytest.raises(ValueError):
        DTESpace([(("A",), 0)])
    with pytest.raises(ValueError):
        DTESpace([(("A",), -5)])


def test_too_small_seed_space_is_rejected():
    with pytest.raises(ValueError):
        DTESpace([("a", 1), ("b", 1), ("c", 1)], seed_bits=1)


# -- Batas interval -----------------------------------------------------------

def test_intervals_are_contiguous_and_cover_whole_space(space):
    """Interval harus bersambung dan menutup seluruh ruang seed."""
    rows = space.describe()
    assert rows[0]["seed_start"] == 0
    assert rows[-1]["seed_end"] == space.scale
    for previous, current in zip(rows, rows[1:]):
        assert previous["seed_end"] == current["seed_start"]


def test_interval_width_is_proportional_to_probability(space):
    """Lebar interval harus sebanding dengan probabilitas pesan.

    Perbandingan memakai rasio relatif, bukan selisih mutlak: ruang seed
    64 bit bernilai sekitar 1,8e19, jauh di luar presisi float64, sehingga
    selisih mutlak akan selalu muncul akibat keterbatasan float.
    """
    for row in space.describe():
        expected = row["probability"] * space.scale
        relative_error = abs(row["seed_count"] - expected) / expected
        assert relative_error < 1e-12


def test_every_message_has_at_least_one_seed(space):
    for row in space.describe():
        assert row["seed_count"] >= 1


# -- Lapis HoneyVault ---------------------------------------------------------

def test_balance_tier_classification():
    assert balance_tier(1000000) == "0-5 jt"
    assert balance_tier(5000000) == "5-10 jt"
    assert balance_tier(20000000) == "20-35 jt"
    assert balance_tier(100000000) == "70 jt+"


def test_balance_tier_covers_all_rows(rows):
    for row in rows:
        assert balance_tier(float(row["balance"])) in {
            label for label, _, _ in BALANCE_TIERS}


def test_encode_profile_then_decode_profile_keeps_message(space, cells, rows):
    """Decode dari seed harus mengembalikan profil pesan yang sama."""
    rng = random.Random(5)
    for row in rows[:30]:
        seed = encode_profile(space, row, rng=rng)
        result = decode_profile(space, cells, seed, rng=random.Random(seed))
        expected = (row["category"], balance_tier(float(row["balance"])))
        assert result["message"] == expected


def test_decoded_balance_stays_within_tier(space, cells, rows):
    rng = random.Random(6)
    for row in rows[:30]:
        seed = encode_profile(space, row, rng=rng)
        result = decode_profile(space, cells, seed, rng=random.Random(seed))
        low, high = _tier_bounds(result["tier"])
        assert low <= result["balance"] < high or result["balance"] >= low


def _tier_bounds(label):
    for name, low, high in BALANCE_TIERS:
        if name == label:
            return low, high
    return 0, float("inf")
