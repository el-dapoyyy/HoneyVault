"""Blueprint rute dashboard: daftar pelanggan, tambah pelanggan, dataset."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from config import CATEGORIES, MAX_BALANCE, MIN_BALANCE
from honeyvault import storage
from honeyvault.services.profiling import profile

bp = Blueprint("dashboard", __name__)


def _next_customer_id(rows):
    """ID pelanggan berikutnya yang tidak bentrok dengan ID yang ada."""
    used = {row.get("id") for row in rows}
    index = len(rows) + 1
    while "C{:03d}".format(index) in used:
        index += 1
    return "C{:03d}".format(index)


@bp.route("/")
def index():
    rows = storage.load_customers()
    stats = profile(rows)
    return render_template(
        "index.html",
        rows=rows,
        stats=stats,
        categories=CATEGORIES,
    )


@bp.post("/customers/add")
def add_customer():
    rows = storage.load_customers()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "Regular").strip()
    raw_balance = request.form.get("balance", "").strip()

    try:
        balance = float(raw_balance)
    except ValueError:
        flash("Saldo harus berupa angka.", "error")
        return redirect(url_for("dashboard.index"))

    if not name:
        flash("Nama pelanggan wajib diisi.", "error")
        return redirect(url_for("dashboard.index"))

    if category not in CATEGORIES:
        flash("Kategori tidak dikenal. Pilih salah satu: {}.".format(
            ", ".join(CATEGORIES)), "error")
        return redirect(url_for("dashboard.index"))

    if not (MIN_BALANCE <= balance <= MAX_BALANCE):
        flash("Saldo harus berada di antara {} dan {}.".format(
            MIN_BALANCE, MAX_BALANCE), "error")
        return redirect(url_for("dashboard.index"))

    rows.append({
        "id": _next_customer_id(rows),
        "name": name,
        "category": category,
        "balance": int(balance),
    })
    storage.save_customers(rows)
    flash("Pelanggan {} ditambahkan.".format(name), "success")
    return redirect(url_for("dashboard.index"))


@bp.post("/customers/reset")
def reset_dataset():
    storage.reset_customers()
    flash("Dataset contoh (8 pelanggan) dipulihkan.", "success")
    return redirect(url_for("dashboard.index"))


@bp.post("/customers/load-synthetic")
def load_synthetic():
    rows = storage.install_synthetic_dataset()
    if rows is None:
        flash(
            "Dataset sintetis besar belum tersedia. Jalankan: "
            "python -m honeyvault.services.synthetic_dataset",
            "error",
        )
    else:
        storage.save_customers(rows)
        flash("Dataset sintetis besar dimuat: {} pelanggan.".format(len(rows)),
              "success")
    return redirect(url_for("dashboard.index"))
