"""Skema SQLite privat untuk Pendamping Jagomat.

Basis data ini sengaja terpisah dari data belajar. Migrasi hanya additive,
idempoten, dan selalu mengaktifkan foreign key pada setiap koneksi.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BAWAAN = Path(os.environ.get("PENDAMPING_BERKAS_DB", "/data/pendamping.db"))
VERSI_SKEMA = 1

_DDL = """
CREATE TABLE IF NOT EXISTS migrasi_pendamping (
    versi INTEGER PRIMARY KEY,
    diterapkan TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    mode_memori TEXT NOT NULL CHECK (mode_memori IN ('aktif', 'tanpa_memori')),
    context_kind TEXT,
    context_id TEXT,
    context_version INTEGER,
    versi INTEGER NOT NULL DEFAULT 1 CHECK (versi >= 1),
    dibuat INTEGER NOT NULL,
    diperbarui INTEGER NOT NULL,
    dihapus INTEGER,
    purge_setelah INTEGER,
    CHECK ((dihapus IS NULL AND purge_setelah IS NULL) OR
           (dihapus IS NOT NULL AND purge_setelah IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_chat_pemilik_status
    ON chat(account_id, dihapus, diperbarui);
CREATE INDEX IF NOT EXISTS idx_chat_purge ON chat(purge_setelah);

CREATE TABLE IF NOT EXISTS pesan (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL REFERENCES chat(id) ON DELETE RESTRICT,
    urut INTEGER NOT NULL CHECK (urut >= 1),
    peran TEXT NOT NULL CHECK (peran IN ('pengguna', 'asisten')),
    teks TEXT NOT NULL CHECK (length(teks) BETWEEN 1 AND 8000),
    status TEXT NOT NULL CHECK (status IN ('final', 'gagal')),
    request_id TEXT,
    dibuat INTEGER NOT NULL,
    UNIQUE(chat_id, urut),
    UNIQUE(request_id)
);
CREATE INDEX IF NOT EXISTS idx_pesan_chat ON pesan(chat_id, urut);

CREATE TABLE IF NOT EXISTS preferensi_memori (
    account_id TEXT PRIMARY KEY,
    aktif INTEGER NOT NULL CHECK (aktif IN (0, 1)),
    versi INTEGER NOT NULL DEFAULT 1 CHECK (versi >= 1),
    diperbarui INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS memori (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    lingkup TEXT NOT NULL CHECK (lingkup = 'preferensi_orang_tua'),
    isi TEXT NOT NULL CHECK (length(isi) BETWEEN 1 AND 500),
    versi INTEGER NOT NULL DEFAULT 1 CHECK (versi >= 1),
    sumber_chat_id TEXT REFERENCES chat(id) ON DELETE RESTRICT,
    dikonfirmasi INTEGER NOT NULL CHECK (dikonfirmasi IN (0, 1)),
    dibuat INTEGER NOT NULL,
    dihapus INTEGER
);
CREATE INDEX IF NOT EXISTS idx_memori_pemilik
    ON memori(account_id, dikonfirmasi, dihapus);

CREATE TABLE IF NOT EXISTS persetujuan (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    kategori TEXT NOT NULL,
    diberikan INTEGER NOT NULL,
    dicabut INTEGER,
    versi INTEGER NOT NULL DEFAULT 1 CHECK (versi >= 1)
);
CREATE INDEX IF NOT EXISTS idx_persetujuan_pemilik
    ON persetujuan(account_id, kategori, dicabut);

CREATE TABLE IF NOT EXISTS operasi (
    request_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL REFERENCES chat(id) ON DELETE RESTRICT,
    account_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'selesai', 'gagal')),
    chat_version INTEGER NOT NULL,
    consent_version INTEGER NOT NULL,
    memory_version INTEGER NOT NULL,
    context_version INTEGER NOT NULL,
    dibuat INTEGER NOT NULL,
    selesai INTEGER
);
CREATE INDEX IF NOT EXISTS idx_operasi_pemilik_status
    ON operasi(account_id, status, dibuat);
"""


def buka(path: Path | str | None = None) -> sqlite3.Connection:
    """Buka DB Pendamping dengan FK aktif dan hasil berbentuk Row."""
    tujuan = Path(path) if path is not None else BAWAAN
    kon = sqlite3.connect(tujuan)
    kon.row_factory = sqlite3.Row
    kon.execute("PRAGMA foreign_keys = ON")
    return kon


def siapkan(path: Path | str | None = None) -> None:
    """Buat/naikkan skema secara idempoten dalam satu transaksi."""
    tujuan = Path(path) if path is not None else BAWAAN
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    with buka(tujuan) as kon:
        versi = kon.execute("PRAGMA user_version").fetchone()[0]
        if versi > VERSI_SKEMA:
            raise RuntimeError("skema Pendamping lebih baru dari aplikasi")
        kon.executescript(_DDL)
        kon.execute(
            "INSERT OR IGNORE INTO migrasi_pendamping(versi) VALUES (?)",
            (VERSI_SKEMA,),
        )
        kon.execute(f"PRAGMA user_version = {VERSI_SKEMA}")
    tujuan.chmod(0o600)
