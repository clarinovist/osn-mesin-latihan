"""Halaman laporan per anak + diagnosa jawaban.

Dipecah dari web.py (refactor 31 Aug 2026) — fungsi pindah utuh, perilaku
identik. Frame halaman diimpor dari teacher_pages.
"""

from __future__ import annotations

import html

import database
import design_tokens as T
from diagnosis import diagnosa
from generator import LEVEL_BAWAAN
from topics import TOPIK_BAWAAN
from teacher_pages import _ambil, _halaman, _soal_dari_baris



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
    # tidak salah menuduh. Storage tetap cara='' — lihat students.AWALAN_DRILL.
    import students  # impor terlambat: modul halaman tidak boleh mengimpor students di atas

    baris_mode = kon.execute(
        "SELECT mode FROM sesi WHERE id = ?", (sesi_id,)
    ).fetchone()
    drill = bool(baris_mode and baris_mode["mode"] == "drill")

    def _cara(b) -> str:
        cara = b["cara"] or ""
        return students.AWALAN_DRILL + cara if drill else cara

    for b in database.isi_sesi(kon, sesi_id):
        if b["jawaban_id"] is None:
            continue  # anak melewati soal ini: biarkan tanpa baris
        if b["manual"] == 1:
            # Segarkan usulan mesin saja; vonis guru tidak disentuh.
            soal = _soal_dari_baris(b)
            u = diagnosa(
                b["kunci"], b["jawaban"] or "", _cara(b),
                b["restatement"] or "", bool(b["belum_pernah"]),
                database.malrule_soal(kon, b["soal_id"]),
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
            database.malrule_soal(kon, b["soal_id"]),
            soal.minta_restatement,
        )
        database.simpan_diagnosis(
            kon, b["jawaban_id"],
            benar=u.benar, kode_usulan=u.kode, kode_final=u.kode,
            malrule_id=u.malrule_id, alasan=u.alasan, manual=False,
        )
        jumlah += 1
    return jumlah

def _chart_tren(ring) -> str:
    """SVG line chart % benar per sesi (mockup guru-laporan).

    ring diurutkan DESC oleh database.ringkasan; dibalik supaya sumbu x
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

    ring = database.ringkasan(kon, siswa_id)
    total_sesi = len(ring)
    benar_sum = sum(r["benar"] or 0 for r in ring)
    soal_sum = sum(r["jumlah_soal"] or 0 for r in ring)
    persen = round(benar_sum / soal_sum * 100) if soal_sum else 0
    topik_lemah = _topik_terlemah(ring)

    tren = "".join(
        f'<tr><td data-label="Sesi"><a href="/sesi/{r["sesi_id"]}">#{r["sesi_id"]}</a></td>'
        f'<td data-label="Tanggal">{r["tanggal"]}</td>'
        f'<td class="tipe" data-label="Level">{_ambil(r, "level", LEVEL_BAWAAN)}</td>'
        f'<td class="tipe" data-label="Topik">{_ambil(r, "topik", TOPIK_BAWAAN)}</td>'
        f'<td class="angka" data-label="Benar">{r["benar"] or 0}/{r["jumlah_soal"]}</td>'
        f'<td class="angka" data-label="K"><b>{r["k"] or 0}</b></td>'
        f'<td class="angka" data-label="B">{r["b"] or 0}</td><td class="angka" data-label="H">{r["h"] or 0}</td>'
        f'<td class="angka" data-label="E">{r["e"] or 0}</td><td class="angka" data-label="T">{r["t"] or 0}</td>'
        f'<td class="angka" data-label="N">{r["n"] or 0}</td></tr>'
        for r in ring
    ) or '<tr><td colspan="11" class="kosong">belum ada sesi dinilai</td></tr>'

    mis = database.miskonsepsi_berulang(kon, siswa_id)
    daftar_mis = "".join(
        f'<tr><td>{html.escape(m["alasan"] or m["malrule_id"])}</td>'
        f'<td class="tipe">{m["template_id"]}</td>'
        f'<td class="tipe">{html.escape(m["topik"])}</td>'
        f'<td class="angka">{m["jumlah_sesi"]}</td>'
        f'<td class="tipe">{m["pertama"]} &rarr; {m["terakhir"]}</td></tr>'
        for m in mis
    ) or ('<tr><td colspan="5" class="kosong">belum ada miskonsepsi '
          "tercatat</td></tr>")

    peta = database.peta_materi_baru(kon, siswa_id)
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
        f'<div class="tabel-wrap tabel-tren"><div class="kartu"><h2>Tren per sesi</h2><table>'
        f"<thead><tr><th>Sesi</th><th>Tanggal</th><th>Level</th><th>Topik</th><th>Benar</th><th>K</th>"
        f"<th>B</th><th>H</th><th>E</th><th>T</th><th>N</th></tr></thead><tbody>{tren}</tbody></table></div></div>"
        f'<div class="tabel-wrap"><div class="kartu"><h2>Miskonsepsi yang bertahan</h2>'
        f'<p class="sub">Dihitung per gagasan keliru, bukan per soal. Satu '
        f"miskonsepsi yang muncul di tiga soal tetap satu baris. Yang muncul "
        f"di lebih dari satu sesi berarti belum tuntas meski angkanya sudah "
        f"diganti.</p><table>"
        f"<tr><th>Miskonsepsi</th><th>Tipe soal</th><th>Topik</th><th>Jumlah sesi</th>"
        f"<th>Rentang</th></tr>{daftar_mis}</table></div></div>"
        f'<div class="tabel-wrap"><div class="kartu"><h2>Materi yang belum diajarkan</h2>'
        f'<p class="sub">Dari soal yang dicentang "belum pernah lihat". Ini '
        f"peta urutan belajar, bukan daftar kegagalan.</p><table>"
        f"<tr><th>Tipe soal</th><th>Topik</th><th>Berapa kali</th><th>Terakhir</th></tr>"
        f"{daftar_peta}</table></div></div>",
        ident=(pengguna, peran) if pengguna else None,
        stitch=True,
    )
