"""Transisi aksi fokus melalui endpoint sungguhan."""
import urllib.parse

import pytest
import database
import interventions
from learning_cycle import rencana_berikutnya
from test_learning_cycle_http import server, _siapkan_putaran_fokus
from test_learning_cycle_routes import _post


def _aksi(s, siswa, **data):
    return _post(s, f"/siklus/{siswa}/aksi", urllib.parse.urlencode(data).encode())[0]


def test_override_awal_bisa_diintervensi_tanpa_kembali_ke_fokus_lama(server):
    s, ids = server
    siswa = ids["siswa_buat"]
    with s.buka() as kon:
        putaran, _ = _siapkan_putaran_fokus(kon, siswa)
    fokus = ("soal_umur", "H", None)
    assert _aksi(s, siswa, aksi="ubah_fokus", template_id=fokus[0], kode_intervensi="H") == 303
    pendekatan = interventions.pilihan_untuk_fokus(fokus)[0].pendekatan_id
    assert _aksi(s, siswa, aksi="intervensi_selesai", putaran_id=putaran,
                 template_id=fokus[0], kode_intervensi="H", pendekatan_id=pendekatan) == 303
    with s.buka() as kon:
        rencana = rencana_berikutnya(database.muat_bukti_siklus(kon, siswa), siswa)
    assert rencana.tindakan == "latihan_terbimbing"
    assert rencana.kandidat == (fokus,)
    with s.buka() as kon:
        assert fokus in dict(database.muat_bukti_siklus(kon, siswa).pendekatan_tersedia)


@pytest.mark.parametrize("override", [False, True])
def test_fokus_otomatis_dipersistenkan_saat_intervensi(server, override):
    s, ids = server
    siswa = ids["siswa_buat"]
    with s.buka() as kon:
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        for nomor in range(3):
            sesi = database.buat_sesi(kon, siswa, seed=920 + nomor, jumlah_soal=1)
            kon.execute("UPDATE sesi SET tujuan = 'pemetaan', putaran_id = ?, tanggal = ?, selesai = ? WHERE id = ?", (putaran, f"2026-01-0{nomor+1}", f"2026-01-0{nomor+1}", sesi))
            butir = database.isi_sesi(kon, sesi)[0]
            jid = database.simpan_jawaban(kon, butir["sesi_soal_id"], "0")
            database.simpan_diagnosis(kon, jid, False, "K", "K")
            database.konfirmasi_hasil(kon, sesi, guru="guru")
        rencana = rencana_berikutnya(database.muat_bukti_siklus(kon, siswa), siswa)
        assert rencana.putaran is not None
        fokus = rencana.putaran.fokus[0].kunci
    if override:
        fokus = ("soal_umur", "H", None)
        assert _aksi(s, siswa, aksi="ubah_fokus", template_id=fokus[0], kode_intervensi=fokus[1]) == 303
    pendekatan = interventions.pilihan_untuk_fokus(fokus)[0].pendekatan_id
    assert _aksi(s, siswa, aksi="intervensi_selesai", putaran_id=putaran,
                 template_id=fokus[0], kode_intervensi=fokus[1], pendekatan_id=pendekatan) == 303
    with s.buka() as kon:
        assert kon.execute("SELECT COUNT(*) FROM anggota_fokus WHERE putaran_id = ?", (putaran,)).fetchone()[0] == 1
        assert kon.execute("SELECT COUNT(*) FROM bukti_fokus").fetchone()[0] == 3
        anggota = kon.execute("SELECT template_id, kode_intervensi, malrule_id_kanonis FROM anggota_fokus WHERE putaran_id = ?", (putaran,)).fetchone()
        assert tuple(anggota) == (fokus[0], fokus[1], fokus[2] or "")
        bukti = database.muat_bukti_siklus(kon, siswa)
        assert fokus in dict(bukti.pendekatan_tersedia)
        assert rencana_berikutnya(bukti, siswa).tindakan == "latihan_terbimbing"


def test_pengenalan_selesai_tersambung_ke_endpoint(server):
    from learning_cycle import RencanaBelajar, PutaranFokus

    s, ids = server
    siswa = ids["siswa_buat"]
    fokus = ("deret_aritmetika", "T", None)
    with s.buka() as kon:
        putaran = database.buat_putaran_fokus(kon, siswa, "P3")
        rencana = RencanaBelajar("pengenalan", "uji", putaran=PutaranFokus(putaran, "P3", ()), kandidat=(fokus,))
        sesi = database.buat_sesi_dari_rencana(kon, siswa, rencana, putaran_id=putaran, seed=931)
    pendekatan = interventions.pilihan_untuk_fokus(fokus)[0].pendekatan_id
    assert _aksi(s, siswa, aksi="pengenalan_selesai", putaran_id=putaran,
                 template_id=fokus[0], kode_intervensi="T", pendekatan_id=pendekatan) == 303
    with s.buka() as kon:
        assert kon.execute("SELECT COUNT(*) FROM kejadian_belajar WHERE jenis = 'pengenalan_selesai'").fetchone()[0] == 1


def test_occurrence_checkpoint_kedua_bagian_dan_pasangan_berikutnya(server):
    from learning_cycle import RencanaBelajar, PutaranFokus
    from learning_cycle_service import _occurrence_berikutnya

    s, ids = server
    with s.buka() as kon:
        siswa = ids["siswa_buat"]
        putaran, fokus = _siapkan_putaran_fokus(kon, siswa)
        for occurrence in (1, 2):
            for bagian in (1, 2):
                rencana = RencanaBelajar(
                    "checkpoint", "uji", putaran=PutaranFokus(putaran, "P3", ()),
                    kandidat=(fokus,), bagian_checkpoint=bagian,
                )
                assert _occurrence_berikutnya(kon, putaran, rencana) == occurrence
                sesi = database.buat_sesi_dari_rencana(
                    kon, siswa, rencana, putaran_id=putaran,
                    seed=1000 + occurrence * 10 + bagian, occurrence=occurrence,
                )
                database.tandai_selesai(kon, sesi)
                lewat = {b["sesi_soal_id"] for b in database.isi_sesi(kon, sesi)}
                database.konfirmasi_hasil(kon, sesi, guru="guru", dilewati=lewat)


@pytest.mark.parametrize("kode", ["", "KH", "ENT", "Z"])
def test_override_menolak_kode_tidak_sah_tanpa_event(server, kode):
    s, ids = server
    with s.buka() as kon:
        _siapkan_putaran_fokus(kon, ids["siswa_buat"])
        sebelum = tuple(kon.iterdump())
    assert _aksi(s, ids["siswa_buat"], aksi="ubah_fokus", template_id="soal_umur", kode_intervensi=kode) == 400
    with s.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
