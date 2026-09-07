"""Prioritas sesi asli tidak boleh digantikan proyeksi carry historis."""
from dataclasses import replace
from datetime import date

import pytest

import learning_cycle as lc
from cycle_carry import bukti_lanjutan
from learning_journey import perjalanan_belajar
from test_cycle_representations import PUTARAN, FOKUS, bukti, sesi

HARI = date(2026, 9, 10)
PASANGAN = ("deret_aritmetika", "H", None)


def sumber_carry():
    lama = replace(PUTARAN, fokus=(PASANGAN, FOKUS))
    baru = replace(lama, id=2, dibuka=date(2026, 9, 2))
    tutup = lc.KejadianSiklus(1, "putaran_ditutup", date(2026, 9, 2), putaran_id=1)
    carry = lc.KejadianSiklus(2, "putaran_kambuh_dibuka", date(2026, 9, 2), putaran_id=2,
        data=(("putaran_lama", 1), ("fokus_diteruskan", (FOKUS,))))
    return replace(bukti(sesi(1)), putaran=(lama, baru), kejadian=(tutup, carry))


def test_kontrol_carry_sah_menjaga_status_reducer_dan_journey():
    sumber = sumber_carry()
    hasil = lc.rencana_berikutnya(sumber, 1, HARI)
    assert hasil.tindakan == "intervensi"
    assert hasil.putaran is not None
    assert next(f for f in hasil.putaran.fokus if f.kunci == FOKUS).status == "mulai_membaik"
    journey = perjalanan_belajar(sumber, 1, HARI)
    assert next(f for f in journey.fokus if f.kunci == FOKUS).tahap == "mulai_membaik"


def test_pending_historis_yang_diteruskan_tidak_memblokir_putaran_aktif():
    sumber = sumber_carry()
    koreksi = lc.KejadianSiklus(3, "konfirmasi_dibatalkan", date(2026, 9, 3),
        putaran_id=1, sesi_id=1)
    pending = replace(sumber.sesi[0], dikonfirmasi=None, outcomes=())
    sumber = replace(sumber, sesi=(pending,), kejadian=(*sumber.kejadian, koreksi))
    aktif = sumber.putaran[-1]
    assert lc._sesi_pemblokir(sumber, aktif) == []
    assert not lc._evaluasi_fokus(bukti_lanjutan(sumber), aktif, FOKUS)
    hasil = lc.rencana_berikutnya(sumber, 1, HARI)
    assert hasil.tindakan == "intervensi", hasil


@pytest.mark.parametrize("selesai,tindakan", [(None, "lanjutkan_sesi"),
                                              ("sah", "konfirmasi_hasil")])
def test_kontrol_pending_putaran_aktif_tetap_memblokir(selesai, tindakan):
    sumber = sumber_carry()
    pending = replace(sesi(3), putaran_id=2, selesai=selesai, dikonfirmasi=None, outcomes=())
    sumber = replace(sumber, sesi=(*sumber.sesi, pending))
    hasil = lc.rencana_berikutnya(sumber, 1, HARI)
    assert hasil.tindakan == tindakan
    assert hasil.sesi_id == 3
