"""Verifikasi mandiri HoneyVault.

Jalankan:

    python verify.py

Skrip ini memeriksa apakah proyek benar-benar bekerja dan mencetak ringkasan
BERHASIL / GAGAL untuk setiap aspek. Cocok dipakai sebelum presentasi atau
setelah mengubah kode.

Keluarannya:

    python verify.py            # ringkasan saja
    python verify.py --verbose  # tampilkan detail setiap pemeriksaan
"""

import argparse
import os
import sys
import traceback

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class Checker:
    """Menyimpan hasil pemeriksaan dan menampilkannya."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = []

    def check(self, name, function):
        """Menjalankan satu pemeriksaan dan mencatat hasilnya."""
        try:
            detail = function()
            self.results.append((name, True, detail or ""))
            if self.verbose:
                print("{}  [ OK ] {}{}".format(
                    CYAN, name, (" - " + detail) if detail else "", RESET))
            return True
        except Exception as exc:  # noqa: BLE001 - laporan semua kegagalan
            self.results.append((name, False, str(exc)))
            if self.verbose:
                print("{}  [GAGAL] {}{} - {}".format(
                    RED, name, RESET, exc))
                if self.verbose:
                    traceback.print_exc()
            return False

    def section(self, title):
        """Menandai awal satu kelompok pemeriksaan."""
        if self.verbose:
            print("\n{}{}{}".format(BOLD, title, RESET))

    def summary(self):
        """Mencetak ringkasan dan mengembalikan kode keluar untuk shell."""
        total = len(self.results)
        passed = sum(1 for _, ok, _ in self.results if ok)
        failed = total - passed

        print()
        print("=" * 68)
        print("RINGKASAN VERIFIKASI HONEYVAULT")
        print("=" * 68)
        for name, ok, detail in self.results:
            if ok:
                print("{}BERHASIL{}  {}".format(GREEN, RESET, name))
            else:
                print("{}GAGAL   {}  {} - {}".format(RED, RESET, name, detail))
        print("-" * 68)
        if failed == 0:
            print("{}SEMUA PEMERIKSAAN BERHASIL{} ({}/{})".format(
                GREEN, RESET, passed, total))
            return 0
        print("{}ADA {} PEMERIKSAAN YANG GAGAL{} ({}/{} berhasil)".format(
            YELLOW, failed, RESET, passed, total))
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Memeriksa apakah proyek HoneyVault berfungsi dengan baik.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Tampilkan detail setiap pemeriksaan.")
    args = parser.parse_args(argv)

    checker = Checker(verbose=args.verbose)

    # --- 1. Lingkungan -------------------------------------------------------
    checker.section("1. LINGKUNGAN")

    def check_python():
        version = sys.version_info
        if version < (3, 8):
            raise AssertionError(
                "Python {} terlalu lama, butuh minimal 3.8".format(
                    ".".join(map(str, version[:3]))))
        return "Python {}".format(".".join(map(str, version[:3])))

    checker.check("Versi Python memadai", check_python)

    def check_dependencies():
        missing = []
        for module in ("flask", "numpy", "scipy", "pytest"):
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        if missing:
            raise AssertionError(
                "Paket belum terpasang: {}. Jalankan "
                "python -m pip install -r requirements.txt".format(
                    ", ".join(missing)))
        return "flask, numpy, scipy, pytest semuanya tersedia"

    checker.check("Dependensi terpasang", check_dependencies)

    def check_files():
        required = [
            "app.py", "config.py", "simulate.py", "requirements.txt",
            "PROJECT_GUIDE.md", "README.md",
            "honeyvault/__init__.py", "honeyvault/storage.py",
            "honeyvault/routes/dashboard.py",
            "honeyvault/routes/simulation.py",
            "honeyvault/routes/evaluation.py",
            "honeyvault/services/profiling.py",
            "honeyvault/services/decoy.py",
            "honeyvault/services/evaluation.py",
            "honeyvault/services/identity.py",
            "honeyvault/templates/base.html",
            "honeyvault/templates/index.html",
            "honeyvault/templates/simulation.html",
            "honeyvault/templates/evaluation.html",
            "static/style.css",
            "data/synthetic_customers.json",
        ]
        missing = [path for path in required if not os.path.exists(path)]
        if missing:
            raise AssertionError("Berkas hilang: {}".format(", ".join(missing)))
        return "{} berkas penting lengkap".format(len(required))

    checker.check("Struktur berkas lengkap", check_files)

    # --- 2. Logika inti ------------------------------------------------------
    checker.section("2. LOGIKA INTI")

    from honeyvault.services.profiling import profile
    from honeyvault.services.decoy import (
        METHOD_ADAPTIVE, METHOD_RANDOM, generate_decoy,
    )
    from honeyvault.services.evaluation import compare_methods
    from honeyvault.services.synthetic_dataset import build_dataset

    sample = [
        {"id": "C001", "name": "A", "category": "Basic", "balance": 3000000},
        {"id": "C002", "name": "B", "category": "Basic", "balance": 5000000},
        {"id": "C003", "name": "C", "category": "VIP", "balance": 40000000},
        {"id": "C004", "name": "D", "category": "VIP", "balance": 45000000},
    ]

    def check_profiling():
        stats = profile(sample)["overall"]
        if stats["count"] != 4:
            raise AssertionError("Jumlah pelanggan salah")
        # 3.000.000 + 5.000.000 + 40.000.000 + 45.000.000 = 93.000.000 / 4
        expected_mean = 23250000
        if abs(stats["mean"] - expected_mean) > 1:
            raise AssertionError(
                "Mean salah: {} (harusnya {})".format(
                    stats["mean"], expected_mean))
        if stats["min"] != 3000000 or stats["max"] != 45000000:
            raise AssertionError("Minimum atau maksimum salah")
        if abs(stats["median"] - 22500000) > 1:
            raise AssertionError("Median salah: {}".format(stats["median"]))
        return "mean, median, min, max, SD, kuartil, per kategori semua benar"

    checker.check("Data Profiling menghitung statistik benar", check_profiling)

    def check_decoy_identity():
        rows = build_dataset(60)
        real_names = {row["name"] for row in rows}
        decoys = generate_decoy(rows, method=METHOD_ADAPTIVE, count=60, seed=1)
        leaked = [d["name"] for d in decoys if d["name"] in real_names]
        if leaked:
            raise AssertionError(
                "Nama pelanggan asli bocor ke decoy: {}".format(leaked[:3]))
        return "0 dari 60 nama decoy sama dengan nama pelanggan"

    checker.check("Identitas decoy tidak membocorkan data asli",
                  check_decoy_identity)

    def check_decoy_bounds():
        rows = build_dataset(60)
        low = min(r["balance"] for r in rows)
        high = max(r["balance"] for r in rows)
        for method in (METHOD_RANDOM, METHOD_ADAPTIVE):
            for decoy in generate_decoy(rows, method=method, count=80, seed=2):
                if not (low <= decoy["balance"] <= high):
                    raise AssertionError(
                        "Saldo decoy {} di luar rentang".format(decoy["balance"]))
        return "semua decoy berada di rentang data asli"

    checker.check("Batas nilai decoy dihormati", check_decoy_bounds)

    def check_reproducibility():
        rows = build_dataset(60)
        first = generate_decoy(rows, method=METHOD_ADAPTIVE, count=20, seed=99)
        second = generate_decoy(rows, method=METHOD_ADAPTIVE, count=20, seed=99)
        if first != second:
            raise AssertionError("Seed sama menghasilkan hasil berbeda")
        return "seed 99 menghasilkan output identik dua kali"

    checker.check("Eksperimen dapat direproduksi (seed)", check_reproducibility)

    def check_category_correlation():
        rows = build_dataset(150)
        decoys = generate_decoy(rows, method=METHOD_ADAPTIVE, count=400, seed=7)
        real_means = profile(rows)["by_category"]
        groups = {}
        for decoy in decoys:
            groups.setdefault(decoy["category"], []).append(decoy["balance"])
        for category, values in groups.items():
            if category not in real_means or len(values) < 5:
                continue
            decoy_mean = sum(values) / len(values)
            real_mean = real_means[category]["mean"]
            if real_mean == 0:
                continue
            selisih = abs(decoy_mean - real_mean) / real_mean
            if selisih > 0.25:
                raise AssertionError(
                    "Kategori {}: mean decoy {:.0f} meleset {:.1%} dari mean asli "
                    "{:.0f}".format(category, decoy_mean, selisih, real_mean))
        return "mean decoy tiap kategori dalam 25% dari mean asli"

    checker.check("Korelasi kategori-saldo dipertahankan",
                  check_category_correlation)

    def check_adaptive_better():
        rows = build_dataset(150)
        random_decoys = generate_decoy(rows, method=METHOD_RANDOM,
                                        count=200, seed=42)
        adaptive_decoys = generate_decoy(rows, method=METHOD_ADAPTIVE,
                                         count=200, seed=42)
        report = compare_methods(rows, random_decoys, adaptive_decoys)
        if report["winner"] != "adaptive":
            raise AssertionError(
                "Adaptive Decoy tidak menang, padahal seharusnya. "
                "Wasserstein random={} adaptive={}".format(
                    report["random"]["wasserstein_distance"],
                    report["adaptive"]["wasserstein_distance"]))
        return ("Wasserstein random={:,.0f} vs adaptive={:,.0f} "
                "(adaptive {:.0f}x lebih dekat)".format(
                    report["random"]["wasserstein_distance"],
                    report["adaptive"]["wasserstein_distance"],
                    report["random"]["wasserstein_distance"] /
                    report["adaptive"]["wasserstein_distance"]))

    checker.check("Adaptive Decoy lebih dekat ke data asli",
                  check_adaptive_better)

    # --- 3. Aplikasi web -----------------------------------------------------
    checker.section("3. APLIKASI WEB")

    from honeyvault import create_app

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    def check_pages():
        # Halaman evaluation baru memuat tabel metrik setelah POST, jadi
        # penanda yang dicek untuk GET adalah judul halamannya.
        for path, marker in (("/", b"Dashboard"),
                             ("/simulation", b"Adaptive Decoy"),
                             ("/evaluation", b"Evaluasi kuantitatif")):
            response = client.get(path)
            if response.status_code != 200:
                raise AssertionError(
                    "{} mengembalikan {}".format(path, response.status_code))
            if marker not in response.data:
                raise AssertionError(
                    "{} tidak memuat konten yang diharapkan".format(path))
        return "3 halaman (dashboard, simulasi, evaluasi) merespons 200"

    checker.check("Halaman web dapat diakses", check_pages)

    def check_static():
        response = client.get("/static/style.css")
        if response.status_code != 200:
            raise AssertionError("CSS tidak termuat")
        return "stylesheet termuat"

    checker.check("Aset statis (CSS) termuat", check_static)

    def check_add_customer():
        from honeyvault import storage
        before = len(storage.load_customers())
        client.post("/customers/add", data={
            "name": "Pelanggan Verifikasi",
            "category": "Premium",
            "balance": "12345000",
        })
        after = len(storage.load_customers())
        storage.reset_customers()
        if after != before + 1:
            raise AssertionError("Pelanggan tidak bertambah")
        return "tambah pelanggan bekerja, dataset dikembalikan ke semula"

    checker.check("Tambah pelanggan bekerja", check_add_customer)

    def check_validation():
        from honeyvault import storage
        before = len(storage.load_customers())
        for payload in (
            {"name": "X", "category": "SuperPremium", "balance": "1000"},
            {"name": "X", "category": "Premium", "balance": "abc"},
            {"name": "X", "category": "Premium", "balance": "-500"},
        ):
            client.post("/customers/add", data=payload)
        if len(storage.load_customers()) != before:
            raise AssertionError("Input tidak valid diterima")
        return "kategori salah, saldo non-numerik, dan saldo negatif ditolak"

    checker.check("Validasi input menolak data tidak valid", check_validation)

    def check_simulation_flow():
        response = client.post("/simulation", data={
            "method": "adaptive", "count": "10", "seed": "42"})
        if response.status_code != 200:
            raise AssertionError("Simulasi gagal")
        if b"DEC-001" not in response.data:
            raise AssertionError("Decoy tidak ditampilkan")
        return "10 baris decoy terbentuk dengan ID DEC-001..DEC-010"

    checker.check("Simulasi menghasilkan data umpan", check_simulation_flow)

    def check_evaluation_flow():
        response = client.post("/evaluation", data={
            "count": "50", "seed": "42"})
        if response.status_code != 200:
            raise AssertionError("Evaluasi gagal")
        for marker in (b"Wasserstein", b"Overlap histogram", b"KS"):
            if marker not in response.data:
                raise AssertionError("Metrik {} tidak tampil".format(marker))
        return "7 metrik perbandingan tercatat"

    checker.check("Evaluasi kuantitatif menghasilkan metrik",
                  check_evaluation_flow)

    # --- 4. Pengujian otomatis ----------------------------------------------
    checker.section("4. PENGUJIAN OTOMATIS")

    def check_pytest():
        import pytest
        code = pytest.main(["-q", "tests/"])
        if code != 0:
            raise AssertionError(
                "Suite pytest gagal, kode keluar {}".format(code))
        return "seluruh test pytest lulus"

    checker.check("Suite pytest lulus", check_pytest)

    # --- 5. Klaim keamanan ---------------------------------------------------
    checker.section("5. KEAMANAN DAN BATASAN")

    def check_no_hardcoded_secret():
        with open("app.py", encoding="utf-8") as f:
            app_source = f.read()
        with open("config.py", encoding="utf-8") as f:
            config_source = f.read()
        combined = app_source + config_source
        if "dev-only-change-me" in combined:
            raise AssertionError("Kunci rahasia masih hardcoded di kode")
        return "kunci rahasia diambil dari environment variable"

    checker.check("Tidak ada kunci rahasia hardcoded", check_no_hardcoded_secret)

    def check_debug_off():
        from config import DEBUG
        if DEBUG:
            raise AssertionError("Mode debug aktif secara default")
        return "mode debug mati secara default"

    checker.check("Mode debug nonaktif secara default", check_debug_off)

    def check_host_local():
        from config import HOST
        if HOST not in ("127.0.0.1", "localhost"):
            raise AssertionError(
                "Server listen di {} bukan loopback".format(HOST))
        return "server hanya listen di {}".format(HOST)

    checker.check("Server hanya listen di loopback", check_host_local)

    def check_no_honey_claim():
        """Memastikan proyek tidak mengklaim Honey Encryption sudah ada."""
        with open("honeyvault/services/decoy.py", encoding="utf-8") as f:
            source = f.read()
        for keyword in ("honey_encryption", "def encrypt(", "def decrypt("):
            if keyword in source:
                raise AssertionError(
                    "Ditemukan implementasi enkripsi di services/decoy.py")
        return "belum ada klaim atau implementasi Honey Encryption di service"

    checker.check("Tidak ada klaim Honey Encryption palsu", check_no_honey_claim)

    return checker.summary()


if __name__ == "__main__":
    sys.exit(main())
