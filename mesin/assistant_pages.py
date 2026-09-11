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
<nav aria-label="Navigasi Pendamping"><a href="/pendamping">Chat baru</a> ·
<a href="/pendamping/memori">Memori</a></nav></header>{isi}</main></body></html>""".encode()


def halaman_tidak_aktif() -> bytes:
    return _bingkai(
        "Pendamping belum aktif",
        '<section class="pendamping-panel"><h1 id="judul-pendamping">Pendamping belum aktif</h1>'
        '<p>Latihan Jagomat tetap dapat digunakan seperti biasa.</p></section>',
    )


def halaman_konteks_berubah() -> bytes:
    return _bingkai(
        "Konteks berubah",
        '<section class="pendamping-panel"><h1 id="judul-pendamping">Konteks belajar berubah</h1>'
        '<p>Data yang dipilih sudah berubah atau tidak lagi tersedia. Buka sumber '
        'belajar lagi, tinjau konteks terbaru, lalu mulai chat baru.</p></section>',
    )


def halaman_pilih_konteks(konteks) -> bytes:
    label = {
        "anak": "Ringkasan netral rencana satu anak",
        "sesi": "Ringkasan netral satu sesi",
        "soal": f'Soal resmi nomor {konteks.muatan.get("nomor", "")}',
    }[konteks.jenis]
    return _bingkai(
        "Pilih konteks",
        '<section class="pendamping-panel"><h1 id="judul-pendamping">Pilih konteks</h1>'
        f'<p><b>{html.escape(label)}</b></p>'
        '<p>Pendamping hanya menerima data minimum dari sumber ini. Berpindah '
        'anak atau melepas konteks akan membuka chat baru.</p>'
        '<form method="post" action="/pendamping/konteks/pilih">'
        f'<input type="hidden" name="jenis" value="{html.escape(konteks.jenis)}">'
        f'<input type="hidden" name="resource_id" value="{html.escape(konteks.resource_id)}">'
        f'<input type="hidden" name="resource_version" value="{html.escape(konteks.versi)}">'
        f'<input type="hidden" name="kategori" value="{html.escape(konteks.kategori)}">'
        '<input type="hidden" name="mode" value="aktif">'
        '<button class="pendamping-tombol" type="submit">Gunakan di chat baru</button>'
        '</form></section>',
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


def _daftar_memori(memori) -> str:
    if not memori:
        return '<p class="pendamping-catatan">Belum ada preferensi tersimpan.</p>'
    baris = []
    for item in memori:
        status = "Tersimpan" if item.dikonfirmasi else "Menunggu konfirmasi"
        aksi = (
            f'<form method="post" action="/pendamping/memori/{html.escape(item.id)}/konfirmasi">'
            f'<input type="hidden" name="versi" value="{item.versi}">'
            '<button class="pendamping-tombol" type="submit">Konfirmasi</button></form>'
            if not item.dikonfirmasi else ""
        )
        baris.append(
            '<article class="pendamping-panel pendamping-memori">'
            f'<p><b>{html.escape(status)}</b> · Preferensi orang tua</p>'
            f'<p>{html.escape(item.isi)}</p>{aksi}'
            f'<form method="post" action="/pendamping/memori/{html.escape(item.id)}/ubah">'
            f'<input type="hidden" name="versi" value="{item.versi}">'
            f'<label class="pendamping-label" for="ubah-{html.escape(item.id)}">Koreksi isi</label>'
            f'<input class="pendamping-input pendamping-input-pendek" id="ubah-{html.escape(item.id)}" name="isi" value="{html.escape(item.isi)}" required>'
            '<button class="pendamping-tombol" type="submit">Simpan koreksi</button></form>'
            f'<form method="post" action="/pendamping/memori/{html.escape(item.id)}/hapus">'
            f'<input type="hidden" name="versi" value="{item.versi}">'
            '<button class="pendamping-tombol" type="submit">Hapus memori ini</button></form>'
            '</article>'
        )
    return "".join(baris)


def halaman_memori(memori, *, aktif: bool, versi: int, galat: str = "") -> bytes:
    pesan = (
        f'<p class="pendamping-galat" role="alert">{html.escape(galat)}</p>'
        if galat else ""
    )
    aksi = "nonaktifkan" if aktif else "aktifkan"
    label = "Nonaktifkan penggunaan" if aktif else "Aktifkan penggunaan"
    return _bingkai(
        "Memori Pendamping",
        '<section><h1 id="judul-pendamping">Memori Pendamping</h1>'
        '<p>Hanya preferensi cara Pendamping menjawab. Memori tidak menyimpan '
        'profil, diagnosis, kontak, atau ringkasan curhatan anak.</p>'
        f'{pesan}<p><b>Status penggunaan:</b> {"aktif" if aktif else "nonaktif"}</p>'
        '<p class="pendamping-catatan">Menonaktifkan penggunaan tidak menghapus '
        'catatan; kamu tetap dapat melihat, mengoreksi, atau menghapusnya.</p>'
        f'<form method="post" action="/pendamping/memori/{aksi}">'
        f'<input type="hidden" name="versi" value="{versi}">'
        f'<button class="pendamping-tombol" type="submit">{label}</button></form>'
        f'{_daftar_memori(memori)}'
        '<form method="post" action="/pendamping/memori/hapus-semua">'
        f'<input type="hidden" name="versi" value="{versi}">'
        '<button class="pendamping-tombol" type="submit">Hapus semua memori</button>'
        '</form></section>',
    )


def halaman_chat(
    chat, pesan, chats, *, galat: str = "", request_id: str, draft=(), konteks=None
) -> bytes:
    daftar = "".join(
        '<article class="pendamping-pesan '
        f'{html.escape(item.peran)}"><b>'
        f'{"Kamu" if item.peran == "pengguna" else "Pendamping"}</b>'
        f'{html.escape(item.teks)}</article>'
        for item in pesan
    )
    status = "Chat tanpa memori" if chat.mode_memori == "tanpa_memori" else "Memori aktif bila sudah dikonfirmasi"
    label_konteks = ""
    if konteks is not None:
        label = {
            "anak": "Ringkasan rencana anak terpilih",
            "sesi": "Sesi belajar terpilih",
            "soal": f'Soal resmi nomor {konteks.muatan.get("nomor", "")}',
        }[konteks.jenis]
        label_konteks = (
            '<p class="pendamping-panel pendamping-catatan">Konteks: '
            f'{html.escape(label)}. <a href="/pendamping">Lepas konteks dan buka chat baru</a></p>'
        )
    pesan_galat = (
        f'<p class="pendamping-galat" role="alert">{html.escape(galat)}</p>'
        if galat else ""
    )
    kartu_draft = "".join(
        '<aside class="pendamping-panel pendamping-memori">'
        '<p><b>Simpan preferensi ini?</b></p>'
        f'<p>{html.escape(item.isi)}</p>'
        f'<form method="post" action="/pendamping/memori/{html.escape(item.id)}/konfirmasi">'
        f'<input type="hidden" name="versi" value="{item.versi}">'
        f'<input type="hidden" name="kembali" value="{html.escape(chat.id)}">'
        '<button class="pendamping-tombol" type="submit">Konfirmasi memori</button>'
        '</form></aside>'
        for item in draft
    )
    return _bingkai(
        "Chat Pendamping",
        f'{_riwayat(chats)}<section><h1 id="judul-pendamping">Pendamping</h1>'
        f'<p class="pendamping-catatan">{html.escape(status)} · '
        '<a href="/pendamping/memori">Atur memori</a></p>'
        f'{label_konteks}{pesan_galat}<div aria-live="polite">{daftar}</div>{kartu_draft}'
        f'<form class="pendamping-form" method="post" action="/pendamping/chat/{html.escape(chat.id)}/pesan">'
        f'<input type="hidden" name="request_id" value="{html.escape(request_id)}">'
        '<label class="pendamping-label" for="pesan">Pesan untuk Pendamping</label>'
        '<textarea class="pendamping-input" id="pesan" name="pesan" required></textarea>'
        '<button class="pendamping-tombol" type="submit">Kirim</button></form></section>',
    )
