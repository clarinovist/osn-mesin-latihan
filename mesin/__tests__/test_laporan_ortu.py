"""Laporan ramah orang tua — ringkasan, kamus kode, detail teknis.

Bahasa teknis (B/K/H/E/T/N, miskonsepsi, malrule) membingungkan orang tua:
laporan kini dibuka dengan ringkasan 3 kalimat + kamus arti nilai, dan
tabel teknisnya dilipat di <details> (tetap ada untuk guru).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import reports  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    import auth

    berkas = tmp_path / "sandi.json"
    monkeypatch.setattr(auth, "BERKAS_SANDI", berkas)
    auth.simpan_sandi("sandi-lama-panjang", "guru", berkas)
    d = tmp_path / "uji.db"
    database.siapkan(d)
    return d


def _sesi_dinilai(kon, sid, benar=8, jumlah=10, kode="K"):
    """Satu sesi berisi + diagnosis manual, tanpa lewat HTTP."""
    import teacher_pages

    sesi_id = database.buat_sesi(kon, sid, seed=jumlah * 100 + benar)
    isi = database.isi_sesi(kon, sesi_id)
    data = {}
    for i, b in enumerate(isi[:jumlah]):
        if i < benar:
            data[f"jwb_{b['sesi_soal_id']}"] = b["kunci"]
            data[f"cara_{b['sesi_soal_id']}"] = "coretan"
        else:
            data[f"jwb_{b['sesi_soal_id']}"] = "pasti salah"
            data[f"cara_{b['sesi_soal_id']}"] = "coretan"
            data[f"kode_{b['sesi_soal_id']}"] = kode
    teacher_pages.simpan_sesi(kon, sesi_id, data)
    return sesi_id


def test_ringkasan_ortu_menyebut_nama_dan_kondisi(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Bima")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        _sesi_dinilai(kon, sid, benar=7, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Ringkasan untuk orang tua" in h
    assert "Bima" in h
    assert "perlu dilatih" in h.lower() or "konsep" in h.lower()


def test_ringkasan_merayakan_tanpa_kata_teknis(db):
    """K=0: kalimat perayaan, tanpa kata yang menakuti (miskonsepsi).

    CSS global ikut ter-render di <style> (kata "diagnosis" ada di nama
    kelas), jadi yang dicek hanya ISI laporan — setelah </style>.
    """
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Rara")
        _sesi_dinilai(kon, sid, benar=10, jumlah=10)
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Ringkasan untuk orang tua" in h
    isi = h.split("</style>", 1)[1]
    assert "miskonsepsi" not in isi.lower()
    assert "malrule" not in isi.lower()


def test_kamus_tanpa_jargon(db):
    """Enam kode dijelaskan bahasa sehari-hari, tanpa kata teknis.

    Seperti test di atas: CSS ikut ter-render, jadi cek isi saja.
    """
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Kamus")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Arti nilai anak" in h
    for kata in ("salah konsep", "salah baca", "salah hitung",
                 "salah tulis", "belum pernah", "menebak"):
        assert kata in h.lower(), f"kamus kehilangan '{kata}'"
    # kamus & ringkasan bebas jargon teknis
    atas = h.split("</style>", 1)[1].split("Detail per sesi")[0]
    assert "malrule" not in atas.lower()
    assert "miskonsepsi" not in atas.lower()


def test_topik_tampil_nama_ramah(db):
    """Id teknis (pola-bilangan) tampil sebagai nama ramah (Pola Bilangan)."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Topik")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Pola Bilangan" in h


def test_kartu_perhatian_tidak_bilang_kuat_saat_ada_k(db):
    """Regresi dari screenshot: ringkasan bilang 6 K tapi kartu bilang
    'belum ada kekeliruan' — K manual tanpa malrule tak masuk miskonsepsi."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Kontradiksi")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    isi = h.split("</style>", 1)[1].split("Detail per sesi")[0]
    assert "Belum ada kekeliruan" not in isi
    assert "kekeliruan konsep" in isi


def test_tabel_teknis_dilipat_tapi_tetap_ada(db):
    """Guru tetap dapat tabelnya: markup utuh di dalam <details>."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Lipat")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "<details" in h
    assert "<th>Topik</th>" in h
    assert h.index("<details") < h.index("<th>Topik</th>")


def test_topik_tak_dikenal_tidak_500(db):
    """Sesi warisan ber-topik asing: laporan tetap 200, tampil apa adanya."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Warisan")
        sesi_id = database.buat_sesi(kon, sid, seed=5)
        kon.execute("UPDATE sesi SET topik = ? WHERE id = ?", ("topik-hantu", sesi_id))
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Ringkasan untuk orang tua" in h
    assert "topik-hantu" in h
