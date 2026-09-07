"""Invariant matematis SVG geometri datar, dihitung dari koordinat."""
from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import design_tokens as T

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
NS = {"s": "http://www.w3.org/2000/svg"}


def gambar(data, namespace="butir-1"):
    from plane_geometry_svg import render_geometri_datar
    akar = ET.fromstring(render_geometri_datar(data, namespace))
    assert akar.tag == "{http://www.w3.org/2000/svg}svg"
    return akar


def titik(path):
    return [tuple(map(float, p.split(","))) for p in path.get("points").split()]


def teks(akar):
    return " ".join("".join(t.itertext()) for t in akar.findall(".//s:text", NS))


SEMUA_MODEL = [
    {"model": "sudut_pasangan", "total": 90, "diketahui": 35},
    {"model": "sudut_rasio", "kali": 4},
    {"model": "segitiga_sudut", "a": 45, "b": 65},
    {"model": "segitiga_rasio", "p": 1, "q": 2, "r": 3},
    {"model": "segitiga_luar", "a": 50, "b": 35},
    {"model": "persegi_panjang", "p": 12, "l": 7},
    {"model": "persegi_panjang_balik", "p": 12, "K": 38},
    {"model": "segitiga_tinggi", "a": 6, "t": 8, "s": 10},
    {"model": "jajargenjang", "a": 6, "t": 8, "s": 10},
    {"model": "trapesium", "a": 8, "b": 14, "t": 5},
    {"model": "ketupat", "d1": 12, "d2": 8},
    {"model": "ketupat_balik", "L": 60, "d1": 12},
    {"model": "lingkaran", "r": 7},
    {"model": "juring", "s": 270, "r": 7},
    {"model": "arsiran_pojok", "r": 7},
    {"model": "jalan", "luar": 18, "dalam": 10},
    {"model": "kisi", "p": 5, "l": 3, "satuan": "cm"},
    {"model": "simetri_persegi", "ukuran": 8, "satuan": "cm"},
    {"model": "simetri_segitiga", "ukuran": 8, "satuan": "cm"},
    {"model": "simetri_ketupat", "ukuran": 8, "satuan": "cm"},
    {"model": "simetri_persegi_panjang", "ukuran": 10, "lebar": 6, "satuan": "cm"},
]


@pytest.mark.parametrize("data", SEMUA_MODEL, ids=lambda d: d["model"])
def test_semua_21_model_menghasilkan_svg_valid_responsif(data):
    akar = gambar(data)
    assert akar.get("class") == "soal-visual"
    assert akar.get("viewBox")
    assert akar.get("role") == "img"
    assert akar.find("s:title", NS) is not None
    assert akar.find("s:desc", NS) is not None
    assert not akar.findall(".//s:script", NS)
    assert not any(k.startswith("on") for e in akar.iter() for k in e.attrib)
    assert "Tidak berskala" not in teks(akar) if data["model"] == "kisi" else "Tidak berskala" in teks(akar)


def test_validator_wajib_tersedia_dan_input_tidak_dikenal_gagal(monkeypatch):
    import plane_geometry_svg

    def tanpa_validator(_data):
        raise ImportError("validator hilang")

    monkeypatch.setattr(plane_geometry_svg, "validasi_data", tanpa_validator)
    with pytest.raises(ImportError, match="validator hilang"):
        plane_geometry_svg.render_geometri_datar(
            {"model": "lingkaran", "r": 7}, "uji-validator"
        )
    monkeypatch.undo()
    with pytest.raises(ValueError, match="model geometri"):
        gambar({"model": "tidak-dikenal"})


def test_namespace_sha_deterministik_dan_aman_dari_injeksi():
    data = {"model": "juring", "s": 270, "r": 7}
    namespace = '\" onload="jahat<script>'
    a, b = gambar(data, namespace), gambar(data, namespace)
    ids = {e.get("id") for e in a.iter() if e.get("id")}
    awalan = "geo-" + hashlib.sha256(namespace.encode()).hexdigest()[:20]
    assert ids and all(i.startswith(awalan) for i in ids)
    assert ET.tostring(a) == ET.tostring(b)
    assert "jahat" not in ET.tostring(a, encoding="unicode")


@pytest.mark.parametrize("total,diketahui", [(90, 35), (180, 65)])
def test_sudut_pasangan_memiliki_sinar_dengan_total_geometris(total, diketahui):
    akar = gambar({"model": "sudut_pasangan", "total": total, "diketahui": diketahui})
    sinar = akar.findall('.//s:line[@class="sinar-sudut"]', NS)
    pusat = tuple(map(float, (sinar[0].get("x1"), sinar[0].get("y1"))))
    arah = []
    for garis in sinar:
        x, y = float(garis.get("x2")) - pusat[0], pusat[1] - float(garis.get("y2"))
        arah.append(math.degrees(math.atan2(y, x)) % 360)
    bentang = (max(arah) - min(arah)) % 360
    assert bentang == pytest.approx(total, abs=0.001)
    assert f"{diketahui}°" in teks(akar) and "?" in teks(akar)
    assert f"{total-diketahui}°" not in teks(akar)


def test_sudut_rasio_hanya_memuat_x_dan_kx_tanpa_jawaban_numerik():
    akar = gambar({"model": "sudut_rasio", "kali": 4})
    assert "x" in teks(akar) and "4x" in teks(akar)
    assert "36" not in teks(akar) and "144" not in teks(akar)


def test_sudut_segitiga_dan_luar_ditempatkan_pada_vertex_yang_benar():
    dalam = gambar({"model": "segitiga_sudut", "a": 45, "b": 65})
    label = {e.get("data-vertex"): "".join(e.itertext()) for e in dalam.findall('.//s:text[@class="label-sudut"]', NS)}
    assert label == {"A": "45°", "B": "65°", "C": "?"}

    luar = gambar({"model": "segitiga_luar", "a": 50, "b": 35})
    label = {e.get("data-vertex"): "".join(e.itertext()) for e in luar.findall('.//s:text[@class="label-sudut"]', NS)}
    assert label == {"A": "50°", "C": "35°", "B-luar": "?"}
    sisi = luar.find('.//s:polyline[@class="alas-diperpanjang"]', NS)
    p = titik(sisi)
    assert p[0][1] == pytest.approx(p[1][1]) == pytest.approx(p[2][1])
    assert p[2][0] > p[1][0]
    assert luar.find('.//s:path[@class="busur-target-luar"]', NS) is not None


def test_rasio_segitiga_memakai_koefisien_bukan_hasil_sudut():
    akar = gambar({"model": "segitiga_rasio", "p": 1, "q": 2, "r": 3})
    assert {"x", "2x", "3x"} <= set(t.text for t in akar.findall('.//s:text[@class="label-sudut"]', NS))
    assert not {"30°", "60°", "90°"} & set(teks(akar).split())


def _luas_polygon(daftar):
    return abs(sum(
        daftar[i][0] * daftar[(i+1) % len(daftar)][1]
        - daftar[(i+1) % len(daftar)][0] * daftar[i][1]
        for i in range(len(daftar))
    )) / 2


@pytest.mark.parametrize("model,faktor", [("segitiga_tinggi", 0.5), ("jajargenjang", 1.0)])
def test_luas_dan_sisi_sejajar_bangun_tinggi_benar(model, faktor):
    akar = gambar({"model": model, "a": 12, "t": 8, "s": 10})
    bangun = akar.find(f'.//s:polygon[@class="{"segitiga" if model == "segitiga_tinggi" else "jajargenjang"}"]', NS)
    p = titik(bangun)
    alas = math.dist(p[0], p[1])
    tinggi = abs(p[0][1] - p[-1][1])
    assert _luas_polygon(p) == pytest.approx(faktor * alas * tinggi)
    if model == "jajargenjang":
        bawah = (p[1][0]-p[0][0], p[1][1]-p[0][1])
        atas = (p[2][0]-p[3][0], p[2][1]-p[3][1])
        kiri = (p[3][0]-p[0][0], p[3][1]-p[0][1])
        kanan = (p[2][0]-p[1][0], p[2][1]-p[1][1])
        assert bawah == pytest.approx(atas)
        assert kiri == pytest.approx(kanan)


@pytest.mark.parametrize("model", ["segitiga_tinggi", "jajargenjang"])
def test_tinggi_tegak_sisi_miring_dan_kaki_eksternal_sah(model):
    # sqrt(10²-8²)=6 > alas 4, jadi kaki tinggi harus di luar alas.
    akar = gambar({"model": model, "a": 4, "t": 8, "s": 10})
    tinggi = akar.find('.//s:line[@class="tinggi"]', NS)
    miring = akar.find('.//s:line[@class="sisi-miring"]', NS)
    siku = akar.find('.//s:polyline[@class="tanda-siku"]', NS)
    tx1, tx2 = float(tinggi.get("x1")), float(tinggi.get("x2"))
    assert tx1 == pytest.approx(tx2)
    panjang_miring = math.hypot(float(miring.get("x2"))-float(miring.get("x1")), float(miring.get("y2"))-float(miring.get("y1")))
    panjang_tinggi = abs(float(tinggi.get("y2"))-float(tinggi.get("y1")))
    assert panjang_miring / panjang_tinggi == pytest.approx(10/8)
    if model == "jajargenjang":
        assert len(akar.findall('.//s:line[@class="sisi-miring"]', NS)) == 2
    assert titik(siku)[0][0] == pytest.approx(tx1)
    alas = akar.find('.//s:line[@class="alas"]', NS)
    if model == "segitiga_tinggi":
        assert tx1 > max(float(alas.get("x1")), float(alas.get("x2")))
    else:
        assert tx1 == pytest.approx(float(alas.get("x1")))


def test_auto_fit_semua_parameter_tinggi_tetap_di_viewbox_dan_label_terpisah():
    for model in ("segitiga_tinggi", "jajargenjang"):
        for data in (
            {"model": model, "a": 4, "t": 20, "s": 39},
            {"model": model, "a": 40, "t": 16, "s": 17},
            {"model": model, "a": 16, "t": 5, "s": 8},
        ):
            akar = gambar(data)
            for elemen in akar.findall(".//s:line", NS):
                for nama in ("x1", "x2"):
                    assert 0 <= float(elemen.get(nama)) <= T.GEO_LEBAR
                for nama in ("y1", "y2"):
                    assert 0 <= float(elemen.get(nama)) <= T.GEO_TINGGI
            label = [e for e in akar.findall(".//s:text", NS) if (e.text or "").startswith(("t =", "s ="))]
            assert len(label) == 2
            assert abs(float(label[0].get("y"))-float(label[1].get("y"))) >= T.GEO_FONT


def test_persegi_panjang_dan_trapesium_menjaga_rasio_dimensi_diketahui():
    pp = gambar({"model": "persegi_panjang", "p": 20, "l": 5})
    rect = pp.find('.//s:rect[@class="persegi-panjang"]', NS)
    assert float(rect.get("width")) / float(rect.get("height")) == pytest.approx(4)
    trap = gambar({"model": "trapesium", "a": 8, "b": 14, "t": 5})
    poly = titik(trap.find('.//s:polygon[@class="trapesium"]', NS))
    assert math.dist(poly[0], poly[1]) / math.dist(poly[2], poly[3]) == pytest.approx(14/8)
    assert abs(poly[0][1]-poly[3][1]) / math.dist(poly[0], poly[1]) == pytest.approx(5/14)
    ketupat = gambar({"model": "ketupat", "d1": 12, "d2": 8})
    belah = titik(ketupat.find('.//s:polygon[@class="ketupat"]', NS))
    diagonal_h = math.dist(belah[1], belah[3])
    diagonal_v = math.dist(belah[0], belah[2])
    assert diagonal_h / diagonal_v == pytest.approx(12/8)


def test_persegi_panjang_balik_dan_ketupat_balik_tidak_menghitung_target():
    pp = gambar({"model": "persegi_panjang_balik", "p": 12, "K": 38})
    assert "12 cm" in teks(pp) and "K = 38 cm" in teks(pp) and "?" in teks(pp)
    assert "7 cm" not in teks(pp)
    ketupat = gambar({"model": "ketupat_balik", "L": 60, "d1": 12})
    assert "L = 60" in teks(ketupat) and "12 cm" in teks(ketupat) and "?" in teks(ketupat)
    assert "10 cm" not in teks(ketupat)


def test_juring_270_derajat_memakai_arc_besar_dan_endpoint_benar():
    akar = gambar({"model": "juring", "s": 270, "r": 7})
    path = akar.find('.//s:path[@class="juring"]', NS)
    bagian = path.get("d").split()
    cx, cy = map(float, bagian[1:3])
    sx, sy = map(float, bagian[4:6])
    ex, ey = map(float, bagian[-3:-1])
    assert bagian[10] == "1"
    assert math.hypot(sx-cx, sy-cy) == pytest.approx(math.hypot(ex-cx, ey-cy), abs=0.001)
    aktual = math.degrees(math.atan2(ex-cx, cy-ey)) % 360
    assert aktual == pytest.approx(270, abs=0.001)


def test_arsiran_pojok_hanya_area_tengah_dengan_empat_busur_seperempat():
    akar = gambar({"model": "arsiran_pojok", "r": 7})
    daerah = akar.find('.//s:path[@class="daerah-arsir-tengah"]', NS)
    assert daerah is not None and daerah.get("fill", "").startswith("url(#")
    d = daerah.get("d")
    assert d.count(" A ") == 4
    assert d.count(" 0 0 0 ") == 4  # busur cekung menuju pusat, bukan lingkaran tengah
    # Sampling independen: pusat persegi masuk arsiran, empat titik dekat
    # sudut berada di dalam seperempat lingkaran dan harus dibuang.
    def di_tengah(x, y, sisi=160.0):
        sudut = ((0.0, 0.0), (sisi, 0.0), (sisi, sisi), (0.0, sisi))
        return all(math.hypot(x-cx, y-cy) >= sisi/2 for cx, cy in sudut)
    resolusi = 300
    kena = sum(
        di_tengah((i+.5)*160/resolusi, (j+.5)*160/resolusi)
        for i in range(resolusi) for j in range(resolusi)
    )
    luas_sample = kena * (160/resolusi) ** 2
    luas_harapan = 160 ** 2 - math.pi * 80 ** 2
    assert luas_sample == pytest.approx(luas_harapan, rel=0.01)
    assert not akar.findall('.//s:path[@class="seperempat-diarsir"]', NS)


def test_jalan_adalah_ring_arsir_dengan_bagian_dalam_putih():
    akar = gambar({"model": "jalan", "luar": 18, "dalam": 10})
    luar = akar.find('.//s:rect[@class="jalan-luar"]', NS)
    dalam = akar.find('.//s:rect[@class="taman-dalam"]', NS)
    assert luar.get("fill", "").startswith("url(#")
    assert dalam.get("fill") != luar.get("fill")
    assert float(dalam.get("x")) > float(luar.get("x"))
    assert float(dalam.get("width")) < float(luar.get("width"))


def test_kisi_tepat_p_kali_l_sel_persegi_sama_dan_tanpa_label_dimensi():
    akar = gambar({"model": "kisi", "p": 5, "l": 3, "satuan": "cm"})
    sel = akar.findall('.//s:rect[@class="sel-kisi"]', NS)
    assert len(sel) == 15
    assert len({(e.get("width"), e.get("height")) for e in sel}) == 1
    assert all(e.get("width") == e.get("height") for e in sel)
    isi = teks(akar)
    assert "Sisi setiap kotak = 1 cm" in isi
    label_data = " ".join(
        "".join(e.itertext()) for e in akar.findall('.//s:text[@class="label-data"]', NS)
    )
    assert "5" not in label_data and "3" not in label_data and "15" not in label_data


def test_segitiga_simetri_benar_benar_sama_sisi():
    akar = gambar({"model": "simetri_segitiga", "ukuran": 8, "satuan": "cm"})
    bangun = akar.find('.//s:polygon[@class="bangun-simetri"]', NS)
    p = titik(bangun)
    sisi = [math.dist(p[i], p[(i+1) % 3]) for i in range(3)]
    assert max(sisi) - min(sisi) < 0.001


def test_jalan_label_tidak_bertumpuk_catatan_skala():
    akar = gambar({"model": "jalan", "luar": 18, "dalam": 10})
    label = akar.find('.//s:text[@class="label-jalan"]', NS)
    catatan = akar.find('.//s:text[@class="catatan-skala"]', NS)
    assert abs(float(label.get("y")) - float(catatan.get("y"))) >= 1.5 * T.GEO_FONT


@pytest.mark.parametrize("data", SEMUA_MODEL[-4:], ids=lambda d: d["model"])
def test_bangun_simetri_tanpa_sumbu_diagonal_atau_petunjuk(data):
    akar = gambar(data)
    kelas = " ".join(e.get("class", "") for e in akar.iter())
    isi = teks(akar).lower()
    assert "sumbu" not in kelas and "diagonal" not in kelas
    assert "sumbu" not in isi and "lipat" not in isi
    assert not akar.findall(".//s:line", NS)


def test_ringkasan_fakta_aman_tidak_menghitung_target():
    from plane_geometry_svg import ringkasan_geometri_datar
    assert ringkasan_geometri_datar({"model": "persegi_panjang_balik", "p": 12, "K": 38}) == (
        "Fakta visual: persegi panjang memiliki panjang 12 cm, keliling 38 cm, dan lebar belum diberi nilai."
    )
    hasil = ringkasan_geometri_datar({"model": "ketupat_balik", "L": 60, "d1": 12})
    assert "60 cm²" in hasil and "12 cm" in hasil and "belum diberi nilai" in hasil
    assert "10 cm" not in hasil
