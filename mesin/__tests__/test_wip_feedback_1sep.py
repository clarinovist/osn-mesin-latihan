"""Pengunci commit 1 Sep 2026 — jawaban feedback Filia (poin 3, 4, 5).

Tiga fitur lahir dari masukan pengguna 1 Sep 2026 dan masing-masing mudah
rusak diam-diam oleh perubahan berikutnya:

1. jumlah_soal — form guru boleh minta 15/20/25/30 soal walau komposisi
   bawaan topik hanya 10 (poin 3: "durasi 1 jam tapi soal tetep 10").
2. topik "campuran" — simulasi ujian: interleave semua topik yang tersedia
   di level itu (poin 4). Harus terdaftar AMBIL, bisa dibangun per level,
   dan deterministik dari seed.
3. pembahasan — perhitungan langkah-langkah untuk orang tua (poin 5).
   YA di sisi guru (halaman koreksi), TIDAK BOLEH sampai ke halaman murid
   (palang murid) dan TIDAK BOLEH mengubah tanda_tangan (bank soal &
   konsistensi replay).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import topics  # noqa: E402
import generator  # noqa: E402
import database  # noqa: E402
import student_pages  # noqa: E402
import teacher_pages  # noqa: E402
from topic_statistics import median_modus  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """Basis data sementara — pola sama dengan test_database/test_students."""
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


# ── 1. jumlah_soal (poin 3) ─────────────────────────────────────────────


def test_buat_lembar_jumlah_soal_menambah_populasi():
    """Komposisi bawaan P3 statistika 10 soal; minta 25 → dapat 25."""
    bawaan = generator.buat_lembar(1, level="P3", topik="statistika")
    assert len(bawaan.soal) == 10

    lembar = generator.buat_lembar(1, level="P3", topik="statistika", jumlah_soal=25)
    assert len(lembar.soal) == 25


@pytest.mark.parametrize("n", (1, 15, 30, 50))
def test_buat_lembar_jumlah_soal_n_tepat(n):
    lembar = generator.buat_lembar(7, level="P4", topik="statistika", jumlah_soal=n)
    assert len(lembar.soal) == n


def test_buat_lembar_jumlah_soal_deterministik():
    a = generator.buat_lembar(9, level="P5", topik="statistika", jumlah_soal=20)
    b = generator.buat_lembar(9, level="P5", topik="statistika", jumlah_soal=20)
    assert [s.tanda_tangan for s in a.soal] == [s.tanda_tangan for s in b.soal]


def test_buat_sesi_menerima_jumlah_soal(db):
    """database.buat_sesi meneruskan jumlah_soal ke lembar yang disimpan."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Uji Jumlah")
        sesi_id = database.buat_sesi(kon, sid, seed=555, jumlah_soal=15)
        isi = database.isi_sesi(kon, sesi_id)
    assert len(isi) == 15
    assert [r["nomor"] for r in isi] == list(range(1, 16))


# ── 2. topik campuran (poin 4) ──────────────────────────────────────────


def test_campuran_terdaftar():
    assert "campuran" in topics.daftar_topik()


@pytest.mark.parametrize("level", ["P3", "P4", "P5", "P6"])
def test_campuran_komposisi_level(level):
    """Komposisi campuran ada untuk semua level resmi."""
    amb = topics.ambil("campuran")
    komposisi = amb.komposisi.get(level)
    assert komposisi, f"campuran tanpa komposisi {level}"


@pytest.mark.parametrize("seed", [1, 7, 42])
@pytest.mark.parametrize("level", ["P3", "P5"])
def test_campuran_buat_lembar_kum(level, seed):
    """Lembar campuran bisa dibangun — semua template muat dispatch param."""
    lembar = generator.buat_lembar(seed, level=level, topik="campuran")
    assert len(lembar.soal) >= 10


def test_campuran_lebih_variatif_dari_topik_tunggal():
    """Campuran P3 memuat template dari beberapa topik berbeda.

    Ini inti permintaan Filia: satu lembar harus lintas topik, mirip ujian.
    """
    lembar = generator.buat_lembar(1, level="P3", topik="campuran")
    ids = {s.template_id for s in lembar.soal}
    # ambil penyusun campuran dari topics: beberapa paket topik berkontribusi
    assert len(ids) >= 5, f"campuran P3 terlalu monoton: {sorted(ids)}"


def test_campuran_deterministik_dari_seed():
    a = generator.buat_lembar(3, level="P4", topik="campuran")
    b = generator.buat_lembar(3, level="P4", topik="campuran")
    assert [s.tanda_tangan for s in a.soal] == [s.tanda_tangan for s in b.soal]


def test_campuran_muncul_di_dropdown_topik():
    """_topik_untuk_level menaruh campuran paling depan (opsi pertama)."""
    daftar = teacher_pages._topik_untuk_level("P5")
    assert daftar[0] == "campuran"


# ── 3. pembahasan statistika (poin 5) ───────────────────────────────────


def test_pembahasan_median_modus_terisi():
    soal = median_modus("modus", [1, 2, 2, 3])
    assert soal.pembahasan
    assert "2" in soal.pembahasan  # memuat perhitungan sungguhan


def test_pembahasan_tidak_mengubah_tanda_tangan():
    """tanda_tangan hanya level|template(parameter) — pembahasan di luar.

    Kalau pembahasan ikut tanda_tangan, bank soal yang sudah ada "hancur"
    dan statistik varian-tersedia jadi bohong.
    """
    soal = median_modus("modus", [1, 2, 2, 3])
    butir = ",".join(f"{k}={soal.parameter[k]}" for k in sorted(soal.parameter))
    assert soal.tanda_tangan == f"P3|median_modus({butir})"


def test_pembahasan_tidak_bocor_ke_halaman_murid(db):
    """Palang murid: perhitungan = jawaban langsung, wajib tak terlihat.

    Halaman kerja penuh sudah dijaga test_murid (fixture db_terjaga di
    test_students.py). Yang dikunci di sini: fungsi-daftar murid tidak
    pernah merender marker pembahasan — kalau suatu saat pembahasan
    disuntik ke halaman murid, test ini pecah dulu.
    """
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Uji Palang")
        database.buat_sesi(kon, sid, seed=999, topik="statistika")
        html = student_pages.halaman_daftar_sesi_baru(kon, sid, "Uji Palang").decode()
    assert "pembahasan" not in html.lower()
    assert "Langkah:" not in html
