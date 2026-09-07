"""Ruang label SVG berdasarkan bbox browser, bukan sekadar markup ada."""
import pytest
from question_views import penyajian_dari_soal
from visual_renderer import render_pertanyaan
from visual_test_support import NS, buat_soal, gambar
import design_tokens as T


@pytest.mark.parametrize("tid,level", (("juring", "P6"), ("simetri_bangun", "P3")))
def test_label_dimensi_terpisah_dari_catatan_skala(monkeypatch, tid, level):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = buat_soal("geometri-datar", level, tid, 0)
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(soal)))
    catatan = svg.find("s:text[@class='catatan-skala']", NS)
    assert catatan is not None
    lainnya = tuple(e for e in svg.findall(".//s:text", NS) if e is not catatan)
    # Bbox aktual font halaman penuh memerlukan lebih dari selisih lama 16 unit.
    terendah = max(float(e.attrib["y"]) for e in lainnya)
    assert float(catatan.attrib["y"]) - terendah >= T.GEO_FONT_CATATAN + 10
    assert float(catatan.attrib["y"]) < T.GEO_TINGGI


def test_jarum_jam_tidak_mencapai_pita_angka():
    assert T.JAM_RADIUS * T.JAM_JARUM_PANJANG <= T.JAM_RADIUS * T.JAM_ANGKA_RADIUS - T.JAM_ANGKA_FONT / 2 - 3
    assert T.JAM_JARUM_PENDEK < T.JAM_JARUM_PANJANG


@pytest.mark.parametrize("tid,kelas", (("luas_arsiran", "jalan-luar"),
    ("luas_segiempat_lain", "ketupat"), ("luas_segitiga_jajargenjang", "jajargenjang")))
def test_label_ukuran_di_bawah_bangun_tidak_menyentuh_garis(monkeypatch, tid, kelas):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = buat_soal("geometri-datar", "P5", tid, 0)
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(soal)))
    bentuk = next(e for e in svg.iter() if e.attrib.get("class") == kelas)
    bawah = (float(bentuk.attrib["y"]) + float(bentuk.attrib["height"]) if kelas == "jalan-luar"
             else max(float(t.split(",")[1]) for t in bentuk.attrib["points"].split()))
    awalan = {"jalan-luar": "luar", "ketupat": "d₁ =", "jajargenjang": "t ="}[kelas]
    label = next(e for e in svg.findall(".//s:text", NS) if (e.text or "").startswith(awalan))
    assert float(label.attrib["y"]) >= bawah + T.GEO_FONT


@pytest.mark.parametrize("tid", ("jumlah_sudut_segitiga", "sudut_luar_segitiga"))
def test_label_sudut_menjauh_dari_sisi_miring(monkeypatch, tid):
    import math
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(buat_soal("geometri-datar", "P5", tid, 0))))
    bangun = svg.find("s:polygon[@class='segitiga']", NS)
    assert bangun is not None
    titik = tuple(tuple(map(float, t.split(","))) for t in bangun.attrib["points"].split())
    for label in svg.findall("s:text[@class='label-sudut']", NS):
        if label.attrib["data-vertex"] == "B-luar":
            continue
        x, y = float(label.attrib["x"]), float(label.attrib["y"])
        for (a, b), (c, d) in ((titik[0], titik[2]), (titik[1], titik[2])):
            jarak = abs((d-b)*x-(c-a)*y+c*b-d*a) / math.hypot(d-b, c-a)
            assert jarak >= 20


def test_label_sudut_lancip_memakai_ruang_lebar_di_antara_sinar(monkeypatch):
    import math
    from templates import REGISTRI
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = REGISTRI["sudut_pelurus_berpenyiku"](varian="penyiku", x=23)
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(soal)))
    label = next(e for e in svg.findall(".//s:text", NS) if e.text == "23°")
    assert math.hypot(float(label.attrib["x"])-T.GEO_SUDUT_X,
                      float(label.attrib["y"])-T.GEO_SUDUT_Y) >= 80


def test_label_tinggi_segitiga_pipih_tidak_memotong_sisi(monkeypatch):
    from templates import REGISTRI
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = REGISTRI["luas_segitiga_jajargenjang"](varian="segitiga", a=16, t=5, s=8)
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(soal)))
    label = next(e for e in svg.findall(".//s:text", NS) if e.text == "t = 5 cm")
    assert float(label.attrib["y"]) > T.GEO_SEGITIGA_ALAS_Y + T.GEO_FONT


def test_sisi_persegi_panjang_menyisakan_ruang_lebar_label(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(buat_soal("geometri-datar", "P4", "keliling_luas_datar", 476))))
    label = next(e for e in svg.findall(".//s:text", NS) if e.text == "20 cm")
    assert float(label.attrib["x"]) >= 54


@pytest.mark.parametrize("seed,akhiran", ((15, "14 cm"), (23, "4 cm")))
def test_label_tinggi_dan_diagonal_pada_ekstrem_terpisah(monkeypatch, seed, akhiran):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(buat_soal("geometri-datar", "P5", "luas_segiempat_lain", seed))))
    label = next(e for e in svg.findall(".//s:text", NS) if (e.text or "").endswith(akhiran))
    bangun = svg.find("s:polygon", NS)
    assert bangun is not None
    bawah = max(float(t.split(",")[1]) for t in bangun.attrib["points"].split())
    assert float(label.attrib["y"]) >= bawah + T.GEO_FONT


def test_baseline_sudut_15_derajat_tidak_mengenai_sinar(monkeypatch):
    from templates import REGISTRI
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = REGISTRI["sudut_pelurus_berpenyiku"](varian="penyiku", x=15)
    svg, = gambar(render_pertanyaan(penyajian_dari_soal(soal)))
    label = next(e for e in svg.findall(".//s:text", NS) if e.text == "15°")
    assert float(label.attrib["y"]) >= 146
