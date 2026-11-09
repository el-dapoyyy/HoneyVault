"""Blueprint rute evaluasi: membandingkan Random Decoy dan Adaptive Decoy."""

from flask import Blueprint, render_template, request

from honeyvault import storage
from honeyvault.services.decoy import (
    DEFAULT_COUNT,
    MAX_COUNT,
    METHOD_ADAPTIVE,
    METHOD_RANDOM,
    generate_decoy,
)
from honeyvault.services.evaluation import compare_methods, time_generation
from honeyvault.services.profiling import profile

bp = Blueprint("evaluation", __name__)


@bp.route("/evaluation", methods=["GET", "POST"])
def evaluation():
    rows = storage.load_customers()
    stats = profile(rows)

    count = DEFAULT_COUNT
    seed = None
    report = None

    if request.method == "POST":
        try:
            count = max(1, min(int(request.form.get("count", DEFAULT_COUNT)),
                               MAX_COUNT))
        except (TypeError, ValueError):
            count = DEFAULT_COUNT

        raw_seed = request.form.get("seed", "").strip()
        if raw_seed:
            try:
                seed = int(raw_seed)
            except ValueError:
                seed = None

        random_rows, random_time = time_generation(
            generate_decoy, rows, method=METHOD_RANDOM, count=count, seed=seed
        )
        adaptive_rows, adaptive_time = time_generation(
            generate_decoy, rows, method=METHOD_ADAPTIVE, count=count, seed=seed
        )

        report = compare_methods(rows, random_rows, adaptive_rows)
        report["random"]["time_seconds"] = random_time
        report["adaptive"]["time_seconds"] = adaptive_time
        report["seed"] = seed
        report["count"] = count
        report["random_sample"] = random_rows[:10]
        report["adaptive_sample"] = adaptive_rows[:10]

    return render_template(
        "evaluation.html",
        stats=stats,
        report=report,
        count=count,
        seed=request.form.get("seed", "").strip() if request.method == "POST" else "",
    )
