"""Fase 1 Slice 2: snapshot penyajian sesi_soal all-or-none."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
from schema import MIGRASI  # noqa: E402


KOLOM_SNAPSHOT = (
    "teks_soal",
    "bagian_soal",
    "tantangan_soal",
    "minta_restatement",
    "penyajian_json",
    "penyajian_versi",
    "renderer_versi",
    "asal_teks",
    "status_visual",
    "mode_representasi",
    "fingerprint_matematis",
    "fingerprint_penyajian",
)


def _buat_induk(kon: sqlite3.Connection) -> tuple[int, int]:
    siswa_id = kon.execute(
        "INSERT INTO siswa (nama, pemilik) VALUES ('Uji', 'guru')"
    ).lastrowid
    soal_id = kon.execute(
        """INSERT INTO soal
               (tanda_tangan, template_id, parameter, kunci, level)
           VALUES ('tt-uji', 'pola', '{}', '1', 'P3')"""
    ).lastrowid
    sesi_id = kon.execute(
        "INSERT INTO sesi (siswa_id, seed) VALUES (?, 1)", (siswa_id,)
    ).lastrowid
    return sesi_id, soal_id


def _snapshot_lengkap() -> dict[str, object]:
    return {
        "teks_soal": "Berapa hasilnya?",
        "bagian_soal": "A",
        "tantangan_soal": 0,
        "minta_restatement": 1,
        "penyajian_json": '{"versi":1}',
        "penyajian_versi": 1,
        "renderer_versi": 1,
        "asal_teks": "bawaan",
        "status_visual": "tanpa_visual",
        "mode_representasi": "teks-v1",
        "fingerprint_matematis": "a" * 64,
        "fingerprint_penyajian": "b" * 64,
    }


def _sisipkan_snapshot(
    kon: sqlite3.Connection,
    sesi_id: int,
    soal_id: int,
    nomor: int,
    snapshot: dict[str, object],
) -> int:
    kolom = ", ".join(snapshot)
    placeholder = ", ".join("?" for _ in snapshot)
    return kon.execute(
        f"""INSERT INTO sesi_soal (sesi_id, soal_id, nomor, {kolom})
            VALUES (?, ?, ?, {placeholder})""",
        (sesi_id, soal_id, nomor, *snapshot.values()),
    ).lastrowid


def _buat_db_warisan(path: Path) -> None:
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
        CREATE TABLE soal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanda_tangan TEXT NOT NULL UNIQUE,
            template_id TEXT NOT NULL,
            parameter TEXT NOT NULL,
            kunci TEXT NOT NULL,
            bagian TEXT NOT NULL DEFAULT '',
            tantangan INTEGER NOT NULL DEFAULT 0,
            dibuat TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE sesi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL REFERENCES siswa(id) ON DELETE CASCADE,
            seed INTEGER NOT NULL,
            topik TEXT NOT NULL DEFAULT 'pola-bilangan',
            tanggal TEXT NOT NULL DEFAULT (date('now')),
            mulai TEXT,
            selesai TEXT,
            catatan TEXT NOT NULL DEFAULT '',
            dibuat TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE sesi_soal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesi_id INTEGER NOT NULL REFERENCES sesi(id) ON DELETE CASCADE,
            soal_id INTEGER NOT NULL REFERENCES soal(id),
            nomor INTEGER NOT NULL,
            UNIQUE (sesi_id, nomor)
        );
        """
    )
    kon.commit()
    kon.close()


def test_database_baru_memiliki_dua_belas_kolom_snapshot_nullable(tmp_path):
    path = tmp_path / "baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        info = {r["name"]: r for r in kon.execute("PRAGMA table_info(sesi_soal)")}

    assert set(KOLOM_SNAPSHOT) <= set(info)
    assert all(info[nama]["notnull"] == 0 for nama in KOLOM_SNAPSHOT)


def test_database_warisan_dimigrasi_additif_dan_idempoten(tmp_path):
    path = tmp_path / "warisan.db"
    _buat_db_warisan(path)

    with database.buka(path) as kon:
        dijalankan = [
            nama
            for nama in database.migrasi(kon)
            if nama.startswith("sesi_soal.")
        ]
        kedua = database.migrasi(kon)
        kolom = {r["name"] for r in kon.execute("PRAGMA table_info(sesi_soal)")}

    assert dijalankan == [f"sesi_soal.{nama}" for nama in KOLOM_SNAPSHOT]
    assert kedua == []
    assert set(KOLOM_SNAPSHOT) <= kolom


def test_daftar_migrasi_snapshot_tepat_satu_per_kolom():
    pasangan = [(tabel, kolom) for tabel, kolom, _ in MIGRASI]

    for kolom in KOLOM_SNAPSHOT:
        assert pasangan.count(("sesi_soal", kolom)) == 1


def test_database_baru_memiliki_timestamp_pembekuan_penyajian_nullable(tmp_path):
    path = tmp_path / "baru-freeze.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        info = {r["name"]: r for r in kon.execute("PRAGMA table_info(sesi)")}

    assert "penyajian_dibekukan" in info
    assert info["penyajian_dibekukan"]["notnull"] == 0


def test_database_warisan_migrasi_freeze_additif_dan_idempoten(tmp_path):
    path = tmp_path / "warisan-freeze.db"
    _buat_db_warisan(path)

    with database.buka(path) as kon:
        pertama = database.migrasi(kon)
        kedua = database.migrasi(kon)
        info = {r["name"]: r for r in kon.execute("PRAGMA table_info(sesi)")}

    assert pertama.count("sesi.penyajian_dibekukan") == 1
    assert kedua == []
    assert info["penyajian_dibekukan"]["notnull"] == 0
    assert sum(
        1 for tabel, kolom, _ in MIGRASI
        if (tabel, kolom) == ("sesi", "penyajian_dibekukan")
    ) == 1


def test_database_baru_menerima_snapshot_semua_null_dan_lengkap(tmp_path):
    path = tmp_path / "baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        lama = kon.execute(
            "INSERT INTO sesi_soal (sesi_id, soal_id, nomor) VALUES (?, ?, 1)",
            (sesi_id, soal_id),
        ).lastrowid
        lengkap = _sisipkan_snapshot(kon, sesi_id, soal_id, 2, _snapshot_lengkap())

        assert lama
        assert lengkap


def test_database_baru_check_tabel_menolak_parsial_tanpa_bantuan_trigger(tmp_path):
    path = tmp_path / "check-baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        kon.execute("DROP TRIGGER sesi_soal_snapshot_validasi_insert")
        kon.execute("DROP TRIGGER sesi_soal_snapshot_validasi_update")
        sesi_id, soal_id = _buat_induk(kon)
        kon.execute(
            "INSERT INTO sesi_soal (sesi_id, soal_id, nomor) VALUES (?, ?, 1)",
            (sesi_id, soal_id),
        )
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            kon.execute(
                """INSERT INTO sesi_soal
                       (sesi_id, soal_id, nomor, teks_soal)
                   VALUES (?, ?, 2, 'parsial')""",
                (sesi_id, soal_id),
            )


@pytest.mark.parametrize(
    "perubahan",
    [
        {"bagian_soal": None},
        {"tantangan_soal": 2},
        {"minta_restatement": -1},
        {"penyajian_versi": 0},
        {"renderer_versi": 0},
        {"asal_teks": "ai"},
        {"status_visual": "liar"},
        {"mode_representasi": ""},
        {"fingerprint_matematis": ""},
        {"fingerprint_penyajian": ""},
    ],
)
def test_database_baru_menolak_insert_snapshot_tidak_valid(tmp_path, perubahan):
    path = tmp_path / "baru.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        snapshot = _snapshot_lengkap()
        snapshot.update(perubahan)
        with pytest.raises(sqlite3.IntegrityError, match="snapshot penyajian"):
            _sisipkan_snapshot(kon, sesi_id, soal_id, 1, snapshot)


def test_database_warisan_menolak_insert_dan_update_parsial_serta_menerima_null(
    tmp_path,
):
    path = tmp_path / "warisan.db"
    _buat_db_warisan(path)
    database.siapkan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        lama = kon.execute(
            "INSERT INTO sesi_soal (sesi_id, soal_id, nomor) VALUES (?, ?, 1)",
            (sesi_id, soal_id),
        ).lastrowid
        with pytest.raises(sqlite3.IntegrityError, match="snapshot penyajian"):
            kon.execute(
                """INSERT INTO sesi_soal
                       (sesi_id, soal_id, nomor, teks_soal)
                   VALUES (?, ?, 2, 'parsial')""",
                (sesi_id, soal_id),
            )
        with pytest.raises(sqlite3.IntegrityError, match="snapshot penyajian"):
            kon.execute(
                "UPDATE sesi_soal SET teks_soal = 'parsial' WHERE id = ?", (lama,)
            )

        kon.execute(
            "UPDATE sesi_soal SET teks_soal = NULL WHERE id = ?", (lama,)
        )
        assert kon.execute(
            "SELECT teks_soal FROM sesi_soal WHERE id = ?", (lama,)
        ).fetchone()["teks_soal"] is None


TRIGGER_SNAPSHOT = (
    "sesi_soal_snapshot_validasi_insert",
    "sesi_soal_snapshot_validasi_update",
)

KASUS_TIPE_TIDAK_VALID = (
    ("teks_soal", sqlite3.Binary(b"teks")),
    ("bagian_soal", sqlite3.Binary(b"bagian")),
    ("tantangan_soal", "abc"),
    ("tantangan_soal", 0.5),
    ("tantangan_soal", sqlite3.Binary(b"1")),
    ("minta_restatement", "abc"),
    ("minta_restatement", 0.5),
    ("minta_restatement", sqlite3.Binary(b"0")),
    ("penyajian_json", sqlite3.Binary(b"{}")),
    ("penyajian_versi", "abc"),
    ("penyajian_versi", 1.5),
    ("penyajian_versi", "true"),
    ("renderer_versi", "abc"),
    ("renderer_versi", 1.5),
    ("renderer_versi", "false"),
    ("asal_teks", sqlite3.Binary(b"bawaan")),
    ("status_visual", sqlite3.Binary(b"siap")),
    ("mode_representasi", sqlite3.Binary(b"teks-v1")),
    ("fingerprint_matematis", sqlite3.Binary(b"a" * 64)),
    ("fingerprint_penyajian", sqlite3.Binary(b"b" * 64)),
)


def _hapus_trigger_snapshot(kon: sqlite3.Connection) -> None:
    for nama in TRIGGER_SNAPSHOT:
        kon.execute(f"DROP TRIGGER {nama}")


def _pastikan_gagal(
    kon: sqlite3.Connection,
    sesi_id: int,
    soal_id: int,
    snapshot: dict[str, object],
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _sisipkan_snapshot(kon, sesi_id, soal_id, 99, snapshot)


def _pastikan_update_gagal(
    kon: sqlite3.Connection,
    baris_id: int,
    kolom: str,
    nilai: object,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        kon.execute(f"UPDATE sesi_soal SET {kolom} = ? WHERE id = ?", (nilai, baris_id))


def test_check_baru_fail_closed_saat_setiap_field_lengkap_dijadikan_null(tmp_path):
    path = tmp_path / "check-null.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        _hapus_trigger_snapshot(kon)
        sesi_id, soal_id = _buat_induk(kon)
        for kolom in KOLOM_SNAPSHOT:
            snapshot = _snapshot_lengkap()
            snapshot[kolom] = None
            _pastikan_gagal(kon, sesi_id, soal_id, snapshot)


def test_trigger_warisan_fail_closed_saat_setiap_field_lengkap_dijadikan_null(
    tmp_path,
):
    path = tmp_path / "warisan-null.db"
    _buat_db_warisan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        for kolom in KOLOM_SNAPSHOT:
            snapshot = _snapshot_lengkap()
            snapshot[kolom] = None
            _pastikan_gagal(kon, sesi_id, soal_id, snapshot)


@pytest.mark.parametrize("kolom,nilai", KASUS_TIPE_TIDAK_VALID)
def test_check_baru_menolak_tipe_sql_tidak_valid_tanpa_trigger(
    tmp_path, kolom, nilai
):
    path = tmp_path / "check-tipe.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        _hapus_trigger_snapshot(kon)
        sesi_id, soal_id = _buat_induk(kon)
        snapshot = _snapshot_lengkap()
        snapshot[kolom] = nilai
        _pastikan_gagal(kon, sesi_id, soal_id, snapshot)


@pytest.mark.parametrize("kolom,nilai", KASUS_TIPE_TIDAK_VALID)
def test_trigger_warisan_menolak_tipe_sql_tidak_valid(tmp_path, kolom, nilai):
    path = tmp_path / "warisan-tipe.db"
    _buat_db_warisan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        snapshot = _snapshot_lengkap()
        snapshot[kolom] = nilai
        _pastikan_gagal(kon, sesi_id, soal_id, snapshot)


@pytest.mark.parametrize("kolom", KOLOM_SNAPSHOT)
def test_check_baru_menolak_update_snapshot_lengkap_menjadi_null_tanpa_trigger(
    tmp_path, kolom
):
    path = tmp_path / "check-update-null.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        _hapus_trigger_snapshot(kon)
        sesi_id, soal_id = _buat_induk(kon)
        baris_id = _sisipkan_snapshot(
            kon, sesi_id, soal_id, 1, _snapshot_lengkap()
        )
        _pastikan_update_gagal(kon, baris_id, kolom, None)


@pytest.mark.parametrize("kolom", KOLOM_SNAPSHOT)
def test_trigger_warisan_menolak_update_snapshot_lengkap_menjadi_null(
    tmp_path, kolom
):
    path = tmp_path / "warisan-update-null.db"
    _buat_db_warisan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        baris_id = _sisipkan_snapshot(
            kon, sesi_id, soal_id, 1, _snapshot_lengkap()
        )
        _pastikan_update_gagal(kon, baris_id, kolom, None)


@pytest.mark.parametrize("kolom,nilai", KASUS_TIPE_TIDAK_VALID)
def test_check_baru_menolak_update_snapshot_lengkap_dengan_tipe_tidak_valid(
    tmp_path, kolom, nilai
):
    path = tmp_path / "check-update-tipe.db"
    database.siapkan(path)

    with database.buka(path) as kon:
        _hapus_trigger_snapshot(kon)
        sesi_id, soal_id = _buat_induk(kon)
        baris_id = _sisipkan_snapshot(
            kon, sesi_id, soal_id, 1, _snapshot_lengkap()
        )
        _pastikan_update_gagal(kon, baris_id, kolom, nilai)


@pytest.mark.parametrize("kolom,nilai", KASUS_TIPE_TIDAK_VALID)
def test_trigger_warisan_menolak_update_snapshot_lengkap_dengan_tipe_tidak_valid(
    tmp_path, kolom, nilai
):
    path = tmp_path / "warisan-update-tipe.db"
    _buat_db_warisan(path)
    database.siapkan(path)

    with database.buka(path) as kon:
        sesi_id, soal_id = _buat_induk(kon)
        baris_id = _sisipkan_snapshot(
            kon, sesi_id, soal_id, 1, _snapshot_lengkap()
        )
        _pastikan_update_gagal(kon, baris_id, kolom, nilai)
