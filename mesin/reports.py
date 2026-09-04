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


# Kamus kode diagnosis dalam bahasa sehari-hari (untuk orang tua).
# Kunci = kode di basis data; nilai = (sebutan ramah, arti 1 kalimat).
# Dipakai kartu "Arti nilai anak" — bebas jargon teknis (malrule,
# miskonsepsi, diagnosis tidak boleh muncul di sini).
KAMUS_ORTU = (
    ("BENAR", "Tepat", "jawabannya cocok dengan kunci."),
    ("K", "Keliru konsep (salah konsep)", "caranya belum tepat — perlu diajar ulang, bukan dimarahi."),
    ("B", "Salah baca soal", "yang ditanya disalahartikan — latih membaca soal, bukan materinya."),
    ("H", "Salah hitung", "caranya sudah benar, berhitungnya meleset — latihan saja."),
    ("E", "Salah tulis akhir", "hitungan benar tapi salah menyalin ke jawaban — kecerobohan, bukan tak paham."),
    ("T", "Belum pernah lihat", "tipe soalnya memang belum diajarkan — bukan kegagalan anak."),
    ("N", "Menebak", "jawab tanpa menunjukkan cara — tanyakan langsung sebelum dinilai."),
)


def _nama_topik(topik_id: str) -> str:
    """Nama ramah topik; id mentah bila tak dikenal (data warisan).

    topics.ambil melempar untuk topik asing — laporan warisan tidak boleh
    500 hanya karena satu sesi menyimpan topik yang sudah tidak ada.
    """
    from topics import ambil

    try:
        return ambil(topik_id).nama
    except KeyError:
        return topik_id


def _ringkasan_ortu(nama: str, ring, mis) -> str:
    """Tiga kalimat otomatis dari data nyata: kondisi, pola, langkah berikut.

    K=0 total -> kalimat perayaan (tanpa kata yang menakuti). Tanpa sesi ->
    ajakan membuat sesi pertama. Topik disebut dengan nama ramah.
    """
    if not ring:
        return (
            f"<p><b>{html.escape(nama)}</b> belum punya sesi yang dinilai. "
            f"Buat sesi latihan dulu — ringkasannya muncul di sini setelah "
            f"ada hasil.</p>"
        )
    total_k = sum(r["k"] or 0 for r in ring)
    if not total_k:
        return (
            f"<p><b>{html.escape(nama)}</b> belum menunjukkan kekeliruan konsep "
            f"di sesi-sesi terakhir — pertahankan! "
            f"Tantang dengan topik atau level berikutnya bila latihan "
            f"sudah terasa mudah.</p>"
        )
    hitung = {"K": 0, "B": 0, "H": 0, "E": 0, "T": 0, "N": 0}
    for r in ring:
        for kode in hitung:
            hitung[kode] += r[kode.lower()] or 0
    dominan = max(hitung, key=hitung.get)
    sebutan = dict((k, s) for k, s, _ in KAMUS_ORTU).get(dominan, dominan)
    lemah = _topik_terlemah(ring)
    lemah_nama = _nama_topik(lemah) if lemah != "tidak ada" else "belum terlihat"
    pola = (
        f"Pola yang paling sering muncul: <b>{html.escape(sebutan)}</b>."
        if hitung[dominan]
        else "Belum ada pola kesalahan yang menonjol."
    )
    saran = (
        f"Latih ulang topik <b>{html.escape(lemah_nama)}</b> dengan soal baru, "
        f"lalu lihat apakah kekeliruannya hilang di sesi berikutnya."
        if lemah != "tidak ada"
        else "Lanjutkan latihan seperti biasa."
    )
    n_sesi = len(ring)
    return (
        f"<p>Dari <b>{n_sesi} sesi</b> terakhir, <b>{html.escape(nama)}</b> "
        f"punya <b>{total_k} kekeliruan konsep</b> yang perlu dilatih — "
        f"angka inilah yang dipantau, bukan skor benarnya.</p>"
        f"<p>{pola}</p>"
        f"<p>Langkah berikut: {saran}</p>"
    )


def _kartu_kamus() -> str:
    baris = "".join(
        f'<li><span class="dot {"kuat" if kode == "BENAR" else ("salah" if kode == "K" else "lemah")}"></span>'
        f"<span><b>{html.escape(sebutan)}</b> — {html.escape(arti)}</span></li>"
        for kode, sebutan, arti in KAMUS_ORTU
    )
    return (
        f'<div class="kartu"><h2>Arti nilai anak</h2>'
        f'<p class="sub">Tiap soal dinilai dengan salah satu sebutan ini:</p>'
        f'<ul class="diagnosis-lis">{baris}</ul></div>'
    )

def _daftar_diagnosis(mis, peta, total_k: int = 0) -> str:
    """Daftar diagnosis dengan dot warna (mockup guru-laporan).

    Sumber data nyata: miskonsepsi_berulang (kode K -> titik coral) dan
    peta_materi_baru (kode T -> titik amber). Tidak ada data yang dikarang:
    kuat (teal) hanya muncul kalau tidak ada kekeliruan sama sekali.
    Bahasa untuk orang tua — kata "miskonsepsi"/"salah konsep" tidak dipakai
    di sini (artinya ada di kartu kamus).

    `total_k` = jumlah K di ringkasan. K yang diberi manual oleh guru tanpa
    malrule tidak masuk `mis` (dihitung per malrule_id) — tanpa ini kartunya
    bilang "belum ada kekeliruan" sementara ringkasan bilang ada K.
    """
    item = []
    for m in mis:
        item.append(
            f'<li><span class="dot salah"></span>'
            f'<span><b>{html.escape(m["alasan"] or m["malrule_id"])}</b> — '
            f"perlu dilatih ulang ({m['jumlah_sesi']} sesi)</span></li>"
        )
    for p in peta:
        item.append(
            f'<li><span class="dot lemah"></span>'
            f'<span><b>{html.escape(p["template_id"])}</b> — belum diajarkan '
            f'({p["kali"]}×)</span></li>'
        )
    if not item:
        if total_k:
            return ('<li><span class="dot salah"></span>'
                    f'<span>Ada <b>{total_k} kekeliruan konsep</b> yang perlu '
                    'dilatih — rinciannya ada di tabel teknis di bawah.</span></li>')
        return ('<li><span class="dot kuat"></span>'
                '<span>Belum ada kekeliruan yang bertahan — polanya kuat.</span></li>')
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
    topik_lemah_nama = _nama_topik(topik_lemah) if topik_lemah != "tidak ada" else "tidak ada"

    tren = "".join(
        f'<tr><td data-label="Sesi"><a href="/sesi/{r["sesi_id"]}">#{r["sesi_id"]}</a></td>'
        f'<td data-label="Tanggal">{r["tanggal"]}</td>'
        f'<td class="tipe" data-label="Level">{_ambil(r, "level", LEVEL_BAWAAN)}</td>'
        f'<td class="tipe" data-label="Topik">{html.escape(_nama_topik(_ambil(r, "topik", TOPIK_BAWAAN) or TOPIK_BAWAAN))} <span class="sub">{html.escape(_ambil(r, "topik", TOPIK_BAWAAN) or TOPIK_BAWAAN)}</span></td>'
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
        f'<td class="tipe">{html.escape(_nama_topik(m["topik"]))} <span class="sub">{html.escape(m["topik"])}</span></td>'
        f'<td class="angka">{m["jumlah_sesi"]}</td>'
        f'<td class="tipe">{m["pertama"]} &rarr; {m["terakhir"]}</td></tr>'
        for m in mis
    ) or ('<tr><td colspan="5" class="kosong">belum ada kekeliruan '
          "yang bertahan</td></tr>")

    peta = database.peta_materi_baru(kon, siswa_id)
    daftar_peta = "".join(
        f'<tr><td>{p["template_id"]}</td>'
        f'<td class="tipe">{html.escape(_nama_topik(p["topik"]))} <span class="sub">{html.escape(p["topik"])}</span></td>'
        f'<td class="angka">{p["kali"]}</td>'
        f'<td class="tipe">{p["terakhir"]}</td></tr>'
        for p in peta
    ) or '<tr><td colspan="4" class="kosong">tidak ada</td></tr>'

    chart = _chart_tren(ring)
    blok_chart = chart or (
        '<p class="sub">Belum cukup data untuk menggambar tren — '
        "butuh minimal 2 sesi.</p>"
    )
    total_k = sum(r["k"] or 0 for r in ring)

    return _halaman(
        f"Laporan {siswa['nama']}",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f'<h1>Laporan — {html.escape(siswa["nama"])}</h1>'
        f'<div class="kartu"><h2>Ringkasan untuk orang tua</h2>'
        f"{_ringkasan_ortu(siswa['nama'], ring, mis)}</div>"
        f"{_kartu_kamus()}"
        f'<p class="sub">Yang dipantau adalah <b>jumlah K</b>, bukan skor. '
        f"Anak dengan 9 H skor 3 lebih siap daripada anak dengan 3 K skor 9.</p>"
        f'<div class="kartu-stat">'
        f'<div class="stat"><div class="angka-besar">{total_sesi}</div>'
        f'<div class="stat-label">sesi</div></div>'
        f'<div class="stat"><div class="angka-besar">{persen}%</div>'
        f'<div class="stat-label">benar</div></div>'
        f'<div class="stat"><div class="stat-nilai-utama">'
        f"{html.escape(topik_lemah_nama)}</div>"
        f'<div class="stat-label">topik terlemah</div></div>'
        f"</div>"
        f'<div class="layout-laporan">'
        f'<div class="kartu"><h2>Perkembangan % benar per sesi</h2>'
        f"{blok_chart}</div>"
        f'<div class="kartu"><h2>Perlu perhatian</h2>'
        f'<ul class="diagnosis-lis">{_daftar_diagnosis(mis, peta, total_k)}</ul></div>'
        f"</div>"
        f'<details class="kartu"><summary><h2 style="display:inline">Detail per sesi (teknis)</h2>'
        f'<p class="sub">Rincian angka per sesi untuk guru — ringkasannya '
        f"sudah ada di atas.</p></summary>"
        f'<div class="tabel-wrap tabel-tren"><div class="kartu"><h2>Tren per sesi</h2><table>'
        f"<thead><tr><th>Sesi</th><th>Tanggal</th><th>Level</th><th>Topik</th><th>Benar</th><th>K</th>"
        f"<th>B</th><th>H</th><th>E</th><th>T</th><th>N</th></tr></thead><tbody>{tren}</tbody></table></div></div>"
        f'<div class="tabel-wrap"><div class="kartu"><h2>Yang perlu dilatih</h2>'
        f'<p class="sub">Kekeliruan yang sama dan muncul di lebih dari satu '
        f"sesi berarti belum tuntas meski angkanya sudah diganti. "
        f"Dihitung per gagasan keliru, bukan per soal.</p><table>"
        f"<tr><th>Kekeliruan</th><th>Tipe soal</th><th>Topik</th><th>Jumlah sesi</th>"
        f"<th>Rentang</th></tr>{daftar_mis}</table></div></div>"
        f'<div class="tabel-wrap"><div class="kartu"><h2>Materi baru untuk anak</h2>'
        f'<p class="sub">Dari soal yang dicentang "belum pernah lihat". Ini '
        f"peta urutan belajar, bukan daftar kegagalan.</p><table>"
        f"<tr><th>Tipe soal</th><th>Topik</th><th>Berapa kali</th><th>Terakhir</th></tr>"
        f"{daftar_peta}</table></div></div></details>",
        ident=(pengguna, peran) if pengguna else None,
        stitch=True,
    )
