"""Validasi data pola baca gambar; tanpa target jawaban dalam descriptor."""
from collections.abc import Mapping


def bulat(nilai, nama, minimum, maksimum):
    """Tolak boolean, pecahan, dan angka di luar batas geometri."""
    if type(nilai) is not int or not minimum <= nilai <= maksimum:
        raise ValueError(f"{nama} wajib bilangan bulat {minimum}..{maksimum}")


def bidang(data, nama):
    """Field harus tepat; tidak menyalin parameter lain ke visual."""
    if not isinstance(data, Mapping) or set(data) != set(nama):
        raise ValueError("field data pola tidak sesuai kontrak")


def validasi_korek(data):
    bidang(data, ("n_tampil", "awal", "tambah"))
    bulat(data["n_tampil"], "n_tampil", 3, 3)
    bulat(data["awal"], "awal", 3, 7)
    bulat(data["tambah"], "tambah", 2, 4)


def validasi_titik(data):
    bidang(data, ("n_tampil",))
    bulat(data["n_tampil"], "n_tampil", 4, 4)
