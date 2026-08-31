"""Verifikasi rute lembar di web — soal bisa dicetak langsung dari situs.

Bahaya terbesar di lapisan ini: rute lembar anak dan lembar kunci hanya
berbeda satu ruas URL. Salah menyambungkannya berarti anak bisa membuka
kunci jawaban lewat tautan yang dia lihat di layar guru — dan halamannya
tetap tampil normal, jadi tidak ada yang menyadari sampai terlambat.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import web  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


def teks(html_bytes: bytes | None) -> str:
    assert html_bytes is not None, "lembar tidak terbangkit"
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_bytes.decode(), flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))


def html_dari(isi: bytes | None) -> str:
    """Pastikan lembar benar-benar terbangkit sebelum diperiksa isinya."""
    assert isi is not None, "lembar tidak terbangkit — sesi tidak ditemukan?"
    return isi.decode()


def test_lembar_soal_bisa_dibangkitkan_dari_sesi(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Cetak")
        sesi_id = database.buat_sesi(kon, sid, seed=1234)
        isi = web.halaman_lembar(kon, sesi_id, untuk_guru=False)

    assert isi is not None
    h = isi.decode()
    assert h.startswith("<!DOCTYPE html>")
    assert h.count('class="soal"') == 12
    assert "Cetak" in h


def test_lembar_anak_tidak_memuat_kunci_di_posisi_jawaban(db):
    """Rute /lembar/<id> dipegang anak — kotak jawaban harus kosong."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak")
        sesi_id = database.buat_sesi(kon, sid, seed=555)
        h = html_dari(web.halaman_lembar(kon, sesi_id, untuk_guru=False))

    for potongan in re.findall(r'class="jawab">(.*?)</div>', h, flags=re.S):
        terbaca = teks(potongan.encode()).replace("Jawabanku:", "")
        terbaca = terbaca.replace("urutan ke-", "").replace("dan", "").strip()
        assert not terbaca, f"ada teks di posisi jawaban: {terbaca!r}"


def test_lembar_anak_tidak_memuat_kata_kunci_atau_kode(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Anak2")
        sesi_id = database.buat_sesi(kon, sid, seed=77)
        t = teks(web.halaman_lembar(kon, sesi_id, untuk_guru=False)).lower()

    for terlarang in ("kunci", "malrule", "miskonsepsi", "salah konsep",
                      "jangan diperlihatkan"):
        assert terlarang not in t, f"{terlarang!r} bocor ke lembar anak"


def test_lembar_penilaian_justru_memuat_kunci(db):
    """Kebalikannya: guru harus melihat semua kunci."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Guru")
        sesi_id = database.buat_sesi(kon, sid, seed=99)
        kunci = [b["kunci"] for b in database.isi_sesi(kon, sesi_id)]
        h = html_dari(web.halaman_lembar(kon, sesi_id, untuk_guru=True))

    for k in kunci:
        assert k in h
    assert "Jangan diperlihatkan ke anak" in h


def test_lembar_cocok_dengan_soal_yang_tercatat_di_sesi(db):
    """Lembar dibangkitkan dari seed, bukan dibaca berkas — harus tetap
    cocok dengan soal yang tersimpan, kalau tidak guru menilai soal lain."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Cocok")
        sesi_id = database.buat_sesi(kon, sid, seed=31337)
        tercatat = database.isi_sesi(kon, sesi_id)
        h = html_dari(web.halaman_lembar(kon, sesi_id, untuk_guru=True))

    for b in tercatat:
        assert b["kunci"] in h, f"kunci soal {b['nomor']} tidak ada di lembar"


def test_sesi_tidak_ada_mengembalikan_none(db):
    with database.buka(db) as kon:
        assert web.halaman_lembar(kon, 99999) is None


# ── Buat sesi baru dari web ─────────────────────────────────────────────


def test_sesi_baru_memakai_seed_yang_belum_pernah_dipakai(db):
    """Seed berulang = soal persis sama = anak bisa hafal jawabannya."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Seed")
        dibuat = [web.buat_sesi_seed_baru(kon, sid) for _ in range(12)]
        seeds = [
            r["seed"]
            for r in kon.execute(
                "SELECT seed FROM sesi WHERE siswa_id = ?", (sid,)
            ).fetchall()
        ]

    assert len(dibuat) == len(set(dibuat)), "id sesi terduplikasi"
    assert len(seeds) == len(set(seeds)), "seed terulang — anak bisa hafal soal"


def test_sesi_baru_langsung_berisi_dua_belas_soal(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Isi")
        sesi_id = web.buat_sesi_seed_baru(kon, sid)
        assert len(database.isi_sesi(kon, sesi_id)) == 12


def test_dua_siswa_dapat_soal_berbeda(db):
    """Kalau lembarnya sama, satu anak bisa menyalin yang lain."""
    with database.buka(db) as kon:
        a = database.tambah_siswa(kon, "A")
        b = database.tambah_siswa(kon, "B")
        sa = web.buat_sesi_seed_baru(kon, a)
        sb = web.buat_sesi_seed_baru(kon, b)
        soal_a = [r["soal_id"] for r in database.isi_sesi(kon, sa)]
        soal_b = [r["soal_id"] for r in database.isi_sesi(kon, sb)]

    assert soal_a != soal_b


def test_halaman_utama_tautan_lembar_pindah_ke_halaman_sesi(db):
    """Lembar soal/kunci cukup satu pintu: dari halaman sesi. Dashboard
    yang menampilkan keduanya terasa redundant (umpan balik guru,
    30 Aug 2026) — yang tersisa hanya link sesi + form sesi baru."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Tautan")
        sesi_id = database.buat_sesi(kon, sid, seed=42)
        h = web.halaman_utama(kon).decode()
        hs = web.halaman_sesi(kon, sesi_id).decode()

    assert f'href="/lembar/{sesi_id}"' not in h
    assert f'href="/lembar/{sesi_id}/penilaian"' not in h
    assert f'href="/lembar/{sesi_id}"' in hs
    assert f'href="/lembar/{sesi_id}/penilaian"' in hs
    assert f'action="/sesi-baru/{sid}"' in h
