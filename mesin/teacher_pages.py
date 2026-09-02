"""Halaman-halaman guru: dashboard, sesi, konfirmasi hapus, lembar.

Dipecah dari web.py (refactor 31 Aug 2026) — fungsi pindah utuh, perilaku
identik. Router HTTP tetap di web.py; frame halaman (_halaman/_topbar)
tinggal di sini dan dipakai reports.py serta account_pages.py.
Aturan lama tetap berlaku: modul ini tidak boleh mengimpor students di atas
file (impor terlambat di dalam fungsi, lihat pemakaian aslinya).
"""

from __future__ import annotations

import html
import json
import random
from dataclasses import replace
from datetime import datetime

import database
import design_tokens as T
import worksheets
from diagnosis import diagnosa
from generator import LEVEL_BAWAAN
from templates import LEVEL, REGISTRI, Soal
from topics import TOPIK_BAWAAN, ambil, daftar_topik, dari_sesi
from teacher_style import GAYA_GURU as GAYA, SKRIP_MATA_SANDI, SKRIP_CEGAH_KIRIM_GANDA
from style_stitch import GAYA_STITCH


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

def _halaman(
    judul: str, isi: str, ident: tuple[str, str] | None = None,
    stitch: bool = False,
) -> bytes:
    """Bingkai semua halaman pengelola. `ident=(pengguna, peran)` menampilkan
    topbar dengan menu pengguna di atas isi — satu pintu agar konsisten.

    stitch=True: pakai GAYA_STITCH + body.st + <link> font CDN (S11-S17).
    """
    if stitch:
        from style_stitch import gaya_stitch, CSS_SESI
        batang = _topbar_stitch(*ident) if ident else ""
        return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
<style>{GAYA}{gaya_stitch()}{CSS_SESI}</style></head>
<body class="st"><div class="bungkus-st">{batang}<div class="sesi-badan-st">{isi}</div></div><script>{SKRIP_MATA_SANDI}</script><script>{SKRIP_CEGAH_KIRIM_GANDA}</script></body></html>""".encode()
    batang = _topbar(*ident) if ident else ""
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title><style>{GAYA}</style></head>
<body><div class="bungkus">{batang}{isi}</div><script>{SKRIP_MATA_SANDI}</script><script>{SKRIP_CEGAH_KIRIM_GANDA}</script></body></html>""".encode()

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
    daftar = [
        topik_id
        for topik_id in daftar_topik()
        if level_efektif in ambil(topik_id).komposisi and topik_id != "campuran"
    ]
    if "campuran" in daftar_topik():
        daftar = ["campuran"] + daftar
    return daftar

def _badge_review_status(baris) -> str:
    direview = _ambil(baris, "direview", None)
    terisi = _ambil(baris, "terisi", 0)
    n = _ambil(baris, "n", 0)
    if direview is not None:
        return '<span class="badge-direview sudah" style="background:#d4edda;color:#155724;padding:0.2rem 0.45rem;border-radius:4px;font-size:0.78rem;font-weight:bold;">✓ Sudah Direview</span>'
    elif terisi == n and n > 0:
        return '<span class="badge-direview perlu" style="background:#fff3cd;color:#856404;padding:0.2rem 0.45rem;border-radius:4px;font-size:0.78rem;font-weight:bold;">⏳ Belum Direview</span>'
    elif terisi > 0:
        return '<span class="badge-direview proses" style="background:#e2e8f0;color:#2d3748;padding:0.2rem 0.45rem;border-radius:4px;font-size:0.78rem;">✏️ Sedang Dikerjakan</span>'
    else:
        return '<span class="badge-direview belum" style="background:#edf2f7;color:#718096;padding:0.2rem 0.45rem;border-radius:4px;font-size:0.78rem;">Belum Dikerjakan</span>'

def _badge_mode(baris) -> str:
    """Badge 'Latihan Cepat' untuk sesi drill; kosong untuk diagnostik.

    CSS guru memuat kata "Latihan Cepat" di komentar, jadi badge-nya
    harus marker kelas, bukan teks yang dicari mentah.
    """
    if _ambil(baris, "mode", "diagnostik") == "drill":
        return '<span class="badge-mode">Latihan Cepat</span>'
    return ""

def _fmt_durasi(mulai, selesai, dicatat_awal=None, dicatat_akhir=None) -> str:
    """Durasi pengerjaan mm:ss dari kolom mulai/selesai sesi.

    Utama: selesai − mulai, dan hanya bila keduanya tercatat. Kalau salah
    satu tidak ada (sesi kertas yang dilengkapi lewat foto) atau durasinya
    nol — versi lama mencatat mulai saat simpan pertama, jadi sesi sekali
    simpan tercatat 0 detik — jatuh ke rentang waktu tercatatnya jawaban
    (dicatat_awal → dicatat_akhir): perkiraan yang tetap jujur karena tiap
    simpan mencatat waktunya. Tanpa jejak waktu sama sekali, tampil '—';
    mengarang durasi lebih buruk daripada menampilkan kosong.
    """
    BENTUK = "%Y-%m-%d %H:%M:%S"
    for awal, akhir in ((mulai, selesai), (dicatat_awal, dicatat_akhir)):
        if not awal or not akhir:
            continue
        try:
            detik = int(
                (
                    datetime.strptime(str(akhir), BENTUK)
                    - datetime.strptime(str(awal), BENTUK)
                ).total_seconds()
            )
        except ValueError:
            continue
        if detik > 0:
            return f"{detik // 60}:{detik % 60:02d}"
    return "&mdash;"

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

def _badge_mode_stitch(baris) -> str:
    """Badge 'Latihan Cepat' untuk sesi drill di dashboard Stitch."""
    if _ambil(baris, "mode", "diagnostik") == "drill":
        return '<span class="st-badge latihan">Latihan Cepat</span>'
    return ""


def _topbar_stitch(pengguna: str, peran: str) -> str:
    """Topbar versi Stitch — pakai .st-topbar supaya CSS lama tidak dicampur.

    Menu pengguna tetap CSS-only (<details>), satu pintu keluar, tautan
    menyesuaikan peran. Logo ikon owl = Material Symbols 'school'.
    """
    if peran == "admin":
        brand, item = "/admin", (
            '<a href="/admin">Dashboard admin</a>'
            '<a href="/akun?section=akun">Ganti sandi</a>'
        )
    else:
        brand, item = "/", '<a href="/akun">Akun &amp; Siswa</a>'
    siapa = html.escape(pengguna) if pengguna else ""
    return (
        '<div class="st-topbar">'
        f'<a class="brand" href="{brand}">'
        '<span class="owl material-symbols-outlined">school</span>'
        f'<span class="nama">{html.escape(T.NAMA_PRODUK)}</span>'
        "</a>"
        '<nav class="topbar-navigasi">'
        f'{_badge_peran(peran)}'           # badge peran lama (Pengelola/Orang Tua)
        f'<details class="menu-pengguna">'
        f"<summary>{siapa}</summary>"
        f'<div class="menu-isi">{item}'
        '<div class="menu-pisah"></div>'
        '<form method="post" action="/keluar" style="margin:0">'
        '<button type="submit" class="cta">Keluar</button>'
        "</form></div></details></nav></div>"
    )


def _halaman_stitch(
    judul: str, isi: str, ident: tuple[str, str] | None = None
) -> bytes:
    """Bingkai halaman versi Stitch — pakai GAYA_STITCH dan body.st.

    Dipisah dari _halaman lama supaya halaman lama tetap utuh; fungsi ini
    satu-satunya penghubung ke CSS Stitch di tree.
    """
    batang = _topbar_stitch(*ident) if ident else ""
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap" rel="stylesheet">
<style>{GAYA_STITCH}</style></head>
<body class="st"><div class="bungkus-st">{batang}{isi}</div><script>{SKRIP_MATA_SANDI}</script><script>{SKRIP_CEGAH_KIRIM_GANDA}</script></body></html>""".encode()


def halaman_utama_stitch(
    kon,
    pesan: str = "",
    pemilik: str | None = None,
    peran: str = "guru",
    sorot: int | None = None,
) -> bytes:
    """Dashboard pengelola versi Stitch. Signature identik dengan
    halaman_utama supaya bisa dipasang berdampingan (web.py beralih saat).

    Perilaku data dan query DIPERTAHANKAN SAMA — hanya markup + kelas CSS
    yang baru. Baris sesi baru tetap diberi kelas sorot-baru.
    """
    baris = []
    admin = peran == "admin"
    for s in database.daftar_siswa(kon, pemilik):
        # Dashboard ringkas (feedback Filia 1 Sep 2026 no. 6): satu kartu
        # NAMA per anak — klik masuk ke /anak/<id> tempat history lengkap
        # dan strip buat sesi. Ringkasan cukup angka, tanpa daftar sesi.
        rekap = kon.execute(
            """SELECT COUNT(*) AS jumlah,
                      SUM(CASE WHEN direview IS NULL THEN 1 ELSE 0 END) AS belum_review
               FROM sesi WHERE siswa_id = ?""",
            (s["id"],),
        ).fetchone()
        jumlah_sesi = rekap["jumlah"] or 0
        belum_review = rekap["belum_review"] or 0
        badge_review = (
            f'<span class="st-badge review">{belum_review} belum direview</span>'
            if belum_review
            else '<span class="st-badge diagnostik">semua direview</span>'
        )
        label_keluarga = ""
        if admin:
            siapa = s["pemilik"] or "warisan"
            label_keluarga = (
                '<span class="st-badge selesai">keluarga: '
                f"{html.escape(siapa)}</span>"
            )

        baris.append(
            f'<a class="st-kartu kartu-anak" href="/anak/{s["id"]}" '
            'style="display:flex;align-items:center;gap:.9rem;'
            'text-decoration:none;color:inherit">'
            '<span class="material-symbols-outlined" style="font-size:2rem;'
            f'color:{T.AKSEN_MURID_UTAMA};flex:none">person</span>'
            '<span style="flex:1;min-width:0">'
            f'<h2 class="st" style="margin:0">{html.escape(s["nama"])}'
            f'<span class="st-badge selesai">({html.escape(str(s["tingkat"]))})</span>'
            f"{label_keluarga}"
            "</h2>"
            f'<span style="font-size:.9rem;color:{T.TEKS_VARIAN}">'
            f"{jumlah_sesi} sesi</span>"
            "</span>"
            f"{badge_review}"
            '<span class="material-symbols-outlined" style="flex:none;'
            f'color:{T.TEKS_SUBTLE}">chevron_right</span>'
            "</a>"
        )

    isi_utama = "".join(baris) or (
        '<div class="st-kartu">Belum ada siswa. '
        '<a href="/akun">Buat siswa</a> dari halaman Akun &amp; Siswa.</div>'
    )

    kabar = (
        '<div class="st-banner-sukses"><span class="ikon">✓</span>'
        f"<span>{html.escape(pesan)}</span></div>"
        if pesan
        else ""
    )

    return _halaman_stitch(
        T.NAMA_PRODUK,
        f'<h1 class="st">{T.NAMA_PRODUK} — Latihan Matematika SD</h1>'
        '<p class="sub">Klik nama anak untuk melihat history dan membuat sesi latihan.</p>'
        f"{kabar}"
        f'<div class="daftar-anak">{isi_utama}</div>'
        "<script>(function(){var r=document.querySelectorAll('input[name=\"mode\"]');for(var i=0;i<r.length;i++){r[i].addEventListener(\"change\",function(){var t=this.closest(\"form\").querySelector(\".pengaturan-timer\");if(t)t.style.display=this.value===\"drill\"?\"\":\"none\";});}})()</script>",
        ident=(pemilik if pemilik else "guru", peran),
    )



def halaman_anak(
    kon,
    siswa,
    peran: str = "guru",
    pengguna: str = "",
    sorot: int | None = None,
    pesan: str = "",
) -> bytes:
    """History satu anak (feedback Filia 1 Sep 2026 no. 6).

    Masuk dari kartu nama di dashboard. Berisi: daftar sesi anak (dengan
    badge review & mode), strip buat sesi baru, dan pintasan laporan.
    `siswa` baris sqlite dari tabel siswa.
    """
    admin = peran == "admin"
    opsi_topik = "".join(
        f'<option value="{html.escape(t)}">{html.escape(ambil(t).nama)}</option>'
        for t in _topik_untuk_level(siswa["tingkat"])
    )
    sesi = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode,
                  s.mulai, s.selesai, s.direview,
                  (SELECT MIN(j.dicatat) FROM sesi_soal ss
                   JOIN jawaban j ON j.sesi_soal_id = ss.id
                   WHERE ss.sesi_id = s.id) AS dicatat_awal,
                  (SELECT MAX(j.dicatat) FROM sesi_soal ss
                   JOIN jawaban j ON j.sesi_soal_id = ss.id
                   WHERE ss.sesi_id = s.id) AS dicatat_akhir,
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
        (siswa["id"],),
    ).fetchall()

    def _kelas_sorot(rid):
        return "sorot-baru" if sorot is not None and rid == sorot else ""

    if sesi:
        item = "".join(
            f'<div class="st-kartu-baris {kelas}">'
            f'<div class="kolom-sesi" style="flex:1">'
            f'<a href="/sesi/{r["id"]}">Sesi #{r["id"]}</a>'
            f'<div class="st-meta" style="font-size:.85rem;opacity:.75">{html.escape(r["tanggal"])}'
            f'&middot; {html.escape(_ambil(r, "level", LEVEL_BAWAAN))}'
            f'&middot; {html.escape(_ambil(r, "topik", TOPIK_BAWAAN))}</div>'
            f"</div>"
            f'<div style="text-align:right;font-variant-numeric:tabular-nums;margin-right:0.6rem">'
            f'<div>Terisi {r["terisi"]}/{r["n"]}</div>'
            f'<div>Benar {r["benar"]}/{r["n"]}</div>'
            f'<div>Waktu {_fmt_durasi(_ambil(r, "mulai", None), _ambil(r, "selesai", None), _ambil(r, "dicatat_awal", None), _ambil(r, "dicatat_akhir", None))}</div>'
            f"</div>"
            f'<div style="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end">'
            f'{_badge_review_status(r)}'
            f'{_badge_mode_stitch(r)}'
            f"</div>"
            f"</div>"
            for r, kelas in (
                (r, _kelas_sorot(r["id"])) for r in sesi
            )
        )
    else:
        item = '<p class="sub">Belum ada sesi — buat yang pertama di bawah.</p>'

    label_keluarga = ""
    if admin:
        siapa = siswa["pemilik"] or "warisan"
        label_keluarga = (
            '<span class="st-badge selesai">keluarga: '
            f"{html.escape(siapa)}</span>"
        )

    strip_sesi = (
        f'<form method="post" action="/sesi-baru/{siswa["id"]}" class="strip-sesi">'
        f'<div class="strip-kolom"><label>Topik</label>'
        f'<select name="topik" class="st-input">{opsi_topik}</select></div>'
        f'<div class="strip-kolom"><label>Jumlah Soal (estimasi ±3 mnt/soal)</label>'
        f'<select name="jumlah_soal" class="st-input">'
        f'<option value="" selected>Default (sesuai topik)</option>'
        f'<option value="10">10 soal (± 30 mnt)</option>'
        f'<option value="15">15 soal (± 45 mnt)</option>'
        f'<option value="20">20 soal (± 60 mnt)</option>'
        f'<option value="25">25 soal (± 75 mnt)</option>'
        f'<option value="30">30 soal (± 90 mnt)</option>'
        f'</select></div>'
        '<div class="strip-kolom"><label>Mode Sesi</label>'
        '<div class="mode-pilih">'
        '<label class="mode-opsi"><input type="radio" name="mode" value="diagnostik" checked>'
        '<span class="mode-teks">Mode Diagnosa'
        '<span class="mode-desk">Identifikasi area kelemahan secara otomatis.</span>'
        '</span></label>'
        '<label class="mode-opsi"><input type="radio" name="mode" value="drill">'
        '<span class="mode-teks">Mode Latihan Cepat'
        '<span class="mode-desk">Latihan intensif dengan pengaturan waktu.</span>'
        '</span></label>'
        "</div></div>"
        '<div class="pengaturan-timer" style="display:none">'
        '<label>Pengaturan Waktu</label>'
        '<div class="mode-pilih">'
        '<label class="mode-opsi"><input type="radio" name="timer_mode" value="tanpa" checked> Tanpa timer</label>'
        '<label class="mode-opsi"><input type="radio" name="timer_mode" value="sesi"> Per sesi (tampil)</label>'
        '<label class="mode-opsi"><input type="radio" name="timer_mode" value="soal"> Per soal (internal)</label>'
        "</div>"
        '<label>Durasi '
        '<input type="number" name="durasi_menit" value="15" min="1" max="180"> menit</label>'
        '<label class="mode-opsi"><input type="checkbox" name="timer_auto" value="1"> Auto-submit ketika waktu habis</label>'
        "</div>"
        '<button type="submit" class="st-tombol-coral">'
        '<span class="material-symbols-outlined" style="font-size:1.1rem">play_arrow</span>'
        "Buat sesi baru</button>"
        "</form>"
    )

    # Latihan ulang (poin a feedback Filia): satu klik membuat sesi berisi
    # HANYA konsep yang pernah dijawab salah anak ini, dengan soal baru.
    # Tombol hanya muncul kalau memang ADA dasarnya — tanpa kesalahan
    # tercatat, menawarkan "remedial" itu mengarang.
    sasaran = database.sasaran_remedial(kon, siswa["id"])
    strip_remedial = ""
    if sasaran and not admin:
        strip_remedial = (
            '<form method="post" '
            f'action="/sesi-remedial/{siswa["id"]}" class="strip-sesi">'
            '<div class="strip-kolom">'
            "<label>Latihan ulang — dari kesalahan yang tercatat</label>"
            f'<p class="sub">{len(sasaran)} konsep akan dilatih ulang '
            "dengan soal baru (angkanya berganti, konsepnya sama).</p>"
            "</div>"
            '<div class="strip-kolom"><label>Jumlah Soal</label>'
            '<select name="jumlah_soal" class="st-input">'
            '<option value="10" selected>10 soal (± 30 mnt)</option>'
            '<option value="15">15 soal (± 45 mnt)</option>'
            '<option value="20">20 soal (± 60 mnt)</option>'
            "</select></div>"
            '<button type="submit" class="st-tombol-coral">'
            '<span class="material-symbols-outlined" style="font-size:1.1rem">'
            "restart_alt</span>Buat latihan ulang</button>"
            "</form>"
        )

    kabar = (
        '<div class="st-banner-sukses"><span class="ikon">✓</span>'
        f"<span>{html.escape(pesan)}</span></div>"
        if pesan
        else ""
    )

    return _halaman_stitch(
        f"{siswa['nama']} — {T.NAMA_PRODUK}",
        f'<div class="jejak"><a href="/">&larr; Semua anak</a></div>'
        f'<h1 class="st">{html.escape(siswa["nama"])}'
        f'<span class="st-badge selesai">({html.escape(str(siswa["tingkat"]))})</span>'
        f"{label_keluarga}"
        "</h1>"
        f'<p class="sub">History latihan — '
        f'<a href="/laporan/{siswa["id"]}">lihat laporan tren &rarr;</a></p>'
        f"{kabar}"
        f'<div class="daftar-anak">{item}</div>'
        f"{strip_remedial}"
        f"{strip_sesi}"
        "<script>(function(){var r=document.querySelectorAll('input[name=\"mode\"]');"
        "for(var i=0;i<r.length;i++){r[i].addEventListener(\"change\","
        "function(){var t=this.closest(\"form\").querySelector(\".pengaturan-timer\");"
        "if(t)t.style.display=this.value===\"drill\"?\"\":\"none\";});}})()</script>",
        ident=(pengguna if pengguna else "guru", peran),
    )

def halaman_utama(
    kon,
    pesan: str = "",
    pemilik: str | None = None,
    peran: str = "guru",
    sorot: int | None = None,
) -> bytes:
    """Dashboard pengelola."""
    baris = []
    admin = peran == "admin"
    for s in database.daftar_siswa(kon, pemilik):
        opsi_topik = "".join(
            f'<option value="{html.escape(t)}">{html.escape(ambil(t).nama)}</option>'
            for t in _topik_untuk_level(s["tingkat"])
        )
        sesi = kon.execute(
            """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode,
                      s.mulai, s.selesai, s.direview,
                      (SELECT MIN(j.dicatat) FROM sesi_soal ss
                       JOIN jawaban j ON j.sesi_soal_id = ss.id
                       WHERE ss.sesi_id = s.id) AS dicatat_awal,
                      (SELECT MAX(j.dicatat) FROM sesi_soal ss
                       JOIN jawaban j ON j.sesi_soal_id = ss.id
                       WHERE ss.sesi_id = s.id) AS dicatat_akhir,
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

        def _kelas_sorot(rid):
            return "sorot-baru" if sorot is not None and rid == sorot else ""
        item = "".join(
            f'<tr class="{_kelas_sorot(r["id"])}"><td class="kolom-sesi"><a href="/sesi/{r["id"]}">Sesi #{r["id"]}</a>'
            f'{_badge_mode(r)}</td>'
            f'<td class="kolom-tanggal">{r["tanggal"]}</td>'
            f'<td class="tipe">{_ambil(r, "level", LEVEL_BAWAAN)}</td>'
            f'<td class="tipe" style="white-space:nowrap">{_ambil(r, "topik", TOPIK_BAWAAN)}</td>'
            f'<td class="angka">{r["terisi"]}/{r["n"]}</td>'
            f'<td class="angka">{r["benar"]}/{r["n"]}</td>'
            f'<td class="angka">{_fmt_durasi(_ambil(r, "mulai", None), _ambil(r, "selesai", None), _ambil(r, "dicatat_awal", None), _ambil(r, "dicatat_akhir", None))}</td>'
            f'<td class="kolom-status">{_badge_review_status(r)}</td></tr>'
            for r in sesi
        ) or '<tr><td colspan="8" class="kosong">belum ada sesi</td></tr>'

        label_keluarga = ""
        if admin:
            siapa = s["pemilik"] or "warisan"
            label_keluarga = (
                f'<span class="badge-keluarga">keluarga: {html.escape(siapa)}</span>'
            )

        strip_sesi = (
            f'<form method="post" action="/sesi-baru/{s["id"]}" class="strip-sesi">'
            f'<div class="strip-kolom"><label>Topik</label>'
            f'<select name="topik">{opsi_topik}</select></div>'
            f'<div class="strip-kolom"><label>Jumlah Soal (estimasi ±3 mnt/soal)</label>'
            f'<select name="jumlah_soal">'
            f'<option value="" selected>Default (sesuai topik)</option>'
            f'<option value="10">10 soal (± 30 mnt)</option>'
            f'<option value="15">15 soal (± 45 mnt)</option>'
            f'<option value="20">20 soal (± 60 mnt)</option>'
            f'<option value="25">25 soal (± 75 mnt)</option>'
            f'<option value="30">30 soal (± 90 mnt)</option>'
            f'</select></div>'
            f'<div class="strip-kolom"><label>Mode</label>'
            f'<div class="mode-pilih">'
            f'<label class="mode-opsi"><input type="radio" name="mode" '
            f'value="diagnostik" checked> Diagnosa</label>'
            f'<label class="mode-opsi"><input type="radio" name="mode" '
            f'value="drill"> Latihan Cepat</label>'
            f'</div></div>'
            f'<div class="pengaturan-timer" style="display:none">'
            f'<label>Durasi '
            f'<input type="number" name="durasi_menit" value="15" '
            f'min="1" max="180" style="width:4.5rem"> menit</label>'
            f'<label class="mode-opsi"><input type="radio" name="timer_mode" '
            f'value="sesi" checked> per sesi (tampil)</label>'
            f'<label class="mode-opsi"><input type="radio" name="timer_mode" '
            f'value="soal"> per soal (internal)</label>'
            f'<label class="mode-opsi"><input type="checkbox" '
            f'name="timer_auto" value="1"> auto-submit</label>'
            f'</div>'
            f'<button type="submit" class="tombol-coral">Buat sesi baru</button>'
            f'</form>'
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
            f"<th>Waktu</th><th>Status Review</th></tr>"
            f"{item}</table></div>"
            f"{strip_sesi}"
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
        f'<div class="daftar-anak">{isi_utama}</div>'
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

def _pil_sesi(kon, sesi_id: int, aktif: str) -> str:
    """Pil navigasi di halaman sesi: Koreksi · Cetak & Cerita · Lampiran."""
    n_lamp = kon.execute(
        "SELECT COUNT(*) FROM lampiran WHERE sesi_id = ?", (sesi_id,)
    ).fetchone()[0]
    def _a(kunci: str, label: str, href: str) -> str:
        cls = "pil aktif" if kunci == aktif else "pil"
        return f'<a class="{cls}" href="{href}">{label}</a>'
    return (
        '<nav class="pil-sesi">'
        + _a("koreksi", "Koreksi", f"/sesi/{sesi_id}")
        + _a("cetak", "Cetak & Cerita", f"/sesi/{sesi_id}/cetak")
        + _a("lampiran", f"Lampiran ({n_lamp})", f"/sesi/{sesi_id}/lampiran")
        + "</nav>"
    )


def halaman_sesi_cetak(
    kon, sesi_id: int, pesan: str = "", peran: str = "guru",
    pengguna: str = "",
) -> bytes | None:
    """Halaman cetak & cerita per sesi — lembar soal/kunci + variasi cerita."""
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode,
                  w.nama, w.id AS siswa_id
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return None
    badge_mode = _badge_mode(info)
    admin = peran == "admin"
    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    blok_cerita = "" if admin else _tombol_cerita(kon, sesi_id)
    pil = _pil_sesi(kon, sesi_id, "cetak")
    return _halaman(
        f"Sesi #{sesi_id} — Cetak",
        f'<div class="jejak"><a href="/sesi/{sesi_id}">&larr; Kembali ke koreksi</a> &middot; <a href="/">&larr; Semua siswa</a></div>'
        f'<h1>{html.escape(info["nama"])} — Sesi #{sesi_id}</h1>'
        f'<p class="sub">{info["tanggal"]} &middot; '
        f'{_ambil(info, "level", LEVEL_BAWAAN)} &middot; '
        f'{_ambil(info, "topik", TOPIK_BAWAAN)} &middot; '
        f'seed {info["seed"]} {badge_mode}</p>'
        f"{kabar}"
        f"{pil}"
        f'<div class="kartu"><h2>Cetak</h2>'
        f'<p><a class="btn" href="/lembar/{sesi_id}" target="_blank">Lembar soal</a> '
        f'<a class="btn" href="/lembar/{sesi_id}/penilaian" target="_blank">Lembar kunci</a></p>'
        f'<p class="sub">Dibuka di tab baru — siap cetak.</p></div>'
        f"{blok_cerita}",
        ident=(pengguna, peran) if pengguna else None,
        stitch=True,
    )


def halaman_sesi_lampiran(
    kon, sesi_id: int, pesan: str = "", peran: str = "guru",
    pengguna: str = "",
) -> bytes | None:
    """Halaman lampiran foto per sesi — daftar + upload."""
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode,
                  w.nama, w.id AS siswa_id
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return None
    badge_mode = _badge_mode(info)
    admin = peran == "admin"
    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    baris_lampiran = []
    for lamp in database.daftar_lampiran(kon, sesi_id):
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
    pil = _pil_sesi(kon, sesi_id, "lampiran")
    return _halaman(
        f"Sesi #{sesi_id} — Lampiran",
        f'<div class="jejak"><a href="/sesi/{sesi_id}">&larr; Kembali ke koreksi</a> &middot; <a href="/">&larr; Semua siswa</a></div>'
        f'<h1>{html.escape(info["nama"])} — Sesi #{sesi_id}</h1>'
        f'<p class="sub">{info["tanggal"]} &middot; '
        f'{_ambil(info, "level", LEVEL_BAWAAN)} &middot; '
        f'{_ambil(info, "topik", TOPIK_BAWAAN)} &middot; '
        f'seed {info["seed"]} {badge_mode}</p>'
        f"{kabar}"
        f"{pil}"
        f"{blok_lampiran}",
        ident=(pengguna, peran) if pengguna else None,
        stitch=True,
    )


def halaman_sesi(
    kon, sesi_id: int, pesan: str = "", peran: str = "guru",
    pengguna: str = "",
) -> bytes:
    """Detail satu sesi — HANYA koreksi (opsi 3: alat pindah ke /cetak & /lampiran).

    Kebijakan admin baca-semua-tulis-tidak dijaga di router (POST ditolak
    404); di sini tombol/form tulis disembunyikan supaya admin tidak
    menabrak 404 dari UI-nya sendiri."""
    admin = peran == "admin"
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode, s.direview,
                   w.nama, w.id AS siswa_id
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return _halaman("Tidak ada", "<h1>Sesi tidak ditemukan</h1>")

    kartu = []
    for b in database.isi_sesi(kon, sesi_id):
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

        pembahasan_html = ""
        if getattr(soal, "pembahasan", ""):
            pembahasan_html = (
                f'<div class="pembahasan-soal" style="margin-top:0.35rem;font-size:0.88rem;'
                f'background:#f0f7ff;border-left:3px solid #3182ce;padding:0.4rem 0.6rem;border-radius:4px;'
                f'color:#2b6cb0;">'
                f'<b>Perhitungan/Langkah:</b> {html.escape(soal.pembahasan)}'
                f'</div>'
            )

        kartu.append(f"""
<div class="kartu soal-kartu {kelas}">
  <div class="kartu-kepala">
    <span class="nomor">{b["nomor"]}</span>{lencana}
    <span class="tipe">{b["template_id"]}</span>
  </div>
  <div class="teks-soal">{html.escape(soal.teks)}</div>
  <div>Kunci: <span class="kunci">{html.escape(b["kunci"])}</span></div>
  {pembahasan_html}
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

    # Badge mode sesi (Latihan Cepat / drill)
    badge_mode = _badge_mode(info)
    badge_review_hdr = (
        '<span class="badge-direview sudah" style="background:#d4edda;color:#155724;padding:0.25rem 0.6rem;border-radius:4px;font-size:0.85rem;font-weight:bold;margin-left:0.5rem">✓ Sudah Direview</span>'
        if _ambil(info, "direview", None)
        else '<span class="badge-direview perlu" style="background:#fff3cd;color:#856404;padding:0.25rem 0.6rem;border-radius:4px;font-size:0.85rem;font-weight:bold;margin-left:0.5rem">⏳ Belum Direview</span>'
    )

    pil = _pil_sesi(kon, sesi_id, "koreksi")

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
    if admin:
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
        f'<h1>{html.escape(info["nama"])} — Sesi #{sesi_id} {badge_review_hdr}</h1>'
        f'<p class="sub">{info["tanggal"]} &middot; '
        f'{_ambil(info, "level", LEVEL_BAWAAN)} &middot; '
        f'{_ambil(info, "topik", TOPIK_BAWAAN)} &middot; '
        f'seed {info["seed"]} {badge_mode}</p>'
        f"{kabar}"
        f"{pil}"
        f"{blok_isi}"
        f'<div class="danger-zone" style="margin-top:1.2rem;border-top:1px solid #e5c3c3;padding-top:.7rem">'
        f'<p class="sub" style="margin:0 0 .4rem">Zona bahaya — hapus tidak bisa dibatalkan.</p>'
        f"{tombol_hapus}</div>",
        ident=(pengguna, peran) if pengguna else None,
    )


def _pil_sesi_stitch(kon, sesi_id: int, aktif: str) -> str:
    """Pil navigasi sesi versi Stitch."""
    n_lamp = kon.execute(
        "SELECT COUNT(*) FROM lampiran WHERE sesi_id = ?", (sesi_id,)
    ).fetchone()[0]
    def _a(kunci: str, label: str, href: str) -> str:
        cls = "aktif" if kunci == aktif else ""
        return f'<a class="{cls}" href="{href}">{label}</a>'
    return (
        '<nav class="pil-sesi-st">'
        + _a("koreksi", "Koreksi", f"/sesi/{sesi_id}")
        + _a("cetak", "Cetak &amp; Cerita", f"/sesi/{sesi_id}/cetak")
        + _a("lampiran", f"Lampiran ({n_lamp})", f"/sesi/{sesi_id}/lampiran")
        + "</nav>"
    )


def halaman_sesi_stitch(
    kon, sesi_id: int, pesan: str = "", peran: str = "guru",
    pengguna: str = "",
) -> bytes:
    """Detail sesi versi Stitch — HANYA koreksi (opsi 3)."""
    from style_stitch import gaya_stitch, CSS_SESI

    admin = peran == "admin"
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik, s.mode, s.direview,
                   w.nama, w.id AS siswa_id
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id WHERE s.id = ?""",
        (sesi_id,),
    ).fetchone()
    if not info:
        return _halaman("Tidak ada", "<h1>Sesi tidak ditemukan</h1>")

    kartu = []
    for b in database.isi_sesi(kon, sesi_id):
        soal = _soal_dari_baris(b)
        sudah = b["jawaban_id"] is not None
        kode = b["kode_final"]
        benar = b["benar"]

        if sudah and (benar or kode):
            kelas_isi = "sudah"
            bulat_cls = "benar" if benar else (kode or "N")
            lencana = (
                '<span class="kode benar">BENAR</span>' if benar
                else f'<span class="kode {kode}">{kode}</span>'
            )
            bulat_label = (
                "Tepat" if benar
                else "Konsep" if kode == "K"
                else "Baca" if kode == "B"
                else "Hitung" if kode == "H"
                else "Tulis" if kode == "E"
                else "Belum lihat" if kode == "T"
                else ""
            )
        elif sudah:
            kelas_isi, bulat_cls, lencana, bulat_label = "", "N", '<span class="kode N">?</span>', "Belum dinilai"
        else:
            kelas_isi, bulat_cls, lencana, bulat_label = "", "", "", ""

        kolom_status = ""
        if lencana:
            kolom_status = (
                '<div class="koreksi-status-st">'
                f'<div class="koreksi-bulat-st {bulat_cls}">{lencana}</div>'
                f'<span class="koreksi-bulat-label-st">{bulat_label}</span>'
                "</div>"
            )

        usulan = ""
        if sudah and b["alasan"]:
            ragu = "" if (benar or kode) else " ragu"
            usulan = (
                f'<div class="usulan-st{ragu}"><b>Mesin:</b> '
                f'{html.escape(b["alasan"])}</div>'
            )

        restate = ""
        if soal.minta_restatement:
            restate = (
                '<label class="koreksi-label-st">Kotak "mintanya apa" — '
                "tulis ulang apa yang anak isi</label>"
                f'<input type="text" class="koreksi-input-st"'
                f' name="restate_{b["sesi_soal_id"]}" '
                f'value="{html.escape(b["restatement"] or "")}">'
            )

        pilih = "".join(
            f'<option value="{v}"{" selected" if (v == kode or (v == "benar" and benar)) else ""}>'
            f"{html.escape(t)}</option>"
            for v, t in KODE_PILIHAN
        )

        nomor = f'<span class="koreksi-nomor-st">{b["nomor"]}</span>'
        tipe = f'<span class="koreksi-tipe-st">{b["template_id"]}</span>'

        pembahasan_html = ""
        if getattr(soal, "pembahasan", ""):
            pembahasan_html = (
                f'<div class="pembahasan-soal-st" style="margin-top:0.35rem;font-size:0.88rem;'
                f'background:#f0f7ff;border-left:3px solid #3182ce;padding:0.4rem 0.6rem;border-radius:4px;'
                f'color:#2b6cb0;">'
                f'<b>Perhitungan/Langkah:</b> {html.escape(soal.pembahasan)}'
                f'</div>'
            )

        kartu.append(f"""
<div class="koreksi-kartu-st">
  <div class="koreksi-isi-st {kelas_isi}">
    <div class="koreksi-kepala-st">{nomor}{tipe}</div>
    <div class="teks-soal-st">{html.escape(soal.teks)}</div>
    <div class="kunci-baris-st">Kunci: <span class="kunci-val">{html.escape(b["kunci"])}</span></div>
    {pembahasan_html}
    {restate}
    <div class="koreksi-baris-st">
      <div>
        <label class="koreksi-label-st"><span class="material-symbols-outlined" style="font-size:1rem">edit</span> Jawaban anak</label>
        <input type="text" class="koreksi-input-st" name="jwb_{b["sesi_soal_id"]}"
               value="{html.escape(b["jawaban"] or "")}">
      </div>
      <div>
        <label class="koreksi-label-st">Kode (kosongkan = pakai usulan mesin)</label>
        <select class="koreksi-select-st" name="kode_{b["sesi_soal_id"]}">{pilih}</select>
      </div>
    </div>
    <label class="koreksi-label-st">Isi kotak "Caraku" — ringkas saja, cukup yang menunjukkan caranya</label>
    <textarea class="koreksi-textarea-st" name="cara_{b["sesi_soal_id"]}">{html.escape(b["cara"] or "")}</textarea>
    <div class="koreksi-centang-st">
      <input type="checkbox" id="bp{b["sesi_soal_id"]}"
             name="belum_{b["sesi_soal_id"]}"
             {"checked" if b["belum_pernah"] else ""}>
      <label for="bp{b["sesi_soal_id"]}">anak mencentang "belum pernah lihat soal seperti ini"</label>
    </div>
    {usulan}
  </div>
  {kolom_status}
</div>""")

    kabar = f'<div class="pesan-st">{html.escape(pesan)}</div>' if pesan else ""
    badge_mode = _badge_mode(info)
    pil = _pil_sesi_stitch(kon, sesi_id, "koreksi")

    tombol_hapus = (
        ""
        if admin
        else (
            f'<form method="get" action="/sesi/{sesi_id}/hapus" '
            f'style="margin:.4rem 0">'
            f'<button type="submit" class="tombol-kecil-st">'
            f"Hapus sesi</button></form>"
        )
    )
    if admin:
        blok_isi = f'<fieldset disabled>{"".join(kartu)}</fieldset>'
    else:
        blok_isi = (
            f'<form method="post" action="/sesi/{sesi_id}">'
            f'{"".join(kartu)}'
            f'<div class="koreksi-simpan-st"><button type="submit">'
            "Simpan &amp; diagnosis</button></div></form>"
        )

    batang = _topbar_stitch(pengguna, peran) if pengguna else ""
    isi = (
        f'<div class="sesi-badan-st">'
        f'<div class="sesi-jejak-st"><a href="/">&larr; Semua siswa</a></div>'
        f'<h1 class="sesi-judul-st">{html.escape(info["nama"])} — Sesi #{sesi_id}</h1>'
        f'<p class="sesi-sub-st">{info["tanggal"]} &middot; '
        f'{_ambil(info, "level", LEVEL_BAWAAN)} &middot; '
        f'{_ambil(info, "topik", TOPIK_BAWAAN)} &middot; '
        f'seed {info["seed"]} {badge_mode}</p>'
        f"{kabar}"
        f"{pil}"
        f"{blok_isi}"
        f'<div class="danger-zone-st">'
        f'<p class="sub">Zona bahaya — hapus tidak bisa dibatalkan.</p>'
        f"{tombol_hapus}</div>"
        f"</div>"
    )
    skrip_extra = (
        f"<script>{SKRIP_MATA_SANDI}</script>"
        f"<script>{SKRIP_CEGAH_KIRIM_GANDA}</script>"
    )
    return (
        f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sesi #{sesi_id} &middot; {html.escape(T.NAMA_PRODUK)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
<style>{gaya_stitch()}{CSS_SESI}</style></head>
<body class="st"><div class="bungkus-st">{batang}{isi}</div>{skrip_extra}</body></html>"""
    ).encode()


def simpan_sesi(kon, sesi_id: int, data: dict) -> str:
    """Simpan jawaban lalu jalankan diagnosis otomatis.

    Kode dari guru menang atas usulan mesin, dan bedanya dicatat lewat kolom
    `manual` supaya nanti bisa diukur seberapa sering mesin meleset.
    """
    diubah = 0
    for b in database.isi_sesi(kon, sesi_id):
        sid = b["sesi_soal_id"]
        jwb = data.get(f"jwb_{sid}", "").strip()
        cara = data.get(f"cara_{sid}", "").strip()
        restate = data.get(f"restate_{sid}", "").strip()
        belum = f"belum_{sid}" in data
        pilihan = data.get(f"kode_{sid}", "").strip()

        if not (jwb or cara or restate or belum or pilihan):
            continue

        jid = database.simpan_jawaban(kon, sid, jwb, cara, restate, belum)

        soal = _soal_dari_baris(b)
        u = diagnosa(
            b["kunci"], jwb, cara, restate, belum,
            database.malrule_soal(kon, b["soal_id"]),
            soal.minta_restatement,
        )

        if pilihan == "benar":
            benar, final, manual = True, None, True
        elif pilihan:
            benar, final, manual = False, pilihan, True
        else:
            benar, final, manual = u.benar, u.kode, False

        database.simpan_diagnosis(
            kon, jid, benar, u.kode, final, u.malrule_id, u.alasan, manual
        )
        diubah += 1

    return f"{diubah} soal tersimpan dan didiagnosis."

def buat_sesi_seed_baru(
    kon,
    siswa_id: int,
    level: str | None = None,
    topik: str | None = None,
    mode: str = "diagnostik",
    timer_mode: str = "tanpa",
    durasi_menit: int = 15,
    timer_auto: int = 0,
    jumlah_soal: int | None = None,
) -> int:
    """Sesi baru dengan seed yang belum pernah dipakai siswa ini."""
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
            return database.buat_sesi(
                kon, siswa_id, seed, level=level, topik=topik, mode=mode,
                timer_mode=timer_mode, durasi_menit=durasi_menit,
                timer_auto=timer_auto, jumlah_soal=jumlah_soal,
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

    soal = [_soal_dari_baris(b) for b in database.isi_sesi(kon, sesi_id)]
    # Judul dari paket topik sesi ini — bukan selalu paket bawaan. Sesi lama
    # dengan nilai kolom aneh jatuh ke bawaan lewat dari_sesi(), sesuai
    # kontrak data produksi.
    paket = dari_sesi(info["topik"])
    # Lembar yang sama, dua tampilan (Fase 3): di web ia dibaca dari layar,
    # jadi dipakai gaya layar — kartu sentuh, tanpa satuan mm. Versi cetak
    # tetap keluar lewat tombol cetak browser (@media print di gaya layar
    # menurunkan dirinya ke perilaku kertas).
    from screen_style import GAYA_LAYAR

    if untuk_guru:
        isi = worksheets.lembar_penilaian(
            soal, info["nama"], info["tanggal"], info["seed"],
            gaya=GAYA_LAYAR, topik_paket=paket,
        )
    else:
        isi = worksheets.lembar_soal(
            soal, info["nama"], info["tanggal"], gaya=GAYA_LAYAR,
            topik_paket=paket,
        )
    return isi.encode()
