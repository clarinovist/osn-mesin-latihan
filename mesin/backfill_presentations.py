"""Backfill eksplisit snapshot penyajian Fase 1.

Modul ini sengaja tidak dipanggil dari ``database.siapkan``. Operator wajib
menjalankannya secara eksplisit pada berkas SQLite yang sudah memiliki kolom
snapshot. Semua keluaran CLI hanya berupa hitungan agregat.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Sequence

import schema
from generator import LEVEL_BAWAAN
from question_views import KOLOM_SNAPSHOT
from templates import REGISTRI
from visual_contract import buat_penyajian, serialisasi_penyajian


_TRIGGER_KUNCI = "sesi_soal_snapshot_tolak_update_terkunci"
_KOLOM_TULIS = KOLOM_SNAPSHOT


class BackfillGagal(RuntimeError):
    """Satu batch gagal; watermark batch sukses terakhir tetap aman."""

    def __init__(self, pesan: str, watermark: int) -> None:
        super().__init__(pesan)
        self.watermark = watermark


class VerifikasiGagal(RuntimeError):
    """Verifier akhir menemukan snapshot atau integritas yang tidak sah."""


@dataclass(frozen=True)
class HasilBatch:
    diperiksa: int
    diubah: int
    watermark: int
    selesai: bool


@dataclass(frozen=True)
class HasilBackfill:
    total_diperiksa: int
    total_diubah: int
    jumlah_batch: int
    watermark: int
    selesai: bool


@dataclass(frozen=True)
class HasilVerifikasi:
    total_baris: int
    baris_lengkap: int
    baris_parsial: int
    baris_warisan: int
    fingerprint_terverifikasi: int
    integrity_check: str
    foreign_key_errors: int


def _validasi_argumen(ukuran_batch: int, watermark: int) -> None:
    if type(ukuran_batch) is not int or ukuran_batch < 1:
        raise ValueError("ukuran_batch wajib bilangan bulat positif")
    if type(watermark) is not int or watermark < 0:
        raise ValueError("watermark wajib bilangan bulat nonnegatif")


def _keadaan_snapshot(baris: sqlite3.Row) -> str:
    nilai = [baris[nama] for nama in KOLOM_SNAPSHOT]
    if all(isi is None for isi in nilai):
        return "warisan"
    if all(isi is not None for isi in nilai):
        return "lengkap"
    return "parsial"


def _ambil_batch(
    kon: sqlite3.Connection, watermark: int, ukuran_batch: int
) -> list[sqlite3.Row]:
    return kon.execute(
        """SELECT ss.*, s.id AS sumber_soal_id,
                  s.template_id, s.parameter, s.level, s.cerita
           FROM sesi_soal ss
           LEFT JOIN soal s ON s.id = ss.soal_id
           WHERE ss.id > ?
           ORDER BY ss.id
           LIMIT ?""",
        (watermark, ukuran_batch),
    ).fetchall()


def _masih_ada(kon: sqlite3.Connection, watermark: int) -> bool:
    return (
        kon.execute(
            "SELECT 1 FROM sesi_soal WHERE id > ? LIMIT 1", (watermark,)
        ).fetchone()
        is not None
    )


def _watermark_tidak_melompati_warisan(
    kon: sqlite3.Connection, watermark: int
) -> bool:
    """True bila ada snapshot belum lengkap pada/bawah watermark."""
    if watermark == 0:
        return False
    syarat_null = " OR ".join(f"{nama} IS NULL" for nama in KOLOM_SNAPSHOT)
    return kon.execute(
        f"SELECT 1 FROM sesi_soal WHERE id <= ? AND ({syarat_null}) LIMIT 1",
        (watermark,),
    ).fetchone() is not None


def _validasi_sumber_dan_bangun(
    baris: sqlite3.Row, *, buat_snapshot: bool
) -> Optional[tuple[Any, ...]]:
    if baris["sumber_soal_id"] is None:
        raise ValueError("sumber soal sesi tidak ditemukan")
    try:
        parameter = json.loads(baris["parameter"])
    except (TypeError, json.JSONDecodeError) as galat:
        raise ValueError("parameter soal tidak valid") from galat
    if not isinstance(parameter, dict):
        raise ValueError("parameter soal wajib berupa objek JSON")

    if baris["sumber_soal_id"] is None:
        raise ValueError("sumber soal sesi tidak ditemukan")
    template_id = baris["template_id"]
    if template_id not in REGISTRI:
        raise ValueError("template soal warisan tidak dikenal")
    try:
        soal = REGISTRI[template_id](**parameter)
    except (KeyError, TypeError, ValueError) as galat:
        raise ValueError("parameter soal tidak valid untuk template") from galat
    if not buat_snapshot:
        return None

    level = baris["level"] or LEVEL_BAWAAN
    cerita = (baris["cerita"] or "").strip()
    penyajian = buat_penyajian(
        template_id=template_id,
        level=level,
        parameter=parameter,
        teks_soal=cerita or soal.teks,
        bagian_soal=soal.bagian,
        tantangan_soal=soal.tantangan,
        minta_restatement=soal.minta_restatement,
        asal_teks="warisan",
        status_visual="warisan",
        mode_representasi="teks-v1",
    )
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


def _sql_trigger(kon: sqlite3.Connection) -> Optional[str]:
    baris = kon.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
        (_TRIGGER_KUNCI,),
    ).fetchone()
    return None if baris is None else str(baris[0])


@lru_cache(maxsize=1)
def _sql_trigger_tepercaya() -> str:
    """Ambil definisi trigger dari SKEMA yang menjadi sumber kebenaran."""
    acuan = sqlite3.connect(":memory:")
    try:
        acuan.executescript(schema.SKEMA)
        sql = _sql_trigger(acuan)
        if sql is None:
            raise RuntimeError("trigger pengunci tidak ada dalam SKEMA")
        return sql
    finally:
        acuan.close()


def _normalisasi_sql(sql: str) -> str:
    return " ".join(sql.split()).casefold()


def _pastikan_trigger_tepercaya(kon: sqlite3.Connection) -> str:
    aktual = _sql_trigger(kon)
    harapan = _sql_trigger_tepercaya()
    if aktual is None or _normalisasi_sql(aktual) != _normalisasi_sql(harapan):
        raise RuntimeError("trigger pengunci snapshot hilang atau berubah")
    return aktual


def _tulis_rencana(
    kon: sqlite3.Connection, rencana: list[tuple[int, tuple[Any, ...]]]
) -> None:
    if not rencana:
        return
    sql_trigger = _pastikan_trigger_tepercaya(kon)
    kon.execute(f'DROP TRIGGER "{_TRIGGER_KUNCI}"')
    try:
        penugasan = ", ".join(f"{nama} = ?" for nama in _KOLOM_TULIS)
        for sesi_soal_id, nilai in rencana:
            kurir = kon.execute(
                f"UPDATE sesi_soal SET {penugasan} WHERE id = ?",
                nilai + (sesi_soal_id,),
            )
            if kurir.rowcount != 1:
                raise RuntimeError("baris sasaran berubah selama backfill")
    finally:
        kon.execute(sql_trigger)


def jalankan_satu_batch(
    kon: sqlite3.Connection, *, ukuran_batch: int = 500, watermark: int = 0
) -> HasilBatch:
    """Proses maksimal satu batch; kegagalan menggulung seluruh batch."""
    _validasi_argumen(ukuran_batch, watermark)
    savepoint = "backfill_penyajian_fase1"
    kon.execute(f"SAVEPOINT {savepoint}")
    try:
        _pastikan_trigger_tepercaya(kon)
        if _watermark_tidak_melompati_warisan(kon, watermark):
            raise ValueError("watermark melewati baris warisan")
        baris_baris = _ambil_batch(kon, watermark, ukuran_batch)
        rencana: list[tuple[int, tuple[Any, ...]]] = []
        for baris in baris_baris:
            keadaan = _keadaan_snapshot(baris)
            if keadaan == "parsial":
                raise ValueError("snapshot penyajian parsial ditolak")
            nilai = _validasi_sumber_dan_bangun(
                baris, buat_snapshot=keadaan == "warisan"
            )
            if keadaan == "warisan":
                assert nilai is not None
                rencana.append((int(baris["id"]), nilai))

        watermark_baru = (
            int(baris_baris[-1]["id"]) if baris_baris else watermark
        )
        _tulis_rencana(kon, rencana)
        selesai = not _masih_ada(kon, watermark_baru)
        kon.execute(f"RELEASE SAVEPOINT {savepoint}")
        return HasilBatch(
            diperiksa=len(baris_baris),
            diubah=len(rencana),
            watermark=watermark_baru,
            selesai=selesai,
        )
    except Exception as galat:
        kon.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        kon.execute(f"RELEASE SAVEPOINT {savepoint}")
        if isinstance(galat, BackfillGagal):
            raise
        raise BackfillGagal(str(galat), watermark) from galat


def _jalankan_semua(
    kon: sqlite3.Connection,
    *,
    ukuran_batch: int,
    watermark: int,
    commit_per_batch: bool,
) -> HasilBackfill:
    total_diperiksa = 0
    total_diubah = 0
    jumlah_batch = 0
    selesai = False
    sekarang = watermark
    while not selesai:
        hasil = jalankan_satu_batch(
            kon, ukuran_batch=ukuran_batch, watermark=sekarang
        )
        if commit_per_batch:
            kon.commit()
        total_diperiksa += hasil.diperiksa
        total_diubah += hasil.diubah
        jumlah_batch += 1
        sekarang = hasil.watermark
        selesai = hasil.selesai
    return HasilBackfill(
        total_diperiksa=total_diperiksa,
        total_diubah=total_diubah,
        jumlah_batch=jumlah_batch,
        watermark=sekarang,
        selesai=selesai,
    )


def jalankan(
    kon: sqlite3.Connection, *, ukuran_batch: int = 500, watermark: int = 0
) -> HasilBackfill:
    """Jalankan semua batch tanpa mengambil alih transaksi pemanggil."""
    _validasi_argumen(ukuran_batch, watermark)
    return _jalankan_semua(
        kon,
        ukuran_batch=ukuran_batch,
        watermark=watermark,
        commit_per_batch=False,
    )


def verifikasi(kon: sqlite3.Connection) -> HasilVerifikasi:
    """Verifikasi snapshot lengkap, fingerprint, integritas, dan foreign key."""
    from question_views import penyajian_dari_baris

    try:
        _pastikan_trigger_tepercaya(kon)
    except RuntimeError as galat:
        raise VerifikasiGagal(str(galat)) from galat

    baris_baris = kon.execute(
        """SELECT ss.*, s.template_id, s.parameter, s.level, s.cerita
           FROM sesi_soal ss JOIN soal s ON s.id = ss.soal_id
           ORDER BY ss.id"""
    ).fetchall()
    lengkap = 0
    parsial = 0
    warisan = 0
    sidik_sah = 0
    for baris in baris_baris:
        keadaan = _keadaan_snapshot(baris)
        if keadaan == "parsial":
            parsial += 1
            continue
        if keadaan == "warisan":
            warisan += 1
            continue
        lengkap += 1
        try:
            penyajian = penyajian_dari_baris(baris)
        except ValueError as galat:
            raise VerifikasiGagal("fingerprint atau snapshot tidak valid") from galat
        if penyajian.fingerprint_penyajian != baris["fingerprint_penyajian"]:
            raise VerifikasiGagal("fingerprint penyajian tidak cocok")
        sidik_sah += 1

    if parsial:
        raise VerifikasiGagal("masih ada snapshot parsial")
    if warisan:
        raise VerifikasiGagal("masih ada baris warisan")

    hasil_integritas = [str(b[0]) for b in kon.execute("PRAGMA integrity_check")]
    integritas = hasil_integritas[0] if len(hasil_integritas) == 1 else "gagal"
    if hasil_integritas != ["ok"]:
        raise VerifikasiGagal("integrity_check gagal")
    galat_fk = len(kon.execute("PRAGMA foreign_key_check").fetchall())
    if galat_fk:
        raise VerifikasiGagal("foreign_key_check gagal")

    return HasilVerifikasi(
        total_baris=len(baris_baris),
        baris_lengkap=lengkap,
        baris_parsial=parsial,
        baris_warisan=warisan,
        fingerprint_terverifikasi=sidik_sah,
        integrity_check=integritas,
        foreign_key_errors=galat_fk,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--watermark", type=int, default=0)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    argumen = _parser().parse_args(argv)
    try:
        _validasi_argumen(argumen.batch_size, argumen.watermark)
        kon = sqlite3.connect(str(argumen.database))
        kon.row_factory = sqlite3.Row
        kon.execute("PRAGMA foreign_keys = ON")
        try:
            hasil = _jalankan_semua(
                kon,
                ukuran_batch=argumen.batch_size,
                watermark=argumen.watermark,
                commit_per_batch=True,
            )
            pemeriksaan = verifikasi(kon)
        finally:
            kon.close()
    except (BackfillGagal, VerifikasiGagal, ValueError, sqlite3.Error) as galat:
        print(json.dumps({"galat": str(galat)}, sort_keys=True))
        return 1

    print(
        json.dumps(
            {"backfill": asdict(hasil), "verifikasi": asdict(pemeriksaan)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
