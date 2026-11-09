"""Lapisan penyimpanan data pelanggan (JSON di disk).

Penyimpanan sengaja dibuat sangat sederhana: satu berkas JSON berisi daftar
pelanggan. Prototipe tidak butuh basis data, dan format JSON mudah dibaca
untuk keperluan laporan.
"""

import json
import os
import shutil

from config import DATA_FILE, SYNTHETIC_DATASET_FILE

# Dataset contoh awal yang dipakai saat aplikasi pertama kali dijalankan.
SEED_CUSTOMERS = [
    {"id": "C001", "name": "Andi Pratama", "category": "Regular", "balance": 8500000},
    {"id": "C002", "name": "Budi Santoso", "category": "Regular", "balance": 7900000},
    {"id": "C003", "name": "Citra Lestari", "category": "Premium", "balance": 9100000},
    {"id": "C004", "name": "Deni Kurniawan", "category": "Regular", "balance": 8200000},
    {"id": "C005", "name": "Eka Putri", "category": "Premium", "balance": 8700000},
    {"id": "C006", "name": "Fajar Hidayat", "category": "Regular", "balance": 7600000},
    {"id": "C007", "name": "Gita Maharani", "category": "Premium", "balance": 9400000},
    {"id": "C008", "name": "Hadi Saputra", "category": "Regular", "balance": 8300000},
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_customers():
    """Mengembalikan daftar pelanggan; membuat berkas awal bila belum ada."""
    if not os.path.exists(DATA_FILE):
        _write(DATA_FILE, SEED_CUSTOMERS)
    return _read(DATA_FILE)


def save_customers(rows):
    """Menyimpan daftar pelanggan ke disk."""
    _write(DATA_FILE, rows)


def reset_customers():
    """Memulihkan dataset ke delapan pelanggan contoh."""
    _write(DATA_FILE, SEED_CUSTOMERS)
    return SEED_CUSTOMERS


def load_synthetic_dataset():
    """Mengembalikan dataset sintetis berukuran lebih besar (150 pelanggan)."""
    if not os.path.exists(SYNTHETIC_DATASET_FILE):
        return None
    return _read(SYNTHETIC_DATASET_FILE)


def install_synthetic_dataset():
    """Menyalin dataset sintetis besar ke penyimpanan aktif."""
    rows = load_synthetic_dataset()
    if rows is None:
        return None
    shutil.copyfile(SYNTHETIC_DATASET_FILE, DATA_FILE)
    return rows
