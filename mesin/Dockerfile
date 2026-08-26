# Mesin latihan — container terisolasi.
#
# Berjalan sebagai user tanpa hak istimewa. Aplikasi ini memuat data anak,
# jadi tidak menumpang user `sekolahdesain` yang dipakai layanan lain dan
# punya cron auto-pull ke repo kerja.
#
# Tanpa dependensi pihak ketiga: seluruh aplikasi hanya memakai stdlib,
# sehingga image-nya tetap kecil dan tidak ada yang perlu diperbarui karena
# CVE pustaka.

FROM python:3.12-slim

# Pengguna khusus, bukan root. UID/GID dipatok agar berkas basis data di
# volume tetap dimiliki pengguna yang sama setelah image dibangun ulang.
RUN groupadd -g 10001 osn && useradd -u 10001 -g osn -m -s /usr/sbin/nologin osn

WORKDIR /app

# Hanya berkas aplikasi. Basis data dan sandi TIDAK ikut masuk image —
# keduanya datang dari volume saat dijalankan.
#
# DAFTAR INI WAJIB DIPERBARUI TIAP ADA MODUL BARU. Pernah terjadi (25 Agustus
# 2026): render.py & murid.py lahir tapi tidak masuk daftar ini, image terbangun
# "sukses", deploy gagal sehat karena import error, dan rollback otomatis yang
# menyelamatkan situs justru menyembunyikan penyebabnya — di lokal semua test
# hijau karena filenya ada; yang hilang hanya di dalam image.
COPY --chown=osn:osn templates.py generator.py skema.py basis.py \
     diagnosa.py cetak.py web.py sandi.py sajikan.py buat_lembar.py \
     siapkan_db.py periksa_sehat.py \
     render.py gaya_layar.py gaya_cetak.py \
     murid.py llm.py /app/

# Basis data & sandi tinggal di volume supaya selamat saat container diganti.
ENV OSN_BERKAS_SANDI=/data/sandi.json \
    OSN_BERKAS_DB=/data/latihan.db \
    OSN_FOLDER_LEMBAR=/data/lembar \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /data && chown osn:osn /data
VOLUME ["/data"]

USER osn
EXPOSE 8724

# Pemeriksaan kesehatan: 401 dihitung SEHAT, karena justru menandakan server
# menjawab DAN palang sandi aktif. Yang tidak sehat adalah tidak menjawab
# sama sekali, atau menjawab 200 tanpa diminta sandi (palang jebol).
COPY --chown=osn:osn periksa_sehat.py /app/
HEALTHCHECK --interval=60s --timeout=8s --start-period=15s --retries=3 \
  CMD ["python", "/app/periksa_sehat.py"]

CMD ["python", "sajikan.py", "--jaringan", "--port", "8724"]
