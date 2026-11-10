"""Distribution-Transforming Encoder (DTE).

DTE adalah komponen inti Honey Encryption. DTE menyediakan dua fungsi yang
saling berbalik:

- ``encode(pesan)`` menghasilkan sebuah *seed* (bilangan bulat) yang
  menentukan pesan tersebut.
- ``decode(seed)`` mengembalikan pesan yang terikat pada seed itu.

Sifat penting yang membedakan DTE dari pemilihan acak biasa:

1. **Deterministik.** ``decode(encode(pesan)) == pesan`` selalu berlaku
   untuk setiap pesan yang sah.
2. **Distribusi terjaga.** Bila seed diambil secara acak seragam, pesan yang
   keluar dari ``decode`` mengikuti model probabilitas yang dirancang, bukan
   sebaran seragam.

Konstruksi yang dipakai di sini adalah pendekatan *inverse transform*
(sering disebut *alias method*): ruang seed dipecah menjadi interval
berurutan, masing-masing interval merupakan satu pesan, dan panjang interval
bersebanding dengan probabilitas pesan tersebut. Interval batasnya
dihitung dengan aritmetika bulat sehingga tidak ada galat pembulatan
floating point.

Rujukan: Juels, A., & Ristenpart, T. (2014). *Honey Encryption: Security
Beyond the Brute-Force Bound*. IEEE Security & Privacy, 12(4), 59-62.
"""

import bisect
import random


class DTESpace:
    """Ruang pesan dengan encoder dan decoder yang saling berbalik.

    Args:
        entries: daftar tuple ``(pesan, bobot)``. Bobot adalah bilangan
            bulat positif yang sebanding dengan probabilitas pesan.
        seed_bits: jumlah bit ruang seed. Default 64 bit.
    """

    def __init__(self, entries, seed_bits=64):
        if seed_bits < 1:
            raise ValueError("seed_bits minimal 1")
        if not entries:
            raise ValueError("ruang pesan tidak boleh kosong")

        total_weight = sum(weight for _, weight in entries)
        if total_weight <= 0:
            raise ValueError("total bobot harus lebih besar dari nol")
        if any(weight <= 0 for _, weight in entries):
            raise ValueError("setiap bobot harus lebih besar dari nol")

        # Pesan diurutkan menurut bobot menurun. Pinggiran pada bobot sama
        # diputuskan lewat repr pesan supaya urutannya deterministik.
        ordered = sorted(entries, key=lambda item: (-item[1], repr(item[0])))

        self.seed_bits = seed_bits
        self.scale = 1 << seed_bits
        if self.scale < len(ordered):
            raise ValueError(
                "seed_bits terlalu kecil untuk menampung {} pesan".format(
                    len(ordered)))

        self.messages = [message for message, _ in ordered]
        self.weights = [weight for _, weight in ordered]

        self._boundaries = self._build_boundaries(self.weights, self.scale)
        self._index = {message: i for i, message in enumerate(self.messages)}

    # -- pembangunan interval ------------------------------------------------

    @staticmethod
    def _build_boundaries(weights, scale):
        """Menghitung batas interval sebagai bilangan bulat.

        Batas kumulatif dihitung dari bobot kumulatif sehingga batas terakhir
        tepat sama dengan ``scale`` dan tidak ada celah yang hilang.
        """
        total_weight = sum(weights)
        widths = []
        for weight in weights:
            # Lebar minimal 1 supaya setiap pesan tetap punya seed yang bisa
            # dipilih, meskipun bobotnya sangat kecil.
            widths.append(max(1, (weight * scale) // total_weight))

        # Selisih pembulatan dialokasikan ke interval terlebar agar total
        # lebar tepat sama dengan scale.
        difference = scale - sum(widths)
        if difference != 0:
            widest = widths.index(max(widths))
            widths[widest] += difference

        boundaries = [0]
        for width in widths:
            boundaries.append(boundaries[-1] + width)
        return boundaries

    # -- encoder dan decoder -------------------------------------------------

    def encode(self, message, rng=None):
        """Mengubah pesan menjadi seed.

        Args:
            message: pesan yang ingin di-encode.
            rng: objek ``random.Random`` opsional agar hasil dapat
                direproduksi.

        Returns:
            Seed berupa bilangan bulat dalam rentang ``[0, scale)``.
        """
        if message not in self._index:
            raise KeyError("pesan tidak termasuk ruang pesan ini")
        index = self._index[message]
        start = self._boundaries[index]
        end = self._boundaries[index + 1]
        if rng is None:
            rng = random.Random()
        return rng.randrange(start, end)

    def decode(self, seed):
        """Mengubah seed kembali menjadi pesan.

        Args:
            seed: bilangan bulat dalam rentang ``[0, scale)``.

        Returns:
            Pesan yang terikat pada seed tersebut.
        """
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("seed harus berupa bilangan bulat")
        if not 0 <= seed < self.scale:
            raise ValueError(
                "seed di luar ruang pesan valid: {} bukan di [0, {})".format(
                    seed, self.scale))
        index = bisect.bisect_right(self._boundaries, seed) - 1
        return self.messages[index]

    # -- Sampling dan-ringkasan ----------------------------------------------

    def sample(self, rng=None):
        """Mengambil pesan secara acak sesuai model probabilitas.

        Setara dengan ``decode`` atas seed acak seragam.
        """
        if rng is None:
            rng = random.Random()
        return self.decode(rng.randrange(self.scale))

    def probability(self, message):
        """Probabilitas sebuah pesan menurut model."""
        if message not in self._index:
            raise KeyError("pesan tidak termasuk ruang pesan ini")
        return self.weights[self._index[message]] / sum(self.weights)

    def interval(self, message):
        """Rentang seed ``(awal, akhir)`` yang memetakan ke sebuah pesan."""
        if message not in self._index:
            raise KeyError("pesan tidak termasuk ruang pesan ini")
        index = self._index[message]
        return self._boundaries[index], self._boundaries[index + 1]

    def describe(self):
        """Menghasilkan ringkasan tiap pesan untuk ditampilkan.

        Returns:
            Daftar dict berisi pesan, bobot, probabilitas, dan rentang seed.
        """
        total_weight = sum(self.weights)
        rows = []
        for index, message in enumerate(self.messages):
            start, end = self._boundaries[index], self._boundaries[index + 1]
            rows.append({
                "message": message,
                "weight": self.weights[index],
                "probability": self.weights[index] / total_weight,
                "seed_start": start,
                "seed_end": end,
                "seed_count": end - start,
            })
        return rows

    def __len__(self):
        return len(self.messages)

    def __contains__(self, message):
        return message in self._index
