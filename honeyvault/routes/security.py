"""Blueprint rute keamanan: demonstrasi skema Honey Encryption."""

from flask import Blueprint, render_template, request

from honeyvault import storage
from honeyvault.crypto.honey_encryption import build_scheme, wrong_key
from honeyvault.crypto.honeyvault_space import balance_tier
from honeyvault.crypto.security_evaluation import (
    brute_force_efficiency,
    evaluate_correct_key_recovery,
    evaluate_ciphertext_leakage,
    evaluate_indistinguishability,
    evaluate_wrong_key_plausibility,
)

bp = Blueprint("security", __name__)


def _parse_int(raw, default):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


@bp.route("/security", methods=["GET", "POST"])
def security():
    rows = storage.load_customers()

    result = None
    if request.method == "POST":
        index = _parse_int(request.form.get("customer_index"), 0)
        source = rows[index % len(rows)]
        scheme = build_scheme(rows)

        encrypted = scheme.encrypt(source)

        # Kunci benar.
        correct = scheme.decrypt(encrypted["ciphertext"], encrypted["nonce"])

        # Kunci salah: tebakan penyerang atas kunci.
        attacker = wrong_key(scheme)
        wrong = attacker.decrypt(encrypted["ciphertext"], encrypted["nonce"])

        expected = (source["category"], balance_tier(float(source["balance"])))

        result = {
            "source": source,
            "expected_message": expected,
            "ciphertext": encrypted["ciphertext"],
            "nonce": encrypted["nonce"],
            "correct": correct,
            "wrong": wrong,
            "correct_matches": correct["message"] == expected,
        }

    return render_template(
        "security.html",
        rows=rows,
        result=result,
        recovery=evaluate_correct_key_recovery(rows, samples=60),
        plausibility=evaluate_wrong_key_plausibility(rows, count=200, seed=42),
        indistinguishability=evaluate_indistinguishability(
            rows, count=300, seed=42),
        leakage=evaluate_ciphertext_leakage(rows, samples=1500),
        brute_force=brute_force_efficiency(rows, attempts=200, seed=42),
    )
