"""Regresi: kartu sesi di /anak ter-render rusak karena `}` nyasar di style.

1 Sep 2026: baris meta kartu sesi memakai `opacity:.75}}>` di f-string —
kurung satu kelebihan membuat atribut style tidak pernah tertutup; browser
menelan teks meta + div berikutnya sebagai isi atribut → kartu sesi yang
badge-nya "Belum Dikerjakan" tampak telanjang tanpa kartu.
"""

import tempfile

import pytest

import database
import teacher_pages


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = str(tmp_path / "uji.db")
    database.siapkan(p)
    with database.buka(p) as kon:
        database.migrasi(kon)
        monkeypatch.setattr(database, "BAWAAN", tmp_path / "uji.db")
        yield kon


def _siswa_dengan_sesi(db):
    db.execute(
        "INSERT INTO siswa (nama, tingkat, pemilik) VALUES ('Uji', 'P3', 'x')"
    )
    sid = db.execute("SELECT id FROM siswa WHERE nama='Uji'").fetchone()[0]
    siswa = db.execute("SELECT * FROM siswa WHERE id=?", (sid,)).fetchone()
    database.buat_sesi(
        db, sid, seed=1, topik="pola-bilangan", level="P3", mode="diagnostik"
    )
    return siswa


def test_kartu_sesi_tidak_punya_kurung_nyasar_di_style(db):
    html = teacher_pages.halaman_anak(
        db, _siswa_dengan_sesi(db), peran="guru", pengguna="g"
    ).decode()
    assert 'opacity:.75">' in html
    # tidak ada atribut style yang ditutup `}` paras — pola bug f-string
    for baris in html.splitlines():
        assert 'style="' not in baris or "}}" not in baris.split('style="')[1], (
            f"atribut style mengandung }} nyasar: {baris[:120]}"
        )


def test_kartu_sesi_meta_tertutup_sebagai_div(db):
    """Meta tanggal/level/topik harus ada sebagai teks di dalam div .st-meta,
    bukan tertelan atribut style yang tak tertutup."""
    html = teacher_pages.halaman_anak(
        db, _siswa_dengan_sesi(db), peran="guru", pengguna="g"
    ).decode()
    i = html.find('<div class="st-meta"')
    potongan = html[i : html.find("</div>", i) + 6]
    # Markup sehat: class + style = 2 atribut. Re-render rusak (dulu)`}`
    # nyasar menelan seluruh halaman berikutnya sebagai atribut → ratusan `=`.
    assert potongan.count('="') <= 2, (
        f"meta tertelan atribut: {potongan[:200]}"
    )
    assert "pola-bilangan" in potongan or "Pola Bilangan" in potongan
