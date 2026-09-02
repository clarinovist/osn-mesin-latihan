"""Poin c feedback Filia — kartu rumus/teori singkat.

Pertanyaan Filia: "Apakah kita perlu menambahkan teori atau rumus untuk
anak pelajari, kemudian membuatkan soal lagi sesuai dengan rumus yg sudah
di pelajari?"

Keputusan desain yang dikunci di sini: kartu rumus muncul di halaman
HASIL, hanya untuk konsep yang anak BELUM tepat — bukan modul teori
terpisah yang wajib dibaca sebelum boleh berlatih. Semua benar berarti
tidak ada kartu sama sekali.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import rumus  # noqa: E402
import student_pages  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


# ── 1. Integritas pemetaan ────────────────────────────────────────────


def test_semua_template_dipetakan_itu_nyata():
    """Kunci pemetaan wajib template yang BENAR-BENAR ada di registri.

    Salah ketik nama template tidak akan meledak saat runtime (kartu
    hanya tidak muncul) — jadi harus dijaga di sini.
    """
    from templates import REGISTRI

    asing = [t for t in rumus.KONSEP_TEMPLATE if t not in REGISTRI]
    assert asing == [], f"template tidak dikenal di pemetaan: {asing}"


def test_semua_konsep_punya_kartu():
    asing = [k for k in rumus.KONSEP_TEMPLATE.values() if k not in rumus.KARTU]
    assert asing == [], f"konsep tanpa kartu: {asing}"


def test_tidak_ada_kartu_yatim():
    """Kartu yang tidak pernah dipakai = beban rawat tanpa manfaat."""
    dipakai = set(rumus.KONSEP_TEMPLATE.values())
    yatim = [k for k in rumus.KARTU if k not in dipakai]
    assert yatim == [], f"kartu tak terpakai: {yatim}"


def test_kartu_punya_judul_dan_inti():
    for nama, k in rumus.KARTU.items():
        assert k.judul.strip(), f"{nama}: judul kosong"
        assert len(k.inti.strip()) > 15, f"{nama}: inti terlalu pendek"


def test_kartu_untuk_template_tak_dipetakan_none():
    assert rumus.kartu_untuk("template_yang_tidak_ada") is None


def test_kartu_untuk_banyak_membuang_duplikat():
    """Beberapa soal salah berbagi satu konsep -> kartu tidak diulang."""
    hasil = rumus.kartu_untuk_banyak(
        ["rata_rata", "rata_rata_gabungan", "median_modus"]
    )
    judul = [k.judul for k in hasil]
    assert judul == ["Rata-rata", "Median dan Modus"]


# ── 2. Kartu di halaman hasil ─────────────────────────────────────────


def _sesi_dinilai(kon, nama, salah_semua=False):
    """Sesi pola-bilangan yang sudah dinilai & direview."""
    import reports

    sid = database.tambah_siswa(kon, nama, pemilik="guru")
    sesi_id = database.buat_sesi(kon, sid, seed=7, jumlah_soal=3,
                                 topik="pola-bilangan")
    for b in database.isi_sesi(kon, sesi_id):
        jwb = "999999" if salah_semua else b["kunci"]
        database.simpan_jawaban(kon, b["sesi_soal_id"], jawaban=jwb, cara="h")
    reports.diagnosa_murid(kon, sesi_id)
    database.tandai_selesai(kon, sesi_id)
    kon.execute("UPDATE sesi SET direview = datetime('now') WHERE id = ?",
                (sesi_id,))
    return sid, sesi_id


def test_kartu_rumus_tampil_untuk_konsep_yang_salah(db):
    with database.buka(db) as kon:
        sid, sesi_id = _sesi_dinilai(kon, "AnakSalah", salah_semua=True)
        html = student_pages.halaman_hasil_murid(kon, sid, sesi_id).decode()
    assert "Ingat rumusnya dulu" in html
    assert "rumus-kartu-st" in html
    assert "Contoh:" in html


def test_tanpa_kartu_kalau_semua_benar(db):
    """Semua benar -> jangan menyodorkan teori tanpa keperluan."""
    with database.buka(db) as kon:
        sid, sesi_id = _sesi_dinilai(kon, "AnakBenar", salah_semua=False)
        html = student_pages.halaman_hasil_murid(kon, sid, sesi_id).decode()
    badan = html.split("</style>")[-1]
    assert "Ingat rumusnya dulu" not in badan


def test_css_kartu_rumus_ada_di_gaya_murid():
    """CSS harus di GAYA_STITCH (halaman murid), bukan CSS_SESI (guru).

    Kena dua kali di sesi ini: menambah CSS di dekat blok "Cetak" membuatnya
    masuk CSS_SESI, dan halaman murid render polos tanpa gaya sama sekali.
    """
    import style_stitch

    assert "rumus-blok-st" in style_stitch.gaya_stitch()
    assert "rumus-blok-st" not in style_stitch.CSS_SESI
