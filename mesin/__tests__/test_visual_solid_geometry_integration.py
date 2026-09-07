"""Integrasi ruang memakai snapshot yang sama pada seluruh permukaan."""
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
import topic_solid_geometry as g
from http_test_kit import ServerUji, SANDI_GURU, SANDI_MURID
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan


@pytest.fixture()
def db(tmp_path):
    jalur = tmp_path / 'ruang.db'
    database.siapkan(jalur)
    return jalur


@pytest.fixture()
def server(tmp_path, monkeypatch):
    layanan = ServerUji(tmp_path, monkeypatch)
    try:
        yield layanan
    finally:
        layanan.berhenti()


def contoh():
    return (g.jaring_jaring(1, (1, 0, 1, 2, 3), versi=2),
            g.volume_kubus_balok('kubus_cari_s', s=4, V=64),
            g.volume_prisma_tabung('tabung_V', r=2, t=3, versi=2),
            g.kubus_dicat(5, 'dua_sisi_kali', 3))


def buat(kon, siswa, soal=None):
    butir = tuple(replace(s, level='P6') for s in (contoh() if soal is None else soal))
    return database.buat_sesi_dari_urutan(
        kon, siswa, seed=41, urutan=tuple(s.template_id for s in butir),
        topik='geometri-ruang', level='P6', soal_terpilih=butir)


@pytest.mark.parametrize('flag', ('geometri-ruang', 'statistika,geometri-datar,geometri-ruang'))
def test_optin_tidak_mengubah_identitas_matematis(monkeypatch, flag):
    monkeypatch.delenv('OSN_VISUAL_KELUARGA', raising=False)
    soal = contoh()[2]
    lama = q.penyajian_dari_soal(soal)
    assert lama.status_visual == 'tanpa_visual'
    monkeypatch.setenv('OSN_VISUAL_KELUARGA', flag)
    baru = q.penyajian_dari_soal(soal)
    assert baru.mode_representasi == 'geometri_ruang-v1'
    assert baru.fingerprint_matematis == lama.fingerprint_matematis
    assert baru.fingerprint_penyajian != lama.fingerprint_penyajian
    assert '<svg' in render_pertanyaan(baru)


def test_snapshot_lama_tetap_teks_flag_off_masih_membaca_visual(db, monkeypatch):
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, 'Fixture', pemilik='guru')
        monkeypatch.delenv('OSN_VISUAL_KELUARGA', raising=False)
        lama = buat(kon, siswa)
        sebelum = tuple(b['penyajian_json'] for b in database.isi_sesi(kon, lama))
        monkeypatch.setenv('OSN_VISUAL_KELUARGA', 'geometri-ruang')
        baru = buat(kon, siswa)
        monkeypatch.delenv('OSN_VISUAL_KELUARGA')
        for b in database.isi_sesi(kon, baru):
            assert '<svg' in render_pertanyaan(q.penyajian_dari_baris(b))
        assert tuple(b['penyajian_json'] for b in database.isi_sesi(kon, lama)) == sebelum
        assert kon.execute('SELECT COUNT(*) FROM soal').fetchone()[0] == 4


def test_visual_invalid_rollback_seluruh_sesi(db, monkeypatch):
    monkeypatch.setenv('OSN_VISUAL_KELUARGA', 'geometri-ruang')
    rusak = replace(contoh()[1], parameter={'varian': 'kubus_cari_s', 'V': 64, 's': 4, 'html': '<svg>'})
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, 'Fixture', pemilik='guru')
        with pytest.raises(ValueError):
            buat(kon, siswa, (contoh()[0], rusak))
        for tabel in ('sesi', 'sesi_soal', 'soal'):
            assert kon.execute(f'SELECT COUNT(*) FROM {tabel}').fetchone()[0] == 0


def test_query_dan_ringkasan_aman_tanpa_rahasia(db, monkeypatch):
    monkeypatch.setenv('OSN_VISUAL_KELUARGA', 'geometri-ruang')
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, 'Fixture', pemilik='guru')
        sesi = buat(kon, siswa)
        def palang(aksi, tabel, kolom, _db, _pemicu):
            if aksi == sqlite3.SQLITE_READ and kolom in {'kunci', 'malrule_id', 'kode_final', 'kode_usulan', 'alasan'}:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        kon.set_authorizer(palang)
        try:
            assert students.soal_murid(kon, sesi, siswa)
            penyajian = q.penyajian_sesi_aman(kon, sesi)
        finally:
            kon.set_authorizer(lambda *_: sqlite3.SQLITE_OK)
    for p in penyajian:
        ringkas = ringkasan_pertanyaan(p)
        assert ringkas and not any(k in ringkas for k in ('<svg', 'kunci', 'malrule', 'diagnosis'))
    assert '64 cm³' in ringkasan_pertanyaan(penyajian[1])
    assert 'rusuk 4 cm' not in ringkasan_pertanyaan(penyajian[1])


def _svg(isi):
    return re.findall(r'<svg[^>]*role="img".*?</svg>', isi, flags=re.S)


def test_http_share_murid_guru_cetak_simpan_reload_hasil(server, monkeypatch):
    monkeypatch.setenv('OSN_VISUAL_KELUARGA', 'geometri-ruang')
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, 'feby', pemilik='guru')
        sesi = buat(kon, siswa)
        token = share_links.buat(kon, sesi)
        baris = database.isi_sesi(kon, sesi)
        sidik = tuple(b['fingerprint_penyajian'] for b in baris)
        ssid = baris[0]['sesi_soal_id']
    monkeypatch.delenv('OSN_VISUAL_KELUARGA')
    target = ((f'/mulai/{token}', None), (f'/murid/kerjakan/{sesi}', ('feby', SANDI_MURID)),
              (f'/sesi/{sesi}', ('guru', SANDI_GURU)), (f'/lembar/{sesi}', ('guru', SANDI_GURU)))
    hasil = ()
    for jalur, auth in target:
        kode, isi, _ = server.minta(jalur, auth=auth)
        assert kode == 200
        assert all(s in isi for s in sidik)
        assert len(_svg(isi)) == 4
        hasil += (tuple(_svg(isi)),)
    assert all(h == hasil[0] for h in hasil)
    assert server.minta(f'/mulai/{token}', data={f'jwb_{ssid}': 'B'})[0] == 200
    assert tuple(_svg(server.minta(f'/mulai/{token}')[1])) == hasil[0]
    with server.buka() as kon:
        assert kon.execute('SELECT jawaban FROM jawaban WHERE sesi_soal_id=?', (ssid,)).fetchone()[0] == 'B'
        assert tuple(b['fingerprint_penyajian'] for b in database.isi_sesi(kon, sesi)) == sidik
        assert students.hasil_murid(kon, siswa, sesi) is None
        import reports
        reports.diagnosa_murid(kon, sesi)
        database.tandai_selesai(kon, sesi)
        kon.execute("UPDATE sesi SET direview=datetime('now') WHERE id=?", (sesi,))
    kode, isi, _ = server.minta(f'/murid/hasil/{sesi}', auth=('feby', SANDI_MURID))
    assert kode == 200 and tuple(_svg(isi)) == hasil[0]


@pytest.mark.parametrize('pilihan', ('geometri-ruang', 'campuran', 'gabungan'))
def test_sesi_biasa_campuran_gabungan(db, monkeypatch, pilihan):
    monkeypatch.setenv('OSN_VISUAL_KELUARGA', 'statistika,geometri-datar,geometri-ruang')
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, 'Fixture', pemilik='guru')
        if pilihan == 'gabungan':
            sesi = database.buat_sesi_gabungan(kon, siswa, seed=41,
                topik_ids=['geometri-ruang', 'statistika'], level='P6', jumlah_soal=50)
        else:
            sesi = database.buat_sesi(kon, siswa, seed=41, topik=pilihan, level='P6', jumlah_soal=50)
        baris = tuple(b for b in database.isi_sesi(kon, sesi)
                      if b['template_id'] in g.REGISTRI_TOPIK and b['template_id'] != 'perbandingan_volume')
        assert baris
        for b in baris:
            assert q.penyajian_dari_baris(b).mode_representasi == 'geometri_ruang-v1'
