"""Empat template baru aritmetika-dasar — gelombang 2, Langkah 2.

Paket ini adalah kasus TERPARAH di seluruh aplikasi: 3000 soal P5 hanya
melahirkan 3 bentuk kalimat, dan itu terjadi di P5/P6 — level yang paling
butuh variasi.

Obat yang dipilih SENGAJA bukan latar cerita. Soalnya 100% perintah hitung
murni ("Hitung: 24 + 54 : 3 x 2 - 7"), dan itu memang bentuk yang benar
untuk melatih urutan operasi; membungkusnya jadi cerita menambah beban
baca yang bukan sedang diuji. Akar masalahnya paket ini cuma punya TIGA
template — jadi obatnya menambah jenis soal.

Empat jenis dikonfirmasi pemilik produk (keputusan kurikulum, bukan
keputusan teknis):

  urut_pecahan_desimal_persen  gap riset 28 soal OSN asli
  pecahan_kali_bagi            template lama cuma + dan -
  pembulatan_taksiran          membulatkan lalu menaksir hasil
  operasi_berkurung            kurung mendahului kali/bagi

Test di berkas ini menghitung ULANG setiap kunci secara independen dari
parameter — bukan membandingkannya dengan keluaran template, yang hanya
akan mengunci bug kalau ada.
"""

from __future__ import annotations

import re
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rumus  # noqa: E402
import topics  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402

BARU = (
    "urut_pecahan_desimal_persen",
    "pecahan_kali_bagi",
    "pembulatan_taksiran",
    "operasi_berkurung",
)


def _soal(template_id: str, seed: int, level: str = "P5"):
    return buat_soal(template_id, seed, level=level, topik="aritmetika-dasar")


# ── Registrasi ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("template_id", BARU)
def test_template_baru_terdaftar(template_id):
    assert template_id in topics.ambil("aritmetika-dasar").templates


@pytest.mark.parametrize("template_id", BARU)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_template_baru_dipakai_komposisi(template_id, level):
    """Template yang terdaftar tapi tidak dipakai = template tidur.

    Gelombang 1 selesai dengan dugaan "template sudah ada, tinggal
    dipakai" dan dugaan itu terbukti salah — tidak ada template tidur di
    paket mana pun. Test ini menjaga supaya penambahan ini tidak
    melahirkan yang pertama.
    """
    komposisi = topics.ambil("aritmetika-dasar").komposisi[level]
    assert template_id in komposisi, f"{template_id} tidak dipakai di {level}"


# ── Kunci dihitung ulang secara independen ─────────────────────────────


def test_urut_pecahan_nilai_tidak_seri():
    """Ekstrem dijaga TUNGGAL: kalau dua nilai seri sebagai yang terkecil,
    malrule "mengambil yang terbesar" bisa menebak kunci dan anak yang
    salah tercatat benar. Ini kerusakan terparah — laporan jadi tidak
    bisa dipercaya."""
    for seed in range(1, 150):
        for level in ("P5", "P6"):
            p = _soal("urut_pecahan_desimal_persen", seed, level).parameter
            nilai = [
                Fraction(p["n1"], p["d1"]),
                Fraction(p["desimal"], 100),
                Fraction(p["persen"], 100),
            ]
            assert len(set(nilai)) == 3, f"nilai seri: {p}"


def test_urut_pecahan_kunci_adalah_urutan_lengkap():
    """Kunci = ketiga bentuk, urut dari terkecil, dipisah koma.

    Dihitung ulang dari parameter secara independen — bukan dibandingkan
    dengan keluaran template, yang hanya akan mengunci bug kalau ada.
    """
    for seed in range(1, 150):
        for level in ("P5", "P6"):
            s = _soal("urut_pecahan_desimal_persen", seed, level)
            p = s.parameter
            bentuk = {
                f"{p['n1']}/{p['d1']}": Fraction(p["n1"], p["d1"]),
                f"{p['desimal'] // 100},{p['desimal'] % 100:02d}": Fraction(
                    p["desimal"], 100
                ),
                f"{p['persen']}%": Fraction(p["persen"], 100),
            }
            harap = ", ".join(
                t for t, _ in sorted(bentuk.items(), key=lambda kv: kv[1])
            )
            assert s.kunci == harap, p
            # ketiga bentuk harus tertulis di soalnya
            for t in bentuk:
                assert t.rstrip("%") in s.teks or t in s.teks, (t, s.teks)


def test_pecahan_kali_bagi_kunci():
    """Kali: n1·n2/(d1·d2). Bagi: n1·d2/(d1·n2). Dihitung ulang."""
    for seed in range(1, 150):
        for level in ("P5", "P6"):
            s = _soal("pecahan_kali_bagi", seed, level)
            p = s.parameter
            a = Fraction(p["n1"], p["d1"])
            b = Fraction(p["n2"], p["d2"])
            harap = a * b if p["op"] == "kali" else a / b
            assert s.kunci == f"{harap.numerator}/{harap.denominator}", p
            assert harap.denominator != 1, f"hasil bulat, bukan pecahan: {p}"


def test_pecahan_bagi_punya_malrule_lupa_membalik():
    """Malrule paling khas pembagian pecahan: dikali langsung tanpa
    membalik pecahan kedua. Kalau jalur ini hilang, template bagi tidak
    membawa informasi diagnosis apa pun yang tidak sudah dibawa kali."""
    ketemu = False
    for seed in range(1, 200):
        s = _soal("pecahan_kali_bagi", seed)
        if s.parameter["op"] != "bagi":
            continue
        ketemu = True
        assert any("balik" in m.id for m in s.malrule), s.parameter
    assert ketemu, "tidak ada soal bagi dalam 200 seed"


def test_pembulatan_taksiran_kunci():
    """Kunci = (a dibulatkan + b dibulatkan) ke satuan pembulatan."""
    for seed in range(1, 150):
        for level in ("P5", "P6"):
            s = _soal("pembulatan_taksiran", seed, level)
            p = s.parameter
            satuan = p["satuan"]

            def bulat(x: int) -> int:
                sisa = x % satuan
                return x - sisa if sisa * 2 < satuan else x - sisa + satuan

            harap = (
                bulat(p["a"]) + bulat(p["b"])
                if p["op"] == "tambah"
                else bulat(p["a"]) - bulat(p["b"])
            )
            assert s.kunci == str(harap), p


def test_pembulatan_tidak_ambigu_di_titik_tengah():
    """Angka yang tepat di tengah (mis. 250 dibulatkan ke ratusan) punya
    dua jawaban yang sama-sama diajarkan di sekolah. Soal seperti itu
    tidak bisa dinilai adil — parameter harus menghindarinya."""
    for seed in range(1, 300):
        for level in ("P5", "P6"):
            p = _soal("pembulatan_taksiran", seed, level).parameter
            for kunci_angka in ("a", "b"):
                sisa = p[kunci_angka] % p["satuan"]
                assert sisa * 2 != p["satuan"], f"{kunci_angka} di titik tengah: {p}"


def test_operasi_berkurung_kunci():
    """Kunci = (a+b) x c - d : e, kurung dikerjakan lebih dulu."""
    for seed in range(1, 150):
        for level in ("P5", "P6"):
            s = _soal("operasi_berkurung", seed, level)
            p = s.parameter
            harap = (p["a"] + p["b"]) * p["c"] - p["d"] // p["e"]
            assert s.kunci == str(harap), p
            assert p["d"] % p["e"] == 0, f"pembagian tidak bulat: {p}"


def test_operasi_berkurung_beda_hasil_tanpa_kurung():
    """Kalau tanpa kurung hasilnya sama, soal ini tidak menguji apa pun.

    Malrule utamanya justru "mengabaikan kurung"; kalau nilainya kebetulan
    sama dengan kunci, saring_malrule membuangnya dan template kehilangan
    satu-satunya jalur K yang membuatnya berbeda dari urutan_operasi_1.
    """
    for seed in range(1, 200):
        for level in ("P5", "P6"):
            p = _soal("operasi_berkurung", seed, level).parameter
            dengan = (p["a"] + p["b"]) * p["c"] - p["d"] // p["e"]
            tanpa = p["a"] + p["b"] * p["c"] - p["d"] // p["e"]
            assert dengan != tanpa, f"kurung tidak mengubah hasil: {p}"


# ── Kontrak wajib tiap template ────────────────────────────────────────


@pytest.mark.parametrize("template_id", BARU)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_malrule_punya_k_dan_h(template_id, level):
    """Malrule adalah jantung produk: soal tanpa K/H adalah beban menulis
    tanpa imbalan informasi."""
    for seed in range(1, 150):
        s = _soal(template_id, seed, level)
        assert s.malrule, f"{template_id}@{level}/{seed} malrule kosong"
        kode = {m.kode for m in s.malrule}
        assert {"K", "H"} <= kode, f"{template_id}@{level}/{seed}: {kode}"
        assert s.kunci not in [m.jawaban for m in s.malrule]


@pytest.mark.parametrize("template_id", BARU)
def test_punya_kartu_rumus(template_id):
    assert rumus.kartu_untuk(template_id) is not None, template_id


@pytest.mark.parametrize("template_id", BARU)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_pembahasan_menjelaskan_langkah(template_id, level):
    """Pembahasan harus menjelaskan LANGKAH, bukan mengulang jawaban."""
    for seed in range(1, 30):
        s = _soal(template_id, seed, level)
        assert s.pembahasan, f"{template_id}@{level}/{seed} pembahasan kosong"
        assert s.pembahasan.strip() != s.kunci
        # bahasa guru tidak boleh bocor: pembahasan kini dibaca anak
        for kata in ("malrule", "halaman koreksi", "miskonsepsi", "kode_final"):
            assert kata not in s.pembahasan.lower(), f"{template_id}: {kata}"


def test_pembahasan_konversi_pecahan_tidak_salah_fakta():
    """Pembahasan menulis "1/d = 0,xx" — angkanya harus BENAR.

    Ketahuan hanya dengan MEMBACA keluaran nyatanya, bukan dari test yang
    lolos: 1/8 ditulis "0,12" padahal 0,125, dan 1/3 akan jadi "0,33".
    Pembahasan kini dibaca ANAK, jadi ini bukan cacat kosmetik — mesin
    mengajarkan fakta yang salah.

    Diperbaiki di sumbernya: pecahan yang tidak habis dua angka di
    belakang koma tidak pernah dipilih jadi parameter.
    """
    for seed in range(1, 200):
        for level in ("P5", "P6"):
            s = _soal("urut_pecahan_desimal_persen", seed, level)
            p = s.parameter
            nilai = Fraction(p["n1"], p["d1"])
            assert (nilai * 100).denominator == 1, (
                f"{p['n1']}/{p['d1']} tidak habis dua angka desimal: {p}"
            )
            # angka yang ditulis di pembahasan harus sama dengan nilainya
            tertulis = f"{p['n1']}/{p['d1']} = "
            mulai = s.pembahasan.index(tertulis) + len(tertulis)
            potong = s.pembahasan[mulai:].split(",")[0:2]
            desimal = Fraction(int(potong[0]) * 100 + int(potong[1][:2]), 100)
            assert desimal == nilai, f"pembahasan salah: {s.pembahasan}"


def test_kalimat_soal_tidak_memuat_lambang_janggal():
    """"lalu hitung hasil −-nya" — lambang matematika ditempel ke akhiran.

    Ketahuan dari membaca keluaran nyatanya. Anak membaca soal yang
    bahasanya janggal dan mulai meragukan soalnya, bukan jawabannya.
    """
    for template_id in BARU:
        for seed in range(1, 120):
            for level in ("P5", "P6"):
                teks = _soal(template_id, seed, level).teks
                for lambang in ("−-", "+-", "×-", "÷-"):
                    assert lambang not in teks, f"{template_id}: {teks}"


@pytest.mark.parametrize("template_id", BARU)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_deterministik_atas_parameter(template_id, level):
    """Memanggil ulang dengan parameter yang sama harus memberi soal yang
    sama persis — kontrak cetak ulang lembar lama dari bank soal."""
    from templates import REGISTRI

    fn = REGISTRI[template_id]
    for seed in range(1, 40):
        asli = _soal(template_id, seed, level)
        ulang = fn(**asli.parameter)
        assert ulang.teks == asli.teks, asli.parameter
        assert ulang.kunci == asli.kunci
        assert [m.jawaban for m in ulang.malrule] == [
            m.jawaban for m in asli.malrule
        ]


# ── Alasan seluruh langkah ini ─────────────────────────────────────────


@pytest.mark.parametrize("level", ("P5", "P6"))
def test_ambang_bentuk_kalimat_aritmetika_dasar(level):
    """Pengunci ALASAN, bukan mekanisme. Baseline 3 bentuk kalimat.

    AMBANGNYA 11, BUKAN 25 — dan itu keputusan sadar, bukan ambang yang
    dikendurkan supaya hijau.

    Metrik "pola-kalimat unik" mengukur berapa banyak BUNYI soal yang
    berbeda. Untuk paket bercerita (kombinatorik, aritmatika-lanjut) itu
    tepat: satu template bisa melahirkan lima bunyi lewat latar berputar.
    Untuk paket ini metrik itu menabrak batas struktural — "Hitung: 5/6 +
    1/3 − 1/2" akan SELALU jadi satu pola kalimat, berapa pun angkanya,
    karena memang tidak ada kalimat untuk divariasikan. Satu template
    menyumbang tepat satu bentuk (kecuali yang punya varian), jadi
    mencapai 25 berarti menulis 25 template untuk satu paket P5/P6 —
    atau membungkus soal hitung jadi cerita, yang justru dilarang dengan
    alasan pedagogis: cerita menambah beban baca yang bukan sedang diuji.

    Jadi 3 -> 11 (naik 3,7x) adalah perbaikan sejati yang dibayar dengan
    empat jenis soal baru, dan sisanya diterima sebagai batas jujur.
    Yang mengunci mutu paket ini adalah test di bawah: berapa banyak
    JENIS SOAL yang dilatih, bukan berapa banyak bunyi kalimat.
    """
    bentuk = set()
    for seed in range(300):
        for s in buat_lembar(seed, level=level, topik="aritmetika-dasar").soal:
            bentuk.add(re.sub(r"-?\d+(?:[.,]\d+)?", "N", s.teks))
    assert len(bentuk) >= 11, (
        f"aritmetika-dasar {level} cuma {len(bentuk)} bentuk kalimat (baseline 3)"
    )


@pytest.mark.parametrize("level", ("P5", "P6"))
def test_jenis_soal_yang_dilatih_naik(level):
    """Metrik yang benar untuk paket hitung murni: berapa JENIS soal.

    Keluhan asal pemilik produk ("soalnya template semua, nanti jadi
    monoton") di paket ini bukan soal bunyi kalimat, melainkan anak
    mengerjakan tiga jenis soal yang sama berulang-ulang. Tujuh jenis
    dari tiga adalah perbaikan yang bisa dirasakan anak, dan itu yang
    dikunci di sini.
    """
    dipakai = {
        s.template_id
        for seed in range(100)
        for s in buat_lembar(seed, level=level, topik="aritmetika-dasar").soal
    }
    assert len(dipakai) >= 7, f"{level} cuma melatih {len(dipakai)} jenis (baseline 3)"


@pytest.mark.parametrize("level", ("P5", "P6"))
def test_lembar_tetap_utuh(level):
    """Komposisi baru harus tetap membangun lembar yang sah."""
    lembar = buat_lembar(7, level=level, topik="aritmetika-dasar")
    assert len(lembar.soal) >= 6
    for s in lembar.soal:
        assert s.teks and s.kunci and s.bagian
