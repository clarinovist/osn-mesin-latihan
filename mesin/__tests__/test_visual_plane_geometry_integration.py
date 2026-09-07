"""Palang integrasi geometri: snapshot, aktivasi, dan permukaan HTTP."""
from __future__ import annotations

import re
from dataclasses import replace
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
import question_views
import share_links
import students
import topic_plane_geometry as geometri
import topic_statistics as statistika
from http_test_kit import SANDI_GURU, SANDI_MURID, ServerUji
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan


@pytest.fixture()
def db(tmp_path):
    jalur = tmp_path / "geometri.db"
    database.siapkan(jalur)
    return jalur


@pytest.fixture()
def server(tmp_path, monkeypatch):
    layanan = ServerUji(tmp_path, monkeypatch)
    try:
        yield layanan
    finally:
        layanan.berhenti()


def _contoh():
    return (
        geometri.luas_kotak_satuan(5, 4),
        geometri.luas_arsiran("persegi_titik_tengah", r=7),
        geometri.luas_segiempat_lain("balik_diagonal", L=84, d1=12),
        geometri.sudut_luar_segitiga(64, 37),
    )


def _buat(kon, siswa, soal=None):
    butir = tuple(replace(s, level="P5") for s in (_contoh() if soal is None else soal))
    return database.buat_sesi_dari_urutan(
        kon, siswa, seed=41, urutan=tuple(s.template_id for s in butir),
        topik="geometri-datar", level="P5", soal_terpilih=butir,
    )


@pytest.mark.parametrize("flag", (
    "geometri-datar", "statistika,geometri-datar",
    " geometri-datar , statistika ", "geometri-datar,geometri-datar",
))
def test_aktivasi_geometri_dan_csv_tidak_mengubah_soal(flag, monkeypatch):
    soal = _contoh()[0]
    monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
    sebelum = question_views.penyajian_dari_soal(soal)
    identitas = soal.tanda_tangan
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", flag)
    visual = question_views.penyajian_dari_soal(soal)
    assert visual.status_visual == "siap"
    assert visual.mode_representasi == "geometri_datar-v1"
    assert visual.descriptor is not None
    assert visual.descriptor.jenis == "geometri_datar"
    assert visual.fingerprint_matematis == sebelum.fingerprint_matematis
    assert visual.fingerprint_penyajian != sebelum.fingerprint_penyajian
    assert soal.tanda_tangan == identitas
    assert sebelum.teks_soal == soal.teks
    assert sebelum.descriptor is None


def test_csv_mempertahankan_statistika_dan_teks_nonvisual(monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika,geometri-datar")
    soal = statistika.diagram_batang_garis("jumlah", [10, 20, 30])
    penyajian = question_views.penyajian_dari_soal(soal)
    assert penyajian.descriptor is not None
    assert penyajian.descriptor.jenis == "batang"
    for varian in ("keliling", "luas", "volume"):
        soal = geometri.perbandingan_ukuran(varian, 3, 12)
        hasil = question_views.penyajian_dari_soal(soal)
        assert hasil.teks_soal == soal.teks
        assert hasil.status_visual == "tanpa_visual"


@pytest.mark.parametrize("flag", ("geometri", "statistika,asing", "geometri-datar,", ","))
def test_flag_salah_rollback_tanpa_sesi_atau_bank_parsial(db, monkeypatch, flag):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", flag)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        with pytest.raises(ValueError, match="keluarga visual tidak dikenal"):
            _buat(kon, siswa)
        for tabel in ("soal", "sesi", "sesi_soal"):
            assert kon.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM siswa").fetchone()[0] == 1


def test_bank_bersama_tidak_mengubah_snapshot_teks_dan_flag_off_tetap_visual(db, monkeypatch):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
        lama = _buat(kon, siswa)
        sebelum = tuple(b["penyajian_json"] for b in database.isi_sesi(kon, lama))
        monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
        baru = _buat(kon, siswa)
        snapshot = tuple(question_views.penyajian_dari_baris(b) for b in database.isi_sesi(kon, baru))
        monkeypatch.delenv("OSN_VISUAL_KELUARGA")
        ulang = tuple(question_views.penyajian_dari_baris(b) for b in database.isi_sesi(kon, baru))
        assert snapshot == ulang
        assert tuple(b["penyajian_json"] for b in database.isi_sesi(kon, lama)) == sebelum
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == len(_contoh())
    for penyajian in ulang:
        for gaya in ("murid", "stitch", "guru", "cetak"):
            assert "<svg" in render_pertanyaan(penyajian, gaya=gaya)


def test_visual_invalid_butir_kedua_membatalkan_semua(db, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    soal = _contoh()[0]
    rusak = geometri.luas_segiempat_lain("balik_diagonal", L=84, d1=12)
    rusak = replace(rusak, parameter={**rusak.parameter, "d2": 14})
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        with pytest.raises(ValueError):
            _buat(kon, siswa, (soal, rusak))
        for tabel in ("soal", "sesi", "sesi_soal"):
            assert kon.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0] == 0


def test_ringkasan_dan_query_murid_tidak_membaca_rahasia(db, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        sesi = _buat(kon, siswa)
        penyajian = question_views.penyajian_sesi_aman(kon, sesi)
        dilarang = {"kunci", "malrule", "malrule_id", "kode_final", "kode_usulan", "alasan"}
        def palang(aksi, tabel, kolom, _db, _pemicu):
            if aksi == sqlite3.SQLITE_READ and kolom in dilarang:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        kon.set_authorizer(palang)
        try:
            assert students.soal_murid(kon, sesi, siswa)
        finally:
            kon.set_authorizer(lambda *_: sqlite3.SQLITE_OK)
    ringkasan = ringkasan_pertanyaan(penyajian[2])
    assert "84" in ringkasan and "12" in ringkasan
    assert "14" not in ringkasan
    assert "<svg" not in ringkasan


def test_http_geometri_identik_di_share_murid_guru_cetak_dan_reload(server, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "geometri-datar")
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
        sesi = _buat(kon, siswa)
        token = share_links.buat(kon, sesi)
        baris = database.isi_sesi(kon, sesi)
        sidik = tuple(b["fingerprint_penyajian"] for b in baris)
        ssid = baris[0]["sesi_soal_id"]
    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    target = (
        (f"/mulai/{token}", None),
        (f"/murid/kerjakan/{sesi}", ("feby", SANDI_MURID)),
        (f"/sesi/{sesi}", ("guru", SANDI_GURU)),
        (f"/lembar/{sesi}", ("guru", SANDI_GURU)),
    )
    semua = []
    for jalur, auth in target:
        kode, isi, _ = server.minta(jalur, auth=auth)
        assert kode == 200
        assert all(f'data-fingerprint-penyajian="{nilai}"' in isi for nilai in sidik)
        svg = re.findall(r'<svg[^>]*role="img".*?</svg>', isi, flags=re.S)
        assert len(svg) == len(_contoh())
        semua.append(svg)
    assert all(svg == semua[0] for svg in semua)
    kode, _, _ = server.minta(f"/mulai/{token}", data={f"jwb_{ssid}": "17"})
    assert kode == 200
    kode, isi, _ = server.minta(f"/mulai/{token}")
    assert kode == 200 and all(nilai in isi for nilai in sidik)
    with server.buka() as kon:
        assert kon.execute("SELECT jawaban FROM jawaban WHERE sesi_soal_id = ?", (ssid,)).fetchone()[0] == "17"
        assert tuple(b["fingerprint_penyajian"] for b in database.isi_sesi(kon, sesi)) == sidik
        assert students.hasil_murid(kon, siswa, sesi) is None
        import reports
        reports.diagnosa_murid(kon, sesi)
        database.tandai_selesai(kon, sesi)
        kon.execute("UPDATE sesi SET direview = datetime('now') WHERE id = ?", (sesi,))
    kode, isi, _ = server.minta(f"/murid/hasil/{sesi}", auth=("feby", SANDI_MURID))
    assert kode == 200
    assert re.findall(r'<svg[^>]*role="img".*?</svg>', isi, flags=re.S) == semua[0]
    badan = isi.split("</style>")[-1].lower()
    assert not any(kata in badan for kata in ("malrule", "kode_final", "diagnosis"))


@pytest.mark.parametrize("pilihan", ("geometri-datar", "campuran", "gabungan"))
def test_pembuat_sesi_biasa_campuran_dan_gabungan_membawa_snapshot(db, monkeypatch, pilihan):
    import topics
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika,geometri-datar")
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        if pilihan == "gabungan":
            sesi = database.buat_sesi_gabungan(
                kon, siswa, seed=20260907, topik_ids=["geometri-datar", "statistika"],
                level="P5", jumlah_soal=50,
            )
        else:
            sesi = database.buat_sesi(kon, siswa, seed=20260907, topik=pilihan, level="P5", jumlah_soal=50)
        baris = database.isi_sesi(kon, sesi)
        geometri_aktif = tuple(b for b in baris if b["template_id"] in geometri.REGISTRI_TOPIK and b["template_id"] != "perbandingan_ukuran")
        assert geometri_aktif
        for b in geometri_aktif:
            penyajian = question_views.penyajian_dari_baris(b)
            assert penyajian.mode_representasi == "geometri_datar-v1"
            assert "<svg" in render_pertanyaan(penyajian)
