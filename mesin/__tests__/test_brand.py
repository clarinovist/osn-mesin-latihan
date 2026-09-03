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
        database.tambah_siswa(kon, "Putri")
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
