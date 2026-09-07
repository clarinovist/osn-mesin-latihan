"""SVG ruang deterministik dari descriptor aman, tanpa Soal atau basis data."""
from __future__ import annotations
import hashlib
import html

import design_tokens as T
import solid_geometry_shapes as bentuk
from plane_geometry_svg_primitives import garis, siku, teks
from solid_geometry_visual_data import validasi_data


def _ukuran(posisi, nama, nilai):
    return teks(posisi[0], posisi[1], f'{nama} = {nilai} cm', kelas='label-ukuran')


def _kotak(d):
    isi = bentuk.kotak()
    model = d['model']
    if model.startswith('kubus'):
        return isi + _ukuran(T.RUANG_LABEL_S, 's', d.get('s', '?'))
    return (isi + _ukuran(T.RUANG_LABEL_S, 'p', d.get('p', '?'))
            + _ukuran(T.RUANG_LABEL_L, 'l', d['l'])
            + _ukuran(T.RUANG_LABEL_T, 't', d['t']))


def _prisma(d):
    a, b, c = T.RUANG_PRISMA
    kaki = (c[0], a[1])
    isi = bentuk.prisma() + garis(*kaki, *c, kelas='tinggi-alas', putus=True)
    isi += siku(*kaki)
    return (isi + _ukuran(T.RUANG_LABEL_A, 'a', d['a'])
            + _ukuran(T.RUANG_LABEL_H, 'h', d['tinggi_alas'])
            + _ukuran(T.RUANG_LABEL_PRISMA_T, 'T', d.get('tinggi', '?')))


def _tabung(d):
    x, y = T.RUANG_TABUNG_PUSAT
    rx, _ = T.RUANG_TABUNG_RADIUS
    titik = f'<circle class="pusat-alas" cx="{x}" cy="{y}" r="{T.RUANG_TITIK_PUSAT}" fill="{T.TEKS_UTAMA}"/>'
    return (bentuk.lengkung() + titik + garis(x, y, x+rx, y, 'jari-jari')
            + _ukuran(T.RUANG_LABEL_R, 'r', d['r'])
            + _ukuran(T.RUANG_LABEL_T, 't', d.get('t', '?')))


def _unsur(d):
    nama = d['bangun']
    if nama in ('kubus', 'balok'):
        isi = bentuk.kotak()
    elif nama == 'prisma_segitiga':
        isi = bentuk.prisma()
    elif nama == 'limas_segiempat':
        isi = bentuk.limas()
    else:
        isi = bentuk.lengkung(nama == 'kerucut')
    return isi + teks(*T.RUANG_LABEL_JUMLAH, 'Contoh satu '+nama.replace('_', ' '),
                      ukuran=T.GEO_FONT_CATATAN)


def _badan(d):
    model = d['model']
    if model == 'unsur':
        return _unsur(d)
    if model == 'kubus_dicat':
        return bentuk.dicat(d['n'], d['jumlah'])
    if model == 'jaring':
        return bentuk.jaring(d['opsi'])
    if model.startswith(('kubus', 'balok')):
        isi = _kotak(d)
    elif model.startswith('prisma'):
        isi = _prisma(d)
    else:
        isi = _tabung(d)
    if model.endswith('_balik'):
        volume = d.get('besaran', 'volume') == 'volume'
        nama, satuan = ('V', 'cm³') if volume else ('LP', 'cm²')
        isi += teks(*T.RUANG_LABEL_TOTAL, f"{nama} = {d['nilai']} {satuan}", 'besaran-diketahui')
    return isi


def ringkasan_geometri_ruang(data):
    """Deskripsikan fakta posisi/ukuran tanpa menghitung jawaban."""
    validasi_data(data)
    m = data['model']
    if m == 'jaring':
        return 'Posisi persegi (baris,kolom), dihitung dari atas dan kiri: ' + ' '.join(
            'ABCDE'[i]+': '+', '.join(f'({r+1},{c+1})' for r, c in pola)+'.'
            for i, pola in enumerate(data['opsi']))
    if m == 'unsur':
        return (f"Contoh satu {data['bangun'].replace('_', ' ')} dari {data['jumlah']} bangun identik. "
                'Garis putus-putus menunjukkan bagian yang tersembunyi.')
    if m == 'kubus_dicat':
        return (f"Contoh satu dari {data['jumlah']} kubus besar identik; tiap rusuk dibagi {data['n']} "
                'bagian sama panjang. Semua sisi luar dicat. Kisi pada tiga muka yang terlihat '
                'menunjukkan pembagian menjadi kubus kecil sama besar.')
    label = {'s': 'rusuk', 'p': 'panjang', 'l': 'lebar', 't': 'tinggi', 'r': 'jari-jari',
             'a': 'alas segitiga', 'tinggi_alas': 'tinggi segitiga', 'tinggi': 'tinggi prisma'}
    rincian = tuple(f'{nama} {data[k]} cm' for k, nama in label.items() if k in data)
    fakta = f"Sketsa {m.replace('_balik', '')}" + (': '+', '.join(rincian) if rincian else '') + '.'
    if m.endswith('_balik'):
        volume = data.get('besaran', 'volume') == 'volume'
        besaran, satuan = ('Volume', 'cm³') if volume else ('Luas permukaan', 'cm²')
        fakta += f" {besaran} {data['nilai']} {satuan}; ukuran yang dicari bertanda ?."
    return fakta


def render_geometri_ruang(data, namespace):
    """Render visual tanpa mengambil parameter target atau data rahasia."""
    validasi_data(data)
    if not isinstance(namespace, str) or not namespace:
        raise ValueError('namespace wajib teks tidak kosong')
    ident = 'ruang-'+hashlib.sha256(namespace.encode('utf-8')).hexdigest()[:20]
    badan = _badan(data)
    tinggi = T.RUANG_JARING_TINGGI if data['model'] == 'jaring' else T.RUANG_TINGGI
    if data['model'] != 'jaring':
        badan += teks(*T.RUANG_LABEL_SKALA, 'Tidak berskala', ukuran=T.GEO_FONT_CATATAN)
    deskripsi = html.escape(ringkasan_geometri_ruang(data))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="soal-visual" '
            f'viewBox="0 0 {T.GEO_LEBAR} {tinggi}" role="img" '
            f'aria-labelledby="{ident}-judul {ident}-desc" '
            f'style="display:block;width:100%;max-width:{T.LEBAR_VISUAL_SOAL};height:auto;margin:{T.JARAK_VISUAL_SOAL} auto">'
            f'<title id="{ident}-judul">Bangun ruang</title><desc id="{ident}-desc">{deskripsi}</desc>'
            f'{badan}</svg>')
