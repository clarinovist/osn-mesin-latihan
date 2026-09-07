"""Intervensi manusiawi untuk setiap fokus siklus belajar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import rumus
from learning_visuals import BantuanVisual

KunciFokus = Tuple[str, str, Optional[str]]


@dataclass(frozen=True)
class MateriIntervensi:
    pendekatan_id: str
    instruksi_orang_tua: str
    contoh_terbimbing: str
    strategi_anak: str
    tersedia: bool = True
    bantuan: Optional[BantuanVisual] = None


_STRATEGI = {
    "B": (
        "baca-tandai-ulang",
        "Minta anak menandai informasi penting lalu mengucapkan ulang pertanyaannya.",
        "Baca satu kalimat, lingkari angkanya, lalu sebutkan apa yang dicari.",
        "Tandai informasi penting dan ucapkan ulang yang ditanya.",
    ),
    "H": (
        "tulis-periksa",
        "Minta anak menulis setiap langkah dan memeriksa hitungannya dari belakang.",
        "Kerjakan satu langkah, berhenti, lalu cocokkan operasi dan angkanya.",
        "Tulis langkah satu per satu dan periksa ulang.",
    ),
    "E": (
        "cocokkan-jawaban-akhir",
        "Minta anak membandingkan hasil kerja dengan kotak jawaban sebelum mengirim.",
        "Tunjuk hasil terakhir, lalu salin persis ke kotak jawaban.",
        "Cocokkan hasil kerja dengan jawaban akhir.",
    ),
    "N": (
        "jelaskan-asal-jawaban",
        "Tanyakan ‘dapat dari mana?’ dan dengarkan urutan langkahnya.",
        "Anak menyebutkan satu alasan untuk tiap langkah yang ditulis.",
        "Jelaskan dari mana jawabanmu berasal.",
    ),
    "T": (
        "kenalkan-contoh-awal",
        "Kenalkan ide dasarnya dengan satu contoh sederhana sebelum memberi probe.",
        "Amati satu contoh, tirukan langkahnya, lalu jelaskan kembali.",
        "Pelajari contoh awal, lalu ceritakan kembali caranya.",
    ),
}


def pilihan_untuk_fokus(kunci: KunciFokus) -> tuple[MateriIntervensi, ...]:
    """Daftar pendekatan manusia-reviewed dalam urutan pemakaian."""
    utama = untuk_fokus(kunci)
    if kunci[1] != "K" or not utama.tersedia:
        return (utama,)
    kartu = rumus.kartu_untuk(kunci[0])
    if kartu is None:
        return (utama,)
    alternatif = MateriIntervensi(
        f"jelaskan-balik:{kunci[0]}:{kunci[2] or 'umum'}",
        "Tutup contoh, lalu minta anak menjelaskan kembali hubungan antar langkah "
        "dengan bahasanya sendiri. Buka kembali hanya bila ia tersendat.",
        kartu.contoh,
        "Jelaskan kembali alasan tiap langkah tanpa menyalin contoh.",
    )
    if kunci[0] in ("korek_api", "titik_segitiga") and kartu.bantuan is not None:
        visual = MateriIntervensi(
            f"visual-pola-v1:{kunci[0]}:{kunci[2] or 'umum'}",
            "Amati contoh gambar bersama. Minta anak menunjuk bagian baru "
            "pada setiap gambar dan menjelaskan cara menghitungnya.",
            kartu.contoh,
            "Tunjuk bagian yang bertambah, lalu jelaskan cara menghitung jumlahnya.",
            bantuan=kartu.bantuan,
        )
        return (visual, utama, alternatif)
    return (utama, alternatif)


def untuk_fokus(kunci: KunciFokus) -> MateriIntervensi:
    """Bangun materi aman; K tanpa kartu gagal terlihat, bukan jadi drill generik."""
    template_id, kode, malrule_id = kunci
    if kode == "K":
        kartu = rumus.kartu_untuk(template_id)
        if kartu is None:
            return MateriIntervensi(
                f"konsep:{template_id}:{malrule_id or 'umum'}",
                "Intervensi spesifik belum tersedia. Atur latihan sendiri setelah "
                "memeriksa cara anak; jangan langsung mengulang drill yang sama.",
                "",
                "Ceritakan bagian yang belum kamu pahami.",
                tersedia=False,
            )
        return MateriIntervensi(
            f"konsep:{template_id}:{malrule_id or 'umum'}",
            f"Gunakan benda atau gambar untuk menjelaskan: {kartu.inti}",
            kartu.contoh,
            f"Ingat cara ini: {kartu.inti}",
        )
    try:
        pendekatan, instruksi, contoh, strategi = _STRATEGI[kode]
    except KeyError as exc:
        raise ValueError("kode intervensi tidak dikenal") from exc
    return MateriIntervensi(pendekatan, instruksi, contoh, strategi)
