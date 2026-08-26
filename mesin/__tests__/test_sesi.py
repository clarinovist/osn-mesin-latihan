"""Test modul sesi: token acak, TTL, hapus, bersih, rate limit."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sesi  # noqa: E402


def _berkas(tmp_path):
    return tmp_path / "sesi.json"


def test_buat_lalu_ambil(tmp_path):
    p = _berkas(tmp_path)
    t = sesi.buat("guru", "guru", path=p)
    assert sesi.ambil(t, path=p) == ("guru", "guru")
    assert sesi.ambil(t, path=p, sekarang=9999999999) is None or sesi.ambil("salah", path=p) is None


def test_token_acak(tmp_path):
    p = _berkas(tmp_path)
    a = sesi.buat("guru", "guru", path=p)
    b = sesi.buat("guru", "guru", path=p)
    assert a != b


def test_kedaluarsa(tmp_path):
    p = _berkas(tmp_path)
    t = sesi.buat("feby", "murid", path=p, sekarang=1000.0)
    assert sesi.ambil(t, path=p, sekarang=1000.0) == ("feby", "murid")
    assert sesi.ambil(t, path=p, sekarang=1000.0 + sesi.TTL_DETIK - 1) is not None
    assert sesi.ambil(t, path=p, sekarang=1000.0 + sesi.TTL_DETIK + 1) is None


def test_hapus(tmp_path):
    p = _berkas(tmp_path)
    t = sesi.buat("guru", "guru", path=p)
    assert sesi.hapus(t, path=p) is True
    assert sesi.ambil(t, path=p) is None
    assert sesi.hapus(t, path=p) is False


def test_bersihkan(tmp_path):
    p = _berkas(tmp_path)
    t1 = sesi.buat("a", "murid", path=p, sekarang=0.0)
    t2 = sesi.buat("b", "murid", path=p, sekarang=0.0)
    # buat satu yang masih hidup
    _ = sesi.buat("c", "guru", path=p)
    n = sesi.bersihkan(path=p)
    assert n == 2
    assert sesi.ambil(t1, path=p) is None
    assert sesi.ambil(t2, path=p) is None


def test_berkas_hilang_aman(tmp_path):
    p = tmp_path / "tidak-ada.json"
    assert sesi.muat(path=p) == {}
    assert sesi.ambil("apa pun", path=p) is None
    assert sesi.hapus("apa pun", path=p) is False


def test_rate_limit(tmp_path):
    sesi._reset_rate_limit()
    for i in range(5):
        assert not sesi.sedang_diblokir("feby", "1.2.3.4", sekarang=1000.0 + i)
        sesi.catat_gagal("feby", "1.2.3.4", sekarang=1000.0 + i)
    assert sesi.sedang_diblokir("feby", "1.2.3.4", sekarang=1004.0)
    # nama lain tidak ikut
    assert not sesi.sedang_diblokir("guru", "1.2.3.4", sekarang=1004.0)
    # setelah jendela habis, boleh lagi
    assert not sesi.sedang_diblokir("feby", "1.2.3.4", sekarang=2000.0)
    sesi._reset_rate_limit()
