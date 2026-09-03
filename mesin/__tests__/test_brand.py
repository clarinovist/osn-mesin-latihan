"""Rute aset brand (/aset/<nama>) + tag kepala favicon/meta.

Palang yang dijaga:
1. Publik — favicon dibutuhkan sebelum login, jadi 200 tanpa kredensial.
2. Allow-list, bukan path gabung: traversal `../` mustahil.
3. MIME benar per ekstensi; cache panjang & immutable.
4. Tidak menyentuh basis data sama sekali.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brand  # noqa: E402
import database  # noqa: E402
import design_tokens as T  # noqa: E402
from http_test_kit import SANDI_GURU, ServerUji  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    with s.buka() as kon:
        # pemilik distempel eksplisit — palang kepemilikan menolak id yang
        # bukan milik guru dengan 404, dan itu bukan yang sedang diuji.
        sid = database.tambah_siswa(kon, "Putri", pemilik="guru")
        s.sesi_id = database.buat_sesi(kon, sid, seed=7)
    yield s
    s.berhenti()


# ───────────────────────── berkas aset ada ─────────────────────────

def test_folder_aset_lengkap():
    """Allow-list dan isi folder harus sinkron: nama yang diizinkan rute
    benar-benar ada sebagai berkas, dan tidak ada berkas liar di luar
    allow-list yang diam-diam ikut ke image."""
    folder = ROOT / "aset"
    assert folder.is_dir(), "mesin/aset/ belum ada"
    di_disk = {p.name for p in folder.iterdir() if p.is_file()}
    assert set(brand.ASET) == di_disk, (
        f"allow-list vs disk beda: hanya-allow={set(brand.ASET) - di_disk}, "
        f"hanya-disk={di_disk - set(brand.ASET)}"
    )


def test_aset_wajib_ada_semua():
    wajib = (
        "mark-sederhana.svg",
        "mark-penuh.svg",
        "mark-tinta.svg",
        "lockup-horizontal.svg",
        "lockup-cetak.svg",
        "lockup-hero.svg",
        "favicon.svg",
        "favicon.ico",
        "apple-touch-180.png",
        "pwa-192.png",
        "pwa-512.png",
        "og-image.png",
    )
    for nama in wajib:
        assert nama in brand.ASET, f"{nama} tidak ada di allow-list"
        assert (ROOT / "aset" / nama).is_file(), f"{nama} tidak ada di disk"


# ───────────────────────── rute publik ─────────────────────────

def test_favicon_publik_tanpa_kredensial(server):
    """Favicon dibutuhkan browser SEBELUM login — kalau kena palang guru,
    tab menampilkan ikon kosong di halaman landing dan masuk."""
    kode, isi, hdr = server.minta("/aset/favicon.ico", biner=True)
    assert kode == 200
    assert isi == (ROOT / "aset" / "favicon.ico").read_bytes()
    assert hdr["Content-Type"] == "image/x-icon"
    assert "immutable" in hdr["Cache-Control"]


def test_semua_aset_terlayani_dan_mime_benar(server):
    harapan = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
        ".json": "application/json",
    }
    for nama in brand.ASET:
        kode, isi, hdr = server.minta(f"/aset/{nama}", biner=True)
        assert kode == 200, f"{nama} -> {kode}"
        ext = Path(nama).suffix
        assert hdr["Content-Type"].startswith(harapan[ext]), f"{nama}: {hdr}"
        assert isi, f"{nama} kosong"


def test_traversal_ditolak(server):
    """Allow-list, bukan path gabung. Semua bentuk traversal -> 404, dan
    yang penting: TIDAK ada isi berkas sistem yang terkirim."""
    jahat = (
        "/aset/../../etc/passwd",
        "/aset/..%2f..%2fetc%2fpasswd",
        "/aset/web.py",
        "/aset/../design_tokens.py",
        "/aset/latihan.db",
        "/aset/",
    )
    for jalur in jahat:
        kode, isi, _ = server.minta(jalur, biner=True)
        assert kode == 404, f"{jalur} -> {kode} (harus 404)"
        assert b"root:" not in isi and b"NAMA_PRODUK" not in isi, (
            f"{jalur} membocorkan isi berkas"
        )


def test_manifest_pwa_dari_tokens(server):
    """manifest.json di-generate, bukan berkas statis: nama & warna harus
    ikut design_tokens supaya brand tidak punya dua sumber kebenaran."""
    kode, isi, hdr = server.minta("/aset/manifest.json")
    assert kode == 200
    assert hdr["Content-Type"].startswith("application/json")
    data = json.loads(isi)
    assert data["name"] == T.NAMA_PRODUK
    assert data["short_name"] == T.NAMA_PRODUK
    assert data["display"] == "standalone"
    assert data["theme_color"] == T.AKSEN_MURID_UTAMA
    src = [i["src"] for i in data["icons"]]
    assert "/aset/pwa-192.png" in src and "/aset/pwa-512.png" in src


def test_aset_tidak_menyentuh_basis_data(server, monkeypatch):
    """Rute publik ini hanya melayani berkas brand. Kalau ia membuka DB,
    permukaan publik tanpa palang jadi bersentuhan dengan data anak."""
    import database as db_mod

    def meledak(*a, **k):
        raise AssertionError("rute /aset tidak boleh membuka basis data")

    monkeypatch.setattr(db_mod, "buka", meledak)
    assert server.minta("/aset/favicon.svg", biner=True)[0] == 200


def test_aset_tetap_publik_untuk_murid_dan_guru(server):
    from http_test_kit import SANDI_MURID

    for kred in (None, ("guru", SANDI_GURU), ("feby", SANDI_MURID)):
        kode, _, _ = server.minta("/aset/mark-sederhana.svg", auth=kred, biner=True)
        assert kode == 200, f"{kred} -> {kode}"


def test_dockerfile_menyalin_folder_aset():
    """COPY *.py adalah wildcard .py saja — berkas non-.py tidak ikut.
    Tanpa baris COPY aset/, favicon 404 di produksi meski hijau di lokal
    (pola insiden 25 Agustus 2026, kali ini untuk berkas biner)."""
    isi = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "aset/" in isi, "Dockerfile tidak menyalin folder aset/"


# ───────────────────────── favicon di SEMUA halaman ─────────────────────────

# Halaman yang dilayani lewat HTTP. Guard ini menutup celah "template baru
# lahir tanpa favicon": sebelumnya tidak SATU pun halaman punya favicon.
JALUR_PUBLIK = ("/", "/masuk", "/daftar", "/kebijakan-privasi", "/lupa-sandi")
JALUR_GURU = ("/akun",)


def _jalur_guru_berdata(sesi_id: int) -> tuple[str, ...]:
    """Halaman guru yang butuh id — sengaja ikut diuji: justru di sinilah
    template baru biasanya lahir (halaman sesi, cetak, laporan)."""
    return (
        f"/sesi/{sesi_id}",
        f"/sesi/{sesi_id}/cetak",
        f"/sesi/{sesi_id}/lampiran",
        f"/laporan/{sesi_id}",
    )


def test_semua_halaman_publik_punya_favicon(server):
    for jalur in JALUR_PUBLIK:
        kode, isi, _ = server.minta(jalur)
        assert kode == 200, f"{jalur} -> {kode}"
        assert 'rel="icon"' in isi, f"{jalur} tanpa favicon"
        assert 'rel="manifest"' in isi, f"{jalur} tanpa manifest"
        assert 'name="theme-color"' in isi, f"{jalur} tanpa theme-color"


def test_semua_halaman_guru_punya_favicon(server):
    for jalur in JALUR_GURU + _jalur_guru_berdata(server.sesi_id):
        kode, isi, _ = server.minta(jalur, auth=("guru", SANDI_GURU))
        assert kode == 200, f"{jalur} -> {kode}"
        assert 'rel="icon"' in isi, f"{jalur} tanpa favicon"


def test_halaman_murid_punya_favicon(server):
    from http_test_kit import SANDI_MURID

    kode, isi, _ = server.minta("/murid", auth=("feby", SANDI_MURID))
    assert kode == 200
    assert 'rel="icon"' in isi, "halaman murid tanpa favicon"


def test_lembar_cetak_punya_favicon_tanpa_og():
    """Kertas A4 tidak di-share ke WhatsApp — og:* di sana hanya sampah."""
    import render
    from generator import buat_lembar

    lembar = buat_lembar(seed=3, jumlah_soal=2)
    for fn in (render.lembar_soal, render.lembar_penilaian):
        halaman = fn(list(lembar.soal), nama="Putri", tanggal="1 Jan")
        assert 'rel="icon"' in halaman, f"{fn.__name__} tanpa favicon"
        assert "og:image" not in halaman, f"{fn.__name__} tidak perlu og:*"


def test_landing_punya_meta_share_absolut(server):
    """Crawler WhatsApp/Facebook menolak path relatif — og:image & og:url
    wajib absolut. Satu konstanta brand.URL_SITUS supaya pindah domain
    nanti = ubah satu baris."""
    kode, isi, _ = server.minta("/")
    assert kode == 200
    assert f'content="{brand.URL_SITUS}/aset/og-image.png"' in isi
    assert f'property="og:url" content="{brand.URL_SITUS}' in isi
    assert 'name="twitter:card" content="summary_large_image"' in isi
    assert f'property="og:title" content="' in isi
    assert brand.URL_SITUS.startswith("https://")


def test_tag_kepala_dipakai_bukan_disalin():
    """Blok favicon harus datang dari brand.tag_kepala(), bukan disalin
    per template — kalau disalin, template ke-15 lahir tanpa favicon dan
    tidak ada yang sadar."""
    for nama in (
        "landing.py",
        "web.py",
        "teacher_pages.py",
        "student_pages.py",
        "attachments.py",
        "render.py",
    ):
        sumber = (ROOT / nama).read_text(encoding="utf-8")
        assert "tag_kepala" in sumber, f"{nama} tidak memakai brand.tag_kepala()"
        assert 'rel="icon"' not in sumber, (
            f"{nama} menyalin blok favicon — pakai brand.tag_kepala()"
        )


MODUL_HALAMAN = (
    "landing.py",
    "web.py",
    "teacher_pages.py",
    "student_pages.py",
    "attachments.py",
    "render.py",
)


def test_setiap_head_memanggil_tag_kepala():
    """Guard STRUKTURAL, bukan lewat HTTP.

    Test lewat HTTP hanya menyentuh halaman yang punya rute aktif — halaman
    legacy dan cabang jarang lolos begitu saja. Terbukti: menghapus satu
    sisipan di student_pages.py (halaman kerja legacy) tidak membuat satu
    pun test HTTP merah. Guard ini menghitung <head> di sumber, jadi
    template mana pun yang lahir tanpa favicon langsung ketahuan.
    """
    kurang: list[str] = []
    for nama in MODUL_HALAMAN:
        sumber = (ROOT / nama).read_text(encoding="utf-8")
        n_head = sumber.count("<head>")
        n_tag = sumber.count("brand.tag_kepala(")
        if n_head != n_tag:
            kurang.append(f"{nama}: {n_head} <head> tapi {n_tag} tag_kepala()")
    assert not kurang, "head tanpa favicon:\n" + "\n".join(kurang)
