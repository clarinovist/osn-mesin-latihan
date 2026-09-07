"""Proyeksi ruang masalah kombinatorik, bukan diagram solusi."""
from __future__ import annotations

from measurement_combinatorics_visual_data import validasi_petak
from visual_contract import DescriptorVisual


def proyeksi_kombinatorik(template_id, parameter):
    from combinatorics_sets_visual import proyeksi_venn
    from combinatorics_arrangements_visual import TEMPLATE_SUSUNAN, proyeksi_susunan
    if template_id == "inklusi_eksklusi_2":
        return proyeksi_venn(parameter)
    if template_id in TEMPLATE_SUSUNAN:
        return proyeksi_susunan(template_id, parameter)
    if template_id != "jalur_petak":
        return None
    validasi_petak(parameter)
    data = {"b": parameter["b"], "k": parameter["k"]}
    teks = (
        "Perhatikan petak dari Kota A ke Kota B. Gerak hanya ke kanan atau ke bawah.\n"
        "Berapa banyak jalur terpendek yang mungkin?"
    )
    return teks, DescriptorVisual("jalur_petak", 1, data)
