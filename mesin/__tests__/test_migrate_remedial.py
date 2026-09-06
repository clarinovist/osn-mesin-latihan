"""Migrasi metadata sesi remedial untuk database baru dan warisan."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
from schema import MIGRASI  # noqa: E402


def test_database_baru_memiliki_metadata_remedial_dan_siklus(tmp_path):
    path = tmp_path / "baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        kolom = {r["name"] for r in kon.execute("PRAGMA table_info(sesi)")}
        foreign_keys = kon.execute("PRAGMA foreign_key_list(sesi)").fetchall()
        tabel = {
            r["name"]
            for r in kon.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {
        "jenis", "sumber_sesi_id", "tujuan", "dikonfirmasi_guru",
        "fingerprint_konfirmasi", "putaran_id", "bagian_checkpoint",
        "dibatalkan",
    } <= kolom
    assert {
        "putaran_fokus", "anggota_fokus", "bukti_fokus",
        "kejadian_belajar", "konfirmasi_hasil", "snapshot_outcome",
    } <= tabel
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
            """SELECT seed, jenis, sumber_sesi_id, tujuan,
                      dikonfirmasi_guru, fingerprint_konfirmasi,
                      putaran_id, bagian_checkpoint, dibatalkan
               FROM sesi WHERE id = 1"""
        ).fetchone()
        assert database.migrasi(kon) == []

    assert dict(lama) == {
        "seed": 12345,
        "jenis": "biasa",
        "sumber_sesi_id": None,
        "tujuan": "bebas",
        "dikonfirmasi_guru": None,
        "fingerprint_konfirmasi": None,
        "putaran_id": None,
        "bagian_checkpoint": None,
        "dibatalkan": None,
    }


def test_validasi_tujuan_dan_checkpoint_berlaku_di_database_baru(tmp_path):
    path = tmp_path / "validasi-baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        siswa_id = database.tambah_siswa(kon, "Baru")
        sesi_id = database.buat_sesi(kon, siswa_id, 1, jumlah_soal=1)
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute("UPDATE sesi SET tujuan = 'liar' WHERE id = ?", (sesi_id,))
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute("UPDATE sesi SET bagian_checkpoint = 3 WHERE id = ?", (sesi_id,))


def test_validasi_tujuan_dan_checkpoint_dimigrasikan_idempoten_ke_skema_warisan(
    tmp_path,
):
    path = tmp_path / "validasi-warisan.db"
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
            topik TEXT NOT NULL DEFAULT 'pola-bilangan',
            level TEXT NOT NULL DEFAULT 'P3',
            mode TEXT NOT NULL DEFAULT 'diagnostik',
            timer_mode TEXT NOT NULL DEFAULT 'tanpa',
            durasi_menit INTEGER NOT NULL DEFAULT 15,
            timer_auto INTEGER NOT NULL DEFAULT 0,
            tanggal TEXT NOT NULL DEFAULT (date('now')),
            mulai TEXT,
            selesai TEXT,
            direview TEXT,
            jenis TEXT NOT NULL DEFAULT 'biasa',
            sumber_sesi_id INTEGER REFERENCES sesi(id) ON DELETE SET NULL,
            tujuan TEXT NOT NULL DEFAULT 'bebas',
            dikonfirmasi_guru TEXT,
            fingerprint_konfirmasi TEXT,
            putaran_id INTEGER,
            bagian_checkpoint INTEGER,
            dibatalkan TEXT,
            catatan TEXT NOT NULL DEFAULT '',
            dibuat TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    kon.commit()
    kon.close()

    database.siapkan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        pemilik = database.tambah_siswa(kon, "Warisan")
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute(
                "INSERT INTO sesi (siswa_id, seed, tujuan) VALUES (?, 1, 'liar')",
                (pemilik,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute(
                """INSERT INTO sesi
                       (siswa_id, seed, tujuan, bagian_checkpoint)
                   VALUES (?, 2, 'checkpoint', 0)""",
                (pemilik,),
            )
        sesi_id = kon.execute(
            """INSERT INTO sesi
                   (siswa_id, seed, tujuan, bagian_checkpoint)
               VALUES (?, 3, 'checkpoint', 1)""",
            (pemilik,),
        ).lastrowid
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute("UPDATE sesi SET tujuan = 'liar' WHERE id = ?", (sesi_id,))
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute(
                "UPDATE sesi SET bagian_checkpoint = 9 WHERE id = ?", (sesi_id,)
            )
        pemicu = kon.execute(
            """SELECT name FROM sqlite_master
               WHERE type = 'trigger'
                 AND name IN (
                     'sesi_validasi_insert', 'sesi_validasi_update',
                     'snapshot_outcome_validasi_insert'
                 )
               ORDER BY name"""
        ).fetchall()

    assert [baris["name"] for baris in pemicu] == [
        "sesi_validasi_insert",
        "sesi_validasi_update",
        "snapshot_outcome_validasi_insert",
    ]


def test_daftar_migrasi_metadata_remedial_dan_siklus_tidak_duplikat():
    pasangan = [(tabel, kolom) for tabel, kolom, _ in MIGRASI]
    for kolom in (
        "jenis", "sumber_sesi_id", "tujuan", "dikonfirmasi_guru",
        "fingerprint_konfirmasi", "putaran_id", "bagian_checkpoint",
        "dibatalkan",
    ):
        assert pasangan.count(("sesi", kolom)) == 1
