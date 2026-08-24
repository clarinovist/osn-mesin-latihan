"""Generator lembar latihan — seed menentukan parameter, parameter menentukan soal.

Dipisahkan dari templates.py supaya batas kesulitan (yang perlu sering
disetel setelah melihat hasil anak) tidak bercampur dengan definisi soal
(yang jarang berubah).

Jaminan yang diuji di __tests__/test_generator.py:
  - seed sama -> lembar identik (bisa dicetak ulang persis)
  - seed beda -> parameter beda (bank soal benar-benar tumbuh)
  - tiap malrule menghasilkan jawaban != kunci (kalau sama, malrule itu bug)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from templates import HARI, REGISTRI, URUTAN_LEMBAR, Soal

WARNA = ("merah", "kuning", "hijau", "biru", "putih", "ungu")
HURUF = ("A", "B", "C", "D")


@dataclass(frozen=True)
class Lembar:
    seed: int
    soal: tuple[Soal, ...]

    @property
    def tanda_tangan(self) -> str:
        return "|".join(s.tanda_tangan for s in self.soal)


def _pola_huruf(rng: random.Random) -> tuple[str, ...]:
    """Pola dengan tepat satu huruf berulang, mis. A B B C.

    Huruf yang muncul dua kali membuat anak tidak bisa menebak dari posisi
    saja; ia harus benar-benar menghitung siklusnya.

    Dua bentuk yang sengaja dihindari:
      - semua huruf sama (AAA) — semua posisi berjawab sama, tidak
        mendiagnosis apa pun
      - semua huruf beda (ABCD) — anak bisa memetakan posisi ke huruf tanpa
        memahami siklus
    """
    panjang = rng.choice([3, 4])
    dasar = list(HURUF[:panjang])
    sumber, tujuan = rng.sample(range(panjang), 2)
    dasar[tujuan] = dasar[sumber]
    return tuple(dasar)


def _parameter(template_id: str, rng: random.Random) -> dict:
    """Batas parameter dijaga supaya soal tetap di level P3.

    Aturan yang ditegakkan di sini:
      - hasil akhir tidak negatif
      - angka hasil masih terbayang anak (< ~1000)
      - posisi target selalu jatuh TEPAT pada suku deret (bukan di antaranya)
    """
    if template_id == "deret_aritmetika":
        return {
            "awal": rng.randint(2, 12),
            "beda": rng.choice([3, 4, 5, 6, 7]),
            "n_tampil": 4,
            "n_minta": 2,
        }

    if template_id == "deret_aritmetika_turun":
        beda = rng.choice([4, 5, 6, 7, 8, 9, 11, 12])
        n_tampil = rng.choice([4, 5])
        # awal harus cukup besar supaya suku terakhir tetap positif
        awal = beda * rng.randint(n_tampil + 2, n_tampil + 8)
        return {"awal": awal, "beda": beda, "n_tampil": n_tampil}

    if template_id == "deret_geometri":
        # rasio 2 diberi porsi lebih besar: pola x2 adalah prasyarat Bagian D
        # (soal terbalik). Rasio 3 dan 4 tetap ada supaya anak tidak menghafal
        # "pola kali berarti dikali dua".
        rasio = rng.choice([2, 2, 2, 3, 3, 4])
        if rasio == 2:
            awal = rng.choice([1, 2, 3, 4, 5, 6])
            n_tampil = rng.choice([4, 5])
        elif rasio == 3:
            awal = rng.choice([1, 2, 3])
            n_tampil = 4
        else:
            awal = rng.choice([1, 2, 3])
            n_tampil = 3
        return {"awal": awal, "rasio": rasio, "n_tampil": n_tampil}

    if template_id == "deret_bertingkat":
        return {
            "awal": rng.randint(1, 9),
            "beda_awal": rng.choice([1, 2, 3, 4]),
            "kenaikan": rng.choice([1, 2, 3]),
            "n_tampil": rng.choice([5, 6]),
        }

    if template_id == "siklus_huruf":
        pola = _pola_huruf(rng)
        # Sisa 0 adalah jebakan off-by-one — pastikan sering muncul.
        posisi = rng.choice(
            [
                len(pola) * rng.randint(4, 8),  # sisa 0
                rng.randint(15, 40),
            ]
        )
        return {"pola": pola, "posisi": posisi}

    if template_id == "siklus_warna":
        n = rng.choice([3, 4])
        pola = tuple(rng.sample(WARNA, n - 1))
        pola = (pola[0],) + pola  # satu warna berulang, seperti lembar asli
        return {"pola": pola, "posisi": rng.randint(20, 45)}

    if template_id == "korek_api":
        return {
            "awal": rng.choice([3, 4, 5, 6, 7]),
            "tambah": rng.choice([2, 3, 4]),
            "gambar_ke": rng.randint(8, 20),
        }

    if template_id == "titik_segitiga":
        # T(12)=78 — masih terbayang anak P3, dan menjaga varian tetap cukup
        # banyak untuk drill mingguan.
        return {"gambar_ke": rng.randint(6, 12)}

    if template_id == "deret_terbalik_aritmetika":
        return {
            "awal": rng.randint(2, 8),
            "beda": rng.choice([3, 4, 5, 6]),
            "posisi_target": rng.randint(10, 16),
        }

    if template_id == "deret_terbalik_geometri":
        rasio = rng.choice([2, 2, 3])
        if rasio == 2:
            awal = rng.choice([2, 3, 4, 5, 6, 7])
            posisi = rng.randint(5, 7)  # 7*2^6 = 448
        else:
            awal = rng.choice([1, 2, 3])
            posisi = rng.randint(4, 5)  # 3*3^4 = 243
        return {"awal": awal, "rasio": rasio, "posisi_target": posisi}

    if template_id == "siklus_hari":
        return {
            "hari_awal": rng.choice(HARI),
            "tambah": rng.choice([16, 20, 23, 30, 40, 50, 100]),
        }

    if template_id == "jumlah_siklus":
        n = rng.choice([3, 4])
        pola = tuple(rng.sample(range(1, 6), n))
        n_angka = rng.randint(5, 12) * n + rng.randint(1, n - 1)  # sisa != 0
        return {"pola": pola, "n_angka": n_angka}

    raise KeyError(f"template tidak dikenal: {template_id}")


def buat_lembar(seed: int, urutan: tuple[str, ...] = URUTAN_LEMBAR) -> Lembar:
    """Bangun satu lembar penuh dari seed. Deterministik."""
    rng = random.Random(seed)
    soal = tuple(_soal_layak(t, rng) for t in urutan)
    return Lembar(seed=seed, soal=soal)


def _soal_layak(template_id: str, rng: random.Random, batas: int = 40) -> Soal:
    """Ambil parameter sampai dapat soal yang benar-benar bisa mendiagnosis.

    Beberapa kombinasi parameter menghasilkan soal yang sah tapi tumpul:
    seluruh malrule-nya bertabrakan dengan kunci atau satu sama lain, lalu
    dibuang oleh `saring_malrule`. Sisanya soal tanpa satu pun jalur
    diagnosis — anak tetap harus mengerjakannya, tapi jawaban salahnya tidak
    memberi tahu apa-apa. Itu beban menulis tanpa imbalan informasi.

    Contoh nyata: siklus huruf 'CBC' dengan posisi kelipatan 3. Kunci 'C',
    dan "ambil unsur terakhir siklus" juga 'C' — satu-satunya malrule
    terbuang, soal jadi kosong.

    Karena rng dipakai berurutan, penolakan tetap deterministik: seed yang
    sama menghasilkan lembar yang sama.
    """
    for _ in range(batas):
        soal = REGISTRI[template_id](**_parameter(template_id, rng))
        if soal.malrule:
            return soal
    raise RuntimeError(
        f"{template_id}: {batas} percobaan tanpa satu pun malrule bertahan — "
        "periksa definisi malrule template ini"
    )


def buat_soal(template_id: str, seed: int) -> Soal:
    """Satu soal saja — untuk menambal bank soal per tipe."""
    return _soal_layak(template_id, random.Random(seed))
