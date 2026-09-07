"""Validasi allow-list fakta pertanyaan pengukuran dan lintasan."""
from __future__ import annotations

from collections.abc import Mapping


FIELD_WAKTU = {
    "cari_mulai": frozenset({"varian", "selesai", "durasi"}),
    "cari_selesai": frozenset({"varian", "mulai", "durasi"}),
    "cari_durasi": frozenset({"varian", "mulai", "selesai"}),
}


def field_tepat(data, field):
    """Tolak field tambahan, termasuk hasil hitung terselubung."""
    if not isinstance(data, Mapping) or set(data) != set(field):
        raise ValueError("field visual tidak sesuai allow-list")


def bulat(nilai, nama, bawah, atas):
    if type(nilai) is not int or not bawah <= nilai <= atas:
        raise ValueError(f"{nama} di luar rentang bilangan bulat yang didukung")
    return nilai


def validasi_petak(data):
    field_tepat(data, {"b", "k"})
    b = bulat(data["b"], "baris", 1, 24)
    k = bulat(data["k"], "kolom", 1, 24)
    if b + k > 25:
        raise ValueError("jumlah baris dan kolom melebihi batas")


def validasi_waktu(data):
    if not isinstance(data, Mapping):
        raise ValueError("data waktu wajib mapping")
    varian = data.get("varian")
    if not isinstance(varian, str) or varian not in FIELD_WAKTU:
        raise ValueError("varian waktu tidak didukung")
    field_tepat(data, FIELD_WAKTU[varian])
    if "mulai" in data:
        bulat(data["mulai"], "mulai", 0, 1439)
    if "selesai" in data:
        bulat(data["selesai"], "selesai", 1, 2878)
    if "durasi" in data:
        bulat(data["durasi"], "durasi", 1, 1439)
    if varian == "cari_mulai" and not 0 <= data["selesai"] - data["durasi"] < 1440:
        raise ValueError("fakta waktu mulai tidak konsisten")
    if varian == "cari_durasi" and not 0 < data["selesai"] - data["mulai"] < 1440:
        raise ValueError("fakta durasi tidak konsisten")
