"""Fase 0: audit matematis SVG yang sudah aktif."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from topic_number_patterns import korek_api  # noqa: E402
from topic_number_patterns_svg import _badan_khusus, _svg_korek, _svg_titik  # noqa: E402

NS = {"svg": "http://www.w3.org/2000/svg"}


def _grup(svg: str):
    akar = ET.fromstring(svg)
    return {int(g.attrib["data-gambar"]): g for g in akar.findall("svg:g", NS)}


def _ruas(g):
    return [
        ((line.attrib["x1"], line.attrib["y1"]),
         (line.attrib["x2"], line.attrib["y2"]))
        for line in g.findall("svg:line", NS)
    ]


def _tersambung(ruas):
    tetangga = defaultdict(set)
    for a, b in ruas:
        tetangga[a].add(b)
        tetangga[b].add(a)
    mulai = next(iter(tetangga))
    terlihat = {mulai}
    antre = deque([mulai])
    while antre:
        for titik in tetangga[antre.popleft()]:
            if titik not in terlihat:
                terlihat.add(titik)
                antre.append(titik)
    return terlihat == set(tetangga)


def test_korek_semua_kombinasi_generator_lama_memiliki_ruas_tepat_dan_tersambung():
    for awal in range(3, 8):
        for tambah in (2, 3, 4):
            grup = _grup(_svg_korek(3, awal, tambah))
            assert set(grup) == {1, 2, 3}
            for gambar_ke, g in grup.items():
                ruas = _ruas(g)
                harapan = awal + tambah * (gambar_ke - 1)
                assert len(ruas) == harapan, (awal, tambah, gambar_ke)
                unik = {tuple(sorted((a, b))) for a, b in ruas}
                assert len(unik) == harapan
                assert _tersambung(ruas)
                assert g.attrib["data-ruas"] == str(harapan)


def test_setiap_gambar_korek_adalah_superset_ketat_gambar_sebelumnya():
    """Pertumbuhan tidak boleh mengganti atau menghapus ruas yang sudah ada."""
    for awal in range(3, 8):
        for tambah in (2, 3, 4):
            grup = _grup(_svg_korek(3, awal, tambah))
            sebelumnya = set()
            for gambar_ke, g in sorted(grup.items()):
                sekarang = {
                    tuple(sorted((a, b)))
                    for a, b in _ruas(g)
                }
                if gambar_ke > 1:
                    assert sebelumnya < sekarang, (awal, tambah, gambar_ke)
                    assert len(sekarang - sebelumnya) == tambah
                sebelumnya = sekarang


def _teks_aksesibel(akar):
    title = akar.find("svg:title", NS)
    desc = akar.find("svg:desc", NS)
    return title, desc, " ".join(e.text or "" for e in (title, desc))


def test_svg_aktif_mengaitkan_nama_dan_deskripsi_dengan_id_unik():
    svg_semua = (
        _svg_korek(1, 4, 3),
        _svg_korek(2, 4, 3),
        _svg_titik(1),
        _svg_titik(2),
    )
    semua_id = set()
    for svg in svg_semua:
        akar = ET.fromstring(svg)
        title, desc, _ = _teks_aksesibel(akar)
        assert akar.attrib["role"] == "img"
        assert "aria-label" not in akar.attrib
        assert title is not None and desc is not None
        title_id, desc_id = title.attrib["id"], desc.attrib["id"]
        assert akar.attrib["aria-labelledby"].split() == [title_id, desc_id]
        assert title_id not in semua_id
        assert desc_id not in semua_id
        semua_id.update((title_id, desc_id))


def _svg_dari_badan(badan):
    assert badan is not None
    svg = "<svg" + badan.split("<svg", 1)[1].split("</svg>", 1)[0] + "</svg>"
    return ET.fromstring(svg)


def test_renderer_produksi_memberi_namespace_per_identitas_soal():
    pertama = _svg_dari_badan(_badan_khusus(
        korek_api(awal=4, tambah=3, gambar_ke=8)
    ))
    kedua = _svg_dari_badan(_badan_khusus(
        korek_api(awal=4, tambah=3, gambar_ke=9)
    ))
    assert pertama.attrib["aria-labelledby"] != kedua.attrib["aria-labelledby"]


def test_namespace_svg_opsional_mencegah_tabrakan_untuk_konten_sama():
    pertama = ET.fromstring(_svg_korek(3, 4, 3, namespace="soal-1"))
    kedua = ET.fromstring(_svg_korek(3, 4, 3, namespace="soal-2"))
    assert pertama.attrib["aria-labelledby"] != kedua.attrib["aria-labelledby"]
    assert _svg_korek(3, 4, 3, namespace="soal-1") == _svg_korek(
        3, 4, 3, namespace="soal-1"
    )


def test_label_aksesibel_mengikuti_jumlah_tahap_yang_ditampilkan():
    for renderer, argumen in ((_svg_korek, (4, 3)), (_svg_titik, ())):
        for n_tampil in (1, 2, 5):
            akar = ET.fromstring(renderer(n_tampil, *argumen))
            _, _, teks = _teks_aksesibel(akar)
            assert f"{n_tampil} tahap pola" in teks.lower()
            for jumlah_lain in (1, 2, 3, 4, 5):
                if jumlah_lain != n_tampil:
                    assert f"{jumlah_lain} tahap pola" not in teks.lower()


def test_deskripsi_aksesibel_tidak_membocorkan_target():
    for svg, target in ((_svg_korek(3, 4, 3), "20"), (_svg_titik(4), "15")):
        akar = ET.fromstring(svg)
        _, _, teks_aksesibel = _teks_aksesibel(akar)
        assert target not in teks_aksesibel


def test_renderer_korek_memakai_narasi_pertumbuhan_batang_yang_jujur():
    badan = _badan_khusus(korek_api(awal=4, tambah=3, gambar_ke=8))
    assert badan is not None
    assert "pola batang korek api bertumbuh" in badan.lower()
    assert "segitiga" not in badan.lower()


def test_svg_tidak_menyimpan_warna_hex_di_renderer():
    sumber = Path(__file__).resolve().parent.parent / "topic_number_patterns_svg.py"
    assert "#000" not in sumber.read_text(encoding="utf-8")


def test_titik_segitiga_memiliki_jumlah_dan_koordinat_unik():
    for n_tampil in range(1, 8):
        grup = _grup(_svg_titik(n_tampil))
        assert set(grup) == set(range(1, n_tampil + 1))
        for gambar_ke, g in grup.items():
            lingkaran = g.findall("svg:circle", NS)
            harapan = gambar_ke * (gambar_ke + 1) // 2
            assert len(lingkaran) == harapan
            koordinat = {(c.attrib["cx"], c.attrib["cy"]) for c in lingkaran}
            assert len(koordinat) == harapan
            assert g.attrib["data-titik"] == str(harapan)
