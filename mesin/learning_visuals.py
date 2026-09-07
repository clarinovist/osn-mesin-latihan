"""Contoh visual belajar tetap, terpisah dari pertanyaan dan jawaban anak."""

from dataclasses import dataclass
import html

import design_tokens as T
from number_patterns_svg import bungkus, gambar_korek, gambar_titik, label, posisi


@dataclass(frozen=True)
class BantuanVisual:
    """Pilih contoh bawaan saja; tidak membawa parameter soal atau markup."""

    jenis: str
    versi: int = 1

    def __post_init__(diri) -> None:
        if type(diri.jenis) is not str or diri.jenis not in ("korek", "titik"):
            raise ValueError("jenis bantuan wajib korek atau titik")
        if type(diri.versi) is not int or diri.versi != 1:
            raise ValueError("versi bantuan wajib bilangan bulat 1")


def _contoh_korek():
    """Empat gambar tetap: awal empat batang, lalu tiga kali menambah tiga."""
    jumlah = (4, 7, 10, 13)
    bentuk = tuple(
        gambar_korek(banyak, jumlah[-1], tebal_dari=jumlah[indeks - 1] if indeks else None)
        for indeks, banyak in enumerate(jumlah)
    )
    uraian = (
        "Contoh pola korek: 4, 7, 10, 13 batang. Setiap ruas antara dua titik "
        "sambungan adalah satu batang. Garis tebal menunjukkan 3 batang baru "
        "pada tiap langkah setelah gambar pertama. Dari gambar 1 ke gambar 4 "
        "ada 3 kali penambahan, bukan 4."
    )
    return bentuk, jumlah, "Contoh pola korek api", uraian, "4 + 3 × 3 = 13 batang."


def _contoh_titik():
    """Baris bertambah panjang, bukan deret dengan beda tetap."""
    bentuk = tuple(gambar_titik(nomor, baris_baru=True) for nomor in range(1, 5))
    uraian = (
        "Contoh pola titik: 1, 3, 6, 10 titik. Titik berbingkai dengan bagian "
        "tengah kosong menandai baris baru. Setiap gambar menambah satu baris "
        "yang lebih panjang: 2, lalu 3, lalu 4 titik. Pertambahannya bukan beda tetap."
    )
    return bentuk, (1, 3, 6, 10), "Contoh pola titik segitiga", uraian, "1 + 2 + 3 + 4 = 10 titik."


def _kelompok(indeks, bentuk, jumlah):
    """Posisikan bentuk dan label pendek dalam kisi token bersama."""
    x, y = posisi(indeks)
    return (
        f'<g data-gambar="{indeks + 1}" transform="translate({x} {y})">'
        + bentuk
        + label(T.POLA_SEL_LEBAR / 2, T.POLA_LABEL_Y, f"Gambar {indeks + 1}: {jumlah}")
        + "</g>"
    )


def render_bantuan(bantuan, *, konteks: str, namespace: str) -> str:
    """Render contoh statis hanya pada permukaan belajar yang diizinkan."""
    if type(bantuan) is not BantuanVisual:
        raise ValueError("objek wajib BantuanVisual")
    if type(konteks) is not str or konteks not in ("hasil_sah", "pelajari_bersama"):
        raise ValueError("konteks bantuan tidak diizinkan")
    sah = BantuanVisual(bantuan.jenis, bantuan.versi)
    bentuk, jumlah, judul, uraian, rumus = (
        _contoh_korek() if sah.jenis == "korek" else _contoh_titik()
    )
    isi = "".join(_kelompok(indeks, satu, jumlah[indeks]) for indeks, satu in enumerate(bentuk))
    gambar = bungkus(isi, judul, uraian, namespace)
    return (
        f'<div class="bantuan-visual" data-bantuan-visual="{sah.jenis}">'
        f'{gambar}<p>{html.escape(uraian)}</p><p>{html.escape(rumus)}</p></div>'
    )
