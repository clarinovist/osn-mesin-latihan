"""Penerusan fokus kedua menjaga probe, nomor checkpoint dan immutability."""
from datetime import date
import database
import learning_cycle as lc
from cycle_carry import bukti_lanjutan
from learning_cycle_service import _occurrence_berikutnya
from test_learning_cycle_e2e import alur

A = ("deret_aritmetika", "K", None)
B = ("soal_umur", "H", None)
HARI = date(2026, 1, 1)


def _bukti():
    sesi = lc.SesiSiklus(1, 1, "P3", "checkpoint", HARI,
        selesai="2026-01-01", dikonfirmasi="2026-01-01", putaran_id=1,
        bagian_checkpoint=1, occurrence=2, konfirmasi_id=1,
        target_fokus=(A, B), outcomes=(
            lc.OutcomeSiklus(A[0], True, target_fokus=A),
            lc.OutcomeSiklus(B[0], True, target_fokus=B)))
    event = lc.KejadianSiklus(5, "putaran_kambuh_dibuka", HARI, 2,
        data=(("putaran_lama", 1), ("fokus_diteruskan", (B,))))
    return lc.BuktiSiklus(1, "P3", (sesi,),
        (lc.PutaranSiklus(1, 1, "P3", HARI, (A, B)),
         lc.PutaranSiklus(2, 1, "P3", HARI, (A, B))), (event,))


def test_proyeksi_hanya_probe_fokus_diteruskan_dan_idempoten():
    bukti = _bukti()
    hasil = bukti_lanjutan(bukti)
    assert hasil.sesi[0] == bukti.sesi[0]
    assert len(bukti.sesi) == 1
    assert len(hasil.sesi) == 2
    assert hasil.sesi[1].target_fokus == (B,)
    assert len(hasil.sesi[1].outcomes) == 1
    assert hasil.sesi[1].outcomes[0].target_fokus == B
    assert hasil.sesi[1].occurrence == 2
    assert bukti_lanjutan(hasil) == hasil


def test_occurrence_checkpoint_meneruskan_nomor_fokus_bawaan(alur, monkeypatch):
    bukti = _bukti()
    monkeypatch.setattr(database, "muat_bukti_siklus", lambda *_: bukti)
    with alur[0].buka() as kon:
        database.buat_putaran_fokus(kon, alur[1], "P3")
        putaran = database.buat_putaran_fokus(kon, alur[1], "P3")
        rencana = lc.RencanaBelajar("checkpoint", "uji", kandidat=(B,), bagian_checkpoint=1)
        assert _occurrence_berikutnya(kon, putaran, rencana) == 3
