"""Akses basis data — simpan bank soal, sesi, jawaban, diagnosis.

Sengaja sqlite3 polos tanpa ORM: skemanya kecil, kuerinya sedikit, dan
ketergantungan tambahan hanya menambah hal yang bisa rusak saat deploy.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from generator import LEVEL_BAWAAN, buat_lembar
from skema import MIGRASI, SKEMA, VIEW_USANG
from templates import Soal

# Lokasi basis data bisa disetel lewat lingkungan, seperti berkas sandi.
#
# Diperlukan karena di dalam container /app dimiliki root dan hanya bisa
# dibaca: basis data harus tinggal di volume (/data) agar bisa ditulis DAN
# selamat saat container diganti. Tanpa ini container gagal start dengan
# "unable to open database file" — kegagalan yang hanya muncul saat deploy,
# tidak pernah saat dijalankan lokal.
BAWAAN = Path(
    os.environ.get("OSN_BERKAS_DB", Path(__file__).resolve().parent / "latihan.db")
)


@contextmanager
def buka(path: Path | str = BAWAAN) -> Iterator[sqlite3.Connection]:
    """Koneksi dengan foreign key aktif dan transaksi otomatis."""
    kon = sqlite3.connect(str(path))
    kon.row_factory = sqlite3.Row
    kon.execute("PRAGMA foreign_keys = ON")
    try:
        yield kon
        kon.commit()
    except Exception:
        kon.rollback()
        raise
    finally:
        kon.close()


def siapkan(path: Path | str = BAWAAN) -> None:
    """Buat/segarkan skema. Aman dijalankan berulang.

    Urutannya penting: view usang dibuang DULU, lalu kolom baru ditambahkan,
    baru SKEMA dijalankan untuk membangun ulang view dengan definisi terkini.
    Kalau view dibangun sebelum kolomnya ada, SQLite menerimanya (view tidak
    divalidasi saat dibuat) lalu gagal saat pertama kali dibaca — kegagalan
    yang muncul di halaman laporan, jauh dari penyebabnya.
    """
    with buka(path) as kon:
        for nama in VIEW_USANG:
            kon.execute(f"DROP VIEW IF EXISTS {nama}")
        migrasi(kon)
        kon.executescript(SKEMA)


def migrasi(kon: sqlite3.Connection) -> list[str]:
    """Tambahkan kolom yang belum ada. Mengembalikan yang benar-benar dijalankan.

    SQLite tidak punya "ADD COLUMN IF NOT EXISTS", jadi kolomnya diperiksa
    lewat PRAGMA table_info. Tabel yang belum ada dilewati — SKEMA akan
    membuatnya lengkap sesaat kemudian.
    """
    dijalankan: list[str] = []
    for tabel, kolom, pernyataan in MIGRASI:
        ada_tabel = kon.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (tabel,)
        ).fetchone()
        if not ada_tabel:
            continue
        kolom_ada = {
            r["name"] for r in kon.execute(f"PRAGMA table_info({tabel})").fetchall()
        }
        if kolom in kolom_ada:
            continue
        kon.execute(pernyataan)
        dijalankan.append(f"{tabel}.{kolom}")
    return dijalankan


# ── Siswa ───────────────────────────────────────────────────────────────


def tambah_siswa(kon: sqlite3.Connection, nama: str, tingkat: str = "P3") -> int:
    kon.execute(
        "INSERT OR IGNORE INTO siswa (nama, tingkat) VALUES (?, ?)", (nama, tingkat)
    )
    baris = kon.execute("SELECT id FROM siswa WHERE nama = ?", (nama,)).fetchone()
    return int(baris["id"])


def daftar_siswa(kon: sqlite3.Connection) -> list[sqlite3.Row]:
    return kon.execute("SELECT * FROM siswa ORDER BY nama").fetchall()


# ── Bank soal ───────────────────────────────────────────────────────────


def simpan_soal(kon: sqlite3.Connection, soal: Soal) -> int:
    """Masukkan soal ke bank. Idempoten lewat tanda_tangan.

    Mengembalikan id soal — yang lama kalau sudah pernah ada, sehingga
    generate berulang tidak menggandakan bank.
    """
    ada = kon.execute(
        "SELECT id FROM soal WHERE tanda_tangan = ?", (soal.tanda_tangan,)
    ).fetchone()
    if ada:
        return int(ada["id"])

    cur = kon.execute(
        """INSERT INTO soal (tanda_tangan, template_id, parameter, kunci,
                             bagian, tantangan, level)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            soal.tanda_tangan,
            soal.template_id,
            json.dumps(soal.parameter, ensure_ascii=False, sort_keys=True),
            soal.kunci,
            soal.bagian,
            int(soal.tantangan),
            soal.level,
        ),
    )
    soal_id = int(cur.lastrowid)

    for m in soal.malrule:
        kon.execute(
            """INSERT OR IGNORE INTO malrule (soal_id, malrule_id, jawaban, kode, alasan)
               VALUES (?, ?, ?, ?, ?)""",
            (soal_id, m.id, m.jawaban, m.kode, m.alasan),
        )
    return soal_id


def statistik_bank(kon: sqlite3.Connection) -> list[sqlite3.Row]:
    return kon.execute(
        """SELECT template_id, COUNT(*) AS jumlah
           FROM soal GROUP BY template_id ORDER BY jumlah DESC"""
    ).fetchall()


# ── Sesi ────────────────────────────────────────────────────────────────


def buat_sesi(
    kon: sqlite3.Connection,
    siswa_id: int,
    seed: int,
    topik: str = "pola bilangan",
    tanggal: str | None = None,
    level: str = LEVEL_BAWAAN,
) -> int:
    """Bangkitkan lembar dari seed, simpan soalnya ke bank, rangkai jadi sesi."""
    lembar = buat_lembar(seed, level=level)

    if tanggal:
        cur = kon.execute(
            """INSERT INTO sesi (siswa_id, seed, topik, level, tanggal)
               VALUES (?, ?, ?, ?, ?)""",
            (siswa_id, seed, topik, level, tanggal),
        )
    else:
        cur = kon.execute(
            "INSERT INTO sesi (siswa_id, seed, topik, level) VALUES (?, ?, ?, ?)",
            (siswa_id, seed, topik, level),
        )
    sesi_id = int(cur.lastrowid)

    for nomor, soal in enumerate(lembar.soal, start=1):
        soal_id = simpan_soal(kon, soal)
        kon.execute(
            "INSERT INTO sesi_soal (sesi_id, soal_id, nomor) VALUES (?, ?, ?)",
            (sesi_id, soal_id, nomor),
        )
    return sesi_id


def isi_sesi(kon: sqlite3.Connection, sesi_id: int) -> list[sqlite3.Row]:
    """Soal satu sesi beserta jawaban & diagnosisnya, urut nomor."""
    return kon.execute(
        """SELECT ss.id AS sesi_soal_id, ss.nomor,
                  s.id AS soal_id, s.template_id, s.parameter, s.kunci,
                  s.bagian, s.tantangan, s.level, s.cerita,
                  j.id AS jawaban_id, j.restatement, j.cara, j.jawaban,
                  j.belum_pernah, j.detik,
                  d.benar, d.kode_usulan, d.kode_final, d.malrule_id,
                  d.alasan, d.manual, d.catatan
           FROM sesi_soal ss
           JOIN soal s        ON s.id = ss.soal_id
           LEFT JOIN jawaban j   ON j.sesi_soal_id = ss.id
           LEFT JOIN diagnosis d ON d.jawaban_id = j.id
           WHERE ss.sesi_id = ?
           ORDER BY ss.nomor""",
        (sesi_id,),
    ).fetchall()


def malrule_soal(kon: sqlite3.Connection, soal_id: int) -> list[sqlite3.Row]:
    return kon.execute(
        "SELECT malrule_id, jawaban, kode, alasan FROM malrule WHERE soal_id = ?",
        (soal_id,),
    ).fetchall()


# ── Jawaban & diagnosis ─────────────────────────────────────────────────


def simpan_jawaban(
    kon: sqlite3.Connection,
    sesi_soal_id: int,
    jawaban: str = "",
    cara: str = "",
    restatement: str = "",
    belum_pernah: bool = False,
    detik: int | None = None,
) -> int:
    """Simpan/perbarui jawaban satu soal. Idempoten per sesi_soal."""
    kon.execute(
        """INSERT INTO jawaban (sesi_soal_id, restatement, cara, jawaban,
                                belum_pernah, detik)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(sesi_soal_id) DO UPDATE SET
               restatement  = excluded.restatement,
               cara         = excluded.cara,
               jawaban      = excluded.jawaban,
               belum_pernah = excluded.belum_pernah,
               detik        = excluded.detik""",
        (sesi_soal_id, restatement, cara, jawaban, int(belum_pernah), detik),
    )
    baris = kon.execute(
        "SELECT id FROM jawaban WHERE sesi_soal_id = ?", (sesi_soal_id,)
    ).fetchone()
    return int(baris["id"])


def simpan_diagnosis(
    kon: sqlite3.Connection,
    jawaban_id: int,
    benar: bool,
    kode_usulan: str | None,
    kode_final: str | None,
    malrule_id: str | None = None,
    alasan: str = "",
    manual: bool = False,
    catatan: str = "",
) -> int:
    kon.execute(
        """INSERT INTO diagnosis (jawaban_id, benar, kode_usulan, kode_final,
                                  malrule_id, alasan, manual, catatan)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(jawaban_id) DO UPDATE SET
               benar       = excluded.benar,
               kode_usulan = excluded.kode_usulan,
               kode_final  = excluded.kode_final,
               malrule_id  = excluded.malrule_id,
               alasan      = excluded.alasan,
               manual      = excluded.manual,
               catatan     = excluded.catatan""",
        (
            jawaban_id,
            int(benar),
            kode_usulan,
            kode_final,
            malrule_id,
            alasan,
            int(manual),
            catatan,
        ),
    )
    baris = kon.execute(
        "SELECT id FROM diagnosis WHERE jawaban_id = ?", (jawaban_id,)
    ).fetchone()
    return int(baris["id"])


# ── Laporan ─────────────────────────────────────────────────────────────


def ringkasan(kon: sqlite3.Connection, siswa_id: int | None = None) -> list[sqlite3.Row]:
    if siswa_id is None:
        return kon.execute(
            "SELECT * FROM ringkasan_sesi ORDER BY tanggal DESC, sesi_id DESC"
        ).fetchall()
    return kon.execute(
        """SELECT * FROM ringkasan_sesi WHERE siswa_id = ?
           ORDER BY tanggal DESC, sesi_id DESC""",
        (siswa_id,),
    ).fetchall()


def miskonsepsi_berulang(
    kon: sqlite3.Connection, siswa_id: int, minimal: int = 1
) -> list[sqlite3.Row]:
    """Miskonsepsi dihitung per malrule_id, bukan per nomor soal.

    Aturan dari lembar penilaian: satu miskonsepsi yang muncul di tiga soal
    tetap satu miskonsepsi. Yang penting bukan berapa soal yang salah, tapi
    berapa gagasan keliru yang masih hidup — dan mana yang bertahan lintas
    sesi meski angkanya sudah diganti.
    """
    return kon.execute(
        """SELECT d.malrule_id,
                  s.template_id,
                  MAX(d.alasan)              AS alasan,
                  COUNT(*)                   AS kemunculan,
                  COUNT(DISTINCT se.id)      AS jumlah_sesi,
                  MIN(se.tanggal)            AS pertama,
                  MAX(se.tanggal)            AS terakhir
           FROM diagnosis d
           JOIN jawaban j    ON j.id  = d.jawaban_id
           JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
           JOIN sesi se      ON se.id = ss.sesi_id
           JOIN soal s       ON s.id  = ss.soal_id
           WHERE se.siswa_id = ?
             AND d.kode_final = 'K'
             AND d.malrule_id IS NOT NULL
           GROUP BY d.malrule_id, s.template_id
           HAVING COUNT(*) >= ?
           ORDER BY jumlah_sesi DESC, kemunculan DESC""",
        (siswa_id, minimal),
    ).fetchall()


def peta_materi_baru(kon: sqlite3.Connection, siswa_id: int) -> list[sqlite3.Row]:
    """Tipe soal yang ditandai T — belum pernah diajarkan, bukan kegagalan."""
    return kon.execute(
        """SELECT s.template_id, COUNT(*) AS kali, MAX(se.tanggal) AS terakhir
           FROM diagnosis d
           JOIN jawaban j    ON j.id  = d.jawaban_id
           JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
           JOIN sesi se      ON se.id = ss.sesi_id
           JOIN soal s       ON s.id  = ss.soal_id
           WHERE se.siswa_id = ? AND d.kode_final = 'T'
           GROUP BY s.template_id
           ORDER BY kali DESC""",
        (siswa_id,),
    ).fetchall()
