"""Data Profiling: ringkasan statistik dataset pelanggan."""

import math
import statistics


def _values(rows, field):
    """Mengambil nilai numerik dari sebuah field pada sekumpulan baris."""
    out = []
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def _describe(values):
    """Statistik dasar untuk satu kumpulan angka."""
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "sd": 0.0,
            "min": 0.0,
            "max": 0.0,
            "sum": 0.0,
            "q1": 0.0,
            "q3": 0.0,
        }
    ordered = sorted(values)
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        # Sampel (stdev) karena data ini dianggap sampel dari populasi.
        "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "sum": math.fsum(values),
        "q1": _percentile(ordered, 25),
        "q3": _percentile(ordered, 75),
    }


def _percentile(ordered, pct):
    """Persentil dengan interpolasi linier pada data yang sudah terurut."""
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * pct / 100.0
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return ordered[int(pos)]
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def profile(rows, field="balance"):
    """Menghitung ringkasan statistik seluruh dataset dan per kategori.

    Args:
        rows: daftar dict pelanggan.
        field: field numerik yang diprofilkan (default ``balance``).

    Returns:
        Dict berisi ``overall``, ``by_category``, dan ``categories``.
    """
    values = _values(rows, field)
    overall = _describe(values)

    by_category = {}
    for row in rows:
        category = row.get("category", "Tidak Diketahui")
        by_category.setdefault(category, []).append(row)

    categories = sorted(by_category)
    per_category = {}
    for category in categories:
        per_category[category] = _describe(_values(by_category[category], field))

    return {
        "field": field,
        "overall": overall,
        "by_category": per_category,
        "categories": categories,
        "count_by_category": {
            category: len(by_category[category]) for category in categories
        },
    }


def observed_categories(rows):
    """Daftar kategori yang benar-benar muncul pada dataset.

    Dipakai oleh kedua generator decoy agar perbandingan statistical
    tidak unfair: Random Decoy dan Adaptive Decoy boleh memakai himpunan
    kategori yang sama.
    """
    categories = []
    for row in rows:
        category = row.get("category")
        if category and category not in categories:
            categories.append(category)
    return sorted(categories)
