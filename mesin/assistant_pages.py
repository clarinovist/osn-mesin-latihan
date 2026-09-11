"""Halaman server-side Pendamping; output model selalu di-escape sebagai teks."""

from __future__ import annotations

import html

import assistant_policy
import assistant_store
import brand
import design_tokens as T
from assistant_style import GAYA_PENDAMPING


def _bingkai(judul: str, isi: str) -> bytes:
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(brand.judul(judul))}</title>{brand.tag_kepala()}
<style>{GAYA_PENDAMPING}</style></head><body class="pendamping-halaman">
<main class="pendamping-bungkus" aria-labelledby="judul-pendamping">
<header class="pendamping-kepala"><a href="/guru">← Kembali ke ruang belajar</a>
<a href="/pendamping">Chat baru</a></header>{isi}</main></body></html>""".encode()


def halaman_tidak_aktif() -> bytes:
    return _bingkai(
        "Pendamping belum aktif",
        '<section class="pendamping-panel"><h1 id="judul-pendamping">Pendamping belum aktif</h1>'
        '<p>Latihan Jagomat tetap dapat digunakan seperti biasa.</p></section>',
    )


def halaman_persetujuan(galat: str = "") -> bytes:
    pesan = (
        f'<p class="pendamping-galat" role="alert">{html.escape(galat)}</p>'
        if galat else ""
    )
    return _bingkai(
        "Persetujuan Pendamping",
        '<section class="pendamping-panel"><h1 id="judul-pendamping">Sebelum mulai</h1>'
        '<p>Pesan chat akan dikirim ke DeepSeek untuk membuat jawaban. Jangan '
        'menulis email, nomor telepon, sandi, token, atau data pribadi anak.</p>'
        '<p>Riwayat chat disimpan sampai 180 hari sejak aktivitas terakhir. '
        'Penghapusan aktif dilakukan segera; salinan cadangan dapat bertahan '
        'maksimal 30 hari.</p>'
        f'{pesan}<form method="post" action="/pendamping/persetujuan">'
        f'<input type="hidden" name="kebijakan" value="{assistant_policy.VERSI_KEBIJAKAN}">'
        '<label><input type="checkbox" name="setuju" value="1" required> '
        'Saya memahami dan setuju mengirim chat ke DeepSeek.</label>'
        '<p><button class="pendamping-tombol" type="submit">Setuju dan lanjutkan</button></p>'
        '</form></section>',
    )


def _riwayat(chats) -> str:
    if not chats:
        return ""
    tautan = "".join(
        f'<a href="/pendamping/chat/{html.escape(chat.id)}">Chat {indeks + 1}</a>'
        for indeks, chat in enumerate(chats)
    )
    return (
        '<details class="pendamping-riwayat"><summary>Riwayat chat</summary>'
        f'<nav aria-label="Riwayat chat">{tautan}</nav></details>'
    )


def halaman_awal(chats, galat: str = "", request_id: str = "") -> bytes:
    pesan = (
        f'<p class="pendamping-galat" role="alert">{html.escape(galat)}</p>'
        if galat else ""
    )
    return _bingkai(
        "Pendamping",
        f'{_riwayat(chats)}<section class="pendamping-panel pendamping-kosong">'
        '<h1 id="judul-pendamping">Pendamping</h1>'
        f'{pesan}<form method="post" action="/pendamping/chat-baru">'
        '<input type="hidden" name="mode" value="aktif">'
        f'<input type="hidden" name="request_id" value="{html.escape(request_id)}">'
        '<label class="pendamping-label" for="awal">Apa yang bisa dibantu hari ini?</label>'
        '<textarea class="pendamping-input" id="awal" name="pesan_awal" '
        'placeholder="Tulis ceritamu di sini"></textarea>'
        '<p><button class="pendamping-tombol" type="submit">Mulai chat</button></p>'
        '</form><form method="post" action="/pendamping/chat-baru">'
        '<input type="hidden" name="mode" value="tanpa_memori">'
        '<input type="hidden" name="pesan_awal" value="">'
        '<input type="hidden" name="request_id" value="">'
        '<button class="pendamping-tombol" type="submit">Chat tanpa memori</button>'
        '</form><p class="pendamping-catatan">Chat tanpa memori tetap tersimpan '
        'sebagai riwayat, tetapi tidak membaca atau menambah memori lintas chat.</p>'
        '</section>',
    )


def halaman_chat(chat, pesan, chats, *, galat: str = "", request_id: str) -> bytes:
    daftar = "".join(
        '<article class="pendamping-pesan '
        f'{html.escape(item.peran)}"><b>'
        f'{"Kamu" if item.peran == "pengguna" else "Pendamping"}</b>'
        f'{html.escape(item.teks)}</article>'
        for item in pesan
    )
    status = "Chat tanpa memori" if chat.mode_memori == "tanpa_memori" else "Memori aktif bila sudah dikonfirmasi"
    pesan_galat = (
        f'<p class="pendamping-galat" role="alert">{html.escape(galat)}</p>'
        if galat else ""
    )
    return _bingkai(
        "Chat Pendamping",
        f'{_riwayat(chats)}<section><h1 id="judul-pendamping">Pendamping</h1>'
        f'<p class="pendamping-catatan">{html.escape(status)}</p>{pesan_galat}'
        f'<div aria-live="polite">{daftar}</div>'
        f'<form class="pendamping-form" method="post" action="/pendamping/chat/{html.escape(chat.id)}/pesan">'
        f'<input type="hidden" name="request_id" value="{html.escape(request_id)}">'
        '<label class="pendamping-label" for="pesan">Pesan untuk Pendamping</label>'
        '<textarea class="pendamping-input" id="pesan" name="pesan" required></textarea>'
        '<button class="pendamping-tombol" type="submit">Kirim</button></form></section>',
    )
