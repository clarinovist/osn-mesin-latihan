"""Migrasi metadata sesi remedial untuk database baru dan warisan."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
from schema import MIGRASI  # noqa: E402


def test_database_baru_memiliki_metadata_remedial(tmp_path):
    path = tmp_path / "baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        kolom = {r["name"] for r in kon.execute("PRAGMA table_info(sesi)")}
        foreign_keys = kon.execute("PRAGMA foreign_key_list(sesi)").fetchall()

    assert {"jenis", "sumber_sesi_id"} <= kolom
    assert any(
        fk["from"] == "sumber_sesi_id"
        and fk["table"] == "sesi"
        and fk["on_delete"] == "SET NULL"
        for fk in foreign_keys
    )


def test_database_lama_dimigrasi_idempoten_dan_sesi_lama_biasa(tmp_path):
    path = tmp_path / "lama.db"
    kon = sqlite3.connect(str(path))
    kon.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE siswa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE,
            tingkat TEXT NOT NULL DEFAULT 'P3',
            dibuat TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE sesi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL REFERENCES siswa(id) ON DELETE CASCADE,
            seed INTEGER NOT NULL,
            topik TEXT NOT NULL DEFAULT 'pola bilangan',
            tanggal TEXT NOT NULL DEFAULT (date('now')),
            mulai TEXT,
            selesai TEXT,
            catatan TEXT NOT NULL DEFAULT '',
            dibuat TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO siswa (nama) VALUES ('Lama');
        INSERT INTO sesi (siswa_id, seed) VALUES (1, 12345);
        """
    )
    kon.commit()
    kon.close()

    database.siapkan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        lama = kon.execute(
            "SELECT seed, jenis, sumber_sesi_id FROM sesi WHERE id = 1"
        ).fetchone()
        assert database.migrasi(kon) == []

    assert dict(lama) == {
        "seed": 12345,
        "jenis": "biasa",
        "sumber_sesi_id": None,
    }


def test_daftar_migrasi_metadata_remedial_tidak_duplikat():
    pasangan = [(tabel, kolom) for tabel, kolom, _ in MIGRASI]
    assert pasangan.count(("sesi", "jenis")) == 1
    assert pasangan.count(("sesi", "sumber_sesi_id")) == 1
