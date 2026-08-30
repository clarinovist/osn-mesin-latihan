"""Halaman guru: input hasil + laporan. Stdlib saja, tanpa framework.

Alasan tanpa framework: satu-satunya pengguna adalah guru di jaringan
rumah/VPS sendiri, kuerinya sedikit, dan tiap dependensi tambahan adalah
satu hal lagi yang bisa gagal saat deploy. spike/sajikan.py sudah memakai
http.server dan itu terbukti cukup.

Rute:
    GET  /                     daftar siswa + sesi
    GET  /sesi/<id>            formulir input hasil satu sesi
    POST /sesi/<id>            simpan jawaban -> diagnosis otomatis
    GET  /laporan/<siswa_id>   tren K, miskonsepsi berulang, peta materi
"""

from __future__ import annotations

import html
import json
import random
import urllib.parse
from dataclasses import replace
from datetime import datetime
from http.server import BaseHTTPRequestHandler

import basis
import cetak
import design_tokens as T
import lampiran as lampiran_mod
import sandi
import sesi
from diagnosa import diagnosa
from gaya_guru import GAYA_GURU as GAYA, SKRIP_MATA_SANDI
from generator import LEVEL_BAWAAN, buat_soal
from templates import LEVEL, REGISTRI, Soal, level_valid
from topik import TOPIK_BAWAAN, Topik, ambil, daftar_topik, dari_sesi

KODE_PILIHAN = [
    ("", "— pilih —"),
    ("benar", "Benar"),
    ("K", "K — salah konsep"),
    ("B", "B — salah baca soal"),
    ("H", "H — salah hitung"),
    ("E", "E — salah tulis akhir"),
    ("T", "T — belum pernah lihat"),
    ("N", "N — menebak"),
]

PETA_SECTION_AKUN = {
    # Aksi POST /akun -> section tempat hasilnya ditampilkan, supaya
    # pengguna kembali ke tempat formnya, bukan melompat ke bawaan.
    "sandi": "akun",
    "siswa": "siswa",
    "anak_baru": "siswa",
    "tingkat": "siswa",
    "siswa_hapus": "siswa",
    "akun_murid_tambah": "akun-murid",
    "akun_murid_hapus": "akun-murid",
    "akun_murid_sandi": "akun-murid",
}


def _halaman(
    judul: str, isi: str, ident: tuple[str, str] | None = None
) -> bytes:
    """Bingkai semua halaman pengelola. `ident=(pengguna, peran)` menampilkan
    topbar dengan menu pengguna di atas isi — satu pintu agar konsisten."""
    batang = _topbar(*ident) if ident else ""
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title><style>{GAYA}</style></head>
<body><div class="bungkus">{batang}{isi}</div><script>{SKRIP_MATA_SANDI}</script></body></html>""".encode()


def _soal_dari_baris(baris) -> Soal:
    """Bangun ulang objek Soal dari parameter yang tersimpan.

    Teks soal sengaja tidak disimpan di basis data — hanya parameter — supaya
    perbaikan kalimat soal langsung berlaku untuk sesi lama juga.

    Level diambil dari baris, bukan dari tingkat siswa saat ini: anak yang
    sudah naik ke P5 tetap harus melihat sesi P3-nya tercetak sebagai P3.

    Sejak A4 parameter tersimpan JSON murni (list tetap list) dan template
    menerima bentuk itu langsung — restorasi TIDAK punya cabang per template.
    Cabang semacam itu adalah jebakan: template baru dengan parameter
    berstruktur harus menambah cabang di sini untuk bisa direstorasi, dan
    yang lupa tidak gagal saat test tapi saat halaman guru menampilkan soal
    yang salah.
    """
    param = json.loads(baris["parameter"])
    soal = REGISTRI[baris["template_id"]](**param)
    soal = replace(soal, level=_ambil(baris, "level", LEVEL_BAWAAN))

    # Versi cerita dari LLM (B2), kalau ada. Yang diganti HANYA kalimatnya;
    # kunci, malrule, dan parameter tetap hasil hitungan Python — itulah
    # yang membuat diagnosis tetap hidup meski kalimatnya dikarang model.
    cerita = (_ambil(baris, "cerita", "") or "").strip()
    if cerita:
        soal = replace(soal, teks=cerita)
    return soal


def _ambil(baris, kolom: str, bawaan):
    """Baca kolom yang mungkin belum ada di baris.

    sqlite3.Row melempar IndexError untuk kolom tak dikenal, dan sebagian
    test memberi dict biasa. Dipakai untuk kolom hasil migrasi supaya
    pemanggil lama tidak pecah.
    """
    try:
        nilai = baris[kolom]
    except (IndexError, KeyError):
        return bawaan
    return bawaan if nilai is None else nilai


def _topik_untuk_level(level: str) -> list[str]:
    """ID topik yang tersedia pada level resmi atau fallback data lama."""
    level_efektif = level if level in LEVEL else LEVEL_BAWAAN
    return [
        topik_id
        for topik_id in daftar_topik()
        if level_efektif in ambil(topik_id).komposisi
    ]


def _badge_mode(baris) -> str:
    """Badge 'Latihan Cepat' untuk sesi drill; kosong untuk diagnostik.

    CSS guru memuat kata "Latihan Cepat" di komentar, jadi badge-nya
    harus marker kelas, bukan teks yang dicari mentah.
    """
    if _ambil(baris, "mode", "diagnostik") == "drill":
        return '<span class="badge-mode">Latihan Cepat</span>'
    return ""


def _fmt_durasi(mulai, selesai) -> str:
    """Durasi pengerjaan mm:ss dari kolom mulai/selesai sesi.

    Keduanya harus terisi — sesi yang belum selesai jujur tampil '—',
    bukan durasi setengah jalan yang menyesatkan. Sesi yang dicatat
    lewat kertas tidak punya keduanya dan memang tidak bisa diukur.
    """
    BENTUK = "%Y-%m-%d %H:%M:%S"
    if not mulai or not selesai:
        return "&mdash;"
    try:
        detik = int(
            (
                datetime.strptime(str(selesai), BENTUK)
                - datetime.strptime(str(mulai), BENTUK)
            ).total_seconds()
        )
    except ValueError:
        return "&mdash;"
    if detik <= 0:
        return "&mdash;"
    return f"{detik // 60}:{detik % 60:02d}"


def _badge_peran(peran: str) -> str:
    """Penanda peran di topbar — supaya siapa pun langsung tahu di sisi mana
    dia berada. Murid punya dunia visual sendiri, jadi cukup dua ini."""
    if peran == "admin":
        return '<span class="badge-peran badge-peran-admin">Pengelola</span>'
    if peran == "guru":
        return '<span class="badge-peran badge-peran-guru">Orang Tua</span>'
    return ""


def _topbar(pengguna: str, peran: str) -> str:
    """Topbar semua halaman pengelola: brand + menu pengguna dropdown.

    Menu dari <details> CSS-only — tanpa JS. Gemboknya nama akun + badge
    peran supaya keluhan "cuma teks polos" hilang: batas menunya jelas.
    Isinya menyesuaikan peran (guru: pintu keluarga; admin: dashboard
    admin + ganti sandi), dan keluar tinggal satu pintu yang sama."""
    if peran == "admin":
        brand, item = "/admin", (
            '<a href="/admin">Dashboard admin</a>'
            '<a href="/akun?section=akun">Ganti sandi</a>'
        )
    else:
        brand, item = "/", '<a href="/akun">Akun &amp; Siswa</a>'
    siapa = html.escape(pengguna) if pengguna else ""
    return (
        f'<div class="topbar">'
        f'<a class="brand" href="{brand}">{T.NAMA_PRODUK}</a>'
        f'<nav class="topbar-navigasi">'
        f'<details class="menu-pengguna">'
        f'<summary>{siapa} {_badge_peran(peran)}</summary>'
        f'<div class="menu-isi">{item}'
        f'<div class="menu-pisah"></div>'
        f'<form method="post" action="/keluar" style="margin:0">'
        f'<button type="submit">Keluar</button>'
        f"</form></div></details></nav></div>"
    )


def halaman_utama(
    kon,
    pesan: str = "",
    pemilik: str | None = None,
    peran: str = "guru",
) -> bytes:
    """Dashboard pengelola. `pemilik=None` = semua keluarga (admin);
    string = hanya keluarga itu. Panggilan lama tanpa argumen tetap
    melihat semuanya — perilaku mode lokal dan test langsung."""
    baris = []
    admin = peran == "admin"
    # Opsi topik disaring per tingkat: paket P5/P6 tidak boleh ditawarkan
    # pada kartu siswa P3 lalu gagal ketika form dikirim.
    for s in basis.daftar_siswa(kon, pemilik):
        opsi_topik = "".join(
            f'<option value="{html.escape(t)}">{html.escape(ambil(t).nama)}</option>'
            for t in _topik_untuk_level(s["tingkat"])
        )
        sesi = kon.execute(
            """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode,
                      s.mulai, s.selesai,
                      (SELECT COUNT(*) FROM sesi_soal WHERE sesi_id = s.id) AS n,
                      (SELECT COUNT(*) FROM sesi_soal ss
                       JOIN jawaban j ON j.sesi_soal_id = ss.id
                       WHERE ss.sesi_id = s.id) AS terisi,
                      (SELECT COUNT(*) FROM sesi_soal ss
                       JOIN jawaban j ON j.sesi_soal_id = ss.id
                       JOIN diagnosis d ON d.jawaban_id = j.id
                       WHERE ss.sesi_id = s.id AND d.benar = 1) AS benar
               FROM sesi s WHERE s.siswa_id = ?
               ORDER BY s.tanggal DESC, s.id DESC""",
            (s["id"],),
        ).fetchall()

        item = "".join(
            f'<tr><td><a href="/sesi/{r["id"]}">Sesi #{r["id"]}</a>'
            f'{_badge_mode(r)}</td>'
            f'<td>{r["tanggal"]}</td>'
            f'<td class="tipe">{_ambil(r, "level", LEVEL_BAWAAN)}</td>'
            f'<td class="tipe" style="white-space:nowrap">{_ambil(r, "topik", TOPIK_BAWAAN)}</td>'
            f'<td class="angka">{r["terisi"]}/{r["n"]}</td>'
            f'<td class="angka">{r["benar"]}/{r["n"]}</td>'
            f'<td class="angka">{_fmt_durasi(_ambil(r, "mulai", None), _ambil(r, "selesai", None))}</td></tr>'
            for r in sesi
        ) or '<tr><td colspan="7" class="kosong">belum ada sesi</td></tr>'

        label_keluarga = ""
        if admin:
            siapa = s["pemilik"] or "warisan"
            label_keluarga = (
                f'<span class="badge-keluarga">keluarga: {html.escape(siapa)}</span>'
            )

        baris.append(
            f'<div class="kartu kartu-siswa">'
            f'<div class="siswa-kepala">'
            f"<h2>{html.escape(s['nama'])}"
            f'<span class="badge-tingkat">({s["tingkat"]})</span>'
            f"{label_keluarga}"
            f"</h2>"
            f'<a class="btn" href="/laporan/{s["id"]}">Lihat laporan &rarr;</a>'
            f"</div>"
            f'<div class="tabel-wrap"><table><tr><th>Sesi</th><th>Tanggal</th>'
            f"<th>Level</th><th>Topik</th><th>Terisi</th><th>Benar</th>"
            f"<th>Waktu</th></tr>"
            f"{item}</table></div>"
            f'<form method="post" action="/sesi-baru/{s["id"]}" '\
                        f'class="baris" style="margin-top:.9rem">'\
                        f'<div><label>Topik</label>'\
                        f'<select name="topik">{opsi_topik}</select></div>'\
                        f'<div><label>Mode</label>'\
                        f'<div class="mode-pilih">'\
                        f'<label class="mode-opsi"><input type="radio" name="mode" '\
                        f'value="diagnostik" checked> Diagnosa</label>'\
                        f'<label class="mode-opsi"><input type="radio" name="mode" '\
                        f'value="drill"> Latihan Cepat</label>'\
                        f'</div></div>'\
                        f'<div class="pengaturan-timer" style="display:none">'\
                        f'<label>Durasi '\
                        f'<input type="number" name="durasi_menit" value="15" '\
                        f'min="1" max="180" style="width:4.5rem"> menit</label>'\
                        f'<label class="mode-opsi"><input type="radio" name="timer_mode" '\
                        f'value="sesi" checked> per sesi (tampil)</label>'\
                        f'<label class="mode-opsi"><input type="radio" name="timer_mode" '\
                        f'value="soal"> per soal (internal)</label>'\
                        f'<label class="mode-opsi"><input type="checkbox" '\
                        f'name="timer_auto" value="1"> auto-submit</label>'\
                        f'</div>'\
                        f'<div style="display:flex;align-items:flex-end">'\
                        f'<button type="submit" class="tombol-coral" style="width:100%">'\
                        f"Buat sesi baru</button></div></form>"
            f"</div>"
        )

    isi_utama = "".join(baris) or (
        '<div class="kartu kosong-hint-guru">Belum ada siswa. '
        '<a href="/akun">Buat siswa</a> dari halaman Akun &amp; Siswa.</div>'
    )

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""

    return _halaman(
        T.NAMA_PRODUK,
        f"<h1>{T.NAMA_PRODUK} — Latihan Matematika SD</h1>"
        f'<p class="sub">Pilih sesi untuk memasukkan hasil, atau buka laporan '
        f"untuk melihat tren.</p>"
        f"{kabar}"
        f'<div class="grid-utama">{isi_utama}</div>'
        f'<script>'
        f'(function(){{'
        f'var r=document.querySelectorAll(\'input[name="mode"]\');'
        f'for(var i=0;i<r.length;i++){{'
        f'r[i].addEventListener("change",function(){{'
        f'var t=this.closest("form").querySelector(".pengaturan-timer");'
        f'if(t)t.style.display=this.value==="drill"?"":"none";'
        f'}});}}'
        f'}})()'
        f'</script>',
        ident=(pemilik if pemilik else "guru", peran),
    )


def _tombol_cerita(kon, sesi_id: int) -> str:
    """Tombol "variasi cerita" (LLM B2). Manual, bukan otomatis.

    Otomatis saat buat sesi berarti tiap sesi membayar 12 panggilan API
    tanpa guru pernah memilih. Satu tombol membuat biayanya sadar: guru
    menekannya kalau anak mulai hafal kalimat soalnya, bukan tiap kali.

    Kalau kunci DeepSeek tidak dipasang, tombolnya tidak muncul sama sekali
    — bukan muncul lalu gagal saat ditekan. Fitur yang mati harus terlihat
    mati.
    """
    import llm

    if not llm.aktif():
        return ""

    sudah = kon.execute(
        """SELECT COUNT(*) AS n FROM soal s
           JOIN sesi_soal ss ON ss.soal_id = s.id
           WHERE ss.sesi_id = ? AND TRIM(COALESCE(s.cerita, '')) <> ''""",
        (sesi_id,),
    ).fetchone()["n"]
    total = kon.execute(
        "SELECT COUNT(*) AS n FROM sesi_soal WHERE sesi_id = ?", (sesi_id,)
    ).fetchone()["n"]

    if sudah >= total and total:
        catatan = f"Semua {total} soal sudah punya versi cerita."
        tombol = ""
    else:
        catatan = (
            f"{sudah} dari {total} soal punya versi cerita. "
            "Angka dan kuncinya tidak berubah — hanya kalimatnya."
        )
        tombol = (
            f'<form method="post" action="/cerita/{sesi_id}" '
            f'style="margin-top:.6rem">'
            f'<button type="submit" class="tombol-amber" '
            f'style="margin-top:0">Variasi cerita &nbsp;✨</button></form>'
        )

    return (
        f'<div class="kartu kartu-variasi"><h2>Variasi cerita ✨</h2>'
        f'<p class="sub">{catatan}</p>{tombol}</div>'
    )


def halaman_konfirmasi_hapus(
    kon, sesi_id: int, pengguna: str = "", peran: str = "guru"
) -> bytes | None:
    """Halaman konfirmasi sebelum menghapus sesi (dua langkah, tanpa JS).

    Peringatannya menyebut angka NYATA sesi ini — berapa jawaban, diagnosis,
    dan foto yang ikut hilang. Tanpa angka, "hapus" terasa ringan; dengan
    angka, keputusannya sadar. Mengembalikan None bila sesi tidak ada.
    """
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.level, s.topik, w.nama
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return None

    def _hitung(sql: str) -> int:
        return kon.execute(sql, (sesi_id,)).fetchone()[0]

    n_jawaban = _hitung(
        """SELECT COUNT(*) FROM jawaban j
           JOIN sesi_soal ss ON ss.id = j.sesi_soal_id WHERE ss.sesi_id = ?"""
    )
    n_diagnosis = _hitung(
        """SELECT COUNT(*) FROM diagnosis d
           JOIN jawaban j ON j.id = d.jawaban_id
           JOIN sesi_soal ss ON ss.id = j.sesi_soal_id WHERE ss.sesi_id = ?"""
    )
    n_foto = _hitung("SELECT COUNT(*) FROM lampiran WHERE sesi_id = ?")

    return _halaman(
        f"Hapus sesi #{sesi_id}?",
        f'<div class="jejak"><a href="/sesi/{sesi_id}">&larr; Batal, kembali ke sesi</a></div>'
        f"<h1>Hapus sesi #{sesi_id}?</h1>"
        f'<div class="kartu">'
        f'<p>Sesi <b>#{sesi_id}</b> milik <b>{html.escape(info["nama"])}</b> '
        f'&middot; {info["tanggal"]} &middot; {_ambil(info, "level", LEVEL_BAWAAN)} '
        f'&middot; {_ambil(info, "topik", TOPIK_BAWAAN)}</p>'
        f"<p>Yang ikut hilang bersama sesi ini:</p>"
        f"<ul><li><b>{n_jawaban} jawaban</b></li>"
        f"<li><b>{n_diagnosis} diagnosis</b></li>"
        f"<li><b>{n_foto} foto</b> lembar</li></ul>"
        f'<div class="pesan galat">Tindakan ini <b>tidak bisa dibatalkan</b>. '
        f"Riwayat diagnosis tidak bisa dibangun ulang.</div>"
        f'<form method="post" action="/sesi/{sesi_id}/hapus" '
        f'style="margin-top:.9rem;display:flex;gap:.6rem;align-items:center">'
        f'<input type="hidden" name="konfirmasi" value="1">'
        f'<button type="submit" class="tombol-hapus">Ya, hapus sesi ini</button>'
        f'<a href="/sesi/{sesi_id}">Batal</a>'
        f"</form></div>",
        ident=(pengguna, peran) if pengguna else None,
    )


def halaman_sesi(
    kon, sesi_id: int, pesan: str = "", peran: str = "guru",
    pengguna: str = "",
) -> bytes:
    """Detail satu sesi. `peran="admin"` = varian hanya-baca.

    Kebijakan admin baca-semua-tulis-tidak dijaga di router (POST ditolak
    404); di sini tombol/form tulis disembunyikan supaya admin tidak
    menabrak 404 dari UI-nya sendiri. Baca tetap utuh: daftar lampiran,
    lembar, kunci, dan tautan laporan."""
    admin = peran == "admin"
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode,
                   w.nama, w.id AS siswa_id
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return _halaman("Tidak ada", "<h1>Sesi tidak ditemukan</h1>")

    kartu = []
    for b in basis.isi_sesi(kon, sesi_id):
        soal = _soal_dari_baris(b)
        sudah = b["jawaban_id"] is not None
        kode = b["kode_final"]
        benar = b["benar"]

        if sudah and (benar or kode):
            kelas, lencana = "sudah", (
                '<span class="kode benar">BENAR</span>' if benar
                else f'<span class="kode {kode}">{kode}</span>'
            )
        elif sudah:
            kelas, lencana = "perlu", '<span class="kode N">?</span>'
        else:
            kelas, lencana = "", ""

        usulan = ""
        if sudah and b["alasan"]:
            ragu = "" if (benar or kode) else " ragu"
            usulan = (
                f'<div class="usulan{ragu}"><b>Mesin:</b> '
                f'{html.escape(b["alasan"])}</div>'
            )

        restate = ""
        if soal.minta_restatement:
            restate = (
                f'<label>Kotak "mintanya apa" — tulis ulang apa yang anak isi</label>'
                f'<input type="text" name="restate_{b["sesi_soal_id"]}" '
                f'value="{html.escape(b["restatement"] or "")}">'
            )

        pilih = "".join(
            f'<option value="{v}"{" selected" if (v == kode or (v == "benar" and benar)) else ""}>'
            f"{html.escape(t)}</option>"
            for v, t in KODE_PILIHAN
        )

        kartu.append(f"""
<div class="kartu soal-kartu {kelas}">
  <div class="kartu-kepala">
    <span class="nomor">{b["nomor"]}</span>{lencana}
    <span class="tipe">{b["template_id"]}</span>
  </div>
  <div class="teks-soal">{html.escape(soal.teks)}</div>
  <div>Kunci: <span class="kunci">{html.escape(b["kunci"])}</span></div>
  {restate}
  <div class="baris">
    <div><label>Jawaban anak</label>
      <input type="text" name="jwb_{b["sesi_soal_id"]}"
             value="{html.escape(b["jawaban"] or "")}"></div>
    <div><label>Kode (kosongkan = pakai usulan mesin)</label>
      <select name="kode_{b["sesi_soal_id"]}">{pilih}</select></div>
  </div>
  <label>Isi kotak "Caraku" — ringkas saja, cukup yang menunjukkan caranya</label>
  <textarea name="cara_{b["sesi_soal_id"]}">{html.escape(b["cara"] or "")}</textarea>
  <div class="centang">
    <input type="checkbox" id="bp{b["sesi_soal_id"]}"
           name="belum_{b["sesi_soal_id"]}"
           {"checked" if b["belum_pernah"] else ""}>
    <label for="bp{b["sesi_soal_id"]}" style="margin:0">
      anak mencentang "belum pernah lihat soal seperti ini"</label>
  </div>
  {usulan}
</div>""")

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""

    # Badge mode sesi (Latihan Cepat / drill) — helper yang sama dengan
    # dashboard; CSS guru memuat kata "Latihan Cepat" di komentar, jadi
    # badge-nya harus marker kelas.
    badge_mode = _badge_mode(info)

    # Lampiran foto lembar (Fase 2): form upload + daftar foto yang sudah ada.
    # Upload menjalankan ekstraksi AI, hasilnya dikonfirmasi guru di halaman
    # /lampiran/<id> sebelum masuk jawaban.
    baris_lampiran = []
    for lamp in basis.daftar_lampiran(kon, sesi_id):
        status_cls = "benar" if lamp["status"] == "diterapkan" else "N"
        baris_lampiran.append(
            f'<li><a href="/lampiran/{lamp["id"]}">'
            f'{html.escape(lamp["nama_berkas"])}</a> '
            f'<span class="kode {status_cls}">{lamp["status"]}</span> '
            f'<span class="waktu">{html.escape(lamp["dibuat"])}</span></li>'
        )
    daftar = (
        f'<ul class="daftar-lampiran">{"".join(baris_lampiran)}</ul>'
        if baris_lampiran
        else '<p class="sub">Belum ada foto lembar.</p>'
    )
    unggah = (
        ""
        if admin
        else (
            f'<form method="post" action="/lampiran/{sesi_id}" '
            'enctype="multipart/form-data">'
            "<label>Foto lembar yang sudah diisi anak (jpeg/png, maks 8MB)</label>"
            '<input type="file" name="foto" accept="image/jpeg,image/png">'
            '<button type="submit">Upload foto</button>'
            "</form>"
        )
    )
    blok_lampiran = (
        '<div class="kartu blok-lampiran">'
        "<h2>Lampiran — foto lembar</h2>"
        f"{daftar}"
        f"{unggah}"
        "</div>"
    )

    tombol_hapus = (
        ""
        if admin
        else (
            f'<form method="get" action="/sesi/{sesi_id}/hapus" '
            f'style="margin:.4rem 0">'
            f'<button type="submit" class="tombol-kecil tombol-hapus">'
            f"Hapus sesi</button></form>"
        )
    )
    blok_cerita = "" if admin else _tombol_cerita(kon, sesi_id)
    if admin:
        # fieldset disabled mematikan semua input tanpa JS — admin tetap
        # bisa MEMBACA nilai tersimpan, tapi tak ada yang bisa dikirim.
        blok_isi = f'<fieldset disabled>{"".join(kartu)}</fieldset>'
    else:
        blok_isi = (
            f'<form method="post" action="/sesi/{sesi_id}">'
            f'{"".join(kartu)}'
            f'<div class="simpan-strip"><button type="submit">'
            f"Simpan &amp; diagnosis</button></div></form>"
        )

    return _halaman(
        f"Sesi #{sesi_id}",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f'<h1>{html.escape(info["nama"])} — Sesi #{sesi_id}</h1>'
        f'<p class="sub">{info["tanggal"]} &middot; '
        f'{_ambil(info, "level", LEVEL_BAWAAN)} &middot; '
        f'{_ambil(info, "topik", TOPIK_BAWAAN)} &middot; '
        f'seed {info["seed"]} {badge_mode} '
        f'&middot; '
        f'<a href="/lembar/{sesi_id}" target="_blank">lembar soal</a> &middot; '
        f'<a href="/lembar/{sesi_id}/penilaian" target="_blank">lembar kunci</a> '
        f'&middot; <a href="/laporan/{info["siswa_id"]}">laporan siswa ini</a></p>'
        f"{tombol_hapus}"
        f"{kabar}"
        f"{blok_cerita}"
        f"{blok_lampiran}"
        f"{blok_isi}",
        ident=(pengguna, peran) if pengguna else None,
    )


def simpan_sesi(kon, sesi_id: int, data: dict) -> str:
    """Simpan jawaban lalu jalankan diagnosis otomatis.

    Kode dari guru menang atas usulan mesin, dan bedanya dicatat lewat kolom
    `manual` supaya nanti bisa diukur seberapa sering mesin meleset.
    """
    diubah = 0
    for b in basis.isi_sesi(kon, sesi_id):
        sid = b["sesi_soal_id"]
        jwb = data.get(f"jwb_{sid}", "").strip()
        cara = data.get(f"cara_{sid}", "").strip()
        restate = data.get(f"restate_{sid}", "").strip()
        belum = f"belum_{sid}" in data
        pilihan = data.get(f"kode_{sid}", "").strip()

        if not (jwb or cara or restate or belum or pilihan):
            continue

        jid = basis.simpan_jawaban(kon, sid, jwb, cara, restate, belum)

        soal = _soal_dari_baris(b)
        u = diagnosa(
            b["kunci"], jwb, cara, restate, belum,
            basis.malrule_soal(kon, b["soal_id"]),
            soal.minta_restatement,
        )

        if pilihan == "benar":
            benar, final, manual = True, None, True
        elif pilihan:
            benar, final, manual = False, pilihan, True
        else:
            benar, final, manual = u.benar, u.kode, False

        basis.simpan_diagnosis(
            kon, jid, benar, u.kode, final, u.malrule_id, u.alasan, manual
        )
        diubah += 1

    return f"{diubah} soal tersimpan dan didiagnosis."


def diagnosa_murid(kon, sesi_id: int) -> int:
    """Jalankan diagnosis atas semua jawaban SESI ini yang belum dinilai.

    Dipanggil otomatis setiap kali anak menyimpan dari HP, supaya guru yang
    membuka halaman sesi langsung melihat BENAR/kode — bukan deretan "?"
    oranye yang menunggu diklik dulu.

    Satu palang yang membuat ini aman: baris diagnosis yang `manual=1`
    (keputusan guru) DILEWATI, bukan dihitung ulang. Mesin boleh menyegarkan
    usulannya di kode_usulan, tapi kode_final dan benar milik guru tetap.
    Tanpa itu, sekali anak memperbarui jawaban dari HP, penilaian guru
    terhapus senyap — kegagalan paling mahal jenisnya.

    Mengembalikan jumlah soal yang baru didiagnosis. Baris tanpa jawaban
    (soal yang anak lewati) tidak dibuat — aturan yang sama dengan guru.
    """
    jumlah = 0
    # Mode sesi: drill (Latihan Cepat) tidak meminta Caraku, jadi diagnosis
    # memakai cara sintetis supaya aturan "jawaban tanpa cara = N (menebak)"
    # tidak salah menuduh. Storage tetap cara='' — lihat murid.AWALAN_DRILL.
    import murid  # impor terlambat: web.py tidak boleh mengimpor murid di atas

    baris_mode = kon.execute(
        "SELECT mode FROM sesi WHERE id = ?", (sesi_id,)
    ).fetchone()
    drill = bool(baris_mode and baris_mode["mode"] == "drill")

    def _cara(b) -> str:
        cara = b["cara"] or ""
        return murid.AWALAN_DRILL + cara if drill else cara

    for b in basis.isi_sesi(kon, sesi_id):
        if b["jawaban_id"] is None:
            continue  # anak melewati soal ini: biarkan tanpa baris
        if b["manual"] == 1:
            # Segarkan usulan mesin saja; vonis guru tidak disentuh.
            soal = _soal_dari_baris(b)
            u = diagnosa(
                b["kunci"], b["jawaban"] or "", _cara(b),
                b["restatement"] or "", bool(b["belum_pernah"]),
                basis.malrule_soal(kon, b["soal_id"]),
                soal.minta_restatement,
            )
            kon.execute(
                """UPDATE diagnosis SET kode_usulan = ?, alasan = ?
                   WHERE jawaban_id = ?""",
                (u.kode, u.alasan, b["jawaban_id"]),
            )
            continue
        soal = _soal_dari_baris(b)
        u = diagnosa(
            b["kunci"], b["jawaban"] or "", _cara(b),
            b["restatement"] or "", bool(b["belum_pernah"]),
            basis.malrule_soal(kon, b["soal_id"]),
            soal.minta_restatement,
        )
        basis.simpan_diagnosis(
            kon, b["jawaban_id"],
            benar=u.benar, kode_usulan=u.kode, kode_final=u.kode,
            malrule_id=u.malrule_id, alasan=u.alasan, manual=False,
        )
        jumlah += 1
    return jumlah


def _chart_tren(ring) -> str:
    """SVG line chart % benar per sesi (mockup guru-laporan).

    ring diurutkan DESC oleh basis.ringkasan; dibalik supaya sumbu x
    berjalan kronologis (sesi terbaru di kanan). Kalau kurang dari 2 titik
    tidak digambar — satu titik tidak bisa disebut tren.
    """
    if len(ring) < 2:
        return ""
    TEAL, GRID, AXIS = T.STATUS_KUAT, T.CHART_GRID, T.CHART_AXIS
    urut = list(reversed(ring))
    LEBAR, TINGGI = 540, 240
    PAD_X, PAD_Y, PAD_B = 40, 16, 40
    n = len(urut)
    def x(i):  # posisi titik ke-i
        return PAD_X + i * (LEBAR - PAD_X - 12) / max(1, n - 1)
    def y(persen):  # 0..100 -> koordinat (SVG y ke bawah)
        return PAD_Y + (100 - persen) * (TINGGI - PAD_Y - PAD_B) / 100
    pts = []
    for i, r in enumerate(urut):
        jml = r["jumlah_soal"] or 0
        psen = (r["benar"] or 0) / jml * 100 if jml else 0
        pts.append(round(x(i), 1))
        pts.append(round(y(psen), 1))
    poly = " ".join(",".join(str(p) for p in pts[i:i+2]) for i in range(0, len(pts), 2))
    titik = "".join(
        f'<circle cx="{(pts[i])}" cy="{pts[i+1]}" r="4" fill="{TEAL}"/>'
        for i in range(0, len(pts), 2)
    )
    grid = "".join(
        f'<line x1="{PAD_X}" y1="{y(p)}" x2="{LEBAR-12}" y2="{y(p)}" '
        f'stroke="{GRID}" stroke-width="1" stroke-dasharray="4 4"/>'
        f'<text x="{PAD_X-6}" y="{y(p)+4}" text-anchor="end" '
        f'font-size="11" fill="{AXIS}">{p}</text>'
        for p in (25, 50, 75, 100)
    )
    xlab = "".join(
        f'<text x="{x(i)}" y="{TINGGI-16}" text-anchor="middle" '
        f'font-size="11" fill="{AXIS}">#{urut[i]["sesi_id"]}</text>'
        for i in range(n)
    )
    return (
        f'<svg viewBox="0 0 {LEBAR} {TINGGI}" role="img" '
        f'aria-label="Tren persentase benar per sesi">'
        f"{grid}{poly and ''}"
        f'<polyline points="{poly}" fill="none" stroke="{TEAL}" '
        f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        f"{titik}{xlab}"
        f'<line x1="{PAD_X}" y1="{y(0)}" x2="{LEBAR-12}" y2="{y(0)}" '
        f'stroke="{AXIS}" stroke-width="1"/>'
        f'<text x="{LEBAR-12}" y="{PAD_Y-2}" text-anchor="end" font-size="11" '
        f'fill="{AXIS}">% benar</text>'
        f"</svg>"
    )


def _topik_terlemah(ring) -> str:
    """Topik dengan jumlah K terbanyak di ringkasan. Data nyata, bukan tebakan."""
    agregat: dict[str, int] = {}
    for r in ring:
        t = _ambil(r, "topik", TOPIK_BAWAAN) or TOPIK_BAWAAN
        agregat[t] = agregat.get(t, 0) + (r["k"] or 0)
    if not agregat or not any(agregat.values()):
        return "tidak ada"
    return max(agregat, key=agregat.get)


def _daftar_diagnosis(mis, peta) -> str:
    """Daftar diagnosis dengan dot warna (mockup guru-laporan).

    Sumber data nyata: miskonsepsi_berulang (kode K -> titik coral,
    'salah konsep') dan peta_materi_baru (kode T -> titik amber,
    'belum diajarkan'). Tidak ada data yang dikarang: kuat (teal) hanya
    muncul kalau tidak ada miskonsepsi sama sekali.
    """
    item = []
    for m in mis:
        item.append(
            f'<li><span class="dot salah"></span>'
            f'<span><b>{html.escape(m["alasan"] or m["malrule_id"])}</b> — '
            f"salah konsep ({m['jumlah_sesi']} sesi)</span></li>"
        )
    for p in peta:
        item.append(
            f'<li><span class="dot lemah"></span>'
            f'<span><b>{html.escape(p["template_id"])}</b> — belum diajarkan '
            f'({p["kali"]}×)</span></li>'
        )
    if not item:
        return ('<li><span class="dot kuat"></span>'
                '<span>Belum ada miskonsepsi tercatat — pola kuat.</span></li>')
    return "".join(item)


def halaman_laporan(
    kon, siswa_id: int, pengguna: str = "", peran: str = "guru"
) -> bytes:
    siswa = kon.execute("SELECT * FROM siswa WHERE id = ?", (siswa_id,)).fetchone()
    if not siswa:
        return _halaman("Tidak ada", "<h1>Siswa tidak ditemukan</h1>")

    ring = basis.ringkasan(kon, siswa_id)
    total_sesi = len(ring)
    benar_sum = sum(r["benar"] or 0 for r in ring)
    soal_sum = sum(r["jumlah_soal"] or 0 for r in ring)
    persen = round(benar_sum / soal_sum * 100) if soal_sum else 0
    topik_lemah = _topik_terlemah(ring)

    tren = "".join(
        f'<tr><td><a href="/sesi/{r["sesi_id"]}">#{r["sesi_id"]}</a></td>'
        f'<td>{r["tanggal"]}</td>'
        f'<td class="tipe">{_ambil(r, "level", LEVEL_BAWAAN)}</td>'
        f'<td class="tipe">{_ambil(r, "topik", TOPIK_BAWAAN)}</td>'
        f'<td class="angka">{r["benar"] or 0}/{r["jumlah_soal"]}</td>'
        f'<td class="angka"><b>{r["k"] or 0}</b></td>'
        f'<td class="angka">{r["b"] or 0}</td><td class="angka">{r["h"] or 0}</td>'
        f'<td class="angka">{r["e"] or 0}</td><td class="angka">{r["t"] or 0}</td>'
        f'<td class="angka">{r["n"] or 0}</td></tr>'
        for r in ring
    ) or '<tr><td colspan="11" class="kosong">belum ada sesi dinilai</td></tr>'

    mis = basis.miskonsepsi_berulang(kon, siswa_id)
    daftar_mis = "".join(
        f'<tr><td>{html.escape(m["alasan"] or m["malrule_id"])}</td>'
        f'<td class="tipe">{m["template_id"]}</td>'
        f'<td class="tipe">{html.escape(m["topik"])}</td>'
        f'<td class="angka">{m["jumlah_sesi"]}</td>'
        f'<td class="tipe">{m["pertama"]} &rarr; {m["terakhir"]}</td></tr>'
        for m in mis
    ) or ('<tr><td colspan="5" class="kosong">belum ada miskonsepsi '
          "tercatat</td></tr>")

    peta = basis.peta_materi_baru(kon, siswa_id)
    daftar_peta = "".join(
        f'<tr><td>{p["template_id"]}</td>'
        f'<td class="tipe">{html.escape(p["topik"])}</td>'
        f'<td class="angka">{p["kali"]}</td>'
        f'<td class="tipe">{p["terakhir"]}</td></tr>'
        for p in peta
    ) or '<tr><td colspan="4" class="kosong">tidak ada</td></tr>'

    chart = _chart_tren(ring)
    blok_chart = chart or (
        '<p class="sub">Belum cukup data untuk menggambar tren — '
        "butuh minimal 2 sesi.</p>"
    )

    return _halaman(
        f"Laporan {siswa['nama']}",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f'<h1>Laporan — {html.escape(siswa["nama"])}</h1>'
        f'<p class="sub">Yang dipantau adalah <b>jumlah K</b>, bukan skor. '
        f"Anak dengan 9 H skor 3 lebih siap daripada anak dengan 3 K skor 9.</p>"
        f'<div class="kartu-stat">'
        f'<div class="stat"><div class="angka-besar">{total_sesi}</div>'
        f'<div class="stat-label">sesi</div></div>'
        f'<div class="stat"><div class="angka-besar">{persen}%</div>'
        f'<div class="stat-label">benar</div></div>'
        f'<div class="stat"><div class="stat-nilai-utama">'
        f"{html.escape(topik_lemah)}</div>"
        f'<div class="stat-label">topik terlemah</div></div>'
        f"</div>"
        f'<div class="layout-laporan">'
        f'<div class="kartu"><h2>Perkembangan % benar per sesi</h2>'
        f"{blok_chart}</div>"
        f'<div class="kartu"><h2>Diagnosis</h2>'
        f'<ul class="diagnosis-lis">{_daftar_diagnosis(mis, peta)}</ul></div>'
        f"</div>"
        f'<div class="tabel-wrap"><div class="kartu"><h2>Tren per sesi</h2><table>'
        f"<tr><th>Sesi</th><th>Tanggal</th><th>Level</th><th>Topik</th><th>Benar</th><th>K</th>"
        f"<th>B</th><th>H</th><th>E</th><th>T</th><th>N</th></tr>{tren}</table></div></div>"
        f'<div class="kartu"><h2>Miskonsepsi yang bertahan</h2>'
        f'<p class="sub">Dihitung per gagasan keliru, bukan per soal. Satu '
        f"miskonsepsi yang muncul di tiga soal tetap satu baris. Yang muncul "
        f"di lebih dari satu sesi berarti belum tuntas meski angkanya sudah "
        f"diganti.</p><table>"
        f"<tr><th>Miskonsepsi</th><th>Tipe soal</th><th>Topik</th><th>Jumlah sesi</th>"
        f"<th>Rentang</th></tr>{daftar_mis}</table></div>"
        f'<div class="kartu"><h2>Materi yang belum diajarkan</h2>'
        f'<p class="sub">Dari soal yang dicentang "belum pernah lihat". Ini '
        f"peta urutan belajar, bukan daftar kegagalan.</p><table>"
        f"<tr><th>Tipe soal</th><th>Topik</th><th>Berapa kali</th><th>Terakhir</th></tr>"
        f"{daftar_peta}</table></div>",
        ident=(pengguna, peran) if pengguna else None,
    )


def _kartu_akun_murid(kon, pengguna: str | None = None, peran: str = "guru") -> str:
    """Kartu akun murid di halaman akun.

    Pola persis kartu Siswa: tabel + form di bawahnya. Daftar akun diambil
    dari sandi.muat_akun() yang disaring peran == murid. Tiap akun dicek
    kecocokannya dengan tabel siswa lewat murid.siswa_dari_akun; kalau tidak
    cocok ditandai jelas "belum terhubung ke siswa" supaya guru tahu kenapa
    anak tidak bisa masuk. Guru hanya melihat & mengelola akun keluarganya;
    panggilan langsung tanpa `pengguna` (mode lokal / test) melihat semua.
    """
    import murid as _murid

    filter_siswa = None if (peran == "admin" or pengguna is None) else pengguna
    daftar_siswa = basis.daftar_siswa(kon, filter_siswa)
    akun_murid = [a for a in sandi.muat_akun() if a.get("peran") == "murid"]
    if pengguna is not None and peran != "admin":
        akun_murid = [
            a
            for a in akun_murid
            if _akun_murid_milik(kon, pengguna, peran, a["pengguna"])
        ]

    if akun_murid:
        baris = ""
        for a in akun_murid:
            nama = a["pengguna"]
            nama_esc = html.escape(nama)
            sid = _murid.siswa_dari_akun(kon, nama)
            if sid is None:
                status = '<span class="status-buruk">belum terhubung ke siswa</span>'
            else:
                status = '<span class="status-ok">terhubung</span>'
            baris += (
                f"<tr><td>{nama_esc}</td><td>{status}</td><td>"
                f'<div class="baris-aksi">'
                f'<form method="post" action="/akun" style="display:inline-flex;gap:.3rem;align-items:center">'
                f'<input type="hidden" name="aksi" value="akun_murid_hapus">'
                f'<input type="hidden" name="nama" value="{nama_esc}">'
                f'<button type="submit" class="tombol-kecil tombol-hapus">Hapus</button>'
                f"</form> "
                f'<form method="post" action="/akun" style="display:inline-flex;gap:.3rem;align-items:center;margin-left:.4rem">'
                f'<input type="hidden" name="aksi" value="akun_murid_sandi">'
                f'<input type="hidden" name="nama" value="{nama_esc}">'
                f'<input type="password" name="baru" placeholder="sandi baru" required style="width:130px;padding:.3rem .5rem;font-size:.85rem">'
                f'<button type="submit" class="tombol-kecil">Setel sandi baru</button>'
                f"</form>"
                f"</div>"
                f"</td></tr>"
            )
    else:
        baris = '<tr><td colspan="3" class="kosong">belum ada akun murid</td></tr>'

    if daftar_siswa:
        opsi = "".join(
            f'<option value="{s["id"]}">{html.escape(s["nama"])}</option>'
            for s in daftar_siswa
        )
        pilih = f'<select name="siswa_id" required><option value="">— pilih siswa —</option>{opsi}</select>'
        dis = ""
    else:
        pilih = '<select name="siswa_id" disabled><option>belum ada siswa</option></select>'
        dis = " disabled"

    tambah = (
        f'<form method="post" action="/akun" style="margin-top:.8rem">'
        f'<input type="hidden" name="aksi" value="akun_murid_tambah">'
        f'<div class="baris">'
        f"<div><label>Siswa</label>"
        f"{pilih}</div>"
        f"<div><label>Nama untuk masuk</label>"
        f'<input type="text" name="nama_akun" placeholder="mis. bima-santoso" required></div>'
        f"</div>"
        f'<div><label>Sandi baru (minimal 8 karakter)</label>'
        f'<input type="password" name="sandi" placeholder="sandi untuk murid" required minlength="8">'
        f"</div>"
        f'<p style="margin-top:.6rem"><button type="submit"{dis}>Tambah akun murid</button></p>'
        f"</form>"
    )

    return (
        f'<div class="kartu"><h2>Akun murid</h2>'
        f"<p class=\"sub\">Akun murid dipakai anak untuk masuk ke /murid. "
        f"Nama untuk masuk harus unik di seluruh aplikasi — kalau sudah "
        f"dipakai keluarga lain, pakai variasi lain (mis. tambah nama belakang).</p>"
        f"<table><tr><th>Nama</th><th>Status</th><th>Aksi</th></tr>{baris}</table>"
        f"{tambah}"
        f"</div>"
    )


def status_akun_latihan(kon, siswa_id: int) -> str:
    """Sel status akun latihan untuk tabel siswa.

    Nama login bila anaknya sudah punya akun, penanda jelas bila belum —
    supaya jelas bahwa menghapus akun latihan tidak menghapus anaknya.
    """
    import murid as _murid

    nama = _murid.akun_murid_dari_siswa(kon, siswa_id)
    if nama:
        return f'<span class="status-ok">{html.escape(nama)}</span>'
    return '<span class="status-buruk">belum ada login</span>'


def halaman_akun(
    kon,
    pesan: str = "",
    galat: str = "",
    pengguna: str | None = None,
    peran: str = "guru",
    section: str = "akun",
) -> bytes:
    """Kelola sandi dan daftar siswa — sidebar + section, tanpa JS.

    Satu halaman, tiga section via ?section=: "akun" (ganti sandi),
    "siswa" (daftar anak + form tambah), "akun-murid" (akun latihan anak).
    Nilai tak dikenal jatuh ke "akun". Admin hanya punya section "akun" —
    data keluarga lain bukan ranahnya (baca-semua-tulis-tidak).

    `pengguna`/`peran` berasal dari sesi: guru melihat & mengelola
    keluarganya saja. Panggilan langsung tanpa `pengguna` (mode lokal,
    test) melihat semuanya — perilaku lama.

    Sandi bisa diganti dari sini supaya sandi acak hasil deploy tidak jadi
    satu-satunya yang pernah ada. Siswa ber-riwayat sengaja tidak bisa
    dihapus dari sini — penjelasannya ada di kartu Catatan, section
    siswa; siswa tanpa riwayat boleh dihapus beserta akun latihannya.
    """
    admin = peran == "admin"
    if admin or section not in ("akun", "siswa", "akun-murid"):
        # Admin cuma punya satu section; nilai asing dari URL jatuh ke bawaan.
        section = "akun"

    daftar = "".join(
        f'<tr><td>{html.escape(s["nama"])}</td>'
        f'<td><form method="post" action="/akun" style="display:flex;gap:.4rem">'
        f'<input type="hidden" name="aksi" value="tingkat">'
        f'<input type="hidden" name="siswa_id" value="{s["id"]}">'
        f'<select name="tingkat" style="width:auto">'
        + "".join(
            f'<option value="{lv}"{" selected" if lv == s["tingkat"] else ""}>{lv}</option>'
            for lv in LEVEL
        )
        + '</select>'
        f'<button type="submit" style="padding:.3rem .7rem;font-size:.85rem">'
        f"Simpan</button></form></td>"
        f'<td class="angka">'
        f'{kon.execute("SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (s["id"],)).fetchone()["n"]}'
        f"</td>"
        f"<td>{status_akun_latihan(kon, s['id'])}</td>"
        f'<td><form method="post" action="/akun" style="display:inline-flex">'
        f'<input type="hidden" name="aksi" value="siswa_hapus">'
        f'<input type="hidden" name="siswa_id" value="{s["id"]}">'
        f'<button type="submit" class="tombol-kecil tombol-hapus">Hapus</button>'
        f"</form></td></tr>"
        for s in basis.daftar_siswa(kon, None if peran == "admin" else pengguna)
    )

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    if galat:
        kabar += f'<div class="pesan galat">{html.escape(galat)}</div>'

    if pengguna is not None:
        pengguna_tampil = html.escape(pengguna)
    else:
        d = sandi.muat_sandi()
        if not d:
            pengguna_tampil = "(belum disetel)"
        elif "akun" in d:
            g = next((a for a in d["akun"] if a.get("peran") in ("guru", "admin")), None)
            pengguna_tampil = html.escape(g["pengguna"]) if g else "(belum disetel)"
        else:
            pengguna_tampil = html.escape(d["pengguna"])

    kartu_sandi = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🔑</span>'
        f"<h2>Ganti sandi</h2></div>"
        f'<p class="sub">Pengguna saat ini: <b>{pengguna_tampil}</b>. Setelah diganti, '
        f"masuk lagi dengan sandi baru.</p>"
        f'<form method="post" action="/akun">'
        f'<input type="hidden" name="aksi" value="sandi">'
        f"<label>Sandi lama</label>"
        f'<input type="password" name="lama" autocomplete="current-password" required>'
        f"<label>Sandi baru (minimal 12 karakter)</label>"
        f'<input type="password" name="baru" autocomplete="new-password" required>'
        f"<label>Ulangi sandi baru</label>"
        f'<input type="password" name="ulang" autocomplete="new-password" required>'
        f'<p style="margin-top:.8rem">'
        f'<button type="submit" class="tombol-sekunder">Ganti sandi</button></p>'
        f"</form></div>"
    )
    kartu_siswa = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">📚</span>'
        f"<h2>Siswa</h2></div>"
        f'<div class="tabel-wrap"><table><tr><th>Nama</th><th>Tingkat</th>'
        f"<th>Sesi</th><th>Akun latihan</th><th>Aksi</th></tr>{daftar}</table></div>"
        f'<form method="post" action="/akun" style="margin-top:.9rem">'
        f'<input type="hidden" name="aksi" value="siswa">'
        f'<div class="baris">'
        f'<div><label>Nama siswa baru</label>'
        f'<input type="text" name="nama" placeholder="nama panggilan saja" required></div>'
        f'<div><label>Tingkat</label>'
        f'<select name="tingkat">'
        + "".join(
            f'<option value="{lv}"{" selected" if lv == LEVEL_BAWAAN else ""}>{lv}</option>'
            for lv in LEVEL
        )
        + f"</select></div></div>"
        f'<p class="sub" style="margin-top:.5rem">Pakai nama panggilan atau '
        f"inisial, bukan nama lengkap — mengurangi dampak bila basis data ini "
        f"bocor.</p>"
        f'<button type="submit" class="tombol-coral">Tambah siswa</button>'
        f"</form></div>"
    )
    kartu_anak = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🧒</span>'
        f"<h2>Tambah anak + akun latihannya</h2></div>"
        f'<p class="sub">Satu langkah untuk pengguna baru: buat siswa '
        f"sekaligus akun yang dipakai anak untuk masuk ke /murid dari HP. "
        f"Nama siswa dan nama akun otomatis dibuat sama.</p>"
        f'<form method="post" action="/akun">'
        f'<input type="hidden" name="aksi" value="anak_baru">'
        f'<div class="baris">'
        f'<div><label>Nama anak (nama panggilan)</label>'
        f'<input type="text" name="nama" placeholder="mis. Aisha" required></div>'
        f'<div><label>Tingkat</label>'
        f'<select name="tingkat">'
        + "".join(
            f'<option value="{lv}"{" selected" if lv == LEVEL_BAWAAN else ""}>{lv}</option>'
            for lv in LEVEL
        )
        + f"</select></div></div>"
        f"<label>Kata sandi anak (minimal 8 karakter)</label>"
        f'<input type="password" name="sandi_anak" autocomplete="new-password" '
        f'required minlength="8">'
        f'<p style="font-size:.9rem">'
        f'<label style="display:flex;gap:.5rem;align-items:flex-start">'
        f'<input type="checkbox" name="persetujuan_ortu" value="1" style="margin-top:.25rem">'
        f"<span>Saya orang tua/wali anak ini dan menyetujui "
        f'<a href="/kebijakan-privasi">Kebijakan Privasi</a> untuk data anak.</span>'
        f"</label></p>"
        f'<button type="submit" class="tombol-coral">Buat anak &amp; akunnya</button>'
        f"</form></div>"
    )
    kartu_catatan = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu amber">💡</span>'
        f"<h2>Catatan</h2></div>"
        f'<p class="sub">Siswa yang masih punya riwayat sesi sengaja tidak '
        f"bisa dihapus: menghapusnya ikut memusnahkan seluruh sesi, "
        f"jawaban, dan diagnosisnya — riwayat yang tidak bisa dibangun "
        f"ulang. Kalau seorang anak berhenti, biarkan saja datanya; ia "
        f"tidak mengganggu apa pun.</p>"
        f'<p class="sub">Siswa tanpa riwayat (salah ketik atau data uji) '
        f"boleh dihapus — akun latihannya ikut dihapus sekalian.</p>"
        f'<p class="sub">Cadangan basis data ditarik otomatis ke Mac tiap '
        f"malam pukul 22:00.</p></div>"
    )

    if section == "siswa":
        isi_section = kartu_siswa + kartu_anak + kartu_catatan
    elif section == "akun-murid":
        isi_section = _kartu_akun_murid(kon, pengguna, peran)
    else:
        isi_section = kartu_sandi

    item = [
        ("akun", "Akun saya"),
        ("siswa", "Siswa"),
        ("akun-murid", "Akun latihan"),
    ]
    if admin:
        item = item[:1]
    nav = "".join(
        f'<a href="/akun?section={sid}"'
        + (' class="aktif"' if sid == section else "")
        + f">{label}</a>"
        for sid, label in item
    )

    return _halaman(
        "Akun",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f"<h1>Akun &amp; pengaturan</h1>"
        f"{kabar}"
        f'<div class="layout-samping">'
        f'<nav class="nav-samping">{nav}</nav>'
        f"<div>{isi_section}</div>"
        f"</div>",
        ident=(pengguna or "guru", peran),
    )


def _akun_murid_milik(kon, pengguna: str, peran: str, nama: str) -> bool:
    """Apakah akun murid `nama` boleh dikelola oleh pengguna ini?

    Admin boleh semua. Guru hanya akun murid yang terikat ke siswa
    miliknya — lewat siswa_id eksplisit, atau (akun warisan) lewat nama
    siswa ber-pemilik dirinya.
    """
    if peran == "admin":
        return True
    a = sandi.cari_akun(nama)
    if not a or a.get("peran") != "murid":
        return False
    if a.get("siswa_id") is not None:
        return basis.siswa_milik(kon, int(a["siswa_id"]), pengguna)
    baris = kon.execute(
        "SELECT 1 FROM siswa WHERE nama = ? COLLATE NOCASE AND pemilik = ?",
        (nama, pengguna),
    ).fetchone()
    return baris is not None


def proses_akun(
    kon, data: dict, pengguna_kini: str, peran: str = "guru"
) -> tuple[str, str]:
    """Jalankan aksi halaman akun. Mengembalikan (pesan, galat).

    Sandi lama SELALU diverifikasi ulang, walaupun pengguna sudah lolos
    palang untuk membuka halaman ini. Peramban menyimpan kredensial Basic
    dan mengirimkannya otomatis, jadi tanpa pemeriksaan ini siapa pun yang
    menemukan laptop dalam keadaan terbuka bisa mengganti sandi tanpa tahu
    yang lama.

    Multi-keluarga: siswa yang dibuat tercatat ber-pemilik pengguna_kini,
    dan aksi ber-id (tingkat, akun murid) hanya menyentuh milik sendiri —
    admin bebas, dengan `peran="admin"`.
    """
    aksi = data.get("aksi", "")

    if aksi == "sandi":
        lama = data.get("lama", "")
        baru = data.get("baru", "")
        ulang = data.get("ulang", "")

        if not sandi.periksa(pengguna_kini, lama):
            return "", "Sandi lama salah."
        if baru != ulang:
            return "", "Sandi baru dan ulangannya tidak sama."
        if len(baru) < 12:
            return "", "Sandi baru minimal 12 karakter."
        if baru == lama:
            return "", "Sandi baru sama dengan yang lama."

        sandi.simpan_sandi(baru, pengguna_kini)
        return (
            "Sandi diganti. Masuk lagi dengan sandi baru.",
            "",
        )

    if aksi == "siswa":
        nama = data.get("nama", "").strip()
        tingkat = data.get("tingkat", LEVEL_BAWAAN).strip() or LEVEL_BAWAAN

        if not nama:
            return "", "Nama siswa tidak boleh kosong."
        if len(nama) > 40:
            return "", "Nama terlalu panjang."
        # Level divalidasi terhadap daftar tertutup. Tanpa ini, salah ketik
        # ("p4", "kelas 4") diam-diam jatuh ke profil P3 lewat `profil()`,
        # dan guru mengira anaknya dapat soal P4 padahal tidak.
        if not level_valid(tingkat):
            return "", f"Tingkat harus salah satu dari: {', '.join(LEVEL)}."
        # Duplikat diperiksa PER KELUARGA: dua keluarga boleh sama-sama
        # punya "Bima", tapi satu keluarga tidak.
        sudah = kon.execute(
            "SELECT 1 FROM siswa WHERE lower(nama) = lower(?) AND pemilik = ?",
            (nama, pengguna_kini),
        ).fetchone()
        if sudah:
            return "", f"Siswa bernama {nama} sudah ada di keluargamu."

        basis.tambah_siswa(kon, nama, tingkat, pemilik=pengguna_kini)
        return f"Siswa {nama} ditambahkan ({tingkat}).", ""

    if aksi == "anak_baru":
        """Onboarding publik: siswa + akun murid sekaligus (atomic).

        Validasi SEMUA dulu sebelum menulis apa pun — siswa yang dibuat
        lalu akunnya gagal meninggalkan siswa tanpa akun ("anak yatim")
        yang hanya bisa dirapikan manual lewat halaman akun.
        """
        nama = data.get("nama", "").strip()
        tingkat = data.get("tingkat", LEVEL_BAWAAN).strip() or LEVEL_BAWAAN
        sandi_anak = data.get("sandi_anak", "")

        if not nama:
            return "", "Nama anak tidak boleh kosong."
        if len(nama) > 40:
            return "", "Nama terlalu panjang."
        if not level_valid(tingkat):
            return "", f"Tingkat harus salah satu dari: {', '.join(LEVEL)}."
        if len(sandi_anak) < 8:
            return "", "Kata sandi anak minimal 8 karakter."
        if kon.execute(
            "SELECT 1 FROM siswa WHERE lower(nama) = lower(?) AND pemilik = ?",
            (nama, pengguna_kini),
        ).fetchone():
            return "", f"Siswa bernama {nama} sudah ada di keluargamu."
        if sandi.cari_akun(nama) is not None:
            return "", f"Nama {nama} sudah dipakai akun lain. Pakai nama lain."

        siswa_id = basis.tambah_siswa(kon, nama, tingkat, pemilik=pengguna_kini)
        try:
            sandi.tambah_akun(nama, sandi_anak, "murid", siswa_id=siswa_id)
        except ValueError as e:
            # Pembuatan akun meledak di tengah: batalkan siswa yang baru
            # dibuat supaya tidak ada anak yatim tanpa akun.
            kon.execute(
                "DELETE FROM siswa WHERE id = ? AND NOT EXISTS "
                "(SELECT 1 FROM sesi WHERE sesi.siswa_id = siswa.id)",
                (siswa_id,),
            )
            return "", str(e)
        catatan = " (persetujuan orang tua dicatat)" if data.get("persetujuan_ortu") else ""
        return (
            f"Anak {nama} ditambahkan ({tingkat}) beserta akun latihannya{catatan}. "
            f"Anak masuk lewat /murid dengan nama {nama}.",
            "",
        )

    if aksi == "tingkat":
        # Menaikkan level anak. Sesi LAMA tidak ikut berubah — levelnya
        # tersimpan di baris sesi masing-masing, jadi riwayat tetap terbaca
        # apa adanya. Yang berubah hanya sesi yang dibuat setelah ini.
        try:
            siswa_id = int(data.get("siswa_id", ""))
        except ValueError:
            return "", "Siswa tidak dikenal."
        tingkat = data.get("tingkat", "").strip()
        if not level_valid(tingkat):
            return "", f"Tingkat harus salah satu dari: {', '.join(LEVEL)}."
        baris = kon.execute(
            "SELECT nama FROM siswa WHERE id = ?", (siswa_id,)
        ).fetchone()
        if not baris or (
            peran != "admin"
            and not basis.siswa_milik(kon, siswa_id, pengguna_kini)
        ):
            return "", "Siswa tidak dikenal."
        kon.execute(
            "UPDATE siswa SET tingkat = ? WHERE id = ?", (tingkat, siswa_id)
        )
        return (
            f"{baris['nama']} sekarang {tingkat}. Sesi lama tetap pada "
            f"levelnya masing-masing; yang berubah hanya sesi berikutnya.",
            "",
        )

    if aksi == "siswa_hapus":
        # Pengaman riwayat: menghapus siswa = CASCADE menghapus seluruh
        # sesi, jawaban, dan diagnosisnya. Yang sudah berriwayat sengaja
        # tak bisa dihapus; yang kosong (salah ketik / data uji) boleh,
        # dan akun latihannya ikut dihapus supaya tak ada anak yatim.
        try:
            siswa_id = int(data.get("siswa_id", ""))
        except ValueError:
            return "", "Siswa tidak dikenal."
        baris = kon.execute(
            "SELECT nama FROM siswa WHERE id = ?", (siswa_id,)
        ).fetchone()
        if not baris or (
            peran != "admin"
            and not basis.siswa_milik(kon, siswa_id, pengguna_kini)
        ):
            return "", "Siswa tidak dikenal."
        nama = baris["nama"]
        n_sesi = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (siswa_id,)
        ).fetchone()["n"]
        if n_sesi:
            return (
                "",
                f"{nama} masih punya {n_sesi} sesi. Siswa ber-riwayat "
                f"sengaja tidak bisa dihapus — sesi, jawaban, dan "
                f"diagnosisnya tidak bisa dibangun ulang.",
            )
        import murid as _murid

        login = _murid.akun_murid_dari_siswa(kon, siswa_id)
        if login:
            sandi.hapus_akun(login)
        kon.execute("DELETE FROM siswa WHERE id = ?", (siswa_id,))
        return f"Siswa {nama} dihapus beserta akun latihannya.", ""

    if aksi == "akun_murid_tambah":
        nama_siswa = (data.get("nama") or "").strip()
        nama_akun = (data.get("nama_akun") or "").strip()
        sandi_baru = data.get("sandi", "")
        # kalau form lama masih mengirim "baru", dukung juga
        if not sandi_baru:
            sandi_baru = data.get("baru", "")

        siswa_id = None
        if data.get("siswa_id"):
            # Bentuk form baru: pilih siswa dari dropdown milik sendiri,
            # lalu tentukan nama login-nya (boleh berbeda dari nama siswa).
            try:
                siswa_id = int(data["siswa_id"])
            except ValueError:
                return "", "Siswa tidak dikenal."
            if peran != "admin" and not basis.siswa_milik(
                kon, siswa_id, pengguna_kini
            ):
                return "", "Siswa tidak dikenal."
            baris = kon.execute(
                "SELECT nama FROM siswa WHERE id = ?", (siswa_id,)
            ).fetchone()
            nama_siswa = baris["nama"]
        elif nama_siswa:
            # Bentuk lama: nama akun = nama siswa. Pencarian dibatasi ke
            # keluarga sendiri supaya nama dobel antar keluarga tak ambigu.
            if peran == "admin":
                baris = kon.execute(
                    "SELECT id, nama FROM siswa WHERE nama = ? COLLATE NOCASE",
                    (nama_siswa,),
                ).fetchone()
            else:
                baris = kon.execute(
                    "SELECT id, nama FROM siswa "
                    "WHERE nama = ? COLLATE NOCASE AND pemilik = ?",
                    (nama_siswa, pengguna_kini),
                ).fetchone()
            if not baris:
                return "", f"Siswa bernama {nama_siswa} tidak ditemukan."
            siswa_id = int(baris["id"])
        else:
            return "", "Pilih siswanya dulu."

        if not nama_akun:
            nama_akun = nama_siswa
        if len(sandi_baru) < 8:
            return "", "Sandi murid minimal 8 karakter."
        try:
            sandi.tambah_akun(nama_akun, sandi_baru, "murid", siswa_id=siswa_id)
        except ValueError as e:
            return "", str(e)
        return f"Akun murid {nama_akun} ditambahkan.", ""

    if aksi == "akun_murid_hapus":
        nama = data.get("nama", "").strip()
        if not nama:
            return "", "Nama tidak boleh kosong."
        if not _akun_murid_milik(kon, pengguna_kini, peran, nama):
            return "", f"Akun {nama} tidak ditemukan."
        ok = sandi.hapus_akun(nama)
        if not ok:
            return "", f"Akun {nama} tidak ditemukan."
        return f"Akun murid {nama} dihapus.", ""

    if aksi == "akun_murid_sandi":
        nama = data.get("nama", "").strip()
        baru = data.get("baru", "")
        if not nama:
            return "", "Nama tidak boleh kosong."
        if len(baru) < 8:
            return "", "Sandi murid minimal 8 karakter."
        if not _akun_murid_milik(kon, pengguna_kini, peran, nama):
            return "", f"Akun {nama} tidak ditemukan."
        ok = sandi.setel_sandi_murid(nama, baru)
        if not ok:
            return "", f"Akun {nama} tidak ditemukan."
        return f"Sandi {nama} diperbarui.", ""

    return "", "Aksi tidak dikenal."


def halaman_admin(
    kon, pesan: str = "", galat: str = "", pengguna: str = ""
) -> bytes:
    """Dashboard admin: ringkasan, daftar keluarga, buat akun orang tua.

    Hanya peran admin yang sampai sini — penjaganya ada di router, dan
    sejak login admin langsung diarahkan ke sini. Kebijakan admin
    baca-semua-tulis-tidak: satu-satunya tulisan di halaman ini adalah
    membuat akun orang tua (domain admin sendiri); data murid hanya bisa
    DIBACA — nama anak jadi tautan ke laporannya, aksi tulis data murid
    ditolak 404 di router.
    """
    akun = sandi.muat_akun()
    n_keluarga = sum(1 for a in akun if a.get("peran", "guru") == "guru")
    total_siswa = kon.execute("SELECT COUNT(*) AS n FROM siswa").fetchone()["n"]
    total_sesi = kon.execute("SELECT COUNT(*) AS n FROM sesi").fetchone()["n"]
    ringkas = (
        '<div class="kartu-stat">'
        f'<div class="stat"><div class="angka-besar">{n_keluarga}</div>'
        f'<div class="stat-label">keluarga</div></div>'
        f'<div class="stat"><div class="angka-besar">{total_siswa}</div>'
        f'<div class="stat-label">siswa</div></div>'
        f'<div class="stat"><div class="angka-besar">{total_sesi}</div>'
        f'<div class="stat-label">sesi</div></div>'
        "</div>"
    )

    keluarga = []
    for a in akun:
        if a.get("peran", "guru") not in ("guru", "admin"):
            continue
        nama = a["pengguna"]
        anak = basis.daftar_siswa(kon, nama)
        daftar_anak = (
            ", ".join(
                f'<a href="/laporan/{s["id"]}">{html.escape(s["nama"])}</a>'
                for s in anak
            )
            or '<span class="kosong">belum ada anak</span>'
        )
        terakhir = kon.execute(
            """SELECT MAX(s.tanggal) AS t FROM sesi s
               JOIN siswa w ON w.id = s.siswa_id WHERE w.pemilik = ?""",
            (nama,),
        ).fetchone()["t"] or "—"
        peran_label = "Pengelola" if a.get("peran") == "admin" else "Orang Tua"
        keluarga.append(
            f"<tr><td>{html.escape(nama)}</td>"
            f"<td>{peran_label}</td>"
            f'<td class="angka">{len(anak)}</td>'
            f"<td>{daftar_anak}</td>"
            f"<td>{terakhir}</td></tr>"
        )
    tabel = (
        "<table><tr><th>Akun</th><th>Peran</th><th>Jumlah anak</th>"
        f"<th>Nama anak</th><th>Sesi terakhir</th></tr>{''.join(keluarga)}</table>"
    )

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    if galat:
        kabar += f'<div class="pesan galat">{html.escape(galat)}</div>'

    return _halaman(
        "Panel Pengelola",
        f"<h1>Panel Pengelola</h1>"
        f'{kabar}'
        f"{ringkas}"
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🏡</span>'
        f"<h2>Keluarga</h2></div>"
        f"{tabel}"
        f"</div>"
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">➕</span>'
        f"<h2>Buat akun orang tua</h2></div>"
        f'<form method="post" action="/admin">'
        f'<input type="hidden" name="aksi" value="guru_baru">'
        f'<div class="baris">'
        f'<div><label>Nama akun</label>'
        f'<input type="text" name="pengguna" autocomplete="off" required></div>'
        f"<div><label>Kata sandi (minimal 12 karakter)</label>"
        f'<input type="password" name="sandi" autocomplete="new-password" '
        f'required minlength="12"></div>'
        f"</div>"
        f'<p style="margin-top:.8rem">'
        f'<button type="submit" class="tombol-coral">Buat akun</button></p>'
        f"</form>"
        f'<p class="sub">Orang tua juga bisa mendaftar sendiri di '
        f'<a href="/daftar">/daftar</a> — setelah isolasi, pendaftar baru '
        f"tidak melihat data keluarga mana pun.</p>"
        f"</div>",
        ident=(pengguna, "admin") if pengguna else None,
    )


def buat_sesi_seed_baru(
    kon,
    siswa_id: int,
    level: str | None = None,
    topik: str | None = None,
    mode: str = "diagnostik",
    timer_mode: str = "tanpa",
    durasi_menit: int = 15,
    timer_auto: int = 0,
) -> int:
    """Sesi baru dengan seed yang belum pernah dipakai siswa ini.

    Mengulang seed berarti mengulang soal yang persis sama — anak bisa
    mengingat jawabannya, dan diagnosisnya berubah jadi menilai hafalan,
    bukan pemahaman.

    Level diambil dari tingkat siswa kalau tidak disebut. Inilah yang membuat
    kolom `siswa.tingkat` akhirnya berarti: sebelum ini kolom itu tersimpan
    rapi dan tidak pernah dibaca siapa pun, sehingga mengubahnya jadi P4
    tidak mengubah satu soal pun.

    Topik TIDAK fallback diam-diam: id yang tidak dikenal dilempar sebagai
    KeyError oleh ambil() — salah ketik id topik adalah bug pemanggil, bukan
    data produksi yang perlu dimaafkan (kontraknya beda dari level).

    `mode` dan `timer_*` diteruskan ke basis.buat_sesi; nilai asing ditolak
    di sana (ValueError) — pemanggil wajib validasi sebelum menyentuh DB.
    """
    if level is None:
        baris = kon.execute(
            "SELECT tingkat FROM siswa WHERE id = ?", (siswa_id,)
        ).fetchone()
        level = baris["tingkat"] if baris else LEVEL_BAWAAN
    if topik is None:
        topik = TOPIK_BAWAAN
    else:
        ambil(topik)  # validasi awal: gagal cepat sebelum menyentuh basis data

    dipakai = {
        r["seed"]
        for r in kon.execute(
            "SELECT seed FROM sesi WHERE siswa_id = ?", (siswa_id,)
        ).fetchall()
    }
    for _ in range(500):
        seed = random.randint(1, 9_999_999)
        if seed not in dipakai:
            return basis.buat_sesi(
                kon, siswa_id, seed, level=level, topik=topik, mode=mode,
                timer_mode=timer_mode, durasi_menit=durasi_menit,
                timer_auto=timer_auto,
            )
    raise RuntimeError("gagal menemukan seed baru")


def halaman_lembar(kon, sesi_id: int, untuk_guru: bool = False) -> bytes | None:
    """Lembar siap cetak, dibangkitkan ulang dari seed.

    Tidak membaca berkas dari cakram: seed tersimpan di basis data, dan
    membangkitkan ulang menjamin lembar yang tampil SELALU cocok dengan soal
    yang tercatat di sesi ini. Berkas di cakram bisa terhapus, tertimpa, atau
    tertinggal versi lama; seed tidak bisa.
    """
    info = kon.execute(
        """SELECT s.seed, s.tanggal, s.topik, w.nama
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return None

    soal = [_soal_dari_baris(b) for b in basis.isi_sesi(kon, sesi_id)]
    # Judul dari paket topik sesi ini — bukan selalu paket bawaan. Sesi lama
    # dengan nilai kolom aneh jatuh ke bawaan lewat dari_sesi(), sesuai
    # kontrak data produksi.
    paket = dari_sesi(info["topik"])
    # Lembar yang sama, dua tampilan (Fase 3): di web ia dibaca dari layar,
    # jadi dipakai gaya layar — kartu sentuh, tanpa satuan mm. Versi cetak
    # tetap keluar lewat tombol cetak browser (@media print di gaya layar
    # menurunkan dirinya ke perilaku kertas).
    from gaya_layar import GAYA_LAYAR

    if untuk_guru:
        isi = cetak.lembar_penilaian(
            soal, info["nama"], info["tanggal"], info["seed"],
            gaya=GAYA_LAYAR, topik_paket=paket,
        )
    else:
        isi = cetak.lembar_soal(
            soal, info["nama"], info["tanggal"], gaya=GAYA_LAYAR,
            topik_paket=paket,
        )
    return isi.encode()


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
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        if host not in ("localhost", "127.0.0.1", ""):
            c["osn_sesi"]["secure"] = True
        c["osn_sesi"]["max-age"] = str(sesi.TTL_DETIK)
        return c.output(header="").strip()

    def _kredensial(self):
        return sandi.dari_header(self.headers.get("Authorization"))

    def _sesi_atau_basic(self, peran_wajib: str | None = None):
        """Kembalikan (pengguna, peran) bila lolos via cookie ATAU Basic.

        Helper kecil untuk rute murid — dipakai di _rute_murid_get dan
        POST /murid/kerjakan/. Nilai peran_wajib bila perlu (mis. "murid").
        """
        tok = self._ambil_token()
        if tok:
            got = sesi.ambil(tok)
            if got and (peran_wajib is None or got[1] == peran_wajib):
                return got
        kred = self._kredensial()
        if not kred:
            return None
        # kred adalah (pengguna, sandi) dari header Basic
        peran = sandi.peran_dari(*kred)
        if peran and (peran_wajib is None or peran == peran_wajib):
            return (kred[0], peran)
        return None

    def _identitas(self) -> tuple[str, str] | None:
        """(pengguna, peran) pengunjung ini, atau None bila anonim.

        Mode lokal (tanpa berkas sandi) = satu akun bawaan "guru": semua
        halaman terbuka seperti semula, dan data yang dibuat tercatat atas
        nama "guru" pula — konsisten dengan pembuatnya.
        """
        if not sandi.wajib_sandi():
            return ("guru", "guru")
        tok = self._ambil_token()
        if tok:
            got = sesi.ambil(tok)
            if got:
                return got
        kred = self._kredensial()
        if not kred:
            return None
        peran = sandi.peran_dari(*kred)
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
        return basis.sesi_milik(kon, sesi_id, ident[0])

    def _bisa_lihat_siswa(self, kon, siswa_id: int) -> bool:
        ident = self._identitas()
        if not ident:
            return False
        if ident[1] == "admin":
            return True
        return basis.siswa_milik(kon, siswa_id, ident[0])

    def _bisa_lihat_lampiran(self, kon, lampiran_id: int) -> bool:
        lamp = basis.ambil_lampiran(kon, lampiran_id)
        if not lamp:
            return False
        return self._bisa_lihat_sesi(kon, int(lamp["sesi_id"]))

    def _kirim_berkas_lampiran(self, kon, lampiran_id: int) -> None:
        """Kirim isi berkas foto lampiran (hanya guru, hanya milik sesi)."""
        lamp = basis.ambil_lampiran(kon, lampiran_id)
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
            return self._kirim(self._halaman_masuk(galat=galat))
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
                    with basis.buka() as kon:
                        return self._kirim(
                            halaman_utama(
                                kon, pesan=pesan, pemilik=ident[0],
                                peran=ident[1],
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
        if jalur == "/murid" or jalur.startswith("/murid/"):
            try:
                with basis.buka() as kon:
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
                with basis.buka() as kon:
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
            with basis.buka() as kon:
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
                if jalur.startswith("/sesi/"):
                    sesi_id = int(jalur.split("/")[2])
                    if not self._bisa_lihat_sesi(kon, sesi_id):
                        return self._kirim(
                            _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                        )
                    ident = self._identitas()
                    return self._kirim(
                        halaman_sesi(
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
        sendiri. Kredensial salah/peran salah -> 401, bukan 404 — supaya
        anak yang salah ketik sandi tidak mengira situsnya rusak.
        """
        import murid

        kredensial = self._sesi_atau_basic(peran_wajib="murid")
        if not kredensial:
            return self._kirim(
                _halaman(
                    "Perlu masuk",
                    "<h1>Halaman murid</h1>"
                    "<p>Masuk dengan akun muridmu (nama &amp; sandi dari gurumu).</p>",
                ),
                401,
            )
        siswa_id = murid.siswa_dari_akun(kon, kredensial[0])
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
            return self._kirim(murid.halaman_daftar_sesi(kon, siswa_id, kredensial[0]))
        bagian = jalur.split("/")
        # /murid/selesai/<id> — konfirmasi setelah semua soal terisi
        if len(bagian) >= 3 and bagian[2] == "selesai":
            try:
                sesi_id = int(bagian[3])
            except (ValueError, IndexError):
                sesi_id = -1
            isi = murid.halaman_selesai(kon, siswa_id, sesi_id)
            if isi is None:
                return self._kirim(
                    _halaman("404", "<h1>Sesi tidak ada</h1>"), 404
                )
            return self._kirim(isi)
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
            isi = murid.halaman_kerja(kon, siswa_id, int(bagian[3]), tersimpan)
            if isi is None:
                return self._kirim(
                    _halaman("404", "<h1>Sesi tidak ada</h1>"), 404
                )
            return self._kirim(isi)
        self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)

    def _halaman_masuk(self, galat: str = "") -> bytes:
        import ikon

        kabar = (
            f'<div class="pesan galat">{html.escape(galat)}</div>' if galat else ""
        )
        return _halaman(
            T.NAMA_PRODUK,
            f'<div class="layout-masuk">'
            f'<div class="masuk-kiri">'
            f'<img src="{ikon.OWL}" alt="Burung hantu lulusan" width="200" height="200">'
            f"<h1>{T.NAMA_PRODUK}</h1>"
            f"<p>{T.TAGLINE}</p>"
            f"</div>"
            f'<div class="masuk-kanan">'
            f'<div class="kartu kartu-masuk">'
            f'<img src="{ikon.GEMBOK}" alt="" class="ikon-gembok" width="44" height="44">'
            f"{kabar}"
            f'<form method="post" action="/masuk">'
            f'<label>Nama</label>'
            f'<input type="text" name="nama" autocomplete="username" required>'
            f'<label>Sandi</label>'
            f'<input type="password" name="sandi" autocomplete="current-password" required>'
            f'<button type="submit">Masuk</button>'
            f"</form>"
            f'<p class="sub" style="text-align:center;margin-top:.8rem">'
            f"Pakai kata sandi yang diberikan</p>"
            f"</div></div></div>",
        )

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
        if sesi.sedang_diblokir(nama, ip):
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
                sandi.tambah_akun(nama, pw, "guru")
            except ValueError:
                galat = f"Nama {nama} sudah dipakai. Pakai nama lain, atau masuk bila memang akunmu."
        if galat:
            return self._kirim(halaman_daftar(galat, galat=True, nama=nama))

        token = sesi.buat(nama, "guru")
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
            return self._kirim(self._halaman_masuk("Nama dan sandi wajib diisi."))
        if sesi.sedang_diblokir(nama, ip):
            return self._kirim(self._halaman_masuk("Terlalu banyak percobaan. Coba lagi 15 menit lagi."), 429)
        peran = sandi.peran_dari(nama, pw)
        if not peran:
            sesi.catat_gagal(nama, ip)
            return self._kirim(self._halaman_masuk("Nama atau sandi belum cocok. Coba lagi, atau minta gurumu."))
        sesi.catat_berhasil(nama, ip)
        token = sesi.buat(nama, peran)
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
            import murid

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
            with basis.buka() as kon:
                siswa_id = murid.siswa_dari_akun(kon, kredensial[0])
                hasil = (
                    murid.simpan_jawaban_murid(kon, siswa_id, sesi_id, data)
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
                    # (WHERE IS NULL) — lihat basis.tandai_mulai.
                    basis.tandai_mulai(kon, sesi_id)
                    diagnosa_murid(kon, sesi_id)
                    # Semua soal sudah terisi → arahkan ke halaman Selesai,
                    # bukan kembali ke lembar yang sama. Anak yang masih
                    # setengah jalan tetap kembali ke lembar + banner
                    # tersimpan supaya bisa lanjut mengerjakan.
                    if siswa_id is not None:
                        selesai = murid.semua_terisi(kon, siswa_id, sesi_id)
                        if selesai:
                            basis.tandai_selesai(kon, sesi_id)
            if hasil is None:
                return self._kirim(
                    _halaman("403", "<h1>Bukan sesimu</h1>"), 403
                )
            if selesai:
                self.send_response(303)
                self.send_header("Location", f"/murid/selesai/{sesi_id}")
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
                sesi.hapus(tok)
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
            with basis.buka() as kon:
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
                        sandi.tambah_akun(nama, pw, "guru")
                        pesan = (
                            f"Akun orang tua {nama} dibuat. Orang tua bisa "
                            f"masuk lewat /masuk."
                        )
                    except ValueError as e:
                        galat = str(e)
            else:
                galat = "Aksi tidak dikenal."
            ident = self._identitas()
            with basis.buka() as kon:
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
            with basis.buka() as kon:
                if not self._bisa_lihat_sesi(kon, sesi_id):
                    return self._kirim(
                        _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                    )
                _, _, catatan = llm.bungkus_sesi(kon, sesi_id, _soal_dari_baris)
                ident = self._identitas()
                return self._kirim(
                    halaman_sesi(
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
            with basis.buka() as kon:
                if not self._bisa_lihat_siswa(kon, siswa_id):
                    return self._kirim(
                        _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                    )
                siswa = kon.execute(
                    "SELECT tingkat FROM siswa WHERE id = ?", (siswa_id,)
                ).fetchone()
                if not siswa:
                    return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
                level = siswa["tingkat"] if siswa["tingkat"] in LEVEL else LEVEL_BAWAAN
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
                    if timer_mode not in ("sesi", "soal"):
                        pesan = (
                            f"<h1>Timer tidak dikenal</h1>"
                            f"<p><code>{html.escape(timer_mode)}</code> tidak terdaftar. "
                            f"Yang tersedia: sesi (per sesi, tampil jalan), "
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
            # Alihkan ke halaman sesinya, bukan menampilkan ulang halaman
            # utama: setelah membuat sesi yang dibutuhkan guru adalah
            # lembarnya, dan pengalihan mencegah sesi ganda kalau halaman
            # di-muat ulang.
            self.send_response(303)
            self.send_header("Location", f"/sesi/{sesi_id}")
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
                with basis.buka() as kon:
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
            with basis.buka() as kon:
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
            with basis.buka() as kon:
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
                with basis.buka() as kon:
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
            with basis.buka() as kon:
                dihapus = basis.hapus_sesi(kon, sesi_id)
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
        with basis.buka() as kon:
            if not self._bisa_lihat_sesi(kon, sesi_id):
                return self._kirim(
                    _halaman("404", "<h1>Halaman tidak ada</h1>"), 404
                )
            pesan = simpan_sesi(kon, sesi_id, data)
            ident = self._identitas()
            self._kirim(
                halaman_sesi(
                    kon, sesi_id, pesan,
                    peran=ident[1] if ident else "guru",
                    pengguna=ident[0] if ident else "",
                )
            )

    def log_message(self, *a) -> None:  # senyapkan log akses
        pass
