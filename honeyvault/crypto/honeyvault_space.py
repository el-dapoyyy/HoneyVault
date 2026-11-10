"""Model ruang pesan HoneyVault di atas DTE generik.

Ruang pesan yang dipakai adalah ringkasan profil pelanggan, bukan saldo
individual. Setiap pesan berbentuk tuple ``(kategori, tingkat_saldo)``:

    ("Regular", "10-20 jt")

Alasan memilih profil, bukan saldo mentah:

- Ruang pesan menjadi kecil dan terdefinisi jelas, sesuai anjuran roadmap
  untuk memulai dari ruang pesan sintetis sederhana.
- Setiap pesan punya probabilitas yang bisa dihitung dari data profil,
  sehingga model distribusi benar-benar berasal dari data pelanggan.
- Dua pelanggan dengan saldo berbeda tetapi profil serupa menghasilkan pesan
  yang sama, sehingga pesan yang dihasilkan tetap "masuk akal" dan tidak
  membocorkan nilai spesifik.

Dari setiap pesan, nilai saldo di dalam rentangnya dibangkitkan mengikuti
distribusi observasi pada sel tersebut. Jadi encoder menghasilkan dua lapis:
pesan profil melalui DTE, lalu saldo di dalam sel.
"""

import random

from honeyvault.crypto.dte import DTESpace
from honeyvault.services.profiling import profile

# Rentang tingkat saldo dalam rupiah. Dipilih agar cukup membedakan profil
# antar kategori tanpa membuat ruang pesan terlalu besar.
BALANCE_TIERS = (
    ("0-5 jt", 0, 5_000_000),
    ("5-10 jt", 5_000_000, 10_000_000),
    ("10-20 jt", 10_000_000, 20_000_000),
    ("20-35 jt", 20_000_000, 35_000_000),
    ("35-50 jt", 35_000_000, 50_000_000),
    ("50-70 jt", 50_000_000, 70_000_000),
    ("70 jt+", 70_000_000, float("inf")),
)


def balance_tier(balance):
    """Menentukan tingkat saldo untuk sebuah nilai."""
    for label, low, high in BALANCE_TIERS:
        if low <= balance < high:
            return label
    return BALANCE_TIERS[-1][0]


def build_message_space(rows, seed_bits=64):
    """Membangun ruang pesan DTE dari data pelanggan.

    Args:
        rows: dataset pelanggan.
        seed_bits: ukuran ruang seed dalam bit.

    Returns:
        Tuple ``(dte_space, cell_salaries)``:
        - ``dte_space``: objek :class:`DTESpace`.
        - ``cell_salaries``: dict pemetaan pesan ke daftar saldo observasi
          pada sel tersebut, dipakai untuk membangkitkan nilai saldo.
    """
    stats = profile(rows)
    entries = []
    cell_salaries = {}

    for category in stats["categories"]:
        category_rows = [r for r in rows if r.get("category") == category]
        if not category_rows:
            continue
        for tier_label, _, _ in BALANCE_TIERS:
            members = [
                float(r["balance"]) for r in category_rows
                if balance_tier(float(r["balance"])) == tier_label
            ]
            if not members:
                continue
            message = (category, tier_label)
            entries.append((message, len(members)))
            cell_salaries[message] = members

    if not entries:
        raise ValueError("tidak ada pesan yang bisa dibentuk dari dataset")

    return DTESpace(entries, seed_bits=seed_bits), cell_salaries


def encode_profile(space, row, rng=None):
    """Mengubah satu baris pelanggan menjadi seed.

    Args:
        space: objek DTE.
        row: baris pelanggan.
        rng: objek ``random.Random`` opsional.

    Returns:
        Seed bilangan bulat.
    """
    message = (row.get("category"), balance_tier(float(row["balance"])))
    return space.encode(message, rng=rng)


def decode_profile(space, cell_salaries, seed, rng=None):
    """Mengubah seed menjadi profil pelanggan beserta saldonya.

    Args:
        space: objek DTE.
        cell_salaries: pemetaan pesan ke daftar saldo observasi.
        seed: seed hasil encode.
        rng: objek ``random.Random`` opsional.

    Returns:
        Dict berisi ``category``, ``tier``, ``balance``, dan ``message``.
    """
    message = space.decode(seed)
    category, tier = message
    salaries = cell_salaries.get(message)

    if salaries:
        if rng is None:
            rng = random.Random()
        balance = rng.choice(salaries)
    else:
        # Sel tanpa observasi: gunakan titik tengah rentang tingkat.
        balance = _tier_midpoint(tier)

    return {
        "message": message,
        "category": category,
        "tier": tier,
        "balance": int(round(balance)),
    }


def _tier_midpoint(tier_label):
    """Nilai tengah suatu tingkat saldo."""
    for label, low, high in BALANCE_TIERS:
        if label == tier_label:
            if high == float("inf"):
                return low * 1.25
            return (low + high) / 2
    return 0.0
