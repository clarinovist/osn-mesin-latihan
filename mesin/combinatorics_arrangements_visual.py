"""Proyeksi digit dan objek tersedia; tidak mengenumerasi pilihan yang sah."""
from collections.abc import Mapping
from measurement_combinatorics_visual_data import bulat, field_tepat
from combinatorics_visual_data import validasi_susunan
from visual_contract import DescriptorVisual

TEMPLATE_SUSUNAN = frozenset({"susun_bilangan", "susun_bilangan_syarat", "permutasi_urutan", "permutasi_blok", "kombinasi_pilih"})


def _digit(tid, p):
    varian = p.get("varian")
    sah = {"dengan_nol", "tanpa_nol"} if tid == "susun_bilangan" else {"genap", "lebih_dari"}
    if not isinstance(varian, str) or varian not in sah:
        raise ValueError("varian susunan digit tidak didukung")
    field_tepat(p, {"varian", "angka", "N"} if varian == "lebih_dari" else {"varian", "angka"})
    angka = p["angka"]
    if not isinstance(angka, (tuple, list)) or not 3 <= len(angka) <= 5:
        raise ValueError("digit wajib berupa daftar sepanjang 3 sampai 5")
    for nilai in angka:
        bulat(nilai, "digit", 0, 9)
    if tid == "susun_bilangan" and ((0 in angka) != (varian == "dengan_nol")):
        raise ValueError("varian nol tidak cocok dengan digit")
    aturan = "digit" if tid == "susun_bilangan" else varian
    data = {"aturan": aturan, "objek": tuple(str(a) for a in angka), "ambil": len(angka)}
    return {**data, "batas": p["N"]} if aturan == "lebih_dari" else data


def _objek(tid, p):
    field_tepat(p, {"n", "k", "objek"} if tid == "permutasi_blok" else {"n", "r", "objek"})
    n = bulat(p["n"], "jumlah objek", 4, 12)
    if not isinstance(p["objek"], (list, tuple)) or len(p["objek"]) != n:
        raise ValueError("jumlah objek tidak sama dengan n")
    aturan = {"permutasi_urutan": "permutasi", "permutasi_blok": "blok", "kombinasi_pilih": "kombinasi"}[tid]
    ambil = n if aturan == "blok" else bulat(p["r"], "jumlah dipilih", 1, n)
    data = {"aturan": aturan, "objek": tuple(p["objek"]), "ambil": ambil}
    if aturan == "blok":
        k = bulat(p["k"], "jumlah berdampingan", 2, n-1)
        return {**data, "berdampingan": tuple(p["objek"][:k])}
    return data


def proyeksi_susunan(tid, parameter):
    if not isinstance(parameter, Mapping):
        raise ValueError("parameter susunan wajib mapping")
    data = _digit(tid, parameter) if tid.startswith("susun_bilangan") else _objek(tid, parameter)
    validasi_susunan(data)
    aturan, ambil = data["aturan"], data["ambil"]
    if aturan in {"digit", "genap", "lebih_dari"}:
        syarat = (" dan genap" if aturan == "genap" else f" dan lebih besar dari {data['batas']}" if aturan == "lebih_dari" else "")
        teks = (f"Susun digit pada kartu menjadi bilangan {ambil} digit{syarat}. "
                "Setiap digit dipakai sekali; nol tidak boleh menjadi digit pertama.\n"
                "Berapa banyak bilangan yang dapat dibuat?")
    elif aturan == "blok":
        nama = " dan ".join(data["berdampingan"])
        teks = f"Susun semua buku pada kartu berjajar di rak. Buku {nama} harus berdampingan.\nBerapa banyak cara susunan yang mungkin?"
    elif aturan == "kombinasi":
        teks = f"Pilih {ambil} orang dari kartu untuk menjadi satu tim. Urutan tidak penting.\nBerapa banyak cara memilih tim?"
    else:
        teks = f"Pilih {ambil} orang dari kartu untuk posisi pertama, kedua, dan seterusnya secara berurutan.\nBerapa banyak cara susunan yang mungkin?"
    return teks, DescriptorVisual("susunan_objek", 1, data)
