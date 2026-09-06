"""Palang dan atomicity pembukaan ulang siklus pada database sintetis."""
import pytest
import database
import cycle_restart
from test_learning_cycle_e2e import alur, sampai_evaluasi, konfirmasi, hari, buat, kirim


def _dump(alur):
    with alur[0].buka() as kon:
        return tuple(kon.iterdump())


def _kambuh(alur):
    konfirmasi(alur, sampai_evaluasi(alur))
    hari(alur[2], 33)
    konfirmasi(alur, buat(alur, "checkpoint"))
    konfirmasi(alur, buat(alur, "checkpoint"))
    hari(alur[2], 61)
    konfirmasi(alur, buat(alur, "checkpoint"), salah="deret_aritmetika")


@pytest.mark.parametrize("payload", [
    {"aksi": "mulai_putaran_baru"},
    {"aksi": "mulai_putaran_baru", "putaran_id": "1"},
])
def test_tanpa_kekambuhan_atau_payload_asing_tidak_mutasi(alur, payload):
    sebelum = _dump(alur)
    assert kirim(alur, f"/siklus/{alur[1]}/aksi", payload)[0] == 400
    assert _dump(alur) == sebelum


def test_siswa_asing_dan_tidak_ada_404_identik_tanpa_mutasi(alur):
    with alur[0].buka() as kon:
        asing = database.tambah_siswa(kon, "Sintetis lain", "P3", pemilik="guru-lain")
    sebelum = _dump(alur)
    ada = kirim(alur, f"/siklus/{asing}/aksi", {"aksi": "mulai_putaran_baru"})
    tiada = kirim(alur, "/siklus/99999/aksi", {"aksi": "mulai_putaran_baru"})
    assert ada[:2] == tiada[:2]
    assert ada[0] == 404
    assert _dump(alur) == sebelum


def test_restart_tidak_menghilangkan_fokus_kedua_dan_tahapnya(alur):
    import interventions
    from test_learning_cycle_e2e import rencana
    _kambuh(alur)
    fokus_b = ("soal_umur", "H", None)
    with alur[0].buka() as kon:
        putaran = kon.execute("SELECT MAX(id) FROM putaran_fokus").fetchone()[0]
        sumber = kon.execute("SELECT MIN(id) FROM sesi").fetchone()[0]
        database.tambah_anggota_fokus(kon, putaran, *fokus_b, [sumber])
        from learning_cycle_service import catat_intervensi_selesai
        catat_intervensi_selesai(kon, alur[1], putaran, fokus_b,
                               interventions.pilihan_untuk_fokus(fokus_b)[0].pendekatan_id)
    assert kirim(alur, f"/siklus/{alur[1]}/aksi", {"aksi": "mulai_putaran_baru"})[0] == 303
    rec = rencana(alur)
    assert rec.putaran is not None
    assert {f.kunci for f in rec.putaran.fokus} == {("deret_aritmetika", "K", None), fokus_b}
    from learning_journey import perjalanan_belajar
    with alur[0].buka() as kon:
        perjalanan = perjalanan_belajar(database.muat_bukti_siklus(kon, alur[1]), alur[1])
        assert {f.kunci: f.tahap for f in perjalanan.fokus}[fokus_b] == "latihan_terbimbing"


def test_gagal_menulis_anggota_rollback_putaran_baru(alur, monkeypatch):
    _kambuh(alur)
    sebelum = _dump(alur)

    def gagal(*_args, **_kwargs):
        raise ValueError("gagal sintetis")

    monkeypatch.setattr(database, "tambah_anggota_fokus", gagal)
    with alur[0].buka() as kon:
        with pytest.raises(ValueError, match="gagal sintetis"):
            cycle_restart.mulai_putaran_baru(kon, alur[1])
    assert _dump(alur) == sebelum
