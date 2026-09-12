# Rilis Pendamping v4 — persiapan dan batas pemasangan

Status dokumen: **B1 persiapan source/CI**. Bukan catatan migrasi selesai.
Panduan [CLAUDE.md](../CLAUDE.md), [kontrak runtime](pendamping-runtime.md), dan
izin operasi produksi tetap berlaku. Data keluarga/credential tidak masuk repo.

## Mengapa rilis ini perlu pengaman

Inspeksi read-only 12 September 2026 menemukan image produksi revision
`7830b6d3eff11b7a5df41d84260b9b65cd7823ef`, manifest digest
`sha256:0129ea4779dd455c900c16435a4e772a342df53d6be836d3813ebe46db302569`.
Pendamping memakai schema v3. Commit `be4ab003f926382238ea9e7153f063b9c50e9e75`
menambah schema v4 dan catatan eksekusi di DB belajar; binary v3 menolak v4.
Ini snapshot inspeksi, bukan jaminan keadaan live setelah tanggal tersebut.

Deployer lama kembali ke image sebelumnya dan hanya memeriksa halaman publik.
Kegagalan `docker run` langsung dapat keluar sebelum bagian rollback. Karena
itu, keberhasilan uji UI tidak mengizinkan mengganti container tanpa recovery
kompatibel. Menurunkan user_version atau menghapus catatan eksekusi bukan solusi.

## Jalur CI yang dijaga

Workflow tetap **uji → bangun → pasang**:

1. **uji:** palang privasi + full pytest candidate; checkout recovery pinned
   full SHA, cwd terpisah, canary lokasi import, palang dan full pytest recovery.
2. **bangun:** build/publish candidate serta recovery; tarik berdasarkan digest
   output build yang sama; verifikasi image sebenarnya dengan probe sintetis.
   Salah satu gagal berarti job gagal, tidak lanjut pasang.
3. **pasang:** hanya pada `refs/heads/main` jika repository variable
   `PENDAMPING_ROLLOUT_SIAP` **persis `1`**. Default tidak disetel berarti skip
   seluruh job, termasuk akses secret SSH. Pada B1 variable ini tidak diaktifkan.

B1 diizinkan push `main`, **bukan cutover**. Publikasi tidak mengganti tag
`latest`. Tag `sha-<SHA>` dan `recovery-<SHA>` membantu inventaris, tetapi dapat
berubah jika build diulang; identitas rilis selalu digest output build.
Manifest artifact menyimpan kedua revision/digest. Job pasang mengirim protokol
`deploy-v2 <candidate-digest> <recovery-digest>`, bukan perintah shell bebas.
Deployer live v1 tidak boleh dipakai untuk menjalankan protokol ini.

Jika variable diaktifkan sesudah job skip, job tidak otomatis lanjut. Dispatch
ulang dapat membangun digest baru: **semua digest baru harus diverifikasi dan
mendapat approval baru**, bukan diam-diam menggantikan pasangan yang disetujui.
Runbook B2 harus mengunci cara melanjutkan job/dispatch/pemasangan artifact yang
tepat. Jangan enable variable sebelum deployer, approval, backup dan write hold
siap; matikan eligibility lagi setelah jendela rilis sesuai izin operator.

## Recovery berbeda dari candidate

Recovery dibangun dari pinned commit backend v4
`bc9c973b50eb1fb04edd37df62f71ba0123f29c6`: UI sebelum redesign, guard
tinjauan server, catatan eksekusi dan idempotensi tahan crash, ditambah perbaikan
penutupan transport HTTP yang sama dengan kandidat.
Recovery bukan image produksi lama, bukan perubahan konstanta schema saja,
dan bukan memilih kembali candidate yang sama ketika gagal.

`verify_release_image.py` menjalankan probe stdlib lewat stdin ke image digest
tertentu, non-root, filesystem read-only, tmpfs sintetis dan `--network none`.
Tidak bind-mount source host, Docker socket, atau volume produksi. Uji meliputi
migrasi sintetis v3→v4 berulang/parsial, preservation/FK/integrity, tinjauan,
crash setelah commit belajar, retry satu sesi, hasil batal/hapus, perubahan
pemilik/izin, invariansi bukti dan HTTP/aset. Output hanya ringkasan teknis.
Lolos probe sintetis bukan pengganti rehearsal backup keluarga saat B2.

## Artefak deployer v2

Deployer v2 berada di `scripts/deploy.py` dan diuji oleh
`mesin/__tests__/test_deployer.py`. Keberadaan source tidak otomatis mengizinkan
instalasi atau eksekusi: artefak yang dipasang harus cocok hash source yang sudah
lolos gate, lalu approval B2 dibuat untuk tepat satu pasangan digest setelah
backup dan write hold benar-benar aktif.
Kontrak yang wajib dipenuhi: forced-command/registry/path terbatas, approval
root-controlled sekali pakai dan lock sebelum perubahan container, kedua image
siap sebelum swap, konfigurasi sama pada run utama/recovery, serta health
`/akun` anonim 401 dan kesiapan schema read-only—bukan sekadar `/` 200.

- Preflight ditolak: container lama tidak disentuh.
- Rilis gagal, recovery sehat: tetap lapor kegagalan rilis, bukan sukses.
- Stop/remove/cleanup/recovery gagal: tahan pemeliharaan dan eskalasi; jangan
  membuat dua writer pada volume yang sama atau terus menghapus container.
- Tidak auto-restore DB, downgrade schema, menghapus backup, membuka write hold
  atau mengaktifkan kembali cron melalui cleanup tanpa pemeriksaan operator.

Kontrak approval dan instalasi detail harus dicocokkan dengan source final,
hash artefak, user forced-command dan permission host yang nyata. Path/boolean
approval bukan bukti backup/drain; operator hanya menerbitkannya setelah kondisi
tersebut benar-benar diverifikasi. File yang tidak memenuhi precondition wajib
menolak, bukan di-chmod/chown otomatis oleh deployer.

## B2 — membutuhkan izin produksi tersendiri

Belum dilakukan oleh B1. Sebelum meminta persetujuan, lengkapi runbook dengan
**digest candidate/recovery nyata, hash deployer, jendela waktu/timezone,
batas durasi/dampak, mekanisme drain, backup dan recovery**.

Urutan minimum:

1. Periksa lagi revision/config/schema dan operasi lain. Pastikan image siap
   sebelum menghentikan layanan. Tidak build di VPS.
2. Pasang deployer yang disetujui secara atomik, simpan script sebelumnya secara
   terproteksi; rollback script bukan izin menjalankan binary v3 pada DB v4.
3. Tahan ingress dan seluruh writer kedua DB, drain request in-flight serta
   pause maintenance. GET/cron juga dapat menulis. Socket count nol sesaat bukan
   bukti semua writer telah berhenti. Cron terkait yang ditemukan `17 20 * * *`;
   timezone/CRON_TZ harus dikonfirmasi sebelum menjadwalkan.
4. Buat backup **pasangan** DB pada keadaan quiescent memakai SQLite backup API,
   temp unik, `umask 077`, transfer terenkripsi ke penyimpanan lokal ignored.
   Catat cutoff/manifest pasangan; hapus hanya temp milik operasi ini.
   **Tidak prune backup lama.** `mesin/cadangkan.sh` existing memakai temp tetap
   dan prune >30 hari, jadi jangan menjalankannya apa adanya sambil mengklaim
   prosedur no-prune. Helper final perlu review dan izin sesuai efek sebenarnya.
5. Rehearsal pada turunan backup, bukan backup induk. Migrasi aktual dua kali,
   integrity/FK serta invariant lintas DB. Tanpa provider/AI atau log isi keluarga.
   Jika write hold sempat dilepas, ambil backup pasangan final baru.
6. Migrasi terkontrol saat write hold sebelum readiness v4; jangan memanggil
   migrator dari pemeriksaan yang diklaim read-only. Pasang digest candidate
   yang sama dengan approval/verifikasi; fallback hanya recovery v4 yang diuji.
7. Periksa schema/integritas/revision/digest aktual. Smoke publik kanonis:
   `https://jagomat.id/` 200, `/akun` 401 anonim, `/murid/` 303 ke `/masuk`.
   Smoke fitur memakai lingkungan sintetis terisolasi, bukan akun keluarga.
8. Buka writer dan resume cron hanya setelah keadaan aman. Recovery gagal
   berarti tetap pemeliharaan dan lapor; jangan restore backup otomatis.

Restore DB memerlukan izin pemulihan data khusus dengan pasangan/cutoff/RPO
serta potensi kehilangan data dan rekonsiliasi. Izin push tidak mencakupnya.

## Pelaporan jujur

B1 selesai berarti **source teruji dan image dibangun/diverifikasi**; bukan
aplikasi sudah terpasang. CI pasang skip yang disengaja harus dilaporkan sebagai
tertahan B1. Tidak ada klaim deployment hanya karena push atau build berhasil.
