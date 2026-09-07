"""Skema dua kota yang tidak menyandikan panjang target lewat geometri."""
from collections.abc import Mapping
import design_tokens as T
from measurement_combinatorics_visual_data import bulat, field_tepat
from measurement_scale_data import FIELD_SKALA, validasi_skala
from phase6_svg import bungkus_svg
from plane_geometry_svg_primitives import garis, teks
from visual_contract import DescriptorVisual


def proyeksi_skala(parameter):
    if not isinstance(parameter, Mapping):
        raise ValueError("parameter skala wajib mapping")
    versi = parameter.get("versi", 1)
    if type(versi) is not int or versi not in (1, 2):
        raise ValueError("versi skala tidak didukung")
    if versi == 1:
        return None
    field_tepat(parameter, {"versi", "varian", "peta", "skala", "sebenarnya"})
    for nama in ("peta", "skala", "sebenarnya"):
        bulat(parameter[nama], nama, 1, 10**9)
    if parameter["peta"] * parameter["skala"] != parameter["sebenarnya"] * 100000:
        raise ValueError("relasi skala tidak konsisten")
    varian = parameter["varian"]
    if not isinstance(varian, str) or varian not in FIELD_SKALA:
        raise ValueError("varian skala tidak didukung")
    data = {nama: parameter[nama] for nama in sorted(FIELD_SKALA[varian])}
    validasi_skala(data)
    tanya = {"cari_skala": "Berapa skala peta tersebut?",
             "cari_peta": "Berapa jarak Kota A ke Kota B pada peta (cm)?",
             "cari_sebenarnya": "Berapa jarak sebenarnya Kota A ke Kota B (km)?"}[varian]
    return "Perhatikan skema peta dan data yang diberikan.\n" + tanya, DescriptorVisual("skala_peta", 1, data)


def ringkasan_skala(data):
    validasi_skala(data)
    peta = f"{data['peta']} cm" if "peta" in data else "belum diketahui"
    nyata = f"{data['sebenarnya']} km" if "sebenarnya" in data else "belum diketahui"
    skala = f"1:{data['skala']}" if "skala" in data else "belum diketahui"
    return f"Kota A dan B; jarak peta {peta}; jarak sebenarnya {nyata}; skala {skala}. Skema tidak berskala."


def render_skala(data, namespace):
    validasi_skala(data)
    kiri, kanan = T.PETA_UJUNG_X
    y = T.PETA_GARIS_Y
    ukuran = T.PETA_TANDA
    jalur = (garis(kiri, y, kanan, y) + garis(kiri, y-ukuran, kiri, y+ukuran)
             + garis(kanan, y-ukuran, kanan, y+ukuran))
    peta = str(data["peta"]) if "peta" in data else "?"
    nyata = str(data["sebenarnya"]) if "sebenarnya" in data else "?"
    skala = str(data["skala"]) if "skala" in data else "?"
    label = (teks(kiri, T.PETA_KOTA_Y, "Kota A") + teks(kanan, T.PETA_KOTA_Y, "Kota B")
             + teks(T.FASE6_LEBAR/2, T.PETA_JARAK_Y, f"Jarak pada peta: {peta} cm")
             + teks(T.FASE6_LEBAR/2, T.PETA_SKALA_Y, f"Skala 1:{skala}")
             + teks(T.FASE6_LEBAR/2, T.PETA_NYATA_Y, f"Jarak sebenarnya: {nyata} km")
             + teks(T.FASE6_LEBAR/2, T.PETA_CATATAN_Y, "Tidak berskala", ukuran=T.GEO_FONT_CATATAN))
    return bungkus_svg(jalur + label, ringkasan_skala(data), namespace, "Skema peta")
