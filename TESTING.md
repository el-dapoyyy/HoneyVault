# Panduan Testing HoneyVault

Dokumen ini menjelaskan cara memastikan proyek berjalan benar, dan cara
membuktikan sendiri bahwa program benar-benar bekerja.

## 1. Tiga tingkat pemeriksaan

Tiga tingkat pemeriksaan, dari yang paling cepat ke yang paling menyeluruh:

| Perintah | Waktu | Yang diperiksa |
| --- | --- | --- |
| `python verify.py` | ~2 detik | 20 pemeriksaan menyeluruh, keluar dengan kode 0/1 |
| `python -m pytest tests/ -v` | ~2 detik | 40 test otomatis, perincian tiap test |
| Cek manual di browser | ~2 menit | Tampilan dan interaksi pengguna |

Ketiganya dipakai bersama. Jangan hanya melakukan yang pertama.

## 2. Pemeriksaan otomatis menyeluruh

```bash
python verify.py
```

Keluaran akhir:

```text
====================================================================
RINGKASAN VERIFIKASI HONEYVAULT
====================================================================
BERHASIL  Versi Python memadai
BERHASIL  Dependensi terpasang
...
SEMUA PEMERIKSAAN BERHASIL (20/20)
```

Exit code `0` berarti semua lulus, `1` berarti ada yang gagal. Ini berguna
jika Anda ingin memakainya di CI atau dipresentasikan.

Pemeriksaan yang dilakukan:

**Lingkungan**
- Versi Python minimal 3.8
- flask, numpy, scipy, pytest semuanya terpasang
- Semua 22 berkas penting ada

**Logika inti**
- Data Profiling menghitung mean, median, min, max dengan benar
- Nama pelanggan asli tidak pernah bocor ke data umpan
- Semua decoy berada di dalam rentang data asli
- Seed yang sama menghasilkan output identik
- Mean decoy per kategori dalam 25% dari mean asli
- Adaptive Decoy menang pada jarak Wasserstein

**Aplikasi web**
- 3 halaman merespons HTTP 200
- CSS termuat
- Tambah pelanggan bekerja
- Input tidak valid ditolak (kategori salah, saldo non-numerik, saldo negatif)
- Simulasi menghasilkan baris decoy
- Evaluasi menghasilkan 7 metrik

**Pengujian otomatis**
- Seluruh suite pytest lulus

**Keamanan dan batasan**
- Tidak ada kunci rahasia hardcoded
- Mode debug mati secara default
- Server hanya listen di loopback (127.0.0.1)
- Tidak ada klaim Honey Encryption palsu di kode

## 3. Test otomatis per unit

```bash
python -m pytest tests/ -v          # semua test, verbose
python -m pytest tests/test_decoy.py -v   # satu berkas
python -m pytest -k "reproducible" -v      # satu topik
python -m pytest --tb=short              # ringkas saat gagal
```

Empat berkas test:

| Berkas | Cakupan |
| --- | --- |
| `tests/test_profiling.py` | Statistik, kuartil, per kategori, data kosong |
| `tests/test_decoy.py` | Identitas, batas, seed, kategori, pembulatan |
| `tests/test_evaluation.py` | Metrik jarak, histogram, classifier, perbandingan |
| `tests/test_app.py` | Rute Flask, validasi input, alur pengguna |

## 4. Membuktikan test benar-benar berguna

Test yang selalu lulus tidak berarti apa-apa. Untuk memastikan test Anda
benar-benar menangkap masalah, sengaja buat kesalahan lalu lihat test gagal.

Contoh: buka `honeyvault/services/decoy.py`, cari baris:

```python
name = generate_decoy_identity(rng, taken_names)
```

Ubah menjadi:

```python
name = rng.choice([r["name"] for r in rows])
```

Lalu jalankan:

```bash
python verify.py
```

Yang terjadi:

```text
GAGAL   Identitas decoy tidak membocorkan data asli - Nama pelanggan asli bocor ke decoy
GAGAL   Suite pytest lulus - Suite pytest gagal, kode keluar 1
```

Sekarang kembalikan kodenya. Ini membuktikan test Anda menangkap regresi
sebenarnya, bukan sekadar mencentang kotak.

## 5. Checklist manual di browser

Jalankan `python app.py`, lalu buka `http://127.0.0.1:5000`.

### Dashboard (`/`)

- [ ] Halaman terbuka, tidak ada error di terminal
- [ ] Enam kartu statistik terisi (total, mean, median, SD, min, maks)
- [ ] Tabel pelanggan menampilkan 8 baris
- [ ] Tabel "Profil per kategori" terisi
- [ ] Tambahkan pelanggan: isi nama/kategori/saldo → muncul di tabel, jumlah naik
- [ ] Saldo `abc` → pesan error, pelanggan tidak bertambah
- [ ] Saldo `-5000` → pesan error, pelanggan tidak bertambah
- [ ] Klik "Muat dataset sintetis besar" → 150 pelanggan
- [ ] Klik "Reset dataset contoh" → kembali ke 8 pelanggan

### Simulasi (`/simulation`)

- [ ] Kotak "Profil dataset" terisi
- [ ] Adaptive Decoy → 5 baris decoy muncul
- [ ] ID_FORMAT `DEC-001`.., bukan `C001`
- [ ] Nama decoy **berbeda** dari nama pelanggan di dashboard
- [ ] Saldo decoy berada dalam rentang data asli
- [ ] Ganti ke Random Decoy → hasil berbeda
- [ ] Isi seed `42` → Generate → ulangi → hasil **identik**
- [ ] Kosongkan seed → Generate → ulangi → hasil **berbeda**
- [ ] Jumlah decoy `20` → 20 baris

### Evaluasi (`/evaluation`)

- [ ] Jalankan perbandingan → tabel 7 metrik terisi
- [ ] Kolom "Lebih dekat ke asli" menunjuk **Adaptive** untuk sebagian besar metrik
- [ ] "Akurasi classifier" < 1.0 (bukan sempurna)
- [ ] Waktu pembentukan tampil dalam milidetik
- [ ] Ganti jumlah ke `200` → metrik berubah, masih Adaptive menang

### Tampilan

- [ ] Navigasi atas bisa ke semua 3 halaman
- [ ] Tabel panjang bisa di-scroll (maks 150 baris)
- [ ] Tampilan rapi di lebar 1280px
- [ ] Tampilan rapi di lebar 375px (mobile) — perkecil jendela browser
- [ ] Tidak ada teks error atau `None` di halaman

## 6. Kalau ada yang gagal

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| `ModuleNotFoundError: flask` | venv tidak aktif | `.\.venv\Scripts\Activate.ps1` lalu install ulang |
| `Address already in use` | Server masih jalan | `Ctrl+C` di terminal, atau ganti port via `HONEYVAULT_PORT` |
| Halaman 500 | Bug di kode | Lihat traceback di terminal |
| Pesan "Paket belum terpasang" | Dependensi kurang | `python -m pip install -r requirements.txt` |
| `PermissionError` saat aktivasi venv | PowerShell memblokir | Pakai `activate.bat` di Command Prompt |
| Angka tidak sinkron antar halaman | Browser cache | `Ctrl+F5` untuk hard refresh |
| Dataset 150 tidak muncul | Dataset belum dibuat | `python -m honeyvault.services.synthetic_dataset` |

## 7. Checklist sebelum presentasi

```bash
python verify.py                    # harus: SEMUA PEMERIKSAAN BERHASIL (20/20)
python -m pytest tests/ -v          # harus: 40 passed
python app.py                       # cek manual checklist di atas
python simulate.py --synthetic --count 200 --seed 42   # siapkan angka untuk laporan
```

## 8. Apa yang BELUM boleh diklaim

Verifikasi ini hanya memastikan prototipe berjalan. Yang **belum** ada dan
tidak boleh diklaim sebagai fitur:

- DTE (Distribution-Transforming Encoder)
- Mekanisme enkripsi dan dekripsi Honey Encryption
- Dekripsi dengan kunci salah yang menghasilkan data umpan

Pengujian di atas hanya memeriksa bahwa generator decoy bekerja dan datanya
tidak bocor. Keamanan kriptografi itu adalah Tahap 4 dan 5, belum dikerjakan.
