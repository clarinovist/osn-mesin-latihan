"""Kontrak pola baca gambar v2, terpisah dari penyajian warisan."""
from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from question_views import penyajian_dari_soal
from topic_number_patterns import korek_api, titik_segitiga
from visual_contract import DescriptorVisual
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan

NS = {"s": "http://www.w3.org/2000/svg"}


def svg(soal):
    penyajian = penyajian_dari_soal(soal)
    badan = render_pertanyaan(penyajian, namespace="uji-pola")
    akar = ET.fromstring("<svg" + badan.split("<svg", 1)[1].split("</svg>")[0] + "</svg>")
    return penyajian, akar


@pytest.fixture(autouse=True)
def aktif(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")


@pytest.mark.parametrize("awal", range(3, 8))
@pytest.mark.parametrize("tambah", (2, 3, 4))
def test_korek_v2_jujur_dan_tiap_ruas_dapat_dihitung(awal, tambah):
    soal = korek_api(awal, tambah, 20)
    penyajian, akar = svg(soal)
    assert penyajian.mode_representasi == "korek-v2"
    assert "Segitiga" not in penyajian.teks_soal
    assert f"menambah {tambah}" not in penyajian.teks_soal
    assert "butuh:" not in penyajian.teks_soal
    grup = akar.findall("s:g", NS)
    assert len(grup) == 3
    sebelumnya = frozenset()
    for n, g in enumerate(grup, 1):
        garis = g.findall("s:line", NS)
        ruas = frozenset(tuple(float(l.attrib[k]) for k in ("x1", "y1", "x2", "y2")) for l in garis)
        assert len(ruas) == len(garis) == awal + tambah * (n - 1)
        assert len({round(math.hypot(c-a, d-b), 6) for a, b, c, d in ruas}) == 1
        if n > 1:
            assert sebelumnya < ruas and len(ruas - sebelumnya) == tambah
        sebelumnya = ruas
        assert [t.text for t in g.findall("s:text", NS)] == [f"Gambar {n}"]
    assert "20" not in " ".join(akar.itertext())
    assert "batang" in ringkasan_pertanyaan(penyajian)


def test_titik_v2_koordinat_segitiga_dan_label_tanpa_jumlah():
    penyajian, akar = svg(titik_segitiga(25))
    assert penyajian.mode_representasi == "titik-v2"
    assert "punya:" not in penyajian.teks_soal
    for n, g in enumerate(akar.findall("s:g", NS), 1):
        titik = g.findall("s:circle", NS)
        assert len(titik) == n * (n + 1) // 2
        posisi = {(float(c.attrib['cx']), float(c.attrib['cy'])) for c in titik}
        assert len(posisi) == len(titik)
        baris = Counter(y for _, y in posisi)
        assert [baris[y] for y in sorted(baris)] == list(range(1, n + 1))
        pusat = [sum(x for x, yy in posisi if yy == y) / baris[y] for y in sorted(baris)]
        assert len(set(pusat)) == 1
        assert [t.text for t in g.findall("s:text", NS)] == [f"Gambar {n}"]
    assert "325" not in " ".join(akar.itertext())
    assert "titik" in ringkasan_pertanyaan(penyajian)


@pytest.mark.parametrize("jenis,data", [
    ("korek", {"n_tampil": 3, "awal": 4, "tambah": 3}),
    ("titik", {"n_tampil": 4}),
])
def test_v2_allowlist_dan_tahap_tetap(jenis, data):
    assert DescriptorVisual(jenis, 2, data).versi == 2
    for nama, nilai in (("n_tampil", True), ("n_tampil", 5), ("n_tampil", 0), ("jawaban", 13)):
        with pytest.raises(ValueError):
            DescriptorVisual(jenis, 2, {**data, nama: nilai})


@pytest.mark.parametrize("soal", (korek_api(4, 3, 20), titik_segitiga(10)))
def test_optin_tidak_mengubah_soal_dan_namespace_aman(soal, monkeypatch):
    sebelum = (soal.teks, soal.parameter.copy(), soal.kunci, soal.malrule, soal.tanda_tangan)
    penyajian = penyajian_dari_soal(soal)
    badan = render_pertanyaan(penyajian, namespace='a" onload="jahat')
    assert 'onload=' not in badan
    assert badan == render_pertanyaan(penyajian, namespace='a" onload="jahat')
    assert badan != render_pertanyaan(penyajian, namespace='lain')
    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    lama = penyajian_dari_soal(soal)
    assert lama.teks_soal == soal.teks and lama.descriptor is None
    assert "<svg" not in render_pertanyaan(lama)
    assert render_pertanyaan(penyajian)  # Reader tidak mengikuti kill switch writer.
    assert sebelum == (soal.teks, soal.parameter, soal.kunci, soal.malrule, soal.tanda_tangan)


def test_proyektor_memvalidasi_semua_input():
    from topic_number_patterns_visual import proyeksi_pola
    assert proyeksi_pola("deret_aritmetika", {}) is None
    for tid, p in (([], {}), ("korek_api", []), ("korek_api", {"awal": 4}),
                   ("korek_api", {"awal": 4, "tambah": 3, "gambar_ke": 3}),
                   ("titik_segitiga", {"gambar_ke": 4}),
                   ("titik_segitiga", {"gambar_ke": True}),
                   ("titik_segitiga", {"gambar_ke": 10000})):
        with pytest.raises(ValueError):
            proyeksi_pola(tid, p)
