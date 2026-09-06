"""Fase 2: renderer snapshot pertanyaan yang aman lintas permukaan."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from visual_contract import DescriptorVisual, buat_penyajian  # noqa: E402
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan  # noqa: E402


def _penyajian(**ubah):
    argumen = {
        "template_id": "korek_api",
        "level": "P4",
        "parameter": {"awal": 4, "tambah": 3, "gambar_ke": 8},
        "teks_soal": "Pola <aman> bertumbuh.\nBerapa banyak batang berikutnya?",
        "bagian_soal": "B",
        "asal_teks": "bawaan",
        "status_visual": "tanpa_visual",
        "mode_representasi": "teks-v1",
        "descriptor": None,
    }
    argumen.update(ubah)
    return buat_penyajian(**argumen)


def _visual(jenis="korek", data=None, **ubah):
    if data is None:
        data = {"n_tampil": 3, "awal": 4, "tambah": 3}
    argumen = {
        "status_visual": "siap",
        "mode_representasi": f"{jenis}-v1",
        "descriptor": DescriptorVisual(jenis, 1, data),
    }
    argumen.update(ubah)
    return _penyajian(**argumen)


def test_renderer_teks_mengikuti_kelas_existing_setiap_permukaan_dan_escape():
    penyajian = _penyajian()

    cetak = render_pertanyaan(penyajian, gaya="cetak")
    murid = render_pertanyaan(penyajian, gaya="murid")
    stitch = render_pertanyaan(penyajian, gaya="stitch")
    guru = render_pertanyaan(penyajian, gaya="guru")

    assert '<div class="teks">Pola &lt;aman&gt; bertumbuh.</div>' in cetak
    assert '<div class="tanya">Berapa banyak batang berikutnya?</div>' in cetak
    assert '<div class="teks">Pola &lt;aman&gt; bertumbuh.</div>' in murid
    assert '<div class="tanya">Berapa banyak batang berikutnya?</div>' in murid
    assert '<div class="kerja-teks-st">Pola &lt;aman&gt; bertumbuh.</div>' in stitch
    assert '<div class="kerja-tanya-st">Berapa banyak batang berikutnya?</div>' in stitch
    assert '<div class="teks-soal">Pola &lt;aman&gt; bertumbuh.\nBerapa banyak batang berikutnya?</div>' in guru
    assert "<aman>" not in cetak + murid + stitch + guru


@pytest.mark.parametrize(
    "gaya, kelas",
    [
        ("cetak", "teks"),
        ("murid", "teks"),
        ("stitch", "kerja-teks-st"),
    ],
)
def test_satu_baris_tetap_teks_bukan_pertanyaan(gaya, kelas):
    html = render_pertanyaan(_penyajian(teks_soal="Satu baris saja."), gaya=gaya)

    assert f'<div class="{kelas}">Satu baris saja.</div>' in html
    assert "tanya" not in html


def test_wrapper_membawa_fingerprint_penyajian_sebagai_bukti_semantik():
    penyajian = _penyajian()

    hasil = render_pertanyaan(penyajian)

    assert hasil.startswith("<div ")
    assert (
        f'data-fingerprint-penyajian="{penyajian.fingerprint_penyajian}"'
        in hasil
    )
    assert hasil.endswith("</div>")


def test_visual_korek_memakai_leaf_tervalidasi_dan_namespace_deterministik():
    penyajian = _visual()

    pertama = render_pertanyaan(penyajian, namespace="kartu-7")
    ulang = render_pertanyaan(penyajian, namespace="kartu-7")
    lain = render_pertanyaan(penyajian, namespace="kartu-8")

    assert pertama == ulang
    assert '<svg ' in pertama
    assert 'data-gambar="1" data-ruas="4"' in pertama
    assert 'data-gambar="2" data-ruas="7"' in pertama
    assert 'data-gambar="3" data-ruas="10"' in pertama
    assert 'pola-korek-kartu-7-title' in pertama
    assert 'pola-korek-kartu-8-title' in lain
    assert pertama != lain


def test_visual_hanya_memiliki_satu_baris_pertanyaan():
    hasil = render_pertanyaan(_visual(teks_soal="Intro satu.\nIntro dua.\nPertanyaan?"))
    assert hasil.count('class="tanya"') == 1
    assert '<div class="teks">Intro dua.</div>' in hasil


def test_mode_visual_tidak_boleh_dilabelkan_pada_teks():
    with pytest.raises(ValueError, match="mode"):
        render_pertanyaan(_penyajian(mode_representasi="korek-v1"))


def test_visual_titik_memakai_leaf_dengan_jumlah_tahap_descriptor():
    penyajian = _visual(
        "titik",
        {"n_tampil": 4},
        template_id="titik_segitiga",
        parameter={"gambar_ke": 9},
    )

    hasil = render_pertanyaan(penyajian, namespace="soal-titik")

    assert '<svg ' in hasil
    assert hasil.count("data-titik=") == 4
    assert 'data-gambar="4" data-titik="10"' in hasil
    assert "Gbr 5" not in hasil


@pytest.mark.parametrize("status", ["tanpa_visual", "warisan"])
def test_tanpa_visual_dan_warisan_hanya_merender_teks_escaped(status):
    hasil = render_pertanyaan(
        _penyajian(
            status_visual=status,
            asal_teks="warisan" if status == "warisan" else "bawaan",
        )
    )

    assert "<svg" not in hasil.lower()
    assert "&lt;aman&gt;" in hasil


def test_status_tidak_valid_gagal_terlihat():
    with pytest.raises(ValueError, match="tidak valid"):
        render_pertanyaan(_penyajian(status_visual="tidak_valid"))


def test_placeholder_tidak_pernah_dianggap_visual_asli():
    penyajian = _penyajian(
        status_visual="siap",
        mode_representasi="placeholder-v1",
        descriptor=DescriptorVisual("placeholder", 1, {"label": "Gambar tersedia"}),
    )

    with pytest.raises(ValueError, match="placeholder"):
        render_pertanyaan(penyajian)


def test_renderer_tidak_memuat_kunci_solusi_atau_target_tak_tergambar():
    penyajian = _visual(
        teks_soal="Amati tiga tahap pola.\nTentukan tahap yang diminta.",
        parameter={
            "awal": 4,
            "tambah": 3,
            "gambar_ke": 123456789,
            "kunci": "RAHASIA-SOLUSI",
        },
    )

    hasil = render_pertanyaan(penyajian)

    assert "RAHASIA-SOLUSI" not in hasil
    assert "123456789" not in hasil
    assert not re.search(r"(?:kunci|solution|jawaban)", hasil, re.I)


def test_visual_tidak_mengubah_teks_snapshot_atau_mengarang_pertanyaan():
    teks = "Konteks persis.\nPertanyaan persis?"
    hasil = render_pertanyaan(_visual(teks_soal=teks))

    assert "Konteks persis." in hasil
    assert "Pertanyaan persis?" in hasil
    assert "butuh berapa" not in hasil.lower()
    assert "punya berapa" not in hasil.lower()


def test_mode_representasi_visual_harus_cocok_dengan_descriptor():
    with pytest.raises(ValueError, match="mode representasi"):
        render_pertanyaan(_visual(mode_representasi="titik-v1"))


def test_ringkasan_visual_korek_menambah_fakta_descriptor_tanpa_target_atau_markup():
    penyajian = _visual(
        teks_soal="Amati pola berikut.",
        parameter={"gambar_ke": 123456789, "kunci": "RAHASIA"},
    )

    ringkasan = ringkasan_pertanyaan(penyajian)

    assert ringkasan.startswith("Amati pola berikut.")
    assert "3 tahap" in ringkasan
    assert "4, 7, 10 batang" in ringkasan
    assert "123456789" not in ringkasan
    assert "RAHASIA" not in ringkasan
    assert "<" not in ringkasan


def test_ringkasan_visual_titik_menambah_fakta_jumlah_tiap_tahap():
    penyajian = _visual(
        "titik",
        {"n_tampil": 4},
        template_id="titik_segitiga",
        parameter={"gambar_ke": 99},
        teks_soal="Amati susunan titik.",
    )

    ringkasan = ringkasan_pertanyaan(penyajian)

    assert ringkasan.startswith("Amati susunan titik.")
    assert "4 tahap" in ringkasan
    assert "1, 3, 6, 10 titik" in ringkasan
    assert "99" not in ringkasan
    assert "<svg" not in ringkasan.lower()


def test_ringkasan_tanpa_visual_mempertahankan_teks_persis():
    penyajian = _penyajian(teks_soal="  Teks persis.\nBaris kedua?  ")

    assert ringkasan_pertanyaan(penyajian) == penyajian.teks_soal


def test_ringkasan_menolak_placeholder_dan_mode_visual_tidak_cocok():
    placeholder = _penyajian(
        status_visual="siap",
        mode_representasi="placeholder-v1",
        descriptor=DescriptorVisual("placeholder", 1, {"label": "Gambar tersedia"}),
    )
    with pytest.raises(ValueError, match="placeholder"):
        ringkasan_pertanyaan(placeholder)
    with pytest.raises(ValueError, match="mode representasi"):
        ringkasan_pertanyaan(_visual(mode_representasi="titik-v1"))


@pytest.mark.parametrize("gaya", ["", "layar", None, 3])
def test_renderer_menolak_gaya_tidak_dikenal(gaya):
    with pytest.raises(ValueError, match="gaya"):
        render_pertanyaan(_penyajian(), gaya=gaya)


@pytest.mark.parametrize("namespace", ["", None, 3])
def test_renderer_visual_menolak_namespace_tidak_valid(namespace):
    with pytest.raises(ValueError, match="namespace"):
        render_pertanyaan(_visual(), namespace=namespace)


def test_renderer_memvalidasi_ulang_fingerprint_objek_yang_ditempa():
    penyajian = _penyajian()
    object.__setattr__(penyajian, "teks_soal", "Teks hasil tempaan")

    with pytest.raises(ValueError, match="fingerprint penyajian"):
        render_pertanyaan(penyajian)
    with pytest.raises(ValueError, match="fingerprint penyajian"):
        ringkasan_pertanyaan(penyajian)


def test_renderer_memvalidasi_ulang_descriptor_objek_yang_ditempa():
    penyajian = _visual()
    object.__setattr__(
        penyajian.descriptor,
        "data",
        {"n_tampil": 3, "awal": 4, "tambah": 3, "target": 99},
    )

    with pytest.raises(ValueError):
        render_pertanyaan(penyajian)
