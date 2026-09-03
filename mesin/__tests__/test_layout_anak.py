"""Layout halaman /anak/<id> — regresi CSS (audit 3 Sep 2026).

Halaman ini dirender ke Chrome headless lalu geometri tiap elemen diukur di
viewport 1440px dan 390px. Tiga bug ditemukan; test di sini menguncinya
supaya tidak kembali saat CSS dirapikan lagi.

B1  `.strip-sesi` terdefinisi DUA KALI di GAYA_STITCH. Definisi lama (strip
    satu baris) membawa `align-items: flex-end`; definisi S6 mengubah arah
    jadi kolom tapi tidak me-reset align-items, sehingga setiap anak yang
    tidak selebar penuh menempel ke tepi KANAN. Terukur di 1440px: kolom
    "Jumlah Soal" di x=866 dan "Mode Sesi" di x=744, sementara tombol di
    x=383 — form terlihat miring.

B2  Media query layar sempit memakai selector `.st-kartu-baris > span`.
    Kartu sesi di halaman GURU anaknya <div>, jadi aturan itu tidak pernah
    kena; di 390px kolom pertama menyusut ke 76px dan judul sesi terlipat
    tiga baris.

B3  `.daftar-anak` hanya ada di GAYA_GURU, yang TIDAK dimuat oleh
    `_halaman_stitch`. Grid+gap hilang dan kartu sesi dempet — jarak
    terukur 1px, bukan 1.2rem.

Test membaca STRING CSS, bukan browser: sama seperti test gaya lain di repo
ini, supaya cepat dan tanpa dependensi luar.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import student_pages  # noqa: E402
import teacher_pages  # noqa: E402
from style_stitch import GAYA_STITCH  # noqa: E402


def _blok(css: str, selektor: str) -> str:
    """Isi blok CSS pertama untuk `selektor`, tanpa kurung kurawal luar."""
    cocok = re.search(re.escape(selektor) + r"\s*\{(.*?)\}", css, re.S)
    assert cocok, f"selektor {selektor} tidak ada di GAYA_STITCH"
    return _tanpa_komentar(cocok.group(1))


def _tanpa_komentar(css: str) -> str:
    """Buang komentar /* ... */.

    Komentar di file ini MENJELASKAN bug (menyebut `align-items:flex-end`),
    jadi assert yang polos ikut menangkap penjelasannya dan gagal padahal
    aturannya sudah benar.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _tanpa_gaya(html: str) -> str:
    """Buang isi <style>…</style>.

    Halaman meng-inline SELURUH GAYA_STITCH, jadi memeriksa nama kelas di
    HTML mentah selalu menemukannya di CSS — bukan bukti bahwa MARKUP-nya
    memakai kelas itu.
    """
    return re.sub(r"<style>.*?</style>", "", html, flags=re.S)


def _jumlah_definisi(css: str, selektor: str) -> int:
    """Berapa kali `selektor` dideklarasikan sendirian di awal baris."""
    return len(re.findall(r"^" + re.escape(selektor) + r"\s*\{", css, re.M))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


@pytest.fixture()
def anak(db):
    """Satu anak dengan dua sesi — cukup untuk merender halaman utuh."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Claudia", pemilik="ortu", tingkat="P3")
        database.buat_sesi(kon, sid, seed=11, topik="statistika")
        database.buat_sesi(kon, sid, seed=17, topik="geometri-datar")
    return db, sid


def _render_anak(db, siswa_id) -> str:
    with database.buka(db) as kon:
        baris = kon.execute(
            "SELECT * FROM siswa WHERE id = ?", (siswa_id,)
        ).fetchone()
        return teacher_pages.halaman_anak(
            kon, baris, peran="guru", pengguna="ortu"
        ).decode()


# ── B1 — strip-sesi: satu definisi, rata kiri ─────────────────────────


def test_strip_sesi_hanya_satu_definisi():
    """Dua blok `.strip-sesi` = properti blok lama bocor ke blok kolom."""
    assert _jumlah_definisi(GAYA_STITCH, ".strip-sesi") == 1


def test_mode_pilih_dan_mode_opsi_hanya_satu_definisi():
    """Sisa refactor S6 yang sama: keduanya sempat ganda."""
    assert _jumlah_definisi(GAYA_STITCH, ".mode-pilih") == 1
    assert _jumlah_definisi(GAYA_STITCH, ".mode-opsi") == 1


def test_strip_sesi_tidak_rata_kanan():
    """`align-items: flex-end` pada container KOLOM melempar semua anak
    ke tepi kanan — inilah penyebab form terlihat miring."""
    assert "flex-end" not in _blok(GAYA_STITCH, ".strip-sesi")


def test_strip_sesi_menegakkan_align_items_stretch():
    """Ditulis eksplisit meski itu nilai default: yang dijaga di sini
    adalah TIDAK adanya warisan flex-end kalau blok lama muncul lagi."""
    blok = _blok(GAYA_STITCH, ".strip-sesi")
    assert "flex-direction: column" in blok
    assert "align-items: stretch" in blok


def test_select_dalam_strip_dibatasi_lebarnya():
    """Tanpa batas, dropdown melar selebar kartu (673px) di desktop."""
    assert ".strip-sesi select.st-input" in GAYA_STITCH


# ── B2 — media query kartu mengenai div, bukan hanya span ─────────────


def test_media_query_kartu_tidak_hanya_menyasar_span():
    """Kartu guru memakai <div>, kartu murid memakai <span>. Selector
    `> span` membuat aturan HP hanya berlaku untuk kartu murid."""
    aturan = _tanpa_komentar(GAYA_STITCH)
    assert ".st-kartu-baris > *" in aturan
    assert ".st-kartu-baris > span" not in aturan


def test_aturan_baris_penuh_dibatasi_ke_kartu_guru():
    """Anak pertama kartu MURID adalah ikon bulat 2.5rem yang harus tetap
    `flex: none`. Aturan "ambil baris penuh" karena itu tidak boleh
    digeneralkan ke .st-kartu-baris, melainkan pakai kelas sendiri."""
    assert ".kartu-sesi-guru" in GAYA_STITCH


def test_kartu_guru_memakai_kelas_penanda_di_markup(anak):
    """CSS tanpa markup yang memakainya = aturan mati."""
    db, sid = anak
    markup = _tanpa_gaya(_render_anak(db, sid))
    assert "kartu-sesi-guru" in markup


def test_kartu_murid_tidak_memakai_kelas_guru(anak):
    """Kelas penanda tidak boleh bocor ke kartu murid — beda struktur."""
    db, sid = anak
    with database.buka(db) as kon:
        html = student_pages.halaman_daftar_sesi_baru(
            kon, sid, nama="Claudia"
        ).decode()
    markup = _tanpa_gaya(html)
    assert "st-kartu-baris" in markup, "fixture harus benar-benar punya kartu"
    assert "kartu-sesi-guru" not in markup


# ── B3 — daftar-anak butuh gaya di halaman Stitch ─────────────────────


def test_daftar_anak_punya_gaya_di_stitch():
    """_halaman_stitch tidak memuat GAYA_GURU, jadi grid+gap harus ada di
    GAYA_STITCH — kalau tidak, kartu sesi dempet 1px."""
    blok = _blok(GAYA_STITCH, ".daftar-anak")
    assert "grid" in blok
    assert "gap" in blok


# ── Guard anti-regresi ────────────────────────────────────────────────


def test_halaman_anak_tetap_utuh(anak):
    db, sid = anak
    html = _render_anak(db, sid)
    assert "Sesi #" in html
    assert "Buat sesi baru" in html
    assert "Buat latihan gabungan" in html
    assert "Claudia" in html
