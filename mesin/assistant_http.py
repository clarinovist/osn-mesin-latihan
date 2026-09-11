"""Parser dan routing HTTP ketat untuk Pendamping."""

from __future__ import annotations

import html
import os
import re
import secrets
import threading
import time
import urllib.parse

import assistant_pages
import assistant_policy
import assistant_schema
import assistant_service
import assistant_store
import sessions

_BATAS_FORM = 12_000
_BATAS_PER_MENIT = 30
_POLA_CHAT = re.compile(r"/pendamping/chat/(chat_[0-9a-f]{32})\Z")
_POLA_PESAN = re.compile(r"/pendamping/chat/(chat_[0-9a-f]{32})/pesan\Z")
_POLA_MEMORI = re.compile(
    r"/pendamping/memori/(memori_[0-9a-f]{32})/(konfirmasi|ubah|hapus)\Z"
)
_riwayat_laju = {}
_kunci_laju = threading.Lock()


class GalatForm(ValueError):
    def __init__(self, pesan: str, status: int = 400):
        super().__init__(pesan)
        self.status = status


def aktif() -> bool:
    return os.environ.get("PENDAMPING_AKTIF", "0") == "1"


def _kirim_privat(penangan, isi: bytes, kode: int = 200) -> None:
    penangan.send_response(kode)
    penangan.send_header("Content-Type", "text/html; charset=utf-8")
    penangan.send_header("Content-Length", str(len(isi)))
    penangan.send_header("Cache-Control", "no-store")
    penangan.send_header("Referrer-Policy", "no-referrer")
    penangan.send_header("X-Robots-Tag", "noindex, nofollow")
    penangan.send_header("X-Frame-Options", "DENY")
    penangan.send_header(
        "Content-Security-Policy",
        "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; "
        "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    )
    penangan.end_headers()
    penangan.wfile.write(isi)


def _redirect(penangan, tujuan: str) -> None:
    penangan.send_response(303)
    penangan.send_header("Location", tujuan)
    penangan.send_header("Cache-Control", "no-store")
    penangan.send_header("Content-Length", "0")
    penangan.end_headers()


def _principal(penangan):
    token = penangan._ambil_token()
    return sessions.ambil_principal_pendamping(token)


def _tolak_login(penangan) -> None:
    _kirim_privat(
        penangan,
        assistant_pages._bingkai(
            "Perlu masuk",
            '<section class="pendamping-panel"><h1 id="judul-pendamping">Perlu masuk lagi</h1>'
            '<p>Pendamping hanya tersedia untuk akun orang tua dengan sesi terbaru.</p>'
            '<p><a href="/masuk">Masuk</a></p></section>',
        ),
        401,
    )


def _tidak_ada(penangan) -> None:
    _kirim_privat(
        penangan,
        assistant_pages._bingkai(
            "404", '<section class="pendamping-panel"><h1 id="judul-pendamping">Halaman tidak ada</h1></section>'
        ),
        404,
    )


def _baca_form(penangan) -> dict[str, str]:
    asal = penangan.headers.get("Origin")
    situs = penangan.headers.get("Sec-Fetch-Site")
    if asal == "null":
        silang = situs != "same-origin"
    else:
        silang = bool(asal) and urllib.parse.urlsplit(asal).netloc != penangan.headers.get("Host")
    if (not asal and situs != "same-origin") or silang or situs == "cross-site":
        raise GalatForm("Permintaan harus berasal dari situs ini.", 403)
    panjang = penangan.headers.get("Content-Length", "0")
    if not re.fullmatch(r"[0-9]+", panjang) or penangan.headers.get("Transfer-Encoding"):
        raise GalatForm("Panjang isian tidak dikenal.")
    if int(panjang) > _BATAS_FORM:
        raise GalatForm("Isian terlalu besar.", 413)
    if penangan.headers.get_content_type() != "application/x-www-form-urlencoded":
        raise GalatForm("Format isian tidak dikenal.")
    try:
        mentah = penangan.rfile.read(int(panjang)).decode("utf-8")
        data = urllib.parse.parse_qs(
            mentah, keep_blank_values=True, errors="strict", max_num_fields=8
        )
    except (UnicodeError, ValueError) as galat:
        raise GalatForm("Isian tidak dapat dibaca.") from galat
    if any(len(nilai) != 1 for nilai in data.values()):
        raise GalatForm("Isian ganda tidak diizinkan.")
    return {nama: nilai[0] for nama, nilai in data.items()}


def _batasi_laju(penangan, account_id: str) -> None:
    kini = time.monotonic()
    ip = penangan.client_address[0] if penangan.client_address else "unknown"
    kunci = (account_id, ip)
    with _kunci_laju:
        aktif = tuple(waktu for waktu in _riwayat_laju.get(kunci, ()) if kini - waktu < 60)
        if len(aktif) >= _BATAS_PER_MENIT:
            raise GalatForm("Terlalu banyak permintaan. Coba lagi sebentar.", 429)
        _riwayat_laju[kunci] = (*aktif, kini)


def _siapkan_db():
    assistant_schema.siapkan()
    return assistant_schema.buka()


def tangani_get(penangan, jalur: str) -> bool:
    if not (jalur == "/pendamping" or jalur.startswith("/pendamping/")):
        return False
    if not aktif():
        _tidak_ada(penangan)
        return True
    principal = _principal(penangan)
    if principal is None:
        _tolak_login(penangan)
        return True
    if not assistant_service.tersedia():
        _kirim_privat(penangan, assistant_pages.halaman_tidak_aktif(), 503)
        return True
    with _siapkan_db() as kon:
        consent = assistant_store.persetujuan_aktif(
            kon, principal.id_akun,
            kategori="chat_umum", provider_id=assistant_policy.PROVIDER_ID,
        )
        if not consent:
            _kirim_privat(penangan, assistant_pages.halaman_persetujuan())
            return True
        chats = assistant_store.daftar_chat(kon, principal.id_akun)
        if jalur == "/pendamping/memori":
            memori = assistant_store.daftar_memori(kon, principal.id_akun)
            _kirim_privat(
                penangan,
                assistant_pages.halaman_memori(
                    memori,
                    aktif=assistant_store.penggunaan_memori_aktif(
                        kon, principal.id_akun
                    ),
                    versi=assistant_store.versi_memori(kon, principal.id_akun),
                ),
            )
            return True
        if jalur == "/pendamping":
            _kirim_privat(
                penangan,
                assistant_pages.halaman_awal(
                    chats, request_id="req_" + secrets.token_hex(16)
                ),
            )
            return True
        cocok = _POLA_CHAT.fullmatch(jalur)
        if not cocok:
            _tidak_ada(penangan)
            return True
        chat = assistant_store.ambil_chat(kon, principal.id_akun, cocok[1])
        if chat is None:
            _tidak_ada(penangan)
            return True
        pesan = assistant_store.daftar_pesan(kon, principal.id_akun, chat.id)
        draft = tuple(
            item for item in assistant_store.daftar_memori(kon, principal.id_akun)
            if not item.dikonfirmasi and item.sumber_chat_id == chat.id
        )
        _kirim_privat(
            penangan,
            assistant_pages.halaman_chat(
                chat, pesan, chats, request_id="req_" + secrets.token_hex(16),
                draft=draft,
            ),
        )
        return True


def tangani_post(penangan, jalur: str) -> bool:
    if not (jalur == "/pendamping" or jalur.startswith("/pendamping/")):
        return False
    if not aktif():
        _tidak_ada(penangan)
        return True
    principal = _principal(penangan)
    if principal is None:
        _tolak_login(penangan)
        return True
    if not assistant_service.tersedia():
        _kirim_privat(penangan, assistant_pages.halaman_tidak_aktif(), 503)
        return True
    try:
        _batasi_laju(penangan, principal.id_akun)
        data = _baca_form(penangan)
    except GalatForm as galat:
        _kirim_privat(
            penangan,
            assistant_pages._bingkai(
                "Permintaan ditolak",
                f'<section class="pendamping-panel"><h1 id="judul-pendamping">Permintaan ditolak</h1><p>{html.escape(str(galat))}</p></section>',
            ),
            galat.status,
        )
        return True

    kini = int(time.time())
    with _siapkan_db() as kon:
        if jalur == "/pendamping/persetujuan":
            if set(data) != {"setuju", "kebijakan"} or data.get("setuju") != "1" or data.get("kebijakan") != assistant_policy.VERSI_KEBIJAKAN:
                _kirim_privat(penangan, assistant_pages.halaman_persetujuan("Persetujuan tidak lengkap."), 400)
                return True
            assistant_store.beri_persetujuan(
                kon, principal.id_akun,
                policy_version=assistant_policy.VERSI_KEBIJAKAN,
                provider_id=assistant_policy.PROVIDER_ID,
                kategori="chat_umum", sekarang=kini,
            )
            _redirect(penangan, "/pendamping")
            return True

        if not assistant_store.persetujuan_aktif(
            kon, principal.id_akun,
            kategori="chat_umum", provider_id=assistant_policy.PROVIDER_ID,
        ):
            _kirim_privat(penangan, assistant_pages.halaman_persetujuan(), 409)
            return True

        if jalur in (
            "/pendamping/memori/aktifkan",
            "/pendamping/memori/nonaktifkan",
            "/pendamping/memori/hapus-semua",
        ):
            if set(data) != {"versi"} or not data["versi"].isdigit():
                _kirim_privat(penangan, assistant_pages.halaman_memori(
                    assistant_store.daftar_memori(kon, principal.id_akun),
                    aktif=assistant_store.penggunaan_memori_aktif(kon, principal.id_akun),
                    versi=assistant_store.versi_memori(kon, principal.id_akun),
                    galat="Versi memori tidak sah.",
                ), 400)
                return True
            versi = int(data["versi"])
            try:
                if jalur.endswith("hapus-semua"):
                    assistant_store.hapus_semua_memori(
                        kon, principal.id_akun, versi_diharapkan=versi,
                        sekarang=kini,
                    )
                else:
                    assistant_store.atur_penggunaan_memori(
                        kon,
                        principal.id_akun,
                        jalur == "/pendamping/memori/aktifkan",
                        versi_diharapkan=versi,
                        sekarang=kini,
                    )
            except ValueError:
                _kirim_privat(penangan, assistant_pages.halaman_memori(
                    assistant_store.daftar_memori(kon, principal.id_akun),
                    aktif=assistant_store.penggunaan_memori_aktif(kon, principal.id_akun),
                    versi=assistant_store.versi_memori(kon, principal.id_akun),
                    galat="Memori berubah. Muat ulang lalu coba lagi.",
                ), 409)
                return True
            _redirect(penangan, "/pendamping/memori")
            return True

        cocok_memori = _POLA_MEMORI.fullmatch(jalur)
        if cocok_memori:
            memori_id, aksi = cocok_memori.groups()
            field = {"versi", "kembali"} if aksi in ("konfirmasi", "hapus") else {"versi", "isi", "kembali"}
            if set(data) - field or "versi" not in data or not data["versi"].isdigit():
                _tidak_ada(penangan)
                return True
            versi = int(data["versi"])
            if aksi == "konfirmasi":
                berhasil = assistant_store.konfirmasi_memori(
                    kon, principal.id_akun, memori_id,
                    versi_diharapkan=versi, sekarang=kini,
                )
            elif aksi == "ubah":
                berhasil = assistant_store.ubah_memori(
                    kon, principal.id_akun, memori_id, data.get("isi", ""),
                    versi_diharapkan=versi, sekarang=kini,
                )
            else:
                berhasil = assistant_store.hapus_memori(
                    kon, principal.id_akun, memori_id,
                    versi_diharapkan=versi, sekarang=kini,
                )
            if not berhasil:
                _tidak_ada(penangan)
                return True
            kembali = data.get("kembali", "")
            tujuan = (
                f"/pendamping/chat/{kembali}"
                if re.fullmatch(r"chat_[0-9a-f]{32}", kembali)
                else "/pendamping/memori"
            )
            _redirect(penangan, tujuan)
            return True

        if jalur == "/pendamping/chat-baru":
            if set(data) - {"mode", "pesan_awal", "request_id"}:
                _tidak_ada(penangan)
                return True
            mode = data.get("mode", "")
            pesan_awal = data.get("pesan_awal", "").strip()
            request_id = data.get("request_id", "")
            if pesan_awal and not re.fullmatch(r"req_[0-9A-Za-z_-]{8,80}", request_id):
                _kirim_privat(
                    penangan,
                    assistant_pages.halaman_awal(
                        assistant_store.daftar_chat(kon, principal.id_akun),
                        galat="Penanda permintaan tidak sah.",
                        request_id="req_" + secrets.token_hex(16),
                    ),
                    400,
                )
                return True
            try:
                if pesan_awal:
                    assistant_policy.pastikan_teks_aman(pesan_awal)
                chat = assistant_store.buat_chat(
                    kon, principal.id_akun, mode, sekarang=kini
                )
                if pesan_awal:
                    assistant_service.kirim_pesan(
                        kon, principal.id_akun, chat.id, pesan_awal,
                        request_id=request_id, sekarang=kini,
                    )
            except (assistant_service.GalatPendamping, ValueError) as galat:
                _kirim_privat(
                    penangan,
                    assistant_pages.halaman_awal(
                        assistant_store.daftar_chat(kon, principal.id_akun),
                        galat=str(galat),
                        request_id="req_" + secrets.token_hex(16),
                    ),
                    503 if isinstance(galat, assistant_service.GalatPendamping) else 400,
                )
                return True
            _redirect(penangan, f"/pendamping/chat/{chat.id}")
            return True

        cocok = _POLA_PESAN.fullmatch(jalur)
        if not cocok or set(data) != {"pesan", "request_id"}:
            _tidak_ada(penangan)
            return True
        chat = assistant_store.ambil_chat(kon, principal.id_akun, cocok[1])
        if chat is None:
            _tidak_ada(penangan)
            return True
        request_id = data["request_id"]
        if not re.fullmatch(r"req_[0-9A-Za-z_-]{8,80}", request_id):
            _kirim_privat(
                penangan,
                assistant_pages.halaman_chat(
                    chat,
                    assistant_store.daftar_pesan(kon, principal.id_akun, chat.id),
                    assistant_store.daftar_chat(kon, principal.id_akun),
                    galat="Penanda permintaan tidak sah.",
                    request_id="req_" + secrets.token_hex(16),
                ),
                400,
            )
            return True
        try:
            assistant_service.kirim_pesan(
                kon, principal.id_akun, chat.id, data["pesan"],
                request_id=request_id, sekarang=kini,
            )
        except (assistant_service.GalatPendamping, ValueError) as galat:
            chats = assistant_store.daftar_chat(kon, principal.id_akun)
            pesan = assistant_store.daftar_pesan(kon, principal.id_akun, chat.id)
            draft = tuple(
                item for item in assistant_store.daftar_memori(
                    kon, principal.id_akun
                ) if not item.dikonfirmasi and item.sumber_chat_id == chat.id
            )
            _kirim_privat(
                penangan,
                assistant_pages.halaman_chat(
                    chat, pesan, chats, galat=str(galat),
                    request_id="req_" + secrets.token_hex(16), draft=draft,
                ),
                503 if isinstance(galat, assistant_service.GalatPendamping) else 400,
            )
            return True
        _redirect(penangan, f"/pendamping/chat/{chat.id}")
        return True
