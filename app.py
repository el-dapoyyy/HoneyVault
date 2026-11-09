"""Titik masuk aplikasi HoneyVault.

Jalankan dengan:

    python app.py

Mode debug dan kunci rahasia diatur lewat environment variable, lihat
`config.py`.
"""

from honeyvault import create_app

app = create_app()

if __name__ == "__main__":
    from config import HOST, PORT

    print("HoneyVault berjalan di http://{}:{}".format(HOST, PORT))
    print("Tekan Ctrl+C untuk menghentikan server.")
    app.run(host=HOST, port=PORT, debug=app.config["DEBUG"])
