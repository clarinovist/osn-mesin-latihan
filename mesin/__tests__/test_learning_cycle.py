"""Kontrak data Fase 0 siklus belajar terpandu.

Status pedagogis belum direduksi di fase ini. Test mengunci bukti immutable,
provenance putaran, serta data yang dibutuhkan reducer Fase 1 untuk menolak
sesi stale, beda level, belum lengkap, belum dikonfirmasi, atau dibatalkan.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "siklus.db"
    database.siapkan(path)
    return path


def _sesi_satu_butir(kon, *, nama="Anak", level="P3", tujuan="bebas"):
    siswa_id = database.tambah_siswa(kon, nama, tingkat=level)
    sesi_id = database.buat_sesi(
        kon, siswa_id, seed=7, level=level, jumlah_soal=1
    )
    kon.execute("UPDATE sesi SET tujuan = ? WHERE id = ?", (tujuan, sesi_id))
    butir = database.isi_sesi(kon, sesi_id)[0]
    return siswa_id, sesi_id, butir


def _isi_dan_selesaikan(
    kon, sesi_id, butir, *, kode="K", malrule_id: str | None = "m-1"
):
    jawaban_id = database.simpan_jawaban(
        kon, butir["sesi_soal_id"], jawaban="0", cara="menghitung"
    )
    database.simpan_diagnosis(
        kon,
        jawaban_id,
        benar=False,
        kode_usulan=kode,
        kode_final=kode,
        malrule_id=malrule_id,
        alasan="cara lama",
    )
    database.tandai_selesai(kon, sesi_id)
    return jawaban_id


def test_sesi_manual_baru_tetap_bebas_tanpa_metadata_siklus_rekaan(db):
    with database.buka(db) as kon:
        siswa_id = database.tambah_siswa(kon, "Manual")
        sesi_id = database.buat_sesi(kon, siswa_id, seed=11, jumlah_soal=1)
        sesi = kon.execute(
            """SELECT tujuan, dikonfirmasi_guru, fingerprint_konfirmasi,
                      putaran_id, bagian_checkpoint, dibatalkan
               FROM sesi WHERE id = ?""",
            (sesi_id,),
        ).fetchone()

    assert dict(sesi) == {
        "tujuan": "bebas",
        "dikonfirmasi_guru": None,
        "fingerprint_konfirmasi": None,
        "putaran_id": None,
        "bagian_checkpoint": None,
        "dibatalkan": None,
    }


def test_buat_putaran_dan_tautkan_sesi_tidak_menyisakan_mutasi_parsial(db):
    with database.buka(db) as kon:
        siswa_id = database.tambah_siswa(kon, "Atomis", tingkat="P3")
        valid_1 = database.buat_sesi(kon, siswa_id, 1, level="P3", jumlah_soal=1)
        valid_2 = database.buat_sesi(kon, siswa_id, 2, level="P3", jumlah_soal=1)
        beda_level = database.buat_sesi(
            kon, siswa_id, 3, level="P4", jumlah_soal=1
        )

        with pytest.raises(ValueError, match="level sesi berbeda"):
            database.buat_putaran_fokus(
                kon, siswa_id, "P3", sesi_ids=[valid_1, beda_level]
            )
        assert kon.execute("SELECT COUNT(*) FROM putaran_fokus").fetchone()[0] == 0
        assert kon.execute(
            "SELECT COUNT(*) FROM sesi WHERE putaran_id IS NOT NULL"
        ).fetchone()[0] == 0

        putaran_id = database.buat_putaran_fokus(kon, siswa_id, "P3")
        with pytest.raises(ValueError, match="level sesi berbeda"):
            database.tautkan_sesi_putaran(
                kon, putaran_id, [valid_1, valid_1, beda_level]
            )
        assert kon.execute(
            "SELECT putaran_id FROM sesi WHERE id = ?", (valid_1,)
        ).fetchone()[0] is None

        database.tautkan_sesi_putaran(
            kon, putaran_id, [valid_1, valid_1, valid_2]
        )
        tertaut = kon.execute(
            "SELECT id FROM sesi WHERE putaran_id = ? ORDER BY id", (putaran_id,)
        ).fetchall()

    assert [baris["id"] for baris in tertaut] == [valid_1, valid_2]


def test_putaran_maksimal_dua_fokus_kanonis_dengan_provenance_multi_sesi(db):
    with database.buka(db) as kon:
        siswa_id = database.tambah_siswa(kon, "Fokus")
        siswa_lain = database.tambah_siswa(kon, "Fokus Lain")
        sesi_1 = database.buat_sesi(kon, siswa_id, 1, jumlah_soal=1)
        sesi_2 = database.buat_sesi(kon, siswa_id, 2, jumlah_soal=1)
        putaran_id = database.buat_putaran_fokus(kon, siswa_id, "P3")
        with pytest.raises(ValueError, match="bukan milik siswa"):
            database.buat_putaran_fokus(kon, siswa_lain, "P3", sesi_ids=[sesi_1])
        database.tautkan_sesi_putaran(kon, putaran_id, [sesi_1, sesi_2])

        fokus_1 = database.tambah_anggota_fokus(
            kon, putaran_id, "deret", "K", "salah-rasio", [sesi_1, sesi_2]
        )
        fokus_2 = database.tambah_anggota_fokus(
            kon, putaran_id, "umur", "H", None, [sesi_2]
        )

        with pytest.raises(ValueError, match="maksimal dua"):
            database.tambah_anggota_fokus(
                kon, putaran_id, "uang", "K", "salah-satuan", [sesi_1]
            )
        with pytest.raises(sqlite3.IntegrityError):
            database.tambah_anggota_fokus(
                kon, putaran_id, "deret", "K", "salah-rasio", [sesi_1]
            )

        sumber = kon.execute(
            """SELECT anggota_fokus_id, sesi_id FROM bukti_fokus
               ORDER BY anggota_fokus_id, sesi_id"""
        ).fetchall()

    assert [(r["anggota_fokus_id"], r["sesi_id"]) for r in sumber] == [
        (fokus_1, sesi_1),
        (fokus_1, sesi_2),
        (fokus_2, sesi_2),
    ]


def test_provenance_fokus_harus_berasal_dari_putaran_dan_siswa_yang_sama(db):
    with database.buka(db) as kon:
        siswa_1 = database.tambah_siswa(kon, "Satu")
        siswa_2 = database.tambah_siswa(kon, "Dua")
        putaran_id = database.buat_putaran_fokus(kon, siswa_1, "P3")
        sesi_tanpa_putaran = database.buat_sesi(kon, siswa_1, 3, jumlah_soal=1)
        sesi_siswa_lain = database.buat_sesi(kon, siswa_2, 4, jumlah_soal=1)
        database.tautkan_sesi_putaran(kon, putaran_id, [])

        with pytest.raises(ValueError, match="siswa dan putaran"):
            database.tambah_anggota_fokus(
                kon, putaran_id, "deret", "K", "m-1", [sesi_tanpa_putaran]
            )
        with pytest.raises(ValueError, match="siswa dan putaran"):
            database.tambah_anggota_fokus(
                kon, putaran_id, "deret", "K", "m-1", [sesi_siswa_lain]
            )


def test_konfirmasi_snapshot_mereproduksi_outcome_lama_setelah_koreksi(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        jawaban_id = _isi_dan_selesaikan(kon, sesi_id, butir)

        konfirmasi_1 = database.konfirmasi_hasil(
            kon,
            sesi_id,
            guru="guru",
            cek_pemahaman={butir["sesi_soal_id"]: "ragu"},
        )
        snapshot_lama = kon.execute(
            """SELECT nomor, template_id, jawaban, benar, kode_final,
                      malrule_id, dilewati, level_efektif, cek_pemahaman
               FROM snapshot_outcome WHERE konfirmasi_id = ?""",
            (konfirmasi_1,),
        ).fetchone()

        database.simpan_diagnosis(
            kon,
            jawaban_id,
            benar=True,
            kode_usulan="K",
            kode_final=None,
            malrule_id=None,
            alasan="dikoreksi guru",
            manual=True,
        )
        snapshot_setelah_koreksi = kon.execute(
            """SELECT nomor, template_id, jawaban, benar, kode_final,
                      malrule_id, dilewati, level_efektif, cek_pemahaman
               FROM snapshot_outcome WHERE konfirmasi_id = ?""",
            (konfirmasi_1,),
        ).fetchone()

    assert dict(snapshot_lama) == dict(snapshot_setelah_koreksi)
    assert snapshot_lama["kode_final"] == "K"
    assert snapshot_lama["malrule_id"] == "m-1"
    assert snapshot_lama["level_efektif"] == "P3"
    assert snapshot_lama["cek_pemahaman"] == "ragu"


def test_koreksi_diagnosis_menginvalidasi_cache_dan_nomor_konfirmasi_monoton(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        jawaban_id = _isi_dan_selesaikan(kon, sesi_id, butir)
        pertama = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        cache_sebelum = kon.execute(
            "SELECT dikonfirmasi_guru, fingerprint_konfirmasi FROM sesi WHERE id = ?",
            (sesi_id,),
        ).fetchone()

        database.simpan_diagnosis(
            kon, jawaban_id, True, "K", None, None, "hasil koreksi", True
        )
        cache_sesudah = kon.execute(
            "SELECT dikonfirmasi_guru, fingerprint_konfirmasi FROM sesi WHERE id = ?",
            (sesi_id,),
        ).fetchone()
        invalidasi = kon.execute(
            """SELECT jenis, konfirmasi_id FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'konfirmasi_dibatalkan'""",
            (sesi_id,),
        ).fetchall()

        kedua = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        urutan = kon.execute(
            """SELECT id, nomor_urut FROM konfirmasi_hasil
               WHERE sesi_id = ? ORDER BY nomor_urut""",
            (sesi_id,),
        ).fetchall()

    assert cache_sebelum["dikonfirmasi_guru"] is not None
    assert cache_sebelum["fingerprint_konfirmasi"]
    assert dict(cache_sesudah) == {
        "dikonfirmasi_guru": None,
        "fingerprint_konfirmasi": None,
    }
    assert len(invalidasi) == 1
    assert invalidasi[0]["konfirmasi_id"] == pertama
    assert [(r["id"], r["nomor_urut"]) for r in urutan] == [
        (pertama, 1),
        (kedua, 2),
    ]


def test_koreksi_jawaban_juga_menginvalidasi_konfirmasi(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        _isi_dan_selesaikan(kon, sesi_id, butir)
        konfirmasi_id = database.konfirmasi_hasil(kon, sesi_id, guru="guru")

        database.simpan_jawaban(
            kon, butir["sesi_soal_id"], jawaban="jawaban diperbaiki"
        )
        sesi = kon.execute(
            "SELECT dikonfirmasi_guru, fingerprint_konfirmasi FROM sesi WHERE id = ?",
            (sesi_id,),
        ).fetchone()
        invalidasi = kon.execute(
            """SELECT konfirmasi_id FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'konfirmasi_dibatalkan'""",
            (sesi_id,),
        ).fetchall()

    assert dict(sesi) == {
        "dikonfirmasi_guru": None,
        "fingerprint_konfirmasi": None,
    }
    assert [r["konfirmasi_id"] for r in invalidasi] == [konfirmasi_id]


def test_hanya_hasil_selesai_lengkap_dan_eksplisit_yang_bisa_dikonfirmasi(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        jawaban_id = database.simpan_jawaban(
            kon, butir["sesi_soal_id"], jawaban="0"
        )
        database.simpan_diagnosis(kon, jawaban_id, False, "K", "K", "m-1")

        # kode_final dan direview bukan bukti, dan sesi belum selesai.
        kon.execute(
            "UPDATE sesi SET direview = datetime('now') WHERE id = ?", (sesi_id,)
        )
        with pytest.raises(ValueError, match="belum selesai"):
            database.konfirmasi_hasil(kon, sesi_id, guru="guru")

        database.tandai_selesai(kon, sesi_id)
        kon.execute("DELETE FROM diagnosis WHERE jawaban_id = ?", (jawaban_id,))
        with pytest.raises(ValueError, match="outcome belum lengkap"):
            database.konfirmasi_hasil(kon, sesi_id, guru="guru")

        konfirmasi_id = database.konfirmasi_hasil(
            kon,
            sesi_id,
            guru="guru",
            dilewati={butir["sesi_soal_id"]},
        )
        snapshot = kon.execute(
            "SELECT dilewati, kode_final FROM snapshot_outcome WHERE konfirmasi_id = ?",
            (konfirmasi_id,),
        ).fetchone()

    assert snapshot["dilewati"] == 1
    assert snapshot["kode_final"] is None


@pytest.mark.parametrize(
    ("benar", "kode_final", "malrule_id"),
    [
        (False, None, None),
        (True, "K", None),
        (True, None, "m-1"),
    ],
)
def test_konfirmasi_menolak_outcome_non_dilewati_yang_kontradiktif(
    db, benar, kode_final, malrule_id
):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        jawaban_id = database.simpan_jawaban(
            kon, butir["sesi_soal_id"], jawaban="0"
        )
        database.simpan_diagnosis(
            kon,
            jawaban_id,
            benar=benar,
            kode_usulan="K",
            kode_final=kode_final,
            malrule_id=malrule_id,
        )
        database.tandai_selesai(kon, sesi_id)

        with pytest.raises(ValueError, match="outcome belum lengkap"):
            database.konfirmasi_hasil(kon, sesi_id, guru="guru")

        assert kon.execute("SELECT COUNT(*) FROM konfirmasi_hasil").fetchone()[0] == 0


@pytest.mark.parametrize("kode_final", ["N", "T"])
def test_konfirmasi_dan_snapshot_raw_sql_menerima_n_t_sebagai_salah_berkode(
    db, kode_final
):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        _isi_dan_selesaikan(
            kon, sesi_id, butir, kode=kode_final, malrule_id=None
        )
        konfirmasi_service = database.konfirmasi_hasil(
            kon, sesi_id, guru="guru"
        )
        snapshot_service = kon.execute(
            """SELECT benar, kode_final FROM snapshot_outcome
               WHERE konfirmasi_id = ?""",
            (konfirmasi_service,),
        ).fetchone()

        sesi_raw = database.buat_sesi(
            kon,
            kon.execute("SELECT siswa_id FROM sesi WHERE id = ?", (sesi_id,)).fetchone()[0],
            seed=17,
            jumlah_soal=1,
        )
        butir_raw = database.isi_sesi(kon, sesi_raw)[0]
        konfirmasi_id = kon.execute(
            """INSERT INTO konfirmasi_hasil
                   (sesi_id, nomor_urut, guru, fingerprint)
               VALUES (?, 1, 'guru', ?)""",
            (sesi_raw, kode_final),
        ).lastrowid
        kon.execute(
            """INSERT INTO snapshot_outcome
                   (konfirmasi_id, sesi_soal_id, nomor, template_id, jawaban,
                    benar, kode_final, dilewati, level_efektif)
               VALUES (?, ?, 1, ?, '', 0, ?, 0, 'P3')""",
            (
                konfirmasi_id,
                butir_raw["sesi_soal_id"],
                butir_raw["template_id"],
                kode_final,
            ),
        )

    assert dict(snapshot_service) == {"benar": 0, "kode_final": kode_final}
    assert konfirmasi_id is not None


def test_snapshot_raw_sql_menolak_outcome_kontradiktif(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        konfirmasi_id = kon.execute(
            """INSERT INTO konfirmasi_hasil
                   (sesi_id, nomor_urut, guru, fingerprint)
               VALUES (?, 1, 'guru', 'raw')""",
            (sesi_id,),
        ).lastrowid
        sql = """INSERT INTO snapshot_outcome
                    (konfirmasi_id, sesi_soal_id, nomor, template_id, jawaban,
                     benar, kode_final, malrule_id, dilewati, level_efektif)
                 VALUES (?, ?, ?, ?, '', ?, ?, ?, 0, 'P3')"""
        kasus = [
            (1, 0, None, None),
            (2, 1, "K", None),
            (3, 1, None, "m-1"),
        ]
        for nomor, benar, kode_final, malrule_id in kasus:
            with pytest.raises(sqlite3.IntegrityError):
                kon.execute(
                    sql,
                    (
                        konfirmasi_id,
                        butir["sesi_soal_id"] + nomor,
                        nomor,
                        butir["template_id"],
                        benar,
                        kode_final,
                        malrule_id,
                    ),
                )


def test_konfirmasi_identik_aktif_idempoten_tanpa_bukti_duplikat(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        _isi_dan_selesaikan(kon, sesi_id, butir)

        pertama = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        kedua = database.konfirmasi_hasil(kon, sesi_id, guru="guru-lain")
        jumlah = {
            "konfirmasi": kon.execute(
                "SELECT COUNT(*) FROM konfirmasi_hasil WHERE sesi_id = ?", (sesi_id,)
            ).fetchone()[0],
            "snapshot": kon.execute(
                """SELECT COUNT(*) FROM snapshot_outcome so
                   JOIN konfirmasi_hasil kh ON kh.id = so.konfirmasi_id
                   WHERE kh.sesi_id = ?""",
                (sesi_id,),
            ).fetchone()[0],
            "event": kon.execute(
                """SELECT COUNT(*) FROM kejadian_belajar
                   WHERE sesi_id = ? AND jenis = 'hasil_dikonfirmasi'""",
                (sesi_id,),
            ).fetchone()[0],
        }

    assert kedua == pertama
    assert jumlah == {"konfirmasi": 1, "snapshot": 1, "event": 1}


def test_invalidasi_memilih_konfirmasi_aktif_terbaru_dan_urutan_tetap_monoton(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        jawaban_id = _isi_dan_selesaikan(kon, sesi_id, butir)
        pertama = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        fingerprint = kon.execute(
            "SELECT fingerprint_konfirmasi FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()[0]
        terbaru = kon.execute(
            """INSERT INTO konfirmasi_hasil
                   (sesi_id, nomor_urut, guru, fingerprint)
               VALUES (?, 2, 'guru', ?)""",
            (sesi_id, fingerprint),
        ).lastrowid

        database.simpan_diagnosis(
            kon, jawaban_id, True, "K", None, None, "hasil koreksi", True
        )
        invalidasi = kon.execute(
            """SELECT konfirmasi_id FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'konfirmasi_dibatalkan'
               ORDER BY id DESC LIMIT 1""",
            (sesi_id,),
        ).fetchone()[0]
        ketiga = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        nomor_ketiga = kon.execute(
            "SELECT nomor_urut FROM konfirmasi_hasil WHERE id = ?", (ketiga,)
        ).fetchone()[0]

    assert terbaru != pertama
    assert invalidasi == terbaru
    assert nomor_ketiga == 3


def test_sesi_dibatalkan_tidak_bisa_dikonfirmasi_dan_snapshot_lama_bertahan(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="evaluasi")
        _isi_dan_selesaikan(kon, sesi_id, butir)
        konfirmasi_id = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        database.batalkan_sesi(kon, sesi_id, alasan="lembar rusak")

        with pytest.raises(ValueError, match="dibatalkan"):
            database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        jumlah_snapshot = kon.execute(
            "SELECT COUNT(*) FROM snapshot_outcome WHERE konfirmasi_id = ?",
            (konfirmasi_id,),
        ).fetchone()[0]
        batal = kon.execute(
            "SELECT dibatalkan FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()[0]

    assert batal is not None
    assert jumlah_snapshot == 1


def test_sesi_berbukti_tidak_bisa_hard_delete_tapi_sesi_biasa_tetap_bisa(db):
    with database.buka(db) as kon:
        siswa_id, sesi_bukti, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        _isi_dan_selesaikan(kon, sesi_bukti, butir)
        database.konfirmasi_hasil(kon, sesi_bukti, guru="guru")

        with pytest.raises(sqlite3.IntegrityError):
            database.hapus_sesi(kon, sesi_bukti)
        with pytest.raises(sqlite3.IntegrityError):
            kon.execute("DELETE FROM sesi WHERE id = ?", (sesi_bukti,))
        assert kon.execute(
            "SELECT COUNT(*) FROM sesi WHERE id = ?", (sesi_bukti,)
        ).fetchone()[0] == 1

        sesi_biasa = database.buat_sesi(kon, siswa_id, 99, jumlah_soal=1)
        assert database.hapus_sesi(kon, sesi_biasa) is True


def test_data_membedakan_bukti_level_aktif_dan_kondisi_yang_harus_ditolak_reducer(db):
    with database.buka(db) as kon:
        siswa_id, sesi_id, butir = _sesi_satu_butir(
            kon, nama="Naik", level="P3", tujuan="pemetaan"
        )
        _isi_dan_selesaikan(kon, sesi_id, butir)
        konfirmasi_id = database.konfirmasi_hasil(kon, sesi_id, guru="guru")
        database.ganti_level(kon, siswa_id, "P4")

        data = kon.execute(
            """SELECT s.level AS level_sesi, w.tingkat AS level_aktif,
                      s.selesai, s.dikonfirmasi_guru, s.dibatalkan,
                      COUNT(so.id) AS jumlah_snapshot
               FROM sesi s
               JOIN siswa w ON w.id = s.siswa_id
               LEFT JOIN konfirmasi_hasil kh ON kh.sesi_id = s.id
               LEFT JOIN snapshot_outcome so ON so.konfirmasi_id = kh.id
               WHERE s.id = ? GROUP BY s.id""",
            (sesi_id,),
        ).fetchone()
        perubahan = kon.execute(
            """SELECT jenis, data FROM kejadian_belajar
               WHERE siswa_id = ? AND jenis = 'diganti_level'""",
            (siswa_id,),
        ).fetchone()
        snapshot_level = kon.execute(
            "SELECT level_efektif FROM snapshot_outcome WHERE konfirmasi_id = ?",
            (konfirmasi_id,),
        ).fetchone()[0]

    assert data["level_sesi"] == snapshot_level == "P3"
    assert data["level_aktif"] == "P4"
    assert data["selesai"] is not None
    assert data["dikonfirmasi_guru"] is not None
    assert data["dibatalkan"] is None
    assert data["jumlah_snapshot"] == 1
    assert perubahan["jenis"] == "diganti_level"
    assert '"level_lama": "P3"' in perubahan["data"]
    assert '"level_baru": "P4"' in perubahan["data"]


def test_kejadian_diganti_level_dapat_merujuk_putaran_lama(db):
    with database.buka(db) as kon:
        siswa_id = database.tambah_siswa(kon, "Putaran lama", tingkat="P3")
        putaran_id = database.buat_putaran_fokus(kon, siswa_id, "P3")

        database.ganti_level(kon, siswa_id, "P4")
        kejadian = kon.execute(
            """SELECT putaran_id, jenis FROM kejadian_belajar
               WHERE siswa_id = ? AND jenis = 'diganti_level'""",
            (siswa_id,),
        ).fetchone()

    assert kejadian["putaran_id"] == putaran_id
    assert kejadian["jenis"] == "diganti_level"


def test_tabel_bukti_append_only(db):
    with database.buka(db) as kon:
        _, sesi_id, butir = _sesi_satu_butir(kon, tujuan="pemetaan")
        _isi_dan_selesaikan(kon, sesi_id, butir)
        konfirmasi_id = database.konfirmasi_hasil(kon, sesi_id, guru="guru")

        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            kon.execute(
                "UPDATE konfirmasi_hasil SET nomor_urut = 9 WHERE id = ?",
                (konfirmasi_id,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            kon.execute(
                "DELETE FROM snapshot_outcome WHERE konfirmasi_id = ?",
                (konfirmasi_id,),
            )
