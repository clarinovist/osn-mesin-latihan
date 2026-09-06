"""Fase 1 Slice 5: snapshot hanya dapat diubah sebelum ada bukti sesi."""

from __future__ import annotations

import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import presentation_lock  # noqa: E402
from visual_contract import (  # noqa: E402
    PenyajianPertanyaan,
    buat_penyajian,
    serialisasi_penyajian,
)


KOLOM_SNAPSHOT = (
    "teks_soal", "bagian_soal", "tantangan_soal", "minta_restatement",
    "penyajian_json", "penyajian_versi", "renderer_versi", "asal_teks",
    "status_visual", "mode_representasi", "fingerprint_matematis",
    "fingerprint_penyajian",
)


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "visual-lock.db"
    database.siapkan(path)
    return path


def _penyajian(teks: str) -> PenyajianPertanyaan:
    return buat_penyajian(
        template_id="uji-kunci-visual",
        level="P3",
        parameter={"nilai": 7},
        teks_soal=teks,
        bagian_soal="A",
        tantangan_soal=False,
        minta_restatement=True,
        asal_teks="bawaan",
        status_visual="tanpa_visual",
        mode_representasi="teks-v1",
    )


def _nilai_snapshot(penyajian: PenyajianPertanyaan) -> tuple[object, ...]:
    return (
        penyajian.teks_soal,
        penyajian.bagian_soal,
        int(penyajian.tantangan_soal),
        int(penyajian.minta_restatement),
        serialisasi_penyajian(penyajian),
        penyajian.penyajian_versi,
        penyajian.renderer_versi,
        penyajian.asal_teks,
        penyajian.status_visual,
        penyajian.mode_representasi,
        penyajian.fingerprint_matematis,
        penyajian.fingerprint_penyajian,
    )


def _buat_butir(kon: sqlite3.Connection) -> tuple[int, int, int, PenyajianPertanyaan]:
    siswa_id = int(kon.execute(
        "INSERT INTO siswa (nama, pemilik) VALUES ('Uji Lock', 'guru')"
    ).lastrowid)
    soal_id = int(kon.execute(
        """INSERT INTO soal
               (tanda_tangan, template_id, parameter, kunci, level)
           VALUES ('tt-lock', 'uji-kunci-visual', '{"nilai":7}', '7', 'P3')"""
    ).lastrowid)
    sesi_id = int(kon.execute(
        "INSERT INTO sesi (siswa_id, seed, level) VALUES (?, 1, 'P3')",
        (siswa_id,),
    ).lastrowid)
    awal = _penyajian("Teks awal")
    kolom = ", ".join(KOLOM_SNAPSHOT)
    placeholder = ", ".join("?" for _ in KOLOM_SNAPSHOT)
    sesi_soal_id = int(kon.execute(
        f"""INSERT INTO sesi_soal (sesi_id, soal_id, nomor, {kolom})
            VALUES (?, ?, 1, {placeholder})""",
        (sesi_id, soal_id, *_nilai_snapshot(awal)),
    ).lastrowid)
    return siswa_id, sesi_id, sesi_soal_id, awal


@pytest.mark.parametrize("keadaan", ["dibatalkan", "jawaban_lain"])
def test_seluruh_sesi_terkunci_setelah_batal_atau_ada_jawaban(db, keadaan):
    with database.buka(db) as kon:
        _, sesi, ssid, awal = _buat_butir(kon)
        if keadaan == "dibatalkan":
            database.batalkan_sesi(kon, sesi)
        else:
            lain = kon.execute(
                "INSERT INTO sesi_soal (sesi_id, soal_id, nomor) "
                "SELECT sesi_id, soal_id, 2 FROM sesi_soal WHERE id = ?", (ssid,)
            ).lastrowid
            kon.execute("INSERT INTO jawaban (sesi_soal_id, jawaban) VALUES (?, '1')", (lain,))
        assert presentation_lock.perbarui_snapshot(
            kon, ssid, awal.fingerprint_penyajian, _penyajian("Perubahan terlarang")
        ) is False
        with pytest.raises(sqlite3.IntegrityError, match="terkunci"):
            kon.execute("UPDATE sesi_soal SET teks_soal = 'terlarang' WHERE id = ?", (ssid,))
        assert _fingerprint(kon, ssid) == awal.fingerprint_penyajian


@pytest.mark.parametrize("kolom", ["soal_id", "nomor"])
def test_identitas_butir_terkunci_tidak_bisa_diubah(db, kolom):
    with database.buka(db) as kon:
        _, sesi, ssid, awal = _buat_butir(kon)
        presentation_lock.bekukan_penyajian(kon, sesi)
        with pytest.raises(sqlite3.IntegrityError, match="terkunci"):
            kon.execute(f"UPDATE sesi_soal SET {kolom} = {kolom} WHERE id = ?", (ssid,))
        assert _fingerprint(kon, ssid) == awal.fingerprint_penyajian


def _fingerprint(kon: sqlite3.Connection, sesi_soal_id: int) -> str:
    return str(kon.execute(
        "SELECT fingerprint_penyajian FROM sesi_soal WHERE id = ?",
        (sesi_soal_id,),
    ).fetchone()[0])


def _raw_update(
    kon: sqlite3.Connection,
    sesi_soal_id: int,
    penyajian: PenyajianPertanyaan,
) -> None:
    penugasan = ", ".join(f"{nama} = ?" for nama in KOLOM_SNAPSHOT)
    kon.execute(
        f"UPDATE sesi_soal SET {penugasan} WHERE id = ?",
        (*_nilai_snapshot(penyajian), sesi_soal_id),
    )


def _kunci_mulai(kon, _siswa_id, sesi_id, _sesi_soal_id):
    kon.execute("UPDATE sesi SET mulai = '2026-09-06 10:00:00' WHERE id = ?", (sesi_id,))


def _kunci_selesai(kon, _siswa_id, sesi_id, _sesi_soal_id):
    kon.execute("UPDATE sesi SET selesai = '2026-09-06 10:30:00' WHERE id = ?", (sesi_id,))


def _kunci_dicetak(kon, _siswa_id, sesi_id, _sesi_soal_id):
    kon.execute(
        "UPDATE sesi SET penyajian_dibekukan = '2026-09-06 09:00:00' WHERE id = ?",
        (sesi_id,),
    )


def _kunci_jawaban(kon, _siswa_id, _sesi_id, sesi_soal_id):
    kon.execute("INSERT INTO jawaban (sesi_soal_id) VALUES (?)", (sesi_soal_id,))


def _kunci_konfirmasi(kon, _siswa_id, sesi_id, _sesi_soal_id):
    kon.execute(
        """INSERT INTO konfirmasi_hasil (sesi_id, nomor_urut, guru, fingerprint)
           VALUES (?, 1, 'guru', 'fingerprint-uji')""",
        (sesi_id,),
    )


def _kunci_bukti_fokus(kon, siswa_id, sesi_id, _sesi_soal_id):
    putaran_id = int(kon.execute(
        "INSERT INTO putaran_fokus (siswa_id, level) VALUES (?, 'P3')",
        (siswa_id,),
    ).lastrowid)
    anggota_id = int(kon.execute(
        """INSERT INTO anggota_fokus
               (putaran_id, slot, template_id, kode_intervensi)
           VALUES (?, 1, 'uji-kunci-visual', 'K')""",
        (putaran_id,),
    ).lastrowid)
    kon.execute(
        "INSERT INTO bukti_fokus (anggota_fokus_id, sesi_id) VALUES (?, ?)",
        (anggota_id, sesi_id),
    )


KUNCI_STATE = (
    pytest.param(_kunci_mulai, id="sesi-mulai"),
    pytest.param(_kunci_selesai, id="sesi-selesai"),
    pytest.param(_kunci_dicetak, id="sesi-sudah-dicetak"),
    pytest.param(_kunci_jawaban, id="sudah-ada-jawaban"),
    pytest.param(_kunci_konfirmasi, id="sudah-dikonfirmasi"),
    pytest.param(_kunci_bukti_fokus, id="sudah-jadi-bukti-fokus"),
)


def test_perbarui_snapshot_memakai_compare_and_swap_atomik(db):
    with database.buka(db) as kon:
        _siswa, _sesi, butir, awal = _buat_butir(kon)
        baru = _penyajian("Teks cerita baru")

        pertama = presentation_lock.perbarui_snapshot(
            kon, butir, awal.fingerprint_penyajian, baru
        )
        kedua = presentation_lock.perbarui_snapshot(
            kon, butir, awal.fingerprint_penyajian, _penyajian("Writer terlambat")
        )

        baris = kon.execute(
            "SELECT * FROM sesi_soal WHERE id = ?", (butir,)
        ).fetchone()
    assert pertama is True
    assert kedua is False
    assert baris["teks_soal"] == "Teks cerita baru"
    assert baris["penyajian_json"] == serialisasi_penyajian(baru)
    assert baris["fingerprint_penyajian"] == baru.fingerprint_penyajian


def test_cas_none_menginisialisasi_snapshot_warisan_sekali(db):
    with database.buka(db) as kon:
        _siswa, _sesi, butir, _awal = _buat_butir(kon)
        kon.execute(
            "UPDATE sesi_soal SET "
            + ", ".join(f"{nama} = NULL" for nama in KOLOM_SNAPSHOT)
            + " WHERE id = ?",
            (butir,),
        )
        baru = _penyajian("Cerita per sesi untuk warisan")

        pertama = presentation_lock.perbarui_snapshot(kon, butir, None, baru)
        kedua = presentation_lock.perbarui_snapshot(
            kon, butir, None, _penyajian("Writer warisan terlambat")
        )
        baris = kon.execute(
            "SELECT * FROM sesi_soal WHERE id = ?", (butir,)
        ).fetchone()

    assert pertama is True
    assert kedua is False
    assert baris["teks_soal"] == "Cerita per sesi untuk warisan"
    assert baris["fingerprint_penyajian"] == baru.fingerprint_penyajian


def test_cas_none_tetap_menolak_identitas_matematis_yang_berbeda(db):
    with database.buka(db) as kon:
        _siswa, _sesi, butir, _awal = _buat_butir(kon)
        kon.execute(
            "UPDATE sesi_soal SET "
            + ", ".join(f"{nama} = NULL" for nama in KOLOM_SNAPSHOT)
            + " WHERE id = ?",
            (butir,),
        )
        salah = buat_penyajian(
            template_id="uji-kunci-visual",
            level="P3",
            parameter={"nilai": 8},
            teks_soal="Identitas matematis lain",
        )

        berhasil = presentation_lock.perbarui_snapshot(kon, butir, None, salah)
        baris = kon.execute(
            "SELECT fingerprint_penyajian FROM sesi_soal WHERE id = ?", (butir,)
        ).fetchone()

    assert berhasil is False
    assert baris["fingerprint_penyajian"] is None


@pytest.mark.parametrize("pengunci", KUNCI_STATE)
def test_layanan_menolak_update_setelah_state_terkunci(db, pengunci):
    with database.buka(db) as kon:
        siswa, sesi, butir, awal = _buat_butir(kon)
        pengunci(kon, siswa, sesi, butir)

        berhasil = presentation_lock.perbarui_snapshot(
            kon, butir, awal.fingerprint_penyajian, _penyajian("Dilarang")
        )

        assert berhasil is False
        assert _fingerprint(kon, butir) == awal.fingerprint_penyajian


@pytest.mark.parametrize("pengunci", KUNCI_STATE)
def test_trigger_menolak_raw_update_setelah_state_terkunci(db, pengunci):
    with database.buka(db) as kon:
        siswa, sesi, butir, awal = _buat_butir(kon)
        pengunci(kon, siswa, sesi, butir)

        with pytest.raises(sqlite3.IntegrityError, match="snapshot penyajian terkunci"):
            _raw_update(kon, butir, _penyajian("Bypass raw SQL"))

        assert _fingerprint(kon, butir) == awal.fingerprint_penyajian


def test_trigger_menerima_raw_update_sebelum_state_terkunci(db):
    with database.buka(db) as kon:
        _siswa, _sesi, butir, _awal = _buat_butir(kon)
        baru = _penyajian("Masih boleh")

        _raw_update(kon, butir, baru)

        assert _fingerprint(kon, butir) == baru.fingerprint_penyajian


def test_trigger_menolak_pemindahan_butir_dari_sesi_yang_sudah_dicetak(db):
    with database.buka(db) as kon:
        siswa, sesi_terkunci, butir, _awal = _buat_butir(kon)
        sesi_baru = int(kon.execute(
            "INSERT INTO sesi (siswa_id, seed, level) VALUES (?, 2, 'P3')",
            (siswa,),
        ).lastrowid)
        kon.execute(
            "UPDATE sesi SET penyajian_dibekukan = datetime('now') WHERE id = ?",
            (sesi_terkunci,),
        )

        with pytest.raises(sqlite3.IntegrityError, match="snapshot penyajian terkunci"):
            kon.execute(
                "UPDATE sesi_soal SET sesi_id = ? WHERE id = ?",
                (sesi_baru, butir),
            )


def test_trigger_menolak_pemindahan_butir_ke_sesi_yang_sudah_dicetak(db):
    with database.buka(db) as kon:
        siswa, sesi_awal, butir, _awal = _buat_butir(kon)
        sesi_terkunci = int(kon.execute(
            """INSERT INTO sesi
                   (siswa_id, seed, level, penyajian_dibekukan)
               VALUES (?, 2, 'P3', datetime('now'))""",
            (siswa,),
        ).lastrowid)

        with pytest.raises(sqlite3.IntegrityError, match="snapshot penyajian terkunci"):
            kon.execute(
                "UPDATE sesi_soal SET sesi_id = ? WHERE id = ?",
                (sesi_terkunci, butir),
            )
        assert kon.execute(
            "SELECT sesi_id FROM sesi_soal WHERE id = ?", (butir,)
        ).fetchone()[0] == sesi_awal


@pytest.mark.parametrize("kunci", [_kunci_konfirmasi, _kunci_bukti_fokus])
def test_butir_tidak_boleh_dipindah_ke_sesi_berbukti(db, kunci):
    with database.buka(db) as kon:
        siswa, asal, butir, _ = _buat_butir(kon)
        target = kon.execute("INSERT INTO sesi(siswa_id, seed, level) VALUES (?, 2, 'P3')", (siswa,)).lastrowid
        kunci(kon, siswa, target, butir)
        with pytest.raises(sqlite3.IntegrityError, match="terkunci"):
            kon.execute("UPDATE sesi_soal SET sesi_id = ? WHERE id = ?", (target, butir))
        assert kon.execute("SELECT sesi_id FROM sesi_soal WHERE id = ?", (butir,)).fetchone()[0] == asal


def test_dua_writer_konkuren_dengan_fingerprint_sama_hanya_satu_berhasil(db):
    with database.buka(db) as kon:
        _siswa, _sesi, butir, awal = _buat_butir(kon)

    gerbang = threading.Barrier(2)

    def menulis(teks: str) -> bool:
        snapshot = _penyajian(teks)
        with database.buka(db) as kon:
            kon.execute("PRAGMA busy_timeout = 5000")
            gerbang.wait(timeout=5)
            return presentation_lock.perbarui_snapshot(
                kon, butir, awal.fingerprint_penyajian, snapshot
            )

    with ThreadPoolExecutor(max_workers=2) as pekerja:
        hasil = list(pekerja.map(menulis, ("Writer A", "Writer B")))

    assert sorted(hasil) == [False, True]
    with database.buka(db) as kon:
        assert kon.execute(
            "SELECT teks_soal FROM sesi_soal WHERE id = ?", (butir,)
        ).fetchone()[0] in {"Writer A", "Writer B"}
