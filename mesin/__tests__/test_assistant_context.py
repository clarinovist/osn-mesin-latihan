"""Konteks anak/sesi Pendamping harus minimum, eksplisit, dan tetap dimiliki."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import assistant_context  # noqa: E402
import assistant_schema  # noqa: E402
import assistant_store  # noqa: E402
import database  # noqa: E402
import question_views  # noqa: E402

AKUN = "akun_" + "a" * 32


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "latihan.db"
    database.siapkan(path)
    return path


@pytest.fixture()
def privat(tmp_path):
    path = tmp_path / "pendamping.db"
    assistant_schema.siapkan(path)
    return path


def test_migrasi_v1_ke_v2_idempoten_dan_menjaga_chat(tmp_path):
    path = tmp_path / "pendamping-v1.db"
    with sqlite3.connect(path) as koneksi:
        koneksi.executescript("""
        CREATE TABLE chat (
            id TEXT PRIMARY KEY, account_id TEXT NOT NULL,
            mode_memori TEXT NOT NULL, context_kind TEXT, context_id TEXT,
            context_version INTEGER, versi INTEGER NOT NULL DEFAULT 1,
            dibuat INTEGER NOT NULL, diperbarui INTEGER NOT NULL,
            dihapus INTEGER, purge_setelah INTEGER
        );
        CREATE TABLE migrasi_pendamping (
            versi INTEGER PRIMARY KEY, diterapkan TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO migrasi_pendamping(versi) VALUES (1);
        INSERT INTO chat(id, account_id, mode_memori, dibuat, diperbarui)
        VALUES ('chat_lama', 'akun_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'aktif', 1, 1);
        PRAGMA user_version = 1;
        """)
    assistant_schema.siapkan(path)
    assistant_schema.siapkan(path)
    with assistant_schema.buka(path) as koneksi:
        assert koneksi.execute("PRAGMA user_version").fetchone()[0] == 3
        assert koneksi.execute("SELECT COUNT(*) FROM chat").fetchone()[0] == 1
        assert "context_resource_version" in {
            baris["name"] for baris in koneksi.execute("PRAGMA table_info(chat)")
        }
        assert koneksi.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert koneksi.execute("PRAGMA foreign_key_check").fetchall() == []


def test_konteks_soal_minimum_dari_snapshot_yang_sama(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anak Sintetis", "P3", pemilik="ortu")
        sesi = database.buat_sesi(kon, siswa, seed=42)
        sumber = database.isi_sesi(kon, sesi)[0]
        hasil = assistant_context.konteks_soal(kon, sesi, 1, pemilik="ortu")
        penyajian = question_views.penyajian_dari_baris(sumber)
        soal = question_views.soal_dari_baris(sumber)

    assert hasil.resource_id == f"{sesi}:1"
    assert hasil.versi == penyajian.fingerprint_penyajian
    assert hasil.muatan["teks_soal"] == penyajian.teks_soal
    assert hasil.muatan["kunci"] == soal.kunci
    assert hasil.muatan["pembahasan"] == soal.pembahasan
    assert set(hasil.muatan) == {
        "jenis", "nomor", "template_id", "level", "teks_soal",
        "descriptor", "kunci", "pembahasan", "fingerprint_penyajian",
    }
    mentah = json.dumps(hasil.muatan)
    for terlarang in ("Anak Sintetis", "jawaban_anak", "diagnosis", "malrule", "catatan"):
        assert terlarang not in mentah


def test_konteks_soal_asing_dan_hilang_identik(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anak A", pemilik="ortu-a")
        sesi = database.buat_sesi(kon, siswa, seed=42)
        assert assistant_context.konteks_soal(kon, sesi, 1, pemilik="ortu-b") is None
        assert assistant_context.konteks_soal(kon, 999999, 1, pemilik="ortu-b") is None
        assert assistant_context.konteks_sesi(kon, sesi, pemilik="ortu-b") is None
        assert assistant_context.konteks_sesi(kon, 999999, pemilik="ortu-b") is None


def test_snapshot_rusak_tidak_fallback_ke_soal_baru(db, monkeypatch):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anak A", pemilik="ortu")
        sesi = database.buat_sesi(kon, siswa, seed=42)
        kon.execute(
            "UPDATE sesi_soal SET penyajian_json = '{rusak' WHERE sesi_id = ? AND nomor = 1",
            (sesi,),
        )
        monkeypatch.setitem(
            question_views.REGISTRI,
            "deret_aritmetika",
            lambda **_: pytest.fail("snapshot rusak tidak boleh regenerate"),
        )
        with pytest.raises(ValueError, match="snapshot"):
            assistant_context.konteks_soal(kon, sesi, 1, pemilik="ortu")


def test_ringkasan_anak_netral_tanpa_nama_atau_kode(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Nama Tidak Boleh Keluar", "P4", pemilik="ortu")
        hasil = assistant_context.konteks_anak(kon, siswa, pemilik="ortu")
    assert hasil.resource_id == str(siswa)
    assert set(hasil.muatan) == {"jenis", "level", "tahap", "tersedia_pada"}
    mentah = json.dumps(hasil.muatan)
    assert "Nama Tidak Boleh Keluar" not in mentah
    assert not any(kode in hasil.muatan["tahap"] for kode in ("K", "B", "H", "E", "N", "T"))


def test_ikat_konteks_hanya_ke_chat_baru_dan_consent_resource(privat):
    with assistant_schema.buka(privat) as kon:
        consent = assistant_store.beri_persetujuan_konteks(
            kon, AKUN, jenis="soal", resource_id="7:1", resource_version="abc",
            kategori="soal_resmi", sekarang=100,
        )
        chat = assistant_store.buat_chat(
            kon, AKUN, "aktif", sekarang=101,
            context_kind="soal", context_id="7:1", context_version=consent.versi,
            context_resource_version="abc", context_category="soal_resmi",
        )
        assert chat.context_kind == "soal"
        assert chat.context_id == "7:1"
        assert assistant_store.persetujuan_konteks_aktif(
            kon, AKUN, jenis="soal", resource_id="7:1",
            resource_version="abc", kategori="soal_resmi",
        )
        with pytest.raises(ValueError, match="konteks"):
            assistant_store.ubah_konteks_chat(
                kon, AKUN, chat.id, context_kind="anak", context_id="8"
            )


def test_kategori_consent_harus_cocok_jenis_context(privat):
    with assistant_schema.buka(privat) as kon:
        consent = assistant_store.beri_persetujuan_konteks(
            kon, AKUN, jenis="anak", resource_id="1", resource_version="v1",
            kategori="ringkasan_netral", sekarang=100,
        )
        with pytest.raises(ValueError, match="persetujuan konteks"):
            assistant_store.buat_chat(
                kon, AKUN, "aktif", sekarang=101,
                context_kind="anak", context_id="1",
                context_version=consent.versi,
                context_resource_version="v1", context_category="soal_resmi",
            )


def test_cabut_context_membuat_izin_tidak_aktif(privat):
    with assistant_schema.buka(privat) as kon:
        consent = assistant_store.beri_persetujuan_konteks(
            kon, AKUN, jenis="anak", resource_id="1", resource_version="v1",
            kategori="ringkasan_netral", sekarang=100,
        )
        assert assistant_store.cabut_persetujuan_konteks(
            kon, AKUN, consent.id, versi_diharapkan=consent.versi,
            sekarang=101,
        )
        assert not assistant_store.persetujuan_konteks_aktif(
            kon, AKUN, jenis="anak", resource_id="1",
            resource_version="v1", kategori="ringkasan_netral",
        )
        with pytest.raises(ValueError, match="persetujuan konteks"):
            assistant_store.buat_chat(
                kon, AKUN, "aktif", sekarang=102,
                context_kind="anak", context_id="1",
                context_version=consent.versi,
                context_resource_version="v1",
                context_category="ringkasan_netral",
            )


def test_context_asing_tidak_bisa_diikat(privat):
    with assistant_schema.buka(privat) as kon:
        assistant_store.beri_persetujuan_konteks(
            kon, AKUN, jenis="anak", resource_id="1", resource_version="v1",
            kategori="ringkasan_netral", sekarang=100,
        )
        with pytest.raises(ValueError, match="persetujuan konteks"):
            assistant_store.buat_chat(
                kon, "akun_" + "b" * 32, "aktif", sekarang=101,
                context_kind="anak", context_id="1", context_version=1,
                context_resource_version="v1",
                context_category="ringkasan_netral",
            )
