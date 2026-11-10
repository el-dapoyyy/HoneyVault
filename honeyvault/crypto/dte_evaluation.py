"""Evaluasi kualitas DTE sebagai sumber data umpan.

Fungsi-fungsi di sini menguji apakah pesan yang dihasilkan DTE benar-benar
sulit dibedakan dari pesan asli. Ini adalah pengukuran empiris, bukan
bukti keamanan kriptografi.

Yang diukur:

1. Jarak distribusi antara data asli dan data yang dihasilkan DTE.
2. Kemampuan classifier membedakan keduanya.
3. Konsistensi: dekripsi dengan seed yang sama selalu menghasilkan pesan sama.
"""

import random
from collections import Counter

from honeyvault.crypto.honeyvault_space import (
    balance_tier,
    build_message_space,
    decode_profile,
)
from honeyvault.services.evaluation import classifier_accuracy
from honeyvault.services.profiling import profile


def generate_dte_decoys(rows, count, seed=None, seed_bits=64):
    """Membuat data umpan dengan mengambil seed acak lalu mendecode.

    Ini meniru perilaku "kunci salah": seed acak tanpa hubungan dengan data
    asli, tetapi pesan yang keluar mengikuti model distribusi yang benar.

    Args:
        rows: dataset pelanggan asli.
        count: jumlah decoy yang dihasilkan.
        seed: seed RNG agar eksperimen dapat direproduksi.
        seed_bits: ukuran ruang seed.

    Returns:
        Daftar dict decoy berisi ``id``, ``name``, ``category``, ``balance``.
    """
    space, cells = build_message_space(rows, seed_bits=seed_bits)
    rng = random.Random(seed)

    decoys = []
    for index in range(1, count + 1):
        dte_seed = rng.randrange(space.scale)
        profile_row = decode_profile(space, cells, dte_seed, rng=random.Random(dte_seed))
        decoys.append({
            "id": "DEC-{:03d}".format(index),
            "name": "DTE Umpan {:03d}".format(index),
            "category": profile_row["category"],
            "balance": profile_row["balance"],
            "dte_seed": dte_seed,
            "message": profile_row["message"],
        })
    return decoys


def dte_distribution_report(rows, count=500, seed=42):
    """Membandingkan sebaran data asli dengan sebaran yang dihasilkan DTE.

    Returns:
        Dict berisi frekuensi tiap pesan pada data asli dan pada hasil DTE,
        beserta selisih maksimum keduanya.
    """
    space, _ = build_message_space(rows)
    decoys = generate_dte_decoys(rows, count=count, seed=seed)

    real_messages = Counter(
        (row["category"], balance_tier(float(row["balance"]))) for row in rows)
    dte_messages = Counter(decoy["message"] for decoy in decoys)

    total_real = sum(real_messages.values())
    total_dte = sum(dte_messages.values())

    comparison = []
    max_difference = 0.0
    for message in space.messages:
        real_freq = real_messages.get(message, 0) / total_real
        dte_freq = dte_messages.get(message, 0) / total_dte
        difference = abs(real_freq - dte_freq)
        max_difference = max(max_difference, difference)
        comparison.append({
            "message": message,
            "real_count": real_messages.get(message, 0),
            "dte_count": dte_messages.get(message, 0),
            "real_frequency": real_freq,
            "dte_frequency": dte_freq,
            "difference": difference,
        })

    return {
        "comparison": comparison,
        "max_frequency_difference": max_difference,
        "space": space,
    }


def evaluate_dte_quality(rows, count=300, seed=42):
    """Mengukur seberapa dekat data DTE dengan data asli.

    Returns:
        Dict metrik: jarak Wasserstein, overlap histogram, statistik KS,
        akurasi classifier, dan frekuensi pesan.
    """
    from honeyvault.services.evaluation import (
        histogram_overlap,
        ks_statistic,
        wasserstein_distance,
    )

    decoys = generate_dte_decoys(rows, count=count, seed=seed)
    real_values = [float(row["balance"]) for row in rows]
    decoy_values = [float(row["balance"]) for row in decoys]

    ks_stat, ks_pvalue = ks_statistic(real_values, decoy_values)

    return {
        "wasserstein_distance": wasserstein_distance(real_values, decoy_values),
        "histogram_overlap": histogram_overlap(real_values, decoy_values),
        "ks_statistic": ks_stat,
        "ks_pvalue": ks_pvalue,
        "classifier": classifier_accuracy(real_values, decoy_values, seed=seed),
        "distribution": dte_distribution_report(rows, count=count, seed=seed),
    }


def dte_consistency_check(rows, count=50, seed=7):
    """Memastikan seed yang sama selalu menghasilkan pesan yang sama.

    Ini adalah syarat konsistensi encoding dan decoding yang diminta pada
    roadmap Tahap 4.
    """
    space, cells = build_message_space(rows)
    rng = random.Random(seed)

    seeds = [rng.randrange(space.scale) for _ in range(count)]
    first_pass = [
        decode_profile(space, cells, s, rng=random.Random(s))["message"]
        for s in seeds
    ]
    second_pass = [
        decode_profile(space, cells, s, rng=random.Random(s))["message"]
        for s in seeds
    ]

    mismatches = sum(
        1 for a, b in zip(first_pass, second_pass) if a != b)
    return {
        "checked": count,
        "mismatches": mismatches,
        "consistent": mismatches == 0,
    }
