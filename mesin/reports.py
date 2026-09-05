"""Halaman laporan per anak + diagnosa jawaban.

Dipecah dari web.py (refactor 31 Aug 2026) — fungsi pindah utuh, perilaku
identik. Frame halaman diimpor dari teacher_pages.
"""

from __future__ import annotations

import html
from datetime import datetime

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
# Dipakai panel "Cara membaca laporan" — bebas jargon teknis (malrule,
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


NAMA_TIPE_SOAL = {
    "benar_salah_pengandaian": "Pengandaian benar atau salah",
    "luas_kotak_satuan": "Menghitung luas dengan kotak satuan",
    "simetri_bangun": "Simetri bangun datar",
    "soal_umur": "Soal tentang umur",
    "fpb_kpk_hubungan": "Hubungan FPB dan KPK",
}

BULAN_PENDEK = (
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
)

SARAN_TIPE_SOAL = {
    "benar_salah_pengandaian": (
        "Baca syarat satu per satu, lalu uji apakah kesimpulannya selalu benar."
    ),
    "luas_kotak_satuan": (
        "Hitung kotak satuan per baris, lalu jumlahkan semua baris yang terisi."
    ),
    "simetri_bangun": (
        "Lipat atau bayangkan bangun dilipat untuk mencari bagian yang berhimpit."
    ),
    "soal_umur": (
        "Buat garis waktu sederhana: umur sekarang, selisih umur, lalu tahun yang ditanya."
    ),
}

SARAN_TOPIK = {
    "logika": "Minta anak menjelaskan alasan setiap jawaban dengan satu kalimat.",
    "geometri-datar": "Gunakan gambar atau benda nyata sebelum beralih ke hitungan.",
    "statistika": "Mulai dari tabel kecil, lalu minta anak menceritakan arti datanya.",
    "pola-bilangan": "Minta anak menyebut perubahan antarangka sebelum meneruskan pola.",
}


def _nama_tipe_soal(template_id: str) -> str:
    """Terjemahkan ID internal menjadi nama yang wajar bagi orang tua."""
    return NAMA_TIPE_SOAL.get(
        template_id,
        template_id.replace("_", " ").replace("-", " ").capitalize(),
    )


def _rapikan_kalimat(teks: str) -> str:
    """Kapitalisasi awal dan akhiri kalimat tanpa merusak singkatan."""
    bersih = teks.strip()
    if not bersih:
        return ""
    hasil = bersih[0].upper() + bersih[1:]
    return hasil if hasil.endswith((".", "!", "?")) else hasil + "."


def _tanggal_pendek(nilai) -> str:
    """Tanggal Indonesia ringkas; data warisan yang aneh tetap tampil aman."""
    mentah = str(nilai or "")
    try:
        tanggal = datetime.strptime(mentah, "%Y-%m-%d")
    except ValueError:
        return f'<span class="tanggal-ringkas">{html.escape(mentah or "—")}</span>'
    label = f"{tanggal.day} {BULAN_PENDEK[tanggal.month - 1]} {tanggal.year}"
    return (
        f'<time class="tanggal-ringkas" datetime="{html.escape(mentah)}">'
        f"{label}</time>"
    )


def _saran_latihan(template_id: str, topik_id: str, materi_baru: bool = False) -> str:
    """Satu tindakan pendek, spesifik bila tipe dikenal dan aman bila warisan."""
    khusus = SARAN_TIPE_SOAL.get(template_id)
    if khusus:
        awalan = "Kenalkan dengan contoh sederhana. " if materi_baru else ""
        return awalan + khusus
    saran_topik = SARAN_TOPIK.get(topik_id)
    if saran_topik:
        return saran_topik
    if materi_baru:
        return "Kenalkan satu contoh bersama, lalu biarkan anak mencoba satu soal serupa."
    return "Ulangi satu contoh bersama, lalu coba dua soal baru dengan angka berbeda."


def _ringkasan_ortu(nama: str, ring, mis) -> str:
    """Ringkasan singkat: kondisi, pola berulang, dan arah berikutnya."""
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
    if not mis:
        return (
            f"<p><b>{html.escape(nama)}</b> sempat mengalami kekeliruan konsep, "
            f"tetapi belum cukup data untuk menetapkan satu topik sebagai fokus. "
            f"Amati apakah pola yang sama muncul lagi di sesi berikutnya.</p>"
        )
    topik_berulang: dict[str, int] = {}
    for m in mis:
        topik_id = str(m["topik"])
        topik_berulang[topik_id] = topik_berulang.get(topik_id, 0) + int(
            m["jumlah_sesi"] or 0
        )
    fokus = max(topik_berulang, key=lambda topik: topik_berulang[topik])
    fokus_nama = _nama_topik(fokus)
    pola_fokus = [m for m in mis if str(m["topik"]) == fokus]
    pola_utama = max(
        pola_fokus,
        key=lambda m: (int(m["jumlah_sesi"] or 0), int(m["kemunculan"] or 0)),
    )
    nama_tipe = _nama_tipe_soal(str(pola_utama["template_id"]))
    return (
        f"<p>Untuk <b>{html.escape(nama)}</b>, pola berulang yang paling perlu "
        f"diperhatikan adalah <b>{html.escape(nama_tipe)}</b>. Mulai dari topik "
        f"<b>{html.escape(fokus_nama)}</b>; langkah konkretnya ada pada prioritas "
        f"latihan di bawah.</p>"
    )


def _kartu_kamus() -> str:
    baris = "".join(
        f'<li><span class="dot {"kuat" if kode == "BENAR" else ("salah" if kode == "K" else "lemah")}"></span>'
        f"<span><b>{html.escape(sebutan)}</b> — {html.escape(arti)}</span></li>"
        for kode, sebutan, arti in KAMUS_ORTU
    )
    return (
        f'<details class="kartu cara-baca-laporan"><summary><h2>'
        f"Cara membaca laporan</h2>"
        f'<span class="sub">Arti istilah penilaian</span></summary>'
        f'<p class="sub">Tiap soal dinilai dengan salah satu sebutan ini:</p>'
        f'<ul class="diagnosis-lis">{baris}</ul></details>'
    )


def _kartu_prioritas(mis, total_k: int) -> str:
    """Kesalahan konsep berulang saja; materi baru tidak dicampur di sini."""
    item = []
    for m in mis:
        nama = _nama_tipe_soal(m["template_id"])
        topik = _nama_topik(m["topik"])
        alasan = m["alasan"] or "cara yang dipakai belum tepat"
        saran = _saran_latihan(m["template_id"], m["topik"])
        item.append(
            '<li class="aksi-laporan salah">'
            f'<div><b>{html.escape(nama)}</b>'
            f'<span class="meta-laporan">{html.escape(topik)} · muncul di '
            f'{m["jumlah_sesi"]} sesi</span></div>'
            f'<p>{html.escape(_rapikan_kalimat(alasan))}</p>'
            f'<p><b>Yang bisa dilakukan:</b> {html.escape(saran)}</p></li>'
        )
    if not item:
        pesan = (
            f"Ada {total_k} kekeliruan konsep, tetapi polanya belum berulang. "
            "Amati lagi di sesi berikutnya sebelum memilih latihan khusus."
            if total_k else
            "Belum ada kekeliruan konsep yang berulang. Pertahankan cara belajar saat ini."
        )
        item.append(f'<li class="aksi-laporan kuat"><p>{pesan}</p></li>')
    return (
        '<section class="kartu"><h2>Prioritas latihan</h2>'
        '<p class="sub">Fokus pada pola keliru yang muncul kembali, bukan semua jawaban salah.</p>'
        f'<ul class="daftar-aksi-laporan">{"".join(item)}</ul></section>'
    )


def _kartu_materi_baru(peta) -> str:
    """Kode T sebagai urutan belajar, terpisah tegas dari kesalahan anak."""
    item = []
    for p in peta:
        nama = _nama_tipe_soal(p["template_id"])
        topik = _nama_topik(p["topik"])
        saran = _saran_latihan(p["template_id"], p["topik"], materi_baru=True)
        item.append(
            '<li class="aksi-laporan baru">'
            f'<div><b>{html.escape(nama)}</b>'
            f'<span class="meta-laporan">{html.escape(topik)} · ditemui '
            f'{p["kali"]}×</span></div>'
            f'<p><b>Yang bisa dilakukan:</b> {html.escape(saran)}</p></li>'
        )
    if not item:
        item.append(
            '<li class="aksi-laporan kuat"><p>Tidak ada materi baru yang perlu '
            "dikenalkan dari sesi-sesi ini.</p></li>"
        )
    return (
        '<section class="kartu"><h2>Materi berikutnya untuk dikenalkan</h2>'
        '<p class="sub">Bagian ini belum familiar bagi anak. Ini bukan kesalahan '
        'anak, melainkan petunjuk urutan belajar berikutnya.</p>'
        f'<ul class="daftar-aksi-laporan">{"".join(item)}</ul></section>'
    )


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

    mis_semua = database.miskonsepsi_berulang(kon, siswa_id)
    # Prioritas latihan berarti pola yang bertahan lintas sesi. Dua kemunculan
    # dalam satu sesi belum cukup untuk menyimpulkan pola berulang.
    mis = [m for m in mis_semua if m["jumlah_sesi"] > 1]
    if mis:
        jumlah_per_topik: dict[str, int] = {}
        for m in mis:
            topik_id = str(m["topik"])
            jumlah_per_topik[topik_id] = jumlah_per_topik.get(topik_id, 0) + int(
                m["jumlah_sesi"] or 0
            )
        topik_fokus = max(
            jumlah_per_topik, key=lambda topik: jumlah_per_topik[topik]
        )
        topik_fokus_nama = _nama_topik(topik_fokus)
    else:
        topik_fokus_nama = "Belum cukup data"

    tren = "".join(
        f'<tr><td data-label="Sesi"><a href="/sesi/{r["sesi_id"]}">#{r["sesi_id"]}</a></td>'
        f'<td data-label="Tanggal">{_tanggal_pendek(r["tanggal"])}</td>'
        f'<td class="tipe" data-label="Level">{html.escape(str(_ambil(r, "level", LEVEL_BAWAAN)))}</td>'
        f'<td data-label="Topik">{html.escape(_nama_topik(_ambil(r, "topik", TOPIK_BAWAAN) or TOPIK_BAWAAN))}</td>'
        f'<td class="angka" data-label="Benar">{r["benar"] or 0}/{r["jumlah_soal"]}</td>'
        f'<td class="angka" data-label="K"><b>{r["k"] or 0}</b></td>'
        f'<td class="angka" data-label="B">{r["b"] or 0}</td><td class="angka" data-label="H">{r["h"] or 0}</td>'
        f'<td class="angka" data-label="E">{r["e"] or 0}</td><td class="angka" data-label="T">{r["t"] or 0}</td>'
        f'<td class="angka" data-label="N">{r["n"] or 0}</td></tr>'
        for r in ring
    ) or '<tr><td colspan="11" class="kosong">belum ada sesi dinilai</td></tr>'

    daftar_mis = "".join(
        f'<tr><td>{html.escape(m["alasan"] or "Cara yang dipakai belum tepat")}</td>'
        f'<td>{html.escape(_nama_tipe_soal(m["template_id"]))}</td>'
        f'<td>{html.escape(_nama_topik(m["topik"]))}</td>'
        f'<td class="angka">{m["jumlah_sesi"]}</td>'
        f'<td>{_tanggal_pendek(m["pertama"])} &rarr; '
        f'{_tanggal_pendek(m["terakhir"])}</td></tr>'
        for m in mis
    ) or ('<tr><td colspan="5" class="kosong">belum ada kekeliruan '
          "yang bertahan</td></tr>")

    peta = database.peta_materi_baru(kon, siswa_id)
    daftar_peta = "".join(
        f'<tr><td>{html.escape(_nama_tipe_soal(p["template_id"]))}</td>'
        f'<td>{html.escape(_nama_topik(p["topik"]))}</td>'
        f'<td class="angka">{p["kali"]}</td>'
        f'<td>{_tanggal_pendek(p["terakhir"])}</td></tr>'
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
        f'<div class="kartu ringkasan-laporan"><h2>Ringkasan untuk orang tua</h2>'
        f"{_ringkasan_ortu(siswa['nama'], ring, mis)}</div>"
        f'<div class="kartu-stat">'
        f'<div class="stat"><div class="angka-besar">{total_sesi}</div>'
        f'<div class="stat-label">sesi diikuti</div></div>'
        f'<div class="stat"><div class="angka-besar">{total_k}</div>'
        f'<div class="stat-label">kekeliruan konsep</div></div>'
        f'<div class="stat"><div class="stat-nilai-utama">'
        f"{html.escape(topik_fokus_nama)}</div>"
        f'<div class="stat-label">fokus latihan</div></div>'
        f"</div>"
        f'<div class="grid-tindakan-laporan">'
        f"{_kartu_prioritas(mis, total_k)}"
        f"{_kartu_materi_baru(peta)}"
        f"</div>"
        f'<div class="kartu"><h2>Perkembangan jawaban tepat</h2>'
        f'<p class="sub skor-sekunder"><b>{persen}% jawaban tepat</b> dari '
        f'{soal_sum} soal pada {total_sesi} sesi. Angka ini membantu melihat '
        f"tren, tetapi tidak menentukan sendiri apa yang perlu dilatih.</p>"
        f'<div class="chart-wrap">{blok_chart}</div></div>'
        f"{_kartu_kamus()}"
        f'<details class="kartu detail-teknis-laporan"><summary><h2>'
        f"Detail per sesi (teknis)</h2>"
        f'<span class="sub">Rincian untuk guru</span></summary>'
        f'<p class="sub">Dalam rincian ini, jumlah <b>K</b> yang berulang '
        f"lebih penting untuk menentukan latihan, bukan skor semata.</p>"
        f'<p class="legenda-teknis"><b>K = keliru konsep</b> · '
        f'B = salah baca · H = salah hitung · E = salah tulis akhir · '
        f"T = belum pernah lihat · N = menebak</p>"
        f'<div class="tabel-wrap tabel-tren"><h3>Tren per sesi</h3><table>'
        f'<caption class="sr-only">Rincian hasil dan jenis kekeliruan setiap sesi</caption>'
        f'<thead><tr><th scope="col">Sesi</th><th scope="col">Tanggal</th>'
        f'<th scope="col">Level</th><th scope="col">Topik</th>'
        f'<th scope="col">Benar</th><th scope="col">K</th>'
        f'<th scope="col">B</th><th scope="col">H</th>'
        f'<th scope="col">E</th><th scope="col">T</th>'
        f'<th scope="col">N</th></tr></thead><tbody>{tren}</tbody></table></div>'
        f'<div class="tabel-wrap"><h3>Yang perlu dilatih</h3>'
        f'<p class="sub">Rincian pola keliru yang sama dan muncul kembali.</p>'
        f'<table><caption class="sr-only">Pola keliru yang berulang lintas sesi</caption>'
        f'<thead><tr><th scope="col">Kekeliruan</th>'
        f'<th scope="col">Tipe soal</th><th scope="col">Topik</th>'
        f'<th scope="col">Jumlah sesi</th><th scope="col">Rentang</th>'
        f'</tr></thead><tbody>{daftar_mis}</tbody></table></div>'
        f'<div class="tabel-wrap"><h3>Materi baru untuk anak</h3>'
        f'<p class="sub">Rincian soal yang ditandai belum pernah dilihat.</p>'
        f'<table><caption class="sr-only">Materi yang belum pernah dilihat anak</caption>'
        f'<thead><tr><th scope="col">Tipe soal</th>'
        f'<th scope="col">Topik</th><th scope="col">Berapa kali</th>'
        f'<th scope="col">Terakhir</th></tr></thead>'
        f'<tbody>{daftar_peta}</tbody></table></div></details>',
        ident=(pengguna, peran) if pengguna else None,
        stitch=True,
    )
