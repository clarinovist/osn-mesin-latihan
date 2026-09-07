"""Fase 8: palang XML nyata pada jalur proyeksi, snapshot, dan render."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from question_views import penyajian_dari_baris
from visual_contract import DescriptorVisual, serialisasi_kanonis, serialisasi_penyajian
from visual_renderer import render_pertanyaan
from visual_security_helpers import (
    GAYA, KASUS, KELUARGA, bangun_ulang, elemen, gambar, periksa_xml,
    snapshot, teks_svg,
)


@pytest.fixture(autouse=True)
def keluarga_aktif(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", ",".join(KELUARGA))


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
@pytest.mark.parametrize("gaya", GAYA)
def test_xml_allowlist_output_aktual_semua_keluarga(kasus, gaya):
    svg = gambar(kasus, gaya=gaya)
    assert elemen(svg, "text"), kasus.nama
    assert len(tuple(svg.iter())) > 4, "Visual kosong bukan keberhasilan palang"


NAMESPACE = (
    "uji-normal", '\" onload="uji', "<svg><script>uji</script></svg>",
    "url(https://contoh.invalid/gambar)", "../lain#judul", "dua id",
    "ｏｎｌｏａｄ", "оnload", "uji\x00id", "uji\x1fid", "uji\u202eid",
    "uji\u200bid", "uji\ud800id", "N" * 10000,
)


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
@pytest.mark.parametrize("namespace", NAMESPACE, ids=lambda s: ascii(s[:35]))
def test_namespace_ditolak_atau_diisolasi_tanpa_event_dan_fetch(kasus, namespace):
    penyajian = snapshot(kasus)
    try:
        hasil = render_pertanyaan(penyajian, namespace=namespace)
    except ValueError:
        return  # Penolakan eksplisit juga merupakan perilaku aman.
    svg = periksa_xml(hasil)
    assert hasil == render_pertanyaan(penyajian, namespace=namespace)
    ids = {e.get("id") for e in svg.iter() if e.get("id")}
    lain = gambar(kasus, namespace="namespace-pembanding")
    assert ids and ids.isdisjoint(e.get("id") for e in lain.iter())


PAYLOAD_LABEL = (
    '<script>uji</script>', '<image href="//contoh.invalid/a"/>',
    '<foreignObject>uji</foreignObject>', 'onload="uji"',
    '"/><g onfocus="uji">', '<!DOCTYPE svg>', '<?xml version="1.0"?>',
    "&lt;script&gt;", "&#x3c;svg&#x3e;", "Ａ＆Ｂ", "оnload", "ｏｎｌｏａｄ＝uji",
    "A & B", "3 < 5", "'kutip' dan \"ganda\"", "//contoh.invalid/a",
    "A\x00B", "A\x01B", "A\x1fB", "A\x7fB", "A\u202eB", "A\u200bB",
    "A\ud800B", "W" * 25, "W" * 10000,
)


@pytest.mark.parametrize("jenis", ("turus", "piktogram", "susunan_objek"))
@pytest.mark.parametrize("label", PAYLOAD_LABEL, ids=lambda s: ascii(s[:30]))
def test_label_berbahaya_hanya_boleh_menjadi_teks_atau_ditolak(jenis, label):
    nama = {"turus": "turus", "piktogram": "piktogram", "susunan_objek": "susunan"}[jenis]
    asal = snapshot(next(k for k in KASUS if k.nama == nama))
    assert asal.descriptor is not None
    data = asal.descriptor.ke_dict()["data"]
    field = "objek" if jenis == "susunan_objek" else "nama"
    baru = {**data, field: [label, *data[field][1:]]}
    try:
        descriptor = DescriptorVisual(jenis, 1, baru)
        hasil = render_pertanyaan(bangun_ulang(asal, descriptor=descriptor))
    except ValueError:
        return
    svg = periksa_xml(hasil)
    assert label in teks_svg(svg), "Label diizinkan harus utuh sebagai teks"
    # Label panjang harus ditolak sebelum menjadi teks tak terbatas.
    assert len(label) <= 24


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
@pytest.mark.parametrize("field", (
    "onload", "xmlns", "xlink:href", "style", "ｋｕｎｃｉ", "kuncі",
    "ku\u200bnci", "correctAnswer", "data-answer", "label",
))
def test_descriptor_setiap_keluarga_menolak_field_tambahan(kasus, field):
    descriptor = snapshot(kasus).descriptor
    assert descriptor is not None
    with pytest.raises(ValueError):
        DescriptorVisual(descriptor.jenis, descriptor.versi,
                         {**descriptor.data, field: "uji"})


@pytest.mark.parametrize("nama,field", (
    ("batang", "varian"), ("datar-balik", "model"), ("ruang-balik", "model"),
    ("waktu", "varian"), ("petak", "b"), ("korek", "n_tampil"),
))
@pytest.mark.parametrize("payload", PAYLOAD_LABEL, ids=lambda s: ascii(s[:30]))
def test_field_aktif_enam_keluarga_menolak_label_pada_enum_atau_angka(nama, field, payload):
    descriptor = snapshot(next(k for k in KASUS if k.nama == nama)).descriptor
    assert descriptor is not None
    with pytest.raises(ValueError):
        DescriptorVisual(descriptor.jenis, descriptor.versi,
                         {**descriptor.data, field: payload})


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
@pytest.mark.parametrize("gaya", GAYA)
def test_teks_soal_escaped_tanpa_menyisipkan_node_atau_atribut(kasus, gaya):
    payload = '<svg onload="uji"><image href="//contoh.invalid/a"/></svg> & Ａ'
    penyajian = bangun_ulang(snapshot(kasus), teks=payload + "\nPertanyaan tetap?")
    hasil = render_pertanyaan(penyajian, gaya=gaya)
    periksa_xml(hasil)
    from xml.etree import ElementTree as ET
    akar = ET.fromstring(hasil)
    assert payload in "".join(akar.itertext())
    assert "Pertanyaan tetap?" in "".join(akar.itertext())


def _baris_ditempa(kasus, field):
    """Hash dihitung ulang agar test menggigit schema, bukan mismatch hash."""
    soal = kasus.pembuat()
    muatan = json.loads(serialisasi_penyajian(snapshot(kasus)))
    descriptor = muatan["descriptor"]
    tanpa_sidik = {k: v for k, v in muatan.items() if k != "fingerprint_penyajian"}
    baru = {**tanpa_sidik, "descriptor": {
        **descriptor, "data": {**descriptor["data"], field: "uji"},
    }}
    sidik = hashlib.sha256(serialisasi_kanonis(baru).encode("utf-8")).hexdigest()
    lengkap = {**baru, "fingerprint_penyajian": sidik}
    return {
        **{k: v for k, v in lengkap.items() if k != "descriptor"},
        "penyajian_json": serialisasi_kanonis(lengkap),
        "parameter": json.dumps(soal.parameter), "template_id": soal.template_id,
        "level": soal.level,
    }


@pytest.mark.parametrize("kasus", KASUS, ids=lambda k: k.nama)
def test_reader_snapshot_ditolak_meski_hash_field_berbahaya_valid(kasus):
    baris = _baris_ditempa(kasus, "ｋｕｎｃｉ")
    with pytest.raises(ValueError, match="descriptor|field"):
        penyajian_dari_baris(baris)


@pytest.mark.parametrize("sisipan", (
    '<script/>', '<foreignObject/>', '<image href="https://contoh.invalid/a"/>',
    '<g onload="uji"/>', '<g xmlns="http://www.w3.org/1999/xhtml"/>',
    '<g xmlns:x="urn:asing" x:href="//contoh.invalid/a"/>',
    '<rect fill="url(//contoh.invalid/a)"/>', '<rect fill="url(#hilang)"/>',
    '<g style="background:url(//contoh.invalid/a)"/>',
    '<g оnload="uji"/>', '<animate attributeName="href"/>',
    '<div xmlns="" class="asing"/>',
))
def test_oracle_xml_sendiri_menolak_node_atribut_dan_fetch_asing(sisipan):
    # Sampel negatif lokal menguji oracle; tidak memutasi modul produksi.
    hasil = '<svg xmlns="http://www.w3.org/2000/svg">' + sisipan + '</svg>'
    with pytest.raises(AssertionError):
        periksa_xml(hasil)
