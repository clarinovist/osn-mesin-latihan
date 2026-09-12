"""Regresi integrasi hasil review independen; fixture data sintetis saja."""
from pathlib import Path
import re
import sys
from html.parser import HTMLParser
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import assistant_actions
import assistant_http
import assistant_policy
import assistant_schema
import assistant_store
import auth
import database
from test_assistant_actions import server as server_usulan, _buat_usulan_http, _origin
from test_assistant_context_http import server as server_konteks
from test_assistant_runtime import server, _token_guru, _consent



class Markup(HTMLParser):
    def __init__(self, isi):
        super().__init__()
        self.links = []
        self.fields = {}
        self.feed(isi)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a': self.links.append(d)
        if tag == 'input' and d.get('type') == 'hidden': self.fields[d['name']] = d.get('value', '')




def snapshot(server):
    with server.buka() as k: belajar = tuple(k.iterdump())
    with assistant_schema.buka() as k: privat = tuple(k.iterdump())
    return belajar, privat


def post(server, token, path, data):
    return server.minta(path, cookie=token, data=data, headers=_origin(server))


@pytest.mark.parametrize('jenis', ('anak', 'sesi', 'soal'))
def test_batal_consent_kembali_sumber_semula(server_konteks, jenis):
    s = server_konteks
    token = _token_guru(s)
    anak, sesi, _, _ = s.konteks_ids
    identitas = str(anak) if jenis == 'anak' else (str(sesi) if jenis == 'sesi' else str(sesi)+':1')
    path = '/pendamping/konteks/'+jenis+'/'+identitas
    kode, isi, _ = s.minta(path, cookie=token)
    assert kode == 200 and 'Sebelum mulai' in isi
    tujuan = '/anak/'+str(anak) if jenis=='anak' else '/sesi/'+str(sesi)
    # Consent provider belum diberikan. Batal bukan sekaligus kehilangan asal.
    assert tujuan in [a['href'] for a in Markup(isi).links]
    assert s.provider.panggilan == []
    kode, galat, _ = post(s,token,'/pendamping/persetujuan',{'kebijakan':assistant_policy.VERSI_KEBIJAKAN,'lanjut':path})
    assert kode==400
    assert tujuan in [a['href'] for a in Markup(galat).links]
    assert s.provider.panggilan == []


def test_hasil_commit_utama_tetap_terjangkau_chat_saat_pointer_privat_belum_commit(server_usulan, monkeypatch):
    s = server_usulan
    token, cid, uid = _buat_usulan_http(s)
    akun = auth.cari_akun('guru')['id_akun']
    kode, tinjau, _ = s.minta('/pendamping/usulan/'+uid, cookie=token)
    data = Markup(tinjau).fields
    def gagal(*a, **kw):
        raise RuntimeError('crash sintetis sesudah commit belajar')
    with monkeypatch.context() as mp:
        mp.setattr(assistant_store, 'selesaikan_usulan', gagal)
        with assistant_schema.buka() as kon:
            with pytest.raises(RuntimeError, match='crash sintetis'):
                assistant_actions.konfirmasi_dan_buat_sesi(kon, akun, 'guru', uid,
                    versi=int(data['versi']),hash_diharapkan=data['hash'],
                    request_id=data['request_id'],sekarang=__import__('time').time().__int__())
    with assistant_schema.buka() as kon:
        assert assistant_store.ambil_usulan(kon,akun,uid).sesi_id is None
    with s.buka() as kon:
        assert kon.execute('SELECT COUNT(*) FROM eksekusi_pendamping').fetchone()[0] == 1
    sebelum = snapshot(s)
    kode, hasil, _ = s.minta('/pendamping/usulan/'+uid,cookie=token)
    assert kode == 200 and 'Sesi #' in hasil  # Recovery service tersedia.
    kode, isi, _ = s.minta('/pendamping/chat/'+cid,cookie=token)
    assert kode == 200 and 'hanya dapat dibaca' in isi
    assert snapshot(s) == sebelum
    assert '/pendamping/chat/'+cid+'/pesan' not in isi
    assert '/pendamping/usulan/'+uid in [a['href'] for a in Markup(isi).links]


def test_konflik_toggle_memori_tetap_mempertahankan_chat_asal(server):
    s=server; token=_token_guru(s);_consent(s,token); akun=auth.cari_akun('guru')['id_akun']
    with assistant_schema.buka() as kon:
        c=assistant_store.buat_chat(kon,akun,'tanpa_memori',sekarang=100)
    kode,isi,_=s.minta('/pendamping/memori?kembali='+c.id,cookie=token)
    data=Markup(isi).fields
    with assistant_schema.buka() as kon:
        assistant_store.atur_penggunaan_memori(kon,akun,False,versi_diharapkan=0,sekarang=101)
    sebelum=snapshot(s)
    kode,galat,_=post(s,token,'/pendamping/memori/aktifkan',data)
    assert kode==409 and snapshot(s)==sebelum
    assert 'Memori nonaktif' in galat
    assert Markup(galat).fields.get('kembali')==c.id
    assert '/pendamping/chat/'+c.id in [a['href'] for a in Markup(galat).links]
    kode,galat,_=post(s,token,'/pendamping/memori/aktifkan',{'versi':'bukan-angka','kembali':c.id})
    assert kode==400 and snapshot(s)==sebelum
    assert Markup(galat).fields.get('kembali')==c.id


@pytest.mark.parametrize('jenis', ('anak','sesi','soal'))
def test_r2_native_details_tidak_mengganti_chat_sumber(server_konteks,jenis):
    s=server_konteks;token=_token_guru(s);_consent(s,token)
    anak,sesi,_,_=s.konteks_ids
    rid=str(anak) if jenis=='anak' else str(sesi)+(':1' if jenis=='soal' else '')
    kode,isi,_=s.minta('/pendamping/konteks/'+jenis+'/'+rid,cookie=token)
    fields=Markup(isi).fields
    assert kode==200
    kode,chat,_=post(s,token,'/pendamping/konteks/pilih',fields)
    assert kode==200
    assert '<details class="pendamping-ganti-sumber">' in chat
    assert 'Tutup rincian ini untuk tetap di chat yang sama.' in chat
    assert '/pendamping/konteks/ganti' not in chat
    before=snapshot(s)
    assert len(s.provider.panggilan)==0
    # Membuka/menutup details native tidak request HTTP; GET ulang pun tidak menulis.
    cid=re.search(r'action="/pendamping/chat/(chat_[0-9a-f]{32})/pesan"',chat).group(1)
    assert s.minta('/pendamping/chat/'+cid,cookie=token)[0]==200
    assert snapshot(s)==before


def test_r1_r5_r6_lima_puluh_riwayat_dan_kembali(server):
    s=server;token=_token_guru(s);_consent(s,token);akun=auth.cari_akun('guru')['id_akun']
    chats=[]
    with assistant_schema.buka() as kon:
        for i in range(50):chats.append(assistant_store.buat_chat(kon,akun,'aktif',sekarang=100+i))
    before=snapshot(s)
    kode,awal,_=s.minta('/pendamping',cookie=token)
    assert kode==200 and [a['href'] for a in Markup(awal).links].count('/guru')==1
    assert '/pendamping/riwayat' in [a['href'] for a in Markup(awal).links]
    found=[]
    for p,n in ((1,20),(2,20),(3,10)):
        kode,isi,_=s.minta('/pendamping/riwayat?halaman='+str(p),cookie=token)
        assert kode==200
        links=Markup(isi).links
        assert not [a for a in links if a.get('aria-current')]
        hrefs=[a['href'] for a in links if a['href'].startswith('/pendamping/chat/')]
        assert len(hrefs)==n
        found+=hrefs
        if p<3:assert '/pendamping/riwayat?halaman='+str(p+1) in [a['href'] for a in links]
    assert len(set(found))==50
    kode,isi,_=s.minta('/pendamping/chat/'+chats[-4].id,cookie=token)
    aktif=[a['href'] for a in Markup(isi).links if a.get('aria-current')]
    assert aktif==['/pendamping/chat/'+chats[-4].id]
    assert snapshot(s)==before and not s.provider.panggilan


def test_foreign_sumber_dan_return_memori_post_tanpa_mutasi(server_konteks):
    s=server_konteks;token=_token_guru(s);_consent(s,token);akun=auth.cari_akun('guru')['id_akun']
    anak,sesi,asing,sesi_asing=s.konteks_ids
    with assistant_schema.buka() as kon:
        c=assistant_store.buat_chat(kon,'akun_'+'b'*32,'aktif',sekarang=100)
    before=snapshot(s)
    a=post(s,token,'/pendamping/memori/aktifkan',{'versi':'0','kembali':c.id})
    b=post(s,token,'/pendamping/memori/aktifkan',{'versi':'0','kembali':'chat_'+'f'*32})
    assert a[0]==b[0]==404 and a[1]==b[1]
    for jenis,r1,r2 in [('anak',str(asing),'999999'),('sesi',str(sesi_asing),'999999'),('soal',str(sesi_asing)+':1','999999:1')]:
        a=s.minta('/pendamping/konteks/'+jenis+'/'+r1,cookie=token)
        b=s.minta('/pendamping/konteks/'+jenis+'/'+r2,cookie=token)
        assert a[0]==b[0]==404 and a[1]==b[1]
    assert snapshot(s)==before and not s.provider.panggilan
