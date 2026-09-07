"""Alur HTTP penggunaan pendekatan visual sampai evaluasi ulang dan checkpoint."""
import json
import re

import pytest

import database
from http_test_kit import SANDI_GURU
from test_learning_cycle_e2e import alur, buat, hari, intervensi, kirim, konfirmasi, rencana


def tanpa_bantuan(alur, sesi, tujuan):
    server, siswa, _ = alur
    with server.buka() as kon:
        info = kon.execute("SELECT tujuan FROM sesi WHERE id = ?", (sesi,)).fetchone()
        assert info["tujuan"] == tujuan
        butir = database.isi_sesi(kon, sesi)
        pola = tuple(b for b in butir if b["template_id"] in {"korek_api", "titik_segitiga"})
        assert pola and all(b["status_visual"] == "siap" for b in pola)
        assert all("bantuan" not in b["penyajian_json"] for b in butir)
    kode, html, _ = server.minta(f"/lembar/{sesi}", auth=("guru", SANDI_GURU))
    assert kode == 200
    assert len(re.findall(r'<svg[^>]*role="img"', html)) == len(pola)
    assert "data-bantuan-visual" not in html


def test_pendekatan_visual_diganti_setelah_gagal_tanpa_mengubah_reducer(alur):
    tid = "korek_api"
    server, siswa, monkeypatch = alur
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
    for nomor in range(3):
        hari(monkeypatch, nomor)
        konfirmasi(alur, buat(alur, "pemetaan"), salah="deret_aritmetika")
    assert kirim(alur, f"/siklus/{siswa}/aksi", {
        "aksi": "ubah_fokus", "template_id": tid, "kode_intervensi": "K",
    })[0] == 303
    awal = rencana(alur)
    assert awal.putaran is not None
    id_visual = intervensi(alur)
    assert id_visual.startswith("visual-pola-v1:")
    with server.buka() as kon:
        events = kon.execute("SELECT data FROM kejadian_belajar WHERE jenis='intervensi_selesai'").fetchall()
        assert any(json.loads(e["data"])["pendekatan_id"] == id_visual for e in events)
    konfirmasi(alur, buat(alur, "latihan_terbimbing"))
    konfirmasi(alur, buat(alur, "penguatan"))
    hari(monkeypatch, 5)
    evaluasi = buat(alur, "evaluasi")
    tanpa_bantuan(alur, evaluasi, "evaluasi")
    konfirmasi(alur, evaluasi, paham="ragu")
    setelah = rencana(alur)
    assert setelah.tindakan == "intervensi"
    assert setelah.putaran is not None
    assert setelah.putaran.fokus[0].pendekatan_berikutnya != id_visual
    # Replay pendekatan yang sama bersifat idempoten, tidak membuka tahap berikutnya.
    assert kirim(alur, f"/siklus/{siswa}/aksi", {
        "aksi": "intervensi_selesai", "putaran_id": awal.putaran.id,
        "template_id": tid, "kode_intervensi": "K", "pendekatan_id": id_visual,
    })[0] == 303
    assert rencana(alur) == setelah
    kode, html, _ = server.minta(f"/anak/{siswa}", auth=("guru", SANDI_GURU))
    assert kode == 200 and "data-bantuan-visual" not in html
    id_lain = intervensi(alur)
    assert id_lain != id_visual
    konfirmasi(alur, buat(alur, "latihan_terbimbing"))
    konfirmasi(alur, buat(alur, "penguatan"))
    hari(monkeypatch, 8)
    konfirmasi(alur, buat(alur, "evaluasi"))
    hari(monkeypatch, 36)
    checkpoint = buat(alur, "checkpoint")
    tanpa_bantuan(alur, checkpoint, "checkpoint")
    konfirmasi(alur, checkpoint)
    bagian_kedua = buat(alur, "checkpoint")
    tanpa_bantuan(alur, bagian_kedua, "checkpoint")
    konfirmasi(alur, bagian_kedua)
    akhir = rencana(alur)
    assert akhir.tindakan == "tunggu_checkpoint" and akhir.putaran is not None
    assert akhir.putaran.fokus[0].status == "bertahan"


@pytest.mark.parametrize("tid", ("korek_api", "titik_segitiga"))
def test_reducer_memilih_id_lain_setelah_bukti_evaluasi_gagal(tid):
    """Kontrak reducer tidak bergantung pada banyaknya variasi generator."""
    from datetime import date
    import interventions
    import learning_cycle as siklus
    from learning_cycle_ui import render_rencana
    fokus = (tid, "K", None)
    pilihan = interventions.pilihan_untuk_fokus(fokus)
    visual = next(m for m in pilihan if m.bantuan is not None)
    putaran = siklus.PutaranSiklus(1, 1, "P3", date(2026, 9, 1), (fokus,))
    evaluasi = siklus.SesiSiklus(
        1, 1, "P3", "evaluasi", date(2026, 9, 8),
        selesai="selesai", direview="ditinjau", dikonfirmasi="sah", putaran_id=1,
        outcomes=tuple(siklus.OutcomeSiklus(tid, False, "K", target_fokus=fokus,
                                           cek_pemahaman="ragu") for _ in range(4)),
        target_fokus=(fokus,),
    )
    event = siklus.KejadianSiklus(1, "intervensi_selesai", date(2026, 9, 3),
        putaran_id=1, data=(("fokus", fokus), ("pendekatan_id", visual.pendekatan_id)))
    bukti = siklus.BuktiSiklus(1, "P3", (evaluasi,), (putaran,), (event,),
        ((fokus, tuple(m.pendekatan_id for m in pilihan)),))
    rec = siklus.rencana_berikutnya(bukti, 1, date(2026, 9, 9))
    assert rec.tindakan == "intervensi" and rec.putaran is not None
    alternatif = rec.putaran.fokus[0].pendekatan_berikutnya
    assert alternatif != visual.pendekatan_id
    assert any(m.pendekatan_id == alternatif and m.bantuan is None for m in pilihan)
    assert "data-bantuan-visual" not in render_rencana(rec, bukti, 1)
    assert siklus.rencana_berikutnya(bukti, 1, date(2026, 9, 9)) == rec
