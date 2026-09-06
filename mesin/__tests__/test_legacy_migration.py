"""Guard preservasi histori saat database pra-siklus dimigrasikan ke Fase 6."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import migrate_params  # noqa: E402


TABEL_HISTORI = (
    "siswa",
    "soal",
    "malrule",
    "sesi",
    "tautan_sesi",
    "sesi_soal",
    "jawaban",
    "diagnosis",
    "lampiran",
)

TABEL_SIKLUS = (
    "putaran_fokus",
    "anggota_fokus",
    "bukti_fokus",
    "konfirmasi_hasil",
    "snapshot_outcome",
    "kejadian_belajar",
)


def _buat_database_pra_siklus(path: Path) -> None:
    """Buat skema valid tepat sebelum metadata siklus belajar tersedia."""
    kon = sqlite3.connect(str(path))
    try:
        kon.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE siswa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tingkat TEXT NOT NULL DEFAULT 'P3',
                pemilik TEXT NOT NULL DEFAULT '',
                dibuat TEXT NOT NULL DEFAULT (datetime('now', '+7 hours')),
                UNIQUE (nama, pemilik)
            );
            CREATE INDEX idx_siswa_pemilik ON siswa(pemilik);

            CREATE TABLE soal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanda_tangan TEXT NOT NULL UNIQUE,
                template_id TEXT NOT NULL,
                parameter TEXT NOT NULL,
                kunci TEXT NOT NULL,
                bagian TEXT NOT NULL DEFAULT '',
                tantangan INTEGER NOT NULL DEFAULT 0,
                level TEXT NOT NULL DEFAULT 'P3',
                cerita TEXT NOT NULL DEFAULT '',
                dibuat TEXT NOT NULL DEFAULT (datetime('now', '+7 hours'))
            );
            CREATE INDEX idx_soal_template ON soal(template_id);
            CREATE INDEX idx_soal_level ON soal(level);

            CREATE TABLE malrule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                soal_id INTEGER NOT NULL REFERENCES soal(id) ON DELETE CASCADE,
                malrule_id TEXT NOT NULL,
                jawaban TEXT NOT NULL,
                kode TEXT NOT NULL CHECK (kode IN ('B','K','H','E','T','N')),
                alasan TEXT NOT NULL DEFAULT '',
                UNIQUE (soal_id, malrule_id)
            );

            CREATE TABLE sesi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siswa_id INTEGER NOT NULL REFERENCES siswa(id) ON DELETE CASCADE,
                seed INTEGER NOT NULL,
                topik TEXT NOT NULL DEFAULT 'pola-bilangan',
                level TEXT NOT NULL DEFAULT 'P3',
                mode TEXT NOT NULL DEFAULT 'diagnostik',
                timer_mode TEXT NOT NULL DEFAULT 'tanpa',
                durasi_menit INTEGER NOT NULL DEFAULT 15,
                timer_auto INTEGER NOT NULL DEFAULT 0,
                tanggal TEXT NOT NULL DEFAULT (date('now', '+7 hours')),
                mulai TEXT,
                selesai TEXT,
                direview TEXT,
                jenis TEXT NOT NULL DEFAULT 'biasa',
                sumber_sesi_id INTEGER REFERENCES sesi(id) ON DELETE SET NULL,
                catatan TEXT NOT NULL DEFAULT '',
                dibuat TEXT NOT NULL DEFAULT (datetime('now', '+7 hours'))
            );
            CREATE INDEX idx_sesi_siswa ON sesi(siswa_id, tanggal);

            CREATE TABLE tautan_sesi (
                sesi_id INTEGER PRIMARY KEY REFERENCES sesi(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                dibuat INTEGER NOT NULL,
                kedaluarsa INTEGER NOT NULL,
                dicabut INTEGER
            );
            CREATE INDEX idx_tautan_sesi_hash ON tautan_sesi(token_hash);

            CREATE TABLE sesi_soal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesi_id INTEGER NOT NULL REFERENCES sesi(id) ON DELETE CASCADE,
                soal_id INTEGER NOT NULL REFERENCES soal(id),
                nomor INTEGER NOT NULL,
                UNIQUE (sesi_id, nomor)
            );

            CREATE TABLE jawaban (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesi_soal_id INTEGER NOT NULL UNIQUE
                    REFERENCES sesi_soal(id) ON DELETE CASCADE,
                restatement TEXT NOT NULL DEFAULT '',
                cara TEXT NOT NULL DEFAULT '',
                jawaban TEXT NOT NULL DEFAULT '',
                belum_pernah INTEGER NOT NULL DEFAULT 0,
                detik INTEGER,
                dicatat TEXT NOT NULL DEFAULT (datetime('now', '+7 hours'))
            );

            CREATE TABLE diagnosis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jawaban_id INTEGER NOT NULL UNIQUE
                    REFERENCES jawaban(id) ON DELETE CASCADE,
                benar INTEGER NOT NULL DEFAULT 0,
                kode_usulan TEXT CHECK (
                    kode_usulan IS NULL OR kode_usulan IN ('B','K','H','E','T','N')
                ),
                kode_final TEXT CHECK (
                    kode_final IS NULL OR kode_final IN ('B','K','H','E','T','N')
                ),
                malrule_id TEXT,
                alasan TEXT NOT NULL DEFAULT '',
                manual INTEGER NOT NULL DEFAULT 0,
                catatan TEXT NOT NULL DEFAULT '',
                didiagnosis TEXT NOT NULL DEFAULT (datetime('now', '+7 hours'))
            );

            CREATE TABLE lampiran (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesi_id INTEGER NOT NULL REFERENCES sesi(id) ON DELETE CASCADE,
                nama_berkas TEXT NOT NULL,
                mime TEXT NOT NULL DEFAULT 'image/jpeg',
                hasil_json TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'baru'
                    CHECK (status IN ('baru', 'diterapkan')),
                dibuat TEXT NOT NULL DEFAULT (datetime('now', '+7 hours'))
            );
            CREATE INDEX idx_lampiran_sesi ON lampiran(sesi_id);

            CREATE VIEW ringkasan_sesi AS
            SELECT s.id AS sesi_id, s.siswa_id, s.level, COUNT(ss.id) AS jumlah_soal
            FROM sesi s
            LEFT JOIN sesi_soal ss ON ss.sesi_id = s.id
            GROUP BY s.id;

            INSERT INTO siswa (id, nama, tingkat, pemilik, dibuat)
            VALUES (7, 'Sintetis P5', 'P5', 'guru-uji', '2026-08-01 07:00:00');

            INSERT INTO soal
                (id, tanda_tangan, template_id, parameter, kunci, bagian,
                 tantangan, level, cerita, dibuat)
            VALUES
                (11, 'P3|siklus_huruf(pola=[''A'', ''B'', ''C'', ''C''],posisi=9)',
                 'siklus_huruf', '{"pola":["A","B","C","C"],"posisi":9}',
                 'A', 'B', 0, 'P3', 'Cerita P3 yang tersimpan',
                 '2026-08-02 07:00:00'),
                (12, 'P5|warisan_sintetis(nilai=42)', 'warisan_sintetis',
                 '{"nilai":42}', '42', 'K', 1, 'P5', '',
                 '2026-08-03 07:00:00');

            INSERT INTO malrule
                (id, soal_id, malrule_id, jawaban, kode, alasan)
            VALUES
                (15, 11, 'salah-posisi', 'B', 'K', 'Menggeser indeks'),
                (16, 12, 'salah-hitung', '24', 'H', 'Membalik angka');

            INSERT INTO sesi
                (id, siswa_id, seed, topik, level, mode, timer_mode,
                 durasi_menit, timer_auto, tanggal, mulai, selesai, direview,
                 jenis, sumber_sesi_id, catatan, dibuat)
            VALUES
                (21, 7, 303, 'pola-bilangan', 'P3', 'diagnostik', 'tanpa',
                 15, 0, '2026-08-10', '2026-08-10 08:00:00',
                 '2026-08-10 08:20:00', '2026-08-10 09:00:00',
                 'biasa', NULL, 'Riwayat level lama', '2026-08-09 07:00:00'),
                (22, 7, 505, 'gabungan:sintetis', 'P5', 'diagnostik', 'tanpa',
                 15, 0, '2026-09-05', '2026-09-05 08:00:00',
                 NULL, '2026-09-05 09:00:00',
                 'biasa', NULL, 'Direview tetapi belum selesai',
                 '2026-09-04 07:00:00');

            INSERT INTO tautan_sesi
                (sesi_id, token_hash, dibuat, kedaluarsa, dicabut)
            VALUES (22, 'hash-sintetis-bukan-token', 1788566400, 1788652800, NULL);

            INSERT INTO sesi_soal (id, sesi_id, soal_id, nomor)
            VALUES (31, 21, 11, 1), (32, 22, 12, 1);

            INSERT INTO jawaban
                (id, sesi_soal_id, restatement, cara, jawaban,
                 belum_pernah, detik, dicatat)
            VALUES
                (41, 31, 'Cari pola', 'Hitung urutan', 'B', 0, 75,
                 '2026-08-10 08:10:00'),
                (42, 32, 'Cari nilai', 'Hitung manual', '24', 0, 91,
                 '2026-09-05 08:10:00');

            INSERT INTO diagnosis
                (id, jawaban_id, benar, kode_usulan, kode_final, malrule_id,
                 alasan, manual, catatan, didiagnosis)
            VALUES
                (51, 41, 0, 'K', 'K', 'salah-posisi',
                 'Diagnosis P3', 1, 'Dikoreksi guru', '2026-08-10 09:00:00'),
                (52, 42, 0, 'H', 'H', 'salah-hitung',
                 'Diagnosis P5', 0, '', '2026-09-05 09:00:00');

            INSERT INTO lampiran
                (id, sesi_id, nama_berkas, mime, hasil_json, status, dibuat)
            VALUES
                (61, 22, 'sintetis.jpg', 'image/jpeg',
                 '{"sumber":"fixture-sintetis"}', 'diterapkan',
                 '2026-09-05 08:30:00');
            """
        )
        kon.commit()
    finally:
        kon.close()


def _metadata_dan_baris(kon: sqlite3.Connection):
    metadata = {}
    baris = {}
    tabel_ada = tuple(r[0] for r in kon.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ))
    assert set(TABEL_HISTORI) <= set(tabel_ada)
    for tabel in tabel_ada:
        info = kon.execute(f"PRAGMA table_info({tabel})").fetchall()
        metadata[tabel] = [tuple(r) for r in info]
        kolom = [r["name"] for r in info]
        pilihan = ", ".join(f'"{nama}"' for nama in kolom)
        baris[tabel] = [
            tuple(r[nama] for nama in kolom)
            for r in kon.execute(
                f'SELECT {pilihan} FROM "{tabel}" ORDER BY rowid'
            ).fetchall()
        ]
    return metadata, baris


def _baris_dengan_kolom_lama(kon: sqlite3.Connection, metadata_lama):
    hasil = {}
    for tabel, info in metadata_lama.items():
        kolom = [r[1] for r in info]
        pilihan = ", ".join(f'"{nama}"' for nama in kolom)
        hasil[tabel] = [
            tuple(r[nama] for nama in kolom)
            for r in kon.execute(
                f'SELECT {pilihan} FROM "{tabel}" ORDER BY rowid'
            ).fetchall()
        ]
    return hasil


def _relasi_dan_indeks(kon):
    """Objek lama dipertahankan; view ringkasan memang dibangun ulang."""
    indeks = tuple(tuple(r) for r in kon.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'index' ORDER BY name"
    ))
    relasi = tuple(
        (tabel, tuple(tuple(r) for r in kon.execute(
            f"PRAGMA foreign_key_list({tabel})"
        )))
        for tabel in TABEL_HISTORI
    )
    return indeks, relasi


def test_siapkan_fase6_mempertahankan_seluruh_histori_pra_siklus(
    tmp_path, monkeypatch
):
    path = tmp_path / "pra-siklus.db"
    _buat_database_pra_siklus(path)

    with database.buka(path) as kon:
        metadata_lama, baris_lama = _metadata_dan_baris(kon)
        indeks_lama, relasi_lama = _relasi_dan_indeks(kon)

    panggilan = []
    migrasi_asli = database.migrasi
    rebuild_asli = database.rebuild_siswa_unik
    parameter_asli = migrate_params.jalankan

    def catat_migrasi(kon):
        panggilan.append("migrasi")
        return migrasi_asli(kon)

    def catat_rebuild(kon):
        panggilan.append("rebuild_siswa_unik")
        return rebuild_asli(kon)

    def catat_parameter(kon):
        panggilan.append("migrate_params")
        return parameter_asli(kon)

    monkeypatch.setattr(database, "migrasi", catat_migrasi)
    monkeypatch.setattr(database, "rebuild_siswa_unik", catat_rebuild)
    monkeypatch.setattr(migrate_params, "jalankan", catat_parameter)

    database.siapkan(path)
    with database.buka(path) as kon:
        assert _baris_dengan_kolom_lama(kon, metadata_lama) == baris_lama
        indeks_baru, relasi_baru = _relasi_dan_indeks(kon)
        assert set(indeks_lama) <= set(indeks_baru)
        for (tabel, lama), (_, baru) in zip(relasi_lama, relasi_baru):
            # ALTER menomori ulang FK ketika menambah putaran_id.
            assert {r[2:] for r in lama} <= {r[2:] for r in baru}, tabel
        sesudah_pertama = tuple(kon.iterdump())
        assert kon.execute("PRAGMA foreign_key_check").fetchall() == []
        assert kon.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    database.siapkan(path)
    with database.buka(path) as kon:
        assert tuple(kon.iterdump()) == sesudah_pertama

    assert panggilan == [
        "migrasi", "rebuild_siswa_unik", "migrate_params",
        "migrasi", "rebuild_siswa_unik", "migrate_params",
    ]

    with database.buka(path) as kon:
        for tabel, info_lama in metadata_lama.items():
            info_baru = [tuple(r) for r in kon.execute(
                f"PRAGMA table_info({tabel})"
            ).fetchall()]
            assert info_baru[:len(info_lama)] == info_lama

        assert _baris_dengan_kolom_lama(kon, metadata_lama) == baris_lama

        sesi = kon.execute(
            """SELECT id, level, selesai, direview, tujuan,
                      dikonfirmasi_guru, fingerprint_konfirmasi, putaran_id,
                      bagian_checkpoint, kunci_idempotensi, dibatalkan
               FROM sesi ORDER BY id"""
        ).fetchall()
        assert [r["level"] for r in sesi] == ["P3", "P5"]
        assert sesi[1]["direview"] == "2026-09-05 09:00:00"
        assert sesi[1]["selesai"] is None
        assert all(r["tujuan"] == "bebas" for r in sesi)
        assert all(r["dikonfirmasi_guru"] is None for r in sesi)
        assert all(r["fingerprint_konfirmasi"] is None for r in sesi)
        assert all(r["putaran_id"] is None for r in sesi)
        assert all(r["bagian_checkpoint"] is None for r in sesi)
        assert all(r["kunci_idempotensi"] is None for r in sesi)
        assert all(r["dibatalkan"] is None for r in sesi)

        assert {
            tabel: kon.execute(f'SELECT COUNT(*) FROM "{tabel}"').fetchone()[0]
            for tabel in TABEL_SIKLUS
        } == {tabel: 0 for tabel in TABEL_SIKLUS}
        assert kon.execute("PRAGMA foreign_key_check").fetchall() == []
        assert kon.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
