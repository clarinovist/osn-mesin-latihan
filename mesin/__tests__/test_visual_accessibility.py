"""Fase 8: ARIA, kontras numerik, dan informasi nonwarna pada SVG nyata."""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import design_tokens as T
from visual_security_helpers import (
    GAYA, KASUS, KELUARGA, elemen, gambar, kelas, kontras, lokal,
    panjang_garis, teks_svg,
)


@pytest.fixture(autouse=True)
def keluarga_aktif(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", ",".join(KELUARGA))


def _gambar(nama):
    return gambar(next(k for k in KASUS if k.nama == nama))


def _teks(svg):
    return tuple("".join(e.itertext()) for e in elemen(svg, "text"))


def _pola_arsir(svg, daerah):
    tautan = re.fullmatch(r"url\(#([^()]+)\)", daerah.get("fill", ""))
    assert tautan is not None, "Daerah harus dibedakan dengan pola, bukan warna saja"
    pola, = tuple(e for e in elemen(svg, "pattern") if e.get("id") == tautan[1])
    assert pola.get("patternUnits") == "userSpaceOnUse"
    assert float(pola.get("width")) > 0 and float(pola.get("height")) > 0
    ruas, = elemen(pola, "path")
    koordinat = re.fullmatch(r"M\s+([0-9.]+)\s+([0-9.]+)\s+L\s+([0-9.]+)\s+([0-9.]+)", ruas.get("d", ""))
    assert koordinat is not None
    x1, y1, x2, y2 = map(float, koordinat.groups())
    assert math.hypot(x2 - x1, y2 - y1) > 0
    assert float(ruas.get("stroke-width")) > 0
    assert kontras(ruas.get("stroke"), T.LATAR_KARTU) >= 3


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
@pytest.mark.parametrize("gaya", GAYA)
def test_title_desc_aria_terhubung_ke_node_bermakna(kasus, gaya):
    svg = gambar(kasus, gaya=gaya)
    judul, = elemen(svg, "title")
    uraian, = elemen(svg, "desc")
    ids = {e.get("id"): e for e in svg.iter() if e.get("id")}
    label = svg.get("aria-labelledby", "").split()
    deskripsi = svg.get("aria-describedby", "").split()
    assert svg.get("role") == "img"
    assert label and len(set(label)) == len(label)
    assert judul.get("id") in label
    assert uraian.get("id") in label + deskripsi
    assert all(i in ids for i in label + deskripsi)
    assert all(lokal(ids[i]) in {"title", "desc"} for i in label + deskripsi)
    assert "".join(judul.itertext()).strip()
    assert len("".join(uraian.itertext()).split()) >= 4
    assert all(e.get("aria-hidden") != "true" for e in (svg, judul, uraian))


def test_id_aria_dan_pola_unik_pada_lembar_campuran_dengan_soal_berulang():
    semua = tuple(gambar(k, namespace=f"lembar-8-soal-{i}-{ulangan}")
                  for i, k in enumerate(KASUS) for ulangan in range(2))
    ids = tuple(e.get("id") for svg in semua for e in svg.iter() if e.get("id"))
    assert len(ids) == len(set(ids))
    for svg in semua:
        lokal_ids = {e.get("id") for e in svg.iter() if e.get("id")}
        assert set(svg.get("aria-labelledby", "").split()) <= lokal_ids


@pytest.mark.parametrize("depan,belakang,harapan", (
    ("#000", "#fff", 21.0), ("#fff", "#fff", 1.0),
    ("#777777", "#ffffff", 4.478089453577214),
))
def test_oracle_kontras_memakai_luminansi_srgb_bukan_selisih_hex(depan, belakang, harapan):
    assert kontras(depan, belakang) == pytest.approx(harapan)
    assert kontras(belakang, depan) == pytest.approx(harapan)


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
@pytest.mark.parametrize("latar", (T.LATAR_KARTU, T.LATAR_MURID))
def test_paint_svg_memakai_token_dan_teks_kontras_wcag_aa(kasus, latar):
    svg = gambar(kasus)
    warna_token = frozenset(v.casefold() for v in vars(T).values()
                           if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", v))
    for e in svg.iter():
        for atribut in ("fill", "stroke"):
            warna = e.get(atribut, "")
            if warna.startswith("#"):
                assert warna.casefold() in warna_token, (kasus.nama, atribut, warna)
    for label in elemen(svg, "text"):
        if not "".join(label.itertext()).strip():
            continue
        assert float(label.attrib["font-size"]) > 0
        warna = label.get("fill")
        assert warna is not None, "Label wajib menyatakan warna dari token"
        assert kontras(warna, latar) >= 4.5, (kasus.nama, warna, latar)


@pytest.mark.parametrize("nama", ("turus", "piktogram", "datar-balik", "ruang-balik", "waktu", "petak", "venn", "korek", "titik"))
def test_geometri_informatif_tetap_kontras_setelah_grayscale(nama):
    svg = _gambar(nama)
    bentuk = tuple(e for e in svg.iter() if lokal(e) in
                   {"line", "circle", "rect", "polygon", "polyline", "path"})
    assert bentuk
    for e in bentuk:
        tinta = e.get("stroke") or e.get("fill")
        assert tinta and tinta != "none"
        # Grayscale berbasis luminansi mempertahankan rasio ini, bukan hue.
        assert kontras(tinta, T.LATAR_KARTU) >= 3, (nama, e.tag, tinta)


@pytest.mark.parametrize("nama,kelas_daerah", (
    ("lingkaran", "sektor-data"), ("arsiran", "daerah-arsir-tengah"),
))
def test_arsiran_terhubung_ke_pola_bergaris_nyata_bukan_warna(nama, kelas_daerah):
    svg = _gambar(nama)
    daerah, = kelas(svg, kelas_daerah)
    _pola_arsir(svg, daerah)
    assert daerah.get("d", "").endswith("Z")
    assert kontras(daerah.get("stroke"), T.LATAR_KARTU) >= 3
    if nama == "lingkaran":
        assert "Daerah bergaris: Membaca" in _teks(svg)
        assert "Membaca: 30 siswa; sudut ?" in _teks(svg)


def test_statistika_bisa_dibaca_dari_posisi_jumlah_dan_legenda_tanpa_warna():
    batang = _gambar("batang")
    skala = kelas(batang, "skala")
    awal, berikut = skala[:2]
    unit = (float(awal.get("y")) - float(berikut.get("y"))) / int(berikut.text)
    batang_data = kelas(batang, "batang-data")
    assert len(batang_data) == 3
    assert tuple(float(b.get("height")) / unit for b in batang_data) == pytest.approx((7, 13, 21))
    assert {"B1", "B2", "B3"} <= set(_teks(batang))
    assert len({b.get("fill") for b in batang_data}) == 1
    for b in batang_data:
        assert kontras(b.get("fill"), T.LATAR_KARTU) >= 3
    turus = kelas(_gambar("turus"), "baris-data")
    assert tuple(len(elemen(b, "line")) for b in turus) == (7, 13, 21)
    assert tuple(sum(g.get("x1") != g.get("x2") for g in elemen(b, "line")) for b in turus) == (1, 2, 4)
    pikto = _gambar("piktogram")
    assert tuple(len(elemen(b, "circle")) for b in kelas(pikto, "baris-data")) == (2, 3, 4)
    assert "1 gambar = 5 buah" in _teks(pikto)


def test_rusuk_tersembunyi_berbeda_garis_bukan_hue():
    svg = _gambar("ruang-balik")
    rusuk = kelas(svg, "rusuk")
    putus = tuple(e for e in rusuk if e.get("stroke-dasharray"))
    utuh = tuple(e for e in rusuk if not e.get("stroke-dasharray"))
    assert len(putus) == 3 and len(utuh) == 9
    assert all(panjang_garis(e) > 0 for e in rusuk)
    assert len({e.get("stroke") for e in rusuk}) == 1
    assert all(all(float(n) > 0 for n in e.get("stroke-dasharray").split()) for e in putus)
    assert "s = ? cm" in _teks(svg) and "V = 64 cm³" in _teks(svg)


def test_jam_dibedakan_panjang_jarum_label_dan_target_kosong():
    svg = _gambar("waktu")
    jam, = kelas(svg, "jarum-jam")
    menit, = kelas(svg, "jarum-menit")
    assert 0 < panjang_garis(jam) < panjang_garis(menit)
    assert jam.get("stroke") == menit.get("stroke")
    assert len(kelas(svg, "tanda-jam")) == 12
    target, = kelas(svg, "waktu-target")
    assert target.text == "?" and float(target.get("x")) > float(jam.get("x1"))
    assert {"Mulai", "Selesai", "21.47", "Durasi: 4 jam 38 menit"} <= set(_teks(svg))


def test_venn_nama_dan_irisan_dapat_dibaca_tanpa_warna():
    svg = _gambar("venn")
    himpunan = kelas(svg, "himpunan")
    assert len(himpunan) == 2
    assert all(e.get("fill") == "none" for e in himpunan)
    a, b = himpunan
    assert float(a.get("cx")) < float(b.get("cx"))
    irisan, = kelas(svg, "irisan-diberikan")
    assert irisan.text == "7"
    for e in himpunan:
        jarak = math.hypot(float(irisan.get("x")) - float(e.get("cx")),
                           float(irisan.get("y")) - float(e.get("cy")))
        assert jarak < float(e.get("r"))
    assert {"A", "B", "Total A = 19", "Total B = 23"} <= set(_teks(svg))


def test_pola_dihitung_dari_ruas_dan_titik_bukan_warna_atau_anotasi():
    korek, titik = _gambar("korek"), _gambar("titik")
    tahap_korek = tuple(e for e in elemen(korek, "g") if e.get("data-gambar"))
    tahap_titik = tuple(e for e in elemen(titik, "g") if e.get("data-gambar"))
    assert tuple(len(elemen(g, "line")) for g in tahap_korek) == (4, 7, 10)
    assert tuple(len(elemen(g, "circle")) for g in tahap_titik) == (1, 3, 6, 10)
    assert set(_teks(korek)) == {"Gambar 1", "Gambar 2", "Gambar 3"}
    assert set(_teks(titik)) == {"Gambar 1", "Gambar 2", "Gambar 3", "Gambar 4"}
    for g in tahap_korek:
        ujung = {(float(c.get("cx")), float(c.get("cy"))) for c in elemen(g, "circle")}
        for garis in elemen(g, "line"):
            assert (float(garis.get("x1")), float(garis.get("y1"))) in ujung
            assert (float(garis.get("x2")), float(garis.get("y2"))) in ujung


@pytest.mark.parametrize("nama,target", (
    ("batang", "13"), ("datar-balik", "84"), ("ruang-balik", "4"),
    ("waktu", "02.25"), ("venn", "35"), ("korek", "61"),
))
def test_target_enam_keluarga_tidak_ditulis_di_label_atau_alternatif(nama, target):
    svg = _gambar(nama)
    # Hanya token angka pada label/title/desc; bukan substring seluruh HTML.
    angka = tuple(n for teks in teks_svg(svg) for n in re.findall(r"\d+(?:[.,]\d+)?", teks))
    assert target not in angka, (nama, target, teks_svg(svg))
    assert all(not any(k in e.attrib for k in ("data-answer", "data-kunci", "data-target"))
               for e in svg.iter())
