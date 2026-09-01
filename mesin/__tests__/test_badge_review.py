""""Pengunci badge status review (feedback Filia poin 1).

Keluhan: di halaman orang tua, sesi yang sudah direview dan belum
direview terlihat SAMA. Root cause ganda:

1. CSS: "Masih di review" dan "Selesai" memakai kelas `.st-badge.selesai`
   yang sama — warnanya identik. Fix: status review punya kelas sendiri
   (amber) dan status selesai pindah ke teal.
2. Deploy: badge di dashboard guru ada di commit yang gagal deploy. Di
   sinar sisi murid yang bisa diperbaiki tanpa push — didorong di sini.

Aturan palang: badge hanya label status, tidak boleh membuka kebocoran
(kunci/malrule/diagnosa tetap terlarang di jalur murid).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import student_pages  # noqa: E402
import style_stitch  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


def _sesi_tiga_status(db):
    """Tiga sesi murid dalam tiga keadaan review yang berbeda."""
    import students

    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Uji Badge")
        database.buat_sesi(kon, sid, seed=1, topik="statistika")   # belum
        proses = database.buat_sesi(kon, sid, seed=2, topik="statistika")
        review = database.buat_sesi(kon, sid, seed=3, topik="statistika")
        # proses: satu jawaban tersimpan lewat jalur murid yang sama dgn HP
        ssid = students.soal_murid(kon, proses, sid)[0]["sesi_soal_id"]
        students.simpan_jawaban_murid(kon, sid, proses, {f"jwb_{ssid}": "7"})
        # review: SEMUA soal terisi + selesai dicatat, guru belum buka
        assert students.simpan_jawaban_murid(kon, sid, review, {
            f"jwb_{s['sesi_soal_id']}": "3"
            for s in students.soal_murid(kon, review, sid)
        })
        database.tandai_selesai(kon, review)
    return {"proses": proses, "review": review}


def _html_daftar(db):
    with database.buka(db) as kon:
        sid = database.daftar_siswa(kon)[0]["id"]
        return student_pages.halaman_daftar_sesi_baru(kon, sid, "Uji Badge").decode()


def test_css_mendefinisikan_kelas_review_terpisah():
    css = style_stitch.gaya_stitch()
    assert ".st-badge.review" in css, "status review butuh warna sendiri"
    # amber laut: beda jelas dari teal & dari abu .selesai
    assert "#fff0d6" in css.lower() or "#fff0d6" in css


def test_sesi_menunggu_review_pakai_badge_amber(db):
    _sesi_tiga_status(db)
    html = _html_daftar(db)
    assert 'st-badge review' in html, \
        "sesi selesai-dikerjakan-tapi-belum-direview harus badge amber"


def test_sesi_selesai_direview_tidak_pakai_badge_abu_genit(db):
    """Selesai & tau hasil = teal (diagnostik), bukan abu .selesai."""
    _sesi_tiga_status(db)
    with database.buka(db) as kon:
        # guru sudah membuka hasil → direview terisi (stamp yang sama dengan
        # yang ditulis web.py saat koreksi disimpan)
        kon.execute(
            "UPDATE sesi SET direview = datetime('now', '+7 hours') "
            "WHERE direview IS NULL AND selesai IS NOT NULL"
        )
        sid = database.daftar_siswa(kon)[0]["id"]
        html = student_pages.halaman_daftar_sesi_baru(kon, sid, "Uji Badge").decode()
    # "Selesai · X/Y benar" harus dibawa kelas diagnostik (teal), bukan abu.
    import re
    potongan = re.findall(
        r'<span class="st-badge ([a-z]+)">Selesai', html
    )
    assert potongan and all(k == "diagnostik" for k in potongan), potongan


def test_teks_status_review_explicit_bukan_abu_sama(db):
    """Teks badge antara dua status benar-benar berbeda (bukan warna doang)."""
    _sesi_tiga_status(db)
    html = _html_daftar(db)
    assert "Menunggu direview" in html
