"""Pengujian skema Honey Encryption.

Sifat yang diuji:

1. Kunci benar memulihkan pesan asli.
2. Kunci salah menghasilkan pesan yang masih masuk akal.
3. Ciphertext tidak membocorkan pesan.
4. Nonce yang berbeda menghasilkan ciphertext yang berbeda.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from honeyvault.crypto.honey_encryption import (
    HoneyEncryption,
    build_scheme,
    generate_decoy_dataset,
    wrong_key,
)
from honeyvault.crypto.honeyvault_space import balance_tier
from honeyvault.services.synthetic_dataset import build_dataset


@pytest.fixture(scope="module")
def rows():
    return build_dataset(150)


@pytest.fixture(scope="module")
def scheme(rows):
    return build_scheme(rows)


# -- kunci benar --------------------------------------------------------------

def test_correct_key_recovers_original_message(rows, scheme):
    for row in rows[:50]:
        encrypted = scheme.encrypt(row)
        result = scheme.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        expected = (row["category"], balance_tier(float(row["balance"])))
        assert result["message"] == expected


def test_recovery_rate_is_perfect(rows, scheme):
    from honeyvault.crypto.security_evaluation import (
        evaluate_correct_key_recovery,
    )
    result = evaluate_correct_key_recovery(rows, samples=80)
    assert result["success_rate"] == 1.0


def test_ciphertext_is_not_the_plaintext_seed(scheme, rows):
    encrypted = scheme.encrypt(rows[0])
    assert encrypted["ciphertext"] != encrypted["seed"]


def test_decrypt_returns_readable_profile(scheme, rows):
    encrypted = scheme.encrypt(rows[0])
    result = scheme.decrypt(encrypted["ciphertext"], encrypted["nonce"])
    assert result["category"] in {row["category"] for row in rows}
    assert result["balance"] > 0
    assert result["tier"] in {label for label, _, _ in _tiers()}


def _tiers():
    from honeyvault.crypto.honeyvault_space import BALANCE_TIERS
    return BALANCE_TIERS


# -- kunci salah --------------------------------------------------------------

def test_wrong_key_still_produces_valid_message(scheme, rows):
    attacker = wrong_key(scheme)
    observed = {row["category"] for row in rows}
    for row in rows[:50]:
        encrypted = scheme.encrypt(row)
        result = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        assert result["category"] in observed
        assert result["balance"] > 0


def test_wrong_key_message_is_in_message_space(scheme):
    attacker = wrong_key(scheme)
    encrypted = scheme.encrypt(_one_customer())
    result = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])
    assert result["message"] in scheme.space


def test_wrong_key_mostly_differs_but_not_always(scheme, rows):
    """Kunci salah hampir selalu menghasilkan pesan berbeda.

    La BJARANG kecil: dengan 10 pesan, kunci salah berpeluang sekitar 10%
    mendarat pada pesan yang sama. Itulah konsekuensi wajar dari ruang pesan
    yang kecil, dan justru sifat yang diinginkan Honey Encryption: tebakan
    yang salah tetap menghasilkan pesan yang tampak sah.
    """
    attacker = wrong_key(scheme)
    row = _one_customer()
    expected = (row["category"], balance_tier(float(row["balance"])))

    matches = 0
    total = 100
    for _ in range(total):
        encrypted = scheme.encrypt(row)
        result = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        if result["message"] == expected:
            matches += 1

    # Tidak mungkin selalu sama, dan tidak mungkin selalu berbeda.
    assert matches < total
    assert matches > 0


def test_wrong_key_messages_follow_distribution(scheme, rows):
    """Pesan dari kunci salah harus mengikuti model distribusi DTE."""
    from collections import Counter
    attacker = wrong_key(scheme)
    counts = Counter()
    for row in rows[:100]:
        encrypted = scheme.encrypt(row)
        result = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        counts[result["message"]] += 1

    total = sum(counts.values())
    # Pesan yang paling sering muncul pada data asli seharusnya juga sering
    # muncul pada hasil kunci salah.
    real_counts = Counter(
        (row["category"], balance_tier(float(row["balance"]))) for row in rows)
    most_common_real = real_counts.most_common(1)[0][0]
    assert counts.get(most_common_real, 0) > 0


def test_generated_decoy_dataset_has_synthetic_names(rows, scheme):
    decoys = generate_decoy_dataset(rows, count=20, scheme=scheme, seed=1)
    assert len(decoys) == 20
    real_names = {row["name"] for row in rows}
    for decoy in decoys:
        assert decoy["name"] not in real_names
        assert decoy["id"].startswith("DEC-")


# -- kerahasiaan ---------------------------------------------------------------

def test_ciphertext_does_not_reveal_message(scheme):
    """Ciphertext untuk pesan berbeda tidak boleh berbeda polanya."""
    from honeyvault.crypto.security_evaluation import (
        evaluate_ciphertext_leakage,
    )
    rows = build_dataset(150)
    result = evaluate_ciphertext_leakage(rows, samples=1200)
    assert result["leak_detected"] is False
    assert result["ks_versus_uniform"]["pvalue"] > 0.01


def test_different_nonce_gives_different_ciphertext(scheme, rows):
    row = rows[0]
    first = scheme.encrypt(row)
    second = scheme.encrypt(row)
    assert first["nonce"] != second["nonce"]
    assert first["ciphertext"] != second["ciphertext"]


def test_same_nonce_still_gives_different_ciphertext(scheme, rows):
    """Nonce sama tidak menghasilkan ciphertext sama.

    Seed di-encode secara acak oleh DTE, sehingga dua enkripsi pesan yang
    sama tidak pernah menghasilkan ciphertext identik. Ini analogsinya
    IND-CPA: ciphertext yang sama tidak berarti pesan yang sama.
    """
    row = rows[0]
    nonce = b"\x00" * 16
    first = scheme.encrypt(row, nonce=nonce)
    second = scheme.encrypt(row, nonce=nonce)
    assert first["ciphertext"] != second["ciphertext"]
    # Tetapi keduanya harus tetap dapat didekripsi ke pesan yang sama.
    assert (scheme.decrypt(first["ciphertext"], first["nonce"])["message"]
            == scheme.decrypt(second["ciphertext"], second["nonce"])["message"])


def test_nonce_must_be_unique_per_key(scheme, rows):
    """Nonce yang sama untuk pesan berbeda menyingkap informasi.

    Jika nonce dipakai ulang, XOR dua ciphertext menghasilkan XOR dua seed.
    Perbedaan itu bisa dipakai penyerang untuk mempersempit pasangan pesan
    yang mungkin. Skema ini karena itu mewajibkan nonce unik per kunci.
    """
    from honeyvault.crypto.security_evaluation import evaluate_nonce_reuse

    result = evaluate_nonce_reuse(rows)
    assert result["message_space_size"] > 1
    # Hanya pasangan pesan yang benar yang boleh konsisten dengan XOR
    # teramati. Bila ada pasangan lain yang juga konsisten, kebocoran ada.
    assert result["leak_detected"] is True


def test_different_key_gives_different_ciphertext(rows):
    scheme_a = build_scheme(rows, key=b"a" * 16)
    scheme_b = build_scheme(rows, key=b"b" * 16)
    row = rows[0]
    nonce = b"\x01" * 16
    assert (scheme_a.encrypt(row, nonce=nonce)["ciphertext"]
            != scheme_b.encrypt(row, nonce=nonce)["ciphertext"])


# -- validasi kunci ------------------------------------------------------------

def test_short_key_is_rejected(scheme):
    with pytest.raises(ValueError):
        HoneyEncryption(scheme.space, scheme.cell_salaries, key=b"pendek")


def test_non_bytes_key_is_rejected(scheme):
    with pytest.raises(TypeError):
        HoneyEncryption(scheme.space, scheme.cell_salaries, key="string")


def test_default_key_is_generated(scheme):
    fresh = HoneyEncryption(scheme.space, scheme.cell_salaries)
    assert len(fresh.key) == 16


def _one_customer():
    return {
        "id": "C001",
        "name": "Pelanggan Uji",
        "category": "Regular",
        "balance": 8_500_000,
    }
