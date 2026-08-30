"""Migrasi kepemilikan keluarga: kolom siswa.pemilik + UNIQUE(nama, pemilik).

Rebuild tabel siswa pada basis data lama adalah langkah paling berisiko di
fitur multi-keluarga: salin, drop, rename harus mempertahankan seluruh baris,
urutan AUTOINCREMENT, dan rujukan FK dari sesi. Tes di sini mengunci semua itu.
"""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402


def _db_lama(tmp_path, nama="lama.db"):
    """Basis data gaya lama: siswa UNIQUE(nama) global, tanpa kolom pemilik."""
    p = tmp_path / nama
    kon = sqlite3.connect(str(p))
    kon.row_factory = sqlite3.Row
    kon.executescript(
        """
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
            tanggal TEXT NOT NULL DEFAULT (date('now')),
            dibuat TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO siswa (nama, tingkat) VALUES ('Rara', 'P3');
        INSERT INTO siswa (nama, tingkat) VALUES ('Bima', 'P4');
        INSERT INTO sesi (siswa_id, seed) VALUES (1, 777);
        """
    )
    kon.commit()
    kon.close()
    return p


def test_db_lama_dapat_kolom_pemilik(tmp_path):
    p = _db_lama(tmp_path)
    basis.siapkan(p)
    with basis.buka(p) as kon:
        kolom = {r["name"] for r in kon.execute("PRAGMA table_info(siswa)")}
        assert "pemilik" in kolom
        baris = kon.execute(
            "SELECT nama, pemilik FROM siswa ORDER BY id"
        ).fetchall()
        assert [r["nama"] for r in baris] == ["Rara", "Bima"]
        assert all(r["pemilik"] == "" for r in baris)


def test_rebuild_mempertahankan_baris_dan_fk(tmp_path):
    p = _db_lama(tmp_path)
    with basis.buka(p) as kon:
        lama = [
            tuple(r)
            for r in kon.execute(
                "SELECT id, nama, tingkat, dibuat FROM siswa ORDER BY id"
            ).fetchall()
        ]
    basis.siapkan(p)
    with basis.buka(p) as kon:
        baru = [
            tuple(r)
            for r in kon.execute(
                "SELECT id, nama, tingkat, dibuat FROM siswa ORDER BY id"
            ).fetchall()
        ]
        assert baru == lama
        assert kon.execute("PRAGMA foreign_key_check").fetchall() == []
        # FK dari sesi masih menunjuk tabel siswa hasil rebuild
        kon.execute("INSERT INTO sesi (siswa_id, seed) VALUES (2, 888)")
    with basis.buka(p) as kon:
        n = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = 2"
        ).fetchone()["n"]
    assert n == 1


def test_id_baru_tidak_dipakai_ulang_setelah_rebuild(tmp_path):
    p = _db_lama(tmp_path)
    basis.siapkan(p)
    with basis.buka(p) as kon:
        baris = kon.execute(
            "SELECT id FROM siswa WHERE nama = 'Cici'"
        ).fetchone()
    assert baris is None
    with basis.buka(p) as kon:
        baris = kon.execute(
            "SELECT id FROM siswa WHERE nama = 'Bima'"
        ).fetchone()
        id_maks = baris["id"]
        cur = kon.execute(
            "INSERT INTO siswa (nama, pemilik) VALUES ('Cici', 'ortu-x')"
        )
        assert int(cur.lastrowid) > id_maks


def test_dobel_nama_antar_pemilik_sah(tmp_path):
    p = _db_lama(tmp_path)
    basis.siapkan(p)
    with basis.buka(p) as kon:
        kon.execute(
            "INSERT INTO siswa (nama, tingkat, pemilik) VALUES ('Bima', 'P3', 'ortu-a')"
        )
        kon.execute(
            "INSERT INTO siswa (nama, tingkat, pemilik) VALUES ('Bima', 'P3', 'ortu-b')"
        )
        # dua baris baru tersimpan utuh, masing-masing satu per pemilik
        for pemilik in ("ortu-a", "ortu-b"):
            n = kon.execute(
                "SELECT COUNT(*) AS n FROM siswa WHERE nama = 'Bima' AND pemilik = ?",
                (pemilik,),
            ).fetchone()["n"]
            assert n == 1


def test_dobel_nama_dalam_satu_pemilik_ditolak(tmp_path):
    p = _db_lama(tmp_path)
    basis.siapkan(p)
    with basis.buka(p) as kon:
        kon.execute(
            "INSERT INTO siswa (nama, tingkat, pemilik) VALUES ('Bima', 'P3', 'ortu-a')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute(
                "INSERT INTO siswa (nama, tingkat, pemilik) VALUES ('Bima', 'P3', 'ortu-a')"
            )


def test_rebuild_idempoten_dijalankan_berulang(tmp_path):
    p = _db_lama(tmp_path)
    basis.siapkan(p)
    basis.siapkan(p)
    basis.siapkan(p)
    with basis.buka(p) as kon:
        n = kon.execute("SELECT COUNT(*) AS n FROM siswa").fetchone()["n"]
        assert n == 2
        # kendala komposit tetap hidup setelah siapkan berulang
        kon.execute("INSERT INTO siswa (nama, pemilik) VALUES ('Rara', 'ortu-z')")


def test_db_baru_langsung_komposit(tmp_path):
    p = tmp_path / "baru.db"
    basis.siapkan(p)
    with basis.buka(p) as kon:
        kon.execute("INSERT INTO siswa (nama, pemilik) VALUES ('Bima', 'a')")
        kon.execute("INSERT INTO siswa (nama, pemilik) VALUES ('Bima', 'b')")
        assert kon.execute("PRAGMA foreign_key_check").fetchall() == []
