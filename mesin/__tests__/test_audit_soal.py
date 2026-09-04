"""Guard perbaikan audit soal 4 Sep 2026 — 4 temuan.

Semua test di sini menghitung ULANG jawaban dari data mentah, bukan
mempercayai kunci yang dihasilkan template. Itu sebabnya 5468 test lama
tetap hijau padahal kuncinya salah.
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topic_logic as tl  # noqa: E402
import topic_statistics as ts  # noqa: E402

LEVEL = ("P3", "P4", "P5", "P6")
SEED = 300


# ── T2: malrule K & H tidak boleh tertukar di tabel_penalaran ──────────

def test_tabel_penalaran_h_beda_dari_k():
    """h dan k2 pernah menunjuk orang yang SAMA. Karena K didaftarkan
    lebih dulu, K yang selamat dan k2 ditambal "orang lain" — anak yang
    menjawab si tertinggi (salah KONSEP) divonis H "meleset satu posisi"
    dan jalur K-nya mati."""
    for lv in LEVEL:
        for sd in range(SEED):
            par = tl._parameter("tabel_penalaran", random.Random(sd), lv)
            s = tl.tabel_penalaran(**par)
            nilai = [m.jawaban for m in s.malrule]
            assert len(nilai) == len(set(nilai)), (
                f"malrule kembar {lv}/{sd}: {nilai}"
            )
            assert s.kunci not in nilai, (
                f"malrule memakai nilai kunci {lv}/{sd}: {par}"
            )


def test_tabel_penalaran_tanpa_jawaban_hantu():
    """"orang lain" bukan jawaban yang mungkin ditulis anak — malrule
    yang memakainya adalah jalur diagnosis mati."""
    for lv in LEVEL:
        for sd in range(SEED):
            par = tl._parameter("tabel_penalaran", random.Random(sd), lv)
            s = tl.tabel_penalaran(**par)
            for m in s.malrule:
                assert m.jawaban != "orang lain", (
                    f"jalur diagnosis mati di {lv}/{sd}: {par} -> {m.id}"
                )
                assert m.jawaban in par["urutan"], (
                    f"malrule menunjuk nama di luar cerita ({lv}/{sd}): {m.jawaban}"
                )


def test_tabel_penalaran_punya_jalur_k_dan_h():
    for lv in LEVEL:
        for sd in range(SEED):
            par = tl._parameter("tabel_penalaran", random.Random(sd), lv)
            kode = {m.kode for m in tl.tabel_penalaran(**par).malrule}
            assert "K" in kode, f"tanpa jalur K: {lv}/{sd} {par}"
            assert "H" in kode, f"tanpa jalur H: {lv}/{sd} {par}"


# ── T3: alasan malrule harus mengikuti pernyataan yang diacak ──────────

MAKNA_PENGANDAIAN = {
    1: ("pengandaian.mungkin_saja", "K"),
    2: ("pengandaian.negasi", "K"),
    3: ("pengandaian.salah_baca", "B"),
    4: ("pengandaian.ekstrem", "H"),
}


def test_pengandaian_malrule_mengikuti_pernyataan_bukan_huruf():
    """`urutan_tampil` mengacak pernyataan ke huruf A–E. Malrule lama
    sekadar menempelkan alasan 1–4 ke daftar huruf salah berurutan,
    sehingga alasan guru sering menjelaskan pernyataan yang berbeda."""
    opsi = ("A", "B", "C", "D", "E")
    for lv in LEVEL:
        for sd in range(SEED):
            par = tl._parameter(
                "benar_salah_pengandaian", random.Random(sd), lv
            )
            soal = tl.benar_salah_pengandaian(**par)
            per_huruf = {m.jawaban: (m.id, m.kode) for m in soal.malrule}
            for posisi, indeks_pernyataan in enumerate(par["urutan_tampil"]):
                if indeks_pernyataan == 0:
                    assert opsi[posisi] == soal.kunci
                    continue
                assert per_huruf[opsi[posisi]] == MAKNA_PENGANDAIAN[indeks_pernyataan], (
                    f"malrule nyasar {lv}/{sd}: opsi {opsi[posisi]} berisi "
                    f"pernyataan {indeks_pernyataan}, dapat {per_huruf[opsi[posisi]]}"
                )
