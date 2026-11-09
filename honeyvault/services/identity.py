"""Generator identitas sintetis untuk data umpan (decoy).

Aturan penting: nama dan ID decoy HARUS sintetis dan tidak boleh menyalin
identitas pelanggan yang ada di dataset. Modul ini menyediakan:

1. Kumpulan nama sintetis terpisah dari nama pelanggan pada dataset.
2. Pengecekan tabrakan nama, sehingga decoy tidak pernah memakai nama yang
   sama dengan pelanggan asli.
3. ID decoy dengan prefiks berbeda (``DEC-``) dari ID pelanggan (``C###``).
"""

import random

# Nama sintetis. Sengaja dipisah dari nama pelanggan pada dataset contoh agar
# tidak ada identitas yang ikut terbawa ke data umpan.
_SYNTHETIC_FIRST_NAMES = (
    "Agus", "Bambang", "Candra", "Damar", "Eka", "Fajar", "Gilang",
    "Hendra", "Indira", "Joko", "Krisna", "Laras", "Maya", "Nanda",
    "Oscar", "Pranata", "Rangga", "Sekar", "Tari", "Umar", "Wahyu",
    "Yudha", "Zaki",
)

_SYNTHETIC_LAST_NAMES = (
    "Anggraini", "Budiman", "Cahyani", "Damarjati", "Efendi", "Fitriani",
    "Gunawan", "Hidayat", "Iskandar", "Jayadi", "Kusuma", "Lestari",
    "Mahendra", "Nugroho", "Puspita", "Rahmawati", "Setiawan", "Utama",
    "Wibowo", "Yuliana",
)

DECOY_ID_PREFIX = "DEC"


def _name_exists(name, taken):
    """True bila nama sudah dipakai pelanggan asli atau decoy sebelumnya."""
    return name.lower() in taken


def generate_decoy_identity(rng, taken_names):
    """Membuat satu pasangan (id, nama) sintetis yang belum terpakai.

    Args:
        rng: objek ``random.Random`` untuk reproducibility.
        taken_names: himpunan nama (lowercase) yang sudah terpakai, baik
            pelanggan asli maupun decoy sebelumnya.

    Returns:
        Tuple ``(decoy_id, name)``.
    """
    for _ in range(200):
        name = "{} {}".format(
            rng.choice(_SYNTHETIC_FIRST_NAMES),
            rng.choice(_SYNTHETIC_LAST_NAMES),
        )
        if not _name_exists(name, taken_names):
            return name
    # Cadangan Extrem: nama dengan penanda nomor agar tetap unik.
    fallback = "Warga Fiktif {}".format(rng.randint(1000, 9999))
    return fallback


def build_decoy_id(index):
    """ID decoy berformat ``DEC-001`` (berbeda dari ID pelanggan ``C###``)."""
    return "{}-{:03d}".format(DECOY_ID_PREFIX, index)
