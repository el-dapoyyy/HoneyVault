"""Blueprint rute simulasi: menjalankan generator decoy."""

from flask import Blueprint, render_template, request

from honeyvault import storage
from honeyvault.services.decoy import (
    DEFAULT_COUNT,
    MAX_COUNT,
    METHOD_ADAPTIVE,
    METHOD_RANDOM,
    generate_decoy,
)
from honeyvault.services.profiling import profile

bp = Blueprint("simulation", __name__)


def _parse_int(raw, default):
    """Mengubah input form menjadi integer dengan fallback aman."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


@bp.route("/simulation", methods=["GET", "POST"])
def simulation():
    rows = storage.load_customers()
    stats = profile(rows)

    method = request.form.get("method", METHOD_ADAPTIVE) \
        if request.method == "POST" else METHOD_ADAPTIVE
    if method not in (METHOD_RANDOM, METHOD_ADAPTIVE):
        method = METHOD_ADAPTIVE

    count = DEFAULT_COUNT
    seed = ""
    result = None

    if request.method == "POST":
        count = max(1, min(_parse_int(request.form.get("count"), DEFAULT_COUNT),
                           MAX_COUNT))
        seed = request.form.get("seed", "").strip()

        seed_value = None
        if seed:
            try:
                seed_value = int(seed)
            except ValueError:
                seed_value = None

        result = generate_decoy(rows, method=method, count=count, seed=seed_value)

    return render_template(
        "simulation.html",
        stats=stats,
        result=result,
        method=method,
        count=count,
        seed=seed,
        max_count=MAX_COUNT,
    )
