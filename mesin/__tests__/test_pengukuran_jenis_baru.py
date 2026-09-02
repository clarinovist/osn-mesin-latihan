"""Empat jenis soal baru untuk pengukuran — gelombang 2, langkah terakhir.

Paket `pengukuran` adalah sisa terakhir yang tercatat di README sebagai
"batas yang diketahui": P4 18 bentuk kalimat, P5/P6 21. Obatnya menambah
JENIS soal, bukan latar cerita — konversi satuan adalah perintah hitung
berbesaran, dan membungkusnya jadi cerita menambah beban baca yang bukan
sedang diuji (kebijakan yang sama dengan aritmetika-dasar di 542eb48).

Yang dikunci di sini BUKAN "template jalan", tapi:

1. kunci tiap template dihitung ULANG secara independen di test, dari
   fakta satuannya (1 lusin = 12, luas ×100, volume ×1000), bukan dengan
   memanggil fungsi yang sama;
2. ketiga jalur diagnosis (K, K, dan H/B) SELAMAT di setiap seed —
   `saring_malrule` bekerja diam-diam, jadi soal yang kehilangan jalur K
   tetap tercetak dan hanya terlihat kalau diuji;
3. batas kesahihan soal: menit selalu melewati 60 (kalau tidak, soalnya
   bisa dijawab tanpa menaikkan jam), pembagian selalu tanpa sisa, dan
   satuan tujuan tidak pernah lebih besar dari satuan terkecil;
4. ambang bentuk kalimat per level, sebagai pengunci ALASAN perubahan.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import buat_lembar, buat_soal  # noqa: E402
from topic_measurement import _KUANTITAS, _NAMA_TANAH  # noqa: E402

BARU = (
    "satuan_kuantitas",
    "tangga_satuan_campuran",
    "satuan_luas_volume",
    "jam_selesai",
)

# satuan_luas_volume dan skala_peta tidak dipakai di P4 (lihat KOMPOSISI).
LEVEL_UNTUK = {
    "satuan_kuantitas": ("P4", "P5", "P6"),
    "tangga_satuan_campuran": ("P4", "P5", "P6"),
    "satuan_luas_volume": ("P5", "P6"),
    "jam_selesai": ("P4", "P5", "P6"),
}


def _pola(teks: str) -> str:
    return re.sub(r"-?\d+(?:[.,]\d+)?", "N", teks)


def _soal(template_id: str, seed: int, level: str):
    return buat_soal(template_id, seed, level=level, topik="pengukuran")


def _seed_level(template_id: str, n: int = 120):
    for level in LEVEL_UNTUK[template_id]:
        for seed in range(1, n):
            yield seed, level


# ── Kontrak lintas keempat template ────────────────────────────────────


@pytest.mark.parametrize("template_id", BARU)
def test_ketiga_jalur_diagnosis_selamat(template_id):
    """Tiap soal WAJIB menyisakan tepat 3 malrule, dan minimal satu K.

    `saring_malrule` membuang malrule yang menebak kunci — penyelamat yang
    benar, tapi ia bekerja diam-diam. Soal yang kehilangan jalur K tetap
    sah dan tetap tercetak; anak yang salah cuma tercatat "salah" tanpa
    kode diagnosis. Dua cacat seperti ini benar-benar ditemukan saat
    menulis paket ini (satuan_kuantitas angka kecil, satuan_luas_volume
    jarak 1) dan keduanya diperbaiki di sumber parameternya.
    """
    # tangga_satuan_campuran punya empat jalur (K, K, B, H); sisanya tiga.
    # Angkanya dikunci per template, bukan dilonggarkan jadi ">= 2":
    # kalau satu jalur hilang, soalnya tetap tercetak dan tidak ada yang
    # memberi tahu — itulah kerusakan yang test ini ada untuk mencegah.
    HARAP = {"tangga_satuan_campuran": 4}
    for seed, level in _seed_level(template_id):
        s = _soal(template_id, seed, level)
        harap = HARAP.get(template_id, 3)
        assert len(s.malrule) == harap, (
            f"{template_id}@{level}/{seed}: {len(s.malrule)} malrule "
            f"({[m.jawaban for m in s.malrule]}), harusnya {harap} — "
            f"satu jalur diagnosis hilang"
        )
        kode = {m.kode for m in s.malrule}
        # Konvensi repo: minimal satu K (salah konsep) DAN satu H (salah
        # hitung). Tanpa keduanya, laporan guru tidak bisa memisahkan
        # "belum paham" dari "sudah paham tapi keliru menghitung".
        assert "K" in kode, f"{template_id}@{level}/{seed}: tanpa jalur K"
        assert "H" in kode, f"{template_id}@{level}/{seed}: tanpa jalur H"


@pytest.mark.parametrize("template_id", BARU)
def test_kunci_tidak_pernah_ditebak_malrule(template_id):
    for seed, level in _seed_level(template_id):
        s = _soal(template_id, seed, level)
        assert s.kunci not in [m.jawaban for m in s.malrule], s.parameter


@pytest.mark.parametrize("template_id", BARU)
def test_deterministik_atas_parameter(template_id):
    """Kontrak cetak ulang bank soal: parameter sama -> soal identik.

    Bank soal menyimpan parameter, bukan teks. Kalau template tidak murni
    atas parameternya, mencetak ulang lembar lama melahirkan kalimat atau
    kunci yang berbeda — guru menilai soal yang tidak dikerjakan anak.
    """
    from templates import REGISTRI

    fn = REGISTRI[template_id]
    for seed, level in _seed_level(template_id, 60):
        asli = _soal(template_id, seed, level)
        ulang = fn(**asli.parameter)
        assert ulang.teks == asli.teks, asli.parameter
        assert ulang.kunci == asli.kunci, asli.parameter


@pytest.mark.parametrize("template_id", BARU)
def test_pembahasan_menjelaskan_langkah(template_id):
    """Pembahasan dibaca ANAK, jadi ia harus menyebut langkahnya."""
    for seed, level in _seed_level(template_id, 40):
        s = _soal(template_id, seed, level)
        assert s.pembahasan.startswith("Langkah:"), s.pembahasan
        assert len(s.pembahasan) > len(s.kunci) + 20, s.pembahasan


# ── satuan_kuantitas ───────────────────────────────────────────────────


def test_satuan_kuantitas_kunci_dihitung_ulang():
    """Kunci dihitung ulang dari FAKTA satuannya, bukan dari fungsinya.

    Isi tiap satuan adalah fakta yang bisa salah ditulis sekali lalu
    terbawa ke mana-mana: 1 lusin 12, 1 kodi 20, 1 gros 144, 1 rim 500.
    Test yang memanggil fungsi yang sama tidak akan pernah menangkap
    kekeliruan itu.
    """
    ISI = {"lusin": 12, "kodi": 20, "gros": 144, "rim": 500}
    assert {k: v[0] for k, v in _KUANTITAS.items()} == ISI, (
        "isi satuan kuantitas berubah — itu fakta, bukan pilihan desain"
    )
    for seed, level in _seed_level("satuan_kuantitas"):
        s = _soal("satuan_kuantitas", seed, level)
        p = s.parameter
        isi = ISI[p["satuan"]]
        if p["arah"] == "ke_satuan":
            assert s.kunci == str(p["nilai"] * isi), p
        else:
            # Pembagian WAJIB tanpa sisa: kalau tidak, kunci dibulatkan
            # diam-diam dan anak yang menjawab sisanya tercatat salah.
            assert p["nilai"] % isi == 0, f"{p} menyisakan sisa"
            assert s.kunci == str(p["nilai"] // isi), p


def test_satuan_kuantitas_benda_cocok_dengan_satuannya():
    """"3 rim pensil" adalah fakta yang salah.

    Kodi dipakai untuk kain, rim untuk kertas, gros untuk barang kecil.
    Soal yang faktanya keliru mengajari anak hal yang keliru dan membuat
    guru ragu pada seluruh lembar.
    """
    from topic_measurement import _BENDA_KUANTITAS

    for seed, level in _seed_level("satuan_kuantitas"):
        p = _soal("satuan_kuantitas", seed, level).parameter
        assert p["benda"] in _BENDA_KUANTITAS[p["satuan"]], p


# ── tangga_satuan_campuran ─────────────────────────────────────────────


def test_tangga_kunci_dihitung_ulang_per_suku():
    """Tiap suku dikonversi SENDIRI-SENDIRI, lalu dijumlahkan.

    Ini persis miskonsepsi yang diuji soalnya, jadi test-nya menghitung
    dengan cara yang benar secara independen: 10 ** (jarak tangga) per
    suku, bukan satu faktor untuk semuanya.
    """
    from topic_measurement import _TANGGA_BERAT, _TANGGA_PANJANG

    for seed, level in _seed_level("tangga_satuan_campuran"):
        s = _soal("tangga_satuan_campuran", seed, level)
        p = s.parameter
        tangga = _TANGGA_PANJANG if p["besaran"] == "panjang" else _TANGGA_BERAT
        harap = sum(
            p[n] * 10 ** (p["tujuan"] - p[i])
            for n, i in (("a", "i1"), ("b", "i2"), ("c", "i3"))
        )
        assert s.kunci == str(harap), p
        # Satuan yang tampil harus satuan yang dipakai menghitung.
        for i in ("i1", "i2", "i3"):
            assert f" {tangga[p[i]]} " in s.teks or s.teks.endswith(
                f" {tangga[p[i]]}?"
            ), p


def test_tangga_selalu_bilangan_bulat_dan_urut_mengecil():
    """Tiga syarat kesahihan, semuanya bisa gagal diam-diam.

    1. Satuan tujuan tidak boleh lebih besar dari satuan terkecil —
       kalau lebih besar hasilnya pecahan, dan pecahan satuan punya
       banyak bentuk penulisan yang sama-sama benar sehingga kunci
       tunggal jadi tidak adil.
    2. Ketiga satuan harus BERBEDA; "2 m + 3 m + 4 m" bukan soal
       konversi sama sekali.
    3. Urut dari yang terbesar — itu cara soal ini ditulis di buku.
    """
    for seed, level in _seed_level("tangga_satuan_campuran"):
        p = _soal("tangga_satuan_campuran", seed, level).parameter
        assert p["i1"] < p["i2"] < p["i3"], p
        assert p["tujuan"] >= p["i3"], p


# ── satuan_luas_volume ─────────────────────────────────────────────────


def test_luas_volume_faktor_seratus_dan_seribu():
    """Faktornya 100 untuk luas dan 1.000 untuk volume — bukan 10.

    Inilah konsep yang sedang diuji, jadi angkanya dikunci eksplisit.
    Kalau seseorang kelak menyeragamkannya jadi 10 "supaya konsisten
    dengan satuan panjang", test ini gagal.
    """
    for seed, level in _seed_level("satuan_luas_volume"):
        s = _soal("satuan_luas_volume", seed, level)
        p = s.parameter
        faktor = 1000 if p["jenis"] == "volume" else 100
        jarak = p["i2"] - p["i1"]
        assert jarak >= 1, p
        assert s.kunci == str(p["nilai"] * faktor ** jarak), p


def test_luas_volume_malrule_faktor_sepuluh_ada():
    """Miskonsepsi terbesar topik ini WAJIB punya jalur diagnosisnya.

    Anak menghafal "turun satu tangga dikali 10" dari satuan panjang dan
    memakainya di satuan luas. Kalau jawaban itu tidak ada di tabel,
    kesalahan yang paling sering terjadi justru yang tidak terdiagnosis.
    """
    for seed, level in _seed_level("satuan_luas_volume"):
        s = _soal("satuan_luas_volume", seed, level)
        p = s.parameter
        jarak = p["i2"] - p["i1"]
        sepuluh = str(p["nilai"] * 10 ** jarak)
        assert sepuluh in [m.jawaban for m in s.malrule], (
            f"{p}: jalur 'faktor 10' hilang — itu miskonsepsi utama topik ini"
        )


def test_luas_volume_nama_tanah_hanya_untuk_indeks_yang_setara():
    """Hektar = hm2 dan are = dam2; penyebutan lain akan salah fakta."""
    assert _NAMA_TANAH == {1: "hektar", 2: "are", 3: "m²"}
    for seed, level in _seed_level("satuan_luas_volume"):
        s = _soal("satuan_luas_volume", seed, level)
        p = s.parameter
        if p["jenis"] != "tanah":
            continue
        assert p["i1"] in _NAMA_TANAH and p["i2"] in _NAMA_TANAH, p
        assert _NAMA_TANAH[p["i1"]] in s.teks, s.teks
        assert "hm²" not in s.teks and "dam²" not in s.teks, s.teks


# ── jam_selesai ────────────────────────────────────────────────────────


def test_jam_selesai_kunci_dihitung_ulang_dengan_menit_total():
    """Kunci dihitung ulang lewat menit total, bukan lewat fungsinya.

    Menghitung dalam menit total adalah cara yang jelas benar (tidak ada
    sistem 60 yang bisa keliru), jadi ia jadi acuan independen untuk
    memeriksa aritmetika jam-menit di template.
    """
    for seed, level in _seed_level("jam_selesai"):
        s = _soal("jam_selesai", seed, level)
        p = s.parameter
        mulai = p["jam"] * 60 + p["menit"]
        durasi = p["durasi_jam"] * 60 + p["durasi_menit"]
        selesai = (mulai + durasi) % (24 * 60)
        if p["varian"] == "cari_selesai":
            harap = f"{selesai // 60:02d}.{selesai % 60:02d}"
        elif p["varian"] == "cari_mulai":
            harap = f"{p['jam']:02d}.{p['menit']:02d}"
        else:
            harap = f"{durasi // 60} jam {durasi % 60} menit"
        assert s.kunci == harap, p


def test_jam_selesai_menit_selalu_melewati_enam_puluh():
    """Syarat KESAHIHAN, bukan selera.

    Kalau menit + durasi_menit <= 60, soalnya bisa dijawab benar tanpa
    pernah menaikkan menit ke jam — padahal itulah satu-satunya yang
    sedang diuji. Lebih buruk lagi, malrule "menit tidak dibawa ke jam"
    akan menebak KUNCI, sehingga anak yang benar tercatat punya
    miskonsepsi. Itu kerusakan terparah: laporan jadi tak bisa dipercaya.
    """
    for seed, level in _seed_level("jam_selesai"):
        p = _soal("jam_selesai", seed, level).parameter
        assert p["menit"] + p["durasi_menit"] > 60, p


def test_jam_selesai_kunci_tidak_pernah_menit_enam_puluh_ke_atas():
    """Jam ditulis 00.00-23.59; "14.70" adalah malrule, bukan kunci."""
    for seed, level in _seed_level("jam_selesai"):
        s = _soal("jam_selesai", seed, level)
        if s.parameter["varian"] == "cari_durasi":
            menit = int(s.kunci.split(" jam ")[1].split(" menit")[0])
        else:
            jam_t, menit_t = s.kunci.split(".")
            assert 0 <= int(jam_t) <= 23, s.kunci
            menit = int(menit_t)
        assert 0 <= menit <= 59, f"{s.parameter}: kunci {s.kunci}"


# ── Ambang bentuk kalimat: pengunci ALASAN perubahan ───────────────────

# Diukur 2 Sep 2026 dengan 300 seed, parameter yang SAMA dengan cara ukur
# di README ("Cara mengukur monoton"). Angka sebelum: P4 18, P5 21, P6 21.
AMBANG = {"P4": 60, "P5": 130, "P6": 130}


@pytest.mark.parametrize("level,ambang", sorted(AMBANG.items()))
def test_bentuk_kalimat_lewat_ambang(level, ambang):
    """Pengunci alasan, bukan mekanisme.

    Paket ini dulu tercatat di README sebagai batas yang diketahui
    (P4 18, P5/P6 21 — di bawah ambang 25). Empat jenis soal baru
    membawanya jauh melewati ambang. Angka di bawah ini adalah lantai
    yang longgar dari hasil ukur nyata (P4 67, P5 146, P6 147), bukan
    nilai persisnya: parameter yang bergeser sedikit tidak boleh
    memerahkan suite, tapi menghapus satu jenis soal harus.
    """
    bentuk = set()
    for seed in range(300):
        for s in buat_lembar(seed, level=level, topik="pengukuran").soal:
            bentuk.add(_pola(s.teks))
    assert len(bentuk) >= ambang, (
        f"pengukuran {level}: {len(bentuk)} bentuk kalimat, "
        f"di bawah lantai {ambang}"
    )


@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_semua_jenis_soal_benar_benar_dipakai(level):
    """Template terdaftar tapi tidak dipakai adalah "template tidur".

    Gelombang 1 ditutup dengan dugaan "template sudah ada, tinggal
    dipakai" dan dugaan itu terbukti salah. Test ini mencegah kebalikannya:
    menambah template lalu lupa memasukkannya ke komposisi, yang membuat
    angka metrik naik di atas kertas tanpa satu anak pun melihat soalnya.
    """
    dipakai = set()
    for seed in range(60):
        for s in buat_lembar(seed, level=level, topik="pengukuran").soal:
            dipakai.add(s.template_id)
    harus = {t for t in BARU if level in LEVEL_UNTUK[t]}
    assert harus <= dipakai, f"{level}: jenis soal tidak terpakai: {harus - dipakai}"


def test_lembar_tetap_sepuluh_soal():
    """Jumlah soal per lembar tidak boleh ikut berubah diam-diam."""
    for level in ("P4", "P5", "P6"):
        for seed in (1, 7, 42):
            assert len(buat_lembar(seed, level=level, topik="pengukuran").soal) == 10
