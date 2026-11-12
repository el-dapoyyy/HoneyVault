# Laporan Proyek Kuliah Kriptografi — HoneyVault

> **Status dokumen:** kerangka laporan siap diisi. Bagian yang membutuhkan data
> pribadi ditandai dengan `[...]` dan **wajib diisi sendiri** sebelum
> diserahkan.
>
> Seluruh angka pada bab hasil diambil dari keluaran program yang benar-benar
> dijalankan, bukan angka contoh. Perintah untuk mereproduksinya tercantum di
> setiap tabel.

---

## Halaman Identitas

| | |
| --- | --- |
| Nama | [Nama Lengkap] |
| NIM | [Nomor Induk Mahasiswa] |
| Program studi | [Sistem Informasi / Informatika / Teknik Komputer] |
| Mata kuliah | Kriptografi |
| Kelompok | [Nomor Kelompok] |
| Dosen Pengampu | [Nama Dosen, S.T., M.T.] |
| Institusi | [Nama Universitas] |
| Tahun | [2025/2026] |

---

## Abstrak

HoneyVault adalah aplikasi web prototipe untuk mempelajari perlindungan data
pelanggan dengan konsep *Honey Encryption*. Ide dasarnya adalah membuat
kesalahan dekripsi tidak menghasilkan data rusak yang mencolok, melainkan pesan
umpan (*honey message*) yang tetap terlihat masuk akal. Dengan demikian
penyerang yang mencoba menebak kunci tidak dapat memakai "hasil yang kacau"
sebagai penanda bahwa tebakan salah.

Prototipe ini dibangun dengan Python dan Flask, menyimpan data pada berkas
JSON lokal, dan tidak memerlukan basis data eksternal. Kontribusi yang
diusulkan adalah model pembentukan data umpan yang **menyesuaiai distribusi
data pelanggan** (*adaptive decoy*), bukan pengambilan acak biasa. Pada
prototipe ini ada tiga lapis: (1) *Data Profiling* untuk memahami karakteristik
saldo per kategori; (2) *Distribution-Transforming Encoder* (DTE) yang mengubah
pesan profil menjadi *seed* secara deterministik sekaligus menjaga model
distribusi; dan (3) skema enkripsi Honey Encryption yang menutupi *seed* dengan
pseudorandom turunan kunci dan *nonce*.

Evaluasi kuantitatif dilakukan terhadap 150 pelanggan sintetis dengan metrik
selisih mean dan standar deviasi, *overlap histogram*, *Wasserstein distance*,
statistik Kolmogorov-Smirnov, akurasi *classifier* pembeda, dan waktu
pembentukan. Hasilnya menunjukkan adaptive decoy memiliki jarak distribusi yang
jauh lebih dekat ke data asli dibandingkan baseline acak (*Wasserstein*
1.708.387 berbanding 23.571.998), dan pada skema enkripsi kunci benar memulihkan
100 persen pesan asli sementara kunci salah menghasilkan pesan umpan yang 100
persen berada di ruang pesan sah dengan akurasi classifier pembeda 0,478,
angka yang mendekati 0,5 (tidak punya daya beda).

**Kata kunci:** Honey Encryption, Distribution-Transforming Encoder, adaptive
decoy, kriptografi, Flask, distribusi data.

---

## 1. Pendahuluan

### 1.1 Latar Belakang

Kerahasiaan data pelanggan adalah masalah klasik. Umumnya, data sensitif
disimpan dengan enkripsi simetris: pemulihannya hanya bisa dilakukan dengan
kunci yang benar, dan kunci yang salah menghasilkan galat autentikasi yang
jelas. Justru kejelasan galat itulah yang menjadi titik lemah: seorang penyerang
dapat mencoba kunci secara membabi buta dan langsung tahu kapan tebakan
meleset.

*Honey Encryption* (Juels dan Ristenpart, 2014) mengubah aturan main tersebut.
Alih-alih ciphertext acak, ciphertext dirancang sehingga **kunci yang salah
tetap menghasilkan pesan yang masuk akal**. Dengan begitu, keabsahan pesan
tidak lagi menjadi penanda kesalahan kunci.

Konsep ini memiliki dua prasyarat yang harus dipenuhi:

1. harus ada *message space* berupa kumpulan pesan dengan model probabilitas
   yang berasal dari data nyata, sehingga pesan umpan sulit dibedakan dengan
   pesan asli;
2. harus ada fungsi pengubah pesan menjadi nilai acak yang bisa ditutupi dan
   dibalik kembali secara deterministik.

Prasyarat pertama dijawab pada Tahap 2-3 prototipe ini (data profiling dan
adaptive decoy), prasyarat kedua dijawab dengan *Distribution-Transforming
Encoder* (DTE), dan penggabungan keduanya dijawab dengan skema enkripsi pada
Tahap 5.

### 1.2 Rumusan Masalah

1. Bagaimana cara membentuk data umpan yang **tidak** memakai pengambilan acak
   murni, melainkan mengikuti distribusi saldo dan kategori pelanggan?
2. Bagaimana cara mengukur secara kuantitatif seberapa dekat data umpan
   terhadap data asli, dan apakah data umpan dapat dibedakan dengan data
   asli?
3. Bagaimana cara mengubah pesan menjadi nilai *seed* secara deterministik
   sekaligus menjaga model distribusi, sehingga nilainya bisa dipakai sebagai
   message space dalam Honey Encryption?
4. Bagaimana skema Honey Encryption dengan DTE sebagai message space berperilaku
   terhadap kunci benar, kunci salah, kebocoran *ciphertext*, dan serangan
   *brute force* atas kunci?

### 1.3 Tujuan

1. Membangun aplikasi web pengelolaan data pelanggan sintetis.
2. Melakukan *Data Profiling* terhadap data pelanggan.
3. Membandingkan *Random Decoy* (baseline) dengan *Adaptive Decoy*.
4. Merancang dan menguji DTE sebagai message space.
5. Mengintegrasikan DTE ke dalam skema Honey Encryption serta mengukur sifat
   keamanannya secara empiris.
6. Menyediakan pengujian otomatis dan verifikasi mandiri yang dapat
   direproduksi.

### 1.4 Manfaat

- Bagi mahasiswa: platform yang menunjukkan secara konkret bagaimana konsep
  kriptografi "pesan umpan" bekerja, bukan sekadar teori.
- Bagi penilaian: seluruh eksperimen dapat direproduksi dengan satu perintah
  dan satu *seed*.

### 1.5 Batasan

- Seluruh data bersifat sintetis. Tidak ada data pelanggan nyata.
- Prototipe berjalan lokal (loopback `127.0.0.1`), bukan aplikasi produksi.
- Pengukuran keamanan bersifat **empiris**, bukan bukti keamanan formal.
- Autentikasi dan proteksi kanal samping belum dikerjakan.

---

## 2. Tinjauan Pustaka

### 2.1 Honey Encryption

Juels dan Ristenpart (2014) mengajukan *Honey Encryption* untuk mengatasi batas
brute force pada skema enkripsi simetris biasa. Ide dasarnya: jika kunci salah
akan menghasilkan pesan yang jelas tidak valid, penyerang dengan cepat tahu
tebakan gagal dan dapat memperkecil ruang pencarian kunci. Dengan
*honey encryption*, setiap tebakan kunci menghasilkan pesan yang
*plausibel*, sehingga penyerang hanya bisa memastikan tebakan
benarnya dengan menyelesaikan seluruh ruang kunci.

Skema yang dipakai pada literatur diringkas sebagai:

```
seed  <- DTE(pesan)
c     <- seed XOR PRF(kunci, nonce)
pesan <- DTE^-1(c XOR PRF(kunci, nonce))
```

Kunci yang salah menghasilkan `PRF` yang berbeda, sehingga `c XOR
PRF(kunci_salah)` adalah nilai yang tersebar acak; DTE memetakannya kembali ke
pesan yang berada di ruang pesan sah.

### 2.2 Distribution-Transforming Encoder (DTE)

DTE diperkenalkan oleh Juels dan Ristenpart sebagai komponen message space.
Fungsinya memetakan pesan ke nilai acak (disebut *seed*) sedemikian rupa
sehingga **sampling seed secara seragam menghasilkan pesan sesuai model
probabilitas** yang dirancang, bukan sebaran seragam. Syarat minimal:

1. `decode(encode(pesan)) == pesan` untuk seluruh pesan sah (deterministik);
2. distribusi pesan dari sampling seed seragam sesuai model.

### 2.3 Adaptive Decoy

*Adaptive decoy* adalah istilah yang dipakai pada prototipe ini untuk
pembentukan data umpan yang mengikuti distribusi data pelanggan, berbeda dari
*random decoy* yang hanya menjaga rentang nilai. Model *Gaussian per kategori*
dipilih karena saldo antar kategori berbeda jauh (Basic sekitar 3,4 juta
rupiah; VIP sekitar 42,7 juta rupiah), sehingga penyamaan distribusi marginal
saldo saja sudah tidak cukup. Struktur kategori-saldo juga harus
dipertahankan.

### 2.4 Referensi

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

> Sesuaikan metadata dan gaya sitasi dengan pedoman kampus sebelum laporan
> diserahkan.

---

## 3. Metode Penelitian

### 3.1 Tahap penelitian

| Tahap | Kegiatan | Keluaran |
| --- | --- | --- |
| 1 | Verifikasi prototipe awal berjalan | Aplikasi web dan test dasar |
| 2 | Data Profiling, Random dan Adaptive Decoy, random seed | Modul `services/` |
| 3 | Evaluasi kuantitatif dua metode | Metrik dan halaman `/evaluation` |
| 4 | Perancangan DTE dan uji sifat dasarnya | Modul `crypto/dte.py` |
| 5 | Integrasi DTE ke skema Honey Encryption dan evaluasi keamanan | Modul `crypto/honey_encryption.py`, `security_evaluation.py`, halaman `/security` |
| 6 | Pengujian otomatis dan penyusunan laporan | 96 test pytest, `verify.py`, dokumen ini |

### 3.2 Metrik evaluasi

| Metrik | Arti | Arah yang diharapkan |
| --- | --- | --- |
| Selisih mean | absolut(mean asli - mean decoy) | kecil |
| Selisih std. deviasi | absolut(sd asli - sd decoy) | kecil |
| Overlap histogram | koefisien tumpang tindih 0 sampai 1 | mendekati 1 |
| Wasserstein distance | jarak transport optimal kedua sebaran | kecil |
| Statistik KS | selisih maksimum antara kedua CDF | kecil, p-value besar |
| Akurasi classifier | kemampuan memisahkan asli dan decoy | mendekati 0,5 |
| Waktu pembentukan | durasi generate decoy dalam milidetik | - |

**Catatan interpretasi:** jarak distribusi yang lebih kecil berarti sebaran
lebih dekat. Ini **tidak** otomatis berarti keamanan kriptografis lebih baik.

### 3.3 Cara pengumpulan data

Data yang dipakai adalah dataset sintetis 150 pelanggan yang dibuat oleh modul
`honeyvault/services/synthetic_dataset.py`. Setiap pelanggan memiliki id,
nama fiktif, kategori, dan saldo. Distribusi saldo tiap kategori sengaja
dibuat berbeda agar model adaptif punya sesuatu untuk bekerja. Semua
eksperimen memakai *seed* yang sama sehingga hasilnya dapat direproduksi oleh
penguji lain.

---

## 4. Perancangan Sistem

### 4.1 Arsitektur

```
+---------------------------------------------------------------+
|  Antarmuka web (Flask)                                        |
|  /  /simulation  /evaluation  /dte  /security                 |
+-------------------------------+-------------------------------+
                                | memanggil
+-------------------------------v-------------------------------+
|  Lapisan logika (services + crypto)                          |
|  services/ : profiling, decoy, evaluation, identity           |
|  crypto/   : dte, honeyvault_space, honey_encryption,        |
|              security_evaluation                              |
+-------------------------------+-------------------------------+
                                | baca/tulis
+-------------------------------v-------------------------------+
|  Penyimpanan: data/customers.json (JSON lokal)               |
+---------------------------------------------------------------+
```

Pola yang dipakai: satu blueprint per halaman untuk rute, satu service per
tanggung jawab untuk logika, dan satu fungsi murni untuk setiap perhitungan
statistik agar mudah diuji terpisah dari antarmuka.

### 4.2 Struktur folder

```text
HoneyVault/
|-- app.py                      # titik masuk, memanggil create_app()
|-- config.py                   # konfigurasi terpusat
|-- simulate.py                 # CLI eksperimen dan laporan tabel
|-- verify.py                   # verifikasi mandiri (32 pemeriksaan)
|-- requirements.txt
|-- README.md
|-- PROJECT_GUIDE.md            # dokumen handoff pengembangan
|-- TESTING.md                  # panduan testing
|-- LAPORAN.md                  # dokumen ini
|-- honeyvault/
|   |-- __init__.py             # create_app() factory
|   |-- storage.py              # baca/tulis data pelanggan JSON
|   |-- routes/                 # blueprint: dashboard, simulation,
|   |                           # evaluation, dte, security
|   |-- services/               # profiling, decoy, evaluation, identity,
|   |                           # synthetic_dataset
|   |-- crypto/                 # dte, honeyvault_space, dte_evaluation,
|   |                           # honey_encryption, security_evaluation
|   `-- templates/              # base dan 5 halaman
|-- static/style.css
|-- data/
|   |-- customers.json          # dataset aktif
|   `-- synthetic_customers.json
`-- tests/                      # 7 berkas, 96 test
```

### 4.3 Model data

Satu entitas pelanggan:

```python
{"id": "C001", "name": "...", "category": "Regular", "balance": 8500000}
```

Kategori yang valid: `Basic`, `Regular`, `Premium`, `VIP`. Batas saldo: 0
sampai 1.000.000.000 rupiah.

### 4.4 Ruang pesan (message space)

Ruang pesan HoneyVault bukan saldo mentah, melainkan **profil** pelanggan:

```
(kategori, tingkat_saldo)
contoh: ("Premium", "20-35 jt")
```

Tingkat saldo yang dipakai:

| Tingkat | Rentang (Rp) |
| --- | --- |
| 0-5 jt | 0 sampai 5.000.000 |
| 5-10 jt | 5.000.000 sampai 10.000.000 |
| 10-20 jt | 10.000.000 sampai 20.000.000 |
| 20-35 jt | 20.000.000 sampai 35.000.000 |
| 35-50 jt | 35.000.000 sampai 50.000.000 |
| 50-70 jt | 50.000.000 sampai 70.000.000 |
| 70 jt+ | 70.000.000 ke atas |

**Alasan memilih profil, bukan saldo mentah:**

1. Ruang pesan menjadi kecil dan jelas batasnya. Pada dataset 150 pelanggan
   hanya **10 pesan** yang terisi, sesuai anjuran memulai dari ruang pesan
   sederhana.
2. Probabilitas tiap pesan bisa dihitung langsung dari frekuensi observasi,
   sehingga model distribusi benar-benar berasal dari data.
3. Dua pelanggan dengan saldo berbeda tetapi profil serupa menghasilkan pesan
   yang sama, sehingga pesan tidak membocorkan nilai spesifik.

Dari tiap pesan, nilai saldo di dalam rentangnya dibangkitkan ulang mengikuti
distribusi observasi pada sel tersebut. Jadi decoder punya dua lapis: pesan
profil dulu, lalu saldo di dalam sel.

### 4.5 Algoritma DTE

Konstruksi yang dipakai adalah **inverse transform (alias method)**:

```
1. Hitung bobot w_i = jumlah observasi pesan i pada dataset.
2. Urutkan pesan menurut bobot menurun, pinggiran dipecah deterministik.
3. Hitung lebar interval dengan aritmetika bulat:
       width_i = max(1, floor(w_i * 2^64 / jumlah w))
   Selisih pembulatan dialokasikan ke interval terlebar agar total tepat 2^64.
4. Batas kumulatif membentuk interval [awal_i, akhir_i).
5. encode(pesan) -> seed acak seragam pada interval pesan tersebut.
   decode(seed)  -> pesan yang intervalnya memuat seed, pencarian biner.
```

Menggunakan aritmetika bulat, bukan floating point, menghilangkan galat
pembulatan pada batas interval sehingga tidak ada seed yang jatuh di celah.

### 4.6 Algoritma skema Honey Encryption

```
enkripsi(row):
    seed <- DTE.encode((kategori, tingkat_saldo(row)))
    mask <- HMAC-SHA256(kunci, nonce)[0:8] mod 2^64
    c    <- seed XOR mask
    return (c, nonce)

dekripsi(c, nonce):
    mask <- HMAC-SHA256(kunci, nonce)[0:8] mod 2^64
    seed <- c XOR mask
    pesan <- DTE.decode(seed)
    saldo <- ambil observasi acak dari sel pesan
    return (pesan, saldo)
```

Konsekuensi kuncinya:

- **Kunci benar** menghasilkan `mask` yang sama, sehingga `seed` pulih persis
  dan pesan asli kembali.
- **Kunci salah** menghasilkan `mask` yang berbeda, sehingga `seed` berubah
  secara acak dan DTE memetakannya ke pesan sah lain. Tidak ada error dan
  tidak ada data kacau.

Catatan penting: nonce harus **unik per kunci**. Bila nonce dipakai ulang,
maka

```
c1 XOR c2 = (s1 XOR mask) XOR (s2 XOR mask) = s1 XOR s2
```

yaitu penyerang memperoleh XOR dua seed tanpa mengetahui kunci. Mekanisme
kebocoran ini diuji secara eksplisit pada bab 9.

### 4.7 Algoritma adaptive decoy

```
1. Statistik per kategori (mean, sd) dihitung dari data asli.
2. Kategori decoy dipilih dengan peluang = frekuensi kategori pada dataset.
3. Saldo decoy diambil dari Gaussian(mean_kategori, sd_kategori).
   - Bila kategori hanya punya satu observasi, nilai observasi itu dipakai.
   - Bila kategori tidak ada, model global dipakai sebagai cadangan.
4. Semua nilai dibatasi pada rentang saldo data asli.
5. ID decoy = "DEC-001", nama diambil dari kumpulan fiktif terpisah, dicek
   agar tidak pernah sama dengan nama pelanggan mana pun.
```

Karena kategori dipilih sesuai frekuensi dan saldo mengikuti model kategori,
korelasi kategori-saldo ikut terjaga, bukan hanya distribusi marginal saldo.

---

## 5. Cara Kerja Program

### 5.1 Alur umum saat aplikasi dijalankan

```
app.py
  `-- create_app()  (honeyvault/__init__.py)
       |-- baca config.py (kunci sesi, debug, host, port)
       |-- register_blueprints(app)
       |    |-- dashboard    -> "/"
       |    |-- simulation  -> "/simulation"
       |    |-- evaluation  -> "/evaluation"
       |    |-- dte         -> "/dte"
       |    `-- security    -> "/security"
       `-- app.run(host, port)
```

Setiap request ditangani blueprint terkait: membaca data JSON, memanggil
service, lalu merender template Jinja2.

### 5.2 Alur tiap halaman

**`/` Dashboard**

1. `storage.load_customers()` membaca `data/customers.json`.
2. `profile(rows)` menghitung count, mean, median, standar deviasi, min, max,
   kuartil, dan rincian per kategori.
3. Template menampilkan kartu statistik, tabel pelanggan, dan profil kategori.
4. Aksi POST: `/customers/add` (validasi nama, kategori, dan saldo),
   `/customers/reset` (8 pelanggan contoh), `/customers/load-synthetic`
   (150 pelanggan).

**`/simulation` Simulasi Metode**

1. POST dengan `method` (random atau adaptive), `count`, dan `seed`.
2. `generate_decoy()` membangun data umpan sesuai metode.
3. `compare_methods()` menghitung tujuh metrik perbandingan.
4. Tabel menampilkan data umpan beserta metriknya.

**`/evaluation` Evaluasi Kuantitatif**

1. POST dengan `count` dan `seed`.
2. Kedua metode dijalankan, lalu metriknya dihitung.
3. Tabel menunjukkan metode mana yang lebih dekat ke data asli.

**`/dte` DTE**

1. `build_message_space(rows)` menyusun ruang pesan dan bobotnya dari data.
2. Tabel menampilkan tiap pesan: jumlah observasi, probabilitas, dan rentang
   seed.
3. Skenario **kunci benar**: pesan pelanggan di-encode lalu di-decode, dan
   ditampilkan hasil `decode(encode(pesan)) == pesan`.
4. Skenario **kunci salah**: seed acak di-decode, dan hasilnya tetap pesan
   sah.
5. Metrik kemiripan DTE terhadap data asli ditampilkan.

**`/security` Keamanan (halaman utama Tahap 5)**

1. `build_scheme(rows)` membangun ruang pesan dan skema enkripsi.
2. Satu pelanggan dienkripsi, lalu `ciphertext` dan `nonce` ditampilkan.
3. **Dekripsi kunci benar** menampilkan pesan asli, diberi penanda hijau bila
   cocok.
4. **Dekripsi kunci salah** menampilkan pesan berbeda, disertai penjelasan
   bahwa pesannya tetap masuk akal.
5. Empat tabel pengukuran keamanan ditampilkan: kerahasiaan pesan,
   plausibilitas umpan, ketidakdapatbedikan, dan brute force atas kunci.

### 5.3 Alur CLI (`simulate.py`)

```
simulate.py
  |-- muat dataset (aktif, atau --synthetic)
  |-- cetak ringkasan dataset dan per kategori
  |-- jalankan Random Decoy dan Adaptive Decoy (dengan seed)
  |-- hitung metrik perbandingan
  |-- opsional: --dte       -> laporan kualitas DTE
  |-- opsional: --honey     -> laporan pengukuran keamanan skema
  `-- opsional: --show-decoy -> contoh baris data umpan
```

### 5.4 Alur enkripsi dan dekripsi secara rinci

```
Pelanggan: C017 | Premium | Rp 14.200.000
   |
   | (1) tentukan tingkat saldo
   v
Pesan DTE: ("Premium", "10-20 jt")
   |
   | (2) encode -> seed pada interval pesan itu
   v
Seed: 7.412.885.204.119.663.298 (bilangan pada ruang 0 .. 2^64-1)
   |
   | (3) mask = HMAC-SHA256(kunci, nonce)
   v
Ciphertext: seed XOR mask
   |
   | (4) dekripsi: mask dihitung ulang, seed dipulihkan, DTE.decode
   v
Pesan: ("Premium", "10-20 jt")  -> saldo diambil dari observasi sel
```

Dengan kunci salah, langkah (3) menghasilkan `mask` berbeda sehingga langkah
(4) menghasilkan pesan lain yang tetap sah, misalnya
`("Regular", "5-10 jt")`, dan tidak ada error yang muncul di antarmuka.

### 5.5 Kode inti yang perlu dipahami saat presentasi

| Berkas | Isi | Peran |
| --- | --- | --- |
| `crypto/dte.py` | `DTESpace`, `encode`, `decode`, `interval` | Inti message space |
| `crypto/honeyvault_space.py` | `BALANCE_TIERS`, `balance_tier`, `build_message_space`, `encode_profile`, `decode_profile` | Menghubungkan data pelanggan dengan DTE |
| `crypto/honey_encryption.py` | `HoneyEncryption.encrypt`, `HoneyEncryption.decrypt`, `build_scheme`, `wrong_key` | Inti skema enkripsi |
| `crypto/security_evaluation.py` | lima fungsi evaluasi keamanan | Mengukur, bukan sekadar mengklaim |
| `services/decoy.py` | `generate_decoy`, `_sample_adaptive_amount` | Pembentukan data umpan |
| `services/evaluation.py` | metrik jarak, histogram, KS, classifier | Alat ukur |
| `services/identity.py` | `generate_decoy_identity` | Nama dan ID decoy sintetis |

---

## 6. Cara Penggunaan

### 6.1 Persiapan (Windows, VS Code)

Tidak perlu Laragon, XAMPP, MySQL, atau Apache. Proyek memakai Python dan
Flask dengan penyimpanan JSON lokal.

```powershell
# 1. Buat virtual environment
py -m venv .venv

# 2. Aktifkan
.\.venv\Scripts\Activate.ps1        # PowerShell
# .venv\Scripts\activate.bat         # Command Prompt, bila PowerShell memblokir

# 3. Instal dependensi
python -m pip install -r requirements.txt
```

### 6.2 Menjalankan aplikasi

```bash
python app.py          # atau: py app.py
```

Buka `http://127.0.0.1:5000`. Hentikan server dengan `Ctrl + C`.

### 6.3 Konfigurasi opsional

| Variabel | Default | Fungsi |
| --- | --- | --- |
| `HONEYVAULT_SECRET_KEY` | acak per proses | Kunci cookie sesi, agar sesi bertahan antar restart |
| `HONEYVAULT_DEBUG` | `0` | Isi `1` untuk auto-reload dan debugger |
| `HONEYVAULT_HOST` | `127.0.0.1` | Alamat server |
| `HONEYVAULT_PORT` | `5000` | Port server |

```powershell
$env:HONEYVAULT_DEBUG = "1"
$env:HONEYVAULT_PORT = "5050"
python app.py
```

### 6.4 Menjalankan eksperimen dari terminal

```bash
python simulate.py --synthetic --count 200 --seed 42
python simulate.py --synthetic --count 200 --seed 42 --dte --honey
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

### 6.5 Memverifikasi proyek

```bash
python verify.py            # 32 pemeriksaan, keluar dengan kode 0 atau 1
python -m pytest tests/ -v  # 96 test otomatis
```

### 6.6 Membuat dataset sintetis besar

```bash
python -m honeyvault.services.synthetic_dataset
```

Atau tombol "Muat dataset sintetis besar" pada dashboard.

### 6.7 Alur pemakaian harian (ringkas)

1. `python app.py`, lalu buka `http://127.0.0.1:5000`.
2. Dashboard, klik "Muat dataset sintetis besar" (150 pelanggan).
3. `/simulation`: Adaptive Decoy, jumlah 20, seed 42, klik Generate.
4. `/evaluation`: jumlah 200, seed 42, jalankan perbandingan.
5. `/dte`: jalankan dua skenario, kunci benar dan kunci salah.
6. `/security`: pilih pelanggan, klik "Enkripsi lalu dekripsi dua kali".
7. Terminal: `python simulate.py --synthetic --count 200 --seed 42 --dte --honey`,
   lalu salin tabelnya ke lampiran laporan.

### 6.8 Cara menjalankan pengujian secara terarah

```bash
python -m pytest tests/ -v                     # semua test
python -m pytest tests/test_honey_encryption.py -v   # hanya test skema enkripsi
python -m pytest -k "wrong_key" -v              # hanya skenario kunci salah
python -m pytest --tb=short                     # ringkas saat gagal
```

### 6.9 Pemecahan masalah

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| `ModuleNotFoundError: flask` | venv tidak aktif | `.\.venv\Scripts\Activate.ps1` lalu install ulang |
| `Address already in use` | Server masih jalan | `Ctrl+C` di terminal, atau ganti port |
| Halaman 500 | Bug di kode | Lihat traceback di terminal |
| `PermissionError` saat aktivasi venv | PowerShell memblokir | Pakai `activate.bat` di Command Prompt |
| Angka tidak sinkron antar halaman | Cache browser | `Ctrl+F5` untuk hard refresh |
| Dataset 150 tidak muncul | Dataset belum dibuat | `python -m honeyvault.services.synthetic_dataset` |

---

## 7. Hasil dan Pembahasan

> Seluruh tabel di bawah dihasilkan oleh perintah
> `python simulate.py --synthetic --count 200 --seed 42 --dte --honey`
> pada dataset 150 pelanggan sintetis. Perintah dan seed yang sama
> menghasilkan angka yang sama persis, sehingga tabel dapat diverifikasi
> ulang. Kunci, nonce, dan seed DTE pada pengukuran keamanan diturunkan
> dari seed eksperimen agar hasilnya deterministik; pada pemakaian nyata
> kunci tetap harus diacak dan disimpan dengan aman.

### 7.1 Karakteristik dataset

| Statistik | Nilai |
| --- | --- |
| Jumlah pelanggan | 150 |
| Mean saldo | Rp 11.981.493 |
| Median saldo | Rp 8.767.500 |
| Std. deviasi | Rp 11.513.149 |
| Minimum sampai maksimum | Rp 1.310.000 sampai Rp 68.590.000 |
| Kuartil 1 sampai 3 | Rp 5.199.250 sampai Rp 11.896.000 |

| Kategori | Jumlah | Mean | Std. deviasi |
| --- | ---: | ---: | ---: |
| Basic | 38 | Rp 3.378.605 | Rp 1.119.239 |
| Regular | 61 | Rp 8.766.393 | Rp 1.474.638 |
| Premium | 36 | Rp 13.725.139 | Rp 4.072.089 |
| VIP | 15 | Rp 42.665.467 | Rp 9.703.410 |

**Pembahasan:** sebaran saldo tidak simetris. Mean (11,98 juta) jauh di atas
median (8,77 juta), artinya ada kemiringan ke kanan yang berasal dari 15
pelanggan VIP. Model Gaussian tunggal tidak akan menangkap hal ini; itulah
alasan model dibangun **per kategori**.

### 7.2 Perbandingan Random Decoy dan Adaptive Decoy (n = 200)

| Metrik | Random Decoy | Adaptive Decoy | Lebih dekat ke asli |
| --- | ---: | ---: | --- |
| Selisih mean saldo | 23.570.952 | 1.503.073 | Adaptive |
| Selisih std. deviasi | 7.638.486 | 628.884 | Adaptive |
| Overlap histogram (1 = identik) | 0,378 | 0,850 | Adaptive |
| Wasserstein distance | 23.571.998 | 1.708.387 | Adaptive |
| Statistik KS | 0,6350 | 0,1483 | Adaptive |
| Akurasi classifier | 0,833 | 0,489 | Adaptive |
| Waktu pembentukan | 0,963 ms | 1,563 ms | Random (selisih di bawah 1 ms) |

Ringkasan statistik tiap kelompok data:

| Kelompok | Mean | Std. deviasi | Minimum | Maksimum |
| --- | ---: | ---: | ---: | ---: |
| Data asli | Rp 11.981.493 | Rp 11.513.149 | Rp 1.310.000 | Rp 68.590.000 |
| Random Decoy | Rp 35.552.445 | Rp 19.151.635 | Rp 1.707.000 | Rp 68.561.000 |
| Adaptive Decoy | Rp 10.478.420 | Rp 10.884.264 | Rp 1.310.000 | Rp 64.559.000 |

**Pembahasan:**

1. **Mean dan standar deviasi.** Random decoy menghasilkan mean Rp 35,55 juta,
   lebih dari tiga kali mean data asli, karena pengambilan acak seragam pada
   rentang Rp 1,31 juta sampai Rp 68,59 juta selalu mengarah ke tengah
   rentang. Adaptive decoy menghasilkan mean Rp 10,48 juta, hanya berbeda
   Rp 1,50 juta atau 12,5 persen dari data asli.
2. **Overlap histogram** naik dari 0,378 menjadi 0,850. Histogram data asli dan
   adaptive decoy tumpang tindih 85 persen pada bin yang sama, sehingga secara
   visual keduanya hampir tidak bisa dibedakan.
3. **Wasserstein distance** turun drastis, dari Rp 23,57 juta menjadi
   Rp 1,71 juta. Ini besaran yang paling drastik: jarak transport massa data
   turun sekitar 13 kali lipat.
4. **Akurasi classifier** 0,489 pada adaptive decoy, sedikit di bawah 0,5,
   artinya classifier tidak lebih baik daripada tebakan acak dalam
   membedakan data asli dari adaptive decoy. Pada random decoy, classifier
   berhasil 83,3 persen, yang menandakan data umpannya sangat mudah
   dibedakan.
5. **Waktu pembentukan** adaptive hanya sekitar 0,6 ms lebih lambat untuk
   200 baris. Beban tambahan berasal dari perhitungan statistik per
   kategori, yang nilainya kecil dibanding manfaat kemiripan yang jauh lebih
   besar. Hal ini penting: pada skenario nyata, waktu pemrosesan data
   pelanggan jauh lebih besar dibanding waktu pemrosesan satu field. Catatan:
   angka waktu bergantung pada perangkat keras sehingga dapat berbeda tipis
   antar mesin, sedangkan metrik lain deterministik untuk seed yang sama.

### 7.3 Kualitas DTE terhadap data asli

| Metrik | Nilai |
| --- | ---: |
| Jumlah pesan dalam ruang pesan | 10 |
| Konsistensi decode | 50 seed diuji, 0 ketidakkonsistenan |
| Wasserstein distance | 673.133 |
| Overlap histogram | 0,893 |
| Statistik KS | 0,0500 (p = 0,9610) |
| Akurasi classifier | 0,478 |
| Selisih frekuensi maksimum | 0,0500 |

Frekuensi tiap pesan, data asli dibandingkan hasil sampling DTE:

| Pesan | Asli | DTE | Frekuensi asli | Frekuensi DTE |
| --- | ---: | ---: | ---: | ---: |
| Regular / 5-10 jt | 49 | 85 | 0,327 | 0,283 |
| Basic / 0-5 jt | 35 | 85 | 0,233 | 0,283 |
| Premium / 10-20 jt | 24 | 53 | 0,160 | 0,177 |
| Regular / 10-20 jt | 12 | 15 | 0,080 | 0,050 |
| VIP / 35-50 jt | 9 | 24 | 0,060 | 0,080 |
| Premium / 5-10 jt | 8 | 18 | 0,053 | 0,060 |
| Premium / 20-35 jt | 4 | 7 | 0,027 | 0,023 |
| VIP / 20-35 jt | 4 | 7 | 0,027 | 0,023 |
| Basic / 5-10 jt | 3 | 4 | 0,020 | 0,013 |
| VIP / 50-70 jt | 2 | 2 | 0,013 | 0,007 |

**Pembahasan:** p-value KS sebesar 0,9610 sangat besar, artinya tidak ada
bukti perbedaan distribusi antara data asli dan data hasil DTE. Selisih
frekuensi maksimum 0,05 berasal dari pembulatan interval: lebar interval
dibatasi kelipatan bulat pada ruang seed 2^64, sehingga pesan dengan bobot
kecil seperti VIP / 50-70 jt hanya mendapat 1,3 persen ruang seed.

### 7.4 Pengukuran keamanan skema Honey Encryption

| Aspek | Pengukuran | Nilai |
| --- | --- | --- |
| Kerahasiaan pesan | Pemulihan dengan kunci benar | 100 persen (100 dari 100) |
| Kerahasiaan pesan | Kebocoran ciphertext antar kategori | tidak terdeteksi |
| Kerahasiaan pesan | Ciphertext dibandingkan seed seragam acak | p = 0,0996 |
| Kerahasiaan pesan | Rasio ciphertext unik | 1,000 |
| Plausibilitas umpan | Kategori pesan umpan valid | 100 persen |
| Plausibilitas umpan | Pesan umpan di dalam ruang pesan DTE | 100 persen |
| Plausibilitas umpan | Semua tebakan kunci terlihat masuk akal | ya |
| Tidak dapat dibedakan | Wasserstein distance | 535.903 |
| Tidak dapat dibedakan | Overlap histogram | 0,953 |
| Tidak dapat dibedakan | Statistik KS | 0,0367 (p = 0,9991) |
| Tidak dapat dibedakan | Akurasi classifier | 0,478 |
| Brute force | Ruang kunci | 2^128 |
| Brute force | Ruang pesan | 10 pesan |
| Brute force | Peluang acak pesan benar per percobaan | 10,0 persen |

**Pembahasan:**

1. **Pemulihan kunci benar 100 persen.** Setiap pesan asli pulih persis, baik
   profilnya maupun nilai saldo di dalam selnya. Ini memang diharapkan,
   karena `seed XOR mask` bersifat involutif dan DTE bersifat deterministik.
2. **Tidak ada kebocoran ciphertext.** Uji Kolmogorov-Smirnov antar kategori
   pesan tidak menemukan perbedaan yang signifikan (p = 0,0996 untuk
   perbandingan dengan seed seragam acak). Rasio ciphertext unik 1,000
   menunjukkan tidak ada pengulangan yang bisa dipakai sebagai penanda.
3. **Pesan umpan selalu sah.** 100 persen pesan hasil dekripsi kunci salah
   berada di dalam ruang pesan DTE, dan kategorinya selalu ada pada dataset.
   Inilah sifat inti Honey Encryption: tidak ada "pesan rusak" yang bisa dipakai
   penyerang sebagai penanda tebakan salah.
4. **Tidak dapat dibedakan dari data asli.** Akurasi classifier 0,478 dengan
   p-value KS 0,9991 menunjukkan pesan umpan secara statistik hampir identik
   dengan data asli. Bandingkan dengan random decoy yang berhasil dibedakan
   83,3 persen.
5. **Peluang acak pesan benar bukan nol.** Ruang pesan hanya 10 pesan, jadi
   peluang tebakan acak mendarat pada pesan yang benar adalah 10 persen per
   percobaan. Ini justru **sifat yang diinginkan**: penyerang tidak dapat
   memakai "pesan benar" sebagai penanda tebakan yang benar, dan tidak dapat
   memakai "pesan kacau" sebagai penanda tebakan yang salah. Yang dilindungi
   adalah kerahasiaan, bukan probabilitas pesan benar per percobaan.
6. **Biaya brute force.** Dengan ruang kunci 2^128, penyerang harus mencoba
   sekitar 2^128 kunci sebelum memastikan pesan aslinya, dan setiap percobaan
   menghasilkan pesan yang sama sekali tidak mencurigakan.

### 7.5 Perbandingan ringkas seluruh tahap

| Aspek | Random Decoy | Adaptive Decoy | Adaptive Decoy + DTE (skema) |
| --- | ---: | ---: | ---: |
| Selisih mean saldo | 23.570.952 | 1.503.073 | - |
| Wasserstein distance | 23.571.998 | 1.708.387 | 535.903 |
| Overlap histogram | 0,378 | 0,850 | 0,953 |
| Akurasi classifier | 0,833 | 0,489 | 0,478 |
| Sumber umpan | pengundian acak | model Gaussian per kategori | DTE di atas model Gaussian |

---

## 8. Pengujian

### 8.1 Pengujian otomatis

Pengujian ditulis dengan pytest dan berada pada folder `tests/`. Tujuh berkas
menutupi seluruh lapisan.

| Berkas | Jumlah test | Cakupan |
| --- | ---: | --- |
| `tests/test_profiling.py` | 7 | Statistik, kuartil, per kategori, data kosong |
| `tests/test_decoy.py` | 13 | Identitas, batas, seed, kategori, pembulatan |
| `tests/test_evaluation.py` | 10 | Metrik jarak, histogram, classifier, perbandingan |
| `tests/test_crypto.py` | 22 | DTE: round-trip, distribusi, seed tak sah, interval |
| `tests/test_dte_evaluation.py` | 10 | Kualitas data DTE, konsistensi, kesamaan dengan asli |
| `tests/test_honey_encryption.py` | 19 | Kunci benar, kunci salah, kebocoran, nonce, validasi kunci |
| `tests/test_app.py` | 15 | Rute Flask, validasi input, alur pengguna |
| **Total** | **96** | |

Contoh sifat yang diuji pada skema enkripsi:

| Pengujian | Skenario | Hasil yang diharapkan |
| --- | --- | --- |
| Enkripsi kunci benar | Dekripsi dengan kunci yang sama | Pesan asli kembali persis |
| Enkripsi kunci salah | Dekripsi dengan kunci berbeda | Pesan sah, kategori valid, saldo positif |
| Kebocoran | Uji KS ciphertext antar kategori pesan | Tidak ada pasangan dengan p-value di bawah 0,01 |
| Nonce berbeda | Dua enkripsi pada pesan sama | Ciphertext berbeda, pesan hasil dekripsi sama |
| Nonce dipakai ulang | Ciphertext di-XOR | Terbukti sama dengan XOR dua seed |
| Validasi kunci | Kunci pendek atau bukan byte | Ditolak dengan exception |
| DTE round-trip | Encode lalu decode | Pesan kembali sama |
| DTE seed tak sah | Decode seed di luar rentang | Ditolak dengan error |
| DTE distribusi | Sampling seed acak | Frekuensi sesuai model |

### 8.2 Verifikasi mandiri

`verify.py` menjalankan 32 pemeriksaan yang mencakup lingkungan, logika inti,
DTE, skema Honey Encryption, aplikasi web, pengujian otomatis, dan keamanan.
Pemeriksaan yang berkaitan dengan Tahap 5:

| Pemeriksaan | kriteria lulus |
| --- | --- |
| Kunci benar memulihkan pesan asli | Tingkat keberhasilan 100 persen |
| Kunci salah menghasilkan pesan yang masuk akal | 100 persen kategori valid dan berada di ruang pesan DTE |
| Ciphertext tidak membocorkan pesan | Tidak ada pasangan kategori dengan p-value di bawah 0,01 |
| Pesan umpan tidak dapat dibedakan dari pesan asli | Akurasi classifier di bawah 0,7 |
| Skema mensyaratkan nonce unik per kunci | Mask saling menghilangkan terdeteksi |
| Brute force kunci tidak menghasilkan pesan kacau | Semua tebakan terlihat masuk akal |

Hasil lengkap:

```text
SEMUA PEMERIKSAAN BERHASIL (32/32)
```

### 8.3 Pengujian manual di browser

Checklist yang dipakai pada pengujian manual:

1. Dashboard menampilkan statistik, tabel pelanggan, dan profil per kategori.
2. Penambahan pelanggan dengan saldo nonnumerik atau negatif ditolak.
3. Tombol muat dataset 150 dan reset dataset contoh bekerja.
4. Simulasi menghasilkan data umpan dengan ID `DEC-001` dan nama yang berbeda
   dari pelanggan asli.
5. Seed yang sama menghasilkan hasil yang sama antar percobaan.
6. Evaluasi menunjukkan Adaptive Decoy lebih dekat ke data asli.
7. DTE menampilkan model distribusi, skenario kunci benar, dan skenario kunci
   salah.
8. Halaman Keamanan menampilkan demo kunci benar dan kunci salah, serta tabel
   pengukuran yang terisi.
9. Tidak ada teks error atau nilai `None` pada halaman mana pun.

---

## 9. Analisis Keamanan

### 9.1 Model ancaman

| Aspek | Keterangan |
| --- | --- |
| Penyerang pasif | Mendengar ciphertext, mencoba memperkirakan pesan asli |
| Penyerang aktif | Dapat menguji tebakan kunci dan mengukur "keberhasilan" tiap tebakan |
| Ancaman utama | Serangan brute force atas kunci, dan analisis ciphertext untuk membocorkan pesan |
| Aset yang dilindungi | Pesan profil pelanggan, yaitu pasangan kategori dan tingkat saldo |
| Di luar cakupan | Serangan ke server aplikasi, kebocoran kunci, serangan kanal samping pada implementasi PRF |

### 9.2 Asumsi keamanan

1. PRF diimplementasikan dengan HMAC-SHA256 dan dianggap pseudorandom ideal.
2. Nonce tidak pernah dipakai ulang dengan kunci yang sama.
3. Penyerang dapat menghitung PRF dengan kunci yang benar (mendekripsi
   ciphertext yang sama berulang kali), tetapi tidak dapat menebak kunci.
4. Penyerang yang mencoba kunci acak mendapat pesan yang tampak sah, sehingga
   tidak dapat memakai isi pesan sebagai penanda tebakan salah.

### 9.3 Yang sudah diukur

- **Kerahasiaan pesan:** pemulihan kunci benar 100 persen; tidak ada
  kebocoran ciphertext terhadap pesan.
- **Plausibilitas umpan:** 100 persen pesan umpan berada di ruang pesan sah.
- **Ketidakdapatbedakan:** akurasi classifier pembeda 0,478, KS p-value 0,9991.
- **Efektivitas brute force:** seluruh tebakan kunci menghasilkan pesan yang
  masuk akal, dan ruang kunci 2^128.

### 9.4 Batas skema dan kebocoran nonce

Pengujian dengan nonce yang dipakai ulang menunjukkan identitas

```
c1 XOR c2 = s1 XOR s2
```

yaitu dua mask saling menghilangkan sehingga penyerang memperoleh XOR dua
seed tanpa mengetahui kunci. Pada dataset 150 pelanggan, rasio pasangan pesan
yang konsisten dengan XOR teramati adalah 0,000978, sedangkan kontrol acak
memberi 0,001067. Penyempitan yang diperoleh memang kecil pada ruang pesan
sekecil ini, tetapi mekanismenya nyata, sehingga nonce wajib unik per kunci.
Kode memakai nonce acak 128 bit, yang membuat pengulangan sangat tidak
mungkin terjadi.

### 9.5 Batasan yang harus dinyatakan di laporan

Yang **boleh** diklaim:

- Skema Honey Encryption dengan DTE sebagai message space sudah diimplementasikan
  dan diuji: kunci benar memulihkan pesan asli, kunci salah menghasilkan pesan
  umpan melalui DTE.
- Pengukuran empiris mendukung pernyataan bahwa pesan umpan sulit dibedakan
  dari pesan asli.

Yang **tidak boleh** diklaim:

- "Aman dari brute force" tanpa menyertakan pengukurannya. Yang benar adalah:
  ruang kunci 2^128 dan setiap tebakan menghasilkan pesan yang tampak sah.
- Bukti keamanan formal. Bukti formal memerlukan analisis *reductions*
  terhadap model keamanan yang dinyatakan, yang belum dilakukan.
- Keamanan autentikasi. Ciphertext tidak dilindungi MAC, sehingga penyerang
  aktif dapat mengubah seed yang pulih. Hasilnya tetap pesan yang sah, bukan
  data kacau, dan justru inilah sifat Honey Encryption.
- Keamanan kanal samping. Tidak diuji.
- Kesiapan produksi.

---

## 10. Kesimpulan

1. Adaptive decoy yang mengikuti model Gaussian per kategori menghasilkan data
   umpan yang jauh lebih dekat ke data asli dibandingkan baseline acak:
   Wasserstein distance turun dari Rp 23,57 juta menjadi Rp 1,71 juta, overlap
   histogram naik dari 0,378 menjadi 0,850, dan akurasi classifier pembeda
   turun dari 0,833 menjadi 0,489. Beban waktu tambahan hanya sekitar 0,6 ms
   untuk 200 baris.
2. DTE berhasil memenuhi dua syarat dasarnya: round-trip berlaku untuk seluruh
   pesan sah, dan distribusi seed seragam menghasilkan pesan sesuai model
   probabilitas yang berasal dari frekuensi observasi data pelanggan
   (KS p-value 0,9610, akurasi classifier 0,478).
3. Skema Honey Encryption di atas DTE berperilaku sesuai harapan: kunci benar
   memulihkan 100 persen pesan asli, kunci salah menghasilkan pesan umpan
   yang 100 persen berada di ruang pesan sah dengan akurasi classifier pembeda
   0,478. Tidak ada kebocoran ciphertext terhadap pesan.
4. Pengujian otomatis (96 test) dan verifikasi mandiri (32 pemeriksaan)
   memastikan seluruh sifat tersebut dapat direproduksi.
5. Analisis keamanan menunjukkan skema yang dipakai konsisten dengan
   literatur, namun analisis formal, autentikasi, dan uji kanal samping
   masih belum dikerjakan.

---

## 11. Saran Pengembangan

1. **Perbesar ruang pesan.** Ruang pesan saat ini 10 profil. Menambah
   tingkat saldo atau menyisipkan atribut tambahan (misalnya kota) membuat
   distribusi umpan lebih kaya dan menurunkan peluang
   tebakan acak yang kebetulan benar.
2. **Model saldo dalam sel.** Saat ini saldo di dalam sel diambil dari
   observasi yang ada. Model kontinu (misalnya kernel density) memberi
   sebaran nilai yang lebih halus.
3. **Penanganan skewness.** Model Gaussian tidak menangkap kemiringan ke kanan
   data; campuran Gaussian atau transformasi quantile dapat mengatasinya.
4. **Skema akar kunci.** Kunci saat ini dibuat acak. Turunan kunci dari
   frasa sandi melalui fungsi *key derivation* akan lebih realistis.
5. **Uji kanal samping dan analisis formal.** Menyusun argumen *reduction*
   terhadap model keamanan yang dinyatakan akan menaikkan nilai akademik
   proyek.
6. **Antarmuka envelope.** Menambahkan envelope yang memuat nonce, versi
   format, dan metadata tanpa membocorkan pesan.

---

## 12. Referensi

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
4. Dokumentasi Python, modul `hmac`, `hashlib`, `secrets`.
5. Dokumentasi Flask, bagian *Blueprints* dan *Application Factories*.
6. Dokumentasi SciPy, modul `scipy.stats` untuk uji Kolmogorov-Smirnov dan
   jarak Wasserstein.

---

## Lampiran A. Daftar Berkas Penting

| Berkas | Fungsi |
| --- | --- |
| `app.py` | Titik masuk aplikasi |
| `config.py` | Konfigurasi terpusat |
| `simulate.py` | CLI eksperimen |
| `verify.py` | Verifikasi mandiri 32 pemeriksaan |
| `honeyvault/__init__.py` | Factory `create_app()` |
| `honeyvault/storage.py` | Baca/tulis JSON |
| `honeyvault/routes/*.py` | Lima blueprint halaman |
| `honeyvault/services/profiling.py` | Data Profiling |
| `honeyvault/services/decoy.py` | Random dan Adaptive Decoy |
| `honeyvault/services/evaluation.py` | Metrik kuantitatif |
| `honeyvault/services/identity.py` | Identitas decoy sintetis |
| `honeyvault/crypto/dte.py` | DTE |
| `honeyvault/crypto/honeyvault_space.py` | Ruang pesan HoneyVault |
| `honeyvault/crypto/dte_evaluation.py` | Evaluasi kualitas DTE |
| `honeyvault/crypto/honey_encryption.py` | Skema Honey Encryption |
| `honeyvault/crypto/security_evaluation.py` | Pengukuran keamanan skema |
| `honeyvault/templates/*.html` | Tampilan lima halaman |
| `tests/*.py` | 96 pengujian otomatis |

## Lampiran B. Cheat Sheet Perintah

```bash
# Instalasi
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Menjalankan aplikasi
python app.py

# Pengujian dan verifikasi
python -m pytest tests/ -v
python verify.py

# Eksperimen
python simulate.py --synthetic --count 200 --seed 42
python simulate.py --synthetic --count 200 --seed 42 --dte --honey
python simulate.py --synthetic --count 200 --seed 42 --show-decoy

# Dataset
python -m honeyvault.services.synthetic_dataset
```

## Lampiran C. Checklist Sebelum Presentasi

- [ ] Data pribadi pada halaman identitas sudah diisi.
- [ ] `python verify.py` menghasilkan 32 dari 32 berhasil.
- [ ] `python -m pytest tests/ -v` menghasilkan 96 passed.
- [ ] Tabel hasil sudah disalin dari keluaran `simulate.py`.
- [ ] Screenshot halaman `/security` dan `/dte` sudah disiapkan.
- [ ] Batasan pada subbab 9.5 sudah dibacakan saat presentasi.
- [ ] Sitasi sesuai pedoman kampus.
