"""Fase 1 Slice 1: kontrak penyajian pertanyaan yang murni dan aman."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from types import MappingProxyType

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from visual_contract import (  # noqa: E402
    DescriptorVisual,
    PenyajianPertanyaan,
    buat_penyajian,
    deserialisasi_penyajian,
    fingerprint_matematis,
    serialisasi_kanonis,
    serialisasi_penyajian,
)
from visual_renderer import render_teks  # noqa: E402


def _penyajian(**ubah):
    argumen = {
        "template_id": "diagram_batang_garis",
        "level": "P4",
        "parameter": {"nilai": [3, 7, 5], "varian": "baca"},
        "teks_soal": "Perhatikan data berikut. Berapa nilai B?",
        "bagian_soal": "B",
        "tantangan_soal": False,
        "minta_restatement": True,
        "asal_teks": "bawaan",
        "status_visual": "tanpa_visual",
        "mode_representasi": "teks-v1",
        "descriptor": None,
    }
    argumen.update(ubah)
    return buat_penyajian(**argumen)


def test_descriptor_dan_penyajian_beku():
    descriptor = DescriptorVisual(
        jenis="placeholder",
        versi=1,
        data={"label": "Visual belum tersedia"},
    )
    penyajian = _penyajian(
        status_visual="siap",
        mode_representasi="placeholder-v1",
        descriptor=descriptor,
    )

    assert dataclasses.is_dataclass(penyajian)
    assert penyajian.descriptor is descriptor
    assert isinstance(descriptor.data, MappingProxyType)
    assert descriptor.data["label"] == "Visual belum tersedia"
    with pytest.raises(dataclasses.FrozenInstanceError):
        penyajian.teks_soal = "berubah"
    with pytest.raises(TypeError):
        descriptor.data["label"] = "berubah"


def test_serialisasi_kanonis_stabil_dan_tidak_mengikuti_urutan_mapping():
    kiri = {"z": [2, 1], "a": {"é": True, "n": None}}
    kanan = {"a": {"n": None, "é": True}, "z": (2, 1)}

    assert serialisasi_kanonis(kiri) == serialisasi_kanonis(kanan)
    assert serialisasi_kanonis(kiri) == '{"a":{"n":null,"é":true},"z":[2,1]}'


@pytest.mark.parametrize(
    "parameter_ubah",
    [
        {"nilai": [3, 7, 6], "varian": "baca"},
        {"nilai": [3, 7, 5], "varian": "jumlah"},
    ],
)
def test_fingerprint_matematis_sha256_mencakup_versi_template_level_parameter(
    parameter_ubah,
):
    dasar = fingerprint_matematis(
        1,
        "diagram_batang_garis",
        "P4",
        {"varian": "baca", "nilai": [3, 7, 5]},
    )
    sama_beda_urutan = fingerprint_matematis(
        1,
        "diagram_batang_garis",
        "P4",
        {"nilai": [3, 7, 5], "varian": "baca"},
    )
    berubah = fingerprint_matematis(
        1, "diagram_batang_garis", "P4", parameter_ubah
    )

    assert dasar == sama_beda_urutan
    assert len(dasar) == 64
    int(dasar, 16)
    assert berubah != dasar
    assert fingerprint_matematis(
        2, "diagram_batang_garis", "P4", parameter_ubah
    ) != berubah
    assert fingerprint_matematis(
        1, "piktogram", "P4", parameter_ubah
    ) != berubah
    assert fingerprint_matematis(
        1, "diagram_batang_garis", "P5", parameter_ubah
    ) != berubah


def test_fingerprint_penyajian_meliputi_snapshot_lengkap_kecuali_dirinya():
    dasar = _penyajian()
    teks_baru = _penyajian(teks_soal="Kalimat aman yang berbeda.")
    asal_baru = _penyajian(asal_teks="cerita")

    assert dasar.fingerprint_penyajian != teks_baru.fingerprint_penyajian
    assert dasar.fingerprint_penyajian != asal_baru.fingerprint_penyajian
    muatan = json.loads(serialisasi_penyajian(dasar))
    fingerprint = muatan.pop("fingerprint_penyajian")
    assert fingerprint == hashlib.sha256(
        serialisasi_kanonis(muatan).encode("utf-8")
    ).hexdigest()


def test_round_trip_json_kanonis_dan_parser_menolak_bentuk_nonkanonis():
    awal = _penyajian()
    teks = serialisasi_penyajian(awal)

    assert serialisasi_penyajian(deserialisasi_penyajian(teks)) == teks
    with pytest.raises(ValueError, match="kanonis"):
        deserialisasi_penyajian(json.dumps(json.loads(teks), indent=2))


def test_pembuat_menolak_level_tidak_dikenal():
    with pytest.raises(ValueError, match="level"):
        _penyajian(level="P7")


@pytest.mark.parametrize(
    "ubah, pesan",
    [
        ({"penyajian_versi": 99}, "versi penyajian"),
        ({"renderer_versi": 99}, "versi renderer"),
        ({"asal_teks": "ai"}, "asal teks"),
        ({"status_visual": "aktif"}, "status visual"),
        ({"mode_representasi": ""}, "mode representasi"),
    ],
)
def test_parser_fail_closed_untuk_versi_dan_domain_tidak_dikenal(ubah, pesan):
    muatan = json.loads(serialisasi_penyajian(_penyajian()))
    muatan.update(ubah)
    muatan.pop("fingerprint_penyajian")
    muatan["fingerprint_penyajian"] = hashlib.sha256(
        serialisasi_kanonis(muatan).encode("utf-8")
    ).hexdigest()

    with pytest.raises(ValueError, match=pesan):
        deserialisasi_penyajian(serialisasi_kanonis(muatan))


def test_parser_fail_closed_untuk_field_hilang_tambahan_dan_fingerprint_palsu():
    muatan = json.loads(serialisasi_penyajian(_penyajian()))
    tanpa_teks = dict(muatan)
    tanpa_teks.pop("teks_soal")
    tambahan = dict(muatan, kunci="rahasia")
    fingerprint_palsu = dict(muatan, fingerprint_penyajian="0" * 64)

    for rusak in (tanpa_teks, tambahan, fingerprint_palsu):
        with pytest.raises(ValueError):
            deserialisasi_penyajian(serialisasi_kanonis(rusak))


def test_status_visual_dan_descriptor_harus_konsisten():
    with pytest.raises(ValueError, match="descriptor"):
        _penyajian(status_visual="siap", descriptor=None)
    with pytest.raises(ValueError, match="descriptor"):
        _penyajian(
            status_visual="tanpa_visual",
            descriptor=DescriptorVisual("placeholder", 1, {"label": "aman"}),
        )


@pytest.mark.parametrize(
    "data",
    [
        {"kunci": "42"},
        {"key": "42"},
        {"malrule": []},
        {"diagnosis": "K"},
        {"reason": "internal"},
        {"alasan": "internal"},
        {"pembahasan": "cara menjawab"},
        {"markup": "<svg><path /></svg>"},
        {"markup": "<strong>rahasia</strong>"},
    ],
)
def test_descriptor_menolak_rahasia_dan_markup_raw(data):
    with pytest.raises(ValueError):
        DescriptorVisual("placeholder", 1, data)


def test_snapshot_tidak_mengekspos_parameter_rahasia_atau_markup_renderer():
    teks = serialisasi_penyajian(_penyajian(parameter={"angka": 17}))
    muatan = json.loads(teks)

    assert "parameter" not in muatan
    assert set(muatan).isdisjoint(
        {"kunci", "key", "malrule", "diagnosis", "reason", "alasan", "pembahasan", "html", "svg"}
    )
    assert "<svg" not in teks.lower()
    assert "<html" not in teks.lower()


def test_renderer_fase_satu_hanya_mengembalikan_teks_identik_tanpa_svg():
    penyajian = _penyajian()

    assert render_teks(penyajian) == penyajian.teks_soal
    assert "<svg" not in render_teks(penyajian).lower()


def _konstruktor_langsung(**ubah):
    dasar = _penyajian()
    argumen = {
        field.name: getattr(dasar, field.name)
        for field in dataclasses.fields(PenyajianPertanyaan)
    }
    argumen.update(ubah)
    return PenyajianPertanyaan(**argumen)


@pytest.mark.parametrize(
    "ubah",
    [
        {"teks_soal": ""},
        {"tantangan_soal": 1},
        {"descriptor": {"jenis": "placeholder", "versi": 1, "data": {}}},
        {"fingerprint_matematis": "bukan-sha256"},
        {"fingerprint_penyajian": "0" * 64},
    ],
)
def test_konstruktor_langsung_menolak_snapshot_tidak_valid_atau_tidak_konsisten(ubah):
    with pytest.raises(ValueError):
        _konstruktor_langsung(**ubah)


@pytest.mark.parametrize("field", ["penyajian_versi", "renderer_versi"])
def test_versi_boolean_ditolak_oleh_pembuat_dan_konstruktor_langsung(field):
    with pytest.raises(ValueError, match="versi"):
        _penyajian(**{field: True})
    with pytest.raises(ValueError, match="versi"):
        _konstruktor_langsung(**{field: True})


@pytest.mark.parametrize(
    "data",
    [
        {"kunci_jawaban": "42"},
        {"correctAnswer": "42"},
        {"diagnosis_internal": "K"},
        {"prefix_kunci": "42"},
        {"ｋｕｎｃｉ": "42"},
        {"label": "<img src=x>"},
        {"label": "<foreignObject>rahasia</foreignObject>"},
        {"label": "onload=alert(1)"},
        {"label": "<g onmouseover='x'>aman</g>"},
        {1: "satu"},
    ],
)
def test_descriptor_menolak_batas_schema_adversarial(data):
    with pytest.raises(ValueError):
        DescriptorVisual("placeholder", 1, data)


@pytest.mark.parametrize(
    "jenis, data",
    [
        ("korek", {"n_tampil": 0, "awal": 4, "tambah": 3}),
        ("korek", {"n_tampil": 8, "awal": 4, "tambah": 3}),
        ("korek", {"n_tampil": True, "awal": 4, "tambah": 3}),
        ("korek", {"n_tampil": 3, "awal": 2, "tambah": 3}),
        ("korek", {"n_tampil": 3, "awal": 8, "tambah": 3}),
        ("korek", {"n_tampil": 3, "awal": 4, "tambah": 1}),
        ("korek", {"n_tampil": 3, "awal": 4, "tambah": 5}),
        ("korek", {"n_tampil": 3, "awal": 4, "tambah": 3, "target": 10}),
        ("korek", {"n_tampil": 3, "awal": 4, "tambah": 3, "answer": 10}),
        ("titik", {"n_tampil": 0}),
        ("titik", {"n_tampil": 8}),
        ("titik", {"n_tampil": 4, "target": 8}),
        ("titik", {"n_tampil": 4, "jawaban": 10}),
    ],
)
def test_descriptor_visual_aktif_menolak_field_dan_batas_di_luar_allowlist(
    jenis, data
):
    with pytest.raises(ValueError):
        DescriptorVisual(jenis, 1, data)


@pytest.mark.parametrize(
    "jenis, data",
    [
        ("korek", {"n_tampil": 1, "awal": 3, "tambah": 2}),
        ("korek", {"n_tampil": 7, "awal": 7, "tambah": 4}),
        ("titik", {"n_tampil": 1}),
        ("titik", {"n_tampil": 7}),
    ],
)
def test_descriptor_visual_aktif_menerima_batas_allowlist(jenis, data):
    descriptor = DescriptorVisual(jenis, 1, data)

    assert dict(descriptor.data) == data


def test_descriptor_menolak_kunci_yang_bertabrakan_setelah_normalisasi():
    with pytest.raises(ValueError, match="duplikat"):
        DescriptorVisual("placeholder", 1, {"label-id": "A", "label_id": "B"})


@pytest.mark.parametrize(
    "jenis, versi, data",
    [
        ("bebas", 1, {"label": "aman"}),
        ("placeholder", 2, {"label": "aman"}),
        ("placeholder", 1, {}),
        ("placeholder", 1, {"label": "aman", "warna": "merah"}),
        ("placeholder", 1, {"label": 42}),
        ("placeholder", 1, {"label": ""}),
        ("placeholder", 1, {"label": "   "}),
        ("placeholder", 1, {"label": "x" * 201}),
    ],
)
def test_descriptor_fail_closed_untuk_jenis_versi_dan_schema(jenis, versi, data):
    with pytest.raises(ValueError):
        DescriptorVisual(jenis, versi, data)


@pytest.mark.parametrize(
    "label",
    [
        "<!-- komentar -->",
        "<!DOCTYPE html>",
        "<![CDATA[rahasia]]>",
        "<?xml version='1.0'?>",
    ],
)
def test_descriptor_menolak_komentar_dan_deklarasi_markup(label):
    with pytest.raises(ValueError, match="markup"):
        DescriptorVisual("placeholder", 1, {"label": label})


def test_descriptor_mengizinkan_tanda_kurang_dari_sebagai_teks_matematika():
    descriptor = DescriptorVisual("placeholder", 1, {"label": "3 < 5"})

    assert descriptor.data["label"] == "3 < 5"


class _MappingKunciDuplikat(Mapping):
    def __getitem__(self, key):
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def items(self):  # type: ignore[override]
        return [("label", "A"), ("label", "B")]


def test_serialisasi_kanonis_menolak_mapping_dengan_kunci_nonstring_dan_duplikat():
    with pytest.raises(ValueError):
        serialisasi_kanonis({1: "satu"})
    with pytest.raises(ValueError):
        serialisasi_kanonis(_MappingKunciDuplikat())


def test_serialisasi_penyajian_memvalidasi_ulang_semua_field():
    penyajian = _penyajian()
    object.__setattr__(penyajian, "renderer_versi", True)

    with pytest.raises(ValueError, match="versi renderer"):
        serialisasi_penyajian(penyajian)


def test_serialisasi_penyajian_memvalidasi_ulang_descriptor_yang_dirusak():
    descriptor = DescriptorVisual("placeholder", 1, {"label": "aman"})
    penyajian = _penyajian(
        status_visual="siap",
        mode_representasi="placeholder-v1",
        descriptor=descriptor,
    )
    object.__setattr__(descriptor, "data", {"label": "<img src=x>"})

    with pytest.raises(ValueError, match="markup"):
        serialisasi_penyajian(penyajian)


def test_fingerprint_deterministik_lintas_pythonhashseed_dan_proses():
    kode = """
from visual_contract import fingerprint_matematis
print(fingerprint_matematis(1, 'diagram_batang_garis', 'P4', {'z': [3, 1], 'a': 'é'}))
"""
    hasil = []
    akar = str(Path(__file__).resolve().parent.parent)
    for seed in ("1", "77"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=akar)
        hasil.append(
            subprocess.check_output([sys.executable, "-c", kode], env=env, text=True).strip()
        )

    assert hasil[0] == hasil[1]
