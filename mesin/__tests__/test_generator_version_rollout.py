"""Palang writer versi baru harus terpisah dari reader histori."""
import random
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import database
import question_views
import topic_measurement as pengukuran
import topic_solid_geometry as ruang
from templates import REGISTRI


@pytest.mark.parametrize("topik,tid", (
    (pengukuran, "skala_peta"), (pengukuran, "jam_menit_detik"),
    (ruang, "jaring_jaring"), (ruang, "perbandingan_volume"),
    (ruang, "luas_permukaan"), (ruang, "volume_prisma_tabung"),
))
def test_writer_warisan_identik_termasuk_konsumsi_rng(monkeypatch, topik, tid):
    monkeypatch.setenv("OSN_MATEMATIKA_VERSI", "1")
    for seed in range(50):
        rng_baru, rng_lama = random.Random(seed), random.Random(seed)
        aktual = topik._parameter(tid, rng_baru, "P6")
        harapan = topik._parameter.__wrapped__(tid, rng_lama, "P6")
        assert aktual == harapan
        assert rng_baru.getstate() == rng_lama.getstate()


@pytest.mark.parametrize("nilai", ("0", "3", "salah", "2,1", "", "   "))
def test_flag_asing_menolak_writer_bukan_reader(monkeypatch, nilai):
    monkeypatch.setenv("OSN_MATEMATIKA_VERSI", nilai)
    with pytest.raises(ValueError, match="OSN_MATEMATIKA_VERSI"):
        pengukuran._parameter("skala_peta", random.Random(0), "P6")
    with pytest.raises(ValueError, match="OSN_MATEMATIKA_VERSI"):
        ruang._parameter("jaring_jaring", random.Random(0), "P6")
    assert pengukuran.skala_peta("cari_peta", 10, 10, 100000, versi=2).kunci == "10"


def test_default_dan_override_writer(monkeypatch):
    import generator_version as versi
    monkeypatch.delenv("OSN_MATEMATIKA_VERSI", raising=False)
    assert versi.versi_generator_baru() == versi.VERSI_GENERATOR_BAWAAN
    for teks, harapan in (("1", 1), ("2", 2), (" 2 ", 2)):
        monkeypatch.setenv("OSN_MATEMATIKA_VERSI", teks)
        assert versi.versi_generator_baru() == harapan


def test_default_rilis_versi2_setelah_image_jembatan(monkeypatch):
    from generator_version import versi_generator_baru
    monkeypatch.delenv("OSN_MATEMATIKA_VERSI", raising=False)
    assert versi_generator_baru() == 2
    assert all(s.parameter.get("versi") == 2 for s in _soal_v2())


def _soal_v2():
    def satu(topik, tid):
        parameter = next(p for p in (topik._parameter(tid, random.Random(s), "P6")
                                     for s in range(100)) if p.get("versi") == 2)
        return replace(REGISTRI[tid](**parameter), level="P6")
    return tuple(satu(t, tid) for t, tids in (
        (pengukuran, ("skala_peta", "jam_menit_detik")),
        (ruang, ("jaring_jaring", "perbandingan_volume", "luas_permukaan", "volume_prisma_tabung")),
    ) for tid in tids)


@pytest.mark.parametrize("flag_reader", ("1", "tidak-valid"))
def test_snapshot_v2_tetap_terbaca_ketika_writer_mundur(tmp_path, monkeypatch, flag_reader):
    monkeypatch.setenv("OSN_MATEMATIKA_VERSI", "2")
    monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
    soal = _soal_v2()
    jalur = tmp_path / "bridge.db"
    database.siapkan(jalur)
    with database.buka(jalur) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        sesi = database.buat_sesi_dari_urutan(kon, siswa, seed=1,
            urutan=tuple(s.template_id for s in soal), topik="campuran", level="P6", soal_terpilih=soal)
        sebelum = tuple(dict(b) for b in database.isi_sesi(kon, sesi))
        monkeypatch.setenv("OSN_MATEMATIKA_VERSI", flag_reader)
        pulih = tuple(question_views.soal_dari_baris(b) for b in database.isi_sesi(kon, sesi))
        assert len(pulih) == 6
        assert tuple(s.tanda_tangan for s in pulih) == tuple(s.tanda_tangan for s in soal)
        assert tuple(s.kunci for s in pulih) == tuple(s.kunci for s in soal)
        assert tuple(s.pembahasan for s in pulih) == tuple(s.pembahasan for s in soal)
        assert tuple(dict(b) for b in database.isi_sesi(kon, sesi)) == sebelum
