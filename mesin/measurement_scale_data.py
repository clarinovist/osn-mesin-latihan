"""Allow-list besaran yang diberikan pada pertanyaan skala peta."""
from collections.abc import Mapping
from measurement_combinatorics_visual_data import bulat, field_tepat

FIELD_SKALA = {
    "cari_skala": frozenset({"varian", "peta", "sebenarnya"}),
    "cari_peta": frozenset({"varian", "skala", "sebenarnya"}),
    "cari_sebenarnya": frozenset({"varian", "skala", "peta"}),
}


def validasi_skala(data):
    if not isinstance(data, Mapping):
        raise ValueError("data skala wajib mapping")
    varian = data.get("varian")
    if not isinstance(varian, str) or varian not in FIELD_SKALA:
        raise ValueError("varian skala tidak didukung")
    field_tepat(data, FIELD_SKALA[varian])
    for nama in FIELD_SKALA[varian] - {"varian"}:
        bulat(data[nama], nama, 1, 10**9)
    if varian == "cari_peta":
        sisa = data["sebenarnya"] * 100000 % data["skala"]
    elif varian == "cari_sebenarnya":
        sisa = data["peta"] * data["skala"] % 100000
    else:
        sisa = data["sebenarnya"] * 100000 % data["peta"]
    if sisa:
        raise ValueError("data skala versi ini wajib menghasilkan bilangan bulat")
