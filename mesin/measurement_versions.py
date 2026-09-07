"""Versi pengukuran eksak tanpa mengubah rekonstruksi soal warisan."""
from __future__ import annotations

import inspect
from dataclasses import replace
from functools import wraps

from templates import Malrule


_PEMBAGI = {
    "menit_ke_jam": ("menit", 60),
    "detik_ke_menit": ("detik", 60),
    "detik_ke_jam": ("detik", 3600),
}
_VARIAN_WAKTU = frozenset({
    "jam_ke_menit", "menit_ke_jam", "menit_ke_detik", "detik_ke_menit",
    "jam_ke_detik", "detik_ke_jam", "durasi_ke_menit", "durasi_ke_detik",
})


def _validasi(nama, parameter):
    varian = parameter["varian"]
    sah = ({"cari_skala", "cari_peta", "cari_sebenarnya"}
           if nama == "skala_peta" else _VARIAN_WAKTU)
    if not isinstance(varian, str) or varian not in sah:
        raise ValueError("varian pengukuran tidak didukung")
    for kunci, nilai in parameter.items():
        if kunci != "varian" and (type(nilai) is not int or not 0 <= nilai <= 10**9):
            raise ValueError("parameter pengukuran wajib bilangan bulat tidak negatif")
    if nama == "skala_peta":
        if (min(parameter[k] for k in ("peta", "skala", "sebenarnya")) <= 0
                or parameter["peta"] * parameter["skala"] != parameter["sebenarnya"] * 100000):
            raise ValueError("relasi skala peta tidak konsisten")
    elif varian in _PEMBAGI:
        satuan, pembagi = _PEMBAGI[varian]
        if parameter[satuan] % pembagi:
            raise ValueError("konversi versi 2 wajib habis dibagi, bukan dipotong")


def _malrule_utuh(soal):
    """Pertahankan kandidat K; H yang bertabrakan digeser sampai unik."""
    if any(m.kode == "H" for m in soal.malrule):
        return soal.malrule
    terpakai = {soal.kunci, *(m.jawaban for m in soal.malrule)}
    awalan = "1:" if soal.kunci.startswith("1:") else ""
    angka = soal.kunci.split(":")[-1]
    h = int(angka) - 1
    while awalan + str(h) in terpakai:
        h += 1
    if soal.template_id == "skala_peta":
        ident = {"cari_skala": "skala.kurang_satu", "cari_peta": "skala.peta_kurang_satu",
                 "cari_sebenarnya": "skala.sebenarnya_kurang_satu"}[soal.parameter["varian"]]
    else:
        ident = "jam.kurang_satu"
    return (*soal.malrule, Malrule(ident, awalan + str(h), "H",
                                 "cara pengukuran benar, hasil hitung meleset"))


def soal_berversi(fungsi):
    """Parameter tanpa versi tetap memakai perilaku historis persis."""
    bentuk = inspect.signature(fungsi)

    @wraps(fungsi)
    def panggil(*args, versi=1, **kwargs):
        if type(versi) is not int or versi not in (1, 2):
            raise ValueError("versi pengukuran tidak didukung")
        if versi == 1:
            return fungsi(*args, **kwargs)
        parameter = dict(bentuk.bind(*args, **kwargs).arguments)
        _validasi(fungsi.__name__, parameter)
        soal = fungsi(**parameter)
        pembahasan = soal.pembahasan
        if soal.template_id == "skala_peta":
            peta, skala, sebenarnya = (parameter[k] for k in ("peta", "skala", "sebenarnya"))
            pembahasan = (
                "Skala 1 : n berarti 1 cm di peta = n cm sebenarnya. "
                f"Jarak peta {peta} cm, skala 1:{skala}, jarak sebenarnya {sebenarnya} km. "
                f"Dalam cm: {peta} × {skala} = {sebenarnya * 100000}; "
                "ubah cm ke km dengan membagi 100.000. "
                f"Jawaban yang diminta: {soal.kunci}."
            )
        return replace(soal, parameter={**soal.parameter, "versi": 2},
                       pembahasan=pembahasan, malrule=_malrule_utuh(soal))
    return panggil


def parameter_baru(fungsi):
    """Buat input bilangan bulat yang konsisten, bukan membulatkan jawaban."""
    @wraps(fungsi)
    def parameter(template_id, rng, level):
        lama = fungsi(template_id, rng, level)
        if template_id == "skala_peta":
            peta = lama["peta"]
            while peta * lama["skala"] % 100000:
                peta += 1
            return {**lama, "peta": peta, "sebenarnya": peta * lama["skala"] // 100000, "versi": 2}
        if template_id != "jam_menit_detik":
            return lama
        varian = lama["varian"]
        if varian in _PEMBAGI:
            satuan, pembagi = _PEMBAGI[varian]
            hasil = rng.randint(1, 60 if varian == "detik_ke_menit" else 23)
            return {**lama, satuan: hasil * pembagi, "versi": 2}
        return {**lama, "versi": 2}
    return parameter
