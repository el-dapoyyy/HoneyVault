"""Alat baris perintah untuk menjalankan eksperimen HoneyVault.

Contoh pemakaian:

    python simulate.py                       # ringkasan dengan seed acak
    python simulate.py --seed 42             # hasil dapat direproduksi
    python simulate.py --count 200 --seed 42 # jumlah decoy lebih besar
    python simulate.py --synthetic            # pakai dataset 150 pelanggan
    python simulate.py --method adaptive     # hanya satu metode
    python simulate.py --show-decoy          # tampilkan contoh data umpan

Keluarannya berupa tabel di terminal yang bisa disalin ke laporan.
"""

import argparse
import random
import statistics
import sys

from honeyvault.services.decoy import (
    METHOD_ADAPTIVE,
    METHOD_RANDOM,
    generate_decoy,
    resolve_bounds,
)
from honeyvault.services.evaluation import compare_methods, time_generation
from honeyvault.services.profiling import profile
from honeyvault.services.synthetic_dataset import build_dataset


def format_rupiah(value):
    """Mengubah angka menjadi format rupiah yang mudah dibaca."""
    if value != value:  # NaN
        return "n/a"
    return "Rp {:,.0f}".format(value)


def print_dataset_summary(rows):
    """Menampilkan ringkasan dataset pelanggan."""
    stats = profile(rows)
    overall = stats["overall"]

    print("=" * 68)
    print("DATASET PELANGGAN")
    print("=" * 68)
    print("Jumlah pelanggan   : {}".format(overall["count"]))
    print("Mean saldo         : {}".format(format_rupiah(overall["mean"])))
    print("Median saldo       : {}".format(format_rupiah(overall["median"])))
    print("Std. deviasi       : {}".format(format_rupiah(overall["sd"])))
    print("Minimum / maksimum : {} / {}".format(
        format_rupiah(overall["min"]), format_rupiah(overall["max"])))
    print("Kuartil 1 - 3      : {} - {}".format(
        format_rupiah(overall["q1"]), format_rupiah(overall["q3"])))
    print()
    print("Rincian per kategori:")
    print("  {:<10} {:>5} {:>16} {:>16}".format(
        "Kategori", "Jml", "Mean", "Std. deviasi"))
    for category in stats["categories"]:
        cat = stats["by_category"][category]
        print("  {:<10} {:>5} {:>16} {:>16}".format(
            category,
            stats["count_by_category"][category],
            format_rupiah(cat["mean"]),
            format_rupiah(cat["sd"]),
        ))
    print()


def print_method_table(rows, decoys, label):
    """Menampilkan statistik satu kelompok data."""
    values = [float(r["balance"]) for r in decoys]
    print("-" * 68)
    print("{} (n={})".format(label, len(values)))
    print("-" * 68)
    print("Mean         : {}".format(format_rupiah(statistics.fmean(values))))
    print("Std. deviasi : {}".format(format_rupiah(statistics.stdev(values))))
    print("Minimum      : {}".format(format_rupiah(min(values))))
    print("Maksimum     : {}".format(format_rupiah(max(values))))
    print()


def print_comparison(report):
    """Menampilkan tabel perbandingan metrik kedua metode."""
    random_metrics = report["random"]
    adaptive_metrics = report["adaptive"]

    print("=" * 68)
    print("PERBANDINGAN METRIK")
    print("=" * 68)
    print("{:<34} {:>15} {:>15}".format("Metrik", "Random", "Adaptive"))
    print("-" * 68)

    def row(name, random_value, adaptive_value, fmt="{:,.0f}"):
        print("{:<34} {:>15} {:>15}".format(
            name, fmt.format(random_value), fmt.format(adaptive_value)))

    row("Selisih mean saldo",
        random_metrics["mean_difference"], adaptive_metrics["mean_difference"])
    row("Selisih std. deviasi",
        random_metrics["sd_difference"], adaptive_metrics["sd_difference"])
    row("Overlap histogram (1 = identik)",
        random_metrics["histogram_overlap"], adaptive_metrics["histogram_overlap"],
        "{:.3f}")
    row("Wasserstein distance (kecil = dekat)",
        random_metrics["wasserstein_distance"],
        adaptive_metrics["wasserstein_distance"])
    row("Statistik KS (0..1)",
        random_metrics["ks_statistic"], adaptive_metrics["ks_statistic"], "{:.4f}")
    row("Akurasi classifier (data uji)",
        random_metrics["classifier"]["test_accuracy"],
        adaptive_metrics["classifier"]["test_accuracy"], "{:.3f}")
    row("Waktu pembentukan (ms)",
        random_metrics.get("time_seconds", 0.0) * 1000,
        adaptive_metrics.get("time_seconds", 0.0) * 1000, "{:.3f}")
    print("-" * 68)
    print("Metode terdekat pada jarak Wasserstein: {}".format(
        {"adaptive": "Adaptive Decoy",
         "random": "Random Decoy"}.get(report["winner"], report["winner"])))
    print()
    print("Catatan: jarak distribusi yang lebih kecil berarti distribusi lebih")
    print("dekat, tetapi tidak otomatis membuktikan keamanan kriptografi.")
    print()


def print_decoy_sample(decoys, limit=10):
    """Menampilkan contoh data umpan."""
    print("=" * 68)
    print("CONTOH DATA UMPAN ({} baris pertama dari {})".format(
        min(limit, len(decoys)), len(decoys)))
    print("=" * 68)
    print("{:<10} {:<24} {:<10} {:>16}".format(
        "ID", "Nama sintetis", "Kategori", "Saldo"))
    print("-" * 68)
    for row in decoys[:limit]:
        print("{:<10} {:<24} {:<10} {:>16}".format(
            row["id"], row["name"], row["category"],
            "{:,.0f}".format(row["balance"])))
    print()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Menjalankan eksperimen Adaptive Decoy pada HoneyVault.")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Seed RNG agar hasil dapat direproduksi. Kosongkan untuk acak.")
    parser.add_argument(
        "--count", type=int, default=100,
        help="Jumlah decoy per metode (default: 100).")
    parser.add_argument(
        "--method", choices=[METHOD_RANDOM, METHOD_ADAPTIVE], default=None,
        help="Tampilkan hanya satu metode.")
    parser.add_argument(
        "--synthetic", action="store_true",
        help="Gunakan dataset sintetis besar (150 pelanggan).")
    parser.add_argument(
        "--show-decoy", action="store_true",
        help="Tampilkan contoh baris data umpan.")
    args = parser.parse_args(argv)

    if args.synthetic:
        rows = build_dataset(150)
    else:
        from honeyvault import storage
        rows = storage.load_customers()

    if not rows:
        print("Dataset kosong. Jalankan aplikasi lebih dulu atau gunakan "
              "--synthetic.", file=sys.stderr)
        return 1

    print_dataset_summary(rows)

    seed_label = args.seed if args.seed is not None else "acak"
    print("Konfigurasi eksperimen")
    print("-" * 68)
    print("Jumlah decoy per metode : {}".format(args.count))
    print("Seed                    : {}".format(seed_label))
    print("Rentang nilai (message space): {} - {}".format(
        format_rupiah(resolve_bounds(rows)[0]),
        format_rupiah(resolve_bounds(rows)[1])))
    print()

    random_decoys, random_time = time_generation(
        generate_decoy, rows, method=METHOD_RANDOM, count=args.count, seed=args.seed)
    adaptive_decoys, adaptive_time = time_generation(
        generate_decoy, rows, method=METHOD_ADAPTIVE, count=args.count, seed=args.seed)

    report = compare_methods(rows, random_decoys, adaptive_decoys)
    report["random"]["time_seconds"] = random_time
    report["adaptive"]["time_seconds"] = adaptive_time

    if args.method is None:
        print_method_table(rows, random_decoys, "RANDOM DECOY (baseline)")
        print_method_table(rows, adaptive_decoys, "ADAPTIVE DECOY")
    elif args.method == METHOD_RANDOM:
        print_method_table(rows, random_decoys, "RANDOM DECOY (baseline)")
    else:
        print_method_table(rows, adaptive_decoys, "ADAPTIVE DECOY")

    print_comparison(report)

    if args.show_decoy:
        print_decoy_sample(
            random_decoys if args.method == METHOD_RANDOM else adaptive_decoys)

    return 0


if __name__ == "__main__":
    sys.exit(main())
