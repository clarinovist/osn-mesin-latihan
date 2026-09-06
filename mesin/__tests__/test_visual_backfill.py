"""Fase 1 Slice 6: backfill snapshot penyajian eksplisit dan aman."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backfill_presentations  # noqa: E402
import database  # noqa: E402
import question_views  # noqa: E402
import schema  # noqa: E402
from templates import REGISTRI  # noqa: E402


KOLOM_SNAPSHOT = question_views.KOLOM_SNAPSHOT


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "backfill.db"
    database.siapkan(path)
    return path


def _buat_sesi(kon, *, seed=42, jumlah=2):
    """Buat sesi lalu kosongkan snapshot untuk mensimulasikan baris warisan."""
    siswa_id = database.tambah_siswa(kon, f"Uji-{seed}", "P3")
    sesi_id = database.buat_sesi(
        kon, siswa_id, seed=seed, level="P3", jumlah_soal=jumlah
    )
    penugasan = ", ".join(f"{nama} = NULL" for nama in KOLOM_SNAPSHOT)
    kon.execute(f"UPDATE sesi_soal SET {penugasan} WHERE sesi_id = ?", (sesi_id,))
    return sesi_id


def _ambil(kon):
    return kon.execute(
        """SELECT ss.*, s.template_id, s.parameter, s.level, s.cerita,
                  s.bagian, s.tantangan
           FROM sesi_soal ss JOIN soal s ON s.id = ss.soal_id
           ORDER BY ss.id"""
    ).fetchall()


def _jumlah_keadaan(kon):
    baris = _ambil(kon)
    lengkap = sum(all(b[n] is not None for n in KOLOM_SNAPSHOT) for b in baris)
    kosong = sum(all(b[n] is None for n in KOLOM_SNAPSHOT) for b in baris)
    return len(baris), lengkap, kosong


def test_backfill_membekukan_teks_terlihat_dan_metadata_rekonstruksi(db):
    with database.buka(db) as kon:
        sesi_id = _buat_sesi(kon)
        awal = database.isi_sesi(kon, sesi_id)
        kon.execute(
            "UPDATE soal SET cerita = ? WHERE id = ?",
            ("Cerita warisan yang sudah dilihat anak", awal[0]["soal_id"]),
        )
        sebelum = [question_views.penyajian_dari_baris(b) for b in database.isi_sesi(kon, sesi_id)]

        laporan = backfill_presentations.jalankan(kon, ukuran_batch=1)
        sesudah = database.isi_sesi(kon, sesi_id)

    assert laporan.total_diperiksa == 2
    assert laporan.total_diubah == 2
    assert laporan.jumlah_batch == 2
    assert laporan.selesai is True
    assert sesudah[0]["teks_soal"] == "Cerita warisan yang sudah dilihat anak"
    for lama, baru in zip(sebelum, sesudah):
        assert baru["teks_soal"] == lama.teks_soal
        assert baru["bagian_soal"] == lama.bagian_soal
        assert bool(baru["tantangan_soal"]) is lama.tantangan_soal
        assert bool(baru["minta_restatement"]) is lama.minta_restatement
        assert baru["asal_teks"] == "warisan"
        assert baru["status_visual"] == "warisan"
        assert baru["mode_representasi"] == "teks-v1"
        snapshot = question_views.penyajian_dari_baris(baru)
        assert snapshot.fingerprint_penyajian == baru["fingerprint_penyajian"]


def test_rerun_idempoten_nol_perubahan(db):
    with database.buka(db) as kon:
        _buat_sesi(kon)
        pertama = backfill_presentations.jalankan(kon, ukuran_batch=10)
        sidik_awal = [b["fingerprint_penyajian"] for b in _ambil(kon)]
        kedua = backfill_presentations.jalankan(kon, ukuran_batch=10)
        sidik_akhir = [b["fingerprint_penyajian"] for b in _ambil(kon)]

    assert pertama.total_diubah == 2
    assert kedua.total_diubah == 0
    assert kedua.total_diperiksa == 2
    assert sidik_akhir == sidik_awal


def test_satu_batch_berbatas_dan_bisa_dilanjutkan_dengan_watermark(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=3)
        pertama = backfill_presentations.jalankan_satu_batch(
            kon, ukuran_batch=2, watermark=0
        )
        assert _jumlah_keadaan(kon) == (3, 2, 1)

        kedua = backfill_presentations.jalankan_satu_batch(
            kon, ukuran_batch=2, watermark=pertama.watermark
        )
        assert _jumlah_keadaan(kon) == (3, 3, 0)

    assert pertama.diperiksa == 2
    assert pertama.diubah == 2
    assert pertama.selesai is False
    assert kedua.diperiksa == 1
    assert kedua.diubah == 1
    assert kedua.selesai is True
    assert kedua.watermark > pertama.watermark


def test_batch_gagal_tergulung_utuh_dan_resume_dari_watermark_aman(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, seed=70, jumlah=3)
        baris = _ambil(kon)
        kon.execute(
            "UPDATE soal SET template_id = 'template-tidak-ada' WHERE id = ?",
            (baris[2]["soal_id"],),
        )
        pertama = backfill_presentations.jalankan_satu_batch(
            kon, ukuran_batch=2, watermark=0
        )

        with pytest.raises(backfill_presentations.BackfillGagal) as galat:
            backfill_presentations.jalankan_satu_batch(
                kon, ukuran_batch=2, watermark=pertama.watermark
            )
        assert galat.value.watermark == pertama.watermark
        assert _jumlah_keadaan(kon) == (3, 2, 1)

        template_id = REGISTRI[baris[2]["template_id"]](
            **json.loads(baris[2]["parameter"])
        ).template_id
        kon.execute(
            "UPDATE soal SET template_id = ? WHERE id = ?",
            (template_id, baris[2]["soal_id"]),
        )
        lanjut = backfill_presentations.jalankan_satu_batch(
            kon, ukuran_batch=2, watermark=galat.value.watermark
        )

    assert lanjut.diubah == 1
    assert lanjut.selesai is True


def test_snapshot_parsial_ditolak_tanpa_mengubah_baris_batch(monkeypatch):
    # Database hasil ALTER TABLE lama tidak memiliki CHECK pada definisi tabel;
    # migrator tetap wajib mendeteksi kerusakan yang sudah telanjur ada.
    kon = sqlite3.connect(":memory:")
    kon.row_factory = sqlite3.Row
    kon.executescript(
        """
        CREATE TABLE soal (
            id INTEGER PRIMARY KEY,
            template_id TEXT NOT NULL,
            parameter TEXT NOT NULL,
            level TEXT NOT NULL,
            cerita TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE sesi_soal (
            id INTEGER PRIMARY KEY,
            soal_id INTEGER NOT NULL,
            teks_soal TEXT, bagian_soal TEXT, tantangan_soal INTEGER,
            minta_restatement INTEGER, penyajian_json TEXT,
            penyajian_versi INTEGER, renderer_versi INTEGER, asal_teks TEXT,
            status_visual TEXT, mode_representasi TEXT,
            fingerprint_matematis TEXT, fingerprint_penyajian TEXT
        );
        """
    )
    kon.executescript(
        schema.SKEMA.split(
            "CREATE TRIGGER IF NOT EXISTS sesi_soal_snapshot_tolak_update_terkunci",
            1,
        )[1].split("END;", 1)[0].join((
            "CREATE TRIGGER IF NOT EXISTS sesi_soal_snapshot_tolak_update_terkunci",
            "END;",
        ))
    )
    parameter = json.dumps(
        {"awal": 12, "beda": 3, "n_minta": 2, "n_tampil": 4}
    )
    kon.executemany(
        "INSERT INTO soal (id, template_id, parameter, level) VALUES (?, ?, ?, 'P3')",
        [(1, "deret_aritmetika", parameter), (2, "deret_aritmetika", parameter)],
    )
    kon.executemany(
        "INSERT INTO sesi_soal (id, soal_id, teks_soal) VALUES (?, ?, ?)",
        [(1, 1, None), (2, 2, "parsial")],
    )
    try:
        with pytest.raises(backfill_presentations.BackfillGagal, match="parsial"):
            backfill_presentations.jalankan_satu_batch(
                kon, ukuran_batch=2, watermark=0
            )

        assert kon.execute(
            "SELECT teks_soal FROM sesi_soal WHERE id = 1"
        ).fetchone()[0] is None
    finally:
        kon.close()


@pytest.mark.parametrize(
    "parameter",
    ["{rusak", "[]"],
)
def test_parameter_tidak_valid_menghentikan_batch(db, parameter):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=1)
        soal_id = _ambil(kon)[0]["soal_id"]
        kon.execute("UPDATE soal SET parameter = ? WHERE id = ?", (parameter, soal_id))

        with pytest.raises(backfill_presentations.BackfillGagal, match="parameter"):
            backfill_presentations.jalankan_satu_batch(
                kon, ukuran_batch=10, watermark=0
            )

        assert _jumlah_keadaan(kon) == (1, 0, 1)


def test_baris_lengkap_tetap_menolak_template_asing_dan_parameter_invalid(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=2)
        backfill_presentations.jalankan(kon)
        baris = _ambil(kon)
        kon.execute(
            "UPDATE soal SET template_id = 'template-tidak-ada' WHERE id = ?",
            (baris[0]["soal_id"],),
        )
        kon.execute(
            "UPDATE soal SET parameter = '[]' WHERE id = ?",
            (baris[1]["soal_id"],),
        )

        with pytest.raises(backfill_presentations.BackfillGagal, match="template"):
            backfill_presentations.jalankan_satu_batch(
                kon, ukuran_batch=1, watermark=0
            )
        with pytest.raises(backfill_presentations.BackfillGagal, match="parameter"):
            backfill_presentations.jalankan_satu_batch(
                kon, ukuran_batch=1, watermark=baris[0]["id"]
            )


def test_backfill_mengisi_sesi_lama_yang_sudah_terkunci(db):
    with database.buka(db) as kon:
        sesi_id = _buat_sesi(kon, jumlah=1)
        kon.execute("UPDATE sesi SET mulai = '2026-01-01 10:00:00' WHERE id = ?", (sesi_id,))

        laporan = backfill_presentations.jalankan(kon, ukuran_batch=10)

        assert laporan.total_diubah == 1
        assert _jumlah_keadaan(kon) == (1, 1, 0)
        with pytest.raises(sqlite3.IntegrityError, match="terkunci"):
            kon.execute(
                "UPDATE sesi_soal SET teks_soal = 'ubah' WHERE sesi_id = ?",
                (sesi_id,),
            )


def test_verifier_final_memeriksa_snapshot_fingerprint_dan_integritas(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=3)
        backfill_presentations.jalankan(kon, ukuran_batch=2)

        hasil = backfill_presentations.verifikasi(kon)

    assert hasil.total_baris == 3
    assert hasil.baris_lengkap == 3
    assert hasil.baris_parsial == 0
    assert hasil.baris_warisan == 0
    assert hasil.fingerprint_terverifikasi == 3
    assert hasil.integrity_check == "ok"
    assert hasil.foreign_key_errors == 0


def test_verifier_final_menolak_warisan_parsial_dan_fingerprint_rusak(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=1)
        with pytest.raises(backfill_presentations.VerifikasiGagal, match="warisan"):
            backfill_presentations.verifikasi(kon)

        backfill_presentations.jalankan(kon)
        pemicu = kon.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
            ("sesi_soal_snapshot_validasi_update",),
        ).fetchone()[0]
        trigger_lock = kon.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
            ("sesi_soal_snapshot_tolak_update_terkunci",),
        ).fetchone()[0]
        kon.execute("DROP TRIGGER sesi_soal_snapshot_validasi_update")
        kon.execute("DROP TRIGGER sesi_soal_snapshot_tolak_update_terkunci")
        kon.execute("UPDATE sesi_soal SET fingerprint_penyajian = ?", ("0" * 64,))
        kon.execute(pemicu)
        kon.execute(trigger_lock)

        with pytest.raises(backfill_presentations.VerifikasiGagal, match="fingerprint"):
            backfill_presentations.verifikasi(kon)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ukuran_batch": 0, "watermark": 0},
        {"ukuran_batch": True, "watermark": 0},
        {"ukuran_batch": 10, "watermark": -1},
        {"ukuran_batch": 10, "watermark": True},
    ],
)
def test_parameter_fungsi_tidak_valid_ditolak(db, kwargs):
    with database.buka(db) as kon:
        with pytest.raises(ValueError):
            backfill_presentations.jalankan_satu_batch(kon, **kwargs)


def test_backfill_gagal_tertutup_bila_trigger_lock_hilang_atau_berubah(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=1)
        kon.execute("DROP TRIGGER sesi_soal_snapshot_tolak_update_terkunci")
        with pytest.raises(backfill_presentations.BackfillGagal, match="trigger"):
            backfill_presentations.jalankan_satu_batch(kon)

    database.siapkan(db)
    with database.buka(db) as kon:
        _buat_sesi(kon, seed=43, jumlah=1)
        kon.execute("DROP TRIGGER sesi_soal_snapshot_tolak_update_terkunci")
        kon.execute(
            """CREATE TRIGGER sesi_soal_snapshot_tolak_update_terkunci
               BEFORE UPDATE OF teks_soal ON sesi_soal BEGIN SELECT 1; END"""
        )
        with pytest.raises(backfill_presentations.BackfillGagal, match="trigger"):
            backfill_presentations.jalankan_satu_batch(kon)


def test_backfill_tidak_commit_transaksi_milik_pemanggil(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=1)
        kon.execute("SAVEPOINT transaksi_luar")
        backfill_presentations.jalankan(kon)
        kon.execute("ROLLBACK TO SAVEPOINT transaksi_luar")
        kon.execute("RELEASE SAVEPOINT transaksi_luar")
        assert _jumlah_keadaan(kon) == (1, 0, 1)


def test_watermark_tidak_boleh_melewati_baris_warisan(db):
    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=2)
        with pytest.raises(backfill_presentations.BackfillGagal, match="watermark"):
            backfill_presentations.jalankan_satu_batch(kon, watermark=999_999)


def test_orphan_sesi_soal_gagal_bukan_loop(tmp_path):
    path = tmp_path / "orphan.db"
    database.siapkan(path)
    kon = sqlite3.connect(str(path))
    kon.row_factory = sqlite3.Row
    kon.execute("PRAGMA foreign_keys = OFF")
    kon.execute("INSERT INTO sesi_soal (sesi_id, soal_id, nomor) VALUES (999, 999, 1)")
    kon.commit()
    try:
        with pytest.raises(backfill_presentations.BackfillGagal, match="sumber"):
            backfill_presentations.jalankan_satu_batch(kon)
    finally:
        kon.close()


def test_cli_memerlukan_path_eksplisit_dan_melaporkan_agregat_json(db):
    skrip = Path(backfill_presentations.__file__)
    tanpa_path = subprocess.run(
        [sys.executable, str(skrip)], capture_output=True, text=True
    )
    assert tanpa_path.returncode != 0

    with database.buka(db) as kon:
        _buat_sesi(kon, jumlah=1)

    proses = subprocess.run(
        [sys.executable, str(skrip), "--database", str(db), "--batch-size", "1"],
        capture_output=True,
        text=True,
    )
    assert proses.returncode == 0, proses.stderr
    muatan = json.loads(proses.stdout)
    assert muatan["backfill"]["total_diubah"] == 1
    assert muatan["verifikasi"]["baris_lengkap"] == 1
    assert "nama" not in proses.stdout.lower()
    assert "cerita" not in proses.stdout.lower()
