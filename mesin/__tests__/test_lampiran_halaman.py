"""Task 2.5 — halaman sesi guru memuat tombol upload + daftar lampiran."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import web  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    return p


def test_halaman_sesi_memuat_form_upload_lampiran(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakUp")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        html = web.halaman_sesi(kon, sesi_id).decode()
    assert 'action="/lampiran/' in html
    assert 'type="file"' in html
    assert 'name="foto"' in html


def test_halaman_sesi_menampilkan_daftar_lampiran(db):
    """Lampiran yang sudah ada tampil sebagai tautan + statusnya."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakUp2")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg", hasil_json="")
        html = web.halaman_sesi(kon, sesi_id).decode()
    assert 'href="/lampiran/' in html
    assert "lembar-1.jpg" in html
