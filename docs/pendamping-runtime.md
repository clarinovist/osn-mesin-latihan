# Kontrak runtime Pendamping

Dokumen ini menjelaskan kontrak **source**, bukan bukti deployment atau penerimaan
redesign. Arah produk tetap [spesifikasi Pendamping](pendamping-jagomat.md);
[palang proyek](../CLAUDE.md) dan [siklus belajar](siklus-belajar-terpandu.md)
tetap berlaku. Seluruh verifikasi lokal menggunakan DB, akun, dan provider sintetis.

## Tinjauan dan pembuatan latihan

- GET tinjauan yang sah menerbitkan token acak, menyimpan **hash token** dan
  ikatan snapshot usulan di DB Pendamping. Ini bukti server menerbitkan tinjauan,
  bukan bukti manusia sudah membaca atau memahami layar.
- Ikatan mencakup generasi akun, pemilik, usulan/payload/hash/versi, pesan sumber,
  chat/versinya, serta consent dan konteks yang ditinjau. POST tidak boleh
  menerbitkan tinjauan sendiri. Token palsu atau milik tinjauan lain ditolak.
- Tinjauan berlaku 30 menit untuk membuat latihan. Membuka tinjauan baru mengganti
  token lama; tab lama mendapat konflik. Refresh tidak mengesahkan usulan usang.
- Konfirmasi menggunakan transaksi privat, lalu transaksi data belajar. Tidak
  ada panggilan provider saat transaksi ditahan. Generator, penguncian sesi,
  dan catatan eksekusi berada dalam transaksi data belajar yang sama.
- Catatan eksekusi `eksekusi_pendamping` mengikat identitas usulan, bukan isi
  payload saja. Hasil commit data belajar dapat ditemukan kembali apabila proses
  terhenti sebelum hasil tersimpan di DB Pendamping. Retry tidak meregenerasi.
- Lookup hasil tetap memeriksa chat, izin, serta kepemilikan sumber dan sesi
  hasil. Sumber/hasil asing atau hilang yang tidak boleh diakses mendapat 404
  generik; hasil dibatalkan/dihapus tidak dibuat ulang. Hasil yang membuat
  ringkasan anak usang dapat ditemukan tanpa menuntut ringkasan lama tetap segar.
- Latihan tetap `bebas`, tanpa putaran atau konfirmasi bukti belajar. Tidak ada
  penulisan diagnosis, fokus, atau kejadian siklus oleh konfirmasi Pendamping.

## Request chat dan consent konteks

- Reservasi chat awal dan operasi dilakukan atomik. Submit ulang request yang
  sama menuju chat asal; bukan membuat chat kosong tambahan.
- Request terikat akun, chat, dan teks pesan asal. Hasil tidak boleh dipinjam oleh
  chat lain. Request pending/gagal tidak otomatis memanggil provider ulang.
- Versi consent konteks adalah versi yang melekat pada **resource chat itu**,
  bukan versi izin terakhir seluruh akun. Memilih resource lain tidak membuat
  chat lama yang masih sah gagal. Resource/izin chat sendiri tetap divalidasi
  sebelum dan sesudah pemanggilan provider.
- Pemulihan request bukan izin menghidupkan chat yang dihapus atau konteks yang
  dicabut. Mode tanpa memori tetap immutable.

## Isi memori

Koreksi manual dan draft model menggunakan validator isi yang sama. Memori
hanya menerima bentuk preferensi cara menjawab yang dikenali, misalnya:

- “Jawab ringkas dengan contoh konkret.”
- “Gunakan kalimat pendek.”
- “Dengarkan dulu sebelum memberi saran.”

Ini **bukan penyimpanan bahasa alami bebas**. Frasa di luar bentuk yang didukung
(termasuk preferensi yang mungkin aman tetapi belum dikenali) ditolak, bukan
teksnya dibersihkan atau diparafrase diam-diam. Label/profil/curhatan/kontak/
credential, termasuk awalan preferensi diikuti cerita personal, tidak diterima.
Penggunaan nonaktif tetap mengizinkan koreksi manual; draft tidak otomatis
terkonfirmasi. Invalidasi versi dan kepemilikan tetap berlaku.

Batas patch: validator baru tidak melakukan audit/backfill memori warisan dan
bukan klaim filter chat umum mendeteksi seluruh kemungkinan data personal.
Penolakan koreksi masih mengikuti respons generik endpoint existing; penjelasan
editor yang lebih membantu termasuk pekerjaan UX yang belum diterima.

## Skema, retensi, dan recovery

- Skema privat versi 4 menambah `tinjauan_usulan` secara additive. Tabel ini
  menyimpan hash dan waktu, tidak menyimpan salinan teks chat; purge usulan
  menghapus tinjauannya melalui FK cascade.
- DB belajar menambah `eksekusi_pendamping`: hash identitas/tinjauan dan ID sesi,
  tanpa nama, teks pesan, jawaban, atau payload usulan. ID sesi sengaja bukan FK:
  menghapus sesi tidak boleh menghapus penanda bahwa usulan pernah dieksekusi.
- Penanda eksekusi tersebut bertahan setelah penghapusan sesi/chat untuk mencegah
  eksekusi kedua. Ini bukan bukti pedagogis dan tidak menjanjikan seluruh metadata
  turunan hilang bersama chat. Retensi teks chat tetap 180 hari sejak aktivitas
  terakhir, operasi pending/gagal 7 hari, dan cadangan maksimal 30 hari sesuai
  pengelola retensi existing.
- Jaminan deduplikasi tahan crash berlaku untuk eksekusi melalui runtime baru.
  Hasil lama yang masih memiliki pointer/kunci tetap diperiksa kepemilikannya.
  Crash pada runtime lama yang disusul penghapusan sesi sebelum catatan eksekusi
  tersedia tidak dapat direkonstruksi pasti; patch tidak mengarang riwayat atau
  melakukan backfill dari data keluarga.
- Jangan menurunkan `user_version` atau menghapus catatan eksekusi untuk
  memulihkan request. Usulan usang perlu usulan baru, bukan reaktivasi data lama.
- Rollback binary sebelum skema privat v4 **tidak otomatis kompatibel** karena
  aplikasi lama menolak versi lebih baru. Recovery harus memakai binary yang
  memahami v4 atau perbaikan maju; jangan memulihkan DB lama sebagai rollback UI.
- Sebelum rollout/migrasi produksi: izin baru, cadangan konsisten kedua DB,
  rehearsal idempoten, `integrity_check`/`foreign_key_check`, dan recovery siap.
  Commit lokal bukan izin push/deploy.

## Batas penerimaan

Guard/recovery diuji pada `test_assistant_review_guards.py`,
`test_assistant_retry_guards.py`, `test_assistant_memory_scope.py`, serta suite
existing Pendamping. Pengujian guard tidak menggantikan walkthrough orang tua.

Redesign shell/chat/riwayat/pengaturan, kendali data baru, label sumber, dan alur
pemulihan visual masih mengikuti gate workflow serta persetujuan prototype.
Wireframe lokal bersifat opsional, bukan dependensi aplikasi/build/test. Tidak
ada klaim seluruh UX, aksesibilitas, browser fisik, atau keadaan produksi sudah
terverifikasi hanya karena test backend lulus.
