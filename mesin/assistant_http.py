"""Parser dan routing HTTP ketat untuk Pendamping."""

from __future__ import annotations

import html
from dataclasses import replace
import os
import re
import secrets
import threading
import time
import urllib.parse

import assistant_actions
import assistant_navigation
import assistant_view
import assistant_context
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
_POLA_KONTEKS = re.compile(
    r"/pendamping/konteks/(anak|sesi|soal)/([0-9]+(?::[0-9]+)?)\Z"
)
_POLA_USULAN = re.compile(r"/pendamping/usulan/(usulan_[0-9a-f]{32})\Z")
_POLA_KONFIRMASI_USULAN = re.compile(
    r"/pendamping/usulan/(usulan_[0-9a-f]{32})/konfirmasi\Z"
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
    penangan.send_header("Referrer-Policy", "no-referrer")
    penangan.send_header("X-Robots-Tag", "noindex, nofollow")
    penangan.send_header("Content-Length", "0")
    penangan.end_headers()


def _principal(penangan):
    token = penangan._ambil_token()
    return sessions.ambil_principal_pendamping(token)


def _tolak_login(penangan, tujuan: str = '') -> None:
    _kirim_privat(
        penangan,
        assistant_pages._bingkai(
            "Perlu masuk",
            '<section class="pendamping-panel"><h1 id="judul-pendamping">Perlu masuk lagi</h1>'
            '<p>Pendamping hanya tersedia untuk akun orang tua dengan sesi terbaru.</p>'
            f'<p><a href="{html.escape(assistant_navigation.tautan_masuk(tujuan), quote=True)}">Masuk</a></p></section>',
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


def _usulan_berubah(penangan, galat, *, chat_id='', usulan_id='') -> None:
    """Gunakan penolakan aman yang sama untuk tinjauan dan konfirmasi."""
    _kirim_privat(
        penangan,
        assistant_pages._bingkai(
            "Usulan berubah",
            '<section class="pendamping-panel"><h1 id="judul-pendamping">Usulan perlu ditinjau ulang</h1>'
            f'<p role="alert">{html.escape(str(galat))}</p>'
            + (f'<p><a href="/pendamping/usulan/{html.escape(usulan_id)}">Tinjau kembali</a></p>'
               if usulan_id and 'kedaluwarsa' in str(galat).lower() else '')
            + (f'<p><a href="/pendamping/chat/{html.escape(chat_id)}">Kembali ke percakapan</a></p>' if chat_id else '')
            + '</section>',
        ),
        409,
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


def _konteks_chat(chat, pemilik: str):
    if chat.context_kind is None:
        return None
    import database

    with database.buka() as kon:
        konteks = assistant_context.ambil(
            kon, chat.context_kind, chat.context_id, pemilik=pemilik
        )
    if (
        konteks is None
        or konteks.versi != chat.context_resource_version
    ):
        return None
    return konteks


def _versi_konteks_chat(chat, pemilik: str):
    import database

    with database.buka() as kon:
        return assistant_context.versi_resource(
            kon, chat.context_kind, chat.context_id, pemilik=pemilik
        )


def _query(penangan):
    """Query terbatas; parameter URL bukan sumber otorisasi."""
    try:
        data = urllib.parse.parse_qs(
            urllib.parse.urlsplit(penangan.path).query,
            keep_blank_values=True, max_num_fields=4, errors='strict',
        )
    except (ValueError, UnicodeError):
        raise GalatForm('Parameter tidak sah.', 404) from None
    if any(len(nilai) != 1 for nilai in data.values()):
        raise GalatForm('Parameter ganda tidak sah.', 404)
    return {k: v[0] for k, v in data.items()}


def _sumber(chat, pemilik):
    if chat.context_kind is None:
        return None
    import database
    with database.buka() as kon_data:
        return assistant_view.sumber_tampilan(
            kon_data, chat.context_kind, chat.context_id, pemilik=pemilik
        )


def _kembali_sah(kon, principal, nilai):
    if not nilai:
        return ''
    if not re.fullmatch(r'chat_[0-9a-f]{32}', nilai):
        raise GalatForm('Tujuan tidak sah.', 404)
    chat = assistant_store.ambil_chat(kon, principal.id_akun, nilai)
    if chat is None or not assistant_view.hak_baca_chat(
        kon, principal.id_akun, chat, pemilik=principal.pengguna
    ):
        raise GalatForm('Tujuan tidak tersedia.', 404)
    return nilai


def _consent(kon, account_id):
    """Pilih izin provider terbaru; izin lama tidak hidup setelah pencabutan."""
    izin = kon.execute(
        "SELECT provider_id,policy_version,dicabut FROM persetujuan "
        "WHERE account_id=? AND kategori='chat_umum' ORDER BY versi DESC,rowid DESC LIMIT 1",
        (account_id,),
    ).fetchone()
    return bool(izin is not None and izin['dicabut'] is None
                and izin['provider_id']==assistant_policy.PROVIDER_ID
                and izin['policy_version']==assistant_policy.VERSI_KEBIJAKAN)


def _daftar(kon, account_id):
    return assistant_view.riwayat(kon, account_id)[0]


def _chat_html(kon, principal, chat, *, galat='', request_id='', operasi_url=''):
    """Proyeksi baca terjaga; stale tidak mengaktifkan composer atau tindakan."""
    sumber = _sumber(chat, principal.pengguna)
    if chat.context_kind is not None and sumber is None:
        raise LookupError('chat tidak ditemukan')
    if not assistant_view.hak_baca_chat(
        kon, principal.id_akun, chat, pemilik=principal.pengguna
    ):
        return assistant_pages.halaman_konteks_berubah(sumber=sumber), 409
    konteks = _konteks_chat(chat, principal.pengguna)
    hanya_baca = chat.context_kind is not None and konteks is None
    # Hasil yang mengubah ringkasan anak tetap dapat diakses dari chat, tetapi
    # jangan tampilkan kandidat tindakan baru pada histori stale.
    usulan = []
    for item in assistant_store.daftar_usulan_chat(kon, principal.id_akun, chat.id):
        try:
            sesi_id = assistant_actions.ambil_hasil_usulan(kon,principal.id_akun,principal.pengguna,item.id)
        except (LookupError,assistant_actions.GalatTindakan):
            sesi_id = None
        if sesi_id is not None:
            # Proyeksi immutable saja: GET tidak finalisasi pointer privat.
            item = replace(item,sesi_id=sesi_id,status='selesai')
        if hanya_baca and item.sesi_id is None:
            continue
        usulan.append(item)
    draft = ()
    if not hanya_baca and chat.mode_memori != 'tanpa_memori' and assistant_store.penggunaan_memori_aktif(kon, principal.id_akun):
        draft = tuple(m for m in assistant_store.daftar_memori(kon, principal.id_akun)
                      if not m.dikonfirmasi and m.sumber_chat_id == chat.id)
    return assistant_pages.halaman_chat(
        chat, assistant_store.daftar_pesan(kon, principal.id_akun, chat.id),
        _daftar(kon, principal.id_akun), galat=galat,
        request_id=request_id or 'req_' + secrets.token_hex(16),
        draft=draft, konteks=konteks, usulan=tuple(usulan),
        status_memori=assistant_view.status_memori(kon, principal.id_akun, chat),
        sumber=sumber, hanya_baca=hanya_baca, operasi_url=operasi_url,
    ), 200


def tangani_get(penangan, jalur: str) -> bool:
    if not (jalur == '/pendamping' or jalur.startswith('/pendamping/')):
        return False
    if not aktif():
        _tidak_ada(penangan)
        return True
    principal = _principal(penangan)
    if principal is None:
        _tolak_login(penangan, assistant_navigation.tujuan_lanjut(jalur))
        return True
    if not assistant_service.tersedia():
        _kirim_privat(penangan, assistant_pages.halaman_tidak_aktif(), 503)
        return True
    try:
        query = _query(penangan)
        cocok_konteks = _POLA_KONTEKS.fullmatch(jalur)
        if cocok_konteks:
            if query or not assistant_navigation.tujuan_lanjut(jalur):
                raise LookupError('sumber tidak tersedia')
            import database
            jenis, resource_id = cocok_konteks.groups()
            with database.buka() as kon_data:
                sumber = assistant_view.sumber_tampilan(kon_data,jenis,resource_id,pemilik=principal.pengguna)
            if sumber is None:
                raise LookupError('sumber tidak tersedia')
        with _siapkan_db() as kon:
            consent = _consent(kon, principal.id_akun)
            if cocok_konteks:
                if query or not assistant_navigation.tujuan_lanjut(jalur):
                    raise LookupError('sumber tidak tersedia')
                import database
                jenis, resource_id = cocok_konteks.groups()
                with database.buka() as kon_data:
                    sumber = assistant_view.sumber_tampilan(
                        kon_data, jenis, resource_id, pemilik=principal.pengguna
                    )
                    konteks = assistant_context.ambil(
                        kon_data, jenis, resource_id, pemilik=principal.pengguna
                    ) if sumber is not None else None
                if sumber is None or konteks is None:
                    raise LookupError('sumber tidak tersedia')
                if not consent:
                    _kirim_privat(penangan, assistant_pages.halaman_persetujuan(lanjut=jalur,sumber=sumber))
                else:
                    _kirim_privat(penangan, assistant_pages.halaman_pilih_konteks(konteks, sumber=sumber))
                return True
            if not consent:
                _kirim_privat(penangan, assistant_pages.halaman_persetujuan())
                return True
            if jalur in ('/pendamping','/pendamping/tanpa-memori'):
                if query:
                    raise LookupError('parameter tidak tersedia')
                _kirim_privat(penangan, assistant_pages.halaman_awal(
                    _daftar(kon, principal.id_akun), request_id='req_'+secrets.token_hex(16),
                    mode='tanpa_memori' if jalur.endswith('tanpa-memori') else 'aktif',
                ))
                return True
            if jalur == '/pendamping/riwayat':
                if set(query) - {'halaman'}:
                    raise LookupError('parameter tidak tersedia')
                nomor = query.get('halaman','1')
                if not re.fullmatch(r'[1-9][0-9]{0,2}', nomor):
                    raise LookupError('halaman tidak tersedia')
                chats, ada_lagi = assistant_view.riwayat(kon, principal.id_akun, halaman=int(nomor))
                _kirim_privat(penangan, assistant_pages.halaman_riwayat(chats, halaman=int(nomor), ada_lagi=ada_lagi))
                return True
            cocok_memori = _POLA_MEMORI.fullmatch(jalur)
            if jalur in ('/pendamping/memori','/pendamping/memori/hapus-semua') or cocok_memori:
                if set(query) - {'kembali'}:
                    raise LookupError('parameter tidak tersedia')
                kembali = _kembali_sah(kon, principal, query.get('kembali',''))
                daftar = assistant_store.daftar_memori(kon, principal.id_akun)
                versi = assistant_store.versi_memori(kon, principal.id_akun)
                if jalur == '/pendamping/memori':
                    isi = assistant_pages.halaman_memori(daftar,
                        aktif=assistant_store.penggunaan_memori_aktif(kon, principal.id_akun),
                        versi=versi, kembali=kembali)
                elif jalur.endswith('hapus-semua'):
                    isi = assistant_pages.halaman_hapus_memori(daftar, versi=versi, semua=True, kembali=kembali)
                else:
                    memori_id, aksi = cocok_memori.groups()
                    item = next((m for m in daftar if m.id == memori_id), None)
                    if item is None or aksi not in ('ubah','hapus'):
                        raise LookupError('memori tidak tersedia')
                    isi = (assistant_pages.halaman_edit_memori(item, kembali=kembali) if aksi == 'ubah' else
                           assistant_pages.halaman_hapus_memori((item,), versi=item.versi, kembali=kembali))
                _kirim_privat(penangan, isi)
                return True
            cocok_usulan = _POLA_USULAN.fullmatch(jalur)
            if cocok_usulan:
                if query:
                    raise LookupError('parameter tidak tersedia')
                usulan = assistant_store.ambil_usulan(kon, principal.id_akun, cocok_usulan[1])
                if usulan is None:
                    raise LookupError('usulan tidak tersedia')
                chat = assistant_store.ambil_chat(kon, principal.id_akun, usulan.chat_id)
                if chat is None:
                    raise LookupError('chat tidak tersedia')
                sumber = _sumber(chat, principal.pengguna)
                try:
                    sesi_id = assistant_actions.ambil_hasil_usulan(kon, principal.id_akun, principal.pengguna, usulan.id)
                    if sesi_id is not None:
                        _kirim_privat(penangan, assistant_pages.halaman_hasil_usulan(usulan, sesi_id=sesi_id, sumber=sumber))
                        return True
                    request_id = assistant_actions.tinjau_usulan(kon, principal.id_akun, principal.pengguna, usulan.id, sekarang=int(time.time()))
                except assistant_actions.GalatTindakan as galat:
                    _usulan_berubah(penangan, galat, chat_id=chat.id, usulan_id=usulan.id)
                    return True
                konteks = _konteks_chat(chat, principal.pengguna)
                if konteks is None:
                    _kirim_privat(penangan, assistant_pages.halaman_konteks_berubah(sumber=sumber),409)
                    return True
                pesan_sumber = assistant_store.pesan_dari_request(kon, principal.id_akun, usulan.sumber_request_id, peran='pengguna')
                if pesan_sumber is not None and pesan_sumber.chat_id != chat.id:
                    raise LookupError('sumber tidak tersedia')
                _kirim_privat(penangan, assistant_pages.halaman_tinjau_usulan(usulan, chat, konteks,
                    request_id=request_id, sumber=sumber, pesan_sumber=pesan_sumber))
                return True
            cocok_operasi = re.fullmatch(r'/pendamping/operasi/(req_[0-9A-Za-z_-]{8,80})',jalur)
            if cocok_operasi:
                if query:
                    raise LookupError('parameter tidak tersedia')
                operasi = kon.execute('SELECT chat_id,status FROM operasi WHERE request_id=? AND account_id=?',
                                      (cocok_operasi[1],principal.id_akun)).fetchone()
                chat = None if operasi is None else assistant_store.ambil_chat(kon,principal.id_akun,operasi['chat_id'])
                if chat is None or not assistant_view.hak_baca_chat(kon,principal.id_akun,chat,pemilik=principal.pengguna):
                    raise LookupError('operasi tidak tersedia')
                if operasi['status']=='selesai':
                    _redirect(penangan,'/pendamping/chat/'+chat.id)
                else:
                    _kirim_privat(penangan,assistant_pages.halaman_status_operasi(operasi['status'],chat_id=chat.id,request_id=cocok_operasi[1]))
                return True
            cocok = _POLA_CHAT.fullmatch(jalur)
            if not cocok or query:
                raise LookupError('chat tidak tersedia')
            chat = assistant_store.ambil_chat(kon,principal.id_akun,cocok[1])
            if chat is None:
                raise LookupError('chat tidak tersedia')
            isi,kode = _chat_html(kon,principal,chat)
            _kirim_privat(penangan,isi,kode)
    except (LookupError, GalatForm):
        _tidak_ada(penangan)
    except ValueError:
        _tidak_ada(penangan)
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
            lanjut = assistant_navigation.tujuan_lanjut(data.get('lanjut', ''))
            if data.get('lanjut') and not lanjut:
                _tidak_ada(penangan)
                return True
            sumber = None
            if lanjut and lanjut != '/pendamping':
                import database
                cocok = _POLA_KONTEKS.fullmatch(lanjut)
                with database.buka() as kon_data:
                    sumber = assistant_view.sumber_tampilan(kon_data, cocok[1], cocok[2], pemilik=principal.pengguna)
                if sumber is None:
                    _tidak_ada(penangan)
                    return True
            if set(data) - {"setuju", "kebijakan", "lanjut"} or data.get("setuju") != "1" or data.get("kebijakan") != assistant_policy.VERSI_KEBIJAKAN:
                _kirim_privat(penangan, assistant_pages.halaman_persetujuan("Persetujuan tidak lengkap.", lanjut=lanjut,sumber=sumber), 400)
                return True
            assistant_store.beri_persetujuan(
                kon, principal.id_akun,
                policy_version=assistant_policy.VERSI_KEBIJAKAN,
                provider_id=assistant_policy.PROVIDER_ID,
                kategori="chat_umum", sekarang=kini,
            )
            kon.commit()
            _redirect(penangan, lanjut or "/pendamping")
            return True

        if not _consent(kon, principal.id_akun):
            _kirim_privat(penangan, assistant_pages.halaman_persetujuan(), 409)
            return True

        if jalur == "/pendamping/konteks/pilih":
            wajib = {
                "jenis", "resource_id", "resource_version", "kategori", "mode"
            }
            if set(data) != wajib or data.get('mode') not in ('aktif','tanpa_memori'):
                _tidak_ada(penangan)
                return True
            import database

            with database.buka() as kon_data:
                konteks = assistant_context.ambil(
                    kon_data,
                    data["jenis"],
                    data["resource_id"],
                    pemilik=principal.pengguna,
                )
            if (
                konteks is None
                or konteks.versi != data["resource_version"]
                or konteks.kategori != data["kategori"]
            ):
                _tidak_ada(penangan)
                return True
            persetujuan = assistant_store.beri_persetujuan_konteks(
                kon,
                principal.id_akun,
                jenis=konteks.jenis,
                resource_id=konteks.resource_id,
                resource_version=konteks.versi,
                kategori=konteks.kategori,
                sekarang=kini,
            )
            chat = assistant_store.buat_chat(
                kon,
                principal.id_akun,
                data["mode"],
                sekarang=kini,
                context_kind=konteks.jenis,
                context_id=konteks.resource_id,
                context_version=persetujuan.versi,
                context_resource_version=konteks.versi,
                context_category=konteks.kategori,
            )
            _redirect(penangan, f"/pendamping/chat/{chat.id}")
            return True

        if jalur in (
            "/pendamping/memori/aktifkan",
            "/pendamping/memori/nonaktifkan",
            "/pendamping/memori/hapus-semua",
        ):
            try:
                kembali = _kembali_sah(kon,principal,data.get('kembali',''))
            except GalatForm:
                _tidak_ada(penangan)
                return True
            if set(data) - {'versi','kembali','persetujuan_hapus'} or not data.get('versi','').isdigit():
                _kirim_privat(penangan, assistant_pages.halaman_memori(
                    assistant_store.daftar_memori(kon, principal.id_akun),
                    aktif=assistant_store.penggunaan_memori_aktif(kon, principal.id_akun),
                    versi=assistant_store.versi_memori(kon, principal.id_akun),
                    galat="Versi memori tidak sah.", kembali=kembali,
                ), 400)
                return True
            if jalur.endswith('hapus-semua') and data.get('persetujuan_hapus') != '1':
                memori = assistant_store.daftar_memori(kon, principal.id_akun)
                if not memori:
                    _tidak_ada(penangan)
                    return True
                _kirim_privat(penangan,assistant_pages.halaman_hapus_memori(
                    memori,
                    versi=assistant_store.versi_memori(kon,principal.id_akun),semua=True,kembali=kembali),400)
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
                    galat="Memori berubah. Muat ulang lalu coba lagi.", kembali=kembali,
                ), 409)
                return True
            kon.commit()
            _redirect(penangan, '/pendamping/memori'+('?kembali='+kembali if kembali else ''))
            return True

        cocok_memori = _POLA_MEMORI.fullmatch(jalur)
        if cocok_memori:
            memori_id, aksi = cocok_memori.groups()
            field = {"versi", "kembali", "persetujuan_hapus"} if aksi in ("konfirmasi", "hapus") else {"versi", "isi", "kembali"}
            if set(data) - field or "versi" not in data or not data["versi"].isdigit():
                _tidak_ada(penangan)
                return True
            try:
                kembali = _kembali_sah(kon,principal,data.get('kembali',''))
            except GalatForm:
                _tidak_ada(penangan)
                return True
            item = next((m for m in assistant_store.daftar_memori(kon,principal.id_akun) if m.id==memori_id),None)
            if item is None:
                _tidak_ada(penangan)
                return True
            if aksi=='hapus' and data.get('persetujuan_hapus')!='1':
                _kirim_privat(penangan,assistant_pages.halaman_hapus_memori((item,),versi=item.versi,kembali=kembali),400)
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
                if aksi == 'ubah':
                    _kirim_privat(penangan,assistant_pages.halaman_edit_memori(
                        item,galat='Koreksi belum disimpan. Gunakan bentuk preferensi yang didukung atau muat ulang catatan.',kembali=kembali),404)
                else:
                    _tidak_ada(penangan)
                return True
            tujuan = (f'/pendamping/chat/{kembali}' if kembali and aksi == 'konfirmasi' else
                      '/pendamping/memori'+('?kembali='+kembali if kembali else ''))
            kon.commit()
            _redirect(penangan, tujuan)
            return True

        cocok_konfirmasi = _POLA_KONFIRMASI_USULAN.fullmatch(jalur)
        if cocok_konfirmasi:
            if (
                set(data) != {"versi", "hash", "request_id"}
                or not data["versi"].isdigit()
                or not re.fullmatch(r"[0-9a-f]{64}", data["hash"])
                or not re.fullmatch(r"aksi_[0-9a-f]{32}", data["request_id"])
            ):
                _tidak_ada(penangan)
                return True
            try:
                sesi_id = assistant_actions.konfirmasi_dan_buat_sesi(
                    kon,
                    principal.id_akun,
                    principal.pengguna,
                    cocok_konfirmasi[1],
                    versi=int(data["versi"]),
                    hash_diharapkan=data["hash"],
                    request_id=data["request_id"],
                    sekarang=kini,
                )
            except LookupError:
                _tidak_ada(penangan)
                return True
            except assistant_actions.GalatTindakan as galat:
                catatan = assistant_store.ambil_usulan(kon,principal.id_akun,cocok_konfirmasi[1])
                _usulan_berubah(penangan, galat, chat_id=catatan.chat_id if catatan else '',usulan_id=cocok_konfirmasi[1])
                return True
            _redirect(penangan, f"/sesi/{sesi_id}")
            return True

        if jalur == "/pendamping/chat-baru":
            if set(data) - {"mode", "pesan_awal", "request_id"}:
                _tidak_ada(penangan)
                return True
            mode = data.get("mode", "")
            pesan_awal = data.get("pesan_awal", "").strip()
            if 'pesan_awal' in data and not pesan_awal:
                _kirim_privat(penangan, assistant_pages.halaman_awal(
                    _daftar(kon, principal.id_akun), galat='Tulis pesan sebelum mengirim.',
                    request_id='req_'+secrets.token_hex(16), mode=mode if mode in ('aktif','tanpa_memori') else 'aktif'),400)
                return True
            request_id = data.get("request_id", "")
            if pesan_awal and not re.fullmatch(r"req_[0-9A-Za-z_-]{8,80}", request_id):
                _kirim_privat(
                    penangan,
                    assistant_pages.halaman_awal(
                        _daftar(kon, principal.id_akun),
                        galat="Penanda permintaan tidak sah.",
                        request_id="req_" + secrets.token_hex(16),
                    ),
                    400,
                )
                return True
            try:
                if pesan_awal:
                    chat = assistant_service.mulai_chat_dan_kirim(
                        kon, principal.id_akun, mode, pesan_awal,
                        request_id=request_id, sekarang=kini,
                    )
                else:
                    chat = assistant_store.buat_chat(
                        kon, principal.id_akun, mode, sekarang=kini
                    )
            except (assistant_service.GalatPendamping, ValueError) as galat:
                operasi = kon.execute('SELECT chat_id,status FROM operasi WHERE request_id=? AND account_id=?',
                                      (request_id,principal.id_akun)).fetchone()
                if operasi is not None and operasi['status']=='pending':
                    chat_lama = assistant_store.ambil_chat(kon,principal.id_akun,operasi['chat_id'])
                    if chat_lama is not None and assistant_view.hak_baca_chat(kon,principal.id_akun,chat_lama,pemilik=principal.pengguna):
                        _kirim_privat(penangan,assistant_pages.halaman_status_operasi('pending',chat_id=chat_lama.id,request_id=request_id),503)
                        return True
                _kirim_privat(
                    penangan,
                    assistant_pages.halaman_awal(
                        _daftar(kon, principal.id_akun),
                        galat=str(galat),
                        request_id="req_" + secrets.token_hex(16),
                        mode=mode if mode in ('aktif','tanpa_memori') else 'aktif',
                    ),
                    503 if isinstance(galat, assistant_service.GalatPendamping) else 400,
                )
                return True
            _redirect(penangan, f"/pendamping/chat/{chat.id}")
            return True

        cocok = _POLA_PESAN.fullmatch(jalur)
        if not cocok or set(data) != {'pesan','request_id'}:
            _tidak_ada(penangan)
            return True
        chat = assistant_store.ambil_chat(kon,principal.id_akun,cocok[1])
        if chat is None:
            _tidak_ada(penangan)
            return True
        sumber = _sumber(chat,principal.pengguna)
        if chat.context_kind is not None and sumber is None:
            _tidak_ada(penangan)
            return True
        request_id=data['request_id']
        if not re.fullmatch(r'req_[0-9A-Za-z_-]{8,80}',request_id):
            try:
                isi,kode=_chat_html(kon,principal,chat,galat='Penanda permintaan tidak sah.')
            except LookupError:
                _tidak_ada(penangan)
                return True
            _kirim_privat(penangan,isi,400 if kode==200 else kode)
            return True
        konteks=_konteks_chat(chat,principal.pengguna)
        if chat.context_kind is not None and (konteks is None or not assistant_view.hak_baca_chat(
            kon,principal.id_akun,chat,pemilik=principal.pengguna
        )):
            _kirim_privat(penangan,assistant_pages.halaman_konteks_berubah(sumber=sumber),409)
            return True
        try:
            assistant_service.kirim_pesan(
                kon,principal.id_akun,chat.id,data['pesan'],request_id=request_id,
                sekarang=kini,konteks=konteks,
                validasi_konteks=None if konteks is None else lambda: _versi_konteks_chat(chat,principal.pengguna),
            )
        except (assistant_service.GalatPendamping,ValueError) as galat:
            operasi=kon.execute('SELECT status FROM operasi WHERE request_id=? AND account_id=? AND chat_id=?',
                                (request_id,principal.id_akun,chat.id)).fetchone()
            if operasi and operasi['status']=='pending':
                _kirim_privat(penangan,assistant_pages.halaman_status_operasi('pending',chat_id=chat.id,request_id=request_id),503)
                return True
            try:
                isi,kode=_chat_html(kon,principal,chat,galat=str(galat),
                                    operasi_url='')
            except LookupError:
                _tidak_ada(penangan)
                return True
            if kode != 200:
                # Tidak render transkrip setelah izin berubah saat network.
                _usulan_berubah(penangan, galat)
            else:
                _kirim_privat(penangan,isi,503 if isinstance(galat,assistant_service.GalatPendamping) else 400)
            return True
        kon.commit()
        _redirect(penangan,f'/pendamping/chat/{chat.id}')
        return True
