"""Tujuan continuation Pendamping yang aman, bukan pengganti otorisasi resource."""

from __future__ import annotations

import re
from urllib.parse import urlencode


_BATAS_ID = 2**63 - 1
_POLA_SUMBER = re.compile(
    r"/pendamping/konteks/(anak|sesi|soal)/([1-9][0-9]{0,18})(?::([1-9][0-9]{0,18}))?\Z"
)


def tujuan_lanjut(nilai: str) -> str:
    """Terima hanya jalur kanonik; jangan decode, strip, atau perbaiki URL bebas.

    Query/form HTTP sudah didekode satu kali oleh parser pemanggil. ID sumber
    hanya petunjuk navigasi: GET tujuan wajib memeriksa principal dan pemilik.
    """
    if not isinstance(nilai, str):
        return ""
    if nilai == "/pendamping":
        return nilai
    cocok = _POLA_SUMBER.fullmatch(nilai)
    if cocok is None:
        return ""
    jenis, resource_id, nomor = cocok.groups()
    if (jenis == "soal") != (nomor is not None):
        return ""
    if int(resource_id) > _BATAS_ID or (nomor is not None and int(nomor) > _BATAS_ID):
        return ""
    return nilai


def tautan_masuk(tujuan: str) -> str:
    """Bentuk tautan login lokal; tujuan yang ditolak tidak dipantulkan."""
    lanjut = tujuan_lanjut(tujuan)
    return "/masuk?" + urlencode({"lanjut": lanjut}) if lanjut else "/masuk"
