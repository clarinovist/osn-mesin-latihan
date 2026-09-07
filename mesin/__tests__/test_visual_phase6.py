"""Kontrak visual terbatas: lintasan grid dan fakta waktu, tanpa solusi."""
from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import question_views as q
import topic_combinatorics as kombinatorik
import topic_measurement as pengukuran
from visual_contract import DescriptorVisual
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan


def _svg(penyajian, namespace="fixture"):
    halaman = render_pertanyaan(penyajian, namespace=namespace)
    return ET.fromstring(halaman[halaman.index("<svg"):halaman.index("</svg>") + 6])


def _kelas(svg, nama):
    return [e for e in svg.iter() if e.get("class") == nama]


@pytest.mark.parametrize("b,k", ((1, 1), (1, 24), (24, 1), (12, 13), (7, 5)))
def test_grid_node_edge_dan_jalur_dari_geometri_aktual(monkeypatch, b, k):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "kombinatorik")
    soal = kombinatorik.jalur_petak(b, k)
    penyajian = q.penyajian_dari_soal(soal)
    assert penyajian.mode_representasi == "jalur_petak-v1"
    assert dict(penyajian.descriptor.data) == {"b": b, "k": k}
    svg = _svg(penyajian)
    titik = {(float(e.get("cx")), float(e.get("cy"))) for e in _kelas(svg, "titik-petak")}
    assert len(titik) == (b + 1) * (k + 1)
    sisi = [((float(e.get("x1")), float(e.get("y1"))),
             (float(e.get("x2")), float(e.get("y2")))) for e in _kelas(svg, "sisi-petak")]
    assert len(sisi) == b * (k + 1) + k * (b + 1)
    assert len(set(sisi)) == len(sisi)
    assert all(a in titik and z in titik for a, z in sisi)
    xs, ys = sorted({x for x, y in titik}), sorted({y for x, y in titik})
    assert len(xs) == k + 1 and len(ys) == b + 1
    # Hitung rute dari edge yang benar-benar digambar, bukan data descriptor.
    from functools import lru_cache
    @lru_cache(None)
    def banyak(tujuan):
        if tujuan == (xs[0], ys[0]):
            return 1
        return sum(banyak(a) for a, z in sisi if z == tujuan)
    assert banyak((xs[-1], ys[-1])) == int(soal.kunci)
    assert not _kelas(svg, "rute-solusi")
    assert not _kelas(svg, "jumlah-jalur")
    assert "A" in "".join(svg.itertext()) and "B" in "".join(svg.itertext())


@pytest.mark.parametrize("b,k", ((24, 1), (12, 13)))
def test_label_b_berjarak_dari_keterangan_grid(monkeypatch, b, k):
    import design_tokens as T
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "kombinatorik")
    svg = _svg(q.penyajian_dari_soal(kombinatorik.jalur_petak(b, k)))
    label_b, = [e for e in svg.iter() if e.text == "B"]
    catatan, = [e for e in svg.iter() if e.tag.endswith("text") and "baris" in (e.text or "")]
    assert float(catatan.attrib["y"]) - float(label_b.attrib["y"]) >= 2 * T.GEO_FONT


@pytest.mark.parametrize("varian,field", (
    ("cari_mulai", {"varian", "selesai", "durasi"}),
    ("cari_selesai", {"varian", "mulai", "durasi"}),
    ("cari_durasi", {"varian", "mulai", "selesai"}),
))
def test_jam_hanya_memproyeksikan_fakta_diberikan(monkeypatch, varian, field):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran")
    soal = pengukuran.jam_selesai(varian, 21, 47, 4, 38)
    penyajian = q.penyajian_dari_soal(soal)
    assert penyajian.mode_representasi == "linimasa_jam-v1"
    assert set(penyajian.descriptor.data) == field
    assert "?" in "".join(_svg(penyajian).itertext())
    assert soal.kunci not in penyajian.teks_soal
    gabung = render_pertanyaan(penyajian) + ringkasan_pertanyaan(penyajian)
    assert soal.kunci not in gabung
    assert not any(k in gabung for k in ("malrule", "kode_final", "kunci", "pembahasan"))


@pytest.mark.parametrize("jam,menit", ((0, 0), (3, 15), (11, 59), (21, 47)))
def test_jarum_jam_bergerak_sesuai_menit(monkeypatch, jam, menit):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran")
    soal = pengukuran.jam_selesai("cari_selesai", jam, menit, 2, 38)
    svg = _svg(q.penyajian_dari_soal(soal))
    for nama, sudut in (("jarum-jam", (jam % 12) * 30 + menit / 2),
                       ("jarum-menit", menit * 6)):
        elemen, = _kelas(svg, nama)
        dx = float(elemen.get("x2")) - float(elemen.get("x1"))
        dy = float(elemen.get("y2")) - float(elemen.get("y1"))
        aktual = math.degrees(math.atan2(dx, -dy)) % 360
        assert aktual == pytest.approx(sudut % 360, abs=0.0001)
    assert len(_kelas(svg, "tanda-jam")) == 12
    assert len(_kelas(svg, "jarum-jam")) == 1  # Target tidak digambar sebagai jam.


@pytest.mark.parametrize("jenis,data", (
    ("jalur_petak", {"b": True, "k": 2}),
    ("jalur_petak", {"b": 25, "k": 1}),
    ("jalur_petak", {"b": 2, "k": 2, "kunci": 6}),
    ("jalur_petak", {"b": 0, "k": 2}),
    ("linimasa_jam", {"varian": [], "mulai": 1, "durasi": 2}),
    ("linimasa_jam", {"varian": "cari_selesai", "mulai": 1, "durasi": 2, "selesai": 3}),
    ("linimasa_jam", {"varian": "cari_durasi", "mulai": 120, "selesai": 60}),
    ("linimasa_jam", {"varian": "cari_mulai", "selesai": 120, "durasi": 180}),
))
def test_descriptor_invalid_gagal_tertutup(jenis, data):
    with pytest.raises(ValueError):
        DescriptorVisual(jenis, 1, data)


def test_namespace_dan_snapshot_tidak_mutable(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "kombinatorik")
    penyajian = q.penyajian_dari_soal(kombinatorik.jalur_petak(3, 4))
    for namespace in ('a"><script>alert(1)</script>', "satu", "dua"):
        svg = _svg(penyajian, namespace)
        assert all("onload" not in e.attrib for e in svg.iter())
        assert all(e.tag.split("}")[-1] in {"svg", "title", "desc", "line", "circle", "text"}
                   for e in svg.iter())
    assert _svg(penyajian, "satu")[0].get("id") != _svg(penyajian, "dua")[0].get("id")
    with pytest.raises(TypeError):
        penyajian.descriptor.data["b"] = 99


def test_topik_di_luar_tranche_tetap_teks(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    for soal in (pengukuran.skala_peta("cari_peta", 10, 10, 100000),
                 pengukuran.jam_menit_detik("jam_ke_menit", 3, 0, 0, versi=2),
                 kombinatorik.aturan_kali(12, 17)):
        assert q.penyajian_dari_soal(soal).status_visual == "tanpa_visual"
