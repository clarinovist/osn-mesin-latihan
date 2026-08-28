"""Kontrak Fase 3: satu sumber render, dua tampilan.

render.py memegang struktur DOM; gaya_layar.py dan gaya_cetak.py memegang
CSS. Yang dijaga di sini:

  1. Struktur DOM identik di kedua tampilan — kalau tidak, test kebocoran
     kunci yang ditulis sekali untuk struktur itu tidak lagi menjamin
     kedua tampilan sekaligus.
  2. Lembar web (gaya layar) juga tidak memuat kunci — palang yang sama
     berlaku untuk tampilan mana pun yang sampai ke layar anak.
  3. Gaya cetak tetap memuat dua riwayat gagal yang mengikat: SVG-tile
     untuk garis panduan. Gradient pernah menghilang total di PDF.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gaya_cetak import GAYA_CETAK  # noqa: E402
from gaya_layar import GAYA_LAYAR  # noqa: E402
from generator import buat_lembar, buat_soal  # noqa: E402
from render import lembar_penilaian, lembar_soal  # noqa: E402


def _dom(html: str) -> str:
    """Struktur DOM tanpa isi CSS: buang <style>, tag jadi pohon bersih."""
    html = re.sub(r"<style>.*?</style>", "<style/>", html, flags=re.S)
    html = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    html = re.sub(r">\s+<", "><", html)
    return html


def test_struktur_dom_identik_di_kedua_tampilan():
    """Satu sumber harus benar-benar satu sumber.

    Kalau DOM-nya beda, perubahan struktur hanya menyentuh satu tampilan dan
    test kontrak (kebocoran kunci, jumlah kartu) diam-diam berhenti mewakili
    tampilan lainnya.
    """
    lb = buat_lembar(42, level="P6")
    cetak_dom = _dom(lembar_soal(lb.soal, "Anak", "2026", gaya=GAYA_CETAK))
    layar_dom = _dom(lembar_soal(lb.soal, "Anak", "2026", gaya=GAYA_LAYAR))
    assert cetak_dom == layar_dom

    cetak_guru = _dom(
        lembar_penilaian(lb.soal, "Anak", "2026", seed=42, gaya=GAYA_CETAK)
    )
    layar_guru = _dom(
        lembar_penilaian(lb.soal, "Anak", "2026", seed=42, gaya=GAYA_LAYAR)
    )
    assert cetak_guru == layar_guru


def test_kunci_tidak_bocor_di_tampilan_layar():
    """Palang yang sama untuk lembar web — ia juga sampai ke mata anak.

    Aturan sama dengan test_cetak.py: kunci yang memang bagian dari soal
    (angka deret, huruf siklus) wajib terlihat; yang dilarang adalah kunci
    di POSISI JAWABAN. Area setelah "Jawabanku:" harus kosong.
    """
    for seed in (3, 17, 250):
        lb = buat_lembar(seed, level="P5")
        html = lembar_soal(lb.soal, gaya=GAYA_LAYAR)
        for potongan in re.findall(r'class="jawab">(.*?)</div>', html, flags=re.S):
            terbaca = potongan
            terbaca = re.sub(r"<[^>]+>", " ", terbaca)
            terbaca = (
                terbaca.replace("Jawabanku:", "")
                .replace("urutan ke-", "")
                .replace("dan", "")
                .strip()
            )
            assert not terbaca, (
                f"seed {seed}: ada teks di posisi jawaban: {terbaca!r}"
            )


def test_gaya_cetak_menjaga_riwayat_gagal_garis_panduan():
    """SVG-tile adalah satu-satunya cara garis panduan yang terbukti bekerja.

    Dua kali gagal dengan gradient (hilang di PDF; cuma satu garis saat
    dicetak). Kalau seseorang menggantinya lagi, komentar riwayatnya saja
    tidak cukup — ini yang membuat penggantian sadar.
    """
    assert "background-image" in GAYA_CETAK
    assert "svg+xml" in GAYA_CETAK, (
        "garis panduan kotak Caraku harus SVG data-URI, bukan gradient — "
        "dua kali sudah gagal, lihat komentar gaya_cetak.py"
    )
    assert "repeating-linear-gradient" not in GAYA_CETAK
    assert "print-color-adjust" in GAYA_CETAK
    assert "@page" in GAYA_CETAK and "A4" in GAYA_CETAK


def test_gaya_layar_tanpa_satuan_mm_dan_punya_target_sentuh():
    """Lembar web dibaca di HP: mm tidak bermakna di layar, sentuhan butuh
    area cukup besar (~44px)."""
    # @page dan page-break adalah urusan kertas; kalau muncul di sini,
    # dua gaya mulai saling menimpa tanggung jawab
    assert "@page" not in GAYA_LAYAR.split("@media print")[0]
    assert "min-height: 44px" in GAYA_LAYAR  # target sentuh .centang
    assert "viewport" in lembar_soal(buat_lembar(1).soal, gaya=GAYA_LAYAR)


def test_fasad_cetak_tetap_mengekspor_nama_lama():
    """Pemanggil lama (buat_lembar.py CLI, web.py, test lama) memakai
    `cetak.lembar_soal` dst. Pemecahan modul tidak boleh mematahkan mereka."""
    import cetak

    assert cetak.lembar_soal is lembar_soal
    assert cetak.lembar_penilaian is lembar_penilaian
    assert cetak.CSS is GAYA_CETAK
    assert hasattr(cetak, "_badan_soal")
    # Diagram SVG kini milik paket topik, bukan renderer
    from topik_pola_bilangan import _svg_korek  # noqa: F401


def test_soal_bagian_f_terender_dengan_kotak_caraku_besar():
    """Soal Bagian F menuntut coretan rumus, bukan sekadar angka jawaban —
    kotak Caraku-nya minimal sedang, apa pun levelnya."""
    from templates import LEVEL

    for lv in ("P4", "P5", "P6"):
        lb = buat_lembar(7, level=lv)
        pasangan = list(zip(lb.soal, _kartu_tinggi(lembar_soal(lb.soal))))
        for s, tinggi in pasangan:
            if s.bagian == "F":
                assert tinggi in ("sedang", "besar"), (
                    f"{lv}/{s.template_id}: kotak Caraku {tinggi}"
                )


def _kartu_tinggi(html: str) -> list[str]:
    return re.findall(r'class="cara ?(\w*)"?>', html)
