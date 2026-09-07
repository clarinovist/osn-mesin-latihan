"""Fakta Venn dan objek tersedia tidak diganti menjadi langkah solusi."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topic_combinatorics as topik
from question_views import penyajian_dari_soal
from visual_contract import DescriptorVisual
from visual_renderer import render_pertanyaan


def svg_dari(soal):
    hasil = penyajian_dari_soal(soal)
    html = render_pertanyaan(hasil)
    assert "<svg" in html
    return hasil, ET.fromstring(html[html.index("<svg"):html.index("</svg>") + 6])


def kelas(svg, nama):
    return tuple(e for e in svg.iter() if e.get("class") == nama)


def test_venn_total_di_luar_lingkaran_dan_irisan_tepat(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "kombinatorik")
    hasil, svg = svg_dari(topik.inklusi_eksklusi_2(19, 23, 7))
    assert hasil.descriptor.jenis == "venn_dua"
    assert dict(hasil.descriptor.data) == {"a": 19, "b": 23, "c": 7}
    lingkaran = kelas(svg, "himpunan")
    assert len(lingkaran) == 2
    irisan, = kelas(svg, "irisan-diberikan")
    assert irisan.text == "7"
    x, y = float(irisan.attrib["x"]), float(irisan.attrib["y"])
    assert all((x-float(e.attrib["cx"]))**2 + (y-float(e.attrib["cy"]))**2 < float(e.attrib["r"])**2 for e in lingkaran)
    for label in kelas(svg, "total-himpunan"):
        lx, ly = float(label.attrib["x"]), float(label.attrib["y"])
        assert all((lx-float(e.attrib["cx"]))**2 + (ly-float(e.attrib["cy"]))**2 > float(e.attrib["r"])**2 for e in lingkaran)
    assert not kelas(svg, "anggota-eksklusif")
    assert "12" not in [e.text for e in svg.iter()]
    assert "16" not in [e.text for e in svg.iter()]
    assert "35" not in [e.text for e in svg.iter()]


@pytest.mark.parametrize("soal,jumlah,slot", (
    (topik.susun_bilangan("dengan_nol", (0, 2, 4, 7)), 4, 4),
    (topik.susun_bilangan_syarat("genap", (1, 2, 5)), 3, 3),
    (topik.susun_bilangan_syarat("lebih_dari", (2, 5, 7), 500), 3, 3),
    (topik.permutasi_urutan(5, 3, ["A", "B", "C", "D", "E"]), 5, 3),
    (topik.permutasi_blok(5, 2, ["A", "B", "C", "D", "E"]), 5, 5),
    (topik.kombinasi_pilih(5, 3, ["A", "B", "C", "D", "E"]), 5, 0),
))
def test_objek_utuh_slot_kosong_tanpa_enumerasi(monkeypatch, soal, jumlah, slot):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "kombinatorik")
    hasil, svg = svg_dari(soal)
    assert hasil.descriptor.jenis == "susunan_objek"
    assert len(kelas(svg, "objek-tersedia")) == jumlah
    assert len(kelas(svg, "slot-kosong")) == slot
    assert not kelas(svg, "banyak-pilihan")
    assert not kelas(svg, "blok-solusi")
    assert "kunci" not in hasil.descriptor.data
    if soal.template_id == "kombinasi_pilih":
        assert len(kelas(svg, "area-tim")) == 1


@pytest.mark.parametrize("jenis,data", (
    ("venn_dua", {"a": 4, "b": 3, "c": 5}),
    ("venn_dua", {"a": 4, "b": 3, "c": 2, "hasil": 5}),
    ("susunan_objek", {"aturan": "permutasi", "objek": ["A", "A"], "ambil": 2}),
    ("susunan_objek", {"aturan": "permutasi", "objek": ["<script>"], "ambil": 1}),
    ("susunan_objek", {"aturan": "digit", "objek": ["0", "2"], "ambil": 3}),
    ("susunan_objek", {"aturan": "digit", "objek": ["0", "2"], "ambil": True}),
))
def test_descriptor_kombinatorik_tidak_valid_ditolak(jenis, data):
    with pytest.raises(ValueError):
        DescriptorVisual(jenis, 1, data)
