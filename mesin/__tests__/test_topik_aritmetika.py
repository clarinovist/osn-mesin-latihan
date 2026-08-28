"""Fase B: kontrak topik kedua aritmetika dasar.

Topik kedua adalah bukti bahwa registry benar-benar menjadi seam: paket baru
harus terdaftar, komposisinya dipakai generator, dan ia tidak mengubah paket
pola bilangan yang telah stabil.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
import pytest  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def test_registry_memuat_pola_dan_aritmetika_dasar():
    """Loader paket harus memberi UI dua opsi topik yang nyata."""
    assert topik.daftar_topik() == ["aritmetika-dasar", "pola-bilangan"]

    paket = topik.ambil("aritmetika-dasar")
    assert paket.id == "aritmetika-dasar"
    assert paket.nama == "Aritmetika Dasar"
    assert paket.judul_lembar == "Latihan Aritmetika Dasar"


def test_registry_global_menggabungkan_template_kedua_paket():
    """Template topik kedua tersedia lewat jalur kompatibilitas REGISTRI."""
    registri = topik.registri()
    assert "deret_aritmetika" in registri
    assert "urutan_operasi_1" in registri
    assert "fpb_dua_bilangan" in registri
    assert "pecahan_operasi_campuran" in registri


def test_lembar_aritmetika_p5_dan_p6_berisi_enam_soal():
    """Paket yang memang mulai P5 tidak boleh mencari komposisi P3."""
    for level in ("P5", "P6"):
        lembar = buat_lembar(7, level=level, topik="aritmetika-dasar")
        assert len(lembar.soal) == 6
        assert {soal.template_id for soal in lembar.soal} == {
            "urutan_operasi_1",
            "fpb_dua_bilangan",
            "pecahan_operasi_campuran",
        }


@pytest.mark.parametrize("level", ("P3", "P4"))
def test_aritmetika_menolak_level_di_luar_scope(level):
    """Paket P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3/P4."""
    with pytest.raises(ValueError, match="aritmetika-dasar"):
        buat_lembar(7, level=level, topik="aritmetika-dasar")
    with pytest.raises(ValueError, match="aritmetika-dasar"):
        buat_soal("urutan_operasi_1", 7, level=level, topik="aritmetika-dasar")


def test_aritmetika_level_teks_aneh_jatuh_ke_p5_bukan_parameter_p6():
    """Data tingkat lama yang aneh memakai level pertama paket, bukan P6."""
    aneh = buat_lembar(7, level="tingkat-lama", topik="aritmetika-dasar")
    p5 = buat_lembar(7, level="P5", topik="aritmetika-dasar")
    assert aneh.level == "P5"
    assert aneh.tanda_tangan == p5.tanda_tangan


def test_template_aritmetika_memiliki_jalur_k_dan_h_tanpa_tabrakan():
    """Jawaban salah harus tetap membedakan konsep dari salah hitung.

    Ini menguji hasil sesudah `saring_malrule`, bukan hanya kandidat yang
    tertulis di template. Malrule yang bertabrakan akan dibuang dan diagnosis
    dapat kehilangan jalur penting tanpa terlihat dari pembacaan kode.
    """
    for template_id in (
        "urutan_operasi_1",
        "fpb_dua_bilangan",
        "pecahan_operasi_campuran",
    ):
        for level in ("P5", "P6"):
            for seed in range(1, 80):
                soal = buat_soal(
                    template_id, seed, level=level, topik="aritmetika-dasar"
                )
                jawaban = [mal.jawaban for mal in soal.malrule]
                kode = {mal.kode for mal in soal.malrule}
                assert soal.kunci not in jawaban, (template_id, level, seed)
                assert len(jawaban) == len(set(jawaban)), (template_id, level, seed)
                assert {"K", "H"} <= kode, (template_id, level, seed, kode)


def test_parameter_aritmetika_berubah_antar_seed_dan_level():
    """Dua pengulangan adalah soal baru, bukan enam salinan parameter tetap."""
    for template_id in (
        "urutan_operasi_1",
        "fpb_dua_bilangan",
        "pecahan_operasi_campuran",
    ):
        p5 = buat_soal(template_id, 7, level="P5", topik="aritmetika-dasar")
        p6 = buat_soal(template_id, 7, level="P6", topik="aritmetika-dasar")
        lain = buat_soal(template_id, 8, level="P5", topik="aritmetika-dasar")
        assert p5.parameter != p6.parameter, template_id
        assert p5.parameter != lain.parameter, template_id


def test_urutan_operasi_malrule_memakai_operasi_persis_bukan_pembulatan():
    """Setiap jalur salah urutan harus tetap berupa bilangan bulat yang sah.

    Jangan memakai `//`: pembulatan bawah mengubah jawaban yang benar-benar
    akan ditulis anak saat ia menjalankan operasi dengan urutan keliru.
    """
    for level in ("P5", "P6"):
        for seed in range(1, 80):
            soal = buat_soal(
                "urutan_operasi_1", seed, level=level, topik="aritmetika-dasar"
            )
            p = soal.parameter
            assert (p["a"] + p["b"]) % p["c"] == 0, (level, seed, p)
            assert p["b"] % (p["c"] * p["d"]) == 0, (level, seed, p)
            jawaban = {mal.id: mal.jawaban for mal in soal.malrule}
            assert jawaban["urutan_operasi.kiri_ke_kanan_tanpa_prioritas"] == str(
                ((p["a"] + p["b"]) // p["c"]) * p["d"] - p["e"]
            )
            assert jawaban["urutan_operasi.kali_sebelum_bagi_tanpa_kiri_ke_kanan"] == str(
                p["a"] + p["b"] // (p["c"] * p["d"]) - p["e"]
            )
