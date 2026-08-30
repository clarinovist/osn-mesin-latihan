"""Fase 1: kontrak paket topik ketiga — geometri datar (P4/P5/P6).

Paket ketiga adalah bukti kedua bahwa registry benar-benar menjadi seam
(plan 30 Aug 2026): paket baru terdaftar, komposisinya dipakai generator,
dan ia tidak mengubah paket pola-bilangan maupun aritmetika-dasar.
Keputusan pengguna: geometri-datar mulai di P4 (P3 ditunda), 10 template,
soal berbentuk teks (SVG belakangan).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topik  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topik.ambil("geometri-datar")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_geometri_datar_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "geometri-datar"
    assert paket.nama == "Geometri Datar"
    assert paket.judul_lembar == "Latihan Geometri Datar"
    assert paket.judul_penilaian == "Penilaian — Geometri Datar"


def test_geometri_datar_memulai_dengan_template_sudut():
    """Task 1.1 (kerangka): paket valid sejak template #1 #2 terisi.
    Daftar 10 template penuh diuji di Task 1.5 saat semua masuk."""
    paket = _paket()
    assert "sudut_pelurus_berpenyiku" in paket.templates
    assert "jumlah_sudut_segitiga" in paket.templates


# ── Komposisi per level (tabel plan 30 Aug 2026) ───────────────────────


def test_komposisi_p4_delapan_soal():
    komposisi = _paket().komposisi_untuk("P4")
    assert komposisi == (
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
    )


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "sudut_pelurus_berpenyiku",
        "jumlah_sudut_segitiga",
        "sudut_luar_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "luas_segiempat_lain",
        "lingkaran_keliling_luas",
        "luas_arsiran",
        "jumlah_sudut_segitiga",
        "luas_segitiga_jajargenjang",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "sudut_luar_segitiga",
        "keliling_luas_datar",
        "luas_segitiga_jajargenjang",
        "luas_segiempat_lain",
        "lingkaran_keliling_luas",
        "juring",
        "luas_arsiran",
        "perbandingan_ukuran",
        "lingkaran_keliling_luas",
        "luas_arsiran",
    )


def test_geometri_menolak_level_di_luar_scope():
    """Paket P4/P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3."""
    with pytest.raises(ValueError, match="geometri-datar"):
        buat_lembar(7, level="P3", topik="geometri-datar")
    with pytest.raises(ValueError, match="geometri-datar"):
        buat_soal("sudut_pelurus_berpenyiku", 7, level="P3", topik="geometri-datar")


# Level teks aneh -> P4 diuji di Task 1.5, saat seluruh template sudah
# ada dan buat_lembar P4 bisa dibangun penuh.


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_geometri():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Sudut",
        "B": "Bagian B — Keliling & luas",
        "C": "Bagian C — Lingkaran",
        "D": "Bagian D — Arsiran & perubahan ukuran",
    }


# ── Template kelompok sudut (#1-#3) — Task 1.2 ────────────────────────

KELOMPOK_SUDUT = ("sudut_pelurus_berpenyiku", "jumlah_sudut_segitiga", "sudut_luar_segitiga")


def test_sudut_luar_segitiga_kunci_dan_malrule():
    """#3 sudut_luar: luar = a+b (dua dalam tak bersisian)."""
    s = buat_soal("sudut_luar_segitiga", 7, level="P5", topik="geometri-datar")
    p = s.parameter
    assert s.kunci == str(p["a"] + p["b"])
    assert "Berapa besar sudut luar" in s.teks
    jawaban = [m.jawaban for m in s.malrule]
    kode = {m.kode for m in s.malrule}
    assert s.kunci not in jawaban
    assert len(jawaban) == len(set(jawaban))
    assert {"K", "H"} <= kode, kode


def test_sudut_luar_malrule_konsep_dan_hitung():
    """#3: 180-(a+b) dikira dalam (K), selisih a-b (K), kurang-1 (H)."""
    s = buat_soal("sudut_luar_segitiga", 11, level="P5", topik="geometri-datar")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert jawaban["sudut_luar.dikira_dalam"] == str(180 - p["a"] - p["b"])
    assert jawaban["sudut_luar.selisih_a_b"] == str(p["a"] - p["b"])
    assert jawaban["sudut_luar.kurang_satu"] == str(p["a"] + p["b"] - 1)


@pytest.mark.parametrize("template_id", KELOMPOK_SUDUT)
@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_kelompok_sudut_sweep_tanpa_malrule_kosong(template_id, level):
    """Tiap soal kelompok sudut punya jalur diagnosis (malrule tak kosong)."""
    if template_id == "sudut_luar_segitiga" and level == "P4":
        return  # #3 hanya P5+
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="geometri-datar")
        assert s.malrule, f"{template_id}@{level}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, (
            f"{template_id}@{level}/{seed}"
        )


def test_sudut_luar_segitiga_tidak_di_komposisi_p4():
    """#3 hanya P5+ — komposisi P4 tidak memuatnya."""
    komposisi = _paket().komposisi_untuk("P4")
    assert "sudut_luar_segitiga" not in komposisi
    # Template tetap bisa dipanggil langsung (P4 adalah level valid paket)
    s = buat_soal("sudut_luar_segitiga", 7, level="P4", topik="geometri-datar")
    assert s is not None


# ── Template keliling-luas datar (#4-#6) — Task 1.3 ───────────────────

KELOMPOK_KELILING_LUAS = (
    "keliling_luas_datar",
    "luas_segitiga_jajargenjang",
    "luas_segiempat_lain",
)


def test_keliling_luas_datar_maju_dan_balik():
    """#4: maju (K = 2(p+l)) dan balik arah (dari K cari luas)."""
    s = buat_soal("keliling_luas_datar", 7, level="P4", topik="geometri-datar")
    p = s.parameter
    assert p["varian"] in ("keliling", "balik_luas")
    if p["varian"] == "keliling":
        assert s.kunci == str(2 * (p["p"] + p["l"]))
    else:
        assert s.kunci == str(p["p"] * (p["K"] // 2 - p["p"]))
    jawaban = [m.jawaban for m in s.malrule]
    kode = {m.kode for m in s.malrule}
    assert s.kunci not in jawaban
    assert len(jawaban) == len(set(jawaban))
    assert {"K", "H"} <= kode, kode


def test_keliling_balik_minta_restatement():
    """#4 balik arah wajib minta restatement — sumber kesalahan utamanya."""
    for seed in range(1, 60):
        s = buat_soal("keliling_luas_datar", seed, level="P4", topik="geometri-datar")
        if s.parameter["varian"] == "balik_luas":
            assert s.minta_restatement is True
            return
    raise AssertionError("tidak ada satu pun soal balik_luas dalam 60 seed")


def test_keliling_luas_malrule_konsep_dan_hitung():
    """#4: tukar rumus (K), lupa bagi dua (K/H), kurang-1 (H)."""
    s = buat_soal("keliling_luas_datar", 11, level="P4", topik="geometri-datar")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    if p["varian"] == "keliling":
        assert jawaban["datar.tukar_luas"] == str(p["p"] * p["l"])
        assert jawaban["datar.kurang_satu"] == str(2 * (p["p"] + p["l"]) - 1)
    else:
        assert jawaban["datar.balik_lupa_bagi_dua"] == str(p["p"] * (p["K"] - p["p"]))
        assert jawaban["datar.balik_kurang_satu"] == str(
            p["p"] * (p["K"] // 2 - p["p"]) - 1
        )


def test_luas_segitiga_jajargenjang():
    """#5: ½·a·t (segitiga) dan a·t (jajargenjang); tinggi tegak."""
    s = buat_soal("luas_segitiga_jajargenjang", 7, level="P4", topik="geometri-datar")
    p = s.parameter
    assert p["varian"] in ("segitiga", "jajargenjang")
    if p["varian"] == "segitiga":
        assert s.kunci == str(p["a"] * p["t"] // 2)
        assert "sisi miring" in s.teks  # tinggi tegak vs sisi miring dibedakan
    else:
        assert s.kunci == str(p["a"] * p["t"])
    jawaban = [m.jawaban for m in s.malrule]
    kode = {m.kode for m in s.malrule}
    assert s.kunci not in jawaban
    assert len(jawaban) == len(set(jawaban))
    assert {"K", "H"} <= kode, kode


def test_luas_segitiga_malrule_pakai_sisi_miring():
    """#5: lupa ½ (K), pakai sisi miring sebagai tinggi (K), kurang-1 (H)."""
    for seed in range(1, 80):
        s = buat_soal("luas_segitiga_jajargenjang", seed, level="P4", topik="geometri-datar")
        if s.parameter["varian"] == "segitiga":
            p = s.parameter
            jawaban = {m.id: m.jawaban for m in s.malrule}
            assert jawaban["segitiga.lupa_setengah"] == str(p["a"] * p["t"])
            assert jawaban["segitiga.pakai_sisi_miring"] == str(p["a"] * p["s"] // 2)
            assert jawaban["segitiga.kurang_satu"] == str(p["a"] * p["t"] // 2 - 1)
            return
    raise AssertionError("tidak ada satu pun soal segitiga dalam 80 seed")


def test_luas_segiempat_lain_trapesium_ketupat_balik():
    """#6: trapesium ½(a+b)t, ketupat/layang ½d₁d₂, balik arah cari diagonal."""
    s = buat_soal("luas_segiempat_lain", 7, level="P5", topik="geometri-datar")
    p = s.parameter
    assert p["varian"] in ("trapesium", "ketupat_layang", "balik_diagonal")
    if p["varian"] == "trapesium":
        assert s.kunci == str((p["a"] + p["b"]) * p["t"] // 2)
    elif p["varian"] == "ketupat_layang":
        assert s.kunci == str(p["d1"] * p["d2"] // 2)
    else:
        assert s.kunci == str(2 * p["L"] // p["d1"])
    jawaban = [m.jawaban for m in s.malrule]
    kode = {m.kode for m in s.malrule}
    assert s.kunci not in jawaban
    assert len(jawaban) == len(set(jawaban))
    assert {"K", "H"} <= kode, kode


def test_luas_segiempat_malrule_konsep():
    """#6: lupa ½ (K), jumlah diagonal d₁+d₂ (K), lupa bagi 2 balik arah (H)."""
    s = buat_soal("luas_segiempat_lain", 11, level="P5", topik="geometri-datar")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    if p["varian"] == "ketupat_layang":
        assert jawaban["segiempat.jumlah_diagonal"] == str(p["d1"] + p["d2"])
        assert jawaban["segiempat.lupa_setengah"] == str(p["d1"] * p["d2"])
    elif p["varian"] == "balik_diagonal":
        assert jawaban["segiempat.balik_lupa_bagi_dua"] == str(p["L"] // p["d1"])


@pytest.mark.parametrize("template_id", KELOMPOK_KELILING_LUAS)
@pytest.mark.parametrize("level", ("P4", "P5", "P6"))
def test_kelompok_keliling_luas_sweep_tanpa_malrule_kosong(template_id, level):
    """Tiap soal kelompok keliling-luas punya jalur diagnosis K dan H."""
    if template_id == "luas_segiempat_lain" and level == "P4":
        return  # #6 hanya P5+
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="geometri-datar")
        assert s.malrule, f"{template_id}@{level}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, (
            f"{template_id}@{level}/{seed}"
        )


# ── Template lingkaran (#7-#8) — Task 1.4 ─────────────────────────────

KELOMPOK_LINGKARAN = ("lingkaran_keliling_luas", "juring")


def test_lingkaran_keliling_luas_maju():
    """#7: K=2πr, L=πr²; dua arah, pi 22/7 atau 3,14."""
    s = buat_soal("lingkaran_keliling_luas", 7, level="P5", topik="geometri-datar")
    p = s.parameter
    assert p["varian"] in ("keliling", "luas")
    if p["r"] % 7 == 0:
        # 22/7 → bulat
        expected = str(2 * p["r"] * 22 // 7) if p["varian"] == "keliling" else str(p["r"] ** 2 * 22 // 7)
        assert s.kunci == expected, f"{p=}, kunci={s.kunci}"
    else:
        # 3,14 → desimal 1 angka
        val = 2 * 3.14 * p["r"] if p["varian"] == "keliling" else 3.14 * p["r"] ** 2
        expected = f"{val:.1f}".replace(".", ",")
        assert s.kunci == expected, f"{p=}, kunci={s.kunci}"
    jawaban = [m.jawaban for m in s.malrule]
    kode = {m.kode for m in s.malrule}
    assert s.kunci not in jawaban
    assert len(jawaban) == len(set(jawaban))
    assert {"K", "H"} <= kode, kode


def test_lingkaran_malrule_konsep():
    """#7: pakai d di rumus luas (K), K=πr² (K), r/d tertukar (B)."""
    for seed in range(1, 80):
        s = buat_soal("lingkaran_keliling_luas", seed, level="P5", topik="geometri-datar")
        p = s.parameter
        jawaban = {m.id: m.jawaban for m in s.malrule}
        if p["varian"] == "keliling":
            assert "lingkaran.tukar_luas" in jawaban
            assert "lingkaran.pakai_diameter" in jawaban
            assert "lingkaran.kurang_satu" in jawaban
            return
        if p["varian"] == "luas":
            assert "lingkaran.pakai_diameter" in jawaban
            assert "lingkaran.tukar_keliling" in jawaban
            assert "lingkaran.kurang_satu" in jawaban
            return
    raise AssertionError("varian keliling dan luas tidak muncul dalam 80 seed")


def test_juring_luas_dan_keliling():
    """#8: L=(s/360)πr²; keliling = busur + 2r."""
    s = buat_soal("juring", 7, level="P6", topik="geometri-datar")
    p = s.parameter
    assert p["varian"] in ("luas_juring", "keliling_juring")
    r_pi = 22 / 7 if p["r"] % 7 == 0 else 3.14
    if p["varian"] == "luas_juring":
        val = p["s"] / 360 * r_pi * p["r"] ** 2
        expected = f"{val:.1f}".replace(".", ",") if val % 1 else str(int(val))
        assert s.kunci == expected
    else:
        val = p["s"] / 360 * 2 * r_pi * p["r"] + 2 * p["r"]
        expected = f"{val:.1f}".replace(".", ",") if val % 1 else str(int(val))
        assert s.kunci == expected
    jawaban = [m.jawaban for m in s.malrule]
    kode = {m.kode for m in s.malrule}
    assert s.kunci not in jawaban
    assert len(jawaban) == len(set(jawaban))
    assert {"K", "H"} <= kode, kode


def test_juring_malrule_konsep():
    """#8: lupa +2r (K), s/180 (K), pakai d (B)."""
    s = buat_soal("juring", 11, level="P6", topik="geometri-datar")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    if p["varian"] == "luas_juring":
        assert "juring.lupa_setengah_busur" in jawaban
        assert "juring.pakai_s_180" in jawaban
    else:
        assert "juring.lupa_tambah_2r" in jawaban
        assert "juring.pakai_diameter" in jawaban


@pytest.mark.parametrize("template_id", KELOMPOK_LINGKARAN)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_lingkaran_sweep_tanpa_malrule_kosong(template_id, level):
    """Tiap soal lingkaran punya K dan H."""
    if template_id == "juring" and level == "P5":
        return  # #8 hanya P6
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="geometri-datar")
        assert s.malrule, f"{template_id}@{level}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, (
            f"{template_id}@{level}/{seed}"
        )
