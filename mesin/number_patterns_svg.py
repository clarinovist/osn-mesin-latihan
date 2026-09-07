"""SVG pola v2: gambar pertanyaan tanpa jumlah atau anotasi penyelesaian."""
from __future__ import annotations

import hashlib
import html

import design_tokens as T
from number_patterns_visual_data import validasi_korek, validasi_titik
from topic_number_patterns_svg import _ruas_bertumbuh


def bungkus(isi, judul, uraian, namespace):
    """Bungkus geometri internal dengan ID deterministik dan label escaped."""
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace pola wajib teks")
    try:
        ident = "pola2-" + hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:20]
    except UnicodeError as galat:
        raise ValueError("namespace pola tidak valid") from galat
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {T.POLA_LEBAR} {T.POLA_TINGGI}" '
        f'role="img" aria-labelledby="{ident}-judul {ident}-uraian" '
        f'style="display:block;width:100%;max-width:{T.LEBAR_VISUAL_SOAL};height:auto;margin:{T.JARAK_VISUAL_SOAL} auto">'
        f'<title id="{ident}-judul">{html.escape(judul)}</title>'
        f'<desc id="{ident}-uraian">{html.escape(uraian)}</desc>{isi}</svg>'
    )


def label(x, y, teks):
    return (f'<text x="{x}" y="{y}" font-size="{T.POLA_FONT}" text-anchor="middle" '
            f'fill="{T.TEKS_UTAMA}">{html.escape(teks)}</text>')


def posisi(indeks):
    return ((indeks % 2) * T.POLA_SEL_LEBAR, (indeks // 2) * T.POLA_SEL_TINGGI)


def gambar_korek(jumlah, maksimum, *, tebal_dari=None):
    """Geometri internal: sambungan eksplisit membuat ruas segaris dapat dihitung."""
    dasar = tuple(_ruas_bertumbuh(maksimum))
    semua = tuple(p for ruas in dasar for p in ruas)
    pusat_x = (min(x for x, _ in semua) + max(x for x, _ in semua)) / 2
    pusat_y = (min(y for _, y in semua) + max(y for _, y in semua)) / 2
    def letak(p):
        return (T.POLA_SEL_LEBAR / 2 + (p[0] - pusat_x) * T.POLA_RUAS,
                T.POLA_BENTUK_Y + (p[1] - pusat_y) * T.POLA_RUAS)
    garis = tuple(
        f'<line x1="{letak(a)[0]}" y1="{letak(a)[1]}" x2="{letak(b)[0]}" y2="{letak(b)[1]}" '
        f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.POLA_TEBAL if tebal_dari is not None and i >= tebal_dari else T.POLA_GARIS}"/>'
        for i, (a, b) in enumerate(dasar[:jumlah])
    )
    titik = sorted({p for ruas in dasar[:jumlah] for p in ruas})
    sambungan = tuple(f'<circle cx="{letak(p)[0]}" cy="{letak(p)[1]}" r="{T.POLA_SAMBUNGAN}" '
                     f'fill="{T.TEKS_UTAMA}"/>' for p in titik)
    return "".join((*garis, *sambungan))


def gambar_titik(n, *, baris_baru=False):
    """Baris segitiga terpusat; outline baris baru hanya untuk bantuan belajar."""
    return "".join(
        f'<circle cx="{T.POLA_SEL_LEBAR / 2 + (kolom - baris / 2) * T.POLA_TITIK_JARAK}" '
        f'cy="{T.POLA_TITIK_ATAS + baris * T.POLA_TITIK_JARAK}" r="{T.POLA_TITIK_RADIUS}" '
        f'fill="{T.LATAR_KARTU if baris_baru and baris == n - 1 else T.TEKS_UTAMA}" '
        f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.POLA_GARIS}"/>'
        for baris in range(n) for kolom in range(baris + 1)
    )


def render_pola(jenis, data, namespace):
    """Render pertanyaan hanya dari data allow-list, tanpa opsi bantuan."""
    if jenis == "korek":
        validasi_korek(data)
        maksimum = data["awal"] + 2 * data["tambah"]
        bentuk = tuple(gambar_korek(data["awal"] + i * data["tambah"], maksimum) for i in range(3))
        judul = "Pola batang korek api"
        uraian = "Tiga gambar pertumbuhan batang. Setiap ruas antara dua titik sambungan adalah satu batang."
    elif jenis == "titik":
        validasi_titik(data)
        bentuk = tuple(gambar_titik(n) for n in range(1, 5))
        judul = "Pola titik segitiga"
        uraian = "Empat gambar susunan titik berbentuk segitiga."
    else:
        raise ValueError("jenis pola tidak dikenal")
    isi = "".join(
        f'<g data-gambar="{i + 1}" transform="translate({posisi(i)[0]} {posisi(i)[1]})">'
        + satu + label(T.POLA_SEL_LEBAR / 2, T.POLA_LABEL_Y, f"Gambar {i + 1}") + '</g>'
        for i, satu in enumerate(bentuk)
    )
    return bungkus(isi, judul, uraian, namespace)
