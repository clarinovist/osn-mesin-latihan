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
import urllib.parse
from http.server import BaseHTTPRequestHandler

import basis
from diagnosa import diagnosa
from generator import buat_soal
from templates import REGISTRI, Soal

GAYA = """
* { box-sizing: border-box; }
body {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  margin: 0; padding: 1.2rem; background: #f4f4f6; color: #16161a;
  font-size: 15px; line-height: 1.5;
}
.bungkus { max-width: 940px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 .3rem; }
h2 { font-size: 1.15rem; margin: 1.6rem 0 .6rem; }
a { color: #1a4fd6; }
.sub { color: #666; font-size: .9rem; margin-bottom: 1.2rem; }
.kartu {
  background: #fff; border: 1px solid #d8d8de; border-radius: 8px;
  padding: .9rem 1rem; margin-bottom: .8rem;
}
.soal-kartu { border-left: 4px solid #c8c8d0; }
.soal-kartu.sudah { border-left-color: #2e9e5b; }
.soal-kartu.perlu { border-left-color: #d68a1a; }
.nomor { font-weight: 700; margin-right: .4rem; }
.tipe { color: #777; font-size: .82rem; }
.teks-soal {
  background: #fafafc; border: 1px solid #e6e6ec; border-radius: 5px;
  padding: .5rem .7rem; margin: .5rem 0; white-space: pre-wrap;
  font-size: .93rem;
}
.kunci { font-weight: 700; color: #1a6b3a; }
label { display: block; font-size: .84rem; color: #555; margin: .5rem 0 .15rem; }
input[type=text], textarea, select {
  width: 100%; padding: .45rem .55rem; border: 1px solid #bfbfc9;
  border-radius: 5px; font-size: .95rem; font-family: inherit;
}
textarea { min-height: 3.2rem; resize: vertical; }
.baris { display: flex; gap: .8rem; flex-wrap: wrap; }
.baris > * { flex: 1; min-width: 190px; }
.centang { display: flex; align-items: center; gap: .4rem; margin-top: .5rem;
  font-size: .88rem; }
.centang input { width: auto; }
button {
  background: #1a4fd6; color: #fff; border: 0; border-radius: 6px;
  padding: .65rem 1.3rem; font-size: 1rem; cursor: pointer;
}
button:hover { background: #1540ad; }
.kode {
  display: inline-block; min-width: 1.5rem; text-align: center;
  font-weight: 700; border-radius: 4px; padding: .1rem .45rem;
  font-size: .85rem; color: #fff;
}
.kode.K { background: #c2352b; }
.kode.B { background: #d68a1a; }
.kode.H { background: #2f7ec4; }
.kode.E { background: #7a5bbd; }
.kode.T { background: #5b8f6d; }
.kode.N { background: #77777f; }
.kode.benar { background: #2e9e5b; }
.usulan {
  background: #f0f4ff; border: 1px solid #c9d8ff; border-radius: 5px;
  padding: .45rem .6rem; margin-top: .5rem; font-size: .87rem;
}
.usulan.ragu { background: #fff7e8; border-color: #f0d9a8; }
table { width: 100%; border-collapse: collapse; background: #fff; }
th, td { border: 1px solid #dcdce4; padding: .45rem .6rem; text-align: left;
  font-size: .9rem; }
th { background: #eeeef3; }
.angka { text-align: right; font-variant-numeric: tabular-nums; }
.kosong { color: #888; font-style: italic; }
.pesan {
  background: #e6f6ec; border: 1px solid #a8dcbd; border-radius: 6px;
  padding: .7rem .9rem; margin-bottom: 1rem;
}
.jejak { font-size: .85rem; margin-bottom: 1rem; }
"""

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
    """
    param = json.loads(baris["parameter"])
    fungsi = REGISTRI[baris["template_id"]]
    # parameter tuple disimpan sebagai string; kembalikan ke bentuk semula
    if baris["template_id"] == "siklus_huruf":
        param["pola"] = tuple(param["pola"])
    elif baris["template_id"] == "siklus_warna":
        param["pola"] = tuple(param["pola"].split(","))
    elif baris["template_id"] == "jumlah_siklus":
        param["pola"] = tuple(int(x) for x in param["pola"].split(","))
    return fungsi(**param)


def halaman_utama(kon) -> bytes:
    baris = []
    for s in basis.daftar_siswa(kon):
        sesi = kon.execute(
            """SELECT s.id, s.tanggal, s.seed,
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
            f'<td class="angka">{r["terisi"]}/{r["n"]}</td>'
            f'<td class="tipe">seed {r["seed"]}</td></tr>'
            for r in sesi
        ) or '<tr><td colspan="4" class="kosong">belum ada sesi</td></tr>'

        baris.append(
            f'<div class="kartu"><h2>{html.escape(s["nama"])} '
            f'<span class="tipe">({s["tingkat"]})</span></h2>'
            f'<p><a href="/laporan/{s["id"]}">Lihat laporan &rarr;</a></p>'
            f"<table><tr><th>Sesi</th><th>Tanggal</th><th>Terisi</th>"
            f"<th></th></tr>{item}</table></div>"
        )

    return _halaman(
        "Mesin Latihan",
        "<h1>Mesin Latihan Pola Bilangan</h1>"
        '<p class="sub">Pilih sesi untuk memasukkan hasil, atau buka laporan '
        "untuk melihat tren.</p>" + "".join(baris),
    )


def halaman_sesi(kon, sesi_id: int, pesan: str = "") -> bytes:
    info = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, w.nama, w.id AS siswa_id
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
  <span class="nomor">{b["nomor"]}.</span>{lencana}
  <span class="tipe">{b["template_id"]}</span>
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
        f'<p class="sub">{info["tanggal"]} &middot; seed {info["seed"]} &middot; '
        f'<a href="/laporan/{info["siswa_id"]}">laporan siswa ini</a></p>'
        f"{kabar}"
        f'<form method="post" action="/sesi/{sesi_id}">'
        f'{"".join(kartu)}'
        f'<button type="submit">Simpan &amp; diagnosis</button></form>',
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


def halaman_laporan(kon, siswa_id: int) -> bytes:
    siswa = kon.execute("SELECT * FROM siswa WHERE id = ?", (siswa_id,)).fetchone()
    if not siswa:
        return _halaman("Tidak ada", "<h1>Siswa tidak ditemukan</h1>")

    ring = basis.ringkasan(kon, siswa_id)
    tren = "".join(
        f'<tr><td><a href="/sesi/{r["sesi_id"]}">#{r["sesi_id"]}</a></td>'
        f'<td>{r["tanggal"]}</td>'
        f'<td class="angka">{r["benar"] or 0}/{r["jumlah_soal"]}</td>'
        f'<td class="angka"><b>{r["k"] or 0}</b></td>'
        f'<td class="angka">{r["b"] or 0}</td><td class="angka">{r["h"] or 0}</td>'
        f'<td class="angka">{r["e"] or 0}</td><td class="angka">{r["t"] or 0}</td>'
        f'<td class="angka">{r["n"] or 0}</td></tr>'
        for r in ring
    ) or '<tr><td colspan="9" class="kosong">belum ada sesi dinilai</td></tr>'

    mis = basis.miskonsepsi_berulang(kon, siswa_id)
    daftar_mis = "".join(
        f'<tr><td>{html.escape(m["alasan"] or m["malrule_id"])}</td>'
        f'<td class="tipe">{m["template_id"]}</td>'
        f'<td class="angka">{m["jumlah_sesi"]}</td>'
        f'<td class="tipe">{m["pertama"]} &rarr; {m["terakhir"]}</td></tr>'
        for m in mis
    ) or ('<tr><td colspan="4" class="kosong">belum ada miskonsepsi '
          "tercatat</td></tr>")

    peta = basis.peta_materi_baru(kon, siswa_id)
    daftar_peta = "".join(
        f'<tr><td>{p["template_id"]}</td><td class="angka">{p["kali"]}</td>'
        f'<td class="tipe">{p["terakhir"]}</td></tr>'
        for p in peta
    ) or '<tr><td colspan="3" class="kosong">tidak ada</td></tr>'

    return _halaman(
        f"Laporan {siswa['nama']}",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f'<h1>Laporan — {html.escape(siswa["nama"])}</h1>'
        f'<p class="sub">Yang dipantau adalah <b>jumlah K</b>, bukan skor. '
        f"Anak dengan 9 H skor 3 lebih siap daripada anak dengan 3 K skor 9.</p>"
        f'<div class="kartu"><h2>Tren per sesi</h2><table>'
        f"<tr><th>Sesi</th><th>Tanggal</th><th>Benar</th><th>K</th><th>B</th>"
        f"<th>H</th><th>E</th><th>T</th><th>N</th></tr>{tren}</table></div>"
        f'<div class="kartu"><h2>Miskonsepsi yang bertahan</h2>'
        f'<p class="sub">Dihitung per gagasan keliru, bukan per soal. Satu '
        f"miskonsepsi yang muncul di tiga soal tetap satu baris. Yang muncul "
        f"di lebih dari satu sesi berarti belum tuntas meski angkanya sudah "
        f"diganti.</p><table>"
        f"<tr><th>Miskonsepsi</th><th>Tipe soal</th><th>Jumlah sesi</th>"
        f"<th>Rentang</th></tr>{daftar_mis}</table></div>"
        f'<div class="kartu"><h2>Materi yang belum diajarkan</h2>'
        f'<p class="sub">Dari soal yang dicentang "belum pernah lihat". Ini '
        f"peta urutan belajar, bukan daftar kegagalan.</p><table>"
        f"<tr><th>Tipe soal</th><th>Berapa kali</th><th>Terakhir</th></tr>"
        f"{daftar_peta}</table></div>",
    )


class Penangan(BaseHTTPRequestHandler):
    def _kirim(self, isi: bytes, kode: int = 200) -> None:
        self.send_response(kode)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        self.wfile.write(isi)

    def do_GET(self) -> None:  # noqa: N802
        jalur = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"
        try:
            with basis.buka() as kon:
                if jalur == "/":
                    return self._kirim(halaman_utama(kon))
                if jalur.startswith("/sesi/"):
                    return self._kirim(halaman_sesi(kon, int(jalur.split("/")[2])))
                if jalur.startswith("/laporan/"):
                    return self._kirim(halaman_laporan(kon, int(jalur.split("/")[2])))
        except (ValueError, IndexError):
            pass
        self._kirim(_halaman("404", "<h1>Halaman tidak ada</h1>"), 404)

    def do_POST(self) -> None:  # noqa: N802
        jalur = urllib.parse.urlparse(self.path).path.rstrip("/")
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
