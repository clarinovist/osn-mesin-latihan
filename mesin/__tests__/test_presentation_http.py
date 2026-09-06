"""E2E penyajian sesi memakai socket dan DB fixture saja."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import database
import presentation_lock
import share_links
from visual_contract import DescriptorVisual, buat_penyajian
from http_test_kit import ServerUji, SANDI_GURU, SANDI_MURID


@pytest.fixture()
def server(tmp_path, monkeypatch):
    srv = ServerUji(tmp_path, monkeypatch)
    try:
        yield srv
    finally:
        srv.berhenti()


def pasang_visual(kon, sesi):
    baris = next(b for b in database.isi_sesi(kon, sesi) if b['template_id'] == 'korek_api')
    p = json.loads(baris['parameter'])
    snapshot = buat_penyajian(
        template_id=baris['template_id'], level=baris['level'], parameter=p,
        teks_soal='Amati pola batang.\nBerapa batang pada gambar berikutnya?',
        bagian_soal=baris['bagian'], status_visual='siap', mode_representasi='korek-v1',
        descriptor=DescriptorVisual('korek', 1, {'n_tampil': 3, 'awal': p['awal'], 'tambah': p['tambah']}),
    )
    assert presentation_lock.perbarui_snapshot(kon, baris['sesi_soal_id'], baris['fingerprint_penyajian'], snapshot)
    return baris['sesi_soal_id'], snapshot.fingerprint_penyajian


@pytest.mark.parametrize('mode', ['diagnostik', 'drill'])
def test_http_snapshot_sama_di_share_murid_guru_cetak_dan_reload(server, mode):
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, 'feby', pemilik='guru')
        sesi = database.buat_sesi(kon, siswa, seed=42, mode=mode)
        ssid, sidik = pasang_visual(kon, sesi)
        token = share_links.buat(kon, sesi)
    target = [
        (f'/mulai/{token}', None),
        (f'/murid/kerjakan/{sesi}', ('feby', SANDI_MURID)),
        (f'/sesi/{sesi}', ('guru', SANDI_GURU)),
        (f'/lembar/{sesi}', ('guru', SANDI_GURU)),
    ]
    gambar = []
    for jalur, ident in target:
        kode, isi, _ = server.minta(jalur, auth=ident)
        assert kode == 200
        assert f'data-fingerprint-penyajian="{sidik}"' in isi
        svg = re.findall(r'<svg[^>]*role="img".*?</svg>', isi, flags=re.S)
        assert svg
        gambar.append(svg)
    assert all(g == gambar[0] for g in gambar)
    kode, _, _ = server.minta(f'/mulai/{token}', data={f'jwb_{ssid}': '17'})
    assert kode == 200
    kode, isi, _ = server.minta(f'/mulai/{token}')
    assert kode == 200
    assert f'data-fingerprint-penyajian="{sidik}"' in isi
    with server.buka() as kon:
        assert kon.execute('SELECT jawaban FROM jawaban WHERE sesi_soal_id = ?', (ssid,)).fetchone()[0] == '17'
        assert kon.execute('SELECT fingerprint_penyajian FROM sesi_soal WHERE id = ?', (ssid,)).fetchone()[0] == sidik
