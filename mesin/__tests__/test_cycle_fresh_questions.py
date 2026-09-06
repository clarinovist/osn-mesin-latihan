"""Pencarian butir baru tetap bekerja ketika ruang parameter menyempit."""
from dataclasses import replace
import pytest
import database
from generator import profil
from topic_number_patterns import deret_aritmetika
from learning_cycle import RencanaBelajar, PutaranFokus
from test_learning_cycle_e2e import alur, kirim


def _siapkan(kon, siswa, sisa):
    putaran = database.buat_putaran_fokus(kon, siswa, "P3")
    lama = database.buat_sesi(kon, siswa, 11, topik="geometri-datar", jumlah_soal=1)
    semua = tuple(replace(deret_aritmetika(a, b, 4, profil("P3")["n_minta"]), level="P3")
                  for a in range(2, 13) for b in profil("P3")["beda_aritmetika"])
    for nomor, soal in enumerate(semua[sisa:], 2):
        sid = database.simpan_soal(kon, soal)
        kon.execute("INSERT INTO sesi_soal (sesi_id,soal_id,nomor) VALUES (?,?,?)", (lama, sid, nomor))
    return putaran, {s.tanda_tangan for s in semua[:sisa]}


def test_sisa_sepuluh_soal_dapat_dirangkai_tanpa_mengulang(alur):
    with alur[0].buka() as kon:
        siswa = alur[1]
        putaran, tersedia = _siapkan(kon, siswa, 10)
        rencana = RencanaBelajar("penguatan", "uji", putaran=PutaranFokus(putaran, "P3", ()),
                                kandidat=(("deret_aritmetika", "K", None),))
        sesi = database.buat_sesi_dari_rencana(kon, siswa, rencana, putaran_id=putaran, seed=100)
        tanda = {b[0] for b in kon.execute("SELECT so.tanda_tangan FROM soal so JOIN sesi_soal ss ON ss.soal_id=so.id WHERE ss.sesi_id=?", (sesi,))}
        assert len(tanda) == 10
        assert tanda <= tersedia


@pytest.mark.parametrize("kasus", ["komposisi", "level"])
def test_butir_terpilih_tidak_cocok_ditolak_sebelum_insert(alur, kasus):
    soal = replace(deret_aritmetika(2, 4, 4, 2), level="P4" if kasus == "level" else "P3")
    urutan = ("deret_aritmetika",) * (2 if kasus == "komposisi" else 1)
    with alur[0].buka() as kon:
        sebelum = tuple(kon.iterdump())
        with pytest.raises(ValueError, match="komposisi atau level"):
            database.buat_sesi_dari_urutan(kon, alur[1], 11, urutan, soal_terpilih=(soal,))
        assert tuple(kon.iterdump()) == sebelum


def test_ruang_soal_habis_menjadi_409_tanpa_sesi_parsial(alur, monkeypatch):
    import learning_sessions
    from test_learning_cycle_e2e import sampai_evaluasi, konfirmasi, intervensi, buat
    evaluasi = sampai_evaluasi(alur)
    konfirmasi(alur, evaluasi, paham="ragu")
    intervensi(alur)
    konfirmasi(alur, buat(alur, "latihan_terbimbing"))
    semua = {deret_aritmetika(a, b, 4, profil("P3")["n_minta"]).tanda_tangan
             for a in range(2, 13) for b in profil("P3")["beda_aritmetika"]}
    with alur[0].buka() as kon:
        sebelum = tuple(kon.iterdump())
    monkeypatch.setattr(learning_sessions, "_tanda_tangan_lama", lambda *_: semua)
    assert kirim(alur, f"/siklus/{alur[1]}/buat")[0] == 409
    with alur[0].buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
