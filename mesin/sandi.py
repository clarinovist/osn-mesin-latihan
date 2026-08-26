"""Autentikasi halaman guru.

Wajib aktif begitu aplikasi ini bisa dijangkau dari luar mesin sendiri:
halamannya memuat jawaban dan diagnosis anak, dan tanpa palang ini siapa
pun yang tahu alamatnya bisa membacanya.

Bentuknya HTTP Basic. Cukup untuk satu pengguna di balik HTTPS, tidak
menambah dependensi, dan tidak perlu tabel sesi. Yang TIDAK boleh:
menjalankannya tanpa HTTPS, karena Basic mengirim sandi sebagai teks
ter-base64 yang bisa dibaca siapa saja di jaringan.

Sandi disimpan sebagai hash PBKDF2 di berkas, bukan di kode dan bukan
sebagai teks biasa. Dibandingkan dengan compare_digest supaya lama
pembandingan tidak membocorkan berapa karakter yang sudah cocok.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

BERKAS_SANDI = Path(
    os.environ.get("OSN_BERKAS_SANDI", Path(__file__).resolve().parent / "sandi.json")
)

# PBKDF2-HMAC-SHA256, bukan scrypt.
#
# scrypt lebih tahan serangan perangkat keras, TAPI hashlib.scrypt hanya ada
# kalau Python dibangun dengan OpenSSL yang mendukungnya — ada di VPS
# (Python 3.12) dan TIDAK ADA di Mac ini (Python 3.9.6 bawaan sistem).
# Memakainya berarti sandi yang disetel di satu mesin tidak bisa diverifikasi
# di mesin lain, dan kegagalannya baru muncul saat login, bukan saat menyetel.
#
# pbkdf2_hmac tersedia di keduanya. 600.000 iterasi mengikuti anjuran OWASP
# 2023 untuk SHA-256, dan diukur ~0,2 detik di mesin ini — tidak terasa saat
# login, tapi mahal bila dicoba jutaan kali.
_ITERASI = 600_000

# Garam/kunci umpan untuk jalur akun-tak-dikenal agar waktu tetap.
# Nilai konstan ini membuat PBKDF2 tetap dijalankan walau nama tidak ada.
_UMPAN_GARAM = bytes.fromhex("aa" * 16)
_UMPAN_KUNCI = bytes.fromhex("bb" * 32)


def buat_hash(sandi: str) -> dict:
    garam = secrets.token_bytes(16)
    kunci = hashlib.pbkdf2_hmac("sha256", sandi.encode(), garam, _ITERASI, dklen=32)
    return {
        "garam": binascii.hexlify(garam).decode(),
        "kunci": binascii.hexlify(kunci).decode(),
        "iterasi": _ITERASI,
    }


def simpan_sandi(sandi: str, pengguna: str = "guru", path: Path | None = None) -> Path:
    """Setel/ganti sandi satu akun tanpa menghapus akun lain.

    PERNAH SALAH (25 Agustus 2026, tertangkap sebelum dipakai anak): versi
    pertama selalu menulis ulang berkas jadi bentuk lama satu-akun, jadi
    begitu guru mengganti sandinya lewat halaman akun, SELURUH akun murid
    lenyap. Anak tiba-tiba tidak bisa masuk, dan tidak ada pesan galat di
    mana pun — berkasnya memang tertulis "berhasil".

    Sekarang: kalau berkas sudah memuat banyak akun, hanya baris akun yang
    bersangkutan yang diperbarui; sisanya dibiarkan apa adanya.
    """
    p = path or BERKAS_SANDI
    akun = _normalisasi(muat_sandi(p))

    # Berkas belum ada / masih bentuk lama satu-akun untuk pengguna yang sama:
    # pertahankan bentuk lama supaya format tidak berubah tanpa alasan.
    if not akun or (len(akun) == 1 and akun[0]["pengguna"] == pengguna):
        p.write_text(
            json.dumps({"pengguna": pengguna, **buat_hash(sandi)}, indent=2),
            encoding="utf-8",
        )
        p.chmod(0o600)  # hanya pemilik yang boleh membaca
        return p

    ketemu = False
    for a in akun:
        if a["pengguna"].strip().lower() == pengguna.strip().lower():
            a.update(buat_hash(sandi))
            a.setdefault("peran", "guru")
            ketemu = True
    if not ketemu:
        akun.append({"pengguna": pengguna, "peran": "guru", **buat_hash(sandi)})

    p.write_text(json.dumps({"akun": akun}, indent=2), encoding="utf-8")
    p.chmod(0o600)
    return p


def muat_sandi(path: Path | None = None) -> dict | None:
    p = path or BERKAS_SANDI
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def periksa(pengguna: str, sandi: str, data: dict | None = None) -> bool:
    """Bandingkan dengan waktu tetap.

    Nama pengguna ikut dibandingkan dengan compare_digest, bukan '==', supaya
    tidak ada jalur yang lebih cepat gagal untuk nama yang salah.

    PERNAH SALAH (25 Agustus 2026): saat berkas sudah bentuk multi-akun
    ({"akun": [...]}), fungsi ini membaca d["pengguna"] yang tidak ada di
    situ dan melempar KeyError. Akibatnya begitu satu akun murid dibuat,
    GURU TIDAK BISA MENGGANTI SANDINYA SAMA SEKALI — halaman akun langsung
    500. Tidak tertangkap test mana pun karena tidak ada yang menguji urutan
    "tambah murid, lalu guru ganti sandi".
    """
    if data is None:
        mentah = muat_sandi()
        if not mentah:
            return False
        # Bentuk multi-akun: cari akun yang namanya cocok, lalu periksa
        # akun itu saja. Bentuk lama satu-akun dipakai apa adanya.
        if "akun" in mentah:
            d = None
            for a in _normalisasi(mentah):
                if a["pengguna"].strip().lower() == pengguna.strip().lower():
                    d = a
                    break
            if d is None:
                # waktu-tetap: jalankan PBKDF2 umpan supaya durasi serupa
                _ = hashlib.pbkdf2_hmac("sha256", sandi.encode(), _UMPAN_GARAM, _ITERASI, dklen=32)
                hmac.compare_digest(_, _UMPAN_KUNCI)
                return False
        else:
            d = mentah
    else:
        d = data

    if not d or "pengguna" not in d:
        return False

    nama_cocok = hmac.compare_digest(pengguna.encode(), d["pengguna"].encode())

    try:
        garam = binascii.unhexlify(d["garam"])
        harap = binascii.unhexlify(d["kunci"])
        coba = hashlib.pbkdf2_hmac(
            "sha256",
            sandi.encode(),
            garam,
            int(d.get("iterasi", _ITERASI)),
            dklen=len(harap),
        )
    except (binascii.Error, ValueError):
        return False

    sandi_cocok = hmac.compare_digest(coba, harap)
    return nama_cocok and sandi_cocok


def dari_header(header: str | None) -> tuple[str, str] | None:
    """Uraikan header Authorization: Basic <base64>."""
    if not header or not header.startswith("Basic "):
        return None
    try:
        mentah = base64.b64decode(header[6:]).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    if ":" not in mentah:
        return None
    pengguna, _, sandi = mentah.partition(":")
    return pengguna, sandi


def wajib_sandi() -> bool:
    """Apakah palang ini aktif.

    Aktif kalau berkas sandi ada. Dengan begitu pemakaian di localhost tetap
    tanpa hambatan, sementara deploy WAJIB membuat berkas sandinya — dan
    kalau lupa, ada palang kedua di sajikan.py yang menolak berjalan terbuka
    ke jaringan tanpa sandi.
    """
    return BERKAS_SANDI.exists()


# ── Peran & multi-akun (Fase 4) ──────────────────────────────────────────
#
# Bentuk berkas lama (satu guru) tetap sah:
#   {"pengguna": "guru", "garam": ..., "kunci": ..., "iterasi": ...}
#
# Bentuk baru (multi-akun):
#   {"akun": [{"pengguna": "guru", "peran": "guru", ...hash...},
#             {"pengguna": "feby",  "peran": "murid", ...hash...}]}
#
# Migrasi satu-arah terjadi saat muat: bentuk lama dibaca sebagai satu akun
# ber-peran "guru". Tidak pernah ditulis balik otomatis — penulisan hanya
# lewat simpan_akun() yang selalu menulis bentuk baru.


PERAN = ("guru", "murid")


def _normalisasi(data: dict | None) -> list[dict]:
    """Bentuk lama atau baru -> daftar akun seragam."""
    if not data:
        return []
    if "akun" in data:
        return list(data["akun"])
    # bentuk lama: satu akun tanpa kunci peran
    return [{**data, "peran": "guru"}]


def muat_akun(path: Path | None = None) -> list[dict]:
    return _normalisasi(muat_sandi(path))


def cari_akun(pengguna: str, path: Path | None = None) -> dict | None:
    """Akun dengan nama pengguna itu. Pencarian case-insensitive supaya
    'Feby' dan 'feby' adalah orang yang sama — anak tidak paham bedanya,
    dan kegagalan login yang tidak bisa dijelaskan membuat mereka menyerah."""
    p = pengguna.strip().lower()
    for a in muat_akun(path):
        if a["pengguna"].strip().lower() == p:
            return a
    return None


def periksa_peran(
    pengguna: str, sandi_diberikan: str, peran: str, path: Path | None = None
) -> bool:
    """Login + cocokkan peran sekaligus.

    Sandi diverifikasi dulu dengan waktu tetap SEBELUM peran dibandingkan:
    mengembalikan False lebih awal untuk peran yang salah akan memberi tahu
    penyerang bahwa nama penggunanya ada.
    """
    a = cari_akun(pengguna, path)
    if not a:
        _ = hashlib.pbkdf2_hmac("sha256", sandi_diberikan.encode(), _UMPAN_GARAM, _ITERASI, dklen=32)
        hmac.compare_digest(_, _UMPAN_KUNCI)
        return False
    if not periksa(a["pengguna"], sandi_diberikan, data=a):
        return False
    return a.get("peran", "guru") == peran


def peran_dari(
    pengguna: str, sandi_diberikan: str, path: Path | None = None
) -> str | None:
    """Peran akun yang kredensialnya benar, atau None. Untuk rute yang
    melayani dua peran sekaligus."""
    a = cari_akun(pengguna, path)
    if not a:
        _ = hashlib.pbkdf2_hmac("sha256", sandi_diberikan.encode(), _UMPAN_GARAM, _ITERASI, dklen=32)
        hmac.compare_digest(_, _UMPAN_KUNCI)
        return None
    if not periksa(a["pengguna"], sandi_diberikan, data=a):
        return None
    return a.get("peran", "guru")


def tambah_akun(
    pengguna: str, sandi_baru: str, peran: str, path: Path | None = None
) -> Path:
    """Tambah akun baru. Nama ganda ditolak — duplikat nama membuat
    pencarian ambigu dan itu risiko keamanan, bukan sekadar rapi."""
    if peran not in PERAN:
        raise ValueError(f"peran tidak dikenal: {peran}")
    akun = muat_akun(path)
    for a in akun:
        if a["pengguna"].strip().lower() == pengguna.strip().lower():
            raise ValueError(f"nama pengguna sudah dipakai: {pengguna}")
    akun.append({"pengguna": pengguna, "peran": peran, **buat_hash(sandi_baru)})
    p = path or BERKAS_SANDI
    p.write_text(json.dumps({"akun": akun}, indent=2), encoding="utf-8")
    p.chmod(0o600)
    return p


def hapus_akun(pengguna: str, path: Path | None = None) -> bool:
    """Hapus satu akun murid. Mengembalikan True kalau ada yang terhapus.

    Akun GURU tidak bisa dihapus dari sini: menghapus satu-satunya akun guru
    membuat berkas sandi kosong, dan `wajib_sandi()` menilai berkas yang ada
    sebagai "palang aktif" — hasilnya aplikasi menolak semua orang tanpa ada
    cara masuk lagi kecuali lewat SSH.

    Menghapus akun murid TIDAK menghapus data anaknya: jawaban dan diagnosis
    terikat ke tabel `siswa`, bukan ke akun. Anak yang akunnya dihapus tetap
    punya riwayat lengkap, dan akunnya bisa dibuat ulang kapan saja.
    """
    akun = muat_akun(path)
    sisa = [
        a
        for a in akun
        if not (
            a["pengguna"].strip().lower() == pengguna.strip().lower()
            and a.get("peran", "guru") == "murid"
        )
    ]
    if len(sisa) == len(akun):
        return False
    p = path or BERKAS_SANDI
    p.write_text(json.dumps({"akun": sisa}, indent=2), encoding="utf-8")
    p.chmod(0o600)
    return True


def setel_sandi_murid(
    pengguna: str, sandi_baru: str, path: Path | None = None
) -> bool:
    """Setel ulang sandi seorang murid (anak lupa sandinya).

    Guru tidak perlu tahu sandi lama anak — itu justru yang membuat fitur ini
    dipakai, bukan diakali dengan menghapus lalu membuat ulang akun (yang
    membuat guru mengira riwayat anak ikut hilang).
    """
    akun = muat_akun(path)
    ubah = False
    for a in akun:
        if (
            a["pengguna"].strip().lower() == pengguna.strip().lower()
            and a.get("peran", "guru") == "murid"
        ):
            a.update(buat_hash(sandi_baru))
            ubah = True
    if not ubah:
        return False
    p = path or BERKAS_SANDI
    p.write_text(json.dumps({"akun": akun}, indent=2), encoding="utf-8")
    p.chmod(0o600)
    return True
