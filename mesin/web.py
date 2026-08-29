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
from http.server import BaseHTTPRequestHandler

import basis
import cetak
import design_tokens as T
import sandi
import sesi
from diagnosa import diagnosa
from gaya_guru import GAYA_GURU as GAYA
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


def _halaman(judul: str, isi: str) -> bytes:
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(judul)}</title><style>{GAYA}</style></head>
<body><div class="bungkus">{isi}</div></body></html>""".encode()


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


def halaman_utama(kon) -> bytes:
    baris = []
    # Opsi topik disaring per tingkat: paket P5/P6 tidak boleh ditawarkan
    # pada kartu siswa P3 lalu gagal ketika form dikirim.
    for s in basis.daftar_siswa(kon):
        opsi_topik = "".join(
            f'<option value="{html.escape(t)}">{html.escape(t)}</option>'
            for t in _topik_untuk_level(s["tingkat"])
        )
        sesi = kon.execute(
            """SELECT s.id, s.tanggal, s.seed, s.level, s.topik,
                      (SELECT COUNT(*) FROM sesi_soal WHERE sesi_id = s.id) AS n,
                      (SELECT COUNT(*) FROM sesi_soal ss
                         JOIN jawaban j ON j.sesi_soal_id = ss.id
                        WHERE ss.sesi_id = s.id) AS terisi
               FROM sesi s WHERE s.siswa_id = ?
               ORDER BY s.tanggal DESC, s.id DESC""",
            (s["id"],),
        ).fetchall()

        item = "".join(
            f'<tr><td><a href="/sesi/{r["id"]}">Sesi #{r["id"]}</a></td>'
            f'<td>{r["tanggal"]}</td>'
            f'<td class="tipe">{_ambil(r, "level", LEVEL_BAWAAN)}</td>'
            f'<td class="tipe" style="white-space:nowrap">{_ambil(r, "topik", TOPIK_BAWAAN)}</td>'
            f'<td class="angka">{r["terisi"]}/{r["n"]}</td>'
            f'<td><a href="/lembar/{r["id"]}" target="_blank">soal</a> &middot; '
            f'<a href="/lembar/{r["id"]}/penilaian" target="_blank">kunci</a></td></tr>'
            for r in sesi
        ) or '<tr><td colspan="6" class="kosong">belum ada sesi</td></tr>'

        baris.append(
            f'<div class="kartu kartu-siswa">'
            f'<div class="siswa-kepala">'
            f'<h2>{html.escape(s["nama"])}'
            f'<span class="badge-tingkat">({s["tingkat"]})</span></h2>'
            f'<a class="btn" href="/laporan/{s["id"]}">Lihat laporan &rarr;</a>'
            f"</div>"
            f'<div class="tabel-wrap"><table><tr><th>Sesi</th><th>Tanggal</th>'
            f"<th>Level</th><th>Topik</th><th>Terisi</th><th>Lembar</th></tr>"
            f"{item}</table></div>"
            f'<form method="post" action="/sesi-baru/{s["id"]}" '
            f'class="baris" style="margin-top:.9rem">'
            f'<div><label>Topik</label>'
            f'<select name="topik">{opsi_topik}</select></div>'
            f'<div style="display:flex;align-items:flex-end">'
            f'<button type="submit" class="tombol-coral" style="width:100%">'
            f"Buat sesi baru</button></div></form>"
            f"</div>"
        )

    isi_utama = "".join(baris) or (
        '<div class="kartu kosong-hint-guru">Belum ada siswa. '
        '<a href="/akun">Buat siswa</a> dari halaman Akun &amp; Siswa.</div>'
    )

    return _halaman(
        "Mesin Latihan",
        f'<div class="topbar">'
        f'<span class="brand">Mesin Latihan</span>'
        f'<nav class="topbar-navigasi">'
        f'<a href="/akun">Akun &amp; Siswa</a>'
        f'<form method="post" action="/keluar" style="margin:0">'
        f'<button type="submit" class="tombol-kecil tombol-putih">Keluar</button>'
        f"</form></nav></div>"
        f"<h1>Mesin Latihan Pola Bilangan</h1>"
        f'<p class="sub">Pilih sesi untuk memasukkan hasil, atau buka laporan '
        f"untuk melihat tren.</p>"
        f'<div class="grid-utama">{isi_utama}</div>',
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


def halaman_sesi(kon, sesi_id: int, pesan: str = "") -> bytes:
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik,
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

    return _halaman(
        f"Sesi #{sesi_id}",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f'<h1>{html.escape(info["nama"])} — Sesi #{sesi_id}</h1>'
        f'<p class="sub">{info["tanggal"]} &middot; '
        f'{_ambil(info, "level", LEVEL_BAWAAN)} &middot; '
        f'{_ambil(info, "topik", TOPIK_BAWAAN)} &middot; '
        f'seed {info["seed"]} &middot; '
        f'<a href="/lembar/{sesi_id}" target="_blank">lembar soal</a> &middot; '
        f'<a href="/lembar/{sesi_id}/penilaian" target="_blank">lembar kunci</a> '
        f'&middot; <a href="/laporan/{info["siswa_id"]}">laporan siswa ini</a></p>'
        f"{kabar}"
        f"{_tombol_cerita(kon, sesi_id)}"
        f'<form method="post" action="/sesi/{sesi_id}">'
        f'{"".join(kartu)}'
        f'<div class="simpan-strip"><button type="submit">'
        f"Simpan &amp; diagnosis</button></div></form>",
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
    for b in basis.isi_sesi(kon, sesi_id):
        if b["jawaban_id"] is None:
            continue  # anak melewati soal ini: biarkan tanpa baris
        if b["manual"] == 1:
            # Segarkan usulan mesin saja; vonis guru tidak disentuh.
            soal = _soal_dari_baris(b)
            u = diagnosa(
                b["kunci"], b["jawaban"] or "", b["cara"] or "",
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
            b["kunci"], b["jawaban"] or "", b["cara"] or "",
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


def halaman_laporan(kon, siswa_id: int) -> bytes:
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
    )


def _kartu_akun_murid(kon) -> str:
    """Kartu akun murid di halaman akun.

    Pola persis kartu Siswa: tabel + form di bawahnya. Daftar akun diambil
    dari sandi.muat_akun() yang disaring peran == murid. Tiap akun dicek
    kecocokannya dengan tabel siswa lewat murid.siswa_dari_akun; kalau tidak
    cocok ditandai jelas "belum terhubung ke siswa" supaya guru tahu kenapa
    anak tidak bisa masuk.
    """
    import murid as _murid

    daftar_siswa = basis.daftar_siswa(kon)
    akun_murid = [a for a in sandi.muat_akun() if a.get("peran") == "murid"]

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
            f'<option value="{html.escape(s["nama"])}">{html.escape(s["nama"])}</option>'
            for s in daftar_siswa
        )
        pilih = f'<select name="nama" required><option value="">— pilih siswa —</option>{opsi}</select>'
        dis = ""
    else:
        pilih = '<select name="nama" disabled><option>belum ada siswa</option></select>'
        dis = " disabled"

    tambah = (
        f'<form method="post" action="/akun" style="margin-top:.8rem">'
        f'<input type="hidden" name="aksi" value="akun_murid_tambah">'
        f'<div class="baris">'
        f"<div><label>Siswa</label>"
        f"{pilih}</div>"
        f'<div><label>Sandi baru (minimal 8 karakter)</label>'
        f'<input type="password" name="sandi" placeholder="sandi untuk murid" required minlength="8">'
        f"</div></div>"
        f'<p style="margin-top:.6rem"><button type="submit"{dis}>Tambah akun murid</button></p>'
        f"</form>"
    )

    return (
        f'<div class="kartu"><h2>Akun murid</h2>'
        f"<p class=\"sub\">Akun murid dipakai anak untuk masuk ke /murid. "
        f"Nama akun harus sama persis dengan nama siswa — kalau tidak, anak tidak bisa masuk meski sandi benar.</p>"
        f"<table><tr><th>Nama</th><th>Status</th><th>Aksi</th></tr>{baris}</table>"
        f"{tambah}"
        f"</div>"
    )


def halaman_akun(kon, pesan: str = "", galat: str = "") -> bytes:
    """Kelola sandi dan daftar siswa.

    Sandi bisa diganti dari sini supaya sandi acak hasil deploy tidak jadi
    satu-satunya yang pernah ada — sandi yang tidak bisa diganti cenderung
    berakhir ditulis di tempat yang tidak aman.

    Siswa bisa dinonaktifkan, bukan dihapus: menghapus siswa akan ikut
    menghapus seluruh sesi, jawaban, dan diagnosisnya lewat ON DELETE
    CASCADE. Riwayat diagnosis adalah hasil kerja berbulan-bulan dan tidak
    bisa dibangun ulang.
    """
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
        f"</td></tr>"
        for s in basis.daftar_siswa(kon)
    )

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    if galat:
        kabar += f'<div class="pesan galat">{html.escape(galat)}</div>'

    d = sandi.muat_sandi()
    if not d:
        pengguna = "(belum disetel)"
    elif "akun" in d:
        g = next((a for a in d["akun"] if a.get("peran") == "guru"), None)
        pengguna = html.escape(g["pengguna"]) if g else "(belum disetel)"
    else:
        pengguna = html.escape(d["pengguna"])

    return _halaman(
        "Akun",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f"<h1>Akun &amp; pengaturan</h1>"
        f"{kabar}"
        f'<div class="layout-akun">'
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🔑</span>'
        f"<h2>Ganti sandi</h2></div>"
        f'<p class="sub">Pengguna saat ini: <b>{pengguna}</b>. Setelah diganti, '
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
        f"{_kartu_akun_murid(kon)}"
        f"</div>"
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">📚</span>'
        f"<h2>Siswa</h2></div>"
        f'<div class="tabel-wrap"><table><tr><th>Nama</th><th>Tingkat</th>'
        f"<th>Sesi</th></tr>{daftar}</table></div>"
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
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu amber">💡</span>'
        f"<h2>Catatan</h2></div>"
        f'<p class="sub">Siswa sengaja tidak bisa dihapus dari sini. Menghapus '
        f"siswa ikut menghapus seluruh sesi, jawaban, dan diagnosisnya — "
        f"riwayat yang tidak bisa dibangun ulang. Kalau seorang anak berhenti, "
        f"biarkan saja datanya; ia tidak mengganggu apa pun.</p>"
        f'<p class="sub">Cadangan basis data ditarik otomatis ke Mac tiap '
        f"malam pukul 22:00.</p></div>",
    )


def proses_akun(kon, data: dict, pengguna_kini: str) -> tuple[str, str]:
    """Jalankan aksi halaman akun. Mengembalikan (pesan, galat).

    Sandi lama SELALU diverifikasi ulang, walaupun pengguna sudah lolos
    palang untuk membuka halaman ini. Peramban menyimpan kredensial Basic
    dan mengirimkannya otomatis, jadi tanpa pemeriksaan ini siapa pun yang
    menemukan laptop dalam keadaan terbuka bisa mengganti sandi tanpa tahu
    yang lama.
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
        sudah = kon.execute(
            "SELECT 1 FROM siswa WHERE lower(nama) = lower(?)", (nama,)
        ).fetchone()
        if sudah:
            return "", f"Siswa bernama {nama} sudah ada."

        basis.tambah_siswa(kon, nama, tingkat)
        return f"Siswa {nama} ditambahkan ({tingkat}).", ""

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
        if not baris:
            return "", "Siswa tidak dikenal."
        kon.execute(
            "UPDATE siswa SET tingkat = ? WHERE id = ?", (tingkat, siswa_id)
        )
        return (
            f"{baris['nama']} sekarang {tingkat}. Sesi lama tetap pada "
            f"levelnya masing-masing; yang berubah hanya sesi berikutnya.",
            "",
        )

    if aksi == "akun_murid_tambah":
        nama = data.get("nama", "").strip()
        sandi_baru = data.get("sandi", "")
        # kalau form lama masih mengirim "baru", dukung juga
        if not sandi_baru:
            sandi_baru = data.get("baru", "")
        if not nama:
            return "", "Nama tidak boleh kosong."
        # nama WAJIB sama persis dengan siswa
        ada = kon.execute(
            "SELECT 1 FROM siswa WHERE nama = ? COLLATE NOCASE", (nama,)
        ).fetchone()
        if not ada:
            return "", f"Siswa bernama {nama} tidak ditemukan."
        if len(sandi_baru) < 8:
            return "", "Sandi murid minimal 8 karakter."
        try:
            sandi.tambah_akun(nama, sandi_baru, "murid")
        except ValueError as e:
            return "", str(e)
        return f"Akun murid {nama} ditambahkan.", ""

    if aksi == "akun_murid_hapus":
        nama = data.get("nama", "").strip()
        if not nama:
            return "", "Nama tidak boleh kosong."
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
        ok = sandi.setel_sandi_murid(nama, baru)
        if not ok:
            return "", f"Akun {nama} tidak ditemukan."
        return f"Sandi {nama} diperbarui.", ""

    return "", "Aksi tidak dikenal."


def buat_sesi_seed_baru(
    kon, siswa_id: int, level: str | None = None, topik: str | None = None
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
            return basis.buat_sesi(kon, siswa_id, seed, level=level, topik=topik)
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

    def _peran_saya(self) -> str | None:
        if not sandi.wajib_sandi():
            return "guru"
        # cookie dulu
        tok = self._ambil_token()
        if tok:
            got = sesi.ambil(tok)
            if got:
                return got[1]
        kred = self._kredensial()
        if not kred:
            return None
        return sandi.peran_dari(*kred)

    def _lolos_sandi(self) -> bool:
        """Palang guru. Dilewati kalau berkas sandi tidak ada (mode lokal)."""
        if self._peran_saya() == "guru":
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

    def do_GET(self) -> None:  # noqa: N802
        jalur = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"
        if jalur == "/masuk":
            galat = ""
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("galat"):
                galat = q["galat"][0]
            # hilangkan sesi lain di URL supaya tidak membingungkan
            return self._kirim(self._halaman_masuk(galat=galat))
        if jalur == "/murid" or jalur.startswith("/murid/"):
            try:
                with basis.buka() as kon:
                    return self._rute_murid_get(kon, jalur, self.path)
            except (ValueError, IndexError):
                pass
            self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)
            return
        if not self._lolos_sandi():
            return
        try:
            with basis.buka() as kon:
                if jalur == "/":
                    return self._kirim(halaman_utama(kon))
                if jalur.startswith("/sesi/"):
                    return self._kirim(halaman_sesi(kon, int(jalur.split("/")[2])))
                if jalur.startswith("/laporan/"):
                    return self._kirim(halaman_laporan(kon, int(jalur.split("/")[2])))
                if jalur == "/akun":
                    return self._kirim(halaman_akun(kon))
                if jalur.startswith("/lembar/"):
                    bagian = jalur.split("/")
                    guru = len(bagian) > 3 and bagian[3] == "penilaian"
                    isi = halaman_lembar(kon, int(bagian[2]), guru)
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
            "Masuk",
            f'<div class="layout-masuk">'
            f'<div class="masuk-kiri">'
            f'<img src="{ikon.OWL}" alt="Burung hantu lulusan" width="200" height="200">'
            f"<h1>Mesin Latihan</h1>"
            f"<p>Latihan soal pola bilangan untuk SD</p>"
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
        tujuan = "/murid" if peran == "murid" else "/"
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
                if hasil:
                    diagnosa_murid(kon, sesi_id)
            if hasil is None:
                return self._kirim(
                    _halaman("403", "<h1>Bukan sesimu</h1>"), 403
                )
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

        # login + logout — terbuka, tanpa palang
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
            kredensial = self._kredensial()
            pengguna = kredensial[0] if kredensial else "guru"
            with basis.buka() as kon:
                pesan, galat = proses_akun(kon, data, pengguna)
                return self._kirim(halaman_akun(kon, pesan, galat))

        if jalur.startswith("/cerita/"):
            import llm

            try:
                sesi_id = int(jalur.split("/")[2])
            except (ValueError, IndexError):
                return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)
            with basis.buka() as kon:
                _, _, catatan = llm.bungkus_sesi(kon, sesi_id, _soal_dari_baris)
                return self._kirim(halaman_sesi(kon, sesi_id, catatan))

        if jalur.startswith("/sesi-baru/"):
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
                sesi_id = buat_sesi_seed_baru(
                    kon, siswa_id, level=level, topik=pilihan_topik
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

        if not jalur.startswith("/sesi/"):
            return self._kirim(_halaman("404", "<h1>Tidak ada</h1>"), 404)

        panjang = int(self.headers.get("Content-Length", 0))
        mentah = self.rfile.read(panjang).decode("utf-8")
        data = {
            k: v[0]
            for k, v in urllib.parse.parse_qs(mentah, keep_blank_values=True).items()
        }

        sesi_id = int(jalur.split("/")[2])
        with basis.buka() as kon:
            pesan = simpan_sesi(kon, sesi_id, data)
            self._kirim(halaman_sesi(kon, sesi_id, pesan))

    def log_message(self, *a) -> None:  # senyapkan log akses
        pass
