"""Test modul sesi: token acak, TTL, hapus, bersih, rate limit."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sessions  # noqa: E402


def _berkas(tmp_path):
    return tmp_path / "sesi.json"


def test_buat_lalu_ambil(tmp_path):
    p = _berkas(tmp_path)
    t = sessions.buat("guru", "guru", path=p)
    assert sessions.ambil(t, path=p) == ("guru", "guru")
    assert sessions.ambil(t, path=p, sekarang=9999999999) is None or sessions.ambil("salah", path=p) is None


def test_token_acak(tmp_path):
    p = _berkas(tmp_path)
    a = sessions.buat("guru", "guru", path=p)
    b = sessions.buat("guru", "guru", path=p)
    assert a != b


def test_kedaluarsa(tmp_path):
    p = _berkas(tmp_path)
    t = sessions.buat("feby", "murid", path=p, sekarang=1000.0)
    assert sessions.ambil(t, path=p, sekarang=1000.0) == ("feby", "murid")
    assert sessions.ambil(t, path=p, sekarang=1000.0 + sessions.TTL_DETIK - 1) is not None
    assert sessions.ambil(t, path=p, sekarang=1000.0 + sessions.TTL_DETIK + 1) is None


def test_hapus(tmp_path):
    p = _berkas(tmp_path)
    t = sessions.buat("guru", "guru", path=p)
    assert sessions.hapus(t, path=p) is True
    assert sessions.ambil(t, path=p) is None
    assert sessions.hapus(t, path=p) is False


def test_bersihkan(tmp_path):
    p = _berkas(tmp_path)
    t1 = sessions.buat("a", "murid", path=p, sekarang=0.0)
    t2 = sessions.buat("b", "murid", path=p, sekarang=0.0)
    # buat satu yang masih hidup
    _ = sessions.buat("c", "guru", path=p)
    n = sessions.bersihkan(path=p)
    assert n == 2
    assert sessions.ambil(t1, path=p) is None
    assert sessions.ambil(t2, path=p) is None


def test_berkas_hilang_aman(tmp_path):
    p = tmp_path / "tidak-ada.json"
    assert sessions.muat(path=p) == {}
    assert sessions.ambil("apa pun", path=p) is None
    assert sessions.hapus("apa pun", path=p) is False


def test_rate_limit(tmp_path):
    sessions._reset_rate_limit()
    for i in range(5):
        assert not sessions.sedang_diblokir("feby", "1.2.3.4", sekarang=1000.0 + i)
        sessions.catat_gagal("feby", "1.2.3.4", sekarang=1000.0 + i)
    assert sessions.sedang_diblokir("feby", "1.2.3.4", sekarang=1004.0)
    # nama lain tidak ikut
    assert not sessions.sedang_diblokir("guru", "1.2.3.4", sekarang=1004.0)
    # setelah jendela habis, boleh lagi
    assert not sessions.sedang_diblokir("feby", "1.2.3.4", sekarang=2000.0)
    sessions._reset_rate_limit()
