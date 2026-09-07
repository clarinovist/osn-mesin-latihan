"""Renderer SVG geometri datar deterministik tanpa state atau basis data."""
from __future__ import annotations

import hashlib
import html
import math

import design_tokens as T
from plane_geometry_visual_data import validasi_data
from plane_geometry_svg_primitives import (
    angka,
    garis,
    label_tidak_berskala,
    pola_arsir,
    poligon,
    polyline,
    siku,
    teks,
)


def _validasi(data):
    validasi_data(data)


def _label_sudut(x, y, isi, vertex):
    return teks(x, y, isi, "label-sudut", data_vertex=vertex)


def _sudut_pasangan(d):
    cx, cy, panjang = T.GEO_SUDUT_X, T.GEO_SUDUT_Y, T.GEO_SINAR
    total, diketahui = d["total"], d["diketahui"]
    sudut_tengah = diketahui
    arah = (0, sudut_tengah, total)
    sinar = "".join(
        garis(cx, cy, cx + panjang * math.cos(math.radians(a)),
              cy - panjang * math.sin(math.radians(a)), "sinar-sudut")
        for a in arah
    )
    lx = cx + T.GEO_RADIUS_LABEL_SUDUT * math.cos(math.radians(diketahui / 2))
    ly = cy - T.GEO_RADIUS_LABEL_SUDUT * math.sin(math.radians(diketahui / 2))
    ux = cx + T.GEO_RADIUS_LABEL_SUDUT * math.cos(math.radians((diketahui + total) / 2))
    uy = cy - T.GEO_RADIUS_LABEL_SUDUT * math.sin(math.radians((diketahui + total) / 2))
    isi = sinar + teks(lx, ly+T.GEO_BASELINE_LABEL_SUDUT, f"{diketahui}°") + teks(ux, uy+T.GEO_BASELINE_LABEL_SUDUT, "?")
    if total == 90:
        isi += siku(cx, cy, 1, -1)
    return isi


def _sudut_rasio(d):
    cx, cy, panjang = T.GEO_SUDUT_X, T.GEO_SUDUT_Y, T.GEO_SINAR
    tengah = 35
    isi = garis(cx, cy, cx-panjang, cy, "sinar-sudut")
    isi += garis(cx, cy, cx+panjang, cy, "sinar-sudut")
    isi += garis(cx, cy, cx+panjang*math.cos(math.radians(tengah)),
                 cy-panjang*math.sin(math.radians(tengah)), "sinar-sudut")
    return isi + teks(225, 140, "x") + teks(145, 115, f"{d['kali']}x")


def _segitiga(d, rasio=False):
    pts = ((T.GEO_SEGITIGA_KIRI, T.GEO_SEGITIGA_ALAS_Y),
           (T.GEO_SEGITIGA_KANAN, T.GEO_SEGITIGA_ALAS_Y),
           (T.GEO_SEGITIGA_PUNCAK_X, T.GEO_SEGITIGA_PUNCAK_Y))
    isi = poligon(pts, "segitiga")
    if rasio:
        nilai = ("x" if d["p"] == 1 else f"{d['p']}x",
                 "x" if d["q"] == 1 else f"{d['q']}x",
                 "x" if d["r"] == 1 else f"{d['r']}x")
    else:
        nilai = (f"{d['a']}°", f"{d['b']}°", "?")
    return (isi + _label_sudut(*T.GEO_LABEL_SEGITIGA[0], nilai[0], "A")
            + _label_sudut(*T.GEO_LABEL_SEGITIGA[1], nilai[1], "B")
            + _label_sudut(*T.GEO_LABEL_SEGITIGA[2], nilai[2], "C"))


def _segitiga_luar(d):
    a, b, c = (70, 180), (250, 180), (175, 50)
    # Busur kecil di B berada antara sisi BC dan perpanjangan alas ke kanan.
    busur = '<path class="busur-target-luar" d="M 265 180 A 15 15 0 0 0 241.3 167.8" fill="none" stroke="{}" stroke-width="{}"/>'.format(T.TEKS_UTAMA, T.GEO_GARIS)
    return (
        poligon((a, b, c), "segitiga")
        + polyline((a, b, (325, 180)), "alas-diperpanjang")
        + busur
        + _label_sudut(*T.GEO_LABEL_SEGITIGA_LUAR[0], f"{d['a']}°", "A")
        + _label_sudut(*T.GEO_LABEL_SEGITIGA_LUAR[1], f"{d['b']}°", "C")
        + _label_sudut(*T.GEO_LABEL_SEGITIGA_LUAR[2], "?", "B-luar")
    )


def _persegi_panjang(d, balik=False):
    if balik:
        w, h = T.GEO_BENTUK_LEBAR, T.GEO_BENTUK_TINGGI * 0.7
    else:
        skala = min(T.GEO_BENTUK_LEBAR/d["p"], T.GEO_BENTUK_TINGGI/d["l"])
        w, h = d["p"]*skala, d["l"]*skala
    x, y = (T.GEO_LEBAR-w)/2, T.GEO_BENTUK_ATAS + (T.GEO_BENTUK_TINGGI-h)/2
    isi = f'<rect class="persegi-panjang" x="{x}" y="{y}" width="{w}" height="{h}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
    isi += teks(x+w/2, y+h+22, f"{d['p']} cm")
    if balik:
        isi += teks(x-T.GEO_JARAK_LABEL_SISI, y+h/2, "?", jangkar="end")
        isi += teks(x+w/2, y-12, f"K = {d['K']} cm")
    else:
        isi += teks(x-T.GEO_JARAK_LABEL_SISI, y+h/2, f"{d['l']} cm", jangkar="end")
    return isi


def _tinggi(d, jajargenjang=False):
    # Bentuk di-auto-fit dari alas, tinggi, dan offset horizontal sisi miring.
    # Kaki tinggi eksternal hanya bila offset lebih besar dari alas; selain itu
    # kaki dipilih di dalam alas agar gambar tidak menyesatkan.
    dasar_y = T.GEO_SEGITIGA_ALAS_Y
    ruang_w = T.GEO_BENTUK_LEBAR
    ruang_h = T.GEO_BENTUK_TINGGI
    offset_asli = math.sqrt(d["s"] ** 2 - d["t"] ** 2)
    lebar_asli = d["a"] + offset_asli if jajargenjang else max(d["a"], offset_asli)
    skala = min(ruang_h / d["t"], ruang_w / lebar_asli)
    alas = d["a"] * skala
    tinggi = d["t"] * skala
    offset = offset_asli * skala
    kiri = (T.GEO_LEBAR-alas-offset)/2 if jajargenjang else (T.GEO_LEBAR-max(alas, offset))/2
    kaki_x = kiri if jajargenjang else kiri+offset
    puncak = (kaki_x, dasar_y-tinggi)
    a = (kiri, dasar_y)
    b = (kiri + alas, dasar_y)
    if jajargenjang:
        isi = poligon((a, b, (b[0]+offset, puncak[1]), (a[0]+offset, puncak[1])), "jajargenjang")
    else:
        isi = poligon((a, b, puncak), "segitiga")
    isi += garis(a[0], a[1], b[0], b[1], "alas")
    isi += garis(kaki_x, dasar_y, puncak[0], puncak[1], "tinggi", putus=True)
    miring_atas = (a[0]+offset, puncak[1]) if jajargenjang else puncak
    if jajargenjang and puncak[0] != miring_atas[0]:
        isi += garis(puncak[0], puncak[1], miring_atas[0], miring_atas[1], "perpanjangan-tinggi", putus=True)
    isi += garis(a[0], a[1], miring_atas[0], miring_atas[1], "sisi-miring")
    if jajargenjang:
        isi += garis(b[0], b[1], b[0]+offset, puncak[1], "sisi-miring")
    if kaki_x < a[0] or kaki_x > b[0]:
        ujung = a[0] if kaki_x < a[0] else b[0]
        isi += garis(kaki_x, dasar_y, ujung, dasar_y, "perpanjangan-alas", putus=True)
    arah_siku = 1 if kaki_x <= b[0] else -1
    isi += siku(kaki_x, dasar_y, arah_siku, -1)
    return isi + "".join(teks(*posisi, f"{nama} = {d[nama]} cm")
                         for posisi, nama in zip(T.GEO_LABEL_UKURAN, ("a", "t", "s")))


def _trapesium(d):
    skala = min(T.GEO_BENTUK_LEBAR/max(d["a"], d["b"]), T.GEO_BENTUK_TINGGI/d["t"])
    bawah, atas, tinggi = d["b"]*skala, d["a"]*skala, d["t"]*skala
    x0, y0 = (T.GEO_LEBAR-bawah)/2, T.GEO_SEGITIGA_ALAS_Y
    masuk = (bawah-atas)/2
    pts = ((x0, y0), (x0+bawah, y0), (x0+bawah-masuk, y0-tinggi), (x0+masuk, y0-tinggi))
    sambungan = garis(x0+masuk, y0, x0, y0, "perpanjangan-alas", putus=True) if masuk < 0 else ""
    return (poligon(pts, "trapesium") + sambungan + teks(T.GEO_LEBAR/2, y0+T.GEO_MARGIN, f"{d['b']} cm")
            + teks(T.GEO_LEBAR/2, max(T.GEO_FONT, y0-tinggi-T.GEO_MARGIN/2), f"{d['a']} cm")
            + garis(x0+masuk, y0-tinggi, x0+masuk, y0, "tinggi", putus=True)
            + siku(x0+masuk, y0) + teks(*T.GEO_LABEL_TINGGI_TRAPESIUM, f"tinggi = {d['t']} cm"))


def _ketupat(d, balik=False):
    if balik:
        w, h = T.GEO_BENTUK_LEBAR * 0.8, T.GEO_BENTUK_TINGGI
    else:
        skala = min(T.GEO_BENTUK_LEBAR/d["d1"], T.GEO_BENTUK_TINGGI/d["d2"])
        w, h = d["d1"]*skala, d["d2"]*skala
    cx, cy = T.GEO_LEBAR/2, T.GEO_BENTUK_ATAS + T.GEO_BENTUK_TINGGI/2
    pts = ((cx, cy-h/2), (cx+w/2, cy), (cx, cy+h/2), (cx-w/2, cy))
    isi = poligon(pts, "ketupat")
    isi += garis(cx-w/2, cy, cx+w/2, cy, "garis-diagonal-diberikan", putus=True)
    isi += garis(cx, cy-h/2, cx, cy+h/2, "garis-diagonal-diberikan", putus=True)
    if balik:
        isi += teks(cx, cy-10, f"{d['d1']} cm") + teks(cx+T.GEO_MARGIN, cy-h/4, "?")
        isi += teks(cx, T.GEO_LABEL_UTAMA_Y, f"L = {d['L']} cm²")
    else:
        isi += teks(*T.GEO_LABEL_DIAGONAL[0], f"d₁ = {d['d1']} cm")
        isi += teks(*T.GEO_LABEL_DIAGONAL[1], f"d₂ = {d['d2']} cm")
    return isi


def _lingkaran(d):
    cx, cy, r = 180, 112, T.GEO_RADIUS
    return (f'<circle class="lingkaran" cx="{cx}" cy="{cy}" r="{r}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
            + garis(cx, cy, cx+r, cy, "jari-jari")
            + teks(cx+r/2, cy-9, f"r = {d['r']} cm"))


def _juring(d):
    cx, cy, r = 180, 120, T.GEO_RADIUS
    sudut = d["s"]
    ex = cx + r * math.sin(math.radians(sudut))
    ey = cy - r * math.cos(math.radians(sudut))
    path = (f'M {cx} {cy} L {cx} {cy-r} A {r} {r} 0 '
            f'{int(sudut > 180)} 1 {angka(ex)} {angka(ey)} Z')
    return (f'<path class="juring" d="{path}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
            + teks(cx, cy+r+22, f"s = {sudut}°; r = {d['r']} cm"))


def _arsiran_pojok(d, ident):
    x, y, r = T.GEO_PERSEGI_X, T.GEO_PERSEGI_Y, T.GEO_PERSEGI_SISI / 2
    # Boundary pusat tersisa: titik tengah sisi dihubungkan empat busur
    # seperempat lingkaran yang berpusat tepat di empat sudut persegi.
    path = (f"M {x+r} {y} A {r} {r} 0 0 0 {x+2*r} {y+r} "
            f"A {r} {r} 0 0 0 {x+r} {y+2*r} "
            f"A {r} {r} 0 0 0 {x} {y+r} "
            f"A {r} {r} 0 0 0 {x+r} {y} Z")
    return (pola_arsir(ident)
            + f'<rect class="persegi-luar" x="{x}" y="{y}" width="{2*r}" height="{2*r}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
            + f'<path class="daerah-arsir-tengah" d="{path}" fill="url(#{ident}-arsir)" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
            + teks(x+r, y+2*r+22, f"sisi = {2*d['r']} cm; r = {d['r']} cm"))


def _jalan(d, ident):
    x, y, sisi = T.GEO_JALAN_X, T.GEO_JALAN_Y, T.GEO_JALAN_SISI
    rasio = d["dalam"] / d["luar"]
    inner = sisi * rasio
    ix = x + (sisi-inner)/2
    iy = y + (sisi-inner)/2
    return (pola_arsir(ident)
            + f'<rect class="jalan-luar" x="{x}" y="{y}" width="{sisi}" height="{sisi}" fill="url(#{ident}-arsir)" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
            + f'<rect class="taman-dalam" x="{angka(ix)}" y="{angka(iy)}" width="{angka(inner)}" height="{angka(inner)}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
            + teks(T.GEO_LEBAR/2, T.GEO_LABEL_JALAN_Y, f"luar {d['luar']} m; dalam {d['dalam']} m", "label-jalan"))


def _kisi(d):
    sel = min(T.GEO_KISI_SEL, 260 / d["p"], 160 / d["l"])
    w, h = d["p"] * sel, d["l"] * sel
    x, y = (T.GEO_LEBAR-w)/2, (T.GEO_TINGGI-h)/2 - T.GEO_FONT
    sel_svg = "".join(
        f'<rect class="sel-kisi" x="{angka(x+i*sel)}" y="{angka(y+j*sel)}" width="{angka(sel)}" height="{angka(sel)}" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS_TIPIS}"/>'
        for j in range(d["l"]) for i in range(d["p"])
    )
    return sel_svg + teks(
        T.GEO_LEBAR/2, y+h+T.GEO_MARGIN, f"Sisi setiap kotak = 1 {d['satuan']}", "legenda-kisi"
    )


def _simetri(d):
    model = d["model"]
    if model == "simetri_persegi":
        bentuk = f'<rect class="bangun-simetri" x="100" y="35" width="160" height="160" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
        posisi = (180, 218)
        ukuran = d["ukuran"]
    elif model == "simetri_persegi_panjang":
        bentuk = f'<rect class="bangun-simetri" x="70" y="55" width="220" height="120" fill="{T.LATAR_KARTU}" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
        posisi = (180, 202)
        ukuran = f"{d['ukuran']} × {d['lebar']}"
    elif model == "simetri_segitiga":
        sisi = min(T.GEO_BENTUK_LEBAR, 2*T.GEO_BENTUK_TINGGI/math.sqrt(3))
        setengah = sisi / 2
        tinggi = sisi * math.sqrt(3) / 2
        dasar_y = T.GEO_SEGITIGA_ALAS_Y
        tengah = T.GEO_LEBAR / 2
        bentuk = poligon(
            ((tengah, dasar_y-tinggi), (tengah+setengah, dasar_y), (tengah-setengah, dasar_y)),
            "bangun-simetri",
        )
        posisi, ukuran = (tengah, T.GEO_LABEL_UTAMA_Y), d["ukuran"]
    else:
        bentuk = poligon(((180, 30), (285, 115), (180, 200), (75, 115)), "bangun-simetri")
        posisi, ukuran = (180, 222), d["ukuran"]
    return bentuk + teks(*posisi, f"{ukuran} {d['satuan']}")


_RENDER = {
    "sudut_pasangan": _sudut_pasangan,
    "sudut_rasio": _sudut_rasio,
    "segitiga_sudut": lambda d: _segitiga(d),
    "segitiga_rasio": lambda d: _segitiga(d, True),
    "segitiga_luar": _segitiga_luar,
    "persegi_panjang": _persegi_panjang,
    "persegi_panjang_balik": lambda d: _persegi_panjang(d, True),
    "segitiga_tinggi": _tinggi,
    "jajargenjang": lambda d: _tinggi(d, True),
    "trapesium": _trapesium,
    "ketupat": _ketupat,
    "ketupat_balik": lambda d: _ketupat(d, True),
    "lingkaran": _lingkaran,
    "juring": _juring,
    "kisi": _kisi,
    "simetri_persegi": _simetri,
    "simetri_segitiga": _simetri,
    "simetri_ketupat": _simetri,
    "simetri_persegi_panjang": _simetri,
}

_JUDUL = {
    "sudut_pasangan": "Pasangan sudut", "sudut_rasio": "Perbandingan sudut",
    "segitiga_sudut": "Sudut segitiga", "segitiga_rasio": "Perbandingan sudut segitiga",
    "segitiga_luar": "Sudut luar segitiga", "persegi_panjang": "Persegi panjang",
    "persegi_panjang_balik": "Persegi panjang", "segitiga_tinggi": "Segitiga dan tingginya",
    "jajargenjang": "Jajargenjang dan tingginya", "trapesium": "Trapesium",
    "ketupat": "Belah ketupat", "ketupat_balik": "Belah ketupat",
    "lingkaran": "Lingkaran", "juring": "Juring lingkaran",
    "arsiran_pojok": "Arsiran di dalam persegi", "jalan": "Jalan mengelilingi taman",
    "kisi": "Kisi persegi satuan", "simetri_persegi": "Persegi",
    "simetri_segitiga": "Segitiga sama sisi", "simetri_ketupat": "Belah ketupat",
    "simetri_persegi_panjang": "Persegi panjang",
}


def render_geometri_datar(data, namespace):
    """Render satu descriptor geometri datar yang telah divalidasi."""
    _validasi(data)
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace wajib teks tidak kosong")
    model = data["model"]
    ident = "geo-" + hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:20]
    if model == "arsiran_pojok":
        badan = _arsiran_pojok(data, ident)
    elif model == "jalan":
        badan = _jalan(data, ident)
    else:
        try:
            badan = _RENDER[model](data)
        except KeyError:
            raise ValueError(f"model geometri tidak dikenal: {model!r}")
    if model != "kisi":
        badan += label_tidak_berskala()
    judul = html.escape(_JUDUL[model])
    desc = html.escape("Diagram geometri dengan label ukuran diketahui dan target bertanda tanya.")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="soal-visual" '
        f'viewBox="0 0 {T.GEO_LEBAR} {T.GEO_TINGGI}" role="img" '
        f'aria-labelledby="{ident}-judul {ident}-desc" '
        f'style="display:block;width:100%;max-width:{T.LEBAR_VISUAL_SOAL};height:auto;margin:{T.JARAK_VISUAL_SOAL} auto">'
        f'<title id="{ident}-judul">{judul}</title><desc id="{ident}-desc">{desc}</desc>{badan}</svg>'
    )


def _ringkasan_sederhana(data):
    m = data["model"]
    if m == "trapesium":
        return f"Fakta visual: sisi sejajar {data['a']} cm dan {data['b']} cm, tinggi {data['t']} cm."
    if m == "ketupat":
        return f"Fakta visual: diagonal belah ketupat {data['d1']} cm dan {data['d2']} cm."
    if m == "persegi_panjang":
        return f"Fakta visual: persegi panjang berukuran {data['p']} cm × {data['l']} cm."
    if m == "lingkaran":
        return f"Fakta visual: jari-jari lingkaran {data['r']} cm."
    if m == "juring":
        return f"Fakta visual: juring bersudut pusat {data['s']} derajat dan berjari-jari {data['r']} cm."
    if m == "arsiran_pojok":
        return f"Fakta visual: persegi bersisi {2*data['r']} cm dengan empat seperempat lingkaran berjari-jari {data['r']} cm."
    if m == "jalan":
        return f"Fakta visual: sisi luar jalan {data['luar']} m dan sisi taman di dalam {data['dalam']} m."
    if m == "kisi":
        return f"Fakta visual: kisi terdiri dari {data['p']} kolom dan {data['l']} baris persegi satuan bersisi 1 {data['satuan']}."
    if m == "simetri_persegi_panjang":
        return f"Fakta visual: persegi panjang berukuran {data['ukuran']} × {data['lebar']} {data['satuan']}."
    return f"Fakta visual: {_JUDUL[m].lower()} memiliki ukuran {data['ukuran']} {data['satuan']}."


def ringkasan_geometri_datar(data):
    """Kembalikan fakta descriptor untuk lampiran, tanpa menghitung target."""
    _validasi(data)
    m = data["model"]
    if m == "persegi_panjang_balik":
        return (f"Fakta visual: persegi panjang memiliki panjang {data['p']} cm, "
                f"keliling {data['K']} cm, dan lebar belum diberi nilai.")
    if m == "ketupat_balik":
        return (f"Fakta visual: luas belah ketupat {data['L']} cm², diagonal pertama "
                f"{data['d1']} cm, dan diagonal kedua belum diberi nilai.")
    if m == "sudut_pasangan":
        return (f"Fakta visual: dua sudut berjumlah {data['total']} derajat; satu sudut "
                f"{data['diketahui']} derajat dan sudut lain belum diberi nilai.")
    if m == "sudut_rasio":
        return f"Fakta visual: dua sudut berpelurus berlabel x dan {data['kali']}x."
    if m == "segitiga_sudut":
        return f"Fakta visual: dua sudut segitiga {data['a']} dan {data['b']} derajat; sudut ketiga belum diberi nilai."
    if m == "segitiga_rasio":
        return f"Fakta visual: sudut segitiga berlabel {data['p']}x, {data['q']}x, dan {data['r']}x."
    if m == "segitiga_luar":
        return f"Fakta visual: sudut dalam tak bersisian {data['a']} dan {data['b']} derajat; sudut luar belum diberi nilai."
    if m in {"segitiga_tinggi", "jajargenjang"}:
        return f"Fakta visual: alas {data['a']} cm, tinggi tegak {data['t']} cm, dan sisi miring {data['s']} cm."
    return _ringkasan_sederhana(data)
