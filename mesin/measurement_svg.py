"""Jam analog dan linimasa netral: hanya fakta yang diberikan pada soal."""
from __future__ import annotations

import math

import design_tokens as T
from measurement_combinatorics_visual_data import validasi_waktu
from phase6_svg import bungkus_svg
from plane_geometry_svg_primitives import garis, teks


def waktu_teks(total):
    return f"{(total // 60) % 24:02d}.{total % 60:02d}"


def durasi_teks(total):
    return f"{total // 60} jam {total % 60} menit"


def ringkasan_waktu(data):
    validasi_waktu(data)
    def label(nama):
        if nama not in data:
            return f"{nama}: belum diketahui"
        total = data[nama]
        hari = " hari berikutnya" if total >= 1440 else ""
        return f"{nama}: pukul {waktu_teks(total)}{hari}"
    durasi = durasi_teks(data["durasi"]) if "durasi" in data else "belum diketahui"
    return f"Kegiatan {label('mulai')}; {label('selesai')}; durasi: {durasi}. Format 24 jam."


def _titik(cx, radius, sudut):
    radian = math.radians(sudut)
    return cx + radius * math.sin(radian), T.JAM_PUSAT_Y - radius * math.cos(radian)


def _jam(cx, total):
    cy, r = T.JAM_PUSAT_Y, T.JAM_RADIUS
    muka = (f'<circle cx="{cx}" cy="{cy}" r="{r}" '
            f'fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>')
    tanda = "".join(garis(*_titik(cx, r * T.JAM_TANDA_DALAM, i * 30),
                          *_titik(cx, r, i * 30), "tanda-jam") for i in range(12))
    label = "".join(teks(*_titik(cx, r * T.JAM_ANGKA_RADIUS, i * 30), i or 12,
                          ukuran=T.JAM_ANGKA_FONT, dominant_baseline="central") for i in range(12))
    sudut_jam = ((total // 60) % 12) * 30 + (total % 60) / 2
    pendek = garis(cx, cy, *_titik(cx, r * T.JAM_JARUM_PENDEK, sudut_jam), "jarum-jam")
    panjang = garis(cx, cy, *_titik(cx, r * T.JAM_JARUM_PANJANG, (total % 60) * 6), "jarum-menit")
    return muka + tanda + label + pendek + panjang


def _panel(cx, nama, data):
    judul = teks(cx, T.JAM_JUDUL_Y, nama.capitalize())
    if nama not in data:
        return judul + teks(cx, T.JAM_PUSAT_Y, "?", "waktu-target")
    total = data[nama]
    hari = "Hari berikutnya" if total >= 1440 else ""
    return (judul + _jam(cx, total) + teks(cx, T.JAM_DIGITAL_Y, waktu_teks(total))
            + teks(cx, T.JAM_HARI_Y, hari, ukuran=T.GEO_FONT_CATATAN))


def render_waktu(data, namespace):
    validasi_waktu(data)
    panel = "".join(_panel(cx, nama, data) for cx, nama in zip(T.JAM_PUSAT_X, ("mulai", "selesai")))
    x1, x2 = T.JAM_PENGHUBUNG_X
    y, ujung = T.JAM_PUSAT_Y, T.JAM_PANAH
    arah = (garis(x1, y, x2, y) + garis(x2 - ujung, y - ujung, x2, y)
            + garis(x2 - ujung, y + ujung, x2, y))
    durasi = durasi_teks(data["durasi"]) if "durasi" in data else "?"
    label = (teks(T.FASE6_LEBAR / 2, T.JAM_DURASI_Y, "Durasi: " + durasi)
             + teks(T.FASE6_LEBAR / 2, T.JAM_CATATAN_Y, "Jarak antarpanel tidak menyatakan durasi",
                    ukuran=T.GEO_FONT_CATATAN))
    return bungkus_svg(panel + arah + label, ringkasan_waktu(data), namespace, "Waktu kegiatan")
