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

## Memverifikasi bahwa proyek benar-benar bekerja

```bash
python verify.py
```

Memeriksa 32 aspek (lingkungan, logika inti, DTE, skema Honey Encryption,
aplikasi web, pengujian otomatis, keamanan) dan mencetak ringkasan
BERHASIL/GAGAL. Keluar dengan kode `0` bila semua lulus.

Panduan lengkap, termasuk cara membuktikan test Anda benar-benar menangkap
masalah dan checklist manual di browser, ada di `TESTING.md`.

## Mensimulasikan tanpa browser

Untuk kebutuhan laporan, eksperimen bisa dijalankan langsung dari terminal:

```bash
python simulate.py --synthetic --count 200 --seed 42
```

| Argumen | Fungsi |
| --- | --- |
| `--synthetic` | Pakai dataset 150 pelanggan, bukan dataset aktif |
| `--count N` | Jumlah decoy per metode (default 100) |
| `--seed N` | Seed agar hasil dapat direproduksi |
| `--method random` / `--method adaptive` | Tampilkan hanya satu metode |
| `--show-decoy` | Tampilkan contoh baris data umpan |
| `--dte` | Tambahkan laporan kualitas DTE |
| `--honey` | Tambahkan laporan pengukuran keamanan Honey Encryption |

Keluarannya berupa tabel metrik yang bisa langsung disalin ke laporan.
Seed yang sama dengan data yang sama selalu menghasilkan angka yang sama.

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
- **DTE (Distribution-Transforming Encoder)**: `encode(pesan) -> seed` dan
  `decode(seed) -> pesan` yang deterministik dan menjaga model distribusi.
- **Skema Honey Encryption**: DTE sebagai message space, seed di-mask dengan
  pseudorandom HMAC-SHA256 dari kunci dan nonce. Kunci salah menghasilkan
  pesan yang **masih masuk akal**, bukan data rusak.
- **Evaluasi keamanan skema**: pemulihan kunci benar, plausibilitas pesan
  umpan, uji kebocoran ciphertext, ketidakdapatbedakan data asli vs umpan,
  dan efektivitas brute force atas kunci.
- Halaman `/security` untuk demonstrasi kunci benar versus kunci salah.
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

Skema Honey Encryption di prototipe ini sudah berjalan: DTE menjadi message
space, seed di-mask dengan pseudorandom HMAC-SHA256 yang diturunkan dari kunci
rahasia dan nonce. Kunci benar memulihkan pesan asli; kunci salah menghasilkan
pesan lain yang tetap mengikuti model distribusi data pelanggan.

Yang **belum** ada dan tidak boleh diklaim:

- **Bukti keamanan formal.** Pengukuran di `verify.py` dan halaman
  `/security` bersifat empiris, bukan analisis reductions terhadap model
  keamanan.
- **Autentikasi.** Ciphertext tidak dilindungi MAC, sehingga penyerang aktif
  bisa mengubah seed yang pulih (hasilnya tetap pesan yang sah, bukan data
  kacau). Honey Encryption memang tidak dirancang untuk tujuan itu.
- **Proteksi kanal samping.**
- **Produksi.** Prototipe lokal untuk penelitian kuliah, bukan aplikasi
  produksi. Jangan simpan data pelanggan nyata dan jangan publikasikan
  server debug.

Catatan: ruang pesan prototipe hanya sekitar 10 profil, jadi peluang acak
mendapatkan pesan yang benar per percobaan kunci bukan nol. Itu justru
sifat yang diinginkan Honey Encryption: tebakan yang salah tetap menghasilkan
pesan yang tampak sah, sehingga penyerang tidak bisa memakai "hasil kacau"
sebagai penanda tebakan salah.
