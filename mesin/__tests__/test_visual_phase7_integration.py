"""Palang bantuan belajar dan snapshot pola pada HTTP fixture terisolasi."""
from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
import interventions
import learning_cycle_ui
import question_views
import reports
import share_links
import students
from http_test_kit import SANDI_GURU, SANDI_MURID, ServerUji
from learning_cycle import BuktiSiklus, PutaranFokus, RencanaBelajar, StatusFokus
from topic_number_patterns import korek_api, titik_segitiga
from visual_renderer import render_pertanyaan


def test_kartu_bantuan_cetak_tidak_terpisah():
    from presentation_style import GAYA_PENYAJIAN
    from style_stitch import gaya_stitch
    aturan = re.search(r"@media print\s*\{\s*\.rumus-kartu-st,\s*\.bantuan-visual\s*\{([^}]+)", GAYA_PENYAJIAN)
    assert aturan is not None
    assert "break-inside: avoid" in aturan.group(1)
    assert re.search(r"\.hasil-soal-st\s*\{\s*break-inside: avoid", GAYA_PENYAJIAN.split("@media print", 1)[1])
    assert GAYA_PENYAJIAN in gaya_stitch()


@pytest.fixture()
def server(tmp_path, monkeypatch):
    layanan = ServerUji(tmp_path, monkeypatch)
    try:
        yield layanan
    finally:
        layanan.berhenti()


def buat(kon, siswa):
    butir = (korek_api(4, 3, 20), titik_segitiga(12))
    return database.buat_sesi_dari_urutan(
        kon, siswa, seed=701, urutan=tuple(s.template_id for s in butir),
        topik="pola-bilangan", level="P3", soal_terpilih=butir)


def gambar(html):
    return tuple(re.findall(r'<svg[^>]*role="img".*?</svg>', html, re.S))


def test_snapshot_baru_berbeda_dari_teks_dan_tidak_bergantung_flag(server, monkeypatch):
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
        monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
        lama = buat(kon, siswa)
        sebelum = question_views.penyajian_sesi_aman(kon, lama)
        monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
        baru = buat(kon, siswa)
        snapshot = question_views.penyajian_sesi_aman(kon, baru)
        monkeypatch.delenv("OSN_VISUAL_KELUARGA")
        assert question_views.penyajian_sesi_aman(kon, lama) == sebelum
        assert question_views.penyajian_sesi_aman(kon, baru) == snapshot
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == 2
        for a, b in zip(sebelum, snapshot):
            assert a.fingerprint_matematis == b.fingerprint_matematis
            assert a.fingerprint_penyajian != b.fingerprint_penyajian
            assert "<svg" not in render_pertanyaan(a)
            assert "<svg" in render_pertanyaan(b)


def test_http_pertanyaan_sama_dan_bantuan_hanya_setelah_review(server, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
        sesi = buat(kon, siswa)
        token = share_links.buat(kon, sesi)
        baris = database.isi_sesi(kon, sesi)
        sidik = tuple(b["fingerprint_penyajian"] for b in baris)
        data = {f"jwb_{b['sesi_soal_id']}": "0" for b in baris}
    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    semua = ()
    for jalur, auth in ((f"/mulai/{token}", None),
                        (f"/murid/kerjakan/{sesi}", ("feby", SANDI_MURID)),
                        (f"/sesi/{sesi}", ("guru", SANDI_GURU)),
                        (f"/lembar/{sesi}", ("guru", SANDI_GURU))):
        kode, html, _ = server.minta(jalur, auth=auth)
        assert kode == 200 and all(s in html for s in sidik)
        assert "data-bantuan-visual" not in html
        assert len(gambar(html)) == 2
        semua = (*semua, gambar(html))
    assert all(s == semua[0] for s in semua)
    kode, _, _ = server.minta(f"/mulai/{token}", data=data)
    assert kode == 200
    kode, html, _ = server.minta(f"/murid/hasil/{sesi}?konteks=hasil_sah", auth=("feby", SANDI_MURID))
    assert kode == 404 and "data-bantuan-visual" not in html
    with server.buka() as kon:
        assert tuple(b["fingerprint_penyajian"] for b in database.isi_sesi(kon, sesi)) == sidik
        assert students.hasil_murid(kon, siswa, sesi) is None
        assert kon.execute("SELECT COUNT(*) FROM jawaban").fetchone()[0] == 2
        reports.diagnosa_murid(kon, sesi)
        database.tandai_selesai(kon, sesi)
        kon.execute("UPDATE sesi SET direview = datetime('now') WHERE id = ?", (sesi,))
        assert students.hasil_murid(kon, siswa + 100, sesi) is None
    kode, html, _ = server.minta(f"/murid/hasil/{sesi}", auth=("feby", SANDI_MURID))
    assert kode == 200
    assert html.count("data-bantuan-visual") == 2
    assert len(gambar(html)) == 4
    assert gambar(html)[-2:] == semua[0]
    assert all(x not in html for x in ("kode_final", "malrule", "visual-pola-v1:", "miskonsepsi"))
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    kode, html, _ = server.minta(f"/murid/kerjakan/{sesi}", auth=("feby", SANDI_MURID))
    assert kode == 200 and "data-bantuan-visual" not in html


def test_query_murid_tetap_tidak_membaca_rahasia(server, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "pola-bilangan")
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        sesi = buat(kon, siswa)
        def palang(aksi, tabel, kolom, _db, _pemicu):
            rahasia = {"kunci", "malrule", "malrule_id", "kode_final", "kode_usulan", "alasan"}
            return sqlite3.SQLITE_DENY if aksi == sqlite3.SQLITE_READ and kolom in rahasia else sqlite3.SQLITE_OK
        kon.set_authorizer(palang)
        try:
            butir = students.soal_murid(kon, sesi, siswa)
            assert len(butir) == 2
            assert all("bantuan" not in b and b["penyajian"].status_visual == "siap" for b in butir)
        finally:
            kon.set_authorizer(lambda *_: sqlite3.SQLITE_OK)


@pytest.mark.parametrize("template_id", ("korek_api", "titik_segitiga"))
def test_pelajari_bersama_visual_dan_pendekatan_lama_tetap_terpisah(template_id):
    fokus = (template_id, "K", "uji-konsep")
    status = StatusFokus(fokus, "perlu_dipelajari", jumlah_sesi=2)
    putaran = PutaranFokus(7, "P3", (status,))
    bukti = BuktiSiklus(9, "P3")
    rencana = RencanaBelajar("intervensi", "uji", putaran=putaran, kandidat=(fokus,))
    html = learning_cycle_ui.render_rencana(rencana, bukti, 9)
    assert html.count("data-bantuan-visual") == 1
    pilihan = interventions.pilihan_untuk_fokus(fokus)
    visual = next(m for m in pilihan if m.bantuan is not None)
    assert f'name="pendekatan_id" value="{visual.pendekatan_id}"' in html
    for materi in pilihan:
        lama = replace(status, pendekatan_berikutnya=materi.pendekatan_id)
        pilih = replace(rencana, putaran=replace(putaran, fokus=(lama,)))
        isi = learning_cycle_ui.render_rencana(pilih, bukti, 9)
        assert ("data-bantuan-visual" in isi) == (materi.bantuan is not None)
    for tindakan in ("evaluasi", "checkpoint", "penguatan", "lanjutkan_sesi", "tunggu_evaluasi"):
        isi = learning_cycle_ui.render_rencana(replace(rencana, tindakan=tindakan), bukti, 9)
        assert "data-bantuan-visual" not in isi
        assert "Contoh terbimbing" not in isi
