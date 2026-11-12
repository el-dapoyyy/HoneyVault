"""Evaluasi keamanan Honey Encryption.

Yang diukur:

1. **Kerahasiaan pesan.** Apakah ciphertext membocorkan pesan asli?
2. **Plausibilitas umpan.** Apakah pesan hasil dekripsi kunci salah terlihat
   masuk akal?
3. **Ketidakdapatbedakan.** Apakah classifier dapat membedakan pesan asli
   dari pesan umpan hasil kunci salah?
4. **Efektivitas brute force.** Berapa banyak percobaan kunci yang dibutuhkan
   penyerang, dan apakah tiap percobaan menghasilkan pesan yang meyakinkan?

Catatan penting: pengukuran di sini bersifat empiris dan menunjukkan sifat
yang diharapkan dari implementasi prototipe. Ini **bukan** bukti keamanan
kriptografi formal. Bukti formal memerlukan analisis reductions terhadap
model keamanan yang dinyatakan, yang di luar cakupan prototipe.
"""

from collections import Counter
import random

from honeyvault.crypto.honey_encryption import (
    build_scheme,
    deterministic_key,
    wrong_key,
)
from honeyvault.crypto.honeyvault_space import balance_tier
from honeyvault.services.evaluation import (
    classifier_accuracy,
    histogram_overlap,
    ks_statistic,
    wasserstein_distance,
)


def _messages(rows):
    return [(row["category"], balance_tier(float(row["balance"])))
            for row in rows]


def _scheme_for(rows, seed, key=None, seed_bits=64):
    """Membangun skema yang deterministik terhadap seed.

    Kunci dan seed DTE diturunkan dari seed eksperimen sehingga seluruh
    angka pada laporan dapat direproduksi ulang. Pada pemakaian nyata,
    kunci harus diacak dan disimpan dengan aman.
    """
    if key is None:
        key = deterministic_key(seed)
    return build_scheme(
        rows, key=key, seed_bits=seed_bits, rng=random.Random(seed))


def _attacker_for(scheme, seed):
    """Membangun skema penyerang dengan kunci berbeda, deterministik."""
    return wrong_key(
        scheme,
        key=deterministic_key(seed + 1),
        rng=random.Random(seed + 1),
    )


def evaluate_correct_key_recovery(rows, key=None, samples=100, seed=42):
    """Mengukur seberapa sering kunci benar memulihkan pesan asli.

    Args:
        rows: dataset pelanggan.
        key: kunci rahasia opsional.
        samples: jumlah baris yang diuji.
        seed: seed eksperimen agar hasil dapat direproduksi.

    Returns:
        Dict berisi jumlah pulih, tingkat keberhasilan, dan daftar yang gagal.
    """
    scheme = _scheme_for(rows, seed, key)
    rng = random.Random(seed)
    step = max(1, len(rows) // samples)

    recovered = 0
    failures = []
    for row in rows[::step][:samples]:
        encrypted = scheme.encrypt(row, nonce=rng.randbytes(16))
        result = scheme.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        expected = (row["category"], balance_tier(float(row["balance"])))
        if result["message"] == expected:
            recovered += 1
        else:
            failures.append({
                "expected": expected,
                "actual": result["message"],
            })

    return {
        "checked": min(samples, len(rows[::step])),
        "recovered": recovered,
        "success_rate": recovered / max(1, min(samples, len(rows[::step]))),
        "failures": failures,
    }


def evaluate_wrong_key_plausibility(rows, count=200, key=None, seed=42):
    """Mengukur apakah pesan hasil dekripsi kunci salah masuk akal.

    Yang dinilai:

    - Berapa persen pesan umpan yang punya kategori valid.
    - Berapa persen pesan umpan yang mengikuti model distribusi DTE.
    - Apakah pesan umpan dapat dibedakan dari pesan asli.
    """
    scheme = _scheme_for(rows, seed, key)
    attacker = _attacker_for(scheme, seed)
    rng = random.Random(seed)

    real_messages = Counter(_messages(rows))

    decoys = []
    for _ in range(count):
        source = rows[rng.randrange(len(rows))]
        encrypted = scheme.encrypt(source, nonce=rng.randbytes(16))
        result = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        decoys.append({
            "category": result["category"],
            "balance": result["balance"],
            "message": result["message"],
        })

    decoy_messages = Counter(decoy["message"] for decoy in decoys)

    # Pesan umpan dianggap "masuk akal" bila kategorinya termasuk kategori
    # yang benar-benar ada pada dataset.
    observed_categories = {row["category"] for row in rows}
    valid_category = sum(
        1 for decoy in decoys if decoy["category"] in observed_categories)
    plausible_rate = valid_category / len(decoys)

    # Semua pesan hasil dekripsi wajib berasal dari ruang pesan DTE.
    in_space = sum(1 for decoy in decoys if decoy["message"] in scheme.space)

    return {
        "count": len(decoys),
        "plausible_rate": plausible_rate,
        "in_message_space_rate": in_space / len(decoys),
        "real_message_frequencies": {
            "{} / {}".format(*message): count / len(rows)
            for message, count in real_messages.items()
        },
        "decoy_message_frequencies": {
            "{} / {}".format(*message): count / len(decoys)
            for message, count in decoy_messages.items()
        },
        "decoys": decoys,
    }


def evaluate_indistinguishability(rows, count=300, key=None, seed=42):
    """Menguji apakah pesan asli dapat dibedakan dari pesan umpan.

    Returns:
        Dict metrik Wasserstein, histogram, KS, dan akurasi classifier.
    """
    scheme = _scheme_for(rows, seed, key)
    attacker = _attacker_for(scheme, seed)
    rng = random.Random(seed)
    decoys = []
    for _ in range(count):
        source = rows[rng.randrange(len(rows))]
        encrypted = scheme.encrypt(source, nonce=rng.randbytes(16))
        result = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        decoys.append({
            "category": result["category"],
            "balance": result["balance"],
        })

    real_values = [float(row["balance"]) for row in rows]
    decoy_values = [float(decoy["balance"]) for decoy in decoys]

    ks_stat, ks_pvalue = ks_statistic(real_values, decoy_values)

    return {
        "wasserstein_distance": wasserstein_distance(real_values, decoy_values),
        "histogram_overlap": histogram_overlap(real_values, decoy_values),
        "ks_statistic": ks_stat,
        "ks_pvalue": ks_pvalue,
        "classifier": classifier_accuracy(real_values, decoy_values, seed=seed),
    }


def evaluate_ciphertext_leakage(rows, samples=500, key=None, seed=123):
    """Menguji apakah ciphertext membocorkan pesan asli.

    Cara pengujiannya: sebaran ciphertext untuk pesan yang berbeda seharusnya
    identik. Diuji dengan statistik Kolmogorov-Smirnov antar kategori pesan.
    Bila ciphertext bocor, p-value antar pasangan kategori akan kecil.

    Args:
        rows: dataset pelanggan.
        samples: jumlah ciphertext yang diuji.
        key: kunci rahasia opsional.
        seed: seed eksperimen agar hasil dapat direproduksi.

    Returns:
        Dict berisi statistik sebaran ciphertext dan hasil uji KS.
    """
    from scipy import stats as scipy_stats

    scheme = _scheme_for(rows, seed, key)
    rng = random.Random(seed)

    ciphertexts = []
    by_category = {}
    for _ in range(samples):
        source = rows[rng.randrange(len(rows))]
        encrypted = scheme.encrypt(source, nonce=rng.randbytes(16))
        ciphertexts.append(encrypted["ciphertext"])
        by_category.setdefault(source["category"], []).append(
            encrypted["ciphertext"])

    # Uji apakah ciphertext untuk tiap kategori berbeda secara statistik.
    ks_results = []
    categories = sorted(by_category)
    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            result = scipy_stats.ks_2samp(
                by_category[categories[i]], by_category[categories[j]])
            ks_results.append({
                "pair": "{} vs {}".format(categories[i], categories[j]),
                "statistic": float(result.statistic),
                "pvalue": float(result.pvalue),
            })

    # Ciphertext juga dibandingkan dengan seed seragam acak. Bila identik,
    # berarti ciphertext tidak membawa informasi apa pun tentang pesan.
    uniform = [rng.randrange(scheme.space.scale) for _ in range(samples)]
    versus_uniform = scipy_stats.ks_2samp(ciphertexts, uniform)

    return {
        "samples": len(ciphertexts),
        "ciphertext_min": min(ciphertexts),
        "ciphertext_max": max(ciphertexts),
        "ciphertext_mean": sum(ciphertexts) / len(ciphertexts),
        "distinct_ratio": len(set(ciphertexts)) / len(ciphertexts),
        "ks_between_categories": ks_results,
        "ks_versus_uniform": {
            "statistic": float(versus_uniform.statistic),
            "pvalue": float(versus_uniform.pvalue),
        },
        # Kebocoran dianggap tidak ada bila tidak ada pasangan kategori dengan
        # p-value di bawah ambang 0.01.
        "leak_detected": any(r["pvalue"] < 0.01 for r in ks_results),
    }


def evaluate_nonce_reuse(rows, key=None, seed_bits=16, seed=17):
    """Menguji dampak penggunaan nonce yang sama dua kali.

    Bila nonce dipakai ulang, mask yang sama dipakai untuk dua ciphertext,
    sehingga mask saling menghilangkan::

        c1 XOR c2 = (s1 XOR mask) XOR (s2 XOR mask) = s1 XOR s2

    Identitas ini selalu berlaku dan inilah **mekanisme kebocorannya**:
    penyerang memperoleh XOR dua seed tanpa mengetahui kunci. Hal itu
    tidak mungkin terjadi pada skema dengan nonce unik.

    Efeknya dikuantifikasi: berapa banyak pasangan pesan yang konsisten dengan
    XOR teramati, dibandingkan dengan XOR kontrol acak. Nilai ini
    menunjukkan seberapa besar penyempitan yang diperoleh penyerang.

    Args:
        rows: dataset pelanggan.
        key: kunci rahasia opsional.
        seed_bits: ukuran ruang seed DTE.
        seed: seed eksperimen agar hasil dapat direproduksi.

    Returns:
        Dict berisi status kebocoran, rasio penyempitan, dan ukuran ruang
        pesan.
    """
    scheme = _scheme_for(rows, seed, key, seed_bits=seed_bits)
    rng = random.Random(seed)

    def xor_for_pair(row_a, row_b):
        nonce = b"\x07" * 16
        encrypted_a = scheme.encrypt(row_a, nonce=nonce)
        encrypted_b = scheme.encrypt(row_b, nonce=nonce)
        return encrypted_a["ciphertext"] ^ encrypted_b["ciphertext"]

    def consistent_pairs_for(x):
        """Pasangan pesan yang konsisten dengan nilai XOR tertentu.

        Pencarian dilakukan per sel pesan, bukan per baris pelanggan, karena
        beberapa pelanggan berbagi sel yang sama. Hanya nilai XOR pertama
        yang perlu dicari untuk tiap pasangan sel.
        """
        # Kumpulkan sel unik beserta intervalnya.
        cells = {}
        for row in rows:
            message = (row["category"], balance_tier(float(row["balance"])))
            if message not in cells:
                cells[message] = scheme.space.interval(message)

        pairs = []
        for message_a, (low_a, high_a) in cells.items():
            for message_b, (low_b, high_b) in cells.items():
                for seed_a in range(low_a, high_a):
                    seed_b = seed_a ^ x
                    if low_b <= seed_b < high_b:
                        pairs.append((message_a[0], message_b[0]))
                        break
        return pairs

    # Cari dua pesan dengan kategori berbeda.
    pair_a, pair_b = None, None
    for _ in range(200):
        candidate_a = rows[rng.randrange(len(rows))]
        candidate_b = rows[rng.randrange(len(rows))]
        if candidate_a["category"] != candidate_b["category"]:
            pair_a, pair_b = candidate_a, candidate_b
            break

    if pair_a is None:
        return {
            "leak_detected": False,
            "message_space_size": len(scheme.space),
            "consistent_pairs": [],
            "note": "tidak ditemukan pasangan pesan berbeda kategori",
        }

    nonce = b"\x07" * 16
    encrypted_a = scheme.encrypt(pair_a, nonce=nonce)
    encrypted_b = scheme.encrypt(pair_b, nonce=nonce)

    # Mekanisme kebocoran: mask saling menghilangkan sehingga penyerang
    # memperoleh XOR dua seed tanpa kunci.
    mask_cancels = (
        (encrypted_a["ciphertext"] ^ encrypted_b["ciphertext"])
        == (encrypted_a["seed"] ^ encrypted_b["seed"])
    )

    observed = xor_for_pair(pair_a, pair_b)
    observed_pairs = consistent_pairs_for(observed)

    # Kontrol: XOR acak yang tidak berasal dari pasangan pesan mana pun.
    control = rng.randrange(scheme.space.scale)
    control_pairs = consistent_pairs_for(control)

    total_pairs = len(rows) * len(rows)
    observed_ratio = len(observed_pairs) / total_pairs
    control_ratio = len(control_pairs) / total_pairs

    return {
        # Kebocoran terdeteksi bila mask benar-benar saling menghilangkan.
        "leak_detected": mask_cancels,
        "mask_cancels": mask_cancels,
        "message_space_size": len(scheme.space),
        "seed_bits": seed_bits,
        "observed_xor": observed,
        "consistent_pairs": observed_pairs,
        "consistent_pair_count": len(observed_pairs),
        "control_pair_count": len(control_pairs),
        "observed_ratio": observed_ratio,
        "control_ratio": control_ratio,
        "narrowing": control_ratio - observed_ratio,
    }


def brute_force_efficiency(rows, attempts=200, key=None, seed=42):
    """Mengukur efektivitas serangan brute force atas kunci.

    **Cara membaca hasil ini dengan benar.** Penyerang yang mencoba kunci
    acak akan sesekali mendapatkan pesan yang kebetulan sama dengan pesan
    asli. Itu **bukan** kelemahan skema, melainkan justru sifat yang
    diinginkan: karena ruang pesan kecil, tebakan yang salah tetap
    menghasilkan pesan yang masuk akal, sehingga penyerang tidak dapat
    membedakan mana yang benar tanpa finishing seluruh ruang kunci.

    Yang benar-benar dilindungi adalah **kerahasiaan**, bukan probabilitas
    pesan benar per percobaan. Ruang kunci 128 bit berarti penyerang perlu
    mencoba sekitar 2^128 kunci sebelum memastikan pesan aslinya.

    Returns:
        Dict berisi jumlah percobaan, tingkat kecocokan pesan, perkiraan
        jumlah percobaan, dan apakah semua tebakan terlihat masuk akal.
    """
    scheme = _scheme_for(rows, seed, key)
    rng = random.Random(seed)
    source = rows[rng.randrange(len(rows))]
    expected = (source["category"], balance_tier(float(source["balance"])))

    encrypted = scheme.encrypt(source, nonce=rng.randbytes(16))
    observed_categories = {row["category"] for row in rows}
    message_count = len(scheme.space)

    matches = 0
    always_plausible = True
    for attempt in range(attempts):
        # Setiap tebakan memakai kunci berbeda, seperti penyerang sungguhan.
        guess = wrong_key(
            scheme,
            key=deterministic_key(seed + attempt + 1),
            rng=random.Random(seed + attempt + 1),
        )
        result = guess.decrypt(encrypted["ciphertext"], encrypted["nonce"])
        if result["message"] == expected:
            matches += 1
        # Pesan hasil tebakan tetap harus masuk akal, itulah inti skema.
        if result["category"] not in observed_categories:
            always_plausible = False

    # Peluang acak mendapatkan pesan yang sama: 1 / jumlah pesan.
    chance = 1.0 / message_count

    return {
        "attempts": attempts,
        "matches": matches,
        "match_rate": matches / attempts,
        "expected_attempts": attempts / max(1, matches),
        "all_guesses_plausible": always_plausible,
        "message_space_size": message_count,
        "chance_by_guessing": chance,
        "key_space_size": 2 ** 128,
        "key_guesses_needed": 2 ** 128,
    }
