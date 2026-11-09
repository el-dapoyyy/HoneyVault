"""Generator data umpan (decoy): Random Decoy dan Adaptive Decoy.

Kedua generator memakai *message space* (rentang saldo) yang sama agar
perbandingan statistik adil. Perbedaannya hanya pada cara nilai saldo
dipilih:

* **Random Decoy** - baseline: saldo diambil seragam (uniform) pada rentang
  yang tersedia, kategori diambil seragam dari kategori yang teramati.
* **Adaptive Decoy** - saldo dibangkitkan mengikuti model statistik
  per kategori, sehingga korelasi kategori-saldo ikut dipertahankan.

Keduanya memakai identitas sintetis (lihat ``honeyvault.services.identity``)
dan tidak pernah menyalin identitas pelanggan asli.
"""

import random

from honeyvault.services.identity import build_decoy_id, generate_decoy_identity
from honeyvault.services.profiling import observed_categories, profile

METHOD_RANDOM = "random"
METHOD_ADAPTIVE = "adaptive"

DEFAULT_COUNT = 5
MAX_COUNT = 200


def resolve_bounds(rows, field="balance"):
    """Menentukan rentang nilai (message space) dari dataset.

    Rentang ini dipakai bersama oleh kedua generator sehingga perbandingan
    statistik tidak bias.
    """
    values = [float(r[field]) for r in rows if r.get(field) is not None]
    if not values:
        return 0.0, 1.0
    return min(values), max(values)


def _category_pool(rows):
    """Kategori yang teramati beserta frekuensinya."""
    counts = {}
    for row in rows:
        category = row.get("category")
        if category:
            counts[category] = counts.get(category, 0) + 1
    return counts


def _round_money(value):
    """Membulatkan ke ribuan rupiah terdekat."""
    return int(round(value / 1000.0) * 1000)


def generate_decoy(
    rows,
    method=METHOD_ADAPTIVE,
    count=DEFAULT_COUNT,
    seed=None,
    field="balance",
    bounds=None,
):
    """Membuat daftar data umpan.

    Args:
        rows: dataset pelanggan sebagai sumber profil.
        method: ``"random"`` atau ``"adaptive"``.
        count: jumlah baris decoy yang dihasilkan.
        seed: seed RNG agar hasil dapat direproduksi.
        field: field numerik yang dimodelkan.
        bounds: rentang nilai ``(min, max)``; jika ``None`` dihitung dari data.

    Returns:
        Daftar dict decoy dengan key ``id``, ``name``, ``category``, ``balance``.
    """
    if not rows:
        return []

    count = max(1, min(int(count), MAX_COUNT))
    rng = random.Random(seed)
    stats = profile(rows, field=field)
    low, high = bounds if bounds else resolve_bounds(rows, field)

    categories = observed_categories(rows)
    if not categories:
        categories = ["Tidak Diketahui"]
    weights = _category_pool(rows)
    category_list = list(stats["by_category"].keys()) or categories
    per_category = stats["by_category"]

    taken_names = {str(r.get("name", "")).lower() for r in rows if r.get("name")}
    decoys = []

    for index in range(1, count + 1):
        if method == METHOD_RANDOM:
            category = rng.choice(category_list)
            amount = rng.uniform(low, high)
        else:
            # Adaptive: kategori dipilih mengikuti frekuensi observasi, lalu
            # saldo dibangkitkan dari model kategori tersebut bila cukup data.
            category = rng.choices(category_list, weights=[
                weights.get(c, 1) for c in category_list
            ])[0]
            amount = _sample_adaptive_amount(rng, category, per_category, stats)

        amount = max(low, min(high, amount))
        name = generate_decoy_identity(rng, taken_names)
        taken_names.add(name.lower())

        decoys.append({
            "id": build_decoy_id(index),
            "name": name,
            "category": category,
            "balance": _round_money(amount),
            "method": method,
        })

    return decoys


def _sample_adaptive_amount(rng, category, per_category, stats):
    """Membangkitkan saldo dari model kategori, dengan fallback ke global."""
    model = per_category.get(category)
    overall = stats["overall"]

    if model and model["count"] >= 2 and model["sd"] > 0:
        return rng.gauss(model["mean"], model["sd"])

    if model and model["count"] == 1:
        # Satu-satunya observasi kategori ini: pakai nilai itu apa adanya.
        return model["mean"]

    # Fallback: model global. Deviasi standar minimum 5% dari mean supaya
    # Gaussian tidak runtuh ketika semua saldo identik.
    sd = overall["sd"] if overall["sd"] > 0 else overall["mean"] * 0.05
    return rng.gauss(overall["mean"], sd)
