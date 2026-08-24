"""Template soal pola bilangan — fungsi atas parameter, bukan tabel literal.

Tiap template menghitung TIGA hal dari satu set parameter:

  1. teks soal
  2. kunci jawaban
  3. daftar malrule — jawaban salah yang bisa diprediksi + kode diagnosisnya

Poin (3) yang membuat bank soal ini berbeda dari daftar soal biasa. Karena
malrule ikut dihitung dari parameter, soal dengan angka baru tetap punya
tabel diagnosis yang sahih — tidak perlu ditulis ulang tiap generate.

Sumber malrule: latihan/2026-08-20-p3-pola-bilangan-PENILAIAN.md, yang
disusun dari bentuk soalnya. Sebagian belum diuji ke anak nyata; lihat
bagian "Perkiraan yang belum terverifikasi" di berkas itu.

Kode diagnosis (taksonomi B/K/H/E/T/N, Rencana Produk - Peta Jalan §02):
  B salah baca soal | K salah konsep | H salah hitung
  E salah tulis akhir | T tidak tahu | N menebak
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


@dataclass(frozen=True)
class Malrule:
    """Satu kesalahan yang bisa diprediksi dari bentuk soal."""

    id: str
    jawaban: str
    kode: str
    alasan: str


@dataclass(frozen=True)
class Soal:
    """Hasil render satu template dengan parameter tertentu."""

    template_id: str
    parameter: dict[str, Any]
    teks: str
    kunci: str
    malrule: tuple[Malrule, ...] = ()
    minta_restatement: bool = False
    bagian: str = ""
    tantangan: bool = False

    @property
    def tanda_tangan(self) -> str:
        """Sidik jari untuk mendeteksi soal duplikat di bank."""
        butir = ",".join(f"{k}={self.parameter[k]}" for k in sorted(self.parameter))
        return f"{self.template_id}({butir})"


def _deret(awal: int, beda: int, n: int) -> list[int]:
    return [awal + beda * i for i in range(n)]


def saring_malrule(kunci: str, kandidat: list[Malrule]) -> tuple[Malrule, ...]:
    """Buang malrule yang tidak bisa membedakan benar dari salah.

    Dua penyakit yang disaring di sini, keduanya merusak diagnosis:

    1. **Malrule menebak jawaban yang BENAR.** Terjadi pada kasus tepi —
       mis. siklus dengan sisa 0: "ambil unsur terakhir siklus" kebetulan
       memberi jawaban yang sama dengan kunci. Kalau dibiarkan, anak yang
       menjawab benar tercatat punya miskonsepsi. Ini kerusakan terparah:
       laporan jadi tidak bisa dipercaya.

    2. **Dua malrule menebak jawaban yang sama.** Satu jawaban salah memetakan
       ke dua kode berbeda, dan sistem tidak punya dasar memilih — hasilnya
       tebakan yang menyamar sebagai diagnosis.

    Disaring terpusat, bukan di tiap template, supaya template baru otomatis
    ikut terlindungi tanpa penulisnya perlu ingat aturan ini.
    """
    bersih: list[Malrule] = []
    terpakai: set[str] = {kunci}
    for m in kandidat:
        if m.jawaban in terpakai:
            continue
        terpakai.add(m.jawaban)
        bersih.append(m)
    return tuple(bersih)


# ── Bagian A — lanjutkan polanya ────────────────────────────────────────


def deret_aritmetika(awal: int, beda: int, n_tampil: int, n_minta: int) -> Soal:
    urut = _deret(awal, beda, n_tampil)
    lanjut = _deret(awal + beda * n_tampil, beda, n_minta)
    terakhir = urut[-1]

    tampil = ", ".join(str(x) for x in urut) + ", " + ", ".join(["___"] * n_minta)
    kunci = ", ".join(str(x) for x in lanjut)

    mal = [
        Malrule(
            "aritmetika.beda_dikira_satu",
            ", ".join(str(terakhir + i) for i in range(1, n_minta + 1)),
            "K",
            "pola dikira selalu +1, selisih sebenarnya tidak dibaca",
        ),
        Malrule(
            "aritmetika.selisih_dikira_berubah",
            ", ".join(
                str(terakhir + beda * (i * (i + 1) // 2)) for i in range(1, n_minta + 1)
            ),
            "K",
            "selisih dianggap bertambah tiap langkah, padahal tetap",
        ),
        Malrule(
            "aritmetika.penjumlahan_meleset",
            ", ".join(str(x - 1) for x in lanjut),
            "H",
            "selisih sudah benar, penjumlahannya meleset",
        ),
    ]
    if n_minta > 1:
        mal.append(
            Malrule(
                "aritmetika.hanya_satu_isian_dibaca",
                str(lanjut[0]),
                "B",
                f"ada {n_minta} isian, hanya satu yang dijawab",
            )
        )

    return Soal(
        "deret_aritmetika",
        {"awal": awal, "beda": beda, "n_tampil": n_tampil, "n_minta": n_minta},
        tampil,
        kunci,
        saring_malrule(kunci, mal),
        bagian="A",
    )


def deret_aritmetika_turun(awal: int, beda: int, n_tampil: int) -> Soal:
    urut = _deret(awal, -beda, n_tampil)
    jawab = urut[-1] - beda
    terakhir = urut[-1]

    mal = (
        Malrule(
            "aritmetika_turun.arah_dibalik",
            str(terakhir + beda),
            "K",
            "pola turun dikerjakan seperti pola naik",
        ),
        Malrule(
            "aritmetika_turun.dikira_pembagian",
            str(terakhir // beda) if terakhir % beda == 0 else str(beda),
            "K",
            "selisih tetap dikira operasi pembagian",
        ),
        Malrule(
            "aritmetika_turun.pengurangan_meleset",
            str(jawab - 2),
            "H",
            "arah sudah benar, pengurangannya meleset",
        ),
    )

    return Soal(
        "deret_aritmetika_turun",
        {"awal": awal, "beda": beda, "n_tampil": n_tampil},
        ", ".join(str(x) for x in urut) + ", ___",
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        bagian="A",
    )


def deret_geometri(awal: int, rasio: int, n_tampil: int) -> Soal:
    urut = [awal * rasio**i for i in range(n_tampil)]
    jawab = urut[-1] * rasio
    terakhir, sebelum = urut[-1], urut[-2]

    mal = (
        Malrule(
            "geometri.pola_tambah_dipaksakan",
            str(terakhir + (terakhir - sebelum)),
            "K",
            "pola perkalian dikerjakan sebagai pola penjumlahan — "
            "selisih terakhir ditambahkan lagi",
        ),
        Malrule(
            "geometri.perkalian_meleset",
            str(jawab - 2),
            "H",
            "sudah tahu dikali, perkaliannya meleset",
        ),
    )

    return Soal(
        "deret_geometri",
        {"awal": awal, "rasio": rasio, "n_tampil": n_tampil},
        ", ".join(str(x) for x in urut) + ", ___",
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        bagian="A",
    )


def deret_bertingkat(awal: int, beda_awal: int, kenaikan: int, n_tampil: int) -> Soal:
    urut = [awal]
    beda = beda_awal
    selisih: list[int] = []
    for _ in range(n_tampil - 1):
        selisih.append(beda)
        urut.append(urut[-1] + beda)
        beda += kenaikan

    jawab = urut[-1] + beda
    terakhir = urut[-1]
    selisih_terakhir = selisih[-1]

    mal = (
        Malrule(
            "bertingkat.selisih_terakhir_diulang",
            str(terakhir + selisih_terakhir),
            "K",
            "selisih terakhir dipakai lagi — belum melihat selisihnya sendiri berpola",
        ),
        Malrule(
            "bertingkat.selisih_dikira_tetap",
            str(terakhir + selisih_terakhir - kenaikan),
            "K",
            "selisih dianggap tetap, kenaikannya tidak terbaca",
        ),
        Malrule(
            "bertingkat.penjumlahan_meleset",
            str(jawab - 1),
            "H",
            "baris selisih sudah benar, penjumlahan akhirnya meleset",
        ),
    )

    return Soal(
        "deret_bertingkat",
        {
            "awal": awal,
            "beda_awal": beda_awal,
            "kenaikan": kenaikan,
            "n_tampil": n_tampil,
        },
        ", ".join(str(x) for x in urut) + ", ___",
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        bagian="A",
    )


# ── Bagian B — pola berulang ────────────────────────────────────────────


def _siklus(pola: list[str], posisi: int) -> str:
    return pola[(posisi - 1) % len(pola)]


def siklus_huruf(pola: tuple[str, ...], posisi: int) -> Soal:
    n = len(pola)
    jawab = _siklus(list(pola), posisi)
    sisa = posisi % n

    mal = [
        Malrule(
            "siklus.panjang_siklus_salah",
            _siklus(list(pola), posisi if n <= 2 else ((posisi - 1) % (n - 1)) + 1),
            "K",
            f"siklus dihitung {n - 1} unsur, bukan {n}",
        ),
        Malrule(
            "siklus.ambil_akhir_siklus",
            pola[-1],
            "K",
            "sisa pembagian diabaikan, langsung ambil unsur terakhir siklus",
        ),
    ]
    if sisa == 0:
        mal.insert(
            0,
            Malrule(
                "siklus.off_by_one_sisa_nol",
                pola[0],
                "K",
                "sisa 0 dikira menunjuk posisi ke-1, padahal posisi terakhir siklus",
            ),
        )

    teks = (
        "Huruf disusun berulang seperti ini:\n\n"
        f"    {'  '.join(''.join(pola) for _ in range(3))}  ...\n\n"
        f"Huruf ke-{posisi} adalah huruf apa?"
    )

    return Soal(
        "siklus_huruf",
        {"pola": "".join(pola), "posisi": posisi},
        teks,
        jawab,
        saring_malrule(jawab, mal),
        minta_restatement=True,
        bagian="B",
    )


def siklus_warna(pola: tuple[str, ...], posisi: int) -> Soal:
    n = len(pola)
    jawab = _siklus(list(pola), posisi)
    sisa = posisi % n

    mal = [
        Malrule(
            "siklus.ambil_akhir_siklus",
            pola[-1],
            "K",
            "sisa pembagian diabaikan, langsung ambil unsur terakhir siklus",
        ),
        Malrule(
            "siklus.sisa_meleset",
            _siklus(list(pola), posisi + 1),
            "H",
            "cara pembagian benar, sisanya salah hitung",
        ),
    ]
    if sisa == 0:
        mal.insert(
            0,
            Malrule(
                "siklus.off_by_one_sisa_nol",
                pola[0],
                "K",
                "sisa 0 dikira menunjuk posisi ke-1",
            ),
        )

    rangkai = ", ".join(pola)
    teks = (
        "Manik-manik dironce berulang:\n\n"
        f"    {rangkai},\n    {rangkai}, ...\n\n"
        f"Manik ke-{posisi} warnanya apa?"
    )

    return Soal(
        "siklus_warna",
        {"pola": ",".join(pola), "posisi": posisi},
        teks,
        jawab,
        saring_malrule(jawab, mal),
        bagian="B",
    )


# ── Bagian C — pola gambar ──────────────────────────────────────────────


def korek_api(awal: int, tambah: int, gambar_ke: int) -> Soal:
    jawab = awal + tambah * (gambar_ke - 1)

    mal = (
        Malrule(
            "korek.tidak_sadar_batang_bersama",
            str(awal * gambar_ke),
            "K",
            "tiap bangun dihitung utuh — belum sadar batang dipakai bersama",
        ),
        Malrule(
            "korek.off_by_one",
            str(awal + tambah * gambar_ke),
            "K",
            "penambahan dihitung sebanyak nomor gambar, seharusnya nomor dikurangi satu",
        ),
        Malrule(
            "korek.perkalian_meleset",
            str(jawab - 2),
            "H",
            "rumusnya benar, hitungannya meleset",
        ),
    )

    contoh = ", ".join(f"{awal + tambah * i}" for i in range(3))
    teks = (
        "Segitiga dibuat dari batang korek api.\n"
        "Segitiga yang bersebelahan memakai batang bersama.\n\n"
        f"    Gambar 1, 2, 3 butuh: {contoh} batang\n\n"
        f"Gambar ke-{gambar_ke} butuh berapa batang?"
    )

    return Soal(
        "korek_api",
        {"awal": awal, "tambah": tambah, "gambar_ke": gambar_ke},
        teks,
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        minta_restatement=True,
        bagian="C",
    )


def titik_segitiga(gambar_ke: int) -> Soal:
    def segitiga(n: int) -> int:
        return n * (n + 1) // 2

    jawab = segitiga(gambar_ke)
    tampil = [segitiga(i) for i in range(1, 5)]

    mal = (
        Malrule(
            "titik.berhenti_satu_gambar_lebih_awal",
            str(segitiga(gambar_ke - 1)),
            "B",
            "polanya benar sampai akhir, tapi berhenti di gambar sebelumnya",
        ),
        Malrule(
            "titik.selisih_dikira_tetap",
            str(tampil[-1] + 4 * (gambar_ke - 4)),
            "K",
            "selisih dianggap tetap, padahal bertambah satu tiap gambar",
        ),
        Malrule(
            "titik.penjumlahan_beruntun_meleset",
            str(jawab - 1),
            "H",
            "cara bertingkat benar, penjumlahan beruntunnya meleset",
        ),
    )

    teks = (
        "Titik disusun jadi segitiga.\n\n"
        f"    Gambar 1, 2, 3, 4 punya: {', '.join(str(x) for x in tampil)} titik\n\n"
        f"Gambar ke-{gambar_ke} punya berapa titik?"
    )

    return Soal(
        "titik_segitiga",
        {"gambar_ke": gambar_ke},
        teks,
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        minta_restatement=True,
        bagian="C",
    )


# ── Bagian D — pola dibalik (paling penting) ────────────────────────────


def deret_terbalik_aritmetika(awal: int, beda: int, posisi_target: int) -> Soal:
    target = awal + beda * (posisi_target - 1)
    urut = _deret(awal, beda, 5)

    mal = (
        Malrule(
            "terbalik.jawab_nilainya",
            str(target),
            "B",
            "yang diminta nomor urutnya, yang dijawab nilainya — "
            "polanya paham, pertanyaannya belum",
        ),
        Malrule(
            "terbalik.lupa_tambah_satu",
            str(posisi_target - 1),
            "K",
            "selisih dibagi dengan benar, lupa menambah satu untuk suku pertama",
        ),
        Malrule(
            "terbalik.hitung_deret_meleset",
            str(posisi_target + 1),
            "H",
            "menulis deretnya, salah hitung di tengah",
        ),
    )

    teks = (
        f"Pola: {', '.join(str(x) for x in urut)}, ...\n\n"
        f"Bilangan {target} ada di urutan ke berapa?"
    )

    return Soal(
        "deret_terbalik_aritmetika",
        {"awal": awal, "beda": beda, "posisi_target": posisi_target},
        teks,
        str(posisi_target),
        saring_malrule(str(posisi_target), list(mal)),
        minta_restatement=True,
        bagian="D",
    )


def deret_terbalik_geometri(awal: int, rasio: int, posisi_target: int) -> Soal:
    target = awal * rasio ** (posisi_target - 1)
    urut = [awal * rasio**i for i in range(4)]

    mal = (
        Malrule(
            "terbalik.jawab_nilainya",
            str(target),
            "B",
            "yang diminta nomor urutnya, yang dijawab nilainya",
        ),
        Malrule(
            "terbalik.dikira_kelipatan",
            str(target // awal),
            "K",
            f"dikira pola kelipatan {awal}, padahal pola perkalian berulang",
        ),
        Malrule(
            "terbalik.berhenti_satu_langkah_awal",
            str(posisi_target - 1),
            "H",
            "berhenti satu suku sebelum target saat menghitung urutan",
        ),
    )

    teks = (
        f"Pola: {', '.join(str(x) for x in urut)}, ...\n\n"
        f"Bilangan {target} ada di urutan ke berapa?"
    )

    return Soal(
        "deret_terbalik_geometri",
        {"awal": awal, "rasio": rasio, "posisi_target": posisi_target},
        teks,
        str(posisi_target),
        saring_malrule(str(posisi_target), list(mal)),
        minta_restatement=True,
        bagian="D",
    )


# ── Bagian E — pola dalam cerita ────────────────────────────────────────


def siklus_hari(hari_awal: str, tambah: int) -> Soal:
    mulai = HARI.index(hari_awal)
    jawab = HARI[(mulai + tambah) % 7]

    mal = (
        Malrule(
            "hari.sisa_diabaikan",
            hari_awal,
            "K",
            f"{tambah} dikira kelipatan 7 — sisa pembagiannya tidak dihitung",
        ),
        Malrule(
            "hari.off_by_one",
            HARI[(mulai + tambah - 1) % 7],
            "K",
            "sisa dihitung mulai dari hari ini, seharusnya dari besok",
        ),
        Malrule(
            "hari.pembagian_meleset",
            HARI[(mulai + tambah + 1) % 7],
            "H",
            "cara siklusnya benar, pembagian tujuh-nya meleset",
        ),
    )

    teks = f"Hari ini hari {hari_awal}.\n{tambah} hari lagi hari apa?"

    return Soal(
        "siklus_hari",
        {"hari_awal": hari_awal, "tambah": tambah},
        teks,
        jawab,
        saring_malrule(jawab, list(mal)),
        minta_restatement=True,
        bagian="E",
    )


def jumlah_siklus(pola: tuple[int, ...], n_angka: int) -> Soal:
    n = len(pola)
    penuh, sisa = divmod(n_angka, n)
    jawab = penuh * sum(pola) + sum(pola[:sisa])

    mal = (
        Malrule(
            "jumlah_siklus.sisa_tidak_dihitung",
            str(penuh * sum(pola)),
            "K",
            f"{sisa} angka sisa di ujung tidak ikut dijumlahkan",
        ),
        Malrule(
            "jumlah_siklus.dikira_mencacah",
            str(n_angka),
            "B",
            "dikira menghitung banyaknya angka, bukan jumlah nilainya",
        ),
        Malrule(
            "jumlah_siklus.pembagian_meleset",
            str((penuh + 1) * sum(pola)),
            "H",
            "cara siklusnya benar, banyak siklusnya salah hitung",
        ),
    )

    ulang = ", ".join(str(x) for x in pola)
    teks = (
        "Angka ditulis berulang:\n\n"
        f"    {ulang}, {ulang}, {ulang}, ...\n\n"
        f"Berapa JUMLAH {n_angka} angka pertama?"
    )

    return Soal(
        "jumlah_siklus",
        {"pola": ",".join(str(x) for x in pola), "n_angka": n_angka},
        teks,
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        minta_restatement=True,
        bagian="E",
        tantangan=True,
    )


# ── Registri ────────────────────────────────────────────────────────────

REGISTRI: dict[str, Callable[..., Soal]] = {
    "deret_aritmetika": deret_aritmetika,
    "deret_aritmetika_turun": deret_aritmetika_turun,
    "deret_geometri": deret_geometri,
    "deret_bertingkat": deret_bertingkat,
    "siklus_huruf": siklus_huruf,
    "siklus_warna": siklus_warna,
    "korek_api": korek_api,
    "titik_segitiga": titik_segitiga,
    "deret_terbalik_aritmetika": deret_terbalik_aritmetika,
    "deret_terbalik_geometri": deret_terbalik_geometri,
    "siklus_hari": siklus_hari,
    "jumlah_siklus": jumlah_siklus,
}

# Urutan tetap satu lembar: mudah -> sulit, tantangan di akhir.
URUTAN_LEMBAR: tuple[str, ...] = (
    "deret_aritmetika",
    "deret_aritmetika_turun",
    "deret_geometri",
    "deret_bertingkat",
    "siklus_huruf",
    "siklus_warna",
    "korek_api",
    "titik_segitiga",
    "deret_terbalik_aritmetika",
    "deret_terbalik_geometri",
    "siklus_hari",
    "jumlah_siklus",
)
