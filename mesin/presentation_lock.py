"""Layanan compare-and-swap untuk snapshot penyajian soal."""

from __future__ import annotations

import json
import sqlite3

from visual_contract import (
    PenyajianPertanyaan,
    fingerprint_matematis,
    serialisasi_penyajian,
)


_KOLOM_SNAPSHOT = (
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


def _nilai_snapshot(penyajian: PenyajianPertanyaan) -> tuple[object, ...]:
    if not isinstance(penyajian, PenyajianPertanyaan):
        raise ValueError("snapshot baru wajib berupa PenyajianPertanyaan")
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


def bekukan_penyajian(kon: sqlite3.Connection, sesi_id: int) -> bool:
    """Bekukan penyajian sesi secara idempoten tanpa mengambil alih commit.

    Mengembalikan ``False`` hanya bila sesi tidak ada. Timestamp pertama tidak
    digeser oleh cetak ulang; transaksi tetap sepenuhnya milik pemanggil.
    """
    kursor = kon.execute(
        """UPDATE sesi
           SET penyajian_dibekukan = COALESCE(
               penyajian_dibekukan, datetime('now', '+7 hours')
           )
           WHERE id = ?""",
        (sesi_id,),
    )
    return kursor.rowcount == 1


def perbarui_snapshot(
    kon: sqlite3.Connection,
    sesi_soal_id: int,
    expected_fingerprint: str | None,
    snapshot_baru: PenyajianPertanyaan,
) -> bool:
    """Ganti snapshot secara atomik bila versi dan keadaan sesi masih cocok.

    ``None`` berarti inisialisasi snapshot warisan dan memakai ``IS NULL``
    sebagai compare-and-swap. Identitas matematis tetap divalidasi terhadap
    sumber bank sebelum penulisan. ``False`` mencakup butir yang tidak ada,
    writer lain sudah menang, identitas berubah, atau sesi sudah terkunci.
    """
    if expected_fingerprint is not None and (
        not isinstance(expected_fingerprint, str) or not expected_fingerprint
    ):
        raise ValueError("expected fingerprint tidak valid")
    nilai = _nilai_snapshot(snapshot_baru)
    penugasan = ", ".join(f"{nama} = ?" for nama in _KOLOM_SNAPSHOT)

    if expected_fingerprint is None:
        sumber = kon.execute(
            """SELECT s.id, s.template_id, s.parameter, s.level
               FROM sesi_soal ss JOIN soal s ON s.id = ss.soal_id
               WHERE ss.id = ?""",
            (sesi_soal_id,),
        ).fetchone()
        if sumber is None:
            return False
        try:
            parameter = json.loads(sumber["parameter"])
            sidik_sumber = fingerprint_matematis(
                snapshot_baru.penyajian_versi,
                sumber["template_id"],
                sumber["level"],
                parameter,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False
        if sidik_sumber != snapshot_baru.fingerprint_matematis:
            return False
        syarat_sidik = "ss.fingerprint_penyajian IS NULL"
        parameter_sidik = ()
        syarat_identitas = """AND EXISTS (
                  SELECT 1 FROM soal s
                  WHERE s.id = ss.soal_id
                    AND s.id = ? AND s.template_id = ?
                    AND s.parameter = ? AND s.level = ?
              )"""
        parameter_identitas = (
            sumber["id"], sumber["template_id"],
            sumber["parameter"], sumber["level"],
        )
    else:
        syarat_sidik = "ss.fingerprint_penyajian = ?"
        parameter_sidik = (expected_fingerprint,)
        syarat_identitas = "AND ss.fingerprint_matematis = ?"
        parameter_identitas = (snapshot_baru.fingerprint_matematis,)

    kursor = kon.execute(
        f"""UPDATE sesi_soal AS ss
            SET {penugasan}
            WHERE ss.id = ?
              AND {syarat_sidik}
              {syarat_identitas}
              AND EXISTS (
                  SELECT 1 FROM sesi se
                  WHERE se.id = ss.sesi_id
                    AND se.mulai IS NULL
                    AND se.selesai IS NULL
                    AND se.dibatalkan IS NULL
                    AND se.penyajian_dibekukan IS NULL
              )
              AND NOT EXISTS (
                  SELECT 1 FROM jawaban j
                  JOIN sesi_soal lain ON lain.id = j.sesi_soal_id
                  WHERE lain.sesi_id = ss.sesi_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM konfirmasi_hasil kh
                  WHERE kh.sesi_id = ss.sesi_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM bukti_fokus bf
                  WHERE bf.sesi_id = ss.sesi_id
              )""",
        (
            *nilai,
            sesi_soal_id,
            *parameter_sidik,
            *parameter_identitas,
        ),
    )
    return kursor.rowcount == 1
