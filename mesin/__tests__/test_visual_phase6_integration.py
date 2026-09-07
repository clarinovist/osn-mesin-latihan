"""Snapshot dan HTTP Fase 6, selalu memakai basis data fixture sementara."""
from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
import question_views as q
import share_links
import students
import topic_combinatorics as k
import topic_measurement as p
from http_test_kit import SANDI_GURU, SANDI_MURID, ServerUji
from visual_renderer import render_pertanyaan


def contoh():
    return (k.jalur_petak(3, 4),
            *(p.jam_selesai(v, 21, 47, 4, 38)
              for v in ("cari_mulai", "cari_selesai", "cari_durasi")),
            *(p.skala_peta(v, 45, 18, 250000, versi=2)
              for v in ("cari_skala", "cari_peta", "cari_sebenarnya")),
            k.inklusi_eksklusi_2(19, 23, 7),
            k.susun_bilangan("dengan_nol", (0, 2, 4, 7)),
            k.susun_bilangan_syarat("genap", (1, 2, 5)),
            k.susun_bilangan_syarat("lebih_dari", (2, 5, 7), 500),
            k.permutasi_urutan(5, 3, ["A", "B", "C", "D", "E"]),
            k.permutasi_blok(5, 2, ["A", "B", "C", "D", "E"]),
            k.kombinasi_pilih(5, 3, ["A", "B", "C", "D", "E"]))


def buat(kon, siswa, soal=None):
    butir = tuple(replace(s, level="P6") for s in (contoh() if soal is None else soal))
    return database.buat_sesi_dari_urutan(
        kon, siswa, seed=41, urutan=tuple(s.template_id for s in butir),
        topik="campuran", level="P6", soal_terpilih=butir)


@pytest.fixture()
def db(tmp_path):
    jalur = tmp_path / "fase6.db"
    database.siapkan(jalur)
    return jalur


@pytest.fixture()
def server(tmp_path, monkeypatch):
    layanan = ServerUji(tmp_path, monkeypatch)
    try:
        yield layanan
    finally:
        layanan.berhenti()


def test_snapshot_teks_tetap_dan_visual_dibaca_saat_flag_mati(db, monkeypatch):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
        lama = buat(kon, siswa)
        sebelum = tuple(b["penyajian_json"] for b in database.isi_sesi(kon, lama))
        monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik,statistika,geometri-datar")
        baru = buat(kon, siswa)
        snapshot = q.penyajian_sesi_aman(kon, baru)
        monkeypatch.delenv("OSN_VISUAL_KELUARGA")
        assert q.penyajian_sesi_aman(kon, baru) == snapshot
        assert tuple(b["penyajian_json"] for b in database.isi_sesi(kon, lama)) == sebelum
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == len(contoh())
        for penyajian in snapshot:
            assert penyajian.status_visual == "siap"
            for gaya in ("stitch", "murid", "cetak", "guru"):
                assert "<svg" in render_pertanyaan(penyajian, gaya=gaya)


def test_query_murid_tidak_membaca_rahasia(db, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        sesi = buat(kon, siswa)
        def palang(aksi, tabel, kolom, _db, _pemicu):
            rahasia = {"kunci", "malrule", "malrule_id", "kode_final", "kode_usulan", "alasan"}
            return sqlite3.SQLITE_DENY if aksi == sqlite3.SQLITE_READ and kolom in rahasia else sqlite3.SQLITE_OK
        kon.set_authorizer(palang)
        try:
            assert len(students.soal_murid(kon, sesi, siswa)) == len(contoh())
        finally:
            kon.set_authorizer(lambda *_: sqlite3.SQLITE_OK)


def test_invalid_membatalkan_seluruh_transaksi(db, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    rusak = replace(contoh()[0], parameter={"b": 3, "k": 4, "jawaban": 35})
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        with pytest.raises(ValueError):
            buat(kon, siswa, (contoh()[1], rusak))
        assert all(kon.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0
                   for t in ("sesi", "soal", "sesi_soal"))


def test_http_semantik_sama_dan_jawaban_tidak_mengubah_snapshot(server, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
        sesi = buat(kon, siswa)
        token = share_links.buat(kon, sesi)
        baris = database.isi_sesi(kon, sesi)
        sidik = tuple(b["fingerprint_penyajian"] for b in baris)
        ssid = baris[0]["sesi_soal_id"]
    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    hasil = ()
    for jalur, auth in ((f"/mulai/{token}", None),
                        (f"/murid/kerjakan/{sesi}", ("feby", SANDI_MURID)),
                        (f"/sesi/{sesi}", ("guru", SANDI_GURU)),
                        (f"/lembar/{sesi}", ("guru", SANDI_GURU))):
        kode, html, _ = server.minta(jalur, auth=auth)
        assert kode == 200 and all(s in html for s in sidik)
        svg = tuple(re.findall(r'<svg[^>]*role="img".*?</svg>', html, re.S))
        assert len(svg) == len(contoh())
        hasil = (*hasil, svg)
    assert all(svg == hasil[0] for svg in hasil)
    kode, _, _ = server.minta(f"/mulai/{token}", data={f"jwb_{ssid}": "17"})
    assert kode == 200
    with server.buka() as kon:
        assert kon.execute("SELECT jawaban FROM jawaban WHERE sesi_soal_id = ?", (ssid,)).fetchone()[0] == "17"
        assert tuple(b["fingerprint_penyajian"] for b in database.isi_sesi(kon, sesi)) == sidik
        assert students.hasil_murid(kon, siswa, sesi) is None
        import reports
        reports.diagnosa_murid(kon, sesi)
        database.tandai_selesai(kon, sesi)
        kon.execute("UPDATE sesi SET direview = datetime('now') WHERE id = ?", (sesi,))
    kode, html, _ = server.minta(f"/murid/hasil/{sesi}", auth=("feby", SANDI_MURID))
    assert kode == 200
    assert tuple(re.findall(r'<svg[^>]*role="img".*?</svg>', html, re.S)) == hasil[0]
    assert "kode_final" not in html and "malrule" not in html


@pytest.mark.parametrize("mode", ("campuran", "gabungan"))
def test_sesi_campuran_dan_gabungan_membawa_visual(db, monkeypatch, mode):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pengukuran,kombinatorik")
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        if mode == "gabungan":
            sesi = database.buat_sesi_gabungan(
                kon, siswa, seed=20260907, topik_ids=["pengukuran", "kombinatorik"],
                level="P6", jumlah_soal=50)
        else:
            sesi = database.buat_sesi(kon, siswa, seed=20260907, topik=mode, level="P6", jumlah_soal=50)
        baris = tuple(b for b in database.isi_sesi(kon, sesi) if b["template_id"] in {"jalur_petak", "jam_selesai"})
        assert baris
        for b in baris:
            assert q.penyajian_dari_baris(b).status_visual == "siap"
