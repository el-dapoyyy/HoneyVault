# HoneyVault

Prototype akademik untuk menguji **Adaptive Decoy Generation** pada dataset
pelanggan sintetis, dalam konteks konsep Honey Encryption.

## Kebutuhan

- Python 3.10 atau lebih baru
- **Tidak perlu Laragon, XAMPP, MySQL, atau Apache.** Proyek ini memakai
  Python + Flask dan menyimpan data pada berkas JSON lokal.

## Menjalankan di Windows

1. Buka folder proyek di VS Code, lalu buka terminal
   (**Terminal → New Terminal**).
2. Buat virtual environment dan aktifkan:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Jika PowerShell memblokir aktivasi, gunakan Command Prompt:
   `.venv\Scripts\activate.bat`

3. Instal dependensi:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Jalankan aplikasi:

   ```bash
   python app.py
   ```

   Jika `python` tidak dikenali, gunakan `py app.py`.

5. Buka `http://127.0.0.1:5000` di browser.

Hentikan server dengan `Ctrl + C`.

## Menjalankan pengujian

```bash
python -m pytest tests/ -v
```

## Membuat dataset sintetis besar

```bash
python -m honeyvault.services.synthetic_dataset
```

Atau gunakan tombol "Muat dataset sintetis besar" pada dashboard.

## Fitur

- Dashboard pelanggan fiktif, penambahan data, dan muat dataset 150 pelanggan.
- Profil statistik saldo: count, mean, median, standar deviasi, min, max,
  kuartil, dan rincian per kategori.
- **Random Decoy** sebagai baseline acak.
- **Adaptive Decoy** berbasis distribusi Gaussian per kategori.
- Identitas decoy sepenuhnya sintetis (`DEC-001` + nama fiktif terpisah).
- **Evaluasi kuantitatif**: selisih mean dan standar deviasi, overlap
  histogram, Wasserstein distance, statistik Kolmogorov-Smirnov, akurasi
  classifier pembeda, dan waktu pembentukan.
- Random seed sehingga eksperimen dapat direproduksi.

## Konfigurasi

| Variabel | Default | Fungsi |
| --- | --- | --- |
| `HONEYVAULT_SECRET_KEY` | acak per proses | Kunci cookie sesi |
| `HONEYVAULT_DEBUG` | `0` | Isi `1` untuk auto-reload dan debugger |
| `HONEYVAULT_HOST` | `127.0.0.1` | Alamat server |
| `HONEYVAULT_PORT` | `5000` | Port server |

```powershell
$env:HONEYVAULT_DEBUG = "1"
python app.py
```

## Batasan penting

Aplikasi ini **BELUM** mengimplementasikan Honey Encryption sesungguhnya. Belum
ada DTE (Distribution-Transforming Encoder), enkripsi, autentikasi, atau
perlindungan data produksi. Ini adalah prototipe untuk menguji satu komponen
usulan, yaitu generator decoy adaptif.

Gunakan data sintetis saja; jangan masukkan data pelanggan nyata. Server debug
hanya untuk pengembangan lokal dan mati secara default.
