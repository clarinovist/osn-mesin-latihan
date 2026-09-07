"""Validator ketat untuk descriptor visual statistika versi 1."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any

_MARKUP = re.compile(r"<[^>]*>")
_SATUAN_PIKTOGRAM = frozenset({2, 4, 5, 10, 20})


def _field_tepat(data: Mapping[str, Any], field: set[str], jenis: str) -> None:
    kunci = set(data)
    if any(not isinstance(nama, str) for nama in kunci):
        raise ValueError(f"field {jenis} wajib memakai kunci teks")
    if kunci != field:
        hilang = sorted(field - kunci)
        tambahan = sorted(kunci - field)
        raise ValueError(
            f"field {jenis} tidak tepat; hilang={hilang}, tambahan={tambahan}"
        )


def _bilangan_bulat(nilai: Any, nama: str, minimum: int, maksimum: int) -> int:
    if type(nilai) is not int or not minimum <= nilai <= maksimum:
        raise ValueError(f"{nama} wajib bilangan bulat {minimum}..{maksimum}")
    return nilai


def _daftar_bulat(
    nilai: Any, nama: str, minimum: int, maksimum: int
) -> tuple[int, ...]:
    if not isinstance(nilai, (list, tuple)):
        raise ValueError(f"{nama} wajib berupa daftar")
    return tuple(
        _bilangan_bulat(isi, f"{nama}[{indeks}]", minimum, maksimum)
        for indeks, isi in enumerate(nilai)
    )


def _nama(nilai: Any) -> tuple[str, ...]:
    if not isinstance(nilai, (list, tuple)):
        raise ValueError("nama wajib berupa daftar")
    for isi in nilai:
        if (
            not isinstance(isi, str)
            or not isi.strip()
            or len(isi) > 24
            or _MARKUP.search(isi)
            or any(unicodedata.category(karakter).startswith("C") for karakter in isi)
        ):
            raise ValueError("nama kategori tidak valid")
    if len({isi.strip() for isi in nilai}) != len(nilai):
        raise ValueError("nama kategori tidak boleh duplikat")
    return tuple(nilai)


def _kategori(
    data: Mapping[str, Any], *, maksimum: int, jenis: str
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    nama = _nama(data["nama"])
    nilai = _daftar_bulat(data["data"], "data", 1, maksimum)
    if not 3 <= len(nama) <= 6 or len(nama) != len(nilai):
        raise ValueError(f"{jenis} wajib memiliki 3..6 kategori sejajar")
    return nama, nilai


def _varian_dan_indeks(
    data: Mapping[str, Any], varian_sah: set[str], banyak: int
) -> tuple[str, int]:
    varian = data["varian"]
    if not isinstance(varian, str) or varian not in varian_sah:
        raise ValueError(f"varian tidak didukung: {varian!r}")
    indeks = _bilangan_bulat(data["i"], "i", 0, banyak - 1)
    return varian, indeks


def _validasi_batang(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"nama", "data", "varian", "i"}, "batang")
    nama, nilai = _kategori(data, maksimum=70, jenis="batang")
    if nama != tuple(f"B{i + 1}" for i in range(len(nama))):
        raise ValueError("nama batang wajib berurutan B1..Bn")
    _varian_dan_indeks(data, {"baca", "jumlah", "selisih"}, len(nilai))


def _validasi_turus(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"nama", "data", "varian", "i"}, "turus")
    _, nilai = _kategori(data, maksimum=25, jenis="turus")
    varian, _ = _varian_dan_indeks(
        data, {"baca", "terbanyak", "jumlah"}, len(nilai)
    )
    if varian == "terbanyak" and nilai.count(max(nilai)) != 1:
        raise ValueError("varian terbanyak wajib memiliki maksimum unik")


def _validasi_piktogram(data: Mapping[str, Any]) -> None:
    _field_tepat(
        data, {"nama", "gambar", "satuan", "varian", "i"}, "piktogram"
    )
    nama = _nama(data["nama"])
    gambar = _daftar_bulat(data["gambar"], "gambar", 1, 12)
    if not 3 <= len(nama) <= 6 or len(nama) != len(gambar):
        raise ValueError("piktogram wajib memiliki 3..6 kategori sejajar")
    satuan = data["satuan"]
    if type(satuan) is not int or satuan not in _SATUAN_PIKTOGRAM:
        raise ValueError("satuan piktogram tidak didukung")
    _varian_dan_indeks(data, {"baca", "total", "selisih"}, len(gambar))


def _validasi_lingkaran(data: Mapping[str, Any]) -> None:
    varian = data.get("varian")
    if varian == "cari_nilai":
        _field_tepat(data, {"varian", "total", "sudut"}, "lingkaran")
        total = _bilangan_bulat(data["total"], "total", 1, 6000)
        sudut = _bilangan_bulat(data["sudut"], "sudut", 1, 359)
        if total * sudut % 360:
            raise ValueError("nilai bagian lingkaran wajib integral")
        return
    if varian == "cari_sudut":
        _field_tepat(data, {"varian", "total", "nilai"}, "lingkaran")
        total = _bilangan_bulat(data["total"], "total", 1, 6000)
        nilai = _bilangan_bulat(data["nilai"], "nilai", 1, total - 1)
        if nilai * 360 % total:
            raise ValueError("sudut bagian lingkaran wajib integral")
        return
    raise ValueError(f"varian lingkaran tidak didukung: {varian!r}")


VALIDATOR_STATISTIKA = {
    "batang": _validasi_batang,
    "turus": _validasi_turus,
    "piktogram": _validasi_piktogram,
    "lingkaran": _validasi_lingkaran,
}


def validasi_data(jenis: str, data: Mapping[str, Any]) -> None:
    """Validasi allow-list descriptor statistika tanpa impor kontrak visual."""
    if not isinstance(data, Mapping):
        raise ValueError("data descriptor wajib berupa mapping")
    validator = VALIDATOR_STATISTIKA.get(jenis)
    if validator is None:
        raise ValueError(f"jenis statistika tidak didukung: {jenis!r}")
    validator(data)
