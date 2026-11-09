# HoneyVault — Panduan Pengembangan Proyek

> Dokumen handoff untuk melanjutkan proyek HoneyVault di Visual Studio Code.
>
> **Mata kuliah:** Kriptografi
> **Jenis aplikasi:** Web
> **Bahasa/framework:** Python + Flask
> **Status:** Prototipe tahap 3 — Adaptive Decoy dan evaluasi kuantitatif sudah berjalan.

## 1. Ringkasan proyek

HoneyVault adalah aplikasi web untuk mempelajari perlindungan data pelanggan
menggunakan konsep **Honey Encryption**. Dalam Honey Encryption, dekripsi dengan
kunci yang salah dirancang agar menghasilkan pesan umpan (*honey message*) yang
tetap terlihat masuk akal. Tujuannya adalah mempersulit penyerang membedakan
pesan asli dari pesan palsu.

Fokus pengembangan yang diusulkan adalah **Adaptive Decoy**: pembentukan data
umpan berdasarkan karakteristik statistik data pelanggan, seperti distribusi
saldo dan kategori pelanggan.

**Penting:** prototipe ini belum merupakan implementasi Honey Encryption
lengkap. Fitur yang sudah ada adalah pengelolaan data pelanggan sintetis, Data
Profiling, Random Decoy, Adaptive Decoy per kategori, evaluasi kuantitatif, dan
pengujian otomatis. DTE serta mekanisme enkripsi-dekripsi Honey Encryption
masih harus dikembangkan.

## 2. Tujuan

1. Membuat aplikasi web untuk mengelola data pelanggan sintetis.
2. Menganalisis karakteristik statistik data pelanggan.
3. Membuat decoy menggunakan Random Decoy sebagai baseline.
4. Membuat decoy menggunakan pendekatan Adaptive Decoy.
5. Membandingkan kedua metode melalui pengujian statistik dan waktu proses.
6. Menyiapkan rancangan integrasi Distribution-Transforming Encoder (DTE) dan
   Honey Encryption.

## 3. Kontribusi dan batas klaim

Honey Encryption bukan metode baru yang diklaim ditemukan dalam proyek ini.
Kontribusi yang diusulkan adalah:

- model pembentukan decoy yang menyesuaikan distribusi data pelanggan;
- perbandingan pendekatan adaptif dengan baseline acak;
- evaluasi kemiripan statistik dan kemampuan membedakan data asli dengan
  decoy;
- rancangan integrasi model distribusi dengan DTE.

Jangan menyatakan sistem sudah aman dari brute force atau sudah menerapkan
Honey Encryption penuh sebelum DTE dan mekanisme enkripsi-dekripsi benar-benar
diimplementasikan dan diuji.

## 4. Status prototipe

| Fitur | Status | Catatan |
| --- | --- | --- |
| Dashboard | Sudah ada | Data pelanggan sintetis |
| Data pelanggan | Sudah ada | Tambah pelanggan, muat dataset 150, reset |
| Data Profiling | Sudah ada | Count, mean, median, std. deviasi, min, max, kuartil, per kategori |
| Random Decoy | Sudah ada | Baseline acak, rentang sama dengan data asli |
| Adaptive Decoy | Sudah ada | Gaussian per kategori, korelasi kategori–saldo dipertahankan |
| Identitas sintetis | Sudah ada | Nama dan ID decoy tidak pernah menyalin data asli |
| Evaluasi/perbandingan | Sudah ada | Mean, std. deviasi, histogram, Wasserstein, KS, classifier, waktu |
| Random seed | Sudah ada | Eksperimen dapat direproduksi |
| Pengujian otomatis | Sudah ada | 40 test dengan pytest |
| Enkripsi data | Belum ada | Rancang pada tahap berikutnya |
| DTE | Belum ada | Komponen penting Honey Encryption |
| Dekripsi salah-kunci yang menghasilkan decoy | Belum ada | Belum boleh diklaim sebagai fitur |

### Catatan Adaptive Decoy

Adaptive Decoy membangkitkan saldo dari model Gaussian **per kategori**: kategori
decoy dipilih mengikuti frekuensi kategori pada dataset, lalu saldo diambil dari
mean dan standar deviasi kategori tersebut. Bila sebuah kategori hanya memiliki
satu observasi, nilai observasi itu yang dipakai; bila tidak ada, model global
digunakan sebagai cadangan. Semua nilai dibatasi pada rentang saldo data asli.

Karena itu korelasi kategori–saldo ikut dipertahankan, bukan hanya distribusi
marginal saldo. Batasannya tetap: model ini masih Gaussian dan belum
mempertimbangkan skewness, heavy tail, atau struktur waktu.

Gunakan ID (`DEC-001`) dan nama sintetis untuk decoy. Nama decoy diambil dari
kumpulan nama fiktif terpisah dan dicek agar tidak pernah sama dengan nama
pelanggan mana pun pada dataset.

## 5. Teknologi

- Python 3
- Flask
- HTML dan CSS
- JSON untuk penyimpanan prototipe
- NumPy dan SciPy (perhitungan distribusi: Wasserstein, KS, histogram)
- pytest (pengujian otomatis)
- Visual Studio Code

Jangan memasukkan data pelanggan sungguhan.

## 6. Menjalankan proyek di VS Code

**Tidak perlu Laragon, XAMPP, MySQL, atau Apache.** Proyek ini memakai Python
+ Flask dan menyimpan data pada berkas JSON lokal. Laragon hanya relevan
bila proyek memakai PHP/MySQL, dan itu bukan kasus di sini.

### A. Buka folder

1. Buka VS Code.
2. Pilih **File → Open Folder**, lalu pilih folder proyek `HoneyVault`.
3. Buka terminal melalui **Terminal → New Terminal**.

Folder proyek sudah berisi seluruh kode. Berkas `HoneyVault_Flask_Prototype.zip`
adalah arsip cadangan dari versi awal dan **tidak perlu diekstrak**.

### B. Buat virtual environment

Windows:

``` powershell
py -m venv .venv
```

Aktifkan melalui PowerShell:

``` powershell
.\.venv\Scripts\Activate.ps1
```

Jika PowerShell memblokir aktivasi, gunakan Command Prompt:

``` cmd
.venv\Scripts\activate.bat
```

### C. Instal dependensi

``` bash
python -m pip install -r requirements.txt
```

Jika gagal, periksa isi `requirements.txt` dan import pada kode. Jangan
menebak dependensi tanpa memeriksa proyek.

### D. Jalankan aplikasi

``` bash
python app.py
```

Jika `python` tidak dikenali:

``` bash
py app.py
```

Buka alamat lokal yang ditampilkan terminal, biasanya:

``` text
http://127.0.0.1:5000
```

Hentikan server dengan `Ctrl + C`.

### E. Jalankan pengujian

``` bash
python -m pytest tests/ -v
```

### F. Pengaturan opsional

| Variabel | Default | Fungsi |
| --- | --- | --- |
| `HONEYVAULT_SECRET_KEY` | acak per proses | Kunci cookie sesi. Tetapkan agar sesi bertahan antar restart |
| `HONEYVAULT_DEBUG` | `0` | Isi `1` untuk auto-reload dan debugger Flask |
| `HONEYVAULT_HOST` | `127.0.0.1` | Alamat server |
| `HONEYVAULT_PORT` | `5000` | Port server |

Contoh di PowerShell:

``` powershell
$env:HONEYVAULT_DEBUG = "1"
python app.py
```

## 7. Struktur folder

Struktur yang berlaku sekarang. Paket memakai nama `honeyvault` (bukan `app`)
agar tidak bentrok dengan berkas `app.py` di root yang berfungsi sebagai titik
masuk.

``` text
HoneyVault/
├── app.py                     # titik masuk, memanggil create_app()
├── config.py                  # konfigurasi terpusat
├── requirements.txt
├── README.md
├── PROJECT_GUIDE.md
├── .gitignore
├── honeyvault/
│   ├── __init__.py            # create_app() factory
│   ├── storage.py             # baca/tulis data pelanggan JSON
│   ├── routes/
│   │   ├── __init__.py        # register_blueprints()
│   │   ├── dashboard.py
│   │   ├── simulation.py
│   │   └── evaluation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── profiling.py       # Data Profiling
│   │   ├── decoy.py           # Random & Adaptive Decoy
│   │   ├── evaluation.py      # metrik kuantitatif
│   │   ├── identity.py        # generator identitas sintetis
│   │   └── synthetic_dataset.py
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── simulation.html
│       └── evaluation.html
├── static/
│   └── style.css
├── data/
│   ├── customers.json         # dataset aktif (diabaikan git)
│   └── synthetic_customers.json
└── tests/
    ├── test_profiling.py
    ├── test_decoy.py
    ├── test_evaluation.py
    └── test_app.py
```

Folder `honeyvault/crypto/` dengan `dte.py` dan `honey_encryption.py` akan
ditambahkan pada Tahap 4 dan 5, setelah model distribusi DTE dirancang.

## 8. Alur penggunaan prototipe

1. Pengguna membuka dashboard HoneyVault.
2. Sistem menampilkan data pelanggan sintetis.
3. Pengguna menambahkan pelanggan, memuat dataset 150, atau memakai data
   contoh.
4. Pengguna menjalankan Data Profiling (otomatis tampil di dashboard).
5. Pengguna menjalankan Random Decoy pada halaman Simulasi.
6. Sistem menghasilkan data umpan acak pada rentang yang sama dengan data asli.
7. Pengguna menjalankan Adaptive Decoy.
8. Sistem menghasilkan data umpan berdasarkan model Gaussian per kategori.
9. Pengguna membuka halaman Evaluasi untuk membandingkan kedua metode melalui
   metrik statistik.

## 9. Alur Honey Encryption penuh yang direncanakan

1. Pengguna memilih data sintetis yang akan dilindungi.
2. Sistem membentuk model distribusi pesan dan DTE.
3. Pesan diubah menjadi seed melalui proses encoding DTE.
4. Seed diamankan menggunakan skema Honey Encryption yang sesuai.
5. Saat dekripsi dilakukan, seed diterjemahkan kembali melalui DTE.
6. Dengan kunci benar, sistem diharapkan memperoleh pesan asli.
7. Dengan kunci salah, sistem diharapkan memperoleh pesan umpan yang masuk akal.
8. Peneliti mengevaluasi apakah pesan umpan sulit dibedakan dari pesan asli.

**Catatan kriptografi:** mengenkripsi JSON dengan AES-GCM lalu menampilkan data
palsu ketika autentikasi gagal bukan Honey Encryption. Itu hanya fallback
aplikasi. DTE harus menjadi bagian nyata dari skema Honey Encryption.

## 10. Roadmap pengembangan

### Tahap 1 — Pastikan prototipe berjalan

- [x] Buka folder di VS Code.
- [x] Instal dependensi.
- [x] Jalankan `python app.py`.
- [x] Uji dashboard, data pelanggan, profiling, Random Decoy, Adaptive Decoy,
      dan evaluasi.
- [x] Tambahkan pengujian otomatis.

**Kriteria selesai:** semua fitur prototipe yang tersedia dapat dicoba.
**Status:** selesai.

### Tahap 2 — Rapikan data dan model adaptif

- [x] Gunakan dataset sintetis yang lebih besar (150 pelanggan).
- [x] Pisahkan fungsi profiling, Random Decoy, Adaptive Decoy, dan evaluasi.
- [x] Buat ID decoy sintetis yang berbeda dari ID pelanggan.
- [x] Jangan menyalin nama atau identitas asli ke decoy.
- [x] Pastikan hasil generator mengikuti batas yang ditentukan.
- [x] Pertimbangkan hubungan antara kategori dan saldo.
- [x] Tambahkan random seed agar eksperimen dapat diulang.

**Kriteria selesai:** generator dapat diuji berulang dengan parameter yang
terdokumentasi.
**Status:** selesai.

### Tahap 3 — Evaluasi kuantitatif

Metrik yang dipakai:

1. Perbedaan mean saldo.
2. Perbedaan standar deviasi.
3. Overlap histogram (koefisien tumpang tindih 0 sampai 1).
4. Wasserstein distance dan statistik Kolmogorov-Smirnov.
5. Waktu pembentukan decoy.
6. Kemampuan classifier membedakan data asli dan decoy, memakai pemisahan data
   latih dan uji yang benar.

Jarak distribusi yang lebih kecil berarti distribusi lebih dekat, tetapi tidak
otomatis membuktikan keamanan kriptografi.

**Kriteria selesai:** hasil kedua metode dapat dibandingkan melalui tabel dan
eksperimen dapat diulang.
**Status:** selesai. Halaman `/evaluation` menampilkan tabel perbandingan.

### Tahap 4 — Rancang DTE

Tentukan:

- format pesan yang didukung;
- ruang pesan dan model probabilitas;
- cara mengurutkan pesan berdasarkan probabilitas;
- pemetaan pesan ke seed;
- cara mengubah seed kembali menjadi pesan;
- perilaku untuk seed di luar ruang pesan valid;
- konsistensi encoding dan decoding.

Mulai dengan ruang pesan sintetis yang kecil. Uji sifat dasar:

``` python
decode(encode(message)) == message
```

untuk seluruh pesan valid dalam ruang uji.

Sampling Gaussian sederhana bukan pengganti DTE.

### Tahap 5 — Integrasikan Honey Encryption

Setelah DTE dirancang dan diuji, pelajari skema Honey Encryption dari literatur
primer dan implementasikan sesuai spesifikasi yang dapat diverifikasi. Jangan
merancang skema kriptografi baru untuk penggunaan nyata hanya berdasarkan
intuisi. Dokumentasikan asumsi keamanan, threat model, dan batasan.

**Kriteria selesai:** kunci benar mengembalikan pesan asli dan kunci salah
menghasilkan pesan umpan melalui DTE, bukan melalui fallback antarmuka.

### Tahap 6 — Pengujian dan dokumentasi

- [x] Uji input valid dan tidak valid.
- [ ] Uji konsistensi DTE.
- [ ] Uji enkripsi dan dekripsi.
- [ ] Uji skenario kunci benar dan salah.
- [x] Evaluasi kemiripan distribusi decoy.
- [x] Catat waktu proses dan batasan sistem.
- [ ] Dokumentasikan hasil dalam laporan dan presentasi.

## 11. Rancangan pengujian

| Pengujian | Skenario | Hasil yang diharapkan |
| --- | --- | --- |
| Profiling | Dataset sintetis | Statistik sesuai perhitungan |
| Random Decoy | Jalankan generator acak | Decoy terbentuk |
| Adaptive Decoy | Jalankan generator adaptif | Decoy mengikuti model |
| Batas nilai | Uji nilai ekstrem | Hasil mengikuti batas |
| Reproducibility | Seed eksperimen sama | Hasil dapat direproduksi |
| Identitas decoy | Bandingkan nama decoy vs pelanggan | Tidak ada nama yang sama |
| DTE round-trip | Encode lalu decode pesan valid | Pesan kembali sama |
| Enkripsi benar | Kunci benar | Pesan asli kembali |
| Enkripsi salah | Kunci salah | Decoy melalui DTE |
| Evaluasi | Bandingkan dua metode | Metrik tercatat |

Pengujian otomatis ada di `tests/` dan dijalankan dengan `python -m pytest`.

## 12. Risiko dan batasan

1. **Dataset terlalu kecil:** model distribusi tidak mewakili populasi. Gunakan
   dataset sintetis lebih besar dan beberapa skenario.
2. **Gaussian terlalu sederhana:** saldo mungkin tidak berdistribusi normal.
   Bandingkan beberapa model.
3. **Korelasi atribut masih parsial:** saldo dan kategori kini diperhitungkan,
   tetapi struktur waktu dan multivariat belum.
4. **Decoy membocorkan informasi:** nama dan ID decoy sintetis, dicek agar tidak
   pernah sama dengan pelanggan asli.
5. **Klaim Honey Encryption keliru:** generator decoy saja belum merupakan
   Honey Encryption.
6. **Keamanan web:** prototipe lokal bukan aplikasi produksi. Jangan menyimpan
   data nyata atau mempublikasikan server debug. Mode debug dimatikan secara
   default.

## 13. Referensi awal

1. Juels, A., & Ristenpart, T. (2014). *Honey Encryption: Security Beyond the
   Brute-Force Bound*. IEEE Security & Privacy, 12(4), 59-62.
   https://doi.org/10.1109/MSP.2014.67
2. Abiodun, E. O., Jantan, A., Abiodun, I. O., & Poston, H. E. (2019). *A
   Comprehensive Review of Honey Encryption Scheme*. Indonesian Journal of
   Electrical Engineering and Computer Science, 13(2), 649-656.
   https://doi.org/10.11591/ijeecs.v13.i2.pp649-656
3. Yin, W., Indulska, J., & Zhou, H. (2017). *Protecting Private Data by Honey
   Encryption*. Security and Communication Networks, 2017, Article 6760532.
   https://doi.org/10.1155/2017/6760532

Periksa kembali metadata dan format sitasi sesuai pedoman kampus sebelum
laporan diserahkan.

## 14. Instruksi untuk asisten AI di VS Code

Salin instruksi berikut ke asisten AI setelah membuka folder proyek:

> Saya sedang mengembangkan proyek kuliah Kriptografi bernama HoneyVault.
> Baca `PROJECT_GUIDE.md` terlebih dahulu, lalu periksa struktur dan isi kode
> proyek yang sebenarnya.
>
> Prototipe memakai Python dan Flask untuk mengelola data pelanggan sintetis,
> melakukan Data Profiling, membuat Random Decoy, membuat Adaptive Decoy per
> kategori, dan mengevaluasi perbandingannya.
>
> Jangan mengklaim proyek sudah mengimplementasikan Honey Encryption penuh.
> DTE dan mekanisme enkripsi-dekripsi masih harus dirancang dan diuji.
>
> Bantu saya melanjutkan proyek secara bertahap. Sebelum mengubah kode,
> jelaskan file yang akan diubah dan alasannya. Jangan menghapus fitur yang
> sudah berjalan. Setelah setiap perubahan, berikan perintah untuk menjalankan
> aplikasi dan pengujian. Prioritaskan kode yang mudah dipahami mahasiswa
> tingkat menengah, pengujian, keamanan dasar, dan dokumentasi.

## 15. Langkah berikutnya

1. Jalankan `python -m pytest tests/ -v` untuk memastikan pengujian lulus.
2. Jalankan `python app.py` lalu buka `http://127.0.0.1:5000/evaluation`.
3. Bandingkan Random Decoy dan Adaptive Decoy pada dataset 150 pelanggan.
4. Catat hasil eksperimen (mean, Wasserstein, KS, akurasi classifier, waktu).
5. Rancang DTE pada ruang pesan saldo yang kecil.
6. Integrasikan DTE dengan skema Honey Encryption sesuai literatur primer.
7. Uji skenario kunci benar dan kunci salah.

**Prioritas saat ini:** evaluations sudah berjalan. Selanjutnya rancang DTE,
lalu integrasikan Honey Encryption, dan lengkapi pengujian serta laporan.
