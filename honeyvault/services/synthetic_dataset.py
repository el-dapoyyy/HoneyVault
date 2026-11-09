"""Pembangkitan dataset pelanggan sintetis berukuran lebih besar.

Tahap 2 roadmap menyebut perlunya dataset yang lebih besar agar model
distribusi lebih representatif. Modul ini membangkitkan 150 pelanggan
fiktif dengan hubungan antara kategori dan saldo yang masuk akal, lalu
menyimpannya sebagai `data/synthetic_customers.json`.
"""

import json
import os
import random

from config import SYNTHETIC_DATASET_FILE

# Profil saldo per kategori: (mean, standar deviasi, batas bawah, batas atas).
CATEGORY_PROFILES = {
    "Basic": (3_500_000, 1_200_000, 500_000, 8_000_000),
    "Regular": (8_500_000, 1_500_000, 4_000_000, 14_000_000),
    "Premium": (15_000_000, 4_000_000, 8_000_000, 28_000_000),
    "VIP": (40_000_000, 12_000_000, 20_000_000, 90_000_000),
}

# Bobot kategori, mencerminkan komposisi dataset bank synthetic.
CATEGORY_WEIGHTS = {
    "Basic": 0.30,
    "Regular": 0.40,
    "Premium": 0.22,
    "VIP": 0.08,
}

FIRST_NAMES = (
    "Agus", "Bambang", "Candra", "Dewi", "Eka", "Fajar", "Gita", "Hendra",
    "Indah", "Joko", "Kartika", "Lina", "Maya", "Nanda", "Oscar", "Putri",
    "Rizky", "Sari", "Tono", "Umar", "Wahyu", "Yuni", "Zaki", "Andri",
    "Bayu", "Citra", "Dimas", "Fitri", "Galang", "Hana",
)

LAST_NAMES = (
    "Adi", "Basuki", "Cahyono", "Djalani", "Effendi", "Firmansyah",
    "Gunawan", "Halim", "Ismail", "Jamal", "Kusuma", "Lestari",
    "Maulana", "Nugroho", "Pranoto", "Rizal", "Suryani", "Tjahjadi",
    "Utami", "Wibowo", "Yulianto", "Zulkifli", "Asmara", "Baskoro",
    "Cahyani", "Damar", "Enggal", "Fitriani", "Gunawan", "Handoko",
)


def build_dataset(size=150, seed=20241101):
    """Membangkitkan daftar pelanggan sintetis.

    Args:
        size: jumlah pelanggan yang dibangkitkan.
        seed: seed RNG agar dataset dapat direproduksi.

    Returns:
        Daftar dict pelanggan dengan key ``id``, ``name``, ``category``,
        ``balance``.
    """
    rng = random.Random(seed)
    categories = list(CATEGORY_PROFILES)
    weights = [CATEGORY_WEIGHTS[c] for c in categories]

    rows = []
    for index in range(1, size + 1):
        category = rng.choices(categories, weights=weights)[0]
        mean, sd, low, high = CATEGORY_PROFILES[category]
        balance = rng.gauss(mean, sd)
        balance = max(low, min(high, balance))
        rows.append({
            "id": "C{:03d}".format(index),
            "name": "{} {}".format(
                rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            ),
            "category": category,
            "balance": int(round(balance / 1000.0) * 1000),
        })
    return rows


def write_dataset(size=150, seed=20241101, path=SYNTHETIC_DATASET_FILE):
    """Membangkitkan dataset lalu menyimpannya sebagai JSON."""
    rows = build_dataset(size=size, seed=seed)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    return rows


if __name__ == "__main__":
    written = write_dataset()
    print("Dataset sintetis ditulis: {} pelanggan".format(len(written)))
    print("Berkas:", SYNTHETIC_DATASET_FILE)
