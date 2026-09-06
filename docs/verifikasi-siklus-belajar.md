# Verifikasi siklus belajar terpandu

## Ruang lingkup

Fase 7 memeriksa alur lintas tahap di atas baseline `99f27f5`.
Fase 8 adalah dokumentasi, commit, push, dan verifikasi deploy—bukan fitur visual.
Seluruh data pengujian sintetis pada SQLite sementara. Tidak ada backfill,
perubahan skema, atau koreksi data anak produksi.

## Temuan yang diperbaiki

- Evaluasi gagal pertama: intervensi alternatif kini membuka rangkaian latihan
  baru berdasarkan urutan kejadian, termasuk kejadian pada tanggal yang sama.
  Sesi terbimbing/penguatan lama tidak memenuhi rangkaian baru; gagal kedua
  tetap eskalasi.
- Kekambuhan: kartu menyediakan aksi POST pembukaan putaran baru, dihitung
  ulang server-side. Snapshot lama tetap identik; double-submit idempoten dan
  kegagalan transaksi di tengah pembukaan di-rollback.
- Pencarian soal baru: pilih pengganti per-butir, bukan membuang seluruh lembar
  karena satu benturan. Sepuluh soal tersisa dapat dirangkai. Bila ruang soal
  tidak cukup, respons 409 ramah tanpa sesi parsial. Generator umum/golden
  tidak diubah; penyajian memakai parameter butir yang tersimpan.
- Label kekambuhan tidak lagi menyatakan pemetaan 0/3.
- Pada putaran dua fokus, fokus non-kambuh diteruskan lewat event eksplisit
  dan proyeksi immutable; tahap serta nomor checkpoint-nya tidak hilang.
  Baris sesi/snapshot lama tidak dipindah. Tiga guard penerusan menjadi merah
  saat proyeksi dimatikan, lalu kembali hijau pada kode normal.
- Review akhir spesifikasi dan kualitas/security: PASS setelah temuan
  pencarian soal dan penerusan fokus kedua ditutup; tidak ada temuan terbuka.

## Bukti eksekusi lokal

- Baseline: 5865 test lulus, tanpa warning.
- Gate lokal terakhir: 5880 test lulus (24,65 detik), tanpa warning;
  kompilasi Python 3.9 dan `git diff --check` lulus.
- Dua gap rantai direproduksi RED sebelum perubahan; GREEN setelah perbaikan.
- Review pertama menemukan pencarian soal gagal 3 dari 30 proses. Sesudah
  perbaikan per-butir, 30 dari 30 proses E2E lulus (90 kasus saat pengujian).
- Kasus deterministik sisa tepat 10 soal: RED pada pencarian seed lama,
  GREEN pada pemilihan butir baru. Exhaustion: 500 menjadi 409, dump DB identik.
- Mutation: mematikan pemulihan, aksi restart menjadi no-op, menghapus
  rollback internal, serta melewati penyaringan soal baru membuat guard merah;
  setelah mutan dilepas guard kembali hijau. Mutan runtime tidak mengubah source.
- Trace stdlib (termasuk thread HTTP): `cycle_recovery.py` 31/32 baris (96,9%),
  `cycle_restart.py` 46/49 (93,9%), `cycle_carry.py` 34/36 (94,4%).
  Ini cakupan baris, bukan branch coverage.
- Browser sintetis 390/1440px: tidak ada overflow horizontal, tinggi CTA
  48,8px. Klik nyata dengan JavaScript dimatikan mengubah kartu kekambuhan
  menjadi intervensi. Preview ditutup setelah verifikasi.

## Matriks 17 skenario fase 7

Semua nama berkas di bawah berada pada `mesin/__tests__/`.

| No | Kontrak | Bukti pengujian |
|---|---|---|
| 1 | Anak baru, pemetaan 0/3 | `test_learning_cycle_ui.py` anak baru |
| 2 | Tiga tanggal, anchor, kandidat terlambat, maksimal dua fokus | `test_learning_cycle.py` anchor/ranking; `test_learning_cycle_generator.py`; rantai E2E pemetaan |
| 3 | Intervensi → terbimbing → penguatan | `test_learning_cycle_e2e.py` rantai sampai evaluasi |
| 4 | Penguatan/manual tidak menambah kelemahan, jeda | `test_learning_cycle.py` anti-penggelembungan/opt-in; E2E jeda |
| 5 | Jeda tiga hari, soal baru, minimal empat probe | `test_learning_cycle.py` waktu domain; generator evaluasi; E2E |
| 6 | Ragu/menghafal belum lulus; N-derived | `test_learning_cycle.py` N dan pemahaman; E2E evaluasi ulang |
| 7 | Alternatif setelah gagal pertama, eskalasi setelah kedua | `test_learning_cycle_e2e.py` pemulihan; unit tanpa alternatif |
| 8 | Checkpoint dua bagian, 28 hari | `test_learning_cycle_e2e.py` rantai checkpoint; unit per-fokus |
| 9 | Bertahan, checkpoint berkala, putaran kambuh | `test_learning_cycle_e2e.py` checkpoint berulang/restart; guard rollback |
| 10 | T → pengenalan → probe; strategi B/H/E/N | `test_learning_cycle_e2e.py` pengenalan; unit intervensi per-kode |
| 11 | Direview belum sah; sesi stale/manual tidak memblokir | `test_learning_cycle_ui.py`, `test_learning_cycle_routes.py` |
| 12 | Double-submit, batal/retry, occurrence | `test_learning_cycle_http.py`, `test_learning_cycle_actions.py`; E2E restart |
| 13 | Invalidasi dan snapshot lama | `test_learning_cycle.py`, `test_learning_cycle_routes.py` |
| 14 | Override terlambat non-destruktif | `test_learning_cycle_http.py` override; `test_learning_cycle_actions.py` |
| 15 | Perubahan level tanpa menghapus histori | `test_learning_cycle_routes.py`, `test_learning_journey.py` |
| 16 | Profil/laporan dari reducer sama | `test_learning_journey.py`, `test_laporan_ortu.py` |
| 17 | Isolasi keluarga dan palang anak | `test_learning_cycle_routes.py`, `test_cycle_restart_guards.py`, `test_learning_stage_labels.py`, `test_students.py` |

## Batas klaim

E2E HTTP membuat sesi, mengonfirmasi hasil, dan melakukan aksi melalui router
nyata; selesainya pekerjaan anak disimulasikan melalui helper database.
Ini bukan pengujian pada HP fisik atau E2E akun produksi. Tidak ada klaim
penguasaan permanen atau kurikulum adaptif baru.

Implementasi dan test fase 7: commit `1b56c1a`.
Review akhir PASS, tanpa temuan terbuka. Push/deploy diverifikasi terpisah
melalui run CI untuk SHA penutupan; hasil runtime dicatat pada plan lokal.
