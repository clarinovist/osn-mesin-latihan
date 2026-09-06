"""Uji intervensi dan generator tahap siklus belajar."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import interventions  # noqa: E402
import topics  # noqa: E402
from learning_cycle import (  # noqa: E402
    Intervensi,
    PutaranFokus,
    RencanaBelajar,
    StatusFokus,
    rencana_berikutnya,
)


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "siklus-generator.db"
    database.siapkan(path)
    return path


def _rencana(tindakan, fokus=(), *, bagian=None, probe=0):
    status = tuple(StatusFokus(k, "perlu_dipelajari") for k in fokus)
    putaran = PutaranFokus(1, "P3", status)
    return RencanaBelajar(
        tindakan,
        "uji",
        putaran=putaran,
        kandidat=tuple(fokus),
        jumlah_probe_minimum=probe,
        bagian_checkpoint=bagian,
    )


def test_intervensi_k_memisahkan_instruksi_orang_tua_dan_anak():
    hasil = interventions.untuk_fokus(("deret_aritmetika", "K", "m1"))

    assert hasil.pendekatan_id
    assert "orang tua" not in hasil.strategi_anak.lower()
    assert hasil.instruksi_orang_tua
    assert hasil.contoh_terbimbing


def test_intervensi_k_menyediakan_pendekatan_alternatif_beridentitas_unik():
    pilihan = interventions.pilihan_untuk_fokus(
        ("deret_aritmetika", "K", "m1")
    )

    assert len(pilihan) >= 2
    assert len({item.pendekatan_id for item in pilihan}) == len(pilihan)
    assert all(item.tersedia for item in pilihan)


def test_intervensi_k_tanpa_kartu_gagal_terlihat(monkeypatch):
    monkeypatch.setattr(interventions.rumus, "kartu_untuk", lambda _tid: None)

    hasil = interventions.untuk_fokus(("tak_ada", "K", "m1"))

    assert hasil.tersedia is False
    assert "belum tersedia" in hasil.instruksi_orang_tua.lower()


@pytest.mark.parametrize("kode", list("BHENT"))
def test_intervensi_kode_non_k_tetap_memberi_tindakan(kode):
    hasil = interventions.untuk_fokus(("deret_aritmetika", kode, None))

    assert hasil.tersedia is True
    assert hasil.instruksi_orang_tua
    assert hasil.strategi_anak


def test_pemetaan_pertama_15_soal_balanced_lintas_topik(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Pemetaan", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        rencana = _rencana("pemetaan")
        sesi = database.buat_sesi_dari_rencana(
            kon, siswa, rencana, putaran_id=putaran, seed=101
        )
        template = [b["template_id"] for b in database.isi_sesi(kon, sesi)]

    assert len(template) == 15
    assert len({topics.pemilik_template(t) for t in template}) >= 4


def test_pemetaan_lanjutan_membawa_maksimal_lima_anchor(db):
    anchor = tuple((t, "K", None) for t in (
        "deret_aritmetika", "soal_umur", "median_modus",
        "keliling_luas_datar", "fpb_dua_bilangan", "aturan_kali",
    ))
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anchor", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi = database.buat_sesi_dari_rencana(
            kon, siswa, _rencana("pemetaan", anchor), putaran_id=putaran, seed=102
        )
        template = [b["template_id"] for b in database.isi_sesi(kon, sesi)]

    assert len(template) == 15
    assert set(k[0] for k in anchor[:5]) <= set(template)
    assert anchor[5][0] not in template[:5]


def test_anchor_pemetaan_memakai_parameter_baru_dan_tidak_meruntuhkan_malrule(db):
    fokus = (
        ("deret_aritmetika", "K", "m1"),
        ("deret_aritmetika", "K", "m2"),
    )
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anchor kanonis", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        awal = database.buat_sesi_dari_rencana(
            kon, siswa, _rencana("pemetaan"), putaran_id=putaran, seed=77
        )
        lanjutan = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("pemetaan", fokus),
            putaran_id=putaran,
            seed=77,
            occurrence=2,
        )
        awal_tt = {
            b["tanda_tangan"]
            for b in kon.execute(
                """SELECT so.tanda_tangan FROM soal so
                   JOIN sesi_soal ss ON ss.soal_id = so.id
                   WHERE ss.sesi_id = ? AND so.template_id = 'deret_aritmetika'""",
                (awal,),
            )
        }
        lanjut_tt = {
            b["tanda_tangan"]
            for b in kon.execute(
                """SELECT so.tanda_tangan FROM soal so
                   JOIN sesi_soal ss ON ss.soal_id = so.id
                   WHERE ss.sesi_id = ? AND so.template_id = 'deret_aritmetika'""",
                (lanjutan,),
            )
        }
        data = kon.execute(
            """SELECT data FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'sesi_dibuat'""",
            (lanjutan,),
        ).fetchone()["data"]

    assert len(lanjut_tt) == 2
    assert awal_tt.isdisjoint(lanjut_tt)
    assert '"m1"' in data and '"m2"' in data


def test_penguatan_dan_evaluasi_memenuhi_komposisi_dua_fokus(db):
    fokus = (
        ("deret_aritmetika", "K", "m1"),
        ("soal_umur", "K", "m2"),
    )
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Komposisi", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        penguatan = database.buat_sesi_dari_rencana(
            kon, siswa, _rencana("penguatan", fokus), putaran_id=putaran, seed=201
        )
        evaluasi = database.buat_sesi_dari_rencana(
            kon, siswa, _rencana("evaluasi", fokus, probe=4), putaran_id=putaran, seed=202
        )
        p = [b["template_id"] for b in database.isi_sesi(kon, penguatan)]
        e = [b["template_id"] for b in database.isi_sesi(kon, evaluasi)]

    assert len(p) == 10
    assert p.count(fokus[0][0]) == 5 and p.count(fokus[1][0]) == 5
    assert len(e) == 10
    assert e.count(fokus[0][0]) >= 4 and e.count(fokus[1][0]) >= 4


def test_latihan_terbimbing_memberi_satu_contoh_per_kunci_fokus(db):
    fokus = (
        ("deret_aritmetika", "K", "m1"),
        ("deret_aritmetika", "K", "m2"),
    )
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Terbimbing", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("latihan_terbimbing", fokus),
            putaran_id=putaran,
            seed=220,
        )
        jumlah = len(database.isi_sesi(kon, sesi))
        metadata = kon.execute(
            """SELECT data FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'sesi_dibuat'""",
            (sesi,),
        ).fetchone()["data"]

    assert jumlah == 2
    assert '"m1"' in metadata and '"m2"' in metadata


def test_checkpoint_dua_bagian_membawa_minimum_probe_per_fokus(db):
    fokus = (("deret_aritmetika", "K", "m1"),)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Checkpoint", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("checkpoint", fokus, bagian=1, probe=3),
            putaran_id=putaran,
            seed=301,
            occurrence=2,
        )
        sesi_2 = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("checkpoint", fokus, bagian=2, probe=3),
            putaran_id=putaran,
            seed=302,
            occurrence=2,
        )
        info = kon.execute(
            "SELECT tujuan, bagian_checkpoint FROM sesi WHERE id = ?", (sesi,)
        ).fetchone()
        template = [b["template_id"] for b in database.isi_sesi(kon, sesi)]
        template_2 = [b["template_id"] for b in database.isi_sesi(kon, sesi_2)]
        event = kon.execute(
            """SELECT data FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'sesi_dibuat'""",
            (sesi,),
        ).fetchone()

    assert len(template) == len(template_2) == 10
    assert template.count(fokus[0][0]) + template_2.count(fokus[0][0]) >= 3
    assert '"target_per_nomor"' in event["data"]
    assert dict(info) == {"tujuan": "checkpoint", "bagian_checkpoint": 1}


def test_metadata_idempotensi_tersedia_pada_database_baru_dan_migrasi_ulang(db):
    database.siapkan(db)
    with database.buka(db) as kon:
        kolom = {r["name"] for r in kon.execute("PRAGMA table_info(sesi)")}
        indeks = {
            r["name"] for r in kon.execute("PRAGMA index_list(sesi)").fetchall()
        }

    assert "kunci_idempotensi" in kolom
    assert "idx_sesi_siklus_aktif" in indeks


def test_snapshot_menyimpan_target_kanonis_per_butir(db):
    fokus = (
        ("deret_aritmetika", "K", "m1"),
        ("deret_aritmetika", "K", "m2"),
    )
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Target snapshot", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("evaluasi", fokus, probe=4),
            putaran_id=putaran,
            seed=350,
        )
        for butir in database.isi_sesi(kon, sesi):
            jawaban_id = database.simpan_jawaban(
                kon, butir["sesi_soal_id"], jawaban=butir["kunci"], cara="hitung"
            )
            database.simpan_diagnosis(
                kon, jawaban_id, True, None, None
            )
        database.tandai_selesai(kon, sesi)
        konfirmasi = database.konfirmasi_hasil(kon, sesi, guru="guru")
        target = kon.execute(
            """SELECT target_template_id, target_kode_intervensi,
                      target_malrule_id
               FROM snapshot_outcome
               WHERE konfirmasi_id = ? AND target_template_id IS NOT NULL
               ORDER BY nomor""",
            (konfirmasi,),
        ).fetchall()

    assert len(target) == 8
    assert {tuple(baris) for baris in target} == set(fokus)


def test_double_submit_idempoten_batal_lalu_buat_ulang_dan_occurrence_baru(db):
    fokus = (("deret_aritmetika", "K", "m1"),)
    rencana = _rencana("evaluasi", fokus, probe=4)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Idempoten", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        pertama = database.buat_sesi_dari_rencana(
            kon, siswa, rencana, putaran_id=putaran, seed=401, occurrence=1
        )
        sama = database.buat_sesi_dari_rencana(
            kon, siswa, rencana, putaran_id=putaran, seed=999, occurrence=1
        )
        database.batalkan_sesi(kon, pertama, "ulang")
        ulang = database.buat_sesi_dari_rencana(
            kon, siswa, rencana, putaran_id=putaran, seed=402, occurrence=1
        )
        berikutnya = database.buat_sesi_dari_rencana(
            kon, siswa, rencana, putaran_id=putaran, seed=403, occurrence=2
        )

    assert sama == pertama
    assert ulang != pertama
    assert berikutnya not in {pertama, ulang}


def test_evaluasi_memakai_soal_baru_dari_penguatannya(db):
    fokus = (("deret_aritmetika", "K", "m1"),)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Soal baru", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        penguatan = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("penguatan", fokus),
            putaran_id=putaran,
            seed=501,
        )
        evaluasi = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("evaluasi", fokus, probe=4),
            putaran_id=putaran,
            seed=502,
        )
        tt_penguat = {
            baris["tanda_tangan"]
            for baris in kon.execute(
                """SELECT so.tanda_tangan FROM soal so
                   JOIN sesi_soal ss ON ss.soal_id = so.id
                   WHERE ss.sesi_id = ? AND so.template_id = ?""",
                (penguatan, fokus[0][0]),
            )
        }
        tt_evaluasi = {
            baris["tanda_tangan"]
            for baris in kon.execute(
                """SELECT so.tanda_tangan FROM soal so
                   JOIN sesi_soal ss ON ss.soal_id = so.id
                   WHERE ss.sesi_id = ? AND so.template_id = ?""",
                (evaluasi, fokus[0][0]),
            )
        }

    assert tt_penguat.isdisjoint(tt_evaluasi)


def test_mixed_maintenance_tidak_menjadi_bukti_pemetaan(db):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Maintenance", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi = database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("mixed_maintenance"),
            putaran_id=putaran,
            seed=450,
        )
        tujuan = kon.execute(
            "SELECT tujuan FROM sesi WHERE id = ?", (sesi,)
        ).fetchone()["tujuan"]
        kon.execute(
            """UPDATE sesi
               SET selesai = '2026-09-01 09:00:00',
                   dikonfirmasi_guru = '2026-09-01 10:00:00'
               WHERE id = ?""",
            (sesi,),
        )
        bukti = database.muat_bukti_siklus(kon, siswa)

    assert tujuan == "maintenance"
    assert rencana_berikutnya(bukti, siswa, date(2026, 9, 2)).tindakan == "pemetaan"


def test_sumber_sesi_harus_milik_siswa_dan_putaran_yang_sama(db):
    fokus = (("deret_aritmetika", "K", "m1"),)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Pemilik", tingkat="P3")
        lain = database.tambah_siswa(kon, "Asing", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        sesi_asing = database.buat_sesi(kon, lain, seed=88, jumlah_soal=1)
        rencana = RencanaBelajar(
            "penguatan",
            "uji",
            putaran=_rencana("penguatan", fokus).putaran,
            sesi_id=sesi_asing,
            kandidat=fokus,
        )
        with pytest.raises(ValueError, match="sumber sesi"):
            database.buat_sesi_dari_rencana(
                kon, siswa, rencana, putaran_id=putaran, seed=89
            )


def test_pengenalan_selesai_idempoten_dan_harus_fokus_t_sah(db):
    fokus = ("deret_aritmetika", "T", None)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Pengenalan", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        with pytest.raises(ValueError, match="belum dibuat"):
            database.tandai_pengenalan_selesai(
                kon, siswa, putaran, fokus, "kenalkan-contoh-awal"
            )
        database.buat_sesi_dari_rencana(
            kon,
            siswa,
            _rencana("pengenalan", (fokus,)),
            putaran_id=putaran,
            seed=601,
        )
        with pytest.raises(ValueError, match="pendekatan"):
            database.tandai_pengenalan_selesai(
                kon, siswa, putaran, fokus, "apa-saja"
            )
        database.tandai_pengenalan_selesai(
            kon, siswa, putaran, fokus, "kenalkan-contoh-awal"
        )
        database.tandai_pengenalan_selesai(
            kon, siswa, putaran, fokus, "kenalkan-contoh-awal"
        )
        jumlah = kon.execute(
            """SELECT COUNT(*) FROM kejadian_belajar
               WHERE putaran_id = ? AND jenis = 'pengenalan_selesai'""",
            (putaran,),
        ).fetchone()[0]
        with pytest.raises(ValueError):
            database.tandai_pengenalan_selesai(
                kon, siswa, putaran, (fokus[0], "K", None), "salah"
            )

    assert jumlah == 1


def test_pembuatan_menolak_siswa_putaran_fokus_dan_bagian_asing(db):
    fokus = (("deret_aritmetika", "K", "m1"),)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Satu", tingkat="P3")
        lain = database.tambah_siswa(kon, "Dua", tingkat="P3")
        putaran = database.buat_putaran_fokus(kon, lain, "P3")
        with pytest.raises(ValueError):
            database.buat_sesi_dari_rencana(
                kon, siswa, _rencana("evaluasi", fokus), putaran_id=putaran, seed=1
            )
        putaran_sah = database.buat_putaran_fokus(kon, siswa, "P3")
        with pytest.raises(ValueError):
            database.buat_sesi_dari_rencana(
                kon,
                siswa,
                _rencana("evaluasi", (("template-asing", "K", None),)),
                putaran_id=putaran_sah,
                seed=2,
            )
        with pytest.raises(ValueError):
            database.buat_sesi_dari_rencana(
                kon,
                siswa,
                _rencana("checkpoint", fokus, bagian=None),
                putaran_id=putaran_sah,
                seed=3,
            )
