"""Variasi cerita LLM (B2) — kalimat berubah, kunci tidak."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import llm  # noqa: E402
import web  # noqa: E402
import teacher_pages  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-uji")
    return p


def _palsu(monkeypatch, kalimat_fn):
    """Ganti llm.bungkus supaya tidak ada panggilan API sungguhan."""
    monkeypatch.setattr(llm, "bungkus", lambda kon, soal: kalimat_fn(soal))


def test_cerita_mengganti_kalimat_tanpa_menyentuh_kunci(db, monkeypatch):
    """Inti kontrak B2: parameter & kunci tetap hasil hitungan Python.
    Kalau kunci ikut berubah, seluruh diagnosis jadi salah menilai."""
    _palsu(monkeypatch, lambda s: "Di toko ada " + s.teks.replace(chr(10), " "))
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        ses = database.buat_sesi(kon, sid, seed=42)
        sebelum = {b["nomor"]: b["kunci"] for b in database.isi_sesi(kon, ses)}
        n, dicoba, _ = llm.bungkus_sesi(kon, ses, teacher_pages._soal_dari_baris)
        assert n == dicoba == 12
        sesudah = {b["nomor"]: b["kunci"] for b in database.isi_sesi(kon, ses)}
    assert sebelum == sesudah, "kunci berubah — diagnosis akan menilai salah"


def test_soal_bercerita_tidak_dibayar_dua_kali(db, monkeypatch):
    """Soal yang sudah punya cerita dilewati — kalimatnya sudah dibayar,
    dan anak mungkin sudah mengerjakannya."""
    _palsu(monkeypatch, lambda s: "Cerita: " + s.teks.replace(chr(10), " "))
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        ses = database.buat_sesi(kon, sid, seed=42)
        llm.bungkus_sesi(kon, ses, teacher_pages._soal_dari_baris)
        n2, dicoba2, catatan = llm.bungkus_sesi(kon, ses, teacher_pages._soal_dari_baris)
    assert dicoba2 == 0
    assert "sudah punya" in catatan


def test_fitur_mati_tanpa_kunci_api(db, monkeypatch):
    """Gagal-diam: tanpa kunci, tidak ada panggilan dan tidak ada exception."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        ses = database.buat_sesi(kon, sid, seed=42)
        n, dicoba, catatan = llm.bungkus_sesi(kon, ses, teacher_pages._soal_dari_baris)
    assert n == 0 and dicoba == 0
    assert "tidak aktif" in catatan


def test_tombol_tidak_muncul_kalau_fitur_mati(db, monkeypatch):
    """Fitur yang mati harus terlihat mati — bukan muncul lalu gagal
    saat ditekan."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        ses = database.buat_sesi(kon, sid, seed=42)
        html_sesi = teacher_pages.halaman_sesi(kon, ses).decode()
        html_cetak_raw = teacher_pages.halaman_sesi_cetak(kon, ses)
        html_cetak = html_cetak_raw.decode() if html_cetak_raw else ""
    assert "Variasi cerita" not in html_sesi
    assert "Variasi cerita" not in html_cetak


def test_tombol_muncul_di_cetak_kalau_fitur_hidup(db):
    """Opsi 3: Variasi cerita pindah ke /sesi/{id}/cetak."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        ses = database.buat_sesi(kon, sid, seed=42)
        html_sesi = teacher_pages.halaman_sesi(kon, ses).decode()
        html_cetak_raw = teacher_pages.halaman_sesi_cetak(kon, ses)
        assert html_cetak_raw is not None
        html_cetak = html_cetak_raw.decode()
    assert "Variasi cerita" not in html_sesi
    assert "Variasi cerita" in html_cetak
    assert "0 dari 12" in html_cetak


def test_kalimat_cerita_tampil_di_lembar_anak(db, monkeypatch):
    """Yang dikerjakan anak harus kalimat ceritanya, bukan kalimat bawaan."""
    _palsu(monkeypatch, lambda s: "Kebun Pak Tani: " + s.teks.replace(chr(10), " "))
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        ses = database.buat_sesi(kon, sid, seed=42)
        llm.bungkus_sesi(kon, ses, teacher_pages._soal_dari_baris)
        lembar = teacher_pages.halaman_lembar(kon, ses).decode()
    assert "Kebun Pak Tani" in lembar
