"""Sidecar provenance penyajian; tidak membuat atau mengoreksi bukti pedagogis."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Optional

import question_views


_KOLOM_ADAPTER = question_views.KOLOM_SNAPSHOT + (
    "template_id", "parameter", "level", "cerita",
)


def provenance_dari_baris(baris) -> tuple[str, Optional[str]]:
    """Validasi snapshot utuh; NULL warisan bukan fingerprint rekonstruksi."""
    try:
        warisan = all(baris[nama] is None for nama in question_views.KOLOM_SNAPSHOT)
        penyajian = question_views.penyajian_dari_baris(baris)
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError) as galat:
        raise ValueError("snapshot penyajian outcome tidak valid") from galat
    return (penyajian.mode_representasi,
            None if warisan else penyajian.fingerprint_penyajian)


def _provenance_sah(mode, fingerprint, *nilai) -> int:
    """UDF fail-closed: trigger menerima hanya metadata hasil adapter aman."""
    try:
        harapan = provenance_dari_baris(dict(zip(_KOLOM_ADAPTER, nilai)))
    except ValueError:
        return 0
    return int((mode, fingerprint) == harapan)


def daftarkan_validasi(kon: sqlite3.Connection) -> None:
    """Koneksi tanpa UDF ini tidak dapat INSERT sidecar melalui raw SQL."""
    kon.create_function("osn_provenance_outcome_sah", 2 + len(_KOLOM_ADAPTER),
                        _provenance_sah)


@contextmanager
def transaksi(kon: sqlite3.Connection):
    """Savepoint lokal tanpa meng-commit transaksi milik pemanggil."""
    if not kon.in_transaction:
        kon.execute("BEGIN")
    kon.execute("SAVEPOINT provenance_outcome")
    try:
        yield
        kon.execute("RELEASE SAVEPOINT provenance_outcome")
    except Exception:
        kon.execute("ROLLBACK TO SAVEPOINT provenance_outcome")
        kon.execute("RELEASE SAVEPOINT provenance_outcome")
        raise


def _sumber(kon: sqlite3.Connection, konfirmasi_id: Optional[int]):
    kolom = ", ".join("ss." + nama for nama in question_views.KOLOM_SNAPSHOT)
    return kon.execute(
        f"""SELECT so.id AS snapshot_outcome_id, ss.id AS hubungan_id,
                   s.id AS sumber_id, {kolom}, s.template_id, s.parameter,
                   s.level, s.cerita, po.snapshot_outcome_id AS provenance_id,
                   po.mode_representasi AS mode_tersimpan,
                   po.fingerprint_penyajian AS fingerprint_tersimpan
            FROM snapshot_outcome so
            LEFT JOIN konfirmasi_hasil kh ON kh.id = so.konfirmasi_id
            LEFT JOIN sesi_soal ss ON ss.id = so.sesi_soal_id
                AND ss.sesi_id = kh.sesi_id AND ss.nomor = so.nomor
            LEFT JOIN soal s ON s.id = ss.soal_id AND s.template_id = so.template_id
            LEFT JOIN penyajian_outcome po ON po.snapshot_outcome_id = so.id
            WHERE (? IS NULL OR so.konfirmasi_id = ?)
              AND (po.snapshot_outcome_id IS NULL OR ? IS NOT NULL)
            ORDER BY so.id""",
        (konfirmasi_id, konfirmasi_id, konfirmasi_id),
    ).fetchall()


def lengkapi(kon: sqlite3.Connection, konfirmasi_id: Optional[int] = None) -> int:
    """Isi hanya metadata hilang, setelah skema siap; gagal tanpa tebakan teks.

    Tanpa id: backfill seluruh riwayat yang belum punya sidecar. Dengan id:
    pastikan pula metadata yang sudah ada cocok, untuk konfirmasi idempoten.
    """
    with transaksi(kon):
        baris = _sumber(kon, konfirmasi_id)
        for b in baris:
            if b["hubungan_id"] is None or b["sumber_id"] is None:
                raise ValueError("hubungan snapshot penyajian outcome hilang atau tidak cocok")
            mode, fingerprint = provenance_dari_baris(b)
            if b["provenance_id"] is not None:
                if (b["mode_tersimpan"], b["fingerprint_tersimpan"]) != (mode, fingerprint):
                    raise ValueError("provenance outcome tidak cocok dengan snapshot")
                continue
            kon.execute(
                """INSERT INTO penyajian_outcome
                   (snapshot_outcome_id, mode_representasi, fingerprint_penyajian)
                   VALUES (?, ?, ?)""",
                (b["snapshot_outcome_id"], mode, fingerprint),
            )
    return sum(b["provenance_id"] is None for b in baris)


def muat(kon: sqlite3.Connection, konfirmasi_id: int) -> tuple[sqlite3.Row, ...]:
    """Baca bukti dan sidecar saja; provenance hilang perlu migrasi eksplisit."""
    baris = tuple(kon.execute(
        """SELECT so.*, po.snapshot_outcome_id AS provenance_id,
                  po.mode_representasi, po.fingerprint_penyajian
           FROM snapshot_outcome so
           LEFT JOIN penyajian_outcome po ON po.snapshot_outcome_id = so.id
           WHERE so.konfirmasi_id = ? ORDER BY so.nomor""",
        (konfirmasi_id,),
    ))
    if any(b["provenance_id"] is None for b in baris):
        raise ValueError("provenance penyajian outcome hilang; jalankan migrasi")
    return baris
