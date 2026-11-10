"""Blueprint rute DTE: demonstrasi encode, decode, dan skenario kunci salah."""

import random

from flask import Blueprint, render_template, request

from honeyvault import storage
from honeyvault.crypto.dte_evaluation import (
    dte_consistency_check,
    evaluate_dte_quality,
    generate_dte_decoys,
)
from honeyvault.crypto.honeyvault_space import (
    balance_tier,
    build_message_space,
    decode_profile,
    encode_profile,
)

bp = Blueprint("dte", __name__)


def _parse_int(raw, default):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


@bp.route("/dte", methods=["GET", "POST"])
def dte():
    rows = storage.load_customers()
    space, cells = build_message_space(rows)

    result = None
    scenario = request.form.get("scenario", "correct") if request.method == "POST" else "correct"

    if request.method == "POST":
        seed_value = _parse_int(request.form.get("seed"), 42)
        customer_index = _parse_int(request.form.get("customer_index"), 0)

        if scenario == "wrong":
            # Skenario kunci salah: seed acak yang tidak ada hubungannya
            # dengan pelanggan. Pesan yang keluar tetap masuk akal.
            rng = random.Random(seed_value)
            dte_seed = rng.randrange(space.scale)
            source = None
        else:
            source = rows[customer_index % len(rows)]
            dte_seed = encode_profile(space, source, rng=random.Random(seed_value))

        decoded = decode_profile(space, cells, dte_seed,
                                 rng=random.Random(dte_seed))

        result = {
            "scenario": scenario,
            "dte_seed": dte_seed,
            "source": source,
            "decoded": decoded,
            "original_message": (
                (source["category"], balance_tier(float(source["balance"])))
                if source else None
            ),
        }

    return render_template(
        "dte.html",
        rows=rows,
        space=space,
        space_description=space.describe(),
        result=result,
        scenario=scenario,
        consistency=dte_consistency_check(rows),
        decoys=generate_dte_decoys(rows, count=8, seed=42),
        quality=evaluate_dte_quality(rows, count=300, seed=42),
    )
