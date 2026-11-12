"""Skema Honey Encryption: enkripsi seed berbasis PRF.

Skema yang diimplementasikan mengikuti konstruksi Juels dan Ristenpart (2014) dengan
*DTE* sebagai komponen message space. Ringkasnya:

1. Pesan ``m`` di-encode menjadi *seed* melalui DTE.
2. Seed tersebut di-mask dengan pseudorandom yang diturunkan dari kunci
   rahasia dan sebuah *nonce* (public seed). Hasilnya adalah *ciphertext*.
3. Saat dekripsi, mask dihitung ulang dari kunci dan nonce yang sama, lalu
   seed dipulihkan dan diterjemahkan kembali melalui DTE.

Konsekuensi penting dari skema ini adalah: bila kunci yang dipakai saat
dekripsi **salah**, mask yang dihasilkan berbeda, sehingga seed yang
dipulihkan juga berbeda dan acak. DTE lalu mengubah seed acak itu menjadi
pesan yang **masih masuk akal** dan mengikuti model distribusi dari data
pelanggan. Itulah inti Honey Encryption: kesalahan kunci tidak menghasilkan
korupsi yang mencolok, melainkan pesan yang meyakinkan.

Asumsi keamanan yang dipakai di sini:

- PRF diimplementasikan dengan HMAC-SHA256 dan dianggap fungsi pseudorandom
  ideal. Ini asumsi standar untuk prototipe, bukan implementasi produksi.
- Nonce tidak pernah dipakai ulang dengan kunci yang sama.
- Penyerang dapat menghitung PRF dengan kunci yang benar (mendekripsi
  ciphertext yang sama berulang kali), tetapi tidak dapat menebak kunci.
- Serangan brute force atas kunci menghasilkan pesan yang tampak sah, sehingga
  penyerang tidak dapat membedakan pesan asli dari pesan umpan hanya dari
  isinya.

Yang **belum** ditangani di prototipe ini: autentikasi, proteksi terhadap
serangan kanal samping, dan pengujian formal terhadap serangan kanal samping.

Rujukan: Juels, A., & Ristenpart, T. (2014). *Honey Encryption: Security
Beyond the Brute-Force Bound*. IEEE Security & Privacy, 12(4), 59-62.
"""

import hashlib
import hmac
import os
import secrets

from honeyvault.crypto.honeyvault_space import (
    build_message_space,
    decode_profile,
    encode_profile,
)

# Panjang kunci dalam bit.
KEY_SIZE_BITS = 128

# Panjang nonce dalam bit.
NONCE_SIZE_BITS = 128

# Jumlah bit ruang seed yang dipakai DTE.
DTE_SEED_BITS = 64


class HoneyEncryption:
    """Skema enkripsi Honey Encryption di atas DTE.

    Args:
        space: objek :class:`DTESpace` yang dipakai sebagai message space.
        cell_salaries: pemetaan pesan ke daftar saldo observasi, dipakai
            untuk membangkitkan nilai saldo dari pesan hasil decode.
        key: kunci rahasia berupa byte. Jika tidak diberi, kunci acak
            dibangkitkan.
        rng: objek ``random.Random`` opsional untuk membangkitkan seed DTE.
            Diberikan agar hasil eksperimen dapat direproduksi. Jika
            ``None``, seed diambil acak pada setiap pemanggilan.
    """

    def __init__(self, space, cell_salaries, key=None, rng=None):
        self.space = space
        self.cell_salaries = cell_salaries
        self.rng = rng
        if key is None:
            key = os.urandom(KEY_SIZE_BITS // 8)
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("kunci harus berupa byte")
        if len(key) < 16:
            raise ValueError("kunci terlalu pendek, minimal 16 byte")
        self.key = bytes(key)

    # -- primitif -------------------------------------------------------------

    def _mask(self, nonce):
        """Menghitung pseudorandom dari kunci dan nonce.

        Args:
            nonce: byte nonce.

        Returns:
            Integer sepanjang ruang seed DTE.
        """
        digest = hmac.new(self.key, nonce, hashlib.sha256).digest()
        # Ubah byte pertama menjadi integer ruang seed.
        return int.from_bytes(digest[:8], "big") % self.space.scale

    # -- enkripsi dan dekripsi ----------------------------------------------

    def encrypt(self, row, nonce=None):
        """Mengenkripsi satu baris pelanggan.

        Args:
            row: baris pelanggan yang akan dilindungi.
            nonce: byte nonce. Jika ``None``, nonce acak dibangkitkan.

        Returns:
            Dict berisi ``ciphertext``, ``nonce``, dan ``seed``.

            ``seed`` hanya berguna untuk verifikasi internal (misalnya
            menunjukkan bahwa XOR dua ciphertext sama dengan XOR dua seed
            saat nonce dipakai ulang). Seed adalah nilai sebelum dimasking,
            jadi **tidak boleh dikirim bersama ciphertext** kepada pihak
            lain.
        """
        if nonce is None:
            nonce = secrets.token_bytes(NONCE_SIZE_BITS // 8)

        # 1. Pesan -> seed lewat DTE.
        seed = encode_profile(self.space, row, rng=self.rng)

        # 2. Seed di-mask dengan pseudorandom dari kunci dan nonce.
        mask = self._mask(nonce)
        ciphertext = seed ^ mask

        return {
            "ciphertext": ciphertext,
            "nonce": nonce,
            "seed": seed,
        }

    def decrypt(self, ciphertext, nonce):
        """Mendekripsi ciphertext menjadi pesan.

        Dengan kunci yang benar, pesan asli pulih. Dengan kunci yang salah,
        pesan yang muncul tetap masuk akal namun berbeda dari aslinya.

        Args:
            ciphertext: integer hasil ``encrypt``.
            nonce: byte nonce yang dipakai saat enkripsi.

        Returns:
            Dict berisi ``message``, ``category``, ``tier``, ``balance``,
            ``recovered_seed``, dan ``is_correct_key``.
        """
        # 1. Mask dihitung ulang dari kunci dan nonce.
        mask = self._mask(nonce)

        # 2. Seed dipulihkan.
        recovered_seed = ciphertext ^ mask

        # 3. Seed diterjemahkan kembali melalui DTE.
        profile_row = decode_profile(
            self.space, self.cell_salaries, recovered_seed, rng=self.rng)

        return {
            "message": profile_row["message"],
            "category": profile_row["category"],
            "tier": profile_row["tier"],
            "balance": profile_row["balance"],
            "recovered_seed": recovered_seed,
        }


def deterministic_key(seed=0, size=KEY_SIZE_BITS // 8):
    """Membangkitkan kunci yang turunan deterministik dari sebuah seed.

    Fungsi ini dipakai oleh modul evaluasi supaya seluruh angka pada
    laporan dapat direproduksi. Pada pemakaian nyata, kunci harus diacak
    dan disimpan dengan aman, bukan diturunkan dari seed publik.

    Args:
        seed: nilai seed.
        size: panjang kunci dalam byte.

    Returns:
        Kunci berupa byte.
    """
    material = "honeyvault-key-{}".format(seed).encode("utf-8")
    return hashlib.sha256(material).digest()[:size]


def build_scheme(rows, key=None, seed_bits=DTE_SEED_BITS, rng=None):
    """Membangun skema Honey Encryption dari dataset pelanggan.

    Args:
        rows: dataset pelanggan.
        key: kunci rahasia opsional.
        seed_bits: ukuran ruang seed DTE.
        rng: objek ``random.Random`` opsional agar seed DTE dapat
            direproduksi.

    Returns:
        Objek :class:`HoneyEncryption`.
    """
    space, cell_salaries = build_message_space(rows, seed_bits=seed_bits)
    return HoneyEncryption(space, cell_salaries, key=key, rng=rng)


def wrong_key(scheme, key=None, rng=None):
    """Membuat skema dengan kunci berbeda, untuk simulasi kunci salah.

    Args:
        scheme: skema acuan.
        key: kunci baru. Jika ``None``, kunci acak dibangkitkan.
        rng: objek ``random.Random`` opsional agar seed DTE dapat
            direproduksi.

    Returns:
        Objek :class:`HoneyEncryption` dengan kunci berbeda.
    """
    if key is None:
        key = os.urandom(KEY_SIZE_BITS // 8)
    return HoneyEncryption(
        scheme.space, scheme.cell_salaries, key=key, rng=rng)


def generate_decoy_dataset(rows, count, scheme, seed=42):
    """Membuat dataset pesan umpan hasil dekripsi dengan kunci acak.

    Setiap pesan dienkripsi dengan nonce lalu didekripsi memakai kunci yang
    berbeda, meniru proses yang terjadi ketika penyerang mencoba
    menebak kunci.

    Args:
        rows: dataset pelanggan.
        count: jumlah baris yang dihasilkan.
        scheme: skema acuan (kuncinya tidak dipakai sebagai kunci benar).
        seed: seed RNG agar eksperimen dapat direproduksi.

    Returns:
        Daftar dict berisi profil hasil dekripsi kunci salah.
    """
    import random

    rng = random.Random(seed)
    other = wrong_key(scheme)

    decoys = []
    for index in range(1, count + 1):
        source = rows[rng.randrange(len(rows))]
        encrypted = scheme.encrypt(source)
        # Dekripsi memakai kunci yang berbeda.
        result = other.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        decoys.append({
            "id": "DEC-{:03d}".format(index),
            "name": "Honey Umpan {:03d}".format(index),
            "category": result["category"],
            "balance": result["balance"],
            "message": result["message"],
        })
    return decoys
