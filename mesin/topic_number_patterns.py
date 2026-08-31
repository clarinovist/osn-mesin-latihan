"""Paket topik POLA BILANGAN — seluruh konten topik ini di satu berkas.

Bagian dari Fase A (registry topik): template, komposisi lembar per level,
profil batas angka, judul bagian, dan renderer diagram milik topik ini
dipindahkan utuh dari templates.py/generator.py/render.py. Kode di sini
DIPINDAHKAN, bukan diubah — identitas perilakunya dikunci oleh
__tests__/test_identitas_refactor.py.

Kode diagnosis (taksonomi B/K/H/E/T/N, Rencana Produk - Peta Jalan §02):
  B salah baca soal | K salah konsep | H salah hitung
  E salah tulis akhir | T tidak tahu | N menebak

Sumber malrule: latihan/2026-08-20-p3-pola-bilangan-PENILAIAN.md.
"""

from __future__ import annotations

import html
from typing import Any, Callable

from templates import HARI, Malrule, Soal, _deret, saring_malrule
from topics import Topik, daftarkan


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


def siklus_huruf(pola: list[str] | tuple[str, ...], posisi: int) -> Soal:
    """`pola` menerima list atau tuple: list adalah bentuk JSON yang
    tersimpan di bank soal, tuple bentuk dari generator. Restorasi bank
    tidak boleh butuh konversi khusus per template."""
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
        Malrule(
            "siklus.ambil_awal_siklus",
            pola[0],
            "K",
            "langsung mengambil unsur pertama siklus tanpa menghitung sisa",
        ),
        Malrule(
            "siklus.panjang_siklus_kelebihan",
            _siklus(list(pola), ((posisi - 1) % (n + 1)) + 1),
            "K",
            f"siklus dihitung {n + 1} unsur, bukan {n}",
        ),
        # K dari arah berlawanan, dan ini bukan pengisi.
        #
        # Semua kandidat K lain ("ambil akhir", "ambil awal", panjang siklus
        # kurang/kelebihan) menebak SATU huruf. Kalau beberapa tebakan itu
        # kebetulan jatuh di huruf yang sama dengan kunci (atau saling
        # bertabrakan), semuanya dibuang saring_malrule sekaligus dan soalnya
        # tinggal tanpa jalur K — terukur ~3% sebelum malrule ini ada.
        #
        # Membaca pola terbalik tidak bergantung pada kebetulan huruf: hasil
        # aritmetikanya (posisi - sisa) hampir selalu berbeda dari posisi
        # itu sendiri. Anak yang melakukannya memang salah konsep: ia mengira
        # siklus dihitung dari ujung.
        Malrule(
            "siklus.dihitung_dari_belakang",
            _siklus(list(pola), posisi - sisa if sisa else n),
            "K",
            "pola dibaca dari belakang — arah hitung siklusnya terbalik",
        ),
        # Jalur H — anak sudah paham siklusnya, hanya salah menghitung sisa.
        #
        # Sempat TIDAK ADA di template ini (siklus_warna punya, siklus_huruf
        # tidak), sehingga setiap kesalahan pada soal siklus huruf otomatis
        # jadi K. Itu berarti anak yang cuma keliru membagi tercatat "salah
        # konsep" dan diarahkan mengulang materi siklus yang sebenarnya sudah
        # ia kuasai. Ditemukan test_setiap_template_bisa_membedakan_k_dari_h,
        # bukan dari membaca kode — cacatnya baru kelihatan setelah
        # penyaringan malrule.
        #
        # Dua arah (kelebihan & kurang satu) supaya setidaknya satu selamat
        # dari penyaringan; dengan satu arah saja mayoritas soal kehilangan
        # jalur H-nya.
        Malrule(
            "siklus.sisa_meleset",
            _siklus(list(pola), posisi + 1),
            "H",
            "cara pembagiannya benar, sisanya kelebihan satu",
        ),
        Malrule(
            "siklus.sisa_kurang_satu",
            _siklus(list(pola), posisi - 1),
            "H",
            "cara pembagiannya benar, sisanya kurang satu",
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
        {"pola": list(pola), "posisi": posisi},
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
            "siklus.ambil_awal_siklus",
            pola[0],
            "K",
            "langsung mengambil unsur pertama siklus tanpa menghitung sisa",
        ),
        Malrule(
            "siklus.panjang_siklus_salah",
            _siklus(list(pola), ((posisi - 1) % max(n - 1, 1)) + 1),
            "K",
            f"siklus dihitung {n - 1} unsur, bukan {n}",
        ),
        # Kandidat K sengaja disebut LEBIH DULU daripada H.
        #
        # `saring_malrule` mempertahankan yang lebih dulu muncul, dan versi
        # sebelumnya menempatkan H di urutan kedua — akibatnya pada sebagian
        # soal yang tersisa justru hanya jalur H, sehingga template ini tidak
        # bisa mendeteksi miskonsepsi sama sekali. Metrik utama proyek ini
        # adalah jumlah K; template tanpa jalur K tidak menyumbang apa pun
        # ke situ. Tertangkap test_tiap_template_punya_malrule_konsep.
        Malrule(
            "siklus.sisa_meleset",
            _siklus(list(pola), posisi + 1),
            "H",
            "cara pembagian benar, sisanya kelebihan satu",
        ),
        Malrule(
            "siklus.sisa_kurang_satu",
            _siklus(list(pola), posisi - 1),
            "H",
            "cara pembagian benar, sisanya kurang satu",
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
        {"pola": list(pola), "posisi": posisi},
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
        # K kedua, dan ini bukan hiasan.
        #
        # `dikira_kelipatan` di atas KOLAPS saat awal == 1: target // 1 ==
        # target, yang persis sama dengan malrule B `jawab_nilainya`, jadi ia
        # selalu dibuang `saring_malrule`. Akibatnya 15,8% soal template ini
        # sama sekali tidak punya jalur K — anak yang benar-benar salah
        # konsep tercatat sebagai salah hitung, dan tidak ikut terhitung di
        # metrik utama proyek ini (jumlah K).
        #
        # Ini pola bug yang sama dengan `pecahan.penjumlahan_meleset`: sebuah
        # malrule yang secara MATEMATIS tidak pernah bisa berbeda dari
        # malrule lain untuk sebagian parameter. Bentuknya tidak kelihatan
        # dari membaca kode template — hanya muncul setelah penyaringan.
        #
        # Membaginya dengan rasio (bukan awal) tetap masuk akal sebagai
        # miskonsepsi: anak melihat 1, 2, 4, 8 lalu mengira "kelipatan 2",
        # sehingga menjawab 2048 : 2 = 1024. Dan ia tidak pernah kolaps,
        # karena rasio selalu >= 2.
        Malrule(
            "terbalik.dikira_kelipatan_rasio",
            str(target // rasio),
            "K",
            f"dikira pola kelipatan {rasio}, jadi urutannya dikira hasil bagi",
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
        {"pola": list(pola), "n_angka": n_angka},
        teks,
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        minta_restatement=True,
        bagian="E",
        tantangan=True,
    )


# ── Bagian F — rumus suku ke-n (P4+) ────────────────────────────────────
#
# Inilah kenaikan level yang sesungguhnya. Bagian A-E bisa dikerjakan dengan
# menulis deretnya satu per satu sampai ketemu; di sini tidak bisa. Posisi
# yang ditanya sengaja jauh (ke-100, ke-250) sehingga cara manual berhenti
# bekerja dan anak terpaksa memakai rumus.
#
# Lembar penilaian 20 Agustus sudah menandai kesiapan ini: "Cara manual
# dipakai di semua soal siklus (5, 6, 11) -> konsepnya benar, tapi belum ada
# jalan pintas pembagian. Ini penanda kesiapan naik level, bukan kesalahan.
# Di P4 angka jadi ke-100 dan cara manual berhenti bekerja."


def suku_ke_n(awal: int, beda: int, posisi: int) -> Soal:
    """Nilai suku ke-n pada posisi yang terlalu jauh untuk ditulis manual."""
    jawab = awal + beda * (posisi - 1)

    mal = (
        Malrule(
            "suku_n.kali_posisi_penuh",
            str(awal + beda * posisi),
            "K",
            f"dikali {posisi} penuh — suku pertama ikut terhitung, "
            "seharusnya posisi dikurangi satu",
        ),
        Malrule(
            "suku_n.lupa_suku_awal",
            str(beda * posisi),
            "K",
            "hanya mengalikan selisih, suku awalnya tidak ditambahkan",
        ),
        Malrule(
            "suku_n.dikira_kelipatan",
            str(awal * posisi),
            "K",
            f"dikira kelipatan {awal}, padahal pola tambah tetap",
        ),
        Malrule(
            "suku_n.perkalian_meleset",
            str(jawab - beda),
            "H",
            "rumusnya benar, perkaliannya meleset satu langkah",
        ),
    )

    urut = _deret(awal, beda, 5)
    teks = (
        f"Pola: {', '.join(str(x) for x in urut)}, ...\n\n"
        f"Berapa bilangan pada urutan ke-{posisi}?"
    )

    return Soal(
        "suku_ke_n",
        {"awal": awal, "beda": beda, "posisi": posisi},
        teks,
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        minta_restatement=True,
        bagian="F",
    )


def sisa_bagi_siklus(pola: tuple[str, ...], posisi: int) -> Soal:
    """Siklus pada posisi yang terlalu jauh untuk dienumerasi.

    Sengaja memakai posisi ratusan. Di P3 anak boleh menulis 20 huruf satu
    per satu dan itu sah; di sini cara itu mati, dan yang tersisa hanya
    pembagian bersisa. Kegagalan di soal ini pada anak yang benar di
    `siklus_huruf` adalah sinyal presisi: konsep siklusnya ada, jalan
    pintasnya belum.
    """
    n = len(pola)
    jawab = _siklus(list(pola), posisi)
    sisa = posisi % n

    # Kandidat malrule sengaja BANYAK dan beragam arah.
    #
    # Pola huruf hanya punya 2-4 unsur berbeda, jadi tebakan salah cepat
    # bertabrakan satu sama lain (atau dengan kunci) lalu dibuang
    # `saring_malrule`. Dengan kandidat sedikit, mayoritas soal berakhir
    # menyisakan satu malrule saja — terukur 78% soal hanya punya 1, dan
    # nyaris tak pernah punya jalur H. Akibatnya anak yang cuma keliru
    # membagi tercatat salah konsep.
    #
    # Urutannya penting: yang paling informatif didahulukan, karena yang
    # bertahan setelah penyaringan adalah yang lebih dulu disebut.
    mal = [
        Malrule(
            "sisa_siklus.ambil_akhir",
            pola[-1],
            "K",
            "sisa pembagian diabaikan, langsung ambil unsur terakhir siklus",
        ),
        Malrule(
            "sisa_siklus.hasil_bagi_dipakai",
            pola[(posisi // n - 1) % n],
            "K",
            "yang dipakai hasil baginya, bukan sisanya",
        ),
        Malrule(
            "sisa_siklus.sisa_meleset",
            _siklus(list(pola), posisi + 1),
            "H",
            "cara pembagiannya benar, sisanya kelebihan satu",
        ),
        Malrule(
            "sisa_siklus.sisa_kurang_satu",
            _siklus(list(pola), posisi - 1),
            "H",
            "cara pembagiannya benar, sisanya kurang satu",
        ),
        Malrule(
            "sisa_siklus.panjang_siklus_salah",
            _siklus(list(pola), ((posisi - 1) % max(n - 1, 1)) + 1),
            "K",
            f"siklus dihitung {n - 1} unsur, bukan {n}",
        ),
        Malrule(
            "sisa_siklus.ambil_awal_siklus",
            pola[0],
            "K",
            "langsung mengambil unsur pertama siklus tanpa menghitung sisa",
        ),
        # Alasannya sama dengan siklus.dihitung_dari_belakang: kandidat K
        # lain menebak satu huruf dan bisa kebetulan jatuh di huruf kunci,
        # sedangkan arah terbalik hampir selalu menghasilkan huruf lain.
        Malrule(
            "sisa_siklus.dihitung_dari_belakang",
            _siklus(list(pola), posisi - sisa if sisa else n),
            "K",
            "pola dibaca dari belakang — arah hitung siklusnya terbalik",
        ),
    ]
    if sisa == 0:
        mal.insert(
            0,
            Malrule(
                "sisa_siklus.off_by_one_sisa_nol",
                pola[0],
                "K",
                "sisa 0 dikira menunjuk posisi ke-1, padahal posisi terakhir siklus",
            ),
        )

    teks = (
        "Pola berulang terus-menerus:\n\n"
        f"    {'  '.join(''.join(pola) for _ in range(3))}  ...\n\n"
        f"Huruf ke-{posisi} adalah huruf apa?\n"
        "(Angkanya terlalu besar untuk ditulis satu per satu.)"
    )

    return Soal(
        "sisa_bagi_siklus",
        {"pola": list(pola), "posisi": posisi},
        teks,
        jawab,
        saring_malrule(jawab, mal),
        minta_restatement=True,
        bagian="F",
    )


def pola_pecahan(pembilang: int, penyebut: int, beda_pembilang: int, n_tampil: int) -> Soal:
    """Deret pecahan berpenyebut tetap, pembilang berpola.

    Bentuk soal yang tidak ada di P3 sama sekali. Miskonsepsi khasnya juga
    baru: anak yang sudah paham pola bilangan bulat sering menambahkan
    penyebut juga (1/4, 2/5, 3/6...) — itu K yang tidak mungkin muncul di
    Bagian A mana pun, dan justru itulah gunanya.
    """
    pemb = [pembilang + beda_pembilang * i for i in range(n_tampil)]
    jawab_pemb = pembilang + beda_pembilang * n_tampil
    jawab = f"{jawab_pemb}/{penyebut}"

    mal = (
        Malrule(
            "pecahan.penyebut_ikut_naik",
            f"{jawab_pemb}/{penyebut + beda_pembilang * n_tampil}",
            "K",
            "penyebut ikut ditambah — pola dikira berlaku untuk kedua angka",
        ),
        Malrule(
            "pecahan.pembilang_tidak_naik",
            f"{pemb[-1]}/{penyebut}",
            "K",
            "pembilang tidak dilanjutkan, hanya menyalin suku terakhir",
        ),
        Malrule(
            "pecahan.beda_dikira_satu",
            f"{pemb[-1] + 1}/{penyebut}",
            "K",
            "selisih pembilang dikira selalu 1",
        ),
        # Malrule H: pembilang MELEWATI satu langkah, bukan kurang satu
        # langkah.
        #
        # Versi pertama memakai `jawab_pemb - beda_pembilang`, dan itu secara
        # matematis SELALU sama dengan `pemb[-1]` (suku terakhir yang tampil)
        # — jadi ia selalu bertabrakan dengan `pembilang_tidak_naik` lalu
        # dibuang `saring_malrule`. Akibatnya pola_pecahan tidak pernah punya
        # jalur H sama sekali: anak yang cuma salah menjumlahkan pembilang
        # akan tercatat sebagai salah konsep, dan itu kesalahan diagnosis
        # yang paling mahal (mengirim anak mengulang materi yang sudah ia
        # pahami). Tertangkap test_bagian_f_punya_kode_k_dan_h.
        Malrule(
            "pecahan.penjumlahan_meleset",
            f"{jawab_pemb + beda_pembilang}/{penyebut}",
            "H",
            "polanya benar, penjumlahan pembilangnya kelebihan satu langkah",
        ),
    )

    tampil = ", ".join(f"{p}/{penyebut}" for p in pemb)
    teks = f"Lanjutkan polanya:\n\n    {tampil}, ___"

    return Soal(
        "pola_pecahan",
        {
            "pembilang": pembilang,
            "penyebut": penyebut,
            "beda_pembilang": beda_pembilang,
            "n_tampil": n_tampil,
        },
        teks,
        jawab,
        saring_malrule(jawab, list(mal)),
        bagian="F",
    )


def jumlah_deret(awal: int, beda: int, n: int) -> Soal:
    """Jumlah n suku pertama. Menuntut rumus, bukan penjumlahan beruntun.

    Soal paling menuntut di bank ini. Anak yang menjumlahkan satu per satu
    biasanya kehabisan waktu atau salah di tengah — dan itu bukan kegagalan
    konsep, melainkan penanda bahwa rumus deret belum diajarkan. Karena itu
    `berhenti_di_tengah` diberi kode H, bukan K.
    """
    suku = _deret(awal, beda, n)
    jawab = sum(suku)
    terakhir = suku[-1]

    mal = (
        Malrule(
            "jumlah_deret.dijawab_suku_terakhir",
            str(terakhir),
            "B",
            "yang diminta JUMLAH seluruh suku, yang dijawab nilai suku terakhir",
        ),
        Malrule(
            "jumlah_deret.rata_rata_ujung_tanpa_kali_n",
            str((awal + terakhir) // 2),
            "K",
            "rata-rata ujung sudah benar, tapi belum dikalikan banyak suku",
        ),
        Malrule(
            "jumlah_deret.kali_n_tanpa_rata_rata",
            str(terakhir * n),
            "K",
            "suku terakhir dikali banyak suku — semua suku dianggap sama besar",
        ),
        Malrule(
            "jumlah_deret.berhenti_di_tengah",
            str(jawab - terakhir),
            "H",
            "penjumlahannya benar tapi berhenti satu suku lebih awal",
        ),
    )

    teks = (
        f"Pola: {', '.join(str(x) for x in suku[:5])}, ...\n\n"
        f"Berapa JUMLAH {n} bilangan pertama pola ini?"
    )

    return Soal(
        "jumlah_deret",
        {"awal": awal, "beda": beda, "n": n},
        teks,
        str(jawab),
        saring_malrule(str(jawab), list(mal)),
        minta_restatement=True,
        bagian="F",
        tantangan=True,
    )


# ── Registri ────────────────────────────────────────────────────────────

REGISTRI_TOPIK: dict[str, Callable[..., Soal]] = {
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
    # Bagian F — P4 ke atas
    "suku_ke_n": suku_ke_n,
    "sisa_bagi_siklus": sisa_bagi_siklus,
    "pola_pecahan": pola_pecahan,
    "jumlah_deret": jumlah_deret,
}


# ── Profil batas angka per level (dipindah dari generator.py) ──

# Pengali batas angka per level.
#
# HANYA menggeser besar angka, TIDAK menaikkan level yang sebenarnya.
# Lembar penilaian 20 Agustus sudah menuliskannya: "di P4 angkanya jadi
# ke-100 dan cara manual berhenti bekerja". Menaikkan posisi dari 20 ke 100
# pada template yang sama membuat anak menulis lebih lama, bukan berpikir
# lebih dalam.
#
# Kenaikan level yang sesungguhnya datang dari template yang menuntut rumus
# suku ke-n (lihat URUTAN_PER_LEVEL) — tabel ini hanya memastikan angkanya
# tidak terasa kekanak-kanakan di level atas.
PROFIL_LEVEL: dict[str, dict] = {
    "P3": {
        "posisi_suku_n": (25, 30, 40),
        "posisi_sisa_bagi": (40, 70),
        "penyebut_pecahan": (4, 5, 6),
        "n_jumlah_deret": (8, 10),
        "n_tampil_geometri": (3, 4),
        "posisi_terbalik_geometri": (4, 6, 3, 4),
        "beda_aritmetika": (3, 4, 5, 6, 7),
        "n_minta": 2,
        "rasio_geometri": (2, 2, 2, 3, 3, 4),
        "kenaikan_bertingkat": (1, 2, 3),
        "posisi_siklus": (15, 40),
        "posisi_warna": (20, 45),
        "gambar_korek": (8, 20),
        "gambar_titik": (6, 12),
        "posisi_terbalik": (10, 16),
        "tambah_hari": (16, 20, 23, 30, 40, 50, 100),
        "n_angka_kelipatan": (5, 12),
    },
    "P4": {
        "posisi_suku_n": (50, 60, 75, 100),
        "posisi_sisa_bagi": (80, 150),
        "penyebut_pecahan": (5, 6, 7, 8),
        "n_jumlah_deret": (10, 12, 15),
        "n_tampil_geometri": (4, 5),
        "posisi_terbalik_geometri": (6, 8, 4, 5),
        "beda_aritmetika": (6, 7, 8, 9, 11, 12),
        "n_minta": 2,
        "rasio_geometri": (2, 2, 3, 3, 4),
        "kenaikan_bertingkat": (2, 3, 4),
        "posisi_siklus": (30, 80),
        "posisi_warna": (40, 90),
        "gambar_korek": (15, 40),
        "gambar_titik": (8, 16),
        "posisi_terbalik": (12, 22),
        "tambah_hari": (45, 60, 75, 90, 100, 120, 150),
        "n_angka_kelipatan": (8, 20),
    },
    "P5": {
        "posisi_suku_n": (100, 120, 150, 200),
        "posisi_sisa_bagi": (150, 300),
        "penyebut_pecahan": (7, 8, 9, 10, 12),
        "n_jumlah_deret": (15, 20, 25),
        "n_tampil_geometri": (5, 6),
        "posisi_terbalik_geometri": (8, 10, 5, 6),
        "beda_aritmetika": (9, 11, 12, 13, 14, 15, 16),
        "n_minta": 3,
        "rasio_geometri": (2, 3, 3, 4, 5),
        "kenaikan_bertingkat": (3, 4, 5),
        "posisi_siklus": (60, 150),
        "posisi_warna": (75, 180),
        "gambar_korek": (25, 60),
        "gambar_titik": (10, 20),
        "posisi_terbalik": (15, 30),
        "tambah_hari": (100, 150, 200, 250, 300, 365),
        "n_angka_kelipatan": (12, 30),
    },
    "P6": {
        "posisi_suku_n": (150, 200, 250, 300, 500),
        "posisi_sisa_bagi": (300, 700),
        "penyebut_pecahan": (9, 10, 11, 12, 15),
        "n_jumlah_deret": (20, 25, 30, 40),
        "n_tampil_geometri": (6, 7),
        "posisi_terbalik_geometri": (10, 12, 6, 7),
        "beda_aritmetika": (12, 13, 14, 15, 16, 17, 18, 19, 21),
        "n_minta": 3,
        "rasio_geometri": (3, 4, 5, 6),
        "kenaikan_bertingkat": (4, 5, 6, 7),
        "posisi_siklus": (100, 300),
        "posisi_warna": (120, 350),
        "gambar_korek": (40, 100),
        "gambar_titik": (12, 25),
        "posisi_terbalik": (20, 40),
        "tambah_hari": (200, 300, 365, 500, 730, 1000),
        "n_angka_kelipatan": (20, 50),
    },
}


def profil(level: str) -> dict:
    """Batas angka untuk satu level. Level tak dikenal jatuh ke bawaan.

    Sengaja tidak melempar: `siswa.tingkat` adalah kolom teks bebas yang
    sudah terisi di basis data produksi, dan satu nilai aneh di situ tidak
    boleh membuat guru gagal membuat sesi. Yang salah levelnya lebih baik
    daripada yang tidak ada lembarnya.
    """
    return PROFIL_LEVEL.get(level, PROFIL_LEVEL[LEVEL_BAWAAN])



WARNA = ("merah", "kuning", "hijau", "biru", "putih", "ungu")
HURUF = ("A", "B", "C", "D")

LEVEL_BAWAAN = "P3"

# Alfabet lebih panjang untuk soal siklus level atas, yang butuh cukup huruf
# unik agar malrule-nya tidak saling bertabrakan (lihat sisa_bagi_siklus).
HURUF_PANJANG = ("A", "B", "C", "D", "E", "F")


def _pola_huruf(rng: random.Random) -> tuple[str, ...]:
    """Pola dengan tepat satu huruf berulang, mis. A B B C.

    Huruf yang muncul dua kali membuat anak tidak bisa menebak dari posisi
    saja; ia harus benar-benar menghitung siklusnya.

    Dua bentuk yang sengaja dihindari:
      - semua huruf sama (AAA) — semua posisi berjawab sama, tidak
        mendiagnosis apa pun
      - semua huruf beda (ABCD) — anak bisa memetakan posisi ke huruf tanpa
        memahami siklus

    Minimal 3 huruf UNIK, karena itu panjangnya mulai dari 4 dan bukan 3.
    Dengan hanya 2 huruf unik cuma ada satu jawaban salah yang mungkin,
    sehingga semua malrule menyusut jadi satu setelah `saring_malrule` dan
    jalur H tidak pernah selamat — soalnya tetap sah, tapi berhenti bisa
    memisahkan salah konsep dari salah hitung. Terukur: pola 3-huruf membuat
    78% soal siklus_huruf bermalrule tunggal.
    """
    panjang = rng.choice([4, 5])
    dasar = list(HURUF_PANJANG[:panjang])
    sumber, tujuan = rng.sample(range(panjang), 2)
    dasar[tujuan] = dasar[sumber]
    # Ujung kembar merusak diagnosis: kalau pola[0] == pola[-1] (DBCD,
    # ABCA), malrule "ambil unsur pertama" dan "ambil unsur terakhir" jadi
    # JAWABAN YANG SAMA, dan pada posisi ber-sisa 0 atau ber-sisa 1 salah
    # satunya bahkan = kunci. Semua kandidat K yang menebak satu huruf
    # lalu habis tersaring bersamaan — terukur ~3% soal kehilangan seluruh
    # jalur K. Ujung harus beda.
    if dasar[0] == dasar[-1]:
        pengganti = next(h for h in HURUF_PANJANG if h not in dasar)
        dasar[-1] = pengganti
    return tuple(dasar)


def _parameter(template_id: str, rng: random.Random, level: str = LEVEL_BAWAAN) -> dict:
    """Batas parameter dijaga supaya soal tetap pada levelnya.

    Aturan yang ditegakkan di sini:
      - hasil akhir tidak negatif
      - angka hasil masih terbayang anak pada level itu
      - posisi target selalu jatuh TEPAT pada suku deret (bukan di antaranya)
    """
    pf = profil(level)
    if template_id == "deret_aritmetika":
        return {
            "awal": rng.randint(2, 12),
            "beda": rng.choice(pf["beda_aritmetika"]),
            "n_tampil": 4,
            "n_minta": pf["n_minta"],
        }

    if template_id == "deret_aritmetika_turun":
        beda = rng.choice(pf["beda_aritmetika"])
        n_tampil = rng.choice([4, 5])
        # awal harus cukup besar supaya suku terakhir tetap positif
        awal = beda * rng.randint(n_tampil + 2, n_tampil + 8)
        return {"awal": awal, "beda": beda, "n_tampil": n_tampil}

    if template_id == "deret_geometri":
        # Rasio 2 diberi porsi lebih besar di level bawah: pola x2 adalah
        # prasyarat Bagian D (soal terbalik). Rasio lain tetap ada supaya anak
        # tidak menghafal "pola kali berarti dikali dua". Di level atas rasio 2
        # ditinggalkan — yang menantang bukan lagi mengenali pola kali,
        # melainkan besarnya perkalian.
        rasio = rng.choice(pf["rasio_geometri"])
        lo_tampil, hi_tampil = pf["n_tampil_geometri"]
        if rasio == 2:
            awal = rng.choice([1, 2, 3, 4, 5, 6])
        elif rasio == 3:
            awal = rng.choice([1, 2, 3])
        else:
            awal = rng.choice([1, 2, 3])
        # n_tampil ikut level, bukan dipatok per rasio. Versi sebelumnya
        # memakai angka tetap untuk rasio 3 dan 4, sehingga P3 dan P6 bisa
        # menghasilkan soal yang identik persis — perbedaan level hilang
        # tanpa ada yang memberi tahu.
        n_tampil = rng.randint(lo_tampil, hi_tampil)
        # Jaga supaya suku terakhir tetap terbayang anak.
        while awal * rasio**n_tampil > 6000 and n_tampil > 3:
            n_tampil -= 1
        return {"awal": awal, "rasio": rasio, "n_tampil": n_tampil}

    if template_id == "deret_bertingkat":
        return {
            "awal": rng.randint(1, 9),
            "beda_awal": rng.choice([1, 2, 3, 4]),
            "kenaikan": rng.choice(pf["kenaikan_bertingkat"]),
            "n_tampil": rng.choice([5, 6]),
        }

    if template_id == "siklus_huruf":
        pola = _pola_huruf(rng)
        # Sisa 0 adalah jebakan off-by-one — pastikan sering muncul.
        lo, hi = pf["posisi_siklus"]
        posisi = rng.choice(
            [
                len(pola) * rng.randint(lo // len(pola) + 1, hi // len(pola)),  # sisa 0
                rng.randint(lo, hi),
            ]
        )
        return {"pola": pola, "posisi": posisi}

    if template_id == "siklus_warna":
        # Sama alasannya dengan _pola_huruf: minimal 3 warna UNIK.
        # Bentuk lama `rng.sample(WARNA, n-1)` lalu menduplikasi unsur
        # pertama menghasilkan hanya 2 warna unik saat n=3, dan 89% soal
        # siklus_warna berakhir bermalrule tunggal — tidak bisa memisahkan
        # salah konsep dari salah hitung.
        n = rng.choice([4, 5])
        pilih = list(rng.sample(WARNA, n - 1))  # n-1 warna unik
        ulang = rng.randrange(len(pilih))
        sisip = rng.randrange(len(pilih) + 1)
        pola = pilih[:sisip] + [pilih[ulang]] + pilih[sisip:]
        return {"pola": tuple(pola), "posisi": rng.randint(*pf["posisi_warna"])}

    if template_id == "korek_api":
        return {
            "awal": rng.choice([3, 4, 5, 6, 7]),
            "tambah": rng.choice([2, 3, 4]),
            "gambar_ke": rng.randint(*pf["gambar_korek"]),
        }

    if template_id == "titik_segitiga":
        # T(12)=78 di P3 — masih terbayang anak, dan menjaga varian tetap
        # cukup banyak untuk drill mingguan. Level atas memperlebar rentang
        # ini, yang sekaligus menambal keluhan "titik_segitiga cuma 7 varian"
        # di README §Batas yang diketahui.
        return {"gambar_ke": rng.randint(*pf["gambar_titik"])}

    if template_id == "deret_terbalik_aritmetika":
        return {
            "awal": rng.randint(2, 8),
            "beda": rng.choice([3, 4, 5, 6]),
            "posisi_target": rng.randint(*pf["posisi_terbalik"]),
        }

    if template_id == "deret_terbalik_geometri":
        # Batas atas dijaga ketat: nilai target tumbuh eksponensial, dan
        # bilangan yang tidak lagi terbayang anak berhenti mendiagnosis
        # apa pun. Posisi diambil dari profil, lalu dipangkas supaya
        # target tetap di bawah ~5000 bahkan di P6.
        # Rasio dibatasi 2 atau 3 (bukan diambil dari rasio_geometri): nilai
        # target tumbuh eksponensial, dan rasio 4+ pada posisi belasan
        # menghasilkan bilangan yang tidak lagi terbayang anak — soal berhenti
        # mendiagnosis dan berubah jadi uji ketelitian mengalikan.
        #
        # Rentang posisi ditulis eksplisit per level, TIDAK diturunkan dari
        # posisi_terbalik lewat min(). Pemangkasan seperti itu membuat P3 dan
        # P6 sama-sama jatuh ke batas yang sama, dan perbedaan levelnya hilang
        # diam-diam — persis bug yang tertangkap test
        # `test_setiap_template_berubah_antara_p3_dan_p6`.
        rasio = rng.choice([2, 2, 3])
        lo2, hi2, lo3, hi3 = pf["posisi_terbalik_geometri"]
        if rasio == 2:
            posisi = rng.randint(lo2, hi2)
            # awal dipilih setelah posisi diketahui, supaya target tetap di
            # bawah ~4000 apa pun levelnya. Tanpa ini P6 posisi 12 dengan
            # awal 7 memberi 14336 — angka yang berhenti mendiagnosis apa
            # pun dan hanya menguji ketelitian mengalikan.
            batas_awal = max(1, 4000 // (2 ** (posisi - 1)))
            awal = rng.choice([a for a in (2, 3, 4, 5, 6, 7) if a <= batas_awal] or [1])
        else:
            posisi = rng.randint(lo3, hi3)
            batas_awal = max(1, 4000 // (3 ** (posisi - 1)))
            # P3: posisi bisa serendah 3, jadi awal=1 memberi target 9 —
            # dan 9 // rasio == 3 == kunci, malrule K-nya kolaps lagi.
            # awal >= 2 menjamin target // rasio != target (malrule B) dan
            # != kunci (kuncinya posisi, bukan nilai).
            kandidat_awal = [a for a in (2, 3) if a <= batas_awal]
            awal = rng.choice(kandidat_awal or [1])
        return {"awal": awal, "rasio": rasio, "posisi_target": posisi}

    if template_id == "siklus_hari":
        return {
            "hari_awal": rng.choice(HARI),
            "tambah": rng.choice(pf["tambah_hari"]),
        }

    if template_id == "jumlah_siklus":
        n = rng.choice([3, 4])
        pola = tuple(rng.sample(range(1, 6), n))
        lo, hi = pf["n_angka_kelipatan"]
        n_angka = rng.randint(lo, hi) * n + rng.randint(1, n - 1)  # sisa != 0
        return {"pola": pola, "n_angka": n_angka}

    if template_id == "suku_ke_n":
        # Posisi sengaja jauh: cara manual harus mati di sini. Kalau anak
        # masih sanggup menulis deretnya sampai ketemu, soal ini kehilangan
        # seluruh maksudnya.
        return {
            "awal": rng.randint(2, 12),
            "beda": rng.choice(pf["beda_aritmetika"]),
            "posisi": rng.choice(pf["posisi_suku_n"]),
        }

    if template_id == "sisa_bagi_siklus":
        # Pola untuk soal ini WAJIB punya minimal 3 huruf berbeda, tidak
        # seperti `siklus_huruf` yang boleh 2.
        #
        # Alasannya matematis, bukan selera: dengan hanya 2 huruf unik cuma
        # ada SATU jawaban salah yang mungkin, sehingga berapa pun malrule
        # yang ditulis akan menyusut jadi satu setelah penyaringan — dan
        # jalur H hampir tidak pernah selamat. Terukur: pola 2-huruf selalu
        # menyisakan 1 malrule.
        #
        # Panjang siklus juga dijaga tidak membagi habis angka bulat yang
        # umum, supaya sisanya bervariasi.
        panjang = rng.choice([4, 5, 6])
        dasar = list(HURUF_PANJANG[:panjang])
        # satu huruf diulang: tetap menuntut perhitungan siklus, tapi
        # menyisakan cukup huruf unik untuk beberapa malrule
        sumber, tujuan = rng.sample(range(panjang), 2)
        dasar[tujuan] = dasar[sumber]
        # Aturan sama dengan _pola_huruf: ujung kembar (DBCD, ABCA) membuat
        # "ambil awal" dan "ambil akhir" jadi jawaban yang sama dan pada
        # sisa 0/1 salah satunya = kunci — semua jalur K habis tersaring.
        if dasar[0] == dasar[-1]:
            pengganti = next(h for h in HURUF_PANJANG if h not in dasar)
            dasar[-1] = pengganti
        return {
            "pola": tuple(dasar),
            "posisi": rng.randint(*pf["posisi_sisa_bagi"]),
        }

    if template_id == "pola_pecahan":
        # Penyebut dijaga tetap dan tidak kecil, supaya malrule
        # "penyebut ikut naik" menghasilkan pecahan yang jelas berbeda.
        #
        # Penyebut dipilih SETELAH pembilang & beda diketahui, dan dijamin
        # lebih besar dari pembilang terjauh yang akan muncul (termasuk
        # malrule H yang melewati satu langkah). Tanpa ini 56% soal
        # menampilkan pecahan seperti 12/12 atau 15/12 — benar secara pola,
        # tapi janggal dibaca anak SD dan mengalihkan perhatian dari yang
        # sedang diuji.
        pembilang = rng.randint(1, 4)
        beda = rng.choice([1, 2, 3])
        n_tampil = 4
        # pembilang terbesar yang bisa tampil: kunci + satu langkah (malrule H)
        pemb_maks = pembilang + beda * (n_tampil + 1)
        layak = [p for p in pf["penyebut_pecahan"] if p > pemb_maks]
        penyebut = rng.choice(layak) if layak else pemb_maks + rng.choice([1, 2, 3])
        return {
            "pembilang": pembilang,
            "penyebut": penyebut,
            "beda_pembilang": beda,
            "n_tampil": n_tampil,
        }

    if template_id == "jumlah_deret":
        return {
            "awal": rng.randint(1, 9),
            "beda": rng.choice([2, 3, 4, 5]),
            "n": rng.choice(pf["n_jumlah_deret"]),
        }

    raise KeyError(f"template tidak dikenal: {template_id}")



# ── Komposisi lembar per level (dipindah dari templates.py) ──

# Urutan tetap satu lembar: mudah -> sulit, tantangan di akhir.
#
# Dipertahankan sebagai komposisi P3 dan sebagai nilai bawaan bagi pemanggil
# lama. Komposisi per level ada di URUTAN_PER_LEVEL di bawah.
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

# Komposisi lembar per level.
#
# Tetap 12 soal di semua level — bukan angka keramat, tapi batas stamina:
# lembar penilaian 20 Agustus mencatat risiko anak lelah menulis dan mulai
# mengosongkan kotak di paruh kedua. Menambah soal untuk level atas akan
# menukar informasi diagnosis dengan kelelahan.
#
# Yang berubah adalah KOMPOSISINya. Makin tinggi level, makin banyak Bagian F
# (rumus suku ke-n) menggantikan Bagian A-C yang bisa diselesaikan dengan
# menulis deretnya satu per satu.
URUTAN_PER_LEVEL: dict[str, tuple[str, ...]] = {
    # P3: seperti lembar 20 Agustus, tanpa Bagian F sama sekali.
    "P3": URUTAN_LEMBAR,
    # P4: dua soal Bagian F masuk, menggantikan satu deret dan satu siklus
    # yang paling mudah dienumerasi.
    "P4": (
        "deret_aritmetika",
        "deret_aritmetika_turun",
        "deret_geometri",
        "deret_bertingkat",
        "siklus_huruf",
        "korek_api",
        "titik_segitiga",
        "deret_terbalik_aritmetika",
        "deret_terbalik_geometri",
        "siklus_hari",
        "suku_ke_n",
        "sisa_bagi_siklus",
    ),
    # P5: pecahan masuk (bentuk soal yang sama sekali tidak ada di P3),
    # Bagian A menyusut.
    "P5": (
        "deret_aritmetika",
        "deret_geometri",
        "deret_bertingkat",
        "siklus_huruf",
        "korek_api",
        "titik_segitiga",
        "deret_terbalik_aritmetika",
        "deret_terbalik_geometri",
        "jumlah_siklus",
        "suku_ke_n",
        "sisa_bagi_siklus",
        "pola_pecahan",
    ),
    # P6: separuh lembar Bagian F, ditutup jumlah_deret sebagai tantangan.
    "P6": (
        "deret_aritmetika",
        "deret_geometri",
        "deret_bertingkat",
        "titik_segitiga",
        "deret_terbalik_aritmetika",
        "deret_terbalik_geometri",
        "siklus_hari",
        "jumlah_siklus",
        "suku_ke_n",
        "sisa_bagi_siklus",
        "pola_pecahan",
        "jumlah_deret",
    ),
}


def susun_lembar(level: str) -> tuple[str, ...]:
    """Daftar template untuk satu lembar di level tertentu.

    Level tak dikenal jatuh ke P3 — sama alasannya dengan `generator.profil`:
    satu nilai aneh di kolom `siswa.tingkat` tidak boleh membuat guru gagal
    membuat sesi.
    """
    return URUTAN_PER_LEVEL.get(level, URUTAN_LEMBAR)

# ── Judul & catatan bagian (dipindah dari render.py) ──

JUDUL_BAGIAN = {
    "A": "Bagian A — Lanjutkan polanya",
    "B": "Bagian B — Pola berulang",
    "C": "Bagian C — Pola gambar",
    "D": "Bagian D — Pola dibalik",
    "E": "Bagian E — Pola dalam cerita",
    "F": "Bagian F — Cari jalan pintasnya",
}

CATATAN_BAGIAN = {
    "D": "Baca pelan-pelan. Yang ditanya di bagian ini <b>berbeda</b> "
         "dari Bagian A.",
    # Anak P3-P4 terbiasa menulis deretnya satu per satu sampai ketemu, dan
    # itu memang cara yang sah di Bagian A-E. Di sini angkanya sengaja dibuat
    # terlalu jauh untuk itu. Tanpa kalimat ini sebagian anak akan mencoba
    # menulis 250 suku, kehabisan waktu, lalu mengosongkan sisa lembarnya —
    # dan yang tercatat jadi "tidak bisa", padahal masalahnya cuma belum
    # tahu boleh mencari jalan pintas.
    "F": "Angkanya terlalu besar untuk ditulis satu per satu. "
         "Coba cari <b>caranya</b>, bukan tulis semuanya.",
}


def _svg_korek(n_tampil: int, awal: int, tambah: int) -> str:
    """Gambar tiga bangun pertama pola korek api sebagai SVG.

    Jumlah titik zig-zag untuk n segitiga berbagi sisi adalah n+2, bukan n+1.
    Nilai batang dihitung ulang di sini dan dipakai sebagai label — kalau
    rumus di template berubah, ketidakcocokannya langsung kelihatan.
    """
    potong = []
    x0 = 6
    for i in range(3):
        n = i + 1
        half, y0, y1 = 20, 44, 14
        P = [(x0 + j * half, y0 if j % 2 == 0 else y1) for j in range(n + 2)]
        zig = "M " + " L ".join(f"{x} {y}" for x, y in P)
        bawah, atas = P[0::2], P[1::2]
        seg = [zig]
        for arr in (bawah, atas):
            seg += [
                f"M {a[0]} {a[1]} L {b[0]} {b[1]}" for a, b in zip(arr, arr[1:])
            ]
        jml = awal + tambah * i
        potong.append(
            f'<path d="{" ".join(seg)}" stroke="#000" stroke-width="1.6" '
            f'fill="none" stroke-linejoin="round"/>'
            f'<text x="{x0 + (n * half) / 2}" y="58" font-size="8.5" '
            f'text-anchor="middle">Gbr {n} — {jml}</text>'
        )
        x0 += (n + 1) * half + 22
    return (
        f'<svg viewBox="0 0 {x0} 64" width="100%" height="64" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(potong)}</svg>'
    )


def _svg_titik(n_tampil: int = 4) -> str:
    """Susunan titik segitiga: 1, 3, 6, 10."""
    potong, x0 = [], 10
    for n in range(1, n_tampil + 1):
        lebar = n * 13
        for baris in range(n):
            for kolom in range(baris + 1):
                cx = x0 + lebar / 2 - (baris * 13) / 2 + kolom * 13
                cy = 10 + baris * 12
                potong.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="3.4" fill="#000"/>')
        jml = n * (n + 1) // 2
        potong.append(
            f'<text x="{x0 + lebar / 2:.1f}" y="{10 + n_tampil * 12 + 6}" '
            f'font-size="8.5" text-anchor="middle">Gbr {n} — {jml}</text>'
        )
        x0 += lebar + 26
    tinggi = 10 + n_tampil * 12 + 12
    return (
        f'<svg viewBox="0 0 {x0} {tinggi}" width="100%" height="{tinggi}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(potong)}</svg>'
    )




# ── Renderer badan khusus topik ini ─────────────────────────────────────
#
# Mengembalikan HTML untuk bentuk soal yang butuh perlakuan khusus (deret
# ditebalkan, diagram SVG), atau None untuk menyerahkan ke renderer teks
# bawaan render.py. Dipanggil render.py SEBELUM renderer bawaannya.


def _badan_khusus(soal: Soal) -> str | None:
    t = soal.template_id

    if t in ("deret_aritmetika", "deret_aritmetika_turun", "deret_geometri",
             "deret_bertingkat"):
        deret = html.escape(soal.teks).replace(
            "___", '<span class="isian"></span>'
        )
        return f'<div class="teks deret">{deret}</div>'

    if t == "korek_api":
        p = soal.parameter
        svg = _svg_korek(3, p["awal"], p["tambah"])
        return (
            '<div class="teks">Segitiga dibuat dari batang korek api. '
            "Segitiga yang bersebelahan memakai batang bersama.</div>"
            f"{svg}"
            f'<div class="tanya">Gambar ke-<b>{p["gambar_ke"]}</b> '
            "butuh berapa batang?</div>"
        )

    if t == "titik_segitiga":
        return (
            '<div class="teks">Titik disusun jadi segitiga.</div>'
            f"{_svg_titik(4)}"
            f'<div class="tanya">Gambar ke-<b>{soal.parameter["gambar_ke"]}</b> '
            "punya berapa titik?</div>"
        )

    return None


# ── Pendaftaran paket ───────────────────────────────────────────────────

TOPIK = Topik(
    id="pola-bilangan",
    nama="Pola Bilangan",
    judul_lembar="Latihan Pola Bilangan",
    judul_penilaian="Penilaian — Pola Bilangan",
    templates=REGISTRI_TOPIK,
    komposisi=URUTAN_PER_LEVEL,
    profil=PROFIL_LEVEL,
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    render_badan=_badan_khusus,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)