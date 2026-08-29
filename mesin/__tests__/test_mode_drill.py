"""Fase 1 mode drill — kolom mode + timer pada sesi.

Alur yang dijaga:
  - sesi punya mode 'diagnostik' (default) | 'drill' (Latihan Cepat)
  - sesi drill punya timer: timer_mode 'tanpa'|'sesi'|'soal',
    durasi_menit (default 15), timer_auto (0 peringatan, 1 auto-submit)
  - halaman kerja murid drill TANPA blok Caraku, dengan timer JS
  - diagnosis drill tidak pernah menghasilkan kode N (jawaban tanpa cara
    dianggap menebak) — via suntikan cara sintetis SAAT PANGGILAN, storage
    tetap bersih
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import murid  # noqa: E402
import web  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    return p


def _sesi_drill(kon, siswa_id: int, seed: int = 7, **kw) -> int:
    return basis.buat_sesi(kon, siswa_id, seed=seed, mode="drill", **kw)


# ── 1.1 Skema & migrasi ──────────────────────────────────────────────


def test_sesi_baru_default_diagnostik(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Uji")
        sesi_id = basis.buat_sesi(kon, sid, seed=42)
        baris = kon.execute(
            "SELECT mode, timer_mode, durasi_menit, timer_auto FROM sesi WHERE id = ?",
            (sesi_id,),
        ).fetchone()
        assert baris["mode"] == "diagnostik"
        assert baris["timer_mode"] == "tanpa"
        assert baris["durasi_menit"] == 15
        assert baris["timer_auto"] == 0


def test_migrasi_menambah_mode_dan_timer_pada_db_lama(tmp_path):
    p = tmp_path / "lama.db"
    kon = sqlite3.connect(p)
    # Skema sesi LAMA (tanpa mode/timer) — yang hidup di produksi sebelum ini.
    kon.executescript(
        """CREATE TABLE sesi (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        siswa_id  INTEGER NOT NULL,
        seed      INTEGER NOT NULL,
        topik     TEXT    NOT NULL DEFAULT 'pola-bilangan',
        level     TEXT    NOT NULL DEFAULT 'P3',
        tanggal   TEXT    NOT NULL DEFAULT (date('now', '+7 hours')),
        mulai     TEXT,
        selesai   TEXT,
        catatan   TEXT    NOT NULL DEFAULT '',
        dibuat    TEXT    NOT NULL DEFAULT (datetime('now', '+7 hours'))
    );
    INSERT INTO sesi (siswa_id, seed) VALUES (1, 99);"""
    )
    kon.commit()
    kon.close()

    basis.siapkan(p)
    with basis.buka(p) as kon:
        baris = kon.execute(
            "SELECT mode, timer_mode, durasi_menit, timer_auto FROM sesi"
        ).fetchone()
        assert baris is not None
        assert baris["mode"] == "diagnostik"
        assert baris["timer_mode"] == "tanpa"
        assert baris["durasi_menit"] == 15
        assert baris["timer_auto"] == 0


# ── 1.2 buat_sesi / buat_sesi_seed_baru terima mode + timer ──────────


def test_buat_sesi_drill_dengan_timer_tersimpan(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Uji")
        sesi_id = basis.buat_sesi(
            kon, sid, seed=7, mode="drill",
            timer_mode="sesi", durasi_menit=10, timer_auto=1,
        )
        baris = kon.execute(
            "SELECT mode, timer_mode, durasi_menit, timer_auto FROM sesi WHERE id = ?",
            (sesi_id,),
        ).fetchone()
        assert baris["mode"] == "drill"
        assert baris["timer_mode"] == "sesi"
        assert baris["durasi_menit"] == 10
        assert baris["timer_auto"] == 1


def test_buat_sesi_mode_asing_ditolak(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Uji")
        with pytest.raises(ValueError):
            basis.buat_sesi(kon, sid, seed=7, mode="aneh")


def test_buat_sesi_timer_mode_asing_ditolak(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Uji")
        with pytest.raises(ValueError):
            basis.buat_sesi(kon, sid, seed=7, mode="drill", timer_mode="aneh")


def test_buat_sesi_seed_baru_drill_via_web(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Uji")
        sesi_id = web.buat_sesi_seed_baru(
            kon, sid, mode="drill", timer_mode="soal",
            durasi_menit=5, timer_auto=0,
        )
        baris = kon.execute(
            "SELECT mode, timer_mode, durasi_menit, timer_auto FROM sesi WHERE id = ?",
            (sesi_id,),
        ).fetchone()
        assert baris["mode"] == "drill"
        assert baris["timer_mode"] == "soal"
        assert baris["durasi_menit"] == 5
        assert baris["timer_auto"] == 0

