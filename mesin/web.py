"""Router HTTP: Penangan(BaseHTTPRequestHandler) + palang peran/kepemilikan.

Stdlib saja, tanpa framework. Alasan tanpa framework: satu-satunya pengguna
adalah guru di jaringan rumah/VPS sendiri, kuerinya sedikit, dan tiap
dependensi tambahan adalah satu hal lagi yang bisa gagal saat deploy.

Halaman-halamannya tinggal di modul sendiri (dipecah 31 Aug 2026):
    teacher_pages.py   dashboard, sesi, konfirmasi hapus, lembar
    reports.py         laporan per anak + diagnosa
    account_pages.py   akun guru & admin
Aturan lama tetap: modul ini tidak boleh mengimpor students di atas file —
impor terlambat di dalam handler (lihat _rute_murid_get).
"""

from __future__ import annotations

import html
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler

import attachments as lampiran_mod
import auth
import database
import sessions
import design_tokens as T
from account_pages import (
    PETA_SECTION_AKUN,
    halaman_admin,
    halaman_akun,
    proses_admin,
    proses_akun,
)
from generator import LEVEL_BAWAAN
from reports import diagnosa_murid, halaman_laporan
from teacher_pages import (
    _halaman,
    _soal_dari_baris,
    _topik_untuk_level,
    buat_sesi_seed_baru,
    halaman_konfirmasi_hapus,
    halaman_lembar,
    halaman_sesi,
    halaman_sesi_cetak,
    halaman_sesi_lampiran,
    halaman_sesi_stitch,
    halaman_utama,
    halaman_utama_stitch,
    simpan_sesi,
)
from templates import LEVEL
from topics import TOPIK_BAWAAN, daftar_topik

class Penangan(BaseHTTPRequestHandler):
    def _kirim(self, isi: bytes, kode: int = 200) -> None:
        self.send_response(kode)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        self.wfile.write(isi)

    def _ambil_token(self) -> str | None:
        import http.cookies

        raw = self.headers.get("Cookie", "") or ""
        try:
            c = http.cookies.SimpleCookie(raw)
            m = c.get("osn_sesi")
            return m.value if m else None
        except Exception:
            return None

    def _set_cookie(self, token: str | None) -> str:
        import http.cookies

        if token is None:
            return "osn_sesi=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
        c = http.cookies.SimpleCookie()
        c["osn_sesi"] = token
        c["osn_sesi"]["path"] = "/"
        c["osn_sesi"]["httponly"] = True
        c["osn_sesi"]["samesite"] = "Lax"
        if self._di_https():
            c["osn_sesi"]["secure"] = True
        c["osn_sesi"]["max-age"] = str(sessions.TTL_DETIK)
        return c.output(header="").strip()

    def _di_https(self) -> bool:
        """Benar bila permintaan ini memang lewat HTTPS.

        Diputus dari petunjuk yang benar-benar menandai HTTPS —
        X-Forwarded-Proto dari proxy (Caddy di VPS) atau env OSN_HTTPS=1 —
        bukan dari nama host. Dulu Secure dipasang untuk semua host
        non-localhost: di mode LAN (serve.py --jaringan, host 192.168.x.x
        lewat HTTP biasa) peramban anak diam-diam membuang kuki Secure itu,
        sehingga setiap muat-ulang tiba tanpa identitas dan halaman murid
        jadi polos sampai masuk ulang (bug lapangan 1 Sep 2026).
        """
        if os.environ.get("OSN_HTTPS") == "1":
            return True
        return (self.headers.get("X-Forwarded-Proto") or "").strip().lower() == "https"

    def _kredensial(self):
        return auth.dari_header(self.headers.get("Authorization"))

    def _sesi_atau_basic(self, peran_wajib: str | None = None):
        """Kembalikan (pengguna, peran) bila lolos via cookie ATAU Basic.

        Helper kecil untuk rute murid — dipakai di _rute_murid_get dan
        POST /murid/kerjakan/. Nilai peran_wajib bila perlu (mis. "murid").
        """
        tok = self._ambil_token()
        if tok:
            got = sessions.ambil(tok)
            if got and (peran_wajib is None or got[1] == peran_wajib):
                return got
        kred = self._kredensial()
        if not kred:
            return None
        # kred adalah (pengguna, sandi) dari header Basic
        peran = auth.peran_dari(*kred)
        if peran and (peran_wajib is None or peran == peran_wajib):
            return (kred[0], peran)
        return None

    def _identitas(self) -> tuple[str, str] | None:
        """(pengguna, peran) pengunjung ini, atau None bila anonim.

        Mode lokal (tanpa berkas sandi) = satu akun bawaan "guru": semua
        halaman terbuka seperti semula, dan data yang dibuat tercatat atas
        nama "guru" pula — konsisten dengan pembuatnya.
        """
        if not auth.wajib_sandi():
            return ("guru", "guru")
        tok = self._ambil_token()
        if tok:
            got = sessions.ambil(tok)
            if got:
                return got
        kred = self._kredensial()
        if not kred:
            return None
        peran = auth.peran_dari(*kred)
        if peran:
            return (kred[0], peran)
        return None

    def _peran_saya(self) -> str | None:
        ident = self._identitas()
        return ident[1] if ident else None

    def _tolak_admin(self) -> None:
        """Tolak admin yang mencoba MENULIS data murid (404, bukan 403).

        Kebijakan baca-semua-tulis-tidak: admin boleh membuka semua halaman
        baca, tapi tidak satu pun aksi tulis. Body 404-nya identik dengan
        tolakan kepemilikan supaya tidak jadi oracle yang berbeda."""
        self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)

    def _lolos_sandi(self) -> bool:
        """Palang pengelola (guru/admin). Dilewati kalau berkas sandi tidak ada."""
        if self._peran_saya() in ("guru", "admin"):
            return True

        pesan = _halaman(
            "Perlu masuk",
            '<h1>Perlu masuk</h1><p><a href="/masuk">Masuk</a> untuk melanjutkan.</p>',
        )
        self.send_response(401)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(pesan)))
        self.end_headers()
        self.wfile.write(pesan)
        return False

    def _bisa_lihat_sesi(self, kon, sesi_id: int) -> bool:
        """Kepemilikan sesi: guru hanya sesi milik keluarganya, admin semua.

        Tolakan rute memakai 404, bukan 403 — keberadaan id orang lain
        bukan informasi yang boleh bocor.
        """
        ident = self._identitas()
        if not ident:
            return False
        if ident[1] == "admin":
            return True
        return database.sesi_milik(kon, sesi_id, ident[0])

    def _bisa_lihat_siswa(self, kon, siswa_id: int) -> bool:
        ident = self._identitas()
        if not ident:
            return False
        if ident[1] == "admin":
            return True
        return database.siswa_milik(kon, siswa_id, ident[0])

    def _bisa_lihat_lampiran(self, kon, lampiran_id: int) -> bool:
        lamp = database.ambil_lampiran(kon, lampiran_id)
        if not lamp:
            return False
        return self._bisa_lihat_sesi(kon, int(lamp["sesi_id"]))

    def _kirim_berkas_lampiran(self, kon, lampiran_id: int) -> None:
        """Kirim isi berkas foto lampiran (hanya guru, hanya milik sesi)."""
        lamp = database.ambil_lampiran(kon, lampiran_id)
        if not lamp or not self._bisa_lihat_sesi(kon, int(lamp["sesi_id"])):
            return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
        berkas = (
            lampiran_mod.direktori_lampiran()
            / str(lamp["sesi_id"])
            / lamp["nama_berkas"]
        )
        try:
            isi = berkas.read_bytes()
        except OSError:
            return self._kirim(_halaman("404", "<h1>Berkas hilang</h1>"), 404)
        self.send_response(200)
        self.send_header("Content-Type", lamp["mime"])
        self.send_header("Content-Length", str(len(isi)))
        self.send_header("Cache-Control", "private, max-age=3600")
        self.end_headers()
        self.wfile.write(isi)

    def do_GET(self) -> None:  # noqa: N802
        jalur = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"
        if jalur == "/masuk":
            galat = ""
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("galat"):
                galat = q["galat"][0]
            # hilangkan sesi lain di URL supaya tidak membingungkan
            return self._kirim(self._halaman_masuk_stitch(galat=galat))
        if jalur == "/":
            # Launch publik: / adalah landing untuk yang belum masuk.
            # Guru dengan sesi valid tetap dapat dashboard. Admin dialihkan
            # ke dashboardnya sendiri di /admin — dashboard guru (dengan
            # form "Buat sesi") bukan tempat admin: baca-semua-tulis-tidak.
            # Murid & anonim -> landing (bukan 401) — dashboard guru bukan
            # rahasia sekuat data anak, tapi tetap tak boleh dilihat murid.
            ident = self._identitas()
            if ident and ident[1] == "admin":
                self.send_response(303)
                self.send_header("Location", "/admin")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if ident and ident[1] == "guru":
                try:
                    q = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query
                    )
                    pesan = (q.get("pesan") or [""])[0]
                    sorot_raw = (q.get("sorot") or [""])[0]
                    try:
                        sorot = int(sorot_raw) if sorot_raw else None
                    except ValueError:
                        sorot = None
                    with database.buka() as kon:
                        return self._kirim(
                            halaman_utama_stitch(
                                kon, pesan=pesan, pemilik=ident[0],
                                peran=ident[1], sorot=sorot,
                            )
                        )
                except Exception:
                    pass  # DB bermasalah -> landing saja, jangan 500 mentah
            from landing import halaman_landing

            return self._kirim(halaman_landing())
        if jalur == "/daftar":
            from landing import halaman_daftar

            return self._kirim(halaman_daftar())
        if jalur == "/kebijakan-privasi":
            # Publik: tujuan checkbox persetujuan di /daftar & form anak,
            # dan footer landing. Statis, tanpa membaca basis data.
            from landing import halaman_kebijakan

            return self._kirim(halaman_kebijakan())
        if jalur == "/lupa-sandi":
            # Publik, dari tautan di /masuk. Aplikasi sengaja tidak
            # menyimpan email, jadi ini halaman panduan ("mintalah sandi
            # baru ke X"), bukan reset mandiri — mengarang alur email
            # berarti mengarang kanal yang tidak ada.
            from landing import halaman_lupa_sandi

            return self._kirim(halaman_lupa_sandi())
        if jalur == "/murid" or jalur.startswith("/murid/"):
            try:
                with database.buka() as kon:
                    return self._rute_murid_get(kon, jalur, self.path)
            except (ValueError, IndexError):
                pass
            self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)
            return
        if jalur == "/admin":
            if self._peran_saya() != "admin":
                return self._kirim(
                    _halaman(
                        "Perlu masuk",
                        "<h1>Halaman pengelola</h1>"
                        "<p>Hanya akun pengelola yang boleh membuka halaman ini.</p>",
                    ),
                    401,
                )
            try:
                ident = self._identitas()
                with database.buka() as kon:
                    return self._kirim(
                        halaman_admin(kon, pengguna=ident[0] if ident else "")
                    )
            except (ValueError, IndexError):
                pass
            self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)
            return
        if not self._lolos_sandi():
            return
        try:
            with database.buka() as kon:
                if jalur.startswith("/lampiran/berkas/"):
                    return self._kirim_berkas_lampiran(
                        kon, int(jalur.rsplit("/", 1)[1])
                    )
                if jalur.startswith("/lampiran/"):
                    lampiran_id = int(jalur.split("/")[2])
                    if not self._bisa_lihat_lampiran(kon, lampiran_id):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    isi = lampiran_mod.halaman_konfirmasi(kon, lampiran_id)
                    if isi:
                        return self._kirim(isi)
                if jalur.startswith("/sesi/") and jalur.endswith("/hapus"):
                    # Halaman konfirmasi hapus = prasyarat tulis; admin
                    # hanya-baca tidak sampai sini.
                    if self._peran_saya() == "admin":
                        return self._tolak_admin()
                    sesi_id = int(jalur.split("/")[2])
                    if not self._bisa_lihat_sesi(kon, sesi_id):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    ident = self._identitas()
                    isi = halaman_konfirmasi_hapus(
                        kon, sesi_id,
                        pengguna=ident[0] if ident else "",
                        peran=ident[1] if ident else "guru",
                    )
                    if isi is None:
                        return self._kirim(
                            _halaman("404", "<h1>Sesi tidak ada</h1>"), 404
                        )
                    return self._kirim(isi)
                if jalur.startswith("/sesi/") and jalur.endswith("/cetak"):
                    try:
                        sesi_id = int(jalur.split("/")[2])
                    except (ValueError, IndexError):
                        return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
                    if not self._bisa_lihat_sesi(kon, sesi_id):
                        return self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)
                    ident = self._identitas()
                    isi = halaman_sesi_cetak(
                        kon, sesi_id,
                        peran=ident[1] if ident else "guru",
                        pengguna=ident[0] if ident else "",
                    )
                    if isi is None:
                        return self._kirim(_halaman("404", "<h1>Sesi tidak ada</h1>"), 404)
                    return self._kirim(isi)
                if jalur.startswith("/sesi/") and jalur.endswith("/lampiran"):
                    try:
                        sesi_id = int(jalur.split("/")[2])
                    except (ValueError, IndexError):
                        return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
                    if not self._bisa_lihat_sesi(kon, sesi_id):
                        return self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)
                    ident = self._identitas()
                    isi = halaman_sesi_lampiran(
                        kon, sesi_id,
                        peran=ident[1] if ident else "guru",
                        pengguna=ident[0] if ident else "",
                    )
                    if isi is None:
                        return self._kirim(_halaman("404", "<h1>Sesi tidak ada</h1>"), 404)
                    return self._kirim(isi)
                if jalur.startswith("/sesi/"):
                    sesi_id = int(jalur.split("/")[2])
                    if not self._bisa_lihat_sesi(kon, sesi_id):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    ident = self._identitas()
                    # Guru membuka sesi yang terisi penuh = momen review:
                    # catat sekali supaya daftar sesi murid bisa menandai
                    # "Selesai". Buka lembar kosong untuk dicetak tidak
                    # dihitung; admin tidak menulis (baca-semua-tulis-tidak).
                    #
                    # Commit sendiri sebelum respons: _kirim dijalankan di
                    # dalam with buka(), jadi commit konteks baru terjadi
                    # SETELAH respons pergi. Siapa pun yang membaca detik
                    # itu juga (murid membuka daftar sesinya, test) akan
                    # melihat keadaan pra-commit. Stamp peristiwa mandiri
                    # — tidak ada tulisan lain yang menunggunya — aman
                    # didahulukan commitnya.
                    if ident and ident[1] == "guru":
                        penuh = kon.execute(
                            """SELECT 1 FROM sesi s
                               WHERE s.id = ? AND s.direview IS NULL
                                 AND (SELECT COUNT(*) FROM sesi_soal ss
                                      WHERE ss.sesi_id = s.id) > 0
                                 AND NOT EXISTS (
                                     SELECT 1 FROM sesi_soal ss2
                                     WHERE ss2.sesi_id = s.id
                                       AND NOT EXISTS (
                                           SELECT 1 FROM jawaban j
                                           WHERE j.sesi_soal_id = ss2.id))""",
                            (sesi_id,),
                        ).fetchone()
                        if penuh:
                            kon.execute(
                                "UPDATE sesi SET direview = "
                                "datetime('now', '+7 hours') WHERE id = ?",
                                (sesi_id,),
                            )
                            kon.commit()
                    return self._kirim(
                        halaman_sesi_stitch(
                            kon, sesi_id,
                            peran=ident[1] if ident else "guru",
                            pengguna=ident[0] if ident else "",
                        )
                    )
                if jalur.startswith("/laporan/"):
                    siswa_id = int(jalur.split("/")[2])
                    if not self._bisa_lihat_siswa(kon, siswa_id):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    ident = self._identitas()
                    return self._kirim(
                        halaman_laporan(
                            kon, siswa_id,
                            pengguna=ident[0] if ident else "",
                            peran=ident[1] if ident else "guru",
                        )
                    )
                if jalur == "/akun":
                    ident = self._identitas()
                    q = urllib.parse.parse_qs(
                        urllib.parse.urlparse(self.path).query
                    )
                    return self._kirim(
                        halaman_akun(
                            kon,
                            pengguna=ident[0] if ident else None,
                            peran=ident[1] if ident else "guru",
                            section=(q.get("section") or ["akun"])[0],
                        )
                    )
                if jalur.startswith("/lembar/"):
                    bagian = jalur.split("/")
                    sesi_id = int(bagian[2])
                    if not self._bisa_lihat_sesi(kon, sesi_id):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    guru = len(bagian) > 3 and bagian[3] == "penilaian"
                    isi = halaman_lembar(kon, sesi_id, guru)
                    if isi:
                        return self._kirim(isi)
        except (ValueError, IndexError):
            pass
        self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)

    def _rute_murid_get(self, kon, jalur: str, jalur_penuh: str = "") -> None:
        """Rute /murid — hanya akun berperan murid.

        Guru sengaja TIDAK bisa membuka halaman murid: halamannya memuat
        form jawaban atas nama anak, dan guru mengerjakan lewat rutenya
        sendiri. GET tanpa identitas murid (kuki hilang, kedaluwarsa, atau
        ditimpa akun lain di perangkat bersama) -> 303 ke /masuk dengan
        pesan yang jelas — anak dibawa ke pintu yang benar, bukan halaman
        401 polos yang terlihat seperti situs rusak saat muat-ulang. POST
        kirim jawaban tetap 401 di do_POST supaya palang tulis tidak
        melemah.
        """
        import student_pages
        import students

        kredensial = self._sesi_atau_basic(peran_wajib="murid")
        if not kredensial:
            qs = urllib.parse.urlencode({
                "galat": "Sesi kamu sudah habis atau akun lain masuk di "
                         "perangkat ini. Masuk lagi dengan nama & sandimu, ya.",
            })
            self.send_response(303)
            self.send_header("Location", f"/masuk?{qs}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        siswa_id = students.siswa_dari_akun(kon, kredensial[0])
        if siswa_id is None:
            nama = html.escape(kredensial[0])
            return self._kirim(
                _halaman(
                    "Belum terhubung",
                    f"<h1>Halo, {nama}</h1>"
                    "<p>Akunmu belum dihubungkan ke daftar siswa. "
                    "Minta gurumu menyiapkannya.</p>",
                )
            )
        if jalur == "/murid":
            # ?selesai=<id> dari pengalihan setelah semua soal terkirim:
            # hanya memicu banner perayaan di daftar, tidak menyentuh data.
            sesi_selesai = None
            if jalur_penuh:
                q = urllib.parse.parse_qs(
                    urllib.parse.urlparse(jalur_penuh).query
                )
                try:
                    sesi_selesai = int(q.get("selesai", ["0"])[0]) or None
                except (ValueError, TypeError):
                    sesi_selesai = None
            return self._kirim(
                student_pages.halaman_daftar_sesi_baru(
                    kon, siswa_id, kredensial[0], sesi_selesai
                )
            )
        bagian = jalur.split("/")
        # /murid/kerjakan/<id>
        if len(bagian) >= 3 and bagian[2] == "kerjakan":
            # Jumlah tersimpan datang dari pengalihan setelah POST. Nilainya
            # dari URL, jadi tidak dipercaya: dibatasi ke bilangan bulat wajar
            # dan hanya dipakai untuk kalimat konfirmasi, tidak menyentuh data.
            tersimpan = 0
            if jalur_penuh:
                q = urllib.parse.parse_qs(
                    urllib.parse.urlparse(jalur_penuh).query
                )
                try:
                    tersimpan = max(0, min(99, int(q.get("tersimpan", ["0"])[0])))
                except (ValueError, TypeError):
                    tersimpan = 0
            sesi_id_kerja = int(bagian[3])
            # Waktu pengerjaan mulai dihitung dari saat lembar DIBUKA, bukan
            # dari simpan pertama: anak yang mengisi semuanya lalu sekali
            # simpan tidak boleh tercatat berdurasi 0 detik. Idempoten —
            # buka ulang tidak menggeser waktu yang sudah tercatat. Commit
            # sendiri sebelum respons: stamp mandiri, dan commit konteks
            # buka() baru terjadi setelah respons pergi (lihat /sesi/).
            if students.sesi_murid(kon, siswa_id, sesi_id_kerja):
                database.tandai_mulai(kon, sesi_id_kerja)
                kon.commit()
            isi = student_pages.halaman_kerja_baru(kon, siswa_id, sesi_id_kerja, tersimpan)
            if isi is None:
                return self._kirim(
                    _halaman("404", "<h1>Sesi tidak ada</h1>"), 404
                )
            return self._kirim(isi)
        self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)

    def _halaman_masuk(self, galat: str = "") -> bytes:
        import icons

        kabar = (
            f'<div class="pesan galat">{html.escape(galat)}</div>' if galat else ""
        )
        return _halaman(
            T.NAMA_PRODUK,
            f'<div class="layout-masuk">'
            f'<div class="masuk-kiri">'
            f'<img src="{icons.OWL}" alt="Burung hantu lulusan" width="200" height="200">'
            f"<h1>{T.NAMA_PRODUK}</h1>"
            f"<p>{T.TAGLINE}</p>"
            f"</div>"
            f'<div class="masuk-kanan">'
            f'<div class="kartu kartu-masuk">'
            f'<img src="{icons.GEMBOK}" alt="" class="ikon-gembok" width="44" height="44">'
            f"{kabar}"
            f'<form method="post" action="/masuk">'
            f'<label>Nama</label>'
            f'<input type="text" name="nama" autocomplete="username" required>'
            f'<label>Sandi</label>'
            f'<input type="password" name="sandi" autocomplete="current-password" required>'
            f'<button type="submit">Masuk</button>'
            f"</form>"
            f'<p class="sub" style="text-align:center;margin-top:.8rem">'
            f'<a href="/lupa-sandi">Lupa sandi?</a></p>'
            f"</div></div></div>",
        )

    def _halaman_masuk_stitch(self, galat: str = "") -> bytes:
        """Versi Stitch dari halaman masuk (S7).

        Single-column card: brand owl + nama, judul + tagline, form nama/sandi,
        tombol coral Masuk, link Lupa sandi. Markup mengikuti mockup
        masuk_mobile. Logika auth TIDAK berubah — ini hanya render.
        """
        from style_stitch import gaya_stitch

        kabar = (
            f'<div class="masuk-galat-st">{html.escape(galat)}</div>' if galat else ""
        )
        body = f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Masuk &middot; {html.escape(T.NAMA_PRODUK)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
<style>{gaya_stitch()}</style></head>
<body class="st">
<div class="masuk-badan-st">
  <div class="masuk-kartu-st">
    <div class="masuk-brand-st">
      <span class="ik-owl material-symbols-outlined fill">school</span>
      <span class="nama-brand">{T.NAMA_PRODUK}</span>
    </div>
    <h1 class="masuk-judul-st">Masuk ke Akun Kamu</h1>
    <p class="masuk-sub-st">{T.TAGLINE}</p>
    {kabar}
    <form class="masuk-form-st" method="post" action="/masuk">
      <div class="masuk-field-st">
        <label for="nama">Nama</label>
        <input type="text" id="nama" name="nama" autocomplete="username" required>
      </div>
      <div class="masuk-field-st">
        <label for="sandi">Sandi</label>
        <input type="password" id="sandi" name="sandi" autocomplete="current-password" required>
      </div>
      <button class="masuk-tombol-st" type="submit">
        <span class="material-symbols-outlined" style="font-size:1.1rem">login</span>
        Masuk
      </button>
    </form>
    <p class="masuk-link-st"><a href="/lupa-sandi">Lupa sandi?</a></p>
  </div>
</div>
</body></html>"""
        return body.encode()

    def _handle_daftar(self, data: dict) -> None:
        """Pendaftaran mandiri pengelola (guru les / orang tua).

        Publik tapi tidak ringan hati: nama ganda ditolak (ambigu = risiko
        keamanan, bukan gaya), sandi minimal 8, dan checkbox persetujuan
        wajib. Gagal = form kembali dengan pesan, BUKAN akun setengah jadi.
        """
        from landing import halaman_daftar

        nama = (data.get("nama") or "").strip()
        pw = data.get("sandi") or ""
        ip = self.client_address[0] if self.client_address else "unknown"
        if sessions.sedang_diblokir(nama, ip):
            return self._kirim(
                halaman_daftar("Terlalu banyak percobaan. Coba lagi 15 menit lagi."),
                galat=True,
            )
        galat = None
        if not nama:
            galat = "Nama wajib diisi."
        elif len(pw) < 8:
            galat = "Kata sandi minimal 8 karakter."
        elif not data.get("setuju"):
            galat = "Centang persetujuan Kebijakan Privasi dulu, ya."
        else:
            try:
                auth.tambah_akun(nama, pw, "guru")
            except ValueError:
                galat = f"Nama {nama} sudah dipakai. Pakai nama lain, atau masuk bila memang akunmu."
        if galat:
            return self._kirim(halaman_daftar(galat, galat=True, nama=nama))

        token = sessions.buat(nama, "guru")
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", self._set_cookie(token))
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _handle_masuk(self, data: dict) -> None:
        nama = (data.get("nama") or "").strip()
        pw = data.get("sandi") or ""
        ip = self.client_address[0] if self.client_address else "unknown"
        if not nama or not pw:
            return self._kirim(self._halaman_masuk_stitch("Nama dan sandi wajib diisi."))
        if sessions.sedang_diblokir(nama, ip):
            return self._kirim(self._halaman_masuk_stitch("Terlalu banyak percobaan. Coba lagi 15 menit lagi."), 429)
        peran = auth.peran_dari(nama, pw)
        if not peran:
            sessions.catat_gagal(nama, ip)
            return self._kirim(self._halaman_masuk_stitch("Nama atau sandi belum cocok. Coba lagi, atau minta gurumu."))
        sessions.catat_berhasil(nama, ip)
        token = sessions.buat(nama, peran)
        tujuan = "/murid" if peran == "murid" else (
            "/admin" if peran == "admin" else "/"
        )
        self.send_response(303)
        self.send_header("Location", tujuan)
        self.send_header("Set-Cookie", self._set_cookie(token))
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        jalur = urllib.parse.urlparse(self.path).path.rstrip("/")

        if jalur.startswith("/murid/kerjakan/"):
            import students

            kredensial = self._sesi_atau_basic(peran_wajib="murid")
            if not kredensial:
                return self._kirim(
                    _halaman("Perlu masuk", "<h1>Halaman murid</h1>"), 401
                )
            panjang = int(self.headers.get("Content-Length", 0))
            mentah = self.rfile.read(panjang).decode("utf-8")
            data = {
                k: v[0]
                for k, v in urllib.parse.parse_qs(
                    mentah, keep_blank_values=True
                ).items()
            }
            sesi_id = int(jalur.split("/")[3])
            with database.buka() as kon:
                siswa_id = students.siswa_dari_akun(kon, kredensial[0])
                hasil = (
                    students.simpan_jawaban_murid(kon, siswa_id, sesi_id, data)
                    if siswa_id is not None
                    else None
                )
                # Diagnosis otomatis: jawaban baru dari HP langsung dinilai
                # mesin (usulan). Keputusan manual guru tidak pernah
                # ditimpa — lihat web.diagnosa_murid. Guru membuka halaman
                # sesi dan membaca hasil, bukan menekan tombol dulu.
                selesai = False
                if hasil:
                    # Waktu pengerjaan: POST pertama yang mengisi soal =
                    # mulai; semua terisi = selesai. Keduanya idempoten
                    # (WHERE IS NULL) — lihat database.tandai_mulai.
                    database.tandai_mulai(kon, sesi_id)
                    diagnosa_murid(kon, sesi_id)
                    # Semua soal sudah terisi → arahkan ke daftar sesi
                    # (?selesai= memicu banner perayaan di sana), bukan ke
                    # lembar yang sama. Anak yang masih setengah jalan
                    # tetap kembali ke lembar + banner tersimpan supaya
                    # bisa lanjut mengerjakan.
                    if siswa_id is not None:
                        selesai = students.semua_terisi(kon, siswa_id, sesi_id)
                        if selesai:
                            database.tandai_selesai(kon, sesi_id)
            if hasil is None:
                return self._kirim(
                    _halaman("403", "<h1>Bukan sesimu</h1>"), 403
                )
            if selesai:
                # Langsung kembali ke daftar sesi — banner ?selesai= sudah
                # mengonfirmasi. Halaman perayaan terpisah berarti satu
                # klik ekstra plus pilihan "Keluar" yang membingungkan;
                # tombol Keluar memang sudah ada di daftar sesi.
                self.send_response(303)
                self.send_header("Location", f"/murid?selesai={sesi_id}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            # Balik ke lembar kerja yang sama lewat 303 + parameter jumlah,
            # bukan menampilkan halaman langsung: pengalihan mencegah
            # pengiriman ganda kalau anak menekan muat-ulang.
            self.send_response(303)
            self.send_header(
                "Location", f"/murid/kerjakan/{sesi_id}?tersimpan={hasil}"
            )
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        # pendaftaran mandiri + login + logout — terbuka, tanpa palang
        if jalur == "/daftar":
            panjang = int(self.headers.get("Content-Length", 0) or 0)
            mentah = self.rfile.read(panjang).decode("utf-8") if panjang else ""
            data = {
                k: v[0]
                for k, v in urllib.parse.parse_qs(
                    mentah, keep_blank_values=True
                ).items()
            }
            return self._handle_daftar(data)
        if jalur == "/masuk":
            panjang = int(self.headers.get("Content-Length", 0) or 0)
            mentah = self.rfile.read(panjang).decode("utf-8") if panjang else ""
            data = {k: v[0] for k, v in urllib.parse.parse_qs(mentah, keep_blank_values=True).items()}
            return self._handle_masuk(data)
        if jalur == "/keluar":
            tok = self._ambil_token()
            if tok:
                sessions.hapus(tok)
            self.send_response(303)
            self.send_header("Location", "/masuk")
            self.send_header("Set-Cookie", self._set_cookie(None))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if not self._lolos_sandi():
            return

        if jalur == "/akun":
            panjang = int(self.headers.get("Content-Length", 0))
            mentah = self.rfile.read(panjang).decode("utf-8")
            data = {
                k: v[0]
                for k, v in urllib.parse.parse_qs(
                    mentah, keep_blank_values=True
                ).items()
            }
            ident = self._identitas()
            pengguna = ident[0] if ident else "guru"
            peran = ident[1] if ident else "guru"
            if peran == "admin" and data.get("aksi") != "sandi":
                # Kebijakan baca-semua-tulis-tidak: satu-satunya aksi admin
                # di /akun adalah mengganti sandinya sendiri.
                return self._tolak_admin()
            with database.buka() as kon:
                pesan, galat = proses_akun(kon, data, pengguna, peran)
                section = data.get("section") or PETA_SECTION_AKUN.get(
                    data.get("aksi", ""), "akun"
                )
                return self._kirim(
                    halaman_akun(
                        kon, pesan, galat,
                        pengguna=pengguna, peran=peran, section=section,
                    )
                )

        if jalur == "/admin":
            if self._peran_saya() != "admin":
                return self._kirim(
                    _halaman("Perlu masuk", "<h1>Halaman pengelola</h1>"), 401
                )
            panjang = int(self.headers.get("Content-Length", 0) or 0)
            mentah = self.rfile.read(panjang).decode("utf-8")
            data = {
                k: v[0]
                for k, v in urllib.parse.parse_qs(
                    mentah, keep_blank_values=True
                ).items()
            }
            pesan, galat = "", ""
            if data.get("aksi") == "guru_baru":
                nama = (data.get("pengguna") or "").strip()
                pw = data.get("sandi") or ""
                if not nama:
                    galat = "Nama akun tidak boleh kosong."
                elif len(pw) < 12:
                    galat = "Kata sandi minimal 12 karakter."
                else:
                    try:
                        auth.tambah_akun(nama, pw, "guru")
                        pesan = (
                            f"Akun orang tua {nama} dibuat. Orang tua bisa "
                            f"masuk lewat /masuk."
                        )
                    except ValueError as e:
                        galat = str(e)
            elif data.get("aksi") == "guru_sandi":
                # Satu tulisan lain yang sah di panel admin: menyetel ulang
                # sandi akun orang tua yang lupa — sama domainnya dengan
                # membuat akun (akun itu ciptaan admin). Detail di proses_admin.
                pesan, galat = proses_admin(data)
            else:
                galat = "Aksi tidak dikenal."
            ident = self._identitas()
            with database.buka() as kon:
                return self._kirim(
                    halaman_admin(
                        kon, pesan, galat,
                        pengguna=ident[0] if ident else "",
                    )
                )

        if jalur.startswith("/cerita/"):
            import llm

            try:
                sesi_id = int(jalur.split("/")[2])
            except (ValueError, IndexError):
                return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
            if self._peran_saya() == "admin":
                return self._tolak_admin()
            with database.buka() as kon:
                if not self._bisa_lihat_sesi(kon, sesi_id):
                    return self._kirim(
                        _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                    )
                _, _, catatan = llm.bungkus_sesi(kon, sesi_id, _soal_dari_baris)
                ident = self._identitas()
                return self._kirim(
                    halaman_sesi_stitch(
                        kon, sesi_id, catatan,
                        peran=ident[1] if ident else "guru",
                        pengguna=ident[0] if ident else "",
                    )
                )

        if jalur.startswith("/sesi-baru/"):
            if self._peran_saya() == "admin":
                return self._tolak_admin()
            try:
                siswa_id = int(jalur.split("/")[2])
            except (ValueError, IndexError):
                return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
            panjang = int(self.headers.get("Content-Length", 0) or 0)
            data = urllib.parse.parse_qs(
                self.rfile.read(panjang).decode("utf-8"),
                keep_blank_values=True,
            )
            pilihan_topik = (data.get("topik") or [TOPIK_BAWAAN])[0].strip()
            if pilihan_topik not in daftar_topik():
                # Topik asing = salah ketik pemanggil: ditolak jelas, BUKAN
                # jatuh diam-diam ke pola bilangan. Pesan menyebut daftar
                # yang sah supaya guru/pemanggil langsung tahu pilihannya.
                pesan = (
                    f"<h1>Topik tidak dikenal</h1>"
                    f"<p><code>{html.escape(pilihan_topik)}</code> tidak "
                    f"terdaftar. Yang tersedia: "
                    f"{', '.join(html.escape(t) for t in daftar_topik())}.</p>"
                )
                return self._kirim(_halaman("Topik tidak dikenal", pesan), 400)
            sesi_id = None
            nama_siswa = None
            with database.buka() as kon:
                if not self._bisa_lihat_siswa(kon, siswa_id):
                    return self._kirim(
                        _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                    )
                siswa = kon.execute(
                    "SELECT nama, tingkat FROM siswa WHERE id = ?", (siswa_id,)
                ).fetchone()
                if not siswa:
                    return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
                level = siswa["tingkat"] if siswa["tingkat"] in LEVEL else LEVEL_BAWAAN
                nama_siswa = siswa["nama"]
                if pilihan_topik not in _topik_untuk_level(level):
                    pesan = (
                        f"<h1>Topik belum tersedia untuk level ini</h1>"
                        f"<p><code>{html.escape(pilihan_topik)}</code> tidak tersedia "
                        f"untuk level {html.escape(siswa['tingkat'])}.</p>"
                    )
                    return self._kirim(_halaman("Topik belum tersedia", pesan), 400)
                pilihan_mode = (data.get("mode") or ["diagnostik"])[0].strip()
                if pilihan_mode not in ("diagnostik", "drill"):
                    pesan = (
                        f"<h1>Mode tidak dikenal</h1>"
                        f"<p><code>{html.escape(pilihan_mode)}</code> tidak terdaftar. "
                        f"Yang tersedia: diagnostik (Diagnosa), drill (Latihan Cepat).</p>"
                    )
                    return self._kirim(_halaman("Mode tidak dikenal", pesan), 400)
                timer_mode, durasi_menit, timer_auto = "tanpa", 15, 0
                if pilihan_mode == "drill":
                    timer_mode = (data.get("timer_mode") or ["sesi"])[0].strip()
                    if timer_mode not in ("tanpa", "sesi", "soal"):
                        pesan = (
                            f"<h1>Timer tidak dikenal</h1>"
                            f"<p><code>{html.escape(timer_mode)}</code> tidak terdaftar. "
                            f"Yang tersedia: tanpa (tanpa timer), sesi (per sesi, tampil jalan), "
                            f"soal (per soal, internal).</p>"
                        )
                        return self._kirim(_halaman("Timer tidak dikenal", pesan), 400)
                    nilai_durasi = (data.get("durasi_menit") or [""])[0].strip()
                    if not nilai_durasi.isdigit() or not 1 <= int(nilai_durasi) <= 180:
                        pesan = (
                            "<h1>Durasi tidak wajar</h1>"
                            f"<p>Durasi Latihan Cepat harus angka 1–180 menit "
                            f"(terima: {html.escape(nilai_durasi or '(kosong)')}).</p>"
                        )
                        return self._kirim(_halaman("Durasi tidak wajar", pesan), 400)
                    durasi_menit = int(nilai_durasi)
                    timer_auto = 1 if (data.get("timer_auto") or ["0"])[0] == "1" else 0
                sesi_id = buat_sesi_seed_baru(
                    kon, siswa_id, level=level, topik=pilihan_topik,
                    mode=pilihan_mode, timer_mode=timer_mode,
                    durasi_menit=durasi_menit, timer_auto=timer_auto,
                )
            # Tetap di dashboard (opsi 1): sesi baru adalah tempat anak
            # mengerjakan, bukan halaman guru yang kosong. Banner + sorotan baris
            # menunjukkan sesi mana yang baru, tanpa menampilkan lembar kosong.
            # PRG tetap dijaga: refresh tidak membuat sesi ganda.
            pesan_sukses = f"Sesi baru untuk {nama_siswa} berhasil dibuat — sesi #{sesi_id} siap dikerjakan."
            qs = urllib.parse.urlencode({"pesan": pesan_sukses, "sorot": sesi_id})
            self.send_response(303)
            self.send_header("Location", f"/?{qs}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if jalur.startswith("/lampiran/"):
            if self._peran_saya() == "admin":
                return self._tolak_admin()
            bagian = jalur.split("/")
            try:
                angka = int(bagian[2])
            except (ValueError, IndexError):
                return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)

            if len(bagian) >= 4 and bagian[3] == "terapkan":
                # Konfirmasi guru: tulis jawaban hasil koreksi ke jalur resmi.
                panjang = int(self.headers.get("Content-Length", 0) or 0)
                mentah = self.rfile.read(panjang).decode("utf-8")
                data = {
                    k: v[0]
                    for k, v in urllib.parse.parse_qs(
                        mentah, keep_blank_values=True
                    ).items()
                }
                with database.buka() as kon:
                    if not self._bisa_lihat_lampiran(kon, angka):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    jumlah, pesan = lampiran_mod.terapkan(kon, angka, data)
                    isi = lampiran_mod.halaman_konfirmasi(kon, angka, pesan)
                    if isi is None:
                        return self._kirim(
                            _halaman("404", "<h1>Lampiran hilang</h1>"), 404
                        )
                    return self._kirim(isi)

            # Upload foto (multipart) -> ekstraksi -> halaman konfirmasi.
            content_type = self.headers.get("Content-Type", "")
            panjang = int(self.headers.get("Content-Length", 0) or 0)
            if panjang > lampiran_mod.BATAS_UKURAN * 2:
                return self._kirim(
                    _halaman("Terlalu besar", "<h1>Upload terlalu besar</h1>"), 400
                )
            tubuh = self.rfile.read(panjang)
            with database.buka() as kon:
                if not kon.execute(
                    "SELECT 1 FROM sesi WHERE id = ?", (angka,)
                ).fetchone() or not self._bisa_lihat_sesi(kon, angka):
                    # Satu body 404 yang sama untuk "tidak ada" maupun
                    # "bukan milikmu" — beda body jadi oracle eksistensi.
                    return self._kirim(
                        _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                    )
                lid, pesan = lampiran_mod.proses_upload(
                    kon, angka, content_type, tubuh
                )
            if lid is None:
                # Gagal validasi (bukan gambar, terlalu besar, kosong):
                # 400 dengan pesan jelas — bukan 200 menyamarkan kegagalan.
                return self._kirim(
                    _halaman("Upload ditolak", f"<h1>Upload ditolak</h1><p>{html.escape(pesan)}</p>"),
                    400,
                )
            self.send_response(303)
            self.send_header("Location", f"/lampiran/{lid}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if jalur.startswith("/sesi/") and jalur.endswith("/hapus"):
            if self._peran_saya() == "admin":
                return self._tolak_admin()
            try:
                sesi_id = int(jalur.split("/")[2])
            except (ValueError, IndexError):
                return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
            with database.buka() as kon:
                if not self._bisa_lihat_sesi(kon, sesi_id):
                    return self._kirim(
                        _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                    )
            panjang = int(self.headers.get("Content-Length", 0) or 0)
            data = urllib.parse.parse_qs(
                self.rfile.read(panjang).decode("utf-8"),
                keep_blank_values=True,
            )
            if (data.get("konfirmasi") or [""])[0] != "1":
                # Tanpa konfirmasi = hanya melihat halaman peringatan lagi.
                # Sesi tidak disentuh sama sekali.
                with database.buka() as kon:
                    ident = self._identitas()
                    isi = halaman_konfirmasi_hapus(
                        kon, sesi_id,
                        pengguna=ident[0] if ident else "",
                        peran=ident[1] if ident else "guru",
                    )
                if isi is None:
                    return self._kirim(
                        _halaman("404", "<h1>Sesi tidak ada</h1>"), 404
                    )
                return self._kirim(isi)
            with database.buka() as kon:
                dihapus = database.hapus_sesi(kon, sesi_id)
            if not dihapus:
                return self._kirim(
                    _halaman("404", "<h1>Sesi tidak ada</h1>"), 404
                )
            # Berkas foto tidak diurus DB — dibuang di sini, SETELAH baris
            # DB benar-benar hilang supaya tidak ada foto yatim sebaliknya.
            lampiran_mod.bersihkan_berkas(sesi_id)
            tujuan = urllib.parse.urlencode({"pesan": f"Sesi {sesi_id} dihapus."})
            self.send_response(303)
            self.send_header("Location", f"/?{tujuan}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if not jalur.startswith("/sesi/"):
            return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
        if self._peran_saya() == "admin":
            # Simpan jawaban/diagnosis = tulis data murid.
            return self._tolak_admin()

        panjang = int(self.headers.get("Content-Length", 0))
        mentah = self.rfile.read(panjang).decode("utf-8")
        data = {
            k: v[0]
            for k, v in urllib.parse.parse_qs(mentah, keep_blank_values=True).items()
        }

        sesi_id = int(jalur.split("/")[2])
        with database.buka() as kon:
            if not self._bisa_lihat_sesi(kon, sesi_id):
                return self._kirim(
                    _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                )
            pesan = simpan_sesi(kon, sesi_id, data)
            ident = self._identitas()
            self._kirim(
                halaman_sesi_stitch(
                    kon, sesi_id, pesan,
                    peran=ident[1] if ident else "guru",
                    pengguna=ident[0] if ident else "",
                )
            )

    def log_message(self, *a) -> None:  # senyapkan log akses
        pass
