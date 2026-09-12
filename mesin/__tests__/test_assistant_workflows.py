"""Alur UI Pendamping lewat HTTP nyata dengan fixture sepenuhnya sintetis."""
from pathlib import Path
import re
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import assistant_policy
import assistant_schema
import assistant_store
import auth
import database
import assistant_context
import assistant_service
import sessions
from test_assistant_actions import server as server_usulan, _buat_usulan_http, _origin
from test_assistant_runtime import server, _token_guru, _consent


def _post(server, token, path, data):
    return server.minta(path, cookie=token, data=data, headers={
        'Origin': server.alamat, 'Sec-Fetch-Site': 'same-origin',
    })


def test_chat_tanpa_memori_get_dan_input_kosong_tidak_membuat_chat(server):
    token = _token_guru(server)
    _consent(server, token)
    akun = auth.cari_akun('guru')['id_akun']
    kode, isi, _ = server.minta('/pendamping/tanpa-memori', cookie=token)
    assert kode == 200
    assert 'name="mode" value="tanpa_memori"' in isi
    with assistant_schema.buka() as kon:
        assert assistant_store.daftar_chat(kon, akun) == ()
    kode, _, _ = _post(server, token, '/pendamping/chat-baru', {
        'mode': 'aktif', 'pesan_awal': '  ', 'request_id': 'req_kosong_sintetis',
    })
    assert kode == 400
    with assistant_schema.buka() as kon:
        assert assistant_store.daftar_chat(kon, akun) == ()
    assert server.provider.panggilan == []


def test_riwayat_paging_terjangkau_dan_tidak_mengklaim_item_aktif(server):
    token = _token_guru(server)
    _consent(server, token)
    akun = auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        for i in range(45):
            assistant_store.buat_chat(kon, akun, 'aktif', sekarang=100+i)
    kode, awal, _ = server.minta('/pendamping', cookie=token)
    assert kode == 200 and 'href="/pendamping/riwayat"' in awal
    for nomor, jumlah in [(1, 20), (2, 20), (3, 5)]:
        kode, isi, _ = server.minta('/pendamping/riwayat?halaman='+str(nomor), cookie=token)
        assert kode == 200
        # Daftar utama, bukan daftar sidebar duplikat.
        assert len(re.findall(r'href="/pendamping/chat/chat_[0-9a-f]{32}"', isi)) == jumlah
        assert not re.search(r'<a\b[^>]*aria-current="page"', isi)
    kode, _, _ = server.minta('/pendamping/riwayat?halaman=1&halaman=2', cookie=token)
    assert kode == 404
    assert server.provider.panggilan == []


def test_editor_batal_memori_nonaktif_menjaga_state_dan_chat_asal(server):
    token = _token_guru(server)
    _consent(server, token)
    akun = auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        chat = assistant_store.buat_chat(kon, akun, 'tanpa_memori', sekarang=100)
        item = assistant_store.tambah_memori(kon, akun, 'Jawab ringkas.',
                    sumber_chat_id=chat.id, dikonfirmasi=True, sekarang=100)
    with assistant_schema.buka() as kon:
        sebelum = tuple(kon.iterdump())
    path='/pendamping/memori/'+item.id+'/ubah?kembali='+chat.id
    kode, isi, _ = server.minta(path, cookie=token)
    assert kode == 200
    assert 'name="kembali" value="'+chat.id+'"' in isi
    assert '/pendamping/memori?kembali='+chat.id in isi
    kode, isi, _ = server.minta('/pendamping/memori?kembali='+chat.id, cookie=token)
    assert kode == 200
    assert 'nonaktif' in isi.lower()
    assert 'href="/pendamping/chat/'+chat.id+'"' in isi
    with assistant_schema.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
        assert not assistant_store.penggunaan_memori_aktif(kon, akun)


def test_hapus_memori_wajib_persetujuan_eksplisit_tanpa_mutasi(server):
    token = _token_guru(server)
    _consent(server, token)
    akun = auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        item = assistant_store.tambah_memori(kon, akun, 'Jawab ringkas.',
                    sumber_chat_id=None, dikonfirmasi=True, sekarang=100)
    with assistant_schema.buka() as kon:
        sebelum=tuple(kon.iterdump())
    kode, _, _ = _post(server, token, '/pendamping/memori/'+item.id+'/hapus', {'versi':str(item.versi)})
    assert kode == 400
    with assistant_schema.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
    kode, _, _ = _post(server, token, '/pendamping/memori/'+item.id+'/hapus',
                       {'versi':str(item.versi),'persetujuan_hapus':'1'})
    assert kode == 200
    with assistant_schema.buka() as kon:
        assert assistant_store.daftar_memori(kon, akun)==()


def _form_tinjau(isi):
    return {k: re.search(r'name="'+k+r'" value="([^"]+)"', isi).group(1)
            for k in ('versi','hash','request_id')}


def test_riwayat_chat_stale_tetap_punya_hasil_yang_sama(server_usulan):
    server = server_usulan
    token, chat_id, usulan_id = _buat_usulan_http(server)
    kode, tinjau, _ = server.minta('/pendamping/usulan/'+usulan_id, cookie=token)
    assert kode == 200
    data = _form_tinjau(tinjau)
    assert _post(server,token,'/pendamping/usulan/'+usulan_id+'/konfirmasi',data)[0]==200
    with server.buka() as kon:
        sebelum=tuple(kon.iterdump())
    kode, chat, _=server.minta('/pendamping/chat/'+chat_id,cookie=token)
    assert kode==200
    assert 'hanya dapat dibaca' in chat
    assert 'action="/pendamping/chat/'+chat_id+'/pesan"' not in chat
    assert 'href="/pendamping/usulan/'+usulan_id+'"' in chat
    kode, hasil, _=server.minta('/pendamping/usulan/'+usulan_id,cookie=token)
    assert kode==200 and 'Sesi #' in hasil
    assert 'href="/pendamping/chat/'+chat_id+'"' in hasil
    assert _post(server,token,'/pendamping/usulan/'+usulan_id+'/konfirmasi',data)[0]==200
    with server.buka() as kon:
        assert tuple(kon.iterdump())==sebelum


def test_provider_consent_kembali_sumber_dan_nama_tidak_ikut_ai(server_usulan):
    server=server_usulan
    token=_token_guru(server)
    tujuan='/pendamping/konteks/anak/'+str(server.anak)
    kode, isi, _=server.minta(tujuan,cookie=token)
    assert kode==200 and 'Sebelum mulai' in isi
    assert 'name="lanjut" value="'+tujuan+'"' in isi
    assert 'Anak Usulan' not in isi
    kode, pilih, _=_post(server,token,'/pendamping/persetujuan',{
        'setuju':'1','kebijakan':assistant_policy.VERSI_KEBIJAKAN,'lanjut':tujuan})
    assert kode==200 and 'Anak Usulan' in pilih
    versi=re.search(r'name="resource_version" value="([0-9a-f]+)"',pilih).group(1)
    kode, chat, _=_post(server,token,'/pendamping/konteks/pilih',{
        'jenis':'anak','resource_id':str(server.anak),'resource_version':versi,'kategori':'ringkasan_netral','mode':'aktif'})
    assert kode==200
    chat_id=re.search(r'action="/pendamping/chat/(chat_[0-9a-f]+)/pesan"',chat).group(1)
    req=re.search(r'name="request_id" value="([^"]+)"',chat).group(1)
    assert _post(server,token,'/pendamping/chat/'+chat_id+'/pesan',{'pesan':'Bantu latihan.','request_id':req})[0]==200
    assert 'Anak Usulan' not in str(server.provider.panggilan)


def test_konteks_dipindah_pemilik_404_tanpa_bocor_transkrip(server_usulan):
    server=server_usulan
    token, chat_id, _=_buat_usulan_http(server)
    with server.buka() as kon:
        kon.execute("UPDATE siswa SET pemilik='orang-lain' WHERE id=?",(server.anak,))
    with assistant_schema.buka() as kon:
        sebelum=tuple(kon.iterdump())
    asing=server.minta('/pendamping/chat/'+chat_id,cookie=token)
    hilang=server.minta('/pendamping/chat/chat_'+'f'*32,cookie=token)
    assert asing[0]==hilang[0]==404 and asing[1]==hilang[1]
    assert 'Tolong usulkan latihan' not in asing[1]
    with assistant_schema.buka() as kon:
        assert tuple(kon.iterdump())==sebelum


def test_konteks_dicabut_tidak_boleh_baca_atau_kirim(server_usulan):
    server=server_usulan
    token, chat_id, _=_buat_usulan_http(server)
    akun=auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        izin=kon.execute('SELECT id,versi FROM persetujuan_konteks WHERE account_id=?',(akun,)).fetchone()
        assistant_store.cabut_persetujuan_konteks(kon,akun,izin['id'],versi_diharapkan=izin['versi'],sekarang=500)
    sebelum=len(server.provider.panggilan)
    kode, isi, _=server.minta('/pendamping/chat/'+chat_id,cookie=token)
    assert kode==409 and 'Tolong usulkan latihan' not in isi
    kode, _, _=_post(server,token,'/pendamping/chat/'+chat_id+'/pesan',{'pesan':'Ulangi.','request_id':'req_dicabut_baru'})
    assert kode==409 and len(server.provider.panggilan)==sebelum


def test_status_pending_owner_guard_nol_provider_dan_mutasi(server):
    token=_token_guru(server)
    _consent(server,token)
    akun=auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        chat=assistant_store.buat_chat(kon,akun,'aktif',sekarang=100)
        assistant_store.mulai_operasi(kon,akun,chat.id,'req_pending_sintetis',
            consent_version=assistant_store.versi_persetujuan(kon,akun),memory_version=0,context_version=0,sekarang=100)
    with assistant_schema.buka() as kon:
        sebelum=tuple(kon.iterdump())
    kode, isi, _=server.minta('/pendamping/operasi/req_pending_sintetis',cookie=token)
    assert kode==200 and 'Jangan kirim ulang' in isi
    assert '<textarea' not in isi
    assert server.provider.panggilan==[]
    with assistant_schema.buka() as kon:
        assert tuple(kon.iterdump())==sebelum
    auth.tambah_akun('ortu-lain','sandi-sintetis-lain','guru')
    lain=auth.cari_akun('ortu-lain')
    token_b=sessions.buat(lain['pengguna'],'guru',id_akun=lain['id_akun'])
    _consent(server,token_b)
    a=server.minta('/pendamping/operasi/req_pending_sintetis',cookie=token_b)
    b=server.minta('/pendamping/operasi/req_hilang_sintetis',cookie=token_b)
    assert a[0]==b[0]==404 and a[1]==b[1]


def test_provider_consent_terbaru_dicabut_tidak_fallback_izin_lama(server):
    token=_token_guru(server)
    _consent(server,token)
    _consent(server,token)
    akun=auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        izin=kon.execute('SELECT id,versi FROM persetujuan WHERE account_id=? ORDER BY versi DESC LIMIT 1',(akun,)).fetchone()
        assistant_store.cabut_persetujuan(kon,akun,izin['id'],versi_diharapkan=izin['versi'],sekarang=500)
    kode,isi,_=server.minta('/pendamping',cookie=token)
    assert kode==200 and 'Sebelum mulai' in isi
    assert 'action="/pendamping/chat-baru"' not in isi
    assert _post(server,token,'/pendamping/chat-baru',{'mode':'aktif','pesan_awal':'Halo.','request_id':'req_consent_dicabut'})[0]==409
    assert server.provider.panggilan==[]


def test_hapus_semua_saat_catatan_sudah_kosong_tidak_error_server(server):
    token=_token_guru(server)
    _consent(server,token)
    with assistant_schema.buka() as kon:
        sebelum=tuple(kon.iterdump())
    kode,_,_=_post(server,token,'/pendamping/memori/hapus-semua',{'versi':'0'})
    assert kode==404
    with assistant_schema.buka() as kon:
        assert tuple(kon.iterdump())==sebelum
    assert server.provider.panggilan==[]


def test_tujuan_memori_asing_dan_hilang_404_tanpa_efek(server):
    token=_token_guru(server)
    _consent(server,token)
    with assistant_schema.buka() as kon:
        chat=assistant_store.buat_chat(kon,'akun_'+'b'*32,'aktif',sekarang=100)
        sebelum=tuple(kon.iterdump())
    a=server.minta('/pendamping/memori?kembali='+chat.id,cookie=token)
    b=server.minta('/pendamping/memori?kembali=chat_'+'f'*32,cookie=token)
    assert a[0]==b[0]==404 and a[1]==b[1]
    with assistant_schema.buka() as kon:
        assert tuple(kon.iterdump())==sebelum
