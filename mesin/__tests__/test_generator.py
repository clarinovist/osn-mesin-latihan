"""Verifikasi generator — kunci dihitung ulang dengan cara independen.

Prinsip yang dipegang: kunci TIDAK BOLEH dipercaya dari implementasi
template. Tiap test di sini menghitung ulang jawabannya dengan cara lain
(brute force, enumerasi, simulasi) lalu membandingkan. Kalau keduanya
sepakat, barulah kunci itu sah.

Satu kunci yang salah akan meracuni seluruh diagnosis di bawahnya —
anak dinyatakan salah padahal benar, dan miskonsepsi palsu tercatat
di laporan.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import buat_lembar, buat_soal  # noqa: E402
from templates import HARI, REGISTRI, URUTAN_LEMBAR  # noqa: E402

SEED_UJI = list(range(1, 201))


# ── Determinisme & pertumbuhan bank ─────────────────────────────────────


def test_seed_sama_menghasilkan_lembar_identik():
    """Guru harus bisa mencetak ulang lembar yang sama persis."""
    a = buat_lembar(42)
    b = buat_lembar(42)
    assert a.tanda_tangan == b.tanda_tangan
    assert [s.kunci for s in a.soal] == [s.kunci for s in b.soal]


def test_seed_berbeda_menghasilkan_soal_berbeda():
    """Inti kebutuhan: tiap generate harus keluar soal baru."""
    tanda = {buat_lembar(s).tanda_tangan for s in SEED_UJI}
    # Toleransi tabrakan kecil wajar, tapi mayoritas harus unik.
    assert len(tanda) > len(SEED_UJI) * 0.95


def test_tiap_lembar_punya_dua_belas_soal():
    lembar = buat_lembar(7)
    assert len(lembar.soal) == 12
    assert [s.template_id for s in lembar.soal] == list(URUTAN_LEMBAR)


def test_semua_template_terdaftar_di_urutan_lembar():
    """Tiap template harus terpakai di setidaknya satu level.

    Dulu ini berbunyi `set(REGISTRI) == set(URUTAN_LEMBAR)`, karena semua
    template memang muncul di satu-satunya lembar yang ada. Sejak Bagian F
    lahir, template P4+ sengaja TIDAK ada di lembar P3 — jadi yang dijaga
    sekarang: tidak ada template yatim (terdaftar tapi tak pernah dipakai),
    dan tidak ada nama di komposisi yang tidak punya implementasi.
    """
    from templates import URUTAN_PER_LEVEL

    terpakai = {t for urutan in URUTAN_PER_LEVEL.values() for t in urutan}

    yatim = set(REGISTRI) - terpakai
    assert not yatim, f"template tidak pernah dipakai di level mana pun: {yatim}"

    hantu = terpakai - set(REGISTRI)
    assert not hantu, f"komposisi menyebut template yang tidak ada: {hantu}"


# ── Kunci: dihitung ulang secara independen ─────────────────────────────


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_deret_aritmetika(seed):
    s = buat_soal("deret_aritmetika", seed)
    p = s.parameter
    # Cara independen: bangun deret penuh, ambil dua suku setelah yang tampil.
    penuh = [p["awal"] + p["beda"] * i for i in range(p["n_tampil"] + p["n_minta"])]
    harap = ", ".join(str(x) for x in penuh[p["n_tampil"] :])
    assert s.kunci == harap


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_deret_turun_tetap_positif(seed):
    s = buat_soal("deret_aritmetika_turun", seed)
    # Soal P3 tidak boleh menghasilkan bilangan negatif.
    assert int(s.kunci) >= 0


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_deret_geometri(seed):
    s = buat_soal("deret_geometri", seed)
    p = s.parameter
    nilai = p["awal"]
    for _ in range(p["n_tampil"]):  # satu langkah lebih jauh dari yang tampil
        nilai *= p["rasio"]
    assert s.kunci == str(nilai)


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_deret_bertingkat(seed):
    s = buat_soal("deret_bertingkat", seed)
    p = s.parameter
    # Simulasi langkah demi langkah, terpisah dari implementasi template.
    nilai, beda = p["awal"], p["beda_awal"]
    for _ in range(p["n_tampil"]):
        nilai += beda
        beda += p["kenaikan"]
    assert s.kunci == str(nilai)


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_siklus_huruf_dengan_enumerasi(seed):
    """Enumerasi manual — cara yang dipakai anak, tanpa pembagian."""
    s = buat_soal("siklus_huruf", seed)
    pola = list(s.parameter["pola"])
    posisi = s.parameter["posisi"]
    rantai = (pola * (posisi // len(pola) + 2))[:posisi]
    assert s.kunci == rantai[-1]


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_siklus_warna_dengan_enumerasi(seed):
    s = buat_soal("siklus_warna", seed)
    pola = list(s.parameter["pola"])
    posisi = s.parameter["posisi"]
    rantai = (pola * (posisi // len(pola) + 2))[:posisi]
    assert s.kunci == rantai[-1]


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_korek_api_dengan_penumpukan(seed):
    """Bangun satu per satu: bangun pertama utuh, sisanya berbagi batang."""
    s = buat_soal("korek_api", seed)
    p = s.parameter
    total = p["awal"]
    for _ in range(p["gambar_ke"] - 1):
        total += p["tambah"]
    assert s.kunci == str(total)


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_titik_segitiga_dengan_penjumlahan_beruntun(seed):
    """1+2+3+... — cara P3, bukan rumus n(n+1)/2."""
    s = buat_soal("titik_segitiga", seed)
    n = s.parameter["gambar_ke"]
    assert s.kunci == str(sum(range(1, n + 1)))


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_terbalik_aritmetika_target_tepat_di_deret(seed):
    """Nilai target WAJIB jatuh persis pada suku deret, bukan di antaranya."""
    s = buat_soal("deret_terbalik_aritmetika", seed)
    p = s.parameter
    deret = [p["awal"] + p["beda"] * i for i in range(40)]
    target = p["awal"] + p["beda"] * (p["posisi_target"] - 1)
    assert target in deret
    assert s.kunci == str(deret.index(target) + 1)


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_terbalik_geometri_target_tepat_di_deret(seed):
    s = buat_soal("deret_terbalik_geometri", seed)
    p = s.parameter
    deret, nilai = [], p["awal"]
    for _ in range(12):
        deret.append(nilai)
        nilai *= p["rasio"]
    target = p["awal"] * p["rasio"] ** (p["posisi_target"] - 1)
    assert target in deret
    assert s.kunci == str(deret.index(target) + 1)


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_siklus_hari_dengan_hitung_kalender(seed):
    """Maju satu hari sekali, seperti anak menghitung di kalender."""
    s = buat_soal("siklus_hari", seed)
    p = s.parameter
    idx = HARI.index(p["hari_awal"])
    for _ in range(p["tambah"]):
        idx = (idx + 1) % 7
    assert s.kunci == HARI[idx]


@pytest.mark.parametrize("seed", SEED_UJI)
def test_kunci_jumlah_siklus_dengan_penjumlahan_lurus(seed):
    """Tulis semua angka lalu jumlahkan — tanpa jalan pintas siklus."""
    s = buat_soal("jumlah_siklus", seed)
    pola = list(s.parameter["pola"])
    n = s.parameter["n_angka"]
    rantai = (pola * (n // len(pola) + 2))[:n]
    assert s.kunci == str(sum(rantai))


# ── Malrule: syarat kesehatan ───────────────────────────────────────────


@pytest.mark.parametrize("seed", SEED_UJI[:60])
def test_malrule_tidak_pernah_sama_dengan_kunci(seed):
    """Malrule yang menghasilkan jawaban benar = bug.

    Kalau sebuah malrule menebak jawaban yang sama dengan kunci, sistem
    akan menandai jawaban BENAR sebagai miskonsepsi. Ini kesalahan yang
    paling merusak kepercayaan pada laporan.
    """
    for soal in buat_lembar(seed).soal:
        for m in soal.malrule:
            assert m.jawaban != soal.kunci, (
                f"{soal.template_id}/{m.id} bertabrakan dengan kunci "
                f"{soal.kunci!r} (parameter {soal.parameter})"
            )


@pytest.mark.parametrize("seed", SEED_UJI[:60])
def test_malrule_tidak_saling_bertabrakan(seed):
    """Dua malrule berbeda tidak boleh menghasilkan jawaban sama.

    Kalau bertabrakan, satu jawaban salah memetakan ke dua kode diagnosis
    dan sistem tidak bisa memilih — diagnosisnya jadi tebakan.
    """
    for soal in buat_lembar(seed).soal:
        jawaban = [m.jawaban for m in soal.malrule]
        assert len(jawaban) == len(set(jawaban)), (
            f"{soal.template_id}: malrule bertabrakan {jawaban} "
            f"(parameter {soal.parameter})"
        )


@pytest.mark.parametrize("seed", SEED_UJI[:60])
def test_kode_malrule_hanya_dari_taksonomi(seed):
    for soal in buat_lembar(seed).soal:
        for m in soal.malrule:
            assert m.kode in {"B", "K", "H", "E", "T", "N"}


def test_tiap_template_punya_malrule_konsep():
    """Tiap tipe soal harus bisa mendeteksi minimal satu miskonsepsi.

    Metrik utama proyek ini adalah jumlah K. Template tanpa malrule K
    tidak berkontribusi ke metrik itu.
    """
    for soal in buat_lembar(3).soal:
        kode = {m.kode for m in soal.malrule}
        assert "K" in kode or "B" in kode, f"{soal.template_id} tanpa malrule K/B"


@pytest.mark.parametrize("seed", SEED_UJI)
def test_tiap_soal_selalu_bisa_mendiagnosis(seed):
    """Soal tanpa malrule sama sekali = soal yang tidak mendiagnosis apa pun.

    Ini regresi yang pernah terjadi: penyaring malrule membuang kandidat
    yang bertabrakan, dan pada kasus tepi (mis. pola siklus 'CBC' dengan
    posisi kelipatan panjang siklus) SEMUA kandidat terbuang — soal lolos
    dengan nol malrule. Jawaban salah di soal itu tidak bisa dikodekan,
    jadi soalnya cuma jadi beban menulis tanpa memberi informasi.

    Generator wajib menolak parameter semacam itu dan memilih yang lain.
    """
    for soal in buat_lembar(seed).soal:
        assert soal.malrule, (
            f"{soal.template_id} tanpa malrule sama sekali "
            f"(parameter {soal.parameter}) — tidak bisa mendiagnosis"
        )


# ── Batas kesulitan level P3 ────────────────────────────────────────────


@pytest.mark.parametrize("seed", SEED_UJI)
def test_angka_masih_terbayang_anak_p3(seed):
    """Hasil akhir numerik dijaga < 1000 supaya tetap level P3."""
    for soal in buat_lembar(seed).soal:
        for bagian in soal.kunci.replace(",", " ").split():
            if bagian.lstrip("-").isdigit():
                assert abs(int(bagian)) < 1000, (
                    f"{soal.template_id} menghasilkan {bagian} "
                    f"(parameter {soal.parameter})"
                )


@pytest.mark.parametrize("seed", SEED_UJI)
def test_soal_selalu_punya_teks_dan_kunci(seed):
    for soal in buat_lembar(seed).soal:
        assert soal.teks.strip()
        assert soal.kunci.strip()


def test_restatement_hanya_di_soal_rawan_salah_baca():
    """Beban menulis dibatasi — tidak semua soal minta restatement.

    Skill diagnostic-worksheet-authoring: anak yang lelah menulis berhenti
    mengisi kotak, dan itu terlihat identik dengan tidak bisa.
    """
    lembar = buat_lembar(11)
    n = sum(1 for s in lembar.soal if s.minta_restatement)
    assert 5 <= n <= 8, f"{n} soal minta restatement — terlalu banyak/sedikit"
