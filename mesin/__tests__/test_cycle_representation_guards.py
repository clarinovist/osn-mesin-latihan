"""Regresi reviewer pada kekambuhan, dilewati, dan carry antarputaran."""
from dataclasses import replace
from datetime import date
import pytest
import learning_cycle as lc
from cycle_representations import bukti_satu_representasi
from test_cycle_representations import sesi, bukti, PUTARAN


@pytest.mark.parametrize("ubah", ({"tujuan": "bebas", "putaran_id": None},
    {"siswa_id": 999}, {"level": "P4"}, {"putaran_id": 999},
    {"dibatalkan": "batal"}, {"dikonfirmasi": None}, {"selesai": None}))
def test_bukti_tidak_sah_tidak_memicu_kambuh(ubah):
    sumber = bukti(sesi(1, "korek-v2"), *(sesi(i, "korek-v2", tujuan="checkpoint", jumlah=2,
        bagian_checkpoint=i-1, occurrence=1) for i in (2, 3)))
    hari = date(2026, 9, 10)
    assert lc.rencana_berikutnya(sumber, 1, hari).tindakan == "tunggu_checkpoint"
    manual = replace(sesi(4, tujuan="pemetaan", benar=False), **ubah)
    hasil = lc.rencana_berikutnya(replace(sumber, sesi=(*sumber.sesi, manual)), 1, hari)
    harapan = ("konfirmasi_hasil" if "dikonfirmasi" in ubah else
               "lanjutkan_sesi" if "selesai" in ubah else "tunggu_checkpoint")
    assert hasil.tindakan == harapan, hasil


def test_sesi_dilewati_beda_mode_tetap_ada():
    lewat = replace(sesi(2, "korek-v2", tujuan="pemetaan"), outcomes=tuple(
        replace(o, benar=None, kode_final=None, dilewati=True) for o in sesi(2, "korek-v2").outcomes))
    sumber = bukti(sesi(1, tujuan="pemetaan"), lewat)
    assert tuple(s.id for s in bukti_satu_representasi(sumber, PUTARAN).sesi) == (1, 2)


def test_carry_tidak_menghidupkan_lagi_bukti_setelah_kelompok_ambigu():
    from test_cycle_representations import FOKUS, outcome
    pasangan = ("deret_aritmetika", "H", None)
    putaran_lama = replace(PUTARAN, fokus=(pasangan, FOKUS))
    putaran_baru = replace(putaran_lama, id=2, dibuka=date(2026, 9, 2))
    tutup = lc.KejadianSiklus(1, "putaran_ditutup", date(2026, 9, 2), putaran_id=1)
    carry = lc.KejadianSiklus(2, "putaran_kambuh_dibuka", date(2026, 9, 2), putaran_id=2,
        data=(("putaran_lama", 1), ("fokus_diteruskan", (FOKUS,))))
    baru = replace(sesi(3), putaran_id=2, outcomes=(outcome(), outcome(),
        outcome("korek-v2"), outcome("korek-v2")))
    sumber = replace(bukti(sesi(1), baru), putaran=(putaran_lama, putaran_baru), kejadian=(tutup, carry))
    from cycle_carry import bukti_lanjutan
    harapan = bukti_satu_representasi(bukti_lanjutan(sumber), putaran_baru)
    assert not lc._evaluasi_fokus(harapan, putaran_baru, FOKUS)
    hasil = lc.rencana_berikutnya(sumber, 1, date(2026, 9, 10))
    assert hasil.putaran is not None
    status = next(f for f in hasil.putaran.fokus if f.kunci == FOKUS)
    assert status.status != "mulai_membaik", hasil


from test_learning_cycle_e2e import alur, buat, hari, intervensi, kirim, konfirmasi, rencana
import database


def test_http_manual_teks_tidak_mereset_fokus_visual_bertahan(alur):
    server, siswa, monkeypatch = alur
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
    for nomor in range(3):
        hari(monkeypatch, nomor)
        konfirmasi(alur, buat(alur, "pemetaan"), salah="deret_aritmetika")
    assert kirim(alur, f"/siklus/{siswa}/aksi", {
        "aksi": "ubah_fokus", "template_id": "korek_api", "kode_intervensi": "K",
    })[0] == 303
    intervensi(alur)
    konfirmasi(alur, buat(alur, "latihan_terbimbing"))
    konfirmasi(alur, buat(alur, "penguatan"))
    hari(monkeypatch, 5)
    konfirmasi(alur, buat(alur, "evaluasi"))
    hari(monkeypatch, 33)
    konfirmasi(alur, buat(alur, "checkpoint"))
    konfirmasi(alur, buat(alur, "checkpoint"))
    keadaan = rencana(alur)
    assert keadaan.putaran is not None
    assert keadaan.putaran.fokus[0].status == "bertahan"
    assert rencana(alur).tindakan == "tunggu_checkpoint"
    hari(monkeypatch, 34)
    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    with server.buka() as kon:
        manual = database.buat_sesi_dari_urutan(kon, siswa, seed=998,
            urutan=("korek_api",), topik="pola-bilangan", level="P3")
    konfirmasi(alur, manual, salah="korek_api")
    assert rencana(alur).tindakan == "tunggu_checkpoint", rencana(alur)


def test_kontrol_dua_template_memilih_mode_sendiri():
    from test_cycle_representations import FOKUS
    lain = ("deret_aritmetika", "H", None)
    pertama = replace(sesi(1), target_fokus=(FOKUS, lain), outcomes=(*sesi(1).outcomes,
        *(replace(o, template_id=lain[0], target_fokus=lain) for o in sesi(1).outcomes)))
    putaran = replace(PUTARAN, fokus=(FOKUS, lain))
    sumber = replace(bukti(pertama, sesi(2, "korek-v2", benar=False)), putaran=(putaran,))
    assert tuple((s.id, baik) for s, baik in lc._evaluasi_fokus(sumber, putaran, FOKUS)) == ((2, False),)
    assert tuple((s.id, baik) for s, baik in lc._evaluasi_fokus(sumber, putaran, lain)) == ((1, True),)


def test_kontrol_manual_optin_sah_dan_skipped_tunggal():
    from test_cycle_representations import FOKUS
    manual = replace(sesi(2, "korek-v2", tujuan="bebas"), konfirmasi_id=20, putaran_id=None)
    event = lc.KejadianSiklus(1, "sertakan_pemetaan", manual.tanggal, sesi_id=2, konfirmasi_id=20)
    sumber = replace(bukti(sesi(1), manual), kejadian=(event,))
    assert lc._evaluasi_fokus(sumber, PUTARAN, FOKUS) == ()
    lewat = replace(sesi(1), outcomes=tuple(replace(o, dilewati=True) for o in sesi(1).outcomes))
    assert bukti_satu_representasi(bukti(lewat), PUTARAN).sesi == (lewat,)
