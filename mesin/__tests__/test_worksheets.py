"""Verifikasi lembar cetak — terutama: kunci tidak bocor ke lembar anak.

Kebocoran kunci menghancurkan dua kode yang paling berharga sekaligus.
Anak yang bisa melihat jawaban tidak akan pernah mencentang "belum pernah
lihat" (T hilang) dan tidak akan terlihat menebak (N hilang) — padahal
justru dua kode itu yang tidak bisa dipulihkan dari data mana pun.

Karena itu test kebocoran di sini bersifat menyeluruh: bukan mencari kata
"kunci", tapi mencari nilai jawaban yang sebenarnya di dalam HTML.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import worksheets  # noqa: E402
from generator import buat_lembar  # noqa: E402


def teks_terlihat(html: str) -> str:
    """Buang tag, sisakan teks yang benar-benar terbaca anak.

    Atribut (path SVG, style, class) sengaja dibuang: koordinat gambar bisa
    memuat angka yang kebetulan sama dengan kunci, dan itu bukan kebocoran
    karena tidak terbaca sebagai jawaban.
    """
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


@pytest.mark.parametrize("seed", [1, 7, 42, 99, 123, 456, 789, 2026])
def test_kunci_tidak_muncul_sebagai_jawaban_di_lembar_anak(seed):
    """Kunci tidak boleh muncul DI POSISI JAWABAN pada lembar anak.

    Dibatasi ke posisi jawaban, bukan seluruh halaman, karena sebagian kunci
    memang WAJIB terlihat sebagai bagian soal: pola siklus 'A B D D' harus
    menampilkan huruf A, dan huruf ke-20 bisa jadi A. Menyembunyikannya
    membuat soal tidak bisa dikerjakan.

    Yang benar-benar berbahaya adalah kunci yang terbaca sebagai jawaban —
    di baris "Jawabanku", di tabel kode, atau di teks penjelasan. Itu yang
    diperiksa di sini: area setelah label "Jawabanku:" harus kosong.
    """
    lembar = buat_lembar(seed)
    html = worksheets.lembar_soal(list(lembar.soal), "Uji", "2026-08-24")

    # Ambil potongan setelah tiap label "Jawabanku:" sampai penutup div —
    # di lembar anak isinya harus hanya kotak isian kosong.
    for potongan in re.findall(r'class="jawab">(.*?)</div>', html, flags=re.S):
        terbaca = teks_terlihat(potongan).replace("Jawabanku:", "")
        terbaca = terbaca.replace("urutan ke-", "").replace("dan", "").strip()
        assert not terbaca, (
            f"ada teks di posisi jawaban lembar anak: {terbaca!r} — "
            "kotak isian harus kosong"
        )


@pytest.mark.parametrize("seed", [3, 17, 64, 250, 1001])
def test_kunci_angka_tidak_bocor_lewat_teks_soal(seed):
    """Untuk soal berjawab angka, kunci tidak boleh ikut tercetak di soal.

    Deret yang ditampilkan memang memuat angka, tapi tidak boleh memuat
    jawabannya. Kalau bocor, anak menyalin tanpa berpikir dan seluruh
    diagnosis jadi tidak bermakna.
    """
    lembar = buat_lembar(seed)
    for i, s in enumerate(lembar.soal, start=1):
        if s.template_id not in ("deret_aritmetika", "deret_aritmetika_turun",
                                 "deret_geometri", "deret_bertingkat"):
            continue
        badan = teks_terlihat(worksheets._badan_soal(s))
        for angka in s.kunci.replace(",", " ").split():
            assert not re.search(rf"\b{re.escape(angka)}\b", badan), (
                f"soal {i} ({s.template_id}): kunci {angka} tercetak "
                f"di deret soalnya — anak bisa menyalin"
            )


def test_kata_penanda_kunci_tidak_ada_di_lembar_anak():
    """Tidak ada label 'Kunci', 'Kode', atau tabel malrule di lembar anak."""
    lembar = buat_lembar(11)
    html = worksheets.lembar_soal(list(lembar.soal), "Uji", "2026-08-24")
    terlihat = teks_terlihat(html).lower()
    for terlarang in ("kunci", "malrule", "miskonsepsi", "salah konsep"):
        assert terlarang not in terlihat, f"kata {terlarang!r} bocor ke lembar anak"


def test_alasan_malrule_tidak_bocor_ke_lembar_anak():
    """Alasan malrule menjelaskan cara berpikir yang salah — kalau terbaca
    anak, itu memberi petunjuk jawaban."""
    lembar = buat_lembar(21)
    terlihat = teks_terlihat(worksheets.lembar_soal(list(lembar.soal), "", "")).lower()
    for s in lembar.soal:
        for m in s.malrule:
            potongan = m.alasan.lower()[:24]
            assert potongan not in terlihat


# ── Kelengkapan struktur ────────────────────────────────────────────────


def test_jumlah_kartu_soal_sesuai():
    html = worksheets.lembar_soal(list(buat_lembar(5).soal), "", "")
    assert html.count('class="soal"') == 12


def test_tiap_soal_punya_kotak_caraku_dan_centang():
    """Kotak Caraku memisahkan K dari H; centang memisahkan T dari N.
    Tanpa keduanya lembar ini tidak mendiagnosis apa pun."""
    html = worksheets.lembar_soal(list(buat_lembar(5).soal), "", "")
    assert len(re.findall(r'class="cara ', html)) == 12
    assert len(re.findall(r'class="centang"', html)) == 12


def test_restatement_dibatasi_supaya_anak_tidak_lelah_menulis():
    """Beban menulis adalah kegagalan nyata: anak berhenti karena capek, dan
    itu terlihat identik dengan tidak bisa."""
    html = worksheets.lembar_soal(list(buat_lembar(5).soal), "", "")
    n = len(re.findall(r'class="restate"', html))
    assert 5 <= n <= 8, f"{n} kotak restatement — terlalu banyak/sedikit"


def test_diagram_digambar_sebagai_svg_bukan_ascii():
    """Font monospace tidak dijamin ada di headless Chrome; seni ASCII dari
    '/' dan '\\' berubah jadi coretan tak beraturan."""
    html = worksheets.lembar_soal(list(buat_lembar(5).soal), "", "")
    assert html.count("<svg") >= 2
    assert "<pre" not in html


def test_svg_korek_api_jumlah_batangnya_benar():
    """Label pada gambar harus cocok dengan pola 3, 5, 7 — kalau tidak,
    anak melihat gambar yang bertentangan dengan soalnya."""
    from topic_number_patterns import _svg_korek

    svg = _svg_korek(3, 3, 2)
    assert "Gbr 1 — 3" in svg
    assert "Gbr 2 — 5" in svg
    assert "Gbr 3 — 7" in svg


def test_svg_titik_segitiga_jumlahnya_benar():
    from topic_number_patterns import _svg_titik

    svg = _svg_titik(4)
    for n, jml in ((1, 1), (2, 3), (3, 6), (4, 10)):
        assert f"Gbr {n} — {jml}" in svg
    # 1+3+6+10 = 20 titik
    assert svg.count("<circle") == 20


def test_lembar_penilaian_memuat_kunci_dan_malrule():
    """Kebalikan dari lembar anak: guru harus melihat semuanya."""
    lembar = buat_lembar(33)
    html = worksheets.lembar_penilaian(list(lembar.soal), "Uji", "2026-08-24", 33)
    for s in lembar.soal:
        assert s.kunci in html
    assert "Jumlah K" in html
    assert "Jangan diperlihatkan ke anak" in html


def test_lembar_penilaian_mencantumkan_seed_untuk_cetak_ulang():
    html = worksheets.lembar_penilaian(list(buat_lembar(77).soal), "A", "2026-08-24", 77)
    assert "77" in html


def test_html_utuh_dan_berbahasa_indonesia():
    html = worksheets.lembar_soal(list(buat_lembar(9).soal), "Andi", "2026-08-24")
    assert html.startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")
    assert 'lang="id"' in html
    assert "Andi" in html
