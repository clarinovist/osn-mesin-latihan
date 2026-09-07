"""Petak menyatakan semua ruas sah tanpa memberi jumlah atau rute solusi."""
from __future__ import annotations

import design_tokens as T
from measurement_combinatorics_visual_data import validasi_petak
from phase6_svg import bungkus_svg
from plane_geometry_svg_primitives import angka, garis, teks


def ringkasan_petak(data):
    validasi_petak(data)
    return (f"Petak {data['b']} baris dan {data['k']} kolom. Kota A di sudut kiri atas, "
            "Kota B di sudut kanan bawah. Hanya bergerak ke kanan atau ke bawah.")


def render_petak(data, namespace):
    validasi_petak(data)
    b, k = data["b"], data["k"]
    sel = min(T.PETAK_SEL, T.PETAK_AREA_LEBAR / k, T.PETAK_AREA_TINGGI / b)
    x, y = (T.FASE6_LEBAR - k * sel) / 2, T.PETAK_ATAS
    mendatar = "".join(
        garis(x + i * sel, y + j * sel, x + (i + 1) * sel, y + j * sel, "sisi-petak")
        for j in range(b + 1) for i in range(k)
    )
    tegak = "".join(
        garis(x + i * sel, y + j * sel, x + i * sel, y + (j + 1) * sel, "sisi-petak")
        for j in range(b) for i in range(k + 1)
    )
    titik = "".join(
        f'<circle class="titik-petak" cx="{angka(x + i * sel)}" cy="{angka(y + j * sel)}" '
        f'r="{T.PETAK_TITIK}" fill="{T.TEKS_UTAMA}"/>'
        for j in range(b + 1) for i in range(k + 1)
    )
    label = (teks(x, y - T.PETAK_LABEL_JARAK, "A")
             + teks(x + k * sel, y + b * sel + T.PETAK_LABEL_JARAK, "B")
             + teks(T.FASE6_LEBAR / 2, T.PETAK_CATATAN_Y,
                    f"{b} baris × {k} kolom · Kanan atau bawah"))
    return bungkus_svg(mendatar + tegak + titik + label, ringkasan_petak(data), namespace, "Petak lintasan")
