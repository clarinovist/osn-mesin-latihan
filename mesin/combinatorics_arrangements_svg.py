"""Kartu objek dan ruang jawaban kosong tanpa diagram enumerasi solusi."""
import design_tokens as T
from combinatorics_visual_data import validasi_susunan
from phase6_svg import bungkus_svg
from plane_geometry_svg_primitives import angka, teks


def ringkasan_susunan(data):
    validasi_susunan(data)
    objek = ", ".join(data["objek"])
    aturan = data["aturan"]
    syarat = ("Bilangan genap." if aturan == "genap" else f"Bilangan lebih besar dari {data['batas']}." if aturan == "lebih_dari" else "")
    if aturan == "blok":
        syarat = " dan ".join(data["berdampingan"]) + " harus berdampingan."
    if aturan == "kombinasi":
        syarat = "Urutan anggota tim tidak penting."
    return f"Objek tersedia: {objek}. Banyak yang dipilih: {data['ambil']}. {syarat} Ruang jawaban belum diisi."


def _kotak(x, y, lebar, kelas):
    return (f'<rect class="{kelas}" x="{angka(x)}" y="{angka(y)}" '
            f'width="{angka(lebar)}" height="{T.OBJEK_TINGGI}" fill="{T.LATAR_KARTU}" '
            f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>')


def _kartu(objek):
    def kartu(i, isi):
        baris, kolom = divmod(i, T.OBJEK_PER_BARIS)
        jumlah = min(T.OBJEK_PER_BARIS, len(objek) - baris*T.OBJEK_PER_BARIS)
        rentang = jumlah*T.OBJEK_LEBAR + (jumlah-1)*T.OBJEK_JARAK
        x = (T.FASE6_LEBAR-rentang)/2 + kolom*(T.OBJEK_LEBAR+T.OBJEK_JARAK)
        y = T.OBJEK_ATAS + baris*T.OBJEK_BARIS
        return (_kotak(x, y, T.OBJEK_LEBAR, "objek-tersedia")
                + teks(x+T.OBJEK_LEBAR/2, y+T.OBJEK_TINGGI/2, isi, dominant_baseline="central"))
    return "".join(kartu(i, isi) for i, isi in enumerate(objek))


def _slot(jumlah):
    lebar = min(T.OBJEK_LEBAR, (T.PETAK_AREA_LEBAR-(jumlah-1)*T.OBJEK_JARAK)/jumlah)
    rentang = jumlah*lebar + (jumlah-1)*T.OBJEK_JARAK
    def slot(i):
        x = (T.FASE6_LEBAR-rentang)/2 + i*(lebar+T.OBJEK_JARAK)
        return (_kotak(x, T.SLOT_ATAS, lebar, "slot-kosong")
                + teks(x+lebar/2, T.SLOT_ATAS+T.OBJEK_TINGGI+T.SLOT_LABEL_JARAK, i+1))
    return "".join(slot(i) for i in range(jumlah))


def render_susunan(data, namespace):
    validasi_susunan(data)
    isi = teks(T.FASE6_LEBAR/2, T.OBJEK_JUDUL_Y, "Kartu yang tersedia") + _kartu(data["objek"])
    if data["aturan"] == "kombinasi":
        kiri, kanan = T.TIM_UJUNG_X
        isi += (_kotak(kiri, T.SLOT_ATAS, kanan-kiri, "area-tim")
                + teks(T.FASE6_LEBAR/2, T.SLOT_JUDUL_Y, f"Pilih {data['ambil']} anggota tim"))
    else:
        isi += teks(T.FASE6_LEBAR/2, T.SLOT_JUDUL_Y, "Posisi yang akan diisi") + _slot(data["ambil"])
    isi += teks(T.FASE6_LEBAR/2, T.SUSUNAN_CATATAN_Y, "Kartu di atas bukan susunan jawaban", ukuran=T.GEO_FONT_CATATAN)
    return bungkus_svg(isi, ringkasan_susunan(data), namespace, "Kartu dan susunan")
