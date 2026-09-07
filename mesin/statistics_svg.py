"""SVG statistika deterministik; hanya menerima data pertanyaan tervalidasi."""
from __future__ import annotations

import hashlib
import html
import math
import design_tokens as T
from statistics_visual_data import validasi_data


def _teks(x, y, isi, kelas='', jangkar='start'):
    return (f'<text x="{x:g}" y="{y:g}" class="{kelas}" text-anchor="{jangkar}" '
            f'font-size="{T.STAT_FONT}" fill="{T.TEKS_UTAMA}">{html.escape(str(isi))}</text>')


def _garis(x1, y1, x2, y2, warna=None):
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{warna or T.TEKS_UTAMA}" stroke-width="{T.STAT_GARIS}"/>')


def _ikon(x, y):
    return (f'<circle cx="{x:g}" cy="{y:g}" r="{T.STAT_IKON_RADIUS}" '
            f'fill="{T.AKSEN_TEAL_TUA}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.STAT_GARIS_TIPIS}"/>')


def _batang(data):
    nilai = data['data']
    langkah = 5 if max(nilai) <= 25 else 10
    atas = math.ceil(max(nilai) / langkah) * langkah
    skala = T.STAT_PLOT_TINGGI / atas
    dasar = T.STAT_ATAS + T.STAT_PLOT_TINGGI
    kiri, kanan = T.STAT_PLOT_KIRI, T.STAT_PLOT_KANAN
    kisi = ''.join(_garis(kiri, dasar-v*skala, kanan, dasar-v*skala,
                         T.BORDER_HALUS if v % langkah else T.CHART_AXIS)
                   for v in range(atas + 1))
    label = ''.join(_teks(kiri-T.STAT_LABEL_DX, dasar-v*skala+T.STAT_LABEL_DY, v, 'skala', 'end')
                    for v in range(0, atas+1, langkah))
    jarak = (kanan-kiri) / len(nilai)
    lebar = jarak / 2
    batang = ''.join(
        f'<rect class="batang-data" x="{kiri+(i+.25)*jarak:g}" '
        f'y="{dasar-v*skala:.6f}" width="{lebar:g}" height="{v*skala:.6f}" '
        f'fill="{T.AKSEN_TEAL_TUA}" stroke="{T.TEKS_UTAMA}"/>'
        + _teks(kiri+(i+.5)*jarak, dasar+T.STAT_MARGIN, nama, jangkar='middle')
        for i, (nama, v) in enumerate(zip(data['nama'], nilai)))
    return kisi + label + batang, dasar + 2*T.STAT_MARGIN


def _turus(nilai, y):
    jarak, bundel = T.STAT_TURUS_JARAK, T.STAT_TURUS_BUNDEL
    def coret(i):
        x = T.STAT_MARGIN + (i//5)*bundel
        if i % 5 == 4:
            return _garis(x-jarak/2, y+T.STAT_TURUS_TINGGI,
                          x+3.5*jarak, y)
        return _garis(x+(i%5)*jarak, y, x+(i%5)*jarak, y+T.STAT_TURUS_TINGGI)
    return ''.join(coret(i) for i in range(nilai))


def _nama_baris(nama, y):
    """Bagi label panjang tanpa mengubah isi kategorinya."""
    batas = T.STAT_NAMA_PER_BARIS
    potongan = tuple(nama[i:i+batas] for i in range(0, len(nama), batas))
    if len(potongan) == 1:
        return _teks(T.STAT_MARGIN, y, nama), y
    isi = ''.join(
        f'<tspan x="{T.STAT_MARGIN}" y="{y+i*T.STAT_FONT:g}">{html.escape(p)}</tspan>'
        for i, p in enumerate(potongan))
    return (f'<text font-size="{T.STAT_FONT}" fill="{T.TEKS_UTAMA}">{isi}</text>',
            y+(len(potongan)-1)*T.STAT_FONT)


def _baris_data(jenis, data):
    nilai = data['data'] if jenis == 'turus' else data['gambar']
    def baris(i, nama, v):
        y = T.STAT_ATAS + i*T.STAT_BARIS
        label, akhir = _nama_baris(nama, y)
        isi = (_turus(v, akhir+T.STAT_FONT/2) if jenis == 'turus' else
               ''.join(_ikon(T.STAT_MARGIN+j*T.STAT_IKON_JARAK, akhir+T.STAT_MARGIN)
                       for j in range(v)))
        return '<g class="baris-data">' + label + isi + '</g>'
    badan = ''.join(baris(i,n,v) for i,(n,v) in enumerate(zip(data['nama'],nilai)))
    tinggi = T.STAT_ATAS + len(nilai)*T.STAT_BARIS
    if jenis == 'piktogram':
        badan += _ikon(T.STAT_MARGIN, tinggi) + _teks(
            2*T.STAT_MARGIN, tinggi+T.STAT_LABEL_DY, f"1 gambar = {data['satuan']} buah")
        tinggi += T.STAT_MARGIN
    return badan, tinggi


def _lingkaran(data, ident):
    cari_nilai = data['varian'] == 'cari_nilai'
    sudut = data['sudut'] if cari_nilai else data['nilai']*360/data['total']
    cx, cy, r = T.STAT_PUSAT_X, T.STAT_PUSAT_Y, T.STAT_RADIUS
    ex, ey = cx+r*math.sin(math.radians(sudut)), cy-r*math.cos(math.radians(sudut))
    arsiran = (f'<defs><pattern id="{ident}-arsir" width="{T.STAT_ARSIR_JARAK}" height="{T.STAT_ARSIR_JARAK}" patternUnits="userSpaceOnUse">'
               f'<path d="M 0 {T.STAT_ARSIR_JARAK} L {T.STAT_ARSIR_JARAK} 0" stroke="{T.TEKS_SUBTLE}" stroke-width="{T.STAT_GARIS_TIPIS}"/></pattern></defs>')
    sektor = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{T.LATAR_KARTU}" '
              f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.STAT_GARIS}"/>'
              f'<path class="sektor-data" d="M {cx} {cy} L {cx} {cy-r} A {r} {r} 0 '
              f'{int(sudut > 180)} 1 {ex:.6f} {ey:.6f} Z" fill="url(#{ident}-arsir)" '
              f'stroke="{T.TEKS_UTAMA}" stroke-width="{T.STAT_GARIS}"/>')
    nama = 'Olahraga' if cari_nilai else 'Membaca'
    label = f"{nama}: {data['sudut']}°" if cari_nilai else f"{nama}: {data['nilai']} siswa; sudut ?"
    badan = (arsiran + sektor + _teks(cx, cy+r+T.STAT_MARGIN, 'Daerah bergaris: '+nama, jangkar='middle')
             + _teks(cx, cy+r+2*T.STAT_MARGIN, label, jangkar='middle')
             + _teks(cx, cy+r+3*T.STAT_MARGIN, f"Total {data['total']} siswa", jangkar='middle'))
    return badan, cy+r+4*T.STAT_MARGIN


def render_statistika(jenis, data, namespace):
    """Render data aman; nama/angka diuji ulang pada batas renderer."""
    validasi_data(jenis, data)
    if not isinstance(namespace, str) or not namespace:
        raise ValueError('namespace wajib teks tidak kosong')
    ident = 'stat-' + hashlib.sha256((jenis+':'+namespace).encode()).hexdigest()[:20]
    if jenis == 'batang':
        badan, tinggi = _batang(data)
    elif jenis in ('turus', 'piktogram'):
        badan, tinggi = _baris_data(jenis, data)
    else:
        badan, tinggi = _lingkaran(data, ident)
    deskripsi = ('Amati diagram dan label yang diberikan. Versi baca gambar; '
                 'nilai yang perlu dibaca tidak dituliskan ulang sebagai alternatif teks.')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {T.STAT_LEBAR} {tinggi}" '
            f'role="img" aria-labelledby="{ident}-judul {ident}-desc">'
            f'<title id="{ident}-judul">{html.escape(jenis.capitalize())}</title>'
            f'<desc id="{ident}-desc">{deskripsi}</desc>{badan}</svg>')
