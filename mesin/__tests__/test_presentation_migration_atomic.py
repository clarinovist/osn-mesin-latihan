"""Migrasi startup harus menggulung perubahan skema bila gagal."""
import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import database


@pytest.mark.parametrize('warisan', [False, True])
def test_startup_gagal_tidak_meninggalkan_skema_parsial(tmp_path, monkeypatch, warisan):
    path = tmp_path / 'atomic.db'
    if warisan:
        with sqlite3.connect(str(path)) as kon:
            kon.executescript('CREATE TABLE siswa(id INTEGER PRIMARY KEY, nama TEXT UNIQUE, tingkat TEXT, dibuat TEXT); CREATE TABLE sesi_soal(id INTEGER PRIMARY KEY, sesi_id INTEGER, soal_id INTEGER, nomor INTEGER);')
    with sqlite3.connect(str(path)) as kon:
        sebelum = tuple(kon.iterdump())
    monkeypatch.setattr(database, 'SKEMA', database.SKEMA + '\nPERINTAH SENGAJA SALAH;')
    with pytest.raises(sqlite3.Error):
        database.siapkan(path)
    with sqlite3.connect(str(path)) as kon:
        assert tuple(kon.iterdump()) == sebelum
