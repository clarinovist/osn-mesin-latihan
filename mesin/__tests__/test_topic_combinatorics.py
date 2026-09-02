"""Fase 2: kontrak paket topik keempat — kombinatorik (P5/P6).

Keputusan pengguna #2: kombinatorik TEKS dulu — soal diekspos utuh dalam
teks; diagram pohon/petak/Venn jadi penyempurnaan render_badan belakangan.
11 template menutup cakupan: aturan mencacah, susun angka, permutasi &
kombinasi, dan penerapan (jabat tangan, jalur petak, sarang merpati,
inklusi-eksklusi).
"""

from __future__ import annotations

import math  # noqa: E402
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topics  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402


def _paket():
    return topics.ambil("kombinatorik")


# ── Identitas & registrasi ─────────────────────────────────────────────


def test_kombinatorik_terdaftar_dengan_identitas():
    paket = _paket()
    assert paket.id == "kombinatorik"
    assert paket.nama == "Kombinatorik"
    assert paket.judul_lembar == "Latihan Kombinatorik"
    assert paket.judul_penilaian == "Penilaian — Kombinatorik"


def test_kombinatorik_memulai_dengan_template_aturan():
    """Task 2.1 (kerangka): paket valid sejak template #1 #2 terisi."""
    paket = _paket()
    assert "aturan_tambah" in paket.templates
    assert "aturan_kali" in paket.templates


# ── Komposisi per level (tabel plan Fase 2) ────────────────────────────


def test_komposisi_p5_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P5")
    assert komposisi == (
        "aturan_tambah",
        "aturan_kali",
        "susun_bilangan",
        "susun_bilangan_syarat",
        "jabat_tangan",
        "inklusi_eksklusi_2",
        "aturan_kali",
        "susun_bilangan",
        "jabat_tangan",
        "inklusi_eksklusi_2",
    )


def test_komposisi_p6_sepuluh_soal():
    komposisi = _paket().komposisi_untuk("P6")
    assert komposisi == (
        "permutasi_urutan",
        "permutasi_blok",
        "kombinasi_pilih",
        "jalur_petak",
        "sarang_merpati",
        "susun_bilangan_syarat",
        "inklusi_eksklusi_2",
        "permutasi_urutan",
        "kombinasi_pilih",
        "jalur_petak",
    )


def test_kombinatorik_menolak_level_di_luar_scope():
    """Paket P5/P6 tidak boleh diam-diam membuat sesi untuk anak P3/P4."""
    for level in ("P3", "P4"):
        with pytest.raises(ValueError, match="kombinatorik"):
            buat_lembar(7, level=level, topik="kombinatorik")
        with pytest.raises(ValueError, match="kombinatorik"):
            buat_soal("aturan_tambah", 7, level=level, topik="kombinatorik")


# Level teks aneh -> P5 diuji di Task 2.5, saat seluruh 11 template sudah
# ada dan buat_lembar P5 bisa dibangun penuh.


# ── Judul bagian ───────────────────────────────────────────────────────


def test_judul_bagian_kombinatorik():
    paket = _paket()
    assert paket.judul_bagian == {
        "A": "Bagian A — Aturan mencacah",
        "B": "Bagian B — Susunan angka",
        "C": "Bagian C — Permutasi & kombinasi",
        "D": "Bagian D — Penerapan",
    }


# ── Template susun angka (#3-#4) — Task 2.2 ────────────────────────────

KELOMPOK_SUSUN = ("susun_bilangan", "susun_bilangan_syarat")


def _enumerasi_bilangan(angka: tuple[int, ...], panjang: int, syarat):
    """Brute force semua bilangan `panjang` digit dari angka berbeda."""
    import itertools

    hasil = 0
    for urutan in itertools.permutations(angka, panjang):
        if urutan[0] == 0:
            continue  # 0 tidak boleh di depan
        if syarat(urutan):
            hasil += 1
    return hasil


def test_susun_bilangan_kunci_dan_malrule():
    """#3: susun n angka jadi bilangan n-digit, 0 tidak boleh di depan."""
    s = buat_soal("susun_bilangan", 7, level="P5", topik="kombinatorik")
    p = s.parameter
    assert p["varian"] in ("dengan_nol", "tanpa_nol")
    angka = tuple(p["angka"])
    n = len(angka)
    # brute force = sumber kebenaran
    expected = _enumerasi_bilangan(angka, n, lambda u: True)
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_susun_bilangan_malrule_konsep():
    """#3: nol_boleh_depan (K), lupa_digit (K), kurang_satu (H)."""
    for seed in range(1, 120):
        s = buat_soal("susun_bilangan", seed, level="P5", topik="kombinatorik")
        jawaban = {m.id: m.jawaban for m in s.malrule}
        assert "susun.nol_boleh_depan" in jawaban
        assert "susun.kurang_satu" in jawaban
        if s.parameter["varian"] == "dengan_nol":
            return
    raise AssertionError("tidak ada satu pun soal dengan_nol dalam 120 seed")


def test_susun_bilangan_syarat_genap():
    """#4 varian genap: digit terakhir harus genap."""
    for seed in range(1, 120):
        s = buat_soal("susun_bilangan_syarat", seed, level="P5", topik="kombinatorik")
        p = s.parameter
        if p["varian"] != "genap":
            continue
        angka = tuple(p["angka"])
        expected = _enumerasi_bilangan(
            angka, len(angka), lambda u: u[-1] % 2 == 0
        )
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p
        return
    raise AssertionError("tidak ada satu pun soal genap dalam 120 seed")


def test_susun_bilangan_syarat_lebih_dari():
    """#4 varian lebih_dari: bilangan harus > N."""
    for seed in range(1, 120):
        s = buat_soal("susun_bilangan_syarat", seed, level="P5", topik="kombinatorik")
        p = s.parameter
        if p["varian"] != "lebih_dari":
            continue
        angka = tuple(p["angka"])
        expected = _enumerasi_bilangan(
            angka, len(angka), lambda u: int("".join(map(str, u))) > p["N"]
        )
        assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
        assert s.kunci not in [m.jawaban for m in s.malrule]
        assert {"K", "H"} <= {m.kode for m in s.malrule}, p
        return
    raise AssertionError("tidak ada satu pun soal lebih_dari dalam 120 seed")


def test_susun_bilangan_syarat_malrule_konsep():
    """#4: abaikan_syarat (K), syarat_terbalik (K), kurang_satu (H)."""
    s = buat_soal("susun_bilangan_syarat", 11, level="P5", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert "susun_syarat.abaikan_syarat" in jawaban
    assert "susun_syarat.syarat_terbalik" in jawaban
    assert "susun_syarat.kurang_satu" in jawaban


@pytest.mark.parametrize("template_id", KELOMPOK_SUSUN)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_susun_sweep_tanpa_malrule_kosong(template_id, level):
    """Tiap soal susun angka punya K dan H."""
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="kombinatorik")
        assert s.malrule, f"{template_id}@{level}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, (
            f"{template_id}@{level}/{seed}"
        )


# ── Template permutasi & kombinasi (#5-#7) — Task 2.3 ─────────────────

KELOMPOK_PERMUTASI = ("permutasi_urutan", "permutasi_blok", "kombinasi_pilih")


def _enumerasi_permutasi(hingga_n: int, r: int) -> int:
    """P(n,r) dengan enumerasi (sumber kebenaran)."""
    import itertools

    return sum(1 for _ in itertools.permutations(range(hingga_n), r))


def test_permutasi_urutan_kunci_dan_malrule():
    """#5: P(n,r) = n!/(n−r)! — urutan penting."""
    s = buat_soal("permutasi_urutan", 7, level="P6", topik="kombinatorik")
    p = s.parameter
    expected = _enumerasi_permutasi(p["n"], p["r"])
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_permutasi_urutan_malrule_konsep():
    """#5: kombinasi tertukar (K), boleh ulang (K), kurang_satu (H)."""
    s = buat_soal("permutasi_urutan", 11, level="P6", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert jawaban["permutasi.tertukar_kombinasi"] == str(math.comb(p["n"], p["r"]))
    assert "permutasi.boleh_ulang" in jawaban
    assert "permutasi.kurang_satu" in jawaban


def test_permutasi_blok_kunci_dan_malrule():
    """#6: n benda, k berdampingan → (n−k+1)!×k!."""
    s = buat_soal("permutasi_blok", 7, level="P6", topik="kombinatorik")
    p = s.parameter
    expected = math.factorial(p["n"] - p["k"] + 1) * math.factorial(p["k"])
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_permutasi_blok_malrule_konsep():
    """#6: hanya blok (K), hanya isi blok (K), kurang_satu (H)."""
    s = buat_soal("permutasi_blok", 11, level="P6", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert "blok.abaikan_isi_blok" in jawaban
    assert "blok.hanya_isi_blok" in jawaban
    assert "blok.kurang_satu" in jawaban


def test_kombinasi_pilih_kunci_dan_malrule():
    """#7: C(n,r) = n!/(r!(n−r)!) — urutan tidak penting."""
    s = buat_soal("kombinasi_pilih", 7, level="P6", topik="kombinatorik")
    p = s.parameter
    assert s.kunci == str(math.comb(p["n"], p["r"])), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_kombinasi_malrule_konsep():
    """#7: permutasi tertukar (K), 2^n dikira (K), kurang_satu (H)."""
    s = buat_soal("kombinasi_pilih", 11, level="P6", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert jawaban["kombinasi.tertukar_permutasi"] == str(
        math.perm(p["n"], p["r"])
    )
    assert "kombinasi.dikira_2_pangkat" in jawaban
    assert "kombinasi.kurang_satu" in jawaban


@pytest.mark.parametrize("template_id", KELOMPOK_PERMUTASI)
def test_kelompok_permutasi_sweep_tanpa_malrule_kosong(template_id):
    """Tiap soal permutasi/kombinasi punya K dan H (P6)."""
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level="P6", topik="kombinatorik")
        assert s.malrule, f"{template_id}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, (
            f"{template_id}/{seed}"
        )


# ── Template penerapan (#8-#11) — Task 2.4 ────────────────────────────

KELOMPOK_PENERAPAN = (
    "jabat_tangan", "jalur_petak", "sarang_merpati", "inklusi_eksklusi_2"
)


def test_jabat_tangan_kunci_dan_malrule():
    """#8: n orang jabat tangan → n(n−1)/2."""
    s = buat_soal("jabat_tangan", 7, level="P5", topik="kombinatorik")
    p = s.parameter
    expected = p["n"] * (p["n"] - 1) // 2
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_jabat_tangan_malrule_konsep():
    """#8: lupa_bagi_2 (K), jabat_diri (K), kurang_satu (H)."""
    s = buat_soal("jabat_tangan", 11, level="P5", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert jawaban["jabat.lupa_bagi_2"] == str(p["n"] * (p["n"] - 1))
    assert jawaban["jabat.jabat_diri"] == str(p["n"])
    assert jawaban["jabat.kurang_satu"] == str(p["n"] * (p["n"] - 1) // 2 - 1)


def test_jalur_petak_kunci_dan_malrule():
    """#9: petak m×n → C(m+n, m) jalur."""
    s = buat_soal("jalur_petak", 7, level="P6", topik="kombinatorik")
    p = s.parameter
    expected = math.comb(p["b"] + p["k"], p["b"])
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_jalur_petak_malrule_konsep():
    """#9: dua_arah (K), jumlah_step (K), kurang_satu (H)."""
    s = buat_soal("jalur_petak", 11, level="P6", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert "jalur.dua_arah" in jawaban
    assert "jalur.jumlah_step" in jawaban
    assert "jalur.kurang_satu" in jawaban


def test_sarang_merpati_kunci_dan_malrule():
    """#10: n benda → m laci → minimal ceil(n/m) sama."""
    s = buat_soal("sarang_merpati", 7, level="P6", topik="kombinatorik")
    p = s.parameter
    expected = (p["n"] + p["m"] - 1) // p["m"]
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_sarang_merpati_malrule_konsep():
    """#10: dibulatkan_bawah (K), kurang_satu (K), kelebihan_satu (H)."""
    s = buat_soal("sarang_merpati", 11, level="P6", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert "merpati.dibulatkan_bawah" in jawaban
    assert "merpati.kelebihan_satu" in jawaban


def test_inklusi_eksklusi_kunci_dan_malrule():
    """#11: |A∪B| = a + b − c."""
    s = buat_soal("inklusi_eksklusi_2", 7, level="P5", topik="kombinatorik")
    p = s.parameter
    expected = p["a"] + p["b"] - p["c"]
    assert s.kunci == str(expected), f"{p=}, kunci={s.kunci}"
    assert s.kunci not in [m.jawaban for m in s.malrule]
    assert {"K", "H"} <= {m.kode for m in s.malrule}, p


def test_inklusi_eksklusi_malrule_konsep():
    """#11: lupa_irisan (K), dikali (K), jawab_irisan (B), kurang_satu (H)."""
    s = buat_soal("inklusi_eksklusi_2", 11, level="P5", topik="kombinatorik")
    p = s.parameter
    jawaban = {m.id: m.jawaban for m in s.malrule}
    assert jawaban["inklusi.lupa_irisan"] == str(p["a"] + p["b"])
    assert "inklusi.dikali" in jawaban
    assert "inklusi.kurang_satu" in jawaban


@pytest.mark.parametrize("template_id", KELOMPOK_PENERAPAN)
@pytest.mark.parametrize("level", ("P5", "P6"))
def test_kelompok_penerapan_sweep_tanpa_malrule_kosong(template_id, level):
    """Tiap soal penerapan punya K dan H."""
    if template_id in ("jalur_petak", "sarang_merpati") and level == "P5":
        return  # #9, #10 hanya P6
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="kombinatorik")
        assert s.malrule, f"{template_id}@{level}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, (
            f"{template_id}@{level}/{seed}"
        )


# ── Latar cerita berputar (2 Sep 2026) ─────────────────────────────────


def test_latar_berputar_menambah_bentuk_kalimat_p5():
    """Empat template P5 dulu punya SATU cerita yang ditulis mati.

    Terukur 2 Sep 2026: 3000 soal kombinatorik P5 hanya melahirkan 14
    bentuk kalimat, dan aturan_tambah/aturan_kali/jabat_tangan/
    inklusi_eksklusi_2 menyumbang tepat 1 bentuk masing-masing — anak
    hafal bunyi soalnya sebelum hafal caranya.
    """
    import re

    from generator import buat_lembar

    bentuk = set()
    for seed in range(300):
        for s in buat_lembar(seed, level="P5", topik="kombinatorik").soal:
            bentuk.add(re.sub(r"-?\d+", "N", s.teks))
    assert len(bentuk) >= 25, (
        f"kombinatorik P5 cuma {len(bentuk)} bentuk kalimat (baseline 14)"
    )


@pytest.mark.parametrize(
    "template_id",
    ("aturan_tambah", "aturan_kali", "jabat_tangan", "inklusi_eksklusi_2"),
)
def test_template_berlatar_punya_lebih_dari_satu_cerita(template_id):
    import re

    bentuk = {
        re.sub(r"-?\d+", "N", buat_soal(
            template_id, seed, level="P5", topik="kombinatorik"
        ).teks)
        for seed in range(1, 200)
    }
    assert len(bentuk) >= 3, f"{template_id}: cuma {len(bentuk)} cerita"


@pytest.mark.parametrize(
    "template_id",
    ("aturan_tambah", "aturan_kali", "jabat_tangan", "inklusi_eksklusi_2"),
)
def test_latar_deterministik_atas_parameter(template_id):
    """Latar HARUS turunan parameter, bukan rng atau hash() bawaan.

    Kalau tidak, mencetak ulang lembar lama dari bank soal (parameter
    sama, proses berbeda) melahirkan kalimat yang berbeda — guru menilai
    soal yang tidak dikerjakan anak.
    """
    from templates import REGISTRI

    fn = REGISTRI[template_id]
    for seed in range(1, 40):
        asli = buat_soal(template_id, seed, level="P5", topik="kombinatorik")
        ulang = fn(**asli.parameter)
        assert ulang.teks == asli.teks, asli.parameter
        assert ulang.kunci == asli.kunci


def test_latar_tidak_menambah_parameter():
    """Parameter ikut tanda_tangan: menambah kunci 'latar' akan
    membatalkan seluruh bank soal dan snapshot golden."""
    for template_id, diharap in (
        ("aturan_tambah", {"m", "n"}),
        ("aturan_kali", {"m", "n"}),
        ("jabat_tangan", {"n"}),
        ("inklusi_eksklusi_2", {"a", "b", "c"}),
    ):
        s = buat_soal(template_id, 5, level="P5", topik="kombinatorik")
        assert set(s.parameter) == diharap, s.parameter
