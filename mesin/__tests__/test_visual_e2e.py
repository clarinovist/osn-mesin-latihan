"""HTTP lintas keluarga dan kill switch; seluruh state memakai fixture temp."""
import re
import sqlite3
from dataclasses import replace

import pytest
import auth
import database
import question_views
import reports
import sessions
import share_links
import students
from http_test_kit import SANDI_GURU, SANDI_MURID, ServerUji
from visual_renderer import render_pertanyaan
from visual_test_support import KELUARGA, SEMUA_KELUARGA, buat_soal

CONTOH = (("statistika", "P4", "diagram_batang_garis"),
          ("geometri-datar", "P5", "luas_arsiran"),
          ("geometri-ruang", "P6", "jaring_jaring"),
          ("pengukuran", "P6", "jam_selesai"),
          ("kombinatorik", "P6", "jalur_petak"),
          ("pola-bilangan", "P6", "korek_api"))


def contoh():
    return tuple(replace(buat_soal(n, lv, tid, 31), level="P6") for n, lv, tid in CONTOH)


def buat(kon, siswa, butir=None, mode="diagnostik"):
    butir = contoh() if butir is None else butir
    return database.buat_sesi_dari_urutan(kon, siswa, seed=31,
        urutan=tuple(s.template_id for s in butir), topik="campuran", level="P6",
        soal_terpilih=butir, mode=mode)


def gambar(html):
    return tuple(re.findall(r'<svg[^>]*role="img".*?</svg>', html, re.S))


@pytest.fixture()
def server(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "BERKAS_SESI", tmp_path / "sesi.json")
    layanan = ServerUji(tmp_path, monkeypatch)
    try:
        yield layanan
    finally:
        layanan.berhenti()


@pytest.mark.parametrize("keluarga", KELUARGA)
def test_kill_switch_per_keluarga_tidak_mengubah_snapshot(server, monkeypatch, keluarga):
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        monkeypatch.setenv("OSN_VISUAL_KELUARGA", SEMUA_KELUARGA)
        lama = buat(kon, siswa)
        snapshot = question_views.penyajian_sesi_aman(kon, lama)
        assert all(s.status_visual == "siap" for s in snapshot)
        monkeypatch.setenv("OSN_VISUAL_KELUARGA", ",".join(k for k in KELUARGA if k != keluarga))
        baru = buat(kon, siswa)
        hasil = question_views.penyajian_sesi_aman(kon, baru)
        for (nama, _, _), awal, akhir in zip(CONTOH, snapshot, hasil):
            assert (akhir.status_visual == "siap") == (nama != keluarga)
            assert awal.fingerprint_matematis == akhir.fingerprint_matematis
        assert question_views.penyajian_sesi_aman(kon, lama) == snapshot
        assert all("<svg" in render_pertanyaan(s) for s in snapshot)


@pytest.mark.parametrize("mode", ("diagnostik", "drill"))
def test_http_seluruh_keluarga_simpan_reload_hasil_dan_palang(server, monkeypatch, mode):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", SEMUA_KELUARGA)
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
        sesi = buat(kon, siswa, mode=mode)
        token = share_links.buat(kon, sesi)
        baris = database.isi_sesi(kon, sesi)
        sidik = tuple(b["fingerprint_penyajian"] for b in baris)
        data = {f"jwb_{b['sesi_soal_id']}": "17" for b in baris}
    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    semua = ()
    for jalur, akun in ((f"/mulai/{token}", None),
                       (f"/murid/kerjakan/{sesi}", ("feby", SANDI_MURID)),
                       (f"/sesi/{sesi}", ("guru", SANDI_GURU)),
                       (f"/lembar/{sesi}", ("guru", SANDI_GURU))):
        kode, html, _ = server.minta(jalur, auth=akun)
        assert kode == 200 and all(s in html for s in sidik)
        assert "data-bantuan-visual" not in html
        assert len(gambar(html)) == len(CONTOH)
        semua = (*semua, gambar(html))
        if akun is None or akun[0] == "feby":
            assert not any(x in html for x in ("kode_final", "malrule", "miskonsepsi"))
    assert all(s == semua[0] for s in semua)
    assert server.minta(f"/mulai/{token}", data=data)[0] == 200
    kode, isi, _ = server.minta(f"/murid/hasil/{sesi}", auth=("feby", SANDI_MURID))
    assert kode == 404 and "data-bantuan-visual" not in isi
    with server.buka() as kon:
        assert tuple(b["fingerprint_penyajian"] for b in database.isi_sesi(kon, sesi)) == sidik
        assert kon.execute("SELECT COUNT(*) FROM jawaban WHERE jawaban='17'").fetchone()[0] == len(CONTOH)
        assert students.hasil_murid(kon, siswa, sesi) is None
        reports.diagnosa_murid(kon, sesi)
        database.tandai_selesai(kon, sesi)
        kon.execute("UPDATE sesi SET direview=datetime('now') WHERE id=?", (sesi,))
    kode, html, _ = server.minta(f"/murid/hasil/{sesi}", auth=("feby", SANDI_MURID))
    assert kode == 200 and all(s in html for s in sidik)
    assert gambar(html)[-len(CONTOH):] == semua[0]
    assert not any(x in html for x in ("kode_final", "malrule", "visual-pola-v1:"))


def test_palang_query_dan_akses_asing_tanpa_efek_samping(server, monkeypatch):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", SEMUA_KELUARGA)
    with server.buka() as kon:
        database.tambah_siswa(kon, "feby", pemilik="guru")
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="lain")
        sesi = buat(kon, siswa)
        sebelum = tuple(kon.iterdump())
        def palang(aksi, tabel, kolom, _db, _pemicu):
            rahasia = {"kunci", "malrule", "malrule_id", "kode_final", "kode_usulan", "alasan"}
            return sqlite3.SQLITE_DENY if aksi == sqlite3.SQLITE_READ and kolom in rahasia else sqlite3.SQLITE_OK
        kon.set_authorizer(palang)
        try:
            assert len(students.soal_murid(kon, sesi, siswa)) == len(CONTOH)
        finally:
            kon.set_authorizer(lambda *_: sqlite3.SQLITE_OK)
    for pola in ("/sesi/{}", "/lembar/{}", "/murid/kerjakan/{}", "/murid/hasil/{}"):
        akun = ("feby", SANDI_MURID) if pola.startswith("/murid") else ("guru", SANDI_GURU)
        asing = server.minta(pola.format(sesi), auth=akun)
        hilang = server.minta(pola.format(sesi + 999), auth=akun)
        assert asing[0] == hilang[0] == 404 and asing[1] == hilang[1]
    assert server.minta(f"/murid/kerjakan/{sesi}", auth=("feby", SANDI_MURID), data={"jwb_1": "17"})[0] == 404
    with server.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
    auth.tambah_akun("pengelola", SANDI_GURU, "admin", path=auth.BERKAS_SANDI)
    assert server.minta(f"/sesi/{sesi}", auth=("pengelola", SANDI_GURU))[0] == 200


@pytest.mark.parametrize("keluarga", (*KELUARGA, "salah-konfigurasi"))
def test_kegagalan_visual_rollback_bank_dan_sesi(server, monkeypatch, keluarga):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", SEMUA_KELUARGA)
    butir = contoh()
    indeks = KELUARGA.index(keluarga) if keluarga in KELUARGA else 0
    rusak = replace(butir[indeks], parameter={**butir[indeks].parameter, "kunci": "RAHASIA"})
    if keluarga not in KELUARGA:
        monkeypatch.setenv("OSN_VISUAL_KELUARGA", keluarga)
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "Fixture", pemilik="guru")
        sebelum = tuple(kon.iterdump())
        with pytest.raises(ValueError):
            buat(kon, siswa, (butir[(indeks + 1) % len(butir)], rusak))
        assert tuple(kon.iterdump()) == sebelum


@pytest.mark.parametrize("nama,level,tid", CONTOH)
def test_remedial_visual_lewat_handler_asli(server, monkeypatch, nama, level, tid):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", SEMUA_KELUARGA)
    soal = buat_soal(nama, level, tid, 31)
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "Fixture remedial", tingkat=level, pemilik="guru")
        sumber = database.buat_sesi_dari_urutan(kon, siswa, seed=31, urutan=(tid,),
            topik=nama, level=level, soal_terpilih=(soal,))
        butir, = database.isi_sesi(kon, sumber)
        database.simpan_jawaban(kon, butir["sesi_soal_id"], jawaban="-999999", cara="Cara uji")
        reports.diagnosa_murid(kon, sumber)
        database.tandai_selesai(kon, sumber)
        kon.execute("UPDATE sesi SET direview=datetime('now') WHERE id=?", (sumber,))
    kode, isi, _ = server.minta(f"/sesi-remedial/{siswa}", auth=("guru", SANDI_GURU),
                              data={"template_id": tid, "jumlah_soal": "4"})
    assert kode == 200 and "Remedial" in isi
    with server.buka() as kon:
        baru = kon.execute("SELECT id FROM sesi WHERE siswa_id=? ORDER BY id DESC", (siswa,)).fetchone()[0]
        butir = database.isi_sesi(kon, baru)
        assert baru != sumber and len(butir) == 4
        assert all(b["template_id"] == tid and b["status_visual"] == "siap" for b in butir)
    kode, isi, _ = server.minta(f"/lembar/{baru}", auth=("guru", SANDI_GURU))
    assert kode == 200 and len(gambar(isi)) == 4
