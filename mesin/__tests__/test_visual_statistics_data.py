"""Kontrak data dan proyeksi visual untuk keluarga statistika."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from statistics_visual_data import validasi_data  # noqa: E402
from topic_statistics_visual import proyeksi_statistika  # noqa: E402
from visual_contract import DescriptorVisual  # noqa: E402


@pytest.mark.parametrize(
    "jenis,data",
    [
        (
            "batang",
            {"nama": ["B1", "B2", "B3"], "data": [4, 9, 7], "varian": "baca", "i": 1},
        ),
        (
            "turus",
            {"nama": ["Apel", "Jeruk", "Mangga"], "data": [4, 9, 7], "varian": "terbanyak", "i": 0},
        ),
        (
            "piktogram",
            {"nama": ["Apel", "Jeruk", "Mangga"], "gambar": [2, 3, 4], "satuan": 5, "varian": "total", "i": 0},
        ),
        ("lingkaran", {"varian": "cari_nilai", "total": 120, "sudut": 90}),
        ("lingkaran", {"varian": "cari_sudut", "total": 120, "nilai": 30}),
    ],
)
def test_validator_menerima_descriptor_statistika_yang_sah(jenis, data):
    assert validasi_data(jenis, data) is None
    assert DescriptorVisual(jenis, 1, data).jenis == jenis


@pytest.mark.parametrize(
    "jenis,data",
    [
        ("batang", {"nama": ["B1", "B2", "B3"], "data": [1, 2, 3], "varian": "baca", "i": 0, "asing": 1}),
        ("turus", {"nama": ["A", "B", "C"], "data": [1, 2, 3], "varian": "baca"}),
        ("piktogram", {"nama": ["A", "B", "C"], "gambar": [1, 2, 3], "satuan": 2, "varian": "baca", "i": 0, "data": [2, 4, 6]}),
        ("lingkaran", {"varian": "cari_nilai", "total": 100, "sudut": 90, "nilai": 25}),
    ],
)
def test_validator_menolak_field_hilang_atau_tambahan(jenis, data):
    with pytest.raises(ValueError, match="field"):
        validasi_data(jenis, data)


@pytest.mark.parametrize(
    "jenis,data",
    [
        ("batang", {"nama": ["B1", "B2", "B3"], "data": [True, 2, 3], "varian": "baca", "i": 0}),
        ("batang", {"nama": ["B1", "B2", "B3"], "data": [1, 2, 71], "varian": "baca", "i": 0}),
        ("turus", {"nama": ["A", "B", "C"], "data": [1, 2, 26], "varian": "jumlah", "i": 0}),
        ("piktogram", {"nama": ["A", "B", "C"], "gambar": [1, 2, 13], "satuan": 2, "varian": "total", "i": 0}),
        ("piktogram", {"nama": ["A", "B", "C"], "gambar": [1, 2, 3], "satuan": True, "varian": "total", "i": 0}),
        ("lingkaran", {"varian": "cari_nilai", "total": True, "sudut": 90}),
    ],
)
def test_validator_menolak_bool_dan_angka_di_luar_batas(jenis, data):
    with pytest.raises(ValueError):
        validasi_data(jenis, data)


@pytest.mark.parametrize(
    "jenis,data",
    [
        ("batang", {"nama": ["B1", "B3", "B2"], "data": [1, 2, 3], "varian": "baca", "i": 0}),
        ("batang", {"nama": ["B1", "B2"], "data": [1, 2], "varian": "jumlah", "i": 0}),
        ("turus", {"nama": ["A", "A", "C"], "data": [1, 2, 3], "varian": "jumlah", "i": 0}),
        ("turus", {"nama": ["A", "B", "C"], "data": [7, 7, 2], "varian": "terbanyak", "i": 0}),
        ("piktogram", {"nama": ["A", "B", "C"], "gambar": [1, 2, 3], "satuan": 3, "varian": "total", "i": 0}),
        ("piktogram", {"nama": ["A", "B", "C"], "gambar": [1, 2, 3], "satuan": 2, "varian": "selisih", "i": 3}),
    ],
)
def test_validator_menolak_invarian_kategori_varian_dan_indeks(jenis, data):
    with pytest.raises(ValueError):
        validasi_data(jenis, data)


@pytest.mark.parametrize(
    "nama",
    [
        ["A", "A", "C"],
        ["A", "<b>B</b>", "C"],
        ["A", "B\nX", "C"],
        ["A", "x" * 25, "C"],
    ],
)
def test_validator_menolak_nama_duplikat_markup_kontrol_dan_terlalu_panjang(nama):
    with pytest.raises(ValueError, match="nama"):
        validasi_data(
            "turus",
            {"nama": nama, "data": [1, 2, 3], "varian": "jumlah", "i": 0},
        )


@pytest.mark.parametrize(
    "data",
    [
        {"varian": "cari_nilai", "total": 0, "sudut": 90},
        {"varian": "cari_nilai", "total": 6001, "sudut": 90},
        {"varian": "cari_nilai", "total": 100, "sudut": 0},
        {"varian": "cari_nilai", "total": 100, "sudut": 360},
        {"varian": "cari_nilai", "total": 101, "sudut": 90},
        {"varian": "cari_sudut", "total": 100, "nilai": 101},
        {"varian": "cari_sudut", "total": 100, "nilai": 13},
    ],
)
def test_validator_lingkaran_menolak_rasio_nonintegral_dan_batas(data):
    with pytest.raises(ValueError):
        validasi_data("lingkaran", data)


@pytest.mark.parametrize(
    "template_id,parameter,jenis,varian",
    [
        ("diagram_batang_garis", {"varian": "baca", "data": [4, 9, 7], "i": 1}, "batang", "baca"),
        ("diagram_batang_garis", {"varian": "jumlah", "data": [4, 9, 7]}, "batang", "jumlah"),
        ("diagram_batang_garis", {"varian": "selisih", "data": [4, 9, 7], "i": 1}, "batang", "selisih"),
        ("tabel_turus", {"varian": "baca", "nama": ["Apel", "Jeruk", "Mangga"], "data": [4, 9, 7], "i": 1}, "turus", "baca"),
        ("tabel_turus", {"varian": "terbanyak", "nama": ["Apel", "Jeruk", "Mangga"], "data": [4, 9, 7]}, "turus", "terbanyak"),
        ("tabel_turus", {"varian": "jumlah", "nama": ["Apel", "Jeruk", "Mangga"], "data": [4, 9, 7]}, "turus", "jumlah"),
        ("piktogram", {"varian": "baca", "satuan": 5, "gambar": [2, 3, 4], "nama": ["Apel", "Jeruk", "Mangga"], "i": 1}, "piktogram", "baca"),
        ("piktogram", {"varian": "total", "satuan": 5, "gambar": [2, 3, 4], "nama": ["Apel", "Jeruk", "Mangga"]}, "piktogram", "total"),
        ("piktogram", {"varian": "selisih", "satuan": 5, "gambar": [2, 3, 4], "nama": ["Apel", "Jeruk", "Mangga"], "i": 1}, "piktogram", "selisih"),
        ("diagram_lingkaran", {"varian": "cari_nilai", "s": 90, "total": 120}, "lingkaran", "cari_nilai"),
        ("diagram_lingkaran", {"varian": "cari_sudut", "s": 90, "total": 120, "nilai": 30}, "lingkaran", "cari_sudut"),
    ],
)
def test_proyektor_membuat_teks_dan_descriptor_valid(template_id, parameter, jenis, varian):
    hasil = proyeksi_statistika(template_id, parameter)

    assert hasil is not None
    teks, descriptor = hasil
    assert teks
    assert descriptor.jenis == jenis
    assert descriptor.versi == 1
    assert descriptor.data["varian"] == varian
    assert "Apel: 2 gambar" not in teks
    assert "Apel = 4 turus" not in teks
    assert "B1: 4" not in teks


def test_proyektor_menghasilkan_nama_batang_dan_tidak_menyimpan_s_computed():
    _, batang = proyeksi_statistika(
        "diagram_batang_garis", {"varian": "jumlah", "data": [4, 9, 7]}
    )
    _, lingkaran = proyeksi_statistika(
        "diagram_lingkaran",
        {"varian": "cari_sudut", "s": 90, "total": 120, "nilai": 30},
    )

    assert batang.data["nama"] == ("B1", "B2", "B3")
    assert batang.data["i"] == 0
    assert set(lingkaran.data) == {"varian", "total", "nilai"}


def test_proyektor_mengembalikan_none_untuk_template_tidak_terkait():
    assert proyeksi_statistika("median_modus", {"varian": "median", "data": [1, 2, 3]}) is None


@pytest.mark.parametrize(
    "template_id,parameter",
    [
        ("diagram_batang_garis", {"varian": "baca", "data": [4, 9, 7]}),
        ("diagram_batang_garis", {"varian": "jumlah", "data": [4, 9, 7], "i": 0}),
        ("tabel_turus", {"varian": "jumlah", "nama": ["A", "B", "C"], "data": [1, 2, 3], "asing": 1}),
        ("piktogram", {"varian": "baca", "satuan": 5, "gambar": [2, 3, 4], "nama": ["A", "B", "C"], "i": True}),
        ("diagram_lingkaran", {"varian": "cari_nilai", "s": 90, "total": 120, "nilai": 30}),
        ("diagram_lingkaran", {"varian": "cari_sudut", "s": 91, "total": 120, "nilai": 30}),
    ],
)
def test_proyektor_menolak_parameter_terkait_yang_tidak_tepat(template_id, parameter):
    with pytest.raises(ValueError):
        proyeksi_statistika(template_id, parameter)
