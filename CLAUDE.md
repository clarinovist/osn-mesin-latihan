# CLAUDE.md — OSN Mesin Latihan

Panduan kerja untuk Claude Code di repo ini. Baca sampai habis sebelum
menyentuh kode: sebagian aturan di sini lahir dari insiden nyata (data anak,
deploy gagal, commit nyasar ke repo hantu).

Bahasa: tulis jawaban, commit message, docstring, dan string UI dalam
**Bahasa Indonesia** — santai tapi akurat. Nama berkas modul bahasa Inggris,
nama fungsi/variabel tetap Indonesia (keputusan eksplisit 31 Agu 2026).

## 1. Apa ini

Aplikasi web untuk orang tua (peran "guru") melatih anak SD mengerjakan soal
gaya OSN/SASMO: generator soal berparameter, diagnosis kesalahan otomatis
(kode B/K/H/E/T/N), lembar cetak, dan laporan per anak.

- **Pure Python stdlib. Tanpa framework, tanpa dependensi pihak ketiga.**
  Satu-satunya dev dependency: `pytest` + `pytest-xdist`. Jangan pernah
  menambah paket (Flask, Jinja, requests, pydantic) — ini keputusan sadar:
  satu pengguna, sedikit query, tiap dependensi = satu hal lagi yang bisa
  gagal saat deploy. Ajukan dulu ke user kalau merasa butuh.
- **Zero-JS by default.** Menu pakai `<details>` CSS-only, navigasi pakai
  `?section=` server-side. Pengecualian yang sudah disetujui: toggle mata
  sandi dan `confirm()` untuk tombol destruktif.
- Live di `https://osn.lesprivate.id` (Caddy → 127.0.0.1:8724).

## 2. Peta repo

| Path | Isi |
|---|---|
| `mesin/` | **Aplikasi.** Semua kode Python + `__tests__/` ada di sini |
| `docs/` | Riset & keputusan. `docs/plan/` **gitignored** (lokal saja) |
| `produk/` | PRD, peta jalan |
| `latihan/`, `kurikulum/`, `riset-pasar/` | Materi & riset, bukan kode |
| `desain-ui/` | Mockup design system (Stitch) |
| `spike/` | Eksperimen lama, ortogonal dari `mesin/` |

## 3. Aturan git yang WAJIB — repo hantu

`mesin/.git` adalah **repo bekas yang basi** (HEAD `96dbc5b`, commit
terakhirnya menghapus semua berkas). Repo yang benar adalah repo LUAR
`/Users/nugroho/Documents/osn` (remote `origin` →
`clarinovist/osn-mesin-latihan`, branch `main`).

- **Setiap perintah git pakai `-C`:**
  `git -C /Users/nugroho/Documents/osn <cmd>`
- Jangan pernah menjalankan git dengan cwd di dalam `mesin/`. Sudah terbukti
  3x menelan commit, `git mv`, dan `git stash` diam-diam — dan `git diff`
  dari sana **berbohong** (pernah menampilkan diff penghapusan 21,5k baris).
- Kalau commit terlanjur masuk repo hantu: `reset --mixed` balik ke
  `96dbc5b`, lalu commit ulang dari repo luar (berkas di disk aman).
- `git checkout -- <file>` menghapus juga WIP yang belum di-commit di file
  itu. Sebelum eksperimen/mutasi, `cp` file ke `/tmp` dan pulihkan dengan
  `cp`, bukan `git checkout`.

## 4. Menjalankan & menguji

```bash
cd /Users/nugroho/Documents/osn/mesin && ./.venv/bin/python -m pytest __tests__/ -q
# lebih cepat:
cd /Users/nugroho/Documents/osn/mesin && ./.venv/bin/python -m pytest __tests__/ -q -n auto
```

- **Pakai venv-nya sendiri** (`mesin/.venv/bin/python`, Python 3.9.6). `python3`
  polos gagal di mesin ini.
- **cwd tiap perintah shell reset ke root repo** — selalu awali
  `cd /Users/nugroho/Documents/osn/mesin && ...` atau pakai path absolut.
- Baseline saat ini: **5334 test, ±85 detik** (±25 detik dengan `-n auto`).
  Kalau ada yang merah sebelum kamu mengubah apa pun, itu bukan regresi kamu —
  cek `git log` file test-nya dulu.
- Server lokal: `cd mesin && ./.venv/bin/python serve.py` (port 8724). Jangan
  pakai ini untuk uji visual berdata — lihat §10.

**Python 3.9, bukan 3.12.** Container pakai 3.12, tapi venv lokal 3.9 —
sintaks yang hanya legal di 3.12 (mis. kutip bersarang di f-string
`f"{"a" if x else "b"}"`) lolos di CI tapi meledak di lokal. Hitung ke
variabel dulu.

## 5. Arsitektur

Alur data: `topics` (paket topik) → `generator` (parameter per level) →
`templates` (Soal + malrule) → `render`/`worksheets` (HTML) →
`database` (simpan) → `diagnosis` (jawaban → kode) → `reports`.

| Modul | Peran |
|---|---|
| `templates.py` | `Soal`, `Malrule`, `saring_malrule`, `LEVEL` (P3–P6) |
| `topics.py` | dataclass `Topik` + registry `PAKET`; `gabungan()` untuk paket ad-hoc |
| `topic_*.py` | Satu paket topik per berkas (pola-bilangan, geometri, kombinatorik, teori-bilangan, aritmatika dasar/lanjut, geometri-ruang, statistika, logika, pengukuran) |
| `generator.py` | `buat_lembar`, `PROFIL_LEVEL`, konstruksi pola |
| `render.py` / `worksheets.py` | Struktur HTML lembar (tanpa CSS) |
| `screen_style.py`, `print_style.py`, `teacher_style.py`, `style_stitch.py` | CSS terpisah dari struktur |
| `design_tokens.py` | **Sumber tunggal nilai visual** — tidak ada hex hardcoded di modul lain |
| `web.py` | Router `Penangan(BaseHTTPRequestHandler)` + palang peran/kepemilikan |
| `teacher_pages.py`, `student_pages.py`, `account_pages.py`, `reports.py`, `landing.py` | Halaman per permukaan |
| `students.py` | Lapisan data sisi anak |
| `auth.py`, `sessions.py` | Login PBKDF2, sesi token JSON |
| `database.py`, `schema.py` | SQLite |
| `diagnosis.py` | Jawaban → kode B/K/H/E/T/N |
| `llm.py` | DeepSeek — HANYA memparafrase kalimat soal (opsi B2) |
| `rumus.py` | Kartu rumus per konsep |
| `attachments.py` | Foto lembar anak → AI vision → konfirmasi guru |

Deploy: push `main` → GitHub Actions (test → build GHCR → deploy by digest
via forced-command SSH `/usr/local/bin/osn-deploy` di VPS) → swap container,
auto-rollback kalau healthcheck gagal.

## 6. Palang yang tidak boleh dilemahkan

**Privasi data anak.** Tidak ada data anak yang boleh masuk repo: `*.db`,
`sandi.json`, `sesi.json`, lembar terisi, `cache_llm/`, `turunan/`,
`kejadian/` semuanya di-gitignore. CI punya job yang menolak build kalau
berkas semacam itu ter-commit. Jangan pernah `git add -f` untuk melewatinya.
Aplikasi juga **tidak menyimpan email/telepon siapa pun** — jadi jangan
usulkan fitur yang butuh kontak (reset sandi via email, notifikasi email).

**Palang murid.** Rute dan fungsi sisi anak tidak boleh menyentuh
`kunci`/`malrule`/`diagnosis`/`laporan`. Ditegakkan `__tests__/test_students.py`
lewat `sqlite3.Row` yang di-monkeypatch supaya meledak saat kolom di
`KOLOM_TERLARANG` (`kunci`, `malrule_id`, `kode_usulan`, `kode_final`,
`alasan`) dibaca. Fixture penting: `db` biasa (perspektif guru) vs
`db_terjaga` (palang aktif) — jangan gabungkan.

- Rute MURID harus didaftarkan **sebelum** palang guru `_lolos_sandi`.
- Fungsi yang menyentuh kunci harus di permukaan terpisah (mis.
  `diagnosa_murid` tinggal di `web.py`, bukan `students.py`).
- CSS halaman murid wajib di `GAYA_STITCH`, bukan `CSS_SESI` (kena 2x).

**Kepemilikan.** Guru hanya boleh menyentuh datanya sendiri; id yang bukan
miliknya dijawab **404** (bukan 403) dengan body identik, supaya keberadaan
resource tidak bisa diprobe. Admin: baca-semua, tulis-tidak-ada.

**Fixture yang kena palang baru distempel eksplisit** (`pemilik="guru"`),
bukan palangnya yang dikendurkan.

## 7. Menambah/mengubah soal — bug class yang selalu balik

**Malrule yang runtuh diam-diam.** `saring_malrule` membuang malrule yang
nilainya sama dengan kunci atau dengan malrule lain — soal jadi kehilangan
jalur diagnosis K, tapi **semua test tetap hijau**. Gejala tidak terlihat
dari membaca kode.

Aturan yang terbukti:

1. Urutan daftar malrule menentukan siapa yang selamat (yang PERTAMA
   disimpan). Kalau K bisa menyamai H, taruh **H dulu**.
2. Bentrok karena identitas aritmetika (`N//d == N%d`, `d == 2*sisa`,
   `a^b` dengan siklus satuan 1) diperbaiki di `_parameter` dengan
   while-loop reject, bukan sekadar urutan.
3. Nudge pakai **while**, bukan `if` sekali:
   `while str(h) in (kunci, k1, k2): h += 1`.
4. Kunci desimal (π=3,14): kunci dan semua malrule diformat sama
   (koma desimal). H desimal = kunci−0,1, bukan kunci−1.
5. Satu nama variabel malrule per branch (`k1`/`k2`/`h` di SEMUA branch) —
   nama beda per varian → `UnboundLocalError` di branch yang tak
   mendefinisikannya.
6. Key dict `_parameter` **wajib sama** dengan nama argumen fungsi template.
   `TypeError: unexpected keyword argument` = cek key dict dulu.
7. Kalau `_parameter` sudah menghitung jawabannya, template **baca saja**,
   jangan hitung ulang.
8. **JANGAN pakai `hash()` untuk mengacak apa pun.** `PYTHONHASHSEED` acak
   per proses → seed sama menghasilkan soal berbeda di proses berbeda,
   dan test determinisme satu-proses tidak menangkapnya. Hitung dengan
   `rng` di `_parameter`, jadikan parameter eksplisit.

Guard terkait: `__tests__/test_level.py` (≤2% soal tanpa jalur K per
template) dan `__tests__/test_parameter_variants.py` (500 seed; template di
luar 19 template asli wajib ≥200 kombinasi parameter unik).

**Verifikasi wajib setelah menyentuh modul topik apa pun** — jalankan
generator lintas seed × level, jangan cuma membaca kode. `NameError`,
`KeyError`, dan `SyntaxError` di cabang jarang hanya muncul saat render:

```python
for t in topics.daftar_topik():
    for lv, urut in topics.ambil(t).komposisi.items():
        for tid in set(urut):
            for sd in range(25):
                REGISTRI[tid](**paket.parameter_untuk(tid, random.Random(sd), lv))
```

**Guard yang sengaja merah saat menambah template:**
`test_rumus.py::test_semua_template_punya_kartu` dan
`test_pembahasan_semua.py::test_pembahasan_tidak_generik` menyapu SEMUA
template. Template baru wajib ikut memikirkan kartu rumus dan pembahasan
yang dibaca anak — jangan dikendurkan, lengkapi kontennya.

**Test kontrak registry harus superset**, bukan daftar tertutup: pakai
`in` / `<=` / `>=`, jangan `== [...]` atau `== 19`. Daftar tertutup pecah
setiap kali paket baru masuk.

**Pembahasan dibaca ANAK.** Bahasa guru (malrule, kode diagnosis, istilah
teknis) tidak boleh bocor ke sana. Fakta di pembahasan harus benar — 7 cacat
(fakta salah, latar mustahil, frasa janggal) pernah lolos semua test dan
baru ketahuan saat soal + kunci + pembahasan **dicetak dan dibaca**.

**Pemilihan jenis soal = keputusan kurikulum. Tanya user dulu**, jangan
diputuskan sendiri.

## 8. Menulis test di sini

- **Guard baru wajib dibuktikan menggigit lewat mutation testing:** hidupkan
  ulang bug-nya (atau hapus fix-nya), jalankan test itu, pastikan **MERAH**,
  pulihkan, pastikan hijau. Test hijau yang baru lahir tidak membuktikan apa
  pun. Mutasinya harus lewat jalur yang SAMA dengan yang test panggil —
  pernah kejadian mutasi lolos karena test tak pernah menyentuh jalur itu.
- Sebelum mutasi: `cp` file ke `/tmp`, pulihkan dengan `cp` (bukan
  `git checkout`, lihat §3).
- **404 saja bukan assertion yang cukup** — buktikan juga efek sampingnya
  tidak terjadi.
- **Fixture `db` / `db_terjaga` TIDAK ada di conftest** — didefinisikan lokal
  per berkas test. Berkas test baru harus menyalin definisinya sendiri
  (`fixture 'db' not found` = ini penyebabnya). `conftest.py` hanya menurunkan
  iterasi PBKDF2 lewat `OSN_PBKDF2_ITERASI`.
- **Test yang meng-assert markup persis gampang pecah.** Sebelum menambah
  `class=` ke tag mana pun:
  `grep -rn '<h1\|class=' __tests__/ | grep assert`. Pola yang disetujui saat
  refresh desain: **pertahankan marker HTML lama sebagai elemen anak**, lalu
  matikan tampilan lamanya lewat CSS override. Hilangkan tampilan via CSS,
  jangan hilangkan marker via HTML.
- Marker CSS bisa bikin `assert "X not in html"` false-positive — assert pada
  marker BENAR/kode, bukan pada nilai kunci (halaman murid memantulkan
  jawaban anak ke `<input value=...>`).
- Refactor "dipindah, bukan diubah": kunci perilaku dulu dengan golden
  signature (`test_golden_identity.py`), lalu wajib identik byte-per-byte
  sesudahnya. Kalau merah, **cari perubahan perilakunya — jangan update
  angka goldennya.**

## 9. Alur kerja & commit

1. **Pahami dulu, lapor, baru eksekusi.** Untuk bug/pertanyaan: telusuri
   kodenya, laporkan root cause dengan `file:line`, tawarkan opsi + trade-off.
   Baru kerjakan setelah user memilih. "Coba kamu cek ya" = investigasi
   sendiri sampai ketemu akarnya, bukan balik bertanya duluan.
2. **Perubahan non-trivial: tulis plan dulu** ke
   `docs/plan/YYYY-MM-DD-slug.md`. Folder itu **gitignored** — jangan
   di-commit (`git add` akan gagal "paths ignored").
3. TDD per task: test merah dulu → implementasi minimal → hijau → satu commit
   lokal per task.
4. **Commit lokal saja. JANGAN push tanpa perintah eksplisit.** "commit dulu"
   = commit saja. "push" / "commit dan push ya" = baru boleh push ke `main`.
5. Format commit: conventional commit Bahasa Indonesia dengan scope —
   `feat(soal):`, `fix(murid):`, `docs(mesin):`, `test(guru):`,
   `refactor(soal):`.
6. **Pesan commit multi-baris SELALU lewat berkas**: tulis ke `/tmp/msg.txt`
   lalu `git commit -F /tmp/msg.txt`. Karakter `>`, `$`, backtick, `!` di
   `-m` dipecah shell dan bikin error "pathspec did not match".
7. **Jangan campur WIP sesi sebelumnya ke commit fiturmu.** Cek
   `git -C /Users/nugroho/Documents/osn status` sebelum mulai; kalau ada
   perubahan yang bukan punyamu, commit terpisah atau tanya.
8. **Commit lintas-berkas jangan dipecah sebagian.** Fitur yang menyentuh
   kode + test harus masuk satu commit — commit parsial bikin CI merah untuk
   semua orang.
9. Setelah push (kalau diminta): pantau CI sampai selesai —
   `gh run list --repo clarinovist/osn-mesin-latihan --branch main` lalu
   `gh run watch <id> --exit-status`. Hijau = sudah live di produksi. Lalu
   verifikasi ringan lewat curl ke produksi (halaman publik 200, `/akun`
   tanpa kredensial 401, `/murid/` 303 ke `/masuk`) — **jangan pernah
   menyentuh data anak**.

## 10. UI, desain, dan uji visual

- Semua nilai visual lewat `design_tokens.py` (`T.*`) yang dipakai di
  `teacher_style.py` / `style_stitch.py` — **tidak ada hex hardcoded**.
- Satu aksi = satu entry point per halaman. CTA/tautan ganda dianggap bug.
  Form pembuatan yang tumpang tindih antar section juga.
- Tombol destruktif: `confirm()` yang menyebut konsekuensi persisnya
  ("Hapus akun ini? Anaknya tetap ada — hanya loginnya yang hilang.").
- Alat perbaikan jalur-langka dirender kontekstual: sembunyi saat normal
  (dengan catatan tenang), muncul saat memang ada yang perlu diperbaiki.
  Handler POST tetap menegakkan invariannya sendiri — POST tidak boleh
  dipercaya.
- Semua input sandi punya toggle mata.
- **Keluhan tampilan tidak boleh didiagnosis dari CSS saja** — render
  halamannya dan lihat. Untuk halaman berdata, jangan pakai `serve.py`
  (menempel DB & sandi asli): tulis server sekali-pakai yang mengarahkan
  `database.BAWAAN` dan berkas sandi ke berkas temp, seed data minimal,
  screenshot, lalu matikan.
- Screenshot headless Chrome wajib `--user-data-dir` terisolasi (profil
  default membawa sesi guru user → `/` malah menampilkan dashboard, bukan
  landing publik). Halaman ber-auth: `curl -u user:pass` ke berkas, lalu
  screenshot `file://` — Chrome membuang kredensial di URL.
- `file://` tidak memuat font CDN, jadi ikon Material Symbols tampil sebagai
  teks (`login`, `school`). Itu **bukan** bug — cek keberadaan elemennya.
- Breakpoint pill 2-kolom Stitch: `24rem`, bukan `36rem`.
- `@import` font harus satu baris utuh, atau pakai `<link>` di `<head>`.

## 11. Produksi & deploy

- Server produksi hanya lewat SSH alias **`biznet-sekolahdesain`**. Setiap
  `docker ...` harus diawali `ssh biznet-sekolahdesain '...'` — jangan
  dijalankan lokal.
- **Pertanyaan "apakah aplikasi punya X?" dijawab dari container yang
  berjalan, bukan dari checkout lokal.** Repo lokal bisa lebih maju
  (fase belum di-commit) atau lebih basi (image belum diperbarui).
- "Kode ter-deploy" dan "fitur berfungsi" adalah dua klaim berbeda —
  `llm.py` sengaja fail-dry, jadi konfigurasi yang hilang menghasilkan
  ketiadaan fitur yang **senyap total**, tanpa error di mana pun.
- Migrasi skema di produksi (ada data anak asli): backup dulu via
  `cadangkan.sh`, uji idempotensi + `PRAGMA foreign_key_check`, dan laporkan
  hanya angka agregat — jangan pernah nama anak.
- Untuk pertanyaan "kenapa data X kosong", kueri backup terbaru di
  `mesin/cadangan/` secara read-only
  (`sqlite3 "file:...?mode=ro"`), bukan DB lokal (yang biasanya kosong).
- `Dockerfile` memakai `COPY *.py` (wildcard) — modul baru otomatis ikut,
  tidak perlu diedit. Guard `__tests__/test_image.py` menegakkan kontrak itu
  dan **menolak** kembalinya daftar manual.
- `/usr/local/bin/osn-deploy` di VPS **tidak tracked di repo**. Kalau
  disentuh, sunting kedua jalur `docker run` (deploy utama DAN rollback) —
  lupa yang rollback berarti deploy gagal diam-diam menghidupkan app tanpa
  konfigurasi.

## 12. Konteks kurikulum & klaim produk

Angka dari audit 1.237 soal OSN asli 2016–2026
(`docs/riset-soal-osn-10-tahun.md`) — pakai ini, bukan tebakan:

- 85 template menutup **74,7%** konsep soal nyata. NAS-eksplorasi cuma
  **24,4%**.
- Bobot topik nyata: Aritmatika 24,2% ≈ Geometri 23,2% > Bilangan 21,5% >
  Statistika-Pengukuran 16,2% > Kombinatorik 14,9%. Dugaan lama "Geometri
  paling besar" **salah**. Pie 25/25/12/38% di silabus resmi = klip-art
  dekoratif, bukan bobot — jangan dikutip.
- Non-rutin naik per tahap: kecamatan 10,6% → OSN-K 26,4% → OSN-P 33,3% →
  nasional ~47% → eksplorasi 100%.
- **Batas jujur produk:** klaim yang aman = "fondasi + pola soal OSN-S/K/P".
  Klaim "siap juara nasional" tidak didukung data — soal eksplorasi minta
  anak mengkonstruksi, tak punya kunci tunggal, bertentangan dengan
  arsitektur diagnosa/malrule. Ini bukan gap yang bisa ditutup dengan
  template.
- Dua template yang belum pernah muncul (`dua_besaran_selisih`, `piktogram`)
  **jangan dihapus** — piktogram ada di silabus resmi.
- P3 tidak lagi dibatasi ke pola-bilangan saja (SASMO memakai band P1–4).

## 13. Kebiasaan yang dihargai user

- Jujur soal batas: "ini belum ada di kode" > overpromise. Klaim "sudah
  diverifikasi" harus disertai output tool nyata, bukan ingatan.
- Kalau menemukan bug di luar scope, angkat terbuka — itu dihargai.
- Review/audit disajikan sebagai tabel + severity (High/Medium/Low), bukan
  narasi panjang.
- Tawarkan opsi A/B dengan trade-off, jangan satu rekomendasi tunggal.
- Ringkas. Tabel > paragraf.
