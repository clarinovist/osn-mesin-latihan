"""Validator ketat descriptor visual geometri datar versi 1."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

_SATUAN = frozenset({"cm", "m"})
_RASIO_SUDUT = frozenset(
    {
        (1, 2, 3), (1, 2, 6), (1, 3, 5), (2, 3, 4), (1, 2, 7),
        (1, 3, 6), (1, 4, 5), (2, 3, 5), (1, 2, 9), (1, 3, 8),
        (1, 4, 7), (1, 5, 6), (2, 3, 7), (2, 4, 6), (3, 4, 5),
    }
)


def _field_tepat(data: Mapping[str, Any], field: set[str], model: str) -> None:
    kunci = set(data)
    if any(not isinstance(nama, str) for nama in kunci):
        raise ValueError(f"field {model} wajib memakai kunci teks")
    if kunci != field | {"model"}:
        hilang = sorted((field | {"model"}) - kunci)
        tambahan = sorted(kunci - (field | {"model"}))
        raise ValueError(
            f"field {model} tidak tepat; hilang={hilang}, tambahan={tambahan}"
        )


def _bulat(nilai: Any, nama: str, minimum: int, maksimum: int) -> int:
    if type(nilai) is not int or not minimum <= nilai <= maksimum:
        raise ValueError(f"{nama} wajib bilangan bulat {minimum}..{maksimum}")
    return nilai


def _satuan(nilai: Any) -> None:
    if not isinstance(nilai, str) or nilai not in _SATUAN:
        raise ValueError("satuan wajib cm atau m")


def _sudut_pasangan(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"total", "diketahui"}, "sudut_pasangan")
    total = data["total"]
    if type(total) is not int or total not in {90, 180}:
        raise ValueError("total sudut pasangan wajib 90 atau 180")
    _bulat(data["diketahui"], "diketahui", 1, total - 1)


def _sudut_rasio(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"kali"}, "sudut_rasio")
    if type(data["kali"]) is not int or data["kali"] not in {3, 4, 5, 8, 9, 11}:
        raise ValueError("kali sudut rasio tidak didukung")


def _segitiga_sudut(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"a", "b"}, "segitiga_sudut")
    a = _bulat(data["a"], "a", 1, 179)
    b = _bulat(data["b"], "b", 1, 179)
    if a + b >= 180:
        raise ValueError("dua sudut segitiga wajib berjumlah kurang dari 180")


def _segitiga_rasio(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"p", "q", "r"}, "segitiga_rasio")
    rasio = tuple(_bulat(data[nama], nama, 1, 9) for nama in ("p", "q", "r"))
    if rasio not in _RASIO_SUDUT:
        raise ValueError("rasio sudut segitiga tidak didukung")


def _segitiga_luar(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"a", "b"}, "segitiga_luar")
    a = _bulat(data["a"], "a", 1, 179)
    b = _bulat(data["b"], "b", 1, 179)
    if a + b >= 180:
        raise ValueError("dua sudut dalam wajib membentuk segitiga")


def _persegi_panjang(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"p", "l"}, "persegi_panjang")
    _bulat(data["p"], "p", 2, 40)
    _bulat(data["l"], "l", 2, 40)


def _persegi_panjang_balik(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"p", "K"}, "persegi_panjang_balik")
    p = _bulat(data["p"], "p", 3, 30)
    keliling = _bulat(data["K"], "K", 10, 110)
    if keliling % 2 or not 2 <= keliling // 2 - p <= 25:
        raise ValueError("keliling tidak menghasilkan lebar persegi panjang yang sah")


def _alas_tinggi_sisi(data: Mapping[str, Any], model: str) -> None:
    _field_tepat(data, {"a", "t", "s"}, model)
    alas = _bulat(data["a"], "a", 4, 40)
    tinggi = _bulat(data["t"], "t", 3, 20)
    sisi = _bulat(data["s"], "s", 4, 39)
    if alas % 2 or sisi <= tinggi:
        raise ValueError("alas, tinggi, dan sisi miring tidak sah")


def _segitiga_tinggi(data: Mapping[str, Any]) -> None:
    _alas_tinggi_sisi(data, "segitiga_tinggi")


def _jajargenjang(data: Mapping[str, Any]) -> None:
    _alas_tinggi_sisi(data, "jajargenjang")


def _trapesium(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"a", "b", "t"}, "trapesium")
    a = _bulat(data["a"], "a", 4, 30)
    b = _bulat(data["b"], "b", 4, 30)
    _bulat(data["t"], "t", 3, 15)
    if a == b or (a + b) % 2:
        raise ValueError("sisi sejajar trapesium wajib berbeda dan berjumlah genap")


def _ketupat(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"d1", "d2"}, "ketupat")
    d1 = _bulat(data["d1"], "d1", 4, 40)
    d2 = _bulat(data["d2"], "d2", 4, 40)
    if d1 % 2 or d2 % 2 or d1 == d2:
        raise ValueError("diagonal ketupat wajib genap dan berbeda")


def _ketupat_balik(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"L", "d1"}, "ketupat_balik")
    luas = _bulat(data["L"], "L", 8, 800)
    d1 = _bulat(data["d1"], "d1", 4, 40)
    if d1 % 2 or (2 * luas) % d1:
        raise ValueError("luas tidak menghasilkan diagonal integral")
    d2 = 2 * luas // d1
    if not 4 <= d2 <= 40 or d2 % 2 or d1 == d2:
        raise ValueError("diagonal hasil balik tidak sah")


def _lingkaran(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"r"}, "lingkaran")
    _bulat(data["r"], "r", 5, 130)


def _juring(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"s", "r"}, "juring")
    if type(data["s"]) is not int or data["s"] not in {30, 45, 60, 90, 120, 180, 270}:
        raise ValueError("sudut pusat juring tidak didukung")
    _bulat(data["r"], "r", 5, 40)


def _arsiran_pojok(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"r"}, "arsiran_pojok")
    if type(data["r"]) is not int or data["r"] not in {7, 14, 21, 28, 35}:
        raise ValueError("jari-jari arsiran pojok wajib kelipatan 7 yang didukung")


def _jalan(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"luar", "dalam"}, "jalan")
    luar = _bulat(data["luar"], "luar", 12, 120)
    dalam = _bulat(data["dalam"], "dalam", 10, 100)
    if luar <= dalam or luar - dalam not in range(2, 21, 2):
        raise ValueError("sisi luar dan dalam jalan tidak sah")


def _kisi(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"p", "l", "satuan"}, "kisi")
    _bulat(data["p"], "p", 2, 8)
    _bulat(data["l"], "l", 2, 8)
    _satuan(data["satuan"])


def _simetri(data: Mapping[str, Any], model: str) -> None:
    _field_tepat(data, {"ukuran", "satuan"}, model)
    _bulat(data["ukuran"], "ukuran", 3, 16)
    _satuan(data["satuan"])


def _simetri_persegi(data: Mapping[str, Any]) -> None:
    _simetri(data, "simetri_persegi")


def _simetri_segitiga(data: Mapping[str, Any]) -> None:
    _simetri(data, "simetri_segitiga")


def _simetri_ketupat(data: Mapping[str, Any]) -> None:
    _simetri(data, "simetri_ketupat")


def _simetri_persegi_panjang(data: Mapping[str, Any]) -> None:
    _field_tepat(data, {"ukuran", "lebar", "satuan"}, "simetri_persegi_panjang")
    ukuran = _bulat(data["ukuran"], "ukuran", 3, 16)
    lebar = _bulat(data["lebar"], "lebar", 2, 15)
    if lebar >= ukuran:
        raise ValueError("lebar persegi panjang wajib lebih kecil dari panjang")
    _satuan(data["satuan"])


VALIDATOR_GEOMETRI: dict[str, Callable[[Mapping[str, Any]], None]] = {
    "sudut_pasangan": _sudut_pasangan,
    "sudut_rasio": _sudut_rasio,
    "segitiga_sudut": _segitiga_sudut,
    "segitiga_rasio": _segitiga_rasio,
    "segitiga_luar": _segitiga_luar,
    "persegi_panjang": _persegi_panjang,
    "persegi_panjang_balik": _persegi_panjang_balik,
    "segitiga_tinggi": _segitiga_tinggi,
    "jajargenjang": _jajargenjang,
    "trapesium": _trapesium,
    "ketupat": _ketupat,
    "ketupat_balik": _ketupat_balik,
    "lingkaran": _lingkaran,
    "juring": _juring,
    "arsiran_pojok": _arsiran_pojok,
    "jalan": _jalan,
    "kisi": _kisi,
    "simetri_persegi": _simetri_persegi,
    "simetri_segitiga": _simetri_segitiga,
    "simetri_ketupat": _simetri_ketupat,
    "simetri_persegi_panjang": _simetri_persegi_panjang,
}


def validasi_data(data: Mapping[str, Any]) -> None:
    """Validasi allow-list satu descriptor geometri tanpa impor kontrak visual."""
    if not isinstance(data, Mapping):
        raise ValueError("data descriptor wajib berupa mapping")
    if any(not isinstance(kunci, str) for kunci in data):
        raise ValueError("field descriptor wajib memakai kunci teks")
    model = data.get("model")
    if not isinstance(model, str):
        raise ValueError("model geometri wajib berupa teks")
    validator = VALIDATOR_GEOMETRI.get(model)
    if validator is None:
        raise ValueError(f"model geometri tidak didukung: {model!r}")
    validator(data)
