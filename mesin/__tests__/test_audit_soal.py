"""Guard perbaikan audit soal 4 Sep 2026 — 4 temuan.

Semua test di sini menghitung ULANG jawaban dari data mentah, bukan
mempercayai kunci yang dihasilkan template. Itu sebabnya 5468 test lama
tetap hijau padahal kuncinya salah.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topic_logic as tl  # noqa: E402
import topic_statistics as ts  # noqa: E402
from diagnosis import setara  # noqa: E402

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


# ── T4: benda pada varian bekal harus benar-benar makanan ──────────────

MAKANAN_BEKAL = {"roti", "nasi", "buah", "telur", "sandwich"}


def test_pengandaian_bekal_memakai_makanan_bukan_perlengkapan():
    """Semua barang lama (pensil, buku, tas, sepatu, topi) menghasilkan
    frasa mustahil seperti 'membawa bekal tas'."""
    jumlah_bekal = 0
    for lv in LEVEL:
        for sd in range(SEED):
            par = tl._parameter(
                "benar_salah_pengandaian", random.Random(sd), lv
            )
            if par["varian"] != "bekal":
                continue
            jumlah_bekal += 1
            assert par["barang"] in MAKANAN_BEKAL, (
                f"bukan makanan {lv}/{sd}: {par['barang']}"
            )
            soal = tl.benar_salah_pengandaian(**par)
            assert f"bekal {par['barang']}" in soal.teks
    assert jumlah_bekal > 0, "audit tidak pernah menyentuh varian bekal"


# ── T1: median genap boleh desimal, tidak boleh dibulatkan // ──────────

def _format_setengah(dua_kali_nilai: int) -> str:
    """Format nilai /2 dengan koma desimal, secara eksak tanpa float."""
    if dua_kali_nilai % 2 == 0:
        return str(dua_kali_nilai // 2)
    return f"{dua_kali_nilai // 2},5"


def test_median_genap_desimal_kunci_dan_pembahasan_benar():
    """Regresi nyata: [1,7,15,16,19,27] punya median 15,5, bukan 15.

    Kunci dihitung ulang dari data mentah. Malrule juga harus memakai
    format koma yang sama supaya diagnosis jawaban salah tidak runtuh.
    """
    kasus_desimal = 0
    for lv in ("P4", "P5", "P6"):
        for sd in range(1000):
            par = ts._parameter("median_modus", random.Random(sd), lv)
            if par["varian"] != "median" or len(par["data"]) % 2:
                continue
            data = par["data"]
            urut = sorted(data)
            dua_tengah = urut[len(urut) // 2 - 1] + urut[len(urut) // 2]
            seharusnya = _format_setengah(dua_tengah)
            soal = ts.median_modus(**par)
            assert soal.kunci == seharusnya, (
                f"median dibulatkan {lv}/{sd}: {data}; "
                f"dapat {soal.kunci}, seharusnya {seharusnya}"
            )
            assert seharusnya in soal.pembahasan
            if ",5" in seharusnya:
                kasus_desimal += 1
                for malrule in soal.malrule:
                    # Semua jawaban numerik memakai format Indonesia;
                    # titik desimal tidak boleh tercampur dengan koma kunci.
                    assert ".5" not in malrule.jawaban
    assert kasus_desimal > 0, "audit tidak pernah menyentuh median desimal"


def test_median_contoh_regresi_15_koma_5():
    soal = ts.median_modus("median", [16, 19, 1, 7, 15, 27])
    assert soal.kunci == "15,5"
    assert "15,5" in soal.pembahasan
    assert setara(soal.kunci, "15.5"), "anak boleh mengetik titik desimal"
