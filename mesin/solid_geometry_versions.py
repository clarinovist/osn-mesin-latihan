"""Versi matematika baru tanpa menulis ulang soal ruang historis."""
from __future__ import annotations

import inspect
from functools import wraps
from typing import Callable

from templates import Soal
from solid_geometry_numbers import (
    angka_json, bulat, desimal, malrule_angka, pecahan, pi_untuk,
)


def soal_berversi(fungsi: Callable[..., Soal]) -> Callable[..., Soal]:
    """Tanpa versi tetap fungsi lama, versi2 memakai fakta eksak."""
    signature = inspect.signature(fungsi)
    bawaan = {n: p.default for n, p in signature.parameters.items()
              if p.default is not inspect.Parameter.empty}

    @wraps(fungsi)
    def panggil(*args, versi=1, **kwargs):
        if type(versi) is not int or versi not in (1, 2):
            raise ValueError('versi soal geometri tidak didukung')
        if versi == 1:
            return fungsi(*args, **kwargs)
        parameter = {**bawaan, **signature.bind(*args, **kwargs).arguments}
        if fungsi.__name__ == 'jaring_jaring':
            from solid_geometry_nets import buat_jaring_v2
            return buat_jaring_v2(**parameter)
        if fungsi.__name__ == 'perbandingan_volume':
            return _perbandingan(parameter)
        return _tabung(fungsi.__name__, parameter)

    return panggil


def parameter_baru(fungsi):
    """Generator baru beridentitas baru; RNG dan jalur lain tetap."""
    @wraps(fungsi)
    def parameter(template_id, rng, level):
        if template_id == 'jaring_jaring':
            from solid_geometry_nets import parameter_jaring_v2
            return parameter_jaring_v2(rng)
        lama = fungsi(template_id, rng, level)
        if template_id == 'perbandingan_volume':
            faktor = lama['k'] ** 3
            v_baru = faktor if lama['varian'] == 'cari_k' else faktor * lama['s']
            return {**lama, 'V_baru': v_baru, 'versi': 2}
        if template_id not in ('volume_prisma_tabung', 'luas_permukaan'):
            return lama
        if not lama['varian'].startswith('tabung'):
            return lama
        r, t = lama['r'], lama['t']
        nilai = (pi_untuk(r) * r * r * t if template_id == 'volume_prisma_tabung'
                 else 2 * pi_untuk(r) * r * (r + t))
        nama = 'V' if template_id == 'volume_prisma_tabung' else 'LP'
        return {**lama, nama: angka_json(nilai), 'versi': 2}
    return parameter


def _tabung(tid, p):
    varian = p['varian']
    volume = tid == 'volume_prisma_tabung'
    maju, balik = (('tabung_V', 'tabung_balik') if volume
                    else ('tabung_LP', 'tabung_cari_t'))
    if varian not in (maju, balik):
        raise ValueError('varian versi2 bukan tabung yang didukung')
    r = bulat(p['r'], 'jari-jari')
    pi = pi_untuk(r)
    nama, satuan = ('V', 'cm³') if volume else ('LP', 'cm²')
    besaran = 'Volume' if volume else 'Luas permukaan'
    label_pi = '22/7' if r % 7 == 0 else '3,14'
    if varian == maju:
        t = bulat(p['t'], 'tinggi')
        nilai = pi*r*r*t if volume else 2*pi*r*(r+t)
        data = {'varian': varian, 'r': r, 't': t, nama: angka_json(nilai), 'versi': 2}
        teks = (f'Tabung dengan jari-jari {r} cm dan tinggi {t} cm '
                f'(π = {label_pi}). Berapa {besaran.lower()}nya ({satuan})?')
        hitung = (f'{label_pi} × {r} × {r} × {t}' if volume
                  else f'2 × {label_pi} × {r} × ({r} + {t})')
        salah = (2*pi*r*t, pi*r*r) if volume else (pi*r*r+2*pi*r*t, pi*r*r*t)
    else:
        total = pecahan(p[nama], nama)
        nilai = total/(pi*r*r) if volume else total/(2*pi*r)-r
        if nilai.denominator != 1:
            raise ValueError('tinggi versi2 wajib bilangan bulat sesuai parameter soal')
        t = bulat(nilai.numerator, 'tinggi')
        if type(p['t']) is not int or p['t'] not in (0, t):
            raise ValueError('tinggi tersimpan tidak sesuai fakta soal')
        data = {'varian': varian, 'r': r, nama: angka_json(total), 'versi': 2}
        teks = (f'{besaran} tabung {desimal(total)} {satuan}, jari-jari {r} cm '
                f'(π = {label_pi}). Berapa tingginya (cm)?')
        hitung = (f'{desimal(total)} ÷ ({label_pi} × {r} × {r})' if volume
                  else f'{desimal(total)} ÷ (2 × {label_pi} × {r}) − {r}')
        salah = (total/(2*pi*r), total/r) if volume else (total/(2*pi*r), total/(pi*r*r))
    return _soal_tabung(tid, data, teks, nilai, salah, hitung, volume)


def _soal_tabung(tid, data, teks, nilai, salah, hitung, volume):
    kunci = desimal(nilai)
    awalan = 'volprisma' if volume else 'lp'
    ids = (('volprisma.lupa_setengah_tabung', 'volprisma.rumus_lain_tabung') if volume
           else ('lp.tabung.lupa', 'lp.tabung.rumus_lain'))
    # Malrule yang menghasilkan pecahan berulang memakai pembulatan turun,
    # sebagaimana kesalahan pembagian bulat; jawaban benar tidak dibulatkan.
    kandidat = tuple((ident, jawaban if (jawaban*10000).denominator == 1
                     else jawaban.numerator // jawaban.denominator,
                     alasan) for ident, jawaban, alasan in zip(
                         ids, salah, ('memakai rumus tabung yang tidak tepat',
                                     'menghilangkan satu faktor pada rumus')))
    mal = malrule_angka(kunci, kandidat, f'{awalan}.kurang_satu' if volume else 'lp.kurang_satu')
    return Soal(tid, data, teks, kunci, mal, minta_restatement=True,
                bagian='A' if volume else 'B',
                pembahasan=f'Gunakan ukuran pada soal. Hitung {hitung} = {kunci}.')


def _perbandingan(p):
    varian = p['varian']
    k = bulat(p['k'], 'faktor panjang', 2, 100)
    s = bulat(p['s'], 'ukuran awal', 0)
    bulat(p['V'], 'volume awal', 0, 10**9)
    bulat(p['V_baru'], 'volume atau faktor akhir', 0, 10**9)
    if varian == 'cari_k':
        faktor = bulat(p['V_baru'], 'faktor volume', 8, 100**3)
        if k**3 != faktor:
            raise ValueError('faktor panjang tidak sesuai faktor volume')
        kunci = str(k)
        teks = f'Volume kubus diperbesar {faktor} kali. Berapa kali panjang rusuknya diperbesar?'
        salah = (faktor // 3, faktor)
        langkah = f'{k} × {k} × {k} = {faktor}, jadi rusuk diperbesar {k} kali.'
    elif varian in ('cari_V_baru', 'balok_V_baru'):
        bulat(s, 'ukuran awal')
        nilai = k**3 * (s if varian == 'balok_V_baru' else 1)
        kunci = str(nilai)
        teks = (f'Kubus dengan panjang rusuk {s} cm. Jika panjang rusuk diperbesar {k} kali, '
                'berapa kali lipat volumenya?' if varian == 'cari_V_baru' else
                f'Balok diperbesar {k} kali pada setiap ukurannya. Volume awal {s} cm³. '
                'Berapa volume barunya (cm³)?')
        pengali = s if varian == 'balok_V_baru' else 1
        salah = (k*pengali, k*k*pengali)
        langkah = f'Faktor volume = {k} × {k} × {k} = {k**3}.'
        if varian == 'balok_V_baru':
            langkah += f' Volume baru = {s} × {k**3} = {nilai} cm³.'
    else:
        raise ValueError('varian perbandingan volume tidak didukung')
    data = {**p, 'versi': 2}
    mal = malrule_angka(kunci, (
        ('perbandingan.kali', salah[0], 'menggunakan faktor panjang langsung untuk volume'),
        ('perbandingan.kuadrat', salah[1], 'menggunakan faktor yang tidak sesuai tiga dimensi'),
    ), 'perbandingan.kurang_satu')
    return Soal('perbandingan_volume', data, teks, kunci, mal,
                minta_restatement=True, bagian='C', pembahasan=langkah)
