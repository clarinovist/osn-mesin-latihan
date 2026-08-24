"""Verifikasi palang sandi — penjaga data anak.

Yang diuji bukan "apakah sandi benar diterima" saja, tapi terutama apakah
yang SALAH benar-benar ditolak, dan apakah tidak ada jalur yang lolos tanpa
sandi. Palang yang bocor di satu rute membuat seluruh sisanya sia-sia.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sandi  # noqa: E402


@pytest.fixture()
def berkas(tmp_path, monkeypatch):
    p = tmp_path / "sandi.json"
    monkeypatch.setattr(sandi, "BERKAS_SANDI", p)
    return p


def test_sandi_benar_diterima(berkas):
    sandi.simpan_sandi("rahasia-kuat-123", "guru", berkas)
    assert sandi.periksa("guru", "rahasia-kuat-123", sandi.muat_sandi(berkas))


def test_sandi_salah_ditolak(berkas):
    sandi.simpan_sandi("rahasia-kuat-123", "guru", berkas)
    d = sandi.muat_sandi(berkas)
    assert not sandi.periksa("guru", "rahasia-kuat-124", d)
    assert not sandi.periksa("guru", "", d)
    assert not sandi.periksa("guru", "rahasia-kuat-1234", d)


def test_nama_pengguna_salah_ditolak(berkas):
    sandi.simpan_sandi("rahasia", "guru", berkas)
    d = sandi.muat_sandi(berkas)
    assert not sandi.periksa("admin", "rahasia", d)
    assert not sandi.periksa("", "rahasia", d)


def test_sandi_tidak_disimpan_sebagai_teks(berkas):
    """Kalau berkasnya terbaca orang, sandinya tidak boleh langsung terpakai."""
    sandi.simpan_sandi("sandi-sangat-rahasia", "guru", berkas)
    isi = berkas.read_text()
    assert "sandi-sangat-rahasia" not in isi
    assert "kunci" in isi and "garam" in isi


def test_berkas_sandi_hanya_bisa_dibaca_pemilik(berkas):
    """Di VPS bersama, berkas world-readable sama saja dengan tanpa sandi."""
    sandi.simpan_sandi("x", "guru", berkas)
    assert oct(berkas.stat().st_mode)[-3:] == "600"


def test_garam_berbeda_tiap_kali(berkas):
    """Dua orang dengan sandi sama tidak boleh punya hash sama."""
    a = sandi.buat_hash("sandi-sama")
    b = sandi.buat_hash("sandi-sama")
    assert a["garam"] != b["garam"]
    assert a["kunci"] != b["kunci"]


def test_tanpa_berkas_sandi_palang_tidak_aktif(berkas):
    """Mode lokal: tanpa berkas sandi, tidak ada palang — dan itu disengaja
    supaya pemakaian di localhost tidak terhambat."""
    assert not sandi.wajib_sandi()
    assert not sandi.periksa("guru", "apa saja", None)


def test_berkas_rusak_tidak_membuka_palang(berkas):
    """Berkas rusak harus GAGAL TERTUTUP, bukan gagal terbuka."""
    berkas.write_text("{ini bukan json")
    assert sandi.muat_sandi(berkas) is None
    assert not sandi.periksa("guru", "apa pun", sandi.muat_sandi(berkas))


def test_hash_rusak_tidak_membuka_palang(berkas):
    berkas.write_text('{"pengguna":"guru","garam":"bukanhex","kunci":"zz"}')
    assert not sandi.periksa("guru", "apa pun", sandi.muat_sandi(berkas))


# ── Penguraian header ───────────────────────────────────────────────────


def test_header_basic_diuraikan():
    sandi_b64 = base64.b64encode(b"guru:rahasia").decode()
    assert sandi.dari_header(f"Basic {sandi_b64}") == ("guru", "rahasia")


def test_header_tidak_sah_ditolak():
    for h in (None, "", "Bearer abc", "Basic ???", "Basic " + base64.b64encode(b"tanpatitikdua").decode()):
        assert sandi.dari_header(h) is None


def test_sandi_boleh_mengandung_titik_dua():
    """Hanya titik dua PERTAMA yang memisahkan; sisanya bagian dari sandi."""
    b = base64.b64encode(b"guru:sandi:dengan:titik").decode()
    assert sandi.dari_header(f"Basic {b}") == ("guru", "sandi:dengan:titik")
