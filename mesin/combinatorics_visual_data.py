"""Validasi fakta Venn dan susunan, tanpa field langkah atau solusi."""
from collections.abc import Mapping
import re
from measurement_combinatorics_visual_data import bulat, field_tepat

ATURAN = frozenset({"digit", "genap", "lebih_dari", "permutasi", "blok", "kombinasi"})


def validasi_venn(data):
    field_tepat(data, {"a", "b", "c"})
    a, b, c = (bulat(data[nama], nama, 1, 1000) for nama in ("a", "b", "c"))
    if c > min(a, b):
        raise ValueError("irisan melebihi total himpunan")


def validasi_susunan(data):
    if not isinstance(data, Mapping):
        raise ValueError("data susunan wajib mapping")
    aturan = data.get("aturan")
    if not isinstance(aturan, str) or aturan not in ATURAN:
        raise ValueError("aturan susunan tidak didukung")
    tambahan = {"batas"} if aturan == "lebih_dari" else {"berdampingan"} if aturan == "blok" else set()
    field_tepat(data, {"aturan", "objek", "ambil"} | tambahan)
    objek = data["objek"]
    pola = r"[0-9]" if aturan in {"digit", "genap", "lebih_dari"} else r"[A-V]"
    if (not isinstance(objek, (list, tuple)) or not 2 <= len(objek) <= 12
            or any(not isinstance(s, str) or not re.fullmatch(pola, s) for s in objek)
            or len(set(objek)) != len(objek)):
        raise ValueError("objek wajib unik dan berupa digit atau kode huruf yang didukung")
    ambil = bulat(data["ambil"], "jumlah dipilih", 1, len(objek))
    if aturan in {"digit", "genap", "lebih_dari", "blok"} and ambil != len(objek):
        raise ValueError("seluruh objek wajib dipakai pada aturan ini")
    if aturan == "lebih_dari":
        bulat(data["batas"], "batas bilangan", 0, 10**len(objek)-1)
    if aturan == "blok":
        dekat = data["berdampingan"]
        if (not isinstance(dekat, (list, tuple)) or not 2 <= len(dekat) < len(objek)
                or any(not isinstance(s, str) or s not in objek for s in dekat)
                or len(set(dekat)) != len(dekat)):
            raise ValueError("objek berdampingan tidak sah")
