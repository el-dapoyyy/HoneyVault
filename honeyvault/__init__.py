"""Paket inti HoneyVault.

Struktur paket memakai nama `honeyvault` (bukan `app`) supaya tidak bentrok
dengan berkas `app.py` di root, yang berfungsi sebagai titik masuk aplikasi.
"""

import os
import sys

# Folder proyek (satu level di atas paket ini) perlu ada di sys.path agar
# modul `config` di root dapat diimpor dari mana pun aplikasi dijalankan.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from flask import Flask

from config import DEBUG, SECRET_KEY


def create_app():
    """Membuat dan mengembalikan objek aplikasi Flask."""
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    app.secret_key = SECRET_KEY
    app.config["DEBUG"] = DEBUG

    from honeyvault.routes import register_blueprints

    register_blueprints(app)
    return app
