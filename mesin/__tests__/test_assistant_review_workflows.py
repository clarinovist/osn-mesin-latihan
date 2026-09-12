"""Regresi integrasi guard lama setelah cutover ke host inline/arsip."""
from pathlib import Path
import re
import sys
from html.parser import HTMLParser

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import assistant_actions
import assistant_policy
import assistant_schema
import assistant_store
import auth
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
        data = dict(attrs)
        if tag == "a":
            self.links.append(data)
        if tag == "input" and data.get("type") == "hidden":
            self.fields[data["name"]] = data.get("value", "")


def snapshot(server):
    with server.buka() as kon:
        belajar = tuple(kon.iterdump())
    with assistant_schema.buka() as kon:
        privat = tuple(kon.iterdump())
    return belajar, privat


def post(server, token, path, data):
    return server.minta(path, cookie=token, data=data, headers=_origin(server))


@pytest.mark.parametrize("jenis", ("anak", "sesi", "soal"))
def test_adapter_konteks_lama_mendarat_di_host_tanpa_efek_otomatis(server_konteks, jenis):
    server = server_konteks
    token = _token_guru(server)
    anak, sesi, _, _ = server.konteks_ids
    identitas = str(anak) if jenis == "anak" else (str(sesi) if jenis == "sesi" else f"{sesi}:1")
    sebelum = snapshot(server)
    kode, isi, header = server.minta(f"/pendamping/konteks/{jenis}/{identitas}", cookie=token)
    assert kode == 200 and "Sebelum memakai bantuan" in isi
    assert "/pendamping/inline/tutup" in isi
    assert header["Cache-Control"] == "no-store"
    assert server.provider.panggilan == []
    if jenis == "anak":
        assert snapshot(server) == sebelum


def test_hasil_commit_utama_tetap_terjangkau_saat_pointer_privat_belum_commit(server_usulan, monkeypatch):
    server = server_usulan
    token, chat_id, usulan_id = _buat_usulan_http(server)
    akun = auth.cari_akun("guru")["id_akun"]
    kode, tinjau, _ = server.minta(f"/pendamping/usulan/{usulan_id}", cookie=token)
    field = Markup(tinjau).fields

    def gagal(*_arg, **_kw):
        raise RuntimeError("crash sintetis sesudah commit belajar")

    with monkeypatch.context() as mp:
        mp.setattr(assistant_store, "selesaikan_usulan", gagal)
        with assistant_schema.buka() as kon:
            with pytest.raises(RuntimeError, match="crash sintetis"):
                assistant_actions.konfirmasi_dan_buat_sesi(
                    kon, akun, "guru", usulan_id,
                    versi=int(field["versi_usulan"]),
                    hash_diharapkan=field["hash_usulan"],
                    request_id=field["request_id"],
                    sekarang=int(__import__("time").time()),
                )
    with server.buka() as kon:
        assert kon.execute("SELECT COUNT(*) FROM eksekusi_pendamping").fetchone()[0] == 1
    sebelum = snapshot(server)
    kode, hasil, _ = server.minta(f"/pendamping/usulan/{usulan_id}", cookie=token)
    assert kode == 200 and "Latihan bebas #" in hasil
    kode, chat, _ = server.minta(f"/pendamping/chat/{chat_id}", cookie=token)
    assert kode == 200 and "hanya dapat dibaca" in chat
    assert "Pesan untuk Pendamping" not in chat
    assert snapshot(server) == sebelum


def test_chat_umum_lama_dan_memori_hanya_arsip_tanpa_kontrol_mutasi(server):
    token = _token_guru(server)
    _consent(server, token)
    akun = auth.cari_akun("guru")["id_akun"]
    with assistant_schema.buka() as kon:
        chat = assistant_store.buat_chat(kon, akun, "tanpa_memori", sekarang=100)
        assistant_store.tambah_memori(
            kon, akun, "Jawab ringkas.", sumber_chat_id=chat.id,
            dikonfirmasi=True, sekarang=101,
        )
        kon.commit()
    sebelum = snapshot(server)
    kode, isi, _ = server.minta(
        f"/akun?section=arsip-pendamping&chat={chat.id}", cookie=token,
    )
    assert kode == 200 and "Arsip percakapan lama" in isi
    assert "aktifkan-memori" not in isi and "ubah-memori" not in isi
    assert snapshot(server) == sebelum


@pytest.mark.parametrize("jenis", ("anak", "sesi", "soal"))
def test_details_inline_tidak_mengganti_chat_sumber(server_konteks, jenis):
    server = server_konteks
    token = _token_guru(server)
    _consent(server, token)
    anak, sesi, _, _ = server.konteks_ids
    rid = str(anak) if jenis == "anak" else str(sesi) + (":1" if jenis == "soal" else "")
    kode, isi, _ = server.minta(f"/pendamping/konteks/{jenis}/{rid}", cookie=token)
    semua = Markup(isi).fields
    field = {
        k: semua[k] for k in ("resource_version", "kategori")
    }
    if jenis == "anak":
        field.update({"inline_host": "anak", "inline_host_id": str(anak),
                      "inline_posisi": "rencana"})
    else:
        field.update({"inline_host": "sesi", "inline_host_id": str(sesi),
                      "inline_posisi": jenis})
        if jenis == "soal":
            field["inline_nomor"] = "1"
    field.update({"setuju_konteks": "1", "mode_chat": "aktif",
                  "request_id": "buka_review_sintetis"})
    kode, chat, _ = post(server, token, "/pendamping/inline/mulai", field)
    assert kode == 200, (field, chat[:300])
    assert '<details class="pendamping-riwayat">' in chat
    chat_id = re.search(r'name="chat" value="(chat_[0-9a-f]{32})"', chat).group(1)
    sebelum = snapshot(server)
    assert server.minta(f"/pendamping/chat/{chat_id}", cookie=token)[0] == 200
    assert snapshot(server) == sebelum


def test_lima_puluh_chat_umum_hanya_di_arsip_paginated(server):
    token = _token_guru(server)
    _consent(server, token)
    akun = auth.cari_akun("guru")["id_akun"]
    with assistant_schema.buka() as kon:
        chats = tuple(
            assistant_store.buat_chat(kon, akun, "aktif", sekarang=100 + i)
            for i in range(50)
        )
        kon.commit()
    sebelum = snapshot(server)
    ditemukan = []
    for halaman, jumlah in ((1, 20), (2, 20), (3, 10)):
        kode, isi, _ = server.minta(
            f"/akun?section=arsip-pendamping&halaman={halaman}", cookie=token,
        )
        assert kode == 200
        href = [a["href"] for a in Markup(isi).links if "chat=" in a.get("href", "")]
        assert len(href) == jumlah
        ditemukan.extend(href)
    assert len(set(ditemukan)) == 50
    kode, isi, _ = server.minta(
        f"/akun?section=arsip-pendamping&chat={chats[-4].id}", cookie=token,
    )
    assert kode == 200 and "Transkrip yang dipilih" in isi
    assert snapshot(server) == sebelum


def test_foreign_sumber_dan_arsip_404_identik_tanpa_mutasi(server_konteks):
    server = server_konteks
    token = _token_guru(server)
    _consent(server, token)
    _, _, asing, sesi_asing = server.konteks_ids
    sebelum = snapshot(server)
    for jenis, foreign, hilang in (
        ("anak", str(asing), "999999"),
        ("sesi", str(sesi_asing), "999999"),
        ("soal", f"{sesi_asing}:1", "999999:1"),
    ):
        a = server.minta(f"/pendamping/konteks/{jenis}/{foreign}", cookie=token)
        b = server.minta(f"/pendamping/konteks/{jenis}/{hilang}", cookie=token)
        assert a[0] == b[0] == 404 and a[1] == b[1]
    assert snapshot(server) == sebelum and not server.provider.panggilan
