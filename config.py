"""Konfigurasi terpusat untuk aplikasi HoneyVault.

Semua nilai yang mungkin berbeda antar lingkungan (kunci rahasia, mode debug,
lokasi data) dipusatkan di sini agar `app.py` tetap ringkas dan mudah dibaca.
"""

import os

# --- Lokasi berkas -----------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "customers.json")
SYNTHETIC_DATASET_FILE = os.path.join(DATA_DIR, "synthetic_customers.json")

# --- Aturan domain ------------------------------------------------------------

CATEGORIES = ("Basic", "Regular", "Premium", "VIP")

MIN_BALANCE = 0
MAX_BALANCE = 1_000_000_000
MAX_DECOY_COUNT = 200
DEFAULT_DECOY_COUNT = 5

# --- Keamanan dasar -----------------------------------------------------------

# Kunci rahasia diambil dari environment variable. Jika belum diset, aplikasi
# memakai kunci acak yang berlaku hanya selama satu proses. Konsekuensinya:
# pesan flash antar-mulai ulang hilang. Ini trade-off yang disengaja untuk
# prototipe lokal, supaya tidak ada kunci hardcoded di dalam kode.
SECRET_KEY = os.environ.get("HONEYVAULT_SECRET_KEY") or os.urandom(24).hex()

# Mode debug TIDAK aktif secara default. Aktifkan bila diperlukan:
#   Windows PowerShell : $env:HONEYVAULT_DEBUG = "1"
#   Windows CMD        : set HONEYVAULT_DEBUG=1
#   Linux/macOS        : HONEYVAULT_DEBUG=1 python app.py
DEBUG = os.environ.get("HONEYVAULT_DEBUG", "0") == "1"

# Server hanya mendengarkan di loopback, tidak diekspos ke jaringan.
HOST = os.environ.get("HONEYVAULT_HOST", "127.0.0.1")
PORT = int(os.environ.get("HONEYVAULT_PORT", "5000"))
