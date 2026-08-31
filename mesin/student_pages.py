"""Halaman sisi anak: kerjakan sesi, daftar sesi ber-status.

Dipecah dari students.py (refactor 31 Aug 2026) — fungsi pindah utuh,
perilaku identik. students.py kini lapisan data; modul ini lapisan tampilan
dan mengimpor dari sana (satu arah). Palang tetap: halaman anak TIDAK boleh
menampilkan kunci, malrule, atau diagnosis — dijaga test_palang_*.
"""

from __future__ import annotations

import json

import design_tokens as T
from topics import Topik, dari_sesi
from students import (
    AWALAN_PILIHAN,
    PILIHAN_CARA,
    _ambil_topik,
    _escape,
    sesi_murid,
    soal_murid,
)


def _badan_teks(teks: str) -> str:
    """Pecah teks soal: baris terakhir = pertanyaan (ditonjolkan), sisanya
    badan soal. Aturan yang sama dengan render._badan_soal untuk teks biasa.

    Tanpa pemecahan ini, pengantar dan pertanyaan menyatu dalam satu div
    berukuran sama — anak tidak tahu mana yang sebenarnya ditanya.
    """
    baris = [b.strip() for b in teks.split("\n") if b.strip()]
    if len(baris) == 1:
        return f'<div class="teks">{_escape(baris[0])}</div>'
    return "".join(
        f'<div class="{"tanya" if i == len(baris) - 1 else "teks"}">'
        f"{_escape(b)}</div>"
        for i, b in enumerate(baris)
    )

CSS_MURID = f"""
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{
  font-family: {T.FONT_LAYAR};
  font-size: {T.UKURAN_BADAN_LAYAR}; line-height: {T.LINE_HEIGHT}; color: {T.TEKS_UTAMA}; margin: 0;
  background: {T.LATAR_MURID};
}}
.wrap {{ max-width: {T.LEBAR_KONTEN}; margin: 0 auto; padding: {T.SP_4} 0.9rem 3rem; }}
h1 {{ font-size: 1.35rem; margin: 0.2rem 0 0.9rem; color: {T.AKSEN_MURID_UTAMA}; }}

/* Gaya dasar di atas adalah separuh dari perbaikan tampilan berantakan:
   halaman ini dulu hanya memuat gaya khusus murid, sementara markupnya
   memakai kelas dasar (.wrap, .soal, .bagian, ...) yang tidak pernah
   didefinisikan — hasilnya tampil dengan font dan lebar bawaan peramban.
   Kelas dasar sengaja disalin dari screen_style.py, bukan diimpor, supaya
   halaman murid tetap satu berkas CSS yang bisa dibaca utuh. */

.murid-header {{ display: flex; align-items: center; gap: .8rem; margin-bottom: 1rem; flex-wrap: wrap; }}
.murid-header h1 {{ margin: 0; flex: 1; }}
.btn {{
  display: inline-block; padding: .7rem 1.2rem; border-radius: 9px;
  border: none; background: {T.AKSEN_TEAL_TUA}; color: #fff; font-size: 1rem;
  text-decoration: none; cursor: pointer;
}}
.btn.secondary {{ background: #eef1f6; color: {T.TEKS_JUDUL}; border: 1px solid #ccd3dd; }}

/* Keadaan mati: auto-lock timer Latihan Cepat mematikan input di kartu
   soal yang waktunya habis; tanpa gaya ini kotak yang tidak bisa diisi
   lagi terlihat sama dengan kotak biasa dan anak terus mengetik tanpa
   efek. */
button:disabled, .btn:disabled {{ opacity: .55; cursor: not-allowed; }}
input:disabled, textarea:disabled {{
  background: #f3f4f6; color: {T.TEKS_SUBTLE}; cursor: not-allowed;
}}

.petunjuk {{
  background: {T.LATAR_KARTU_SEKUNDER}; border: 1px solid {T.BORDER_INTERAKTIF}; border-radius: {T.RADIUS_SEDANG};
  padding: 0.9rem 1rem; margin-bottom: 1.2rem; font-size: 0.95rem;
}}
.petunjuk p {{ margin: 0 0 0.6rem; }}
.petunjuk p:last-child {{ margin-bottom: 0; }}

.bagian {{
  font-size: 1.05rem; font-weight: 700; color: {T.TEKS_JUDUL};
  margin: 1.6rem 0 0.7rem; padding-bottom: 0.35rem;
  border-bottom: 2px solid {T.TEKS_JUDUL};
}}
.catatan-bagian {{
  background: {T.LATAR_CATATAN}; border: 1px solid {T.BORDER_CATATAN}; border-radius: {T.RADIUS_KECIL};
  padding: 0.55rem 0.8rem; margin: -0.2rem 0 0.8rem; font-size: 0.92rem;
}}

.soal {{
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS}; border-radius: {T.RADIUS_KARTU};
  padding: 1rem; margin-bottom: 1rem;
}}
.nomor {{
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 2rem; height: 2rem; font-weight: 700;
  border: 2px solid {T.AKSEN_MURID_UTAMA}; border-radius: {T.RADIUS_BULAT};
  margin-right: 0.55rem; font-size: 0.95rem;
}}
.bintang {{ font-weight: 700; color: {T.AKSEN_MURID_AMBER}; }}

/* Pertanyaan utama adalah yang paling penting di kartu, jadi ia harus
   paling menonjol. Dulu badan soal dan pertanyaan berukuran sama persis —
   anak membaca ulang semua kalimat untuk mencari apa yang ditanya. */
.teks {{ display: block; margin-top: 0.4rem; }}
.tanya {{
  display: block; font-size: 1.12rem; font-weight: 700;
  margin-top: 0.6rem; color: {T.TEKS_JUDUL};
}}

.label {{ display: block; font-size: 0.85rem; color: {T.TEKS_SUBTLE}; margin: 0.8rem 0 0.35rem; }}

.daftar-sesi {{ display: block; color: inherit; text-decoration: none; }}
.daftar-sesi:hover {{ border-color: {T.TEKS_JUDUL}; }}

.soal-murid textarea {{
  width: 100%; min-height: 84px; border: 1.5px dashed #99a;
  border-radius: {T.RADIUS_KECIL}; padding: .6rem; font-size: 1rem; font-family: inherit;
  background: #fafafc;
}}
.soal-murid input[type=text] {{
  font-size: 1.15rem; padding: .55rem .7rem; border: 2px solid #333;
  border-radius: {T.RADIUS_KECIL}; min-width: 7rem;
}}
/* Fokus yang terlihat: jawaban dan caraku adalah medan utama halaman ini.
   outline diganti border+bayangan (bukan dihapus tanpa pengganti). */
.soal-murid input[type=text]:focus, .soal-murid textarea:focus {{
  outline: none; border-color: {T.AKSEN_MURID_UTAMA}; border-style: solid;
  box-shadow: 0 0 0 3px rgba(15,163,163,0.18);
}}
.baris-jawab {{ display: flex; align-items: baseline; gap: .6rem; margin-top: .7rem; flex-wrap: wrap; }}
.baris-jawab input[type=text] {{ flex: 1; min-width: 0; }}
.centang-baris {{
  display: flex; align-items: center; gap: .5rem; margin-top: .7rem;
  font-size: .95rem; color: #444;
}}
.simpan-strip {{
  position: sticky; bottom: 0; padding: .8rem 0 .4rem;
  background: linear-gradient(to top, {T.LATAR_MURID} 70%, transparent);
}}
.simpan-strip .btn {{ width: 100%; font-size: 1.1rem; padding: .95rem; background: {T.AKSEN_KORAL_TUA}; }}

/* Pilihan cepat "Caraku" — target sentuh penuh, bukan lingkaran radio kecil.
   Seluruh kotak bisa di-tap; anak tidak perlu membidik titik 20px. */
.pilih-cara-grup {{
  display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: .8rem;
}}
.pilih-cara {{
  display: flex; align-items: center; gap: .45rem;
  border: 1.5px solid #ccd3dd; border-radius: {T.RADIUS_PIL};
  padding: .55rem .9rem; min-height: {T.TARGET_SENTUH};
  background: {T.LATAR_KARTU_MURID}; cursor: pointer; font-size: .95rem;
}}
.pilih-cara input {{ width: 1.2rem; height: 1.2rem; flex: none; }}
/* :has() didukung Safari 15.4+ dan Chrome 105+; kalau peramban lebih tua,
   yang hilang hanya penandaan warna — radio-nya tetap berfungsi. */
.pilih-cara:has(input:checked) {{
  border-color: {T.AKSEN_MURID_UTAMA}; background: {T.LATAR_KARTU_SEKUNDER}; font-weight: 600;
}}
/* Fokus papan tombol pada pilihan cara: cincin di KOTAK, bukan pada titik
   radio kecil di dalamnya. Outline radio diganti, bukan dihapus begitu saja. */
.pilih-cara:has(input:focus-visible) {{
  border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 0 0 3px rgba(15,163,163,0.28);
}}
.pilih-cara input:focus-visible {{ outline: none; }}

/* Konfirmasi setelah simpan. Tanpa ini anak tidak tahu jawabannya masuk,
   lalu menekan tombol berulang kali atau mengira kerjanya hilang. */
.tersimpan {{
  background: {T.LATAR_TERSIMPAN}; border: 1px solid {T.BORDER_TERSIMPAN}; color: {T.TEKS_TERSIMPAN};
  border-radius: {T.RADIUS_SEDANG}; padding: .8rem 1rem; margin-bottom: 1rem;
  font-size: .98rem;
}}

/* ── Timer Latihan Cepat ── */
.timer-strip {{
  position: sticky; top: 0; z-index: 5;
  background: {T.AKSEN_TEAL_TUA}; color: #fff;
  padding: .55rem .9rem; border-radius: {T.RADIUS_SEDANG};
  margin-bottom: .8rem; font-size: .98rem; font-weight: 600; text-align: center;
}}
.timer-strip b {{ font-size: 1.15rem; }}
/* Waktu habis: putih di atas coral hanya 2.8:1 — pakai kosakata galat
   aplikasi (latar merah muda + teks merah gelap) supaya terbaca dan
   konsisten dengan pesan galat di permukaan lain. */
.timer-strip.habis {{
  background: {T.LATAR_GALAT}; color: {T.TEKS_GALAT};
  border: 2px solid {T.BORDER_GALAT};
}}
.soal-timer-note {{
  margin-top: .5rem; font-size: .85rem; color: {T.AKSEN_KORAL_TUA};
}}

/* ── halaman daftar sesi (/murid) ── */
.owl-mascot {{ flex: none; width: 40px; height: 40px; }}
.sub-judul {{
  font-size: 0.95rem; color: {T.TEKS_SUBTLE}; margin: -0.5rem 0 1.2rem;
}}
.keluar-form {{ margin: 0 0 1.2rem; }}
.keluar-form .btn {{ padding: .4rem 1rem; font-size: 0.85rem; }}

.daftar-sesi-grup {{ display: flex; flex-direction: column; gap: 0.7rem; }}

.kartu-sesi {{
  display: flex; align-items: center; gap: 0.8rem;
  background: {T.LATAR_KARTU_MURID}; border: 1px solid {T.BORDER_HALUS};
  border-radius: {T.RADIUS_KARTU}; padding: 0.8rem 1rem;
  text-decoration: none; color: {T.TEKS_UTAMA};
  transition: border-color 0.15s, box-shadow 0.15s;
}}
.kartu-sesi:hover {{
  border-color: {T.AKSEN_MURID_UTAMA};
  box-shadow: 0 2px 8px rgba(15,163,163,0.12);
}}
.ikon-sesi {{
  flex: none; width: 2.5rem; height: 2.5rem; border-radius: {T.RADIUS_BULAT};
}}
.isi-sesi {{ display: flex; flex-direction: column; flex: 1; min-width: 0; }}
.tanggal-sesi {{ font-weight: 700; font-size: 1rem; color: {T.TEKS_JUDUL}; }}
.meta-sesi {{ font-size: 0.85rem; color: {T.TEKS_SUBTLE}; }}
.badge-soal {{
  flex: none; font-size: 0.8rem; font-weight: 600;
  background: {T.LATAR_KARTU_SEKUNDER}; color: {T.AKSEN_TEAL_TUA};
  padding: 0.25rem 0.6rem; border-radius: {T.RADIUS_PIL};
}}
/* Slot kanan kartu sesi: badge "baru" atau kosong. Badge statis di slot,
   bukan absolute-transform di slot chevron 16px yang rapuh. */
.ujung-sesi {{
  flex: none; display: flex; align-items: center;
}}
.badge-baru {{
  font-size: 0.7rem; font-weight: 700; color: #fff;
  background: {T.AKSEN_KORAL_TUA}; padding: 0.15rem 0.5rem;
  border-radius: {T.RADIUS_PIL}; white-space: nowrap;
}}
.badge-latihan {{
  font-size: 0.7rem; font-weight: 700; color: {T.AKSEN_TEAL_TUA};
  background: {T.LATAR_KARTU_SEKUNDER}; padding: 0.15rem 0.4rem;
  border-radius: {T.RADIUS_PIL}; white-space: nowrap; margin-left: 0.25rem;
}}
/* Badge status pengerjaan (menggantikan badge-tanggal "baru"): satu warna
   untuk satu keadaan sesuai kosakata status aplikasi — coral = belum
   disentuh, amber = sedang dikerjakan, teal netral = menunggu review guru,
   teal kuat = sudah dinilai. Ukuran disamakan supaya kartu tidak melompat
   saat statusnya berubah. */
.badge-kerja {{
  font-size: 0.7rem; font-weight: 700;
  color: {T.BADGE_ADMIN_TEKS};
  background: rgba(255, 176, 32, 0.2);  /* AKSEN_MURID_AMBER versi lembut */
  padding: 0.15rem 0.5rem;
  border-radius: {T.RADIUS_PIL}; white-space: nowrap;
}}
.badge-review {{
  font-size: 0.7rem; font-weight: 700; color: {T.AKSEN_TEAL_TUA};
  background: {T.LATAR_KARTU_SEKUNDER}; padding: 0.15rem 0.5rem;
  border-radius: {T.RADIUS_PIL}; white-space: nowrap;
}}
.badge-selesai {{
  font-size: 0.7rem; font-weight: 700; color: {T.TEKS_PUTIH};
  background: {T.STATUS_KUAT}; padding: 0.15rem 0.5rem;
  border-radius: {T.RADIUS_PIL}; white-space: nowrap;
}}
.kosong-hint {{
  border: 1.5px dashed #ccd3dd; border-radius: {T.RADIUS_KARTU};
  padding: 1.5rem; text-align: center; color: {T.TEKS_SUBTLE};
  font-size: 0.95rem;
}}

/* ── halaman kerja (/murid/kerjakan) ── */
.meta-sesi-line {{ font-size: 0.85rem; color: {T.TEKS_SUBTLE}; margin-bottom: 1rem; }}
.petunjuk-ikon {{ display: flex; gap: 0.7rem; align-items: flex-start; }}
.ikon-petunjuk {{ flex: none; margin-top: 0.15rem; }}
.petunjuk-ikon > div {{ flex: 1; }}

/* Pilihan "Caraku" — 2 kolom rapi di layar lebar, 1 kolom di sempit */
.pilih-cara-grup {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: .8rem;
}}
@media (max-width: 36rem) {{
  .pilih-cara-grup {{ grid-template-columns: 1fr; }}
}}

/* Hormati preferensi gerak — satu blok untuk seluruh permukaan murid. */
@media (prefers-reduced-motion: reduce) {{
  * {{
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
  }}
}}

@media print {{
  /* Tombol "Cetak / PDF" di kepala halaman memicu window.print(); di sini
     halaman menurunkan dirinya ke kertas: kontrol hilang, kartu jadi kotak
     hitam-putih, soal tidak terpotong antarhalaman. Di dialog cetak, murid
     memilih "Simpan sebagai PDF" — tidak perlu berkas PDF terpisah. */
  body {{ background: #fff; font-size: {T.UKURAN_BADAN_CETAK}; }}
  .wrap {{ max-width: none; padding: 0; }}
  .hanya-layar {{ display: none; }}
  .soal, .petunjuk {{ border-color: #000; border-radius: 0; }}
  .soal {{ break-inside: avoid; }}
  .bagian {{ break-after: avoid; }}
}}
"""

def halaman_kerja(
    kon, siswa_id: int, sesi_id: int, tersimpan: int = 0,
    topik_paket: Topik | None = None,
) -> bytes | None:
    """Lembar interaktif murid: baca soal, tulis caraku + jawaban.

    Dua mode sesi (29 Aug 2026):
      - diagnostik (default): kartu penuh — restate + pill "Caraku" + kotak tulis.
      - drill (Latihan Cepat): kartu ringan — hanya Jawabanku + centang
        "belum pernah lihat". Timer per-sesi (tampil jalan) atau per-soal
        (internal, tak ditampilkan), dengan perilaku peringatan / auto-lock.
    """
    import icons

    info = sesi_murid(kon, siswa_id, sesi_id)
    if not info:
        return None
    if topik_paket is None:
        topik_paket = dari_sesi(info.get("topik"))
    daftar = soal_murid(kon, sesi_id, siswa_id)

    drill = info.get("mode", "diagnostik") == "drill"
    timer_mode = info.get("timer_mode", "tanpa") or "tanpa"
    durasi_menit = int(info.get("durasi_menit") or 15)
    timer_auto = 1 if info.get("timer_auto") else 0

    kartu: list[str] = []
    bagian_kini = None
    for s in daftar:
        if s["bagian"] != bagian_kini:
            bagian_kini = s["bagian"]
            judul = topik_paket.judul_bagian.get(
                bagian_kini, f"Bagian {bagian_kini}"
            )
            kartu.append(f'<div class="bagian">{judul}</div>')
            if bagian_kini in topik_paket.catatan_bagian:
                kartu.append(
                    f'<div class="catatan-bagian">'
                    f"{topik_paket.catatan_bagian[bagian_kini]}</div>"
                )
        t = s["terjawab"] or {}
        ssid = s["sesi_soal_id"]
        belum = " checked" if t.get("belum_pernah") else ""

        if drill:
            catatan_soal = ""
            if timer_mode == "soal":
                catatan_soal = (
                    '<div class="soal-timer-note" style="display:none">'
                    "Waktu untuk soal ini habis — lanjut ke soal berikutnya.</div>"
                )
            kartu.append(f"""
<div class="soal soal-murid">
  <span class="nomor">{s['nomor']}</span>
  {'<span class="bintang">★</span>' if s['tantangan'] else ''}
  {_badan_teks(s['teks'])}
  <div class="baris-jawab">
    <span>Jawabanku:</span>
    <input type="text" name="jwb_{ssid}"
           value="{_escape(t.get('jawaban', ''))}" autocomplete="off">
  </div>
  <label class="centang-baris">
    <input type="checkbox" name="blm_{ssid}"{belum} style="width:1.3rem;height:1.3rem">
    belum pernah lihat soal seperti ini
  </label>
  {catatan_soal}
</div>""")
            continue

        restate = ""
        if s["minta_restatement"]:
            nilai = _escape(t.get("restatement", ""))
            restate = (
                '<label class="label">Soal ini mintanya apa? '
                "(tulis pakai kalimatmu sendiri)</label>"
                f'<textarea name="restate_{ssid}">{nilai}</textarea>'
            )

        # Pilihan cepat "Caraku". Kalau jawaban tersimpan berupa pilihan,
        # tandai yang terpilih supaya anak melihat isiannya kembali.
        cara_tersimpan = t.get("cara", "") or ""
        pilihan_kini = ""
        teks_cara = cara_tersimpan
        if cara_tersimpan.startswith(AWALAN_PILIHAN):
            sisa = cara_tersimpan[len(AWALAN_PILIHAN):]
            pilihan_kini, _, teks_cara = sisa.partition(" — ")
            pilihan_kini = pilihan_kini.strip()
            teks_cara = teks_cara.strip()

        tombol = "".join(
            f'<label class="pilih-cara">'
            f'<input type="radio" name="pilih_{ssid}" value="{kode}"'
            f'{" checked" if kode == pilihan_kini else ""}>'
            f"<span>{_escape(teks)}</span></label>"
            for kode, teks in PILIHAN_CARA
        )

        kartu.append(f"""
<div class="soal soal-murid">
  <span class="nomor">{s['nomor']}</span>
  {'<span class="bintang">★</span>' if s['tantangan'] else ''}
  {_badan_teks(s['teks'])}
  {restate}
  <label class="label">Caraku — pilih dulu yang paling mirip:</label>
  <div class="pilih-cara-grup">{tombol}</div>
  <label class="label">Kalau mau, tulis lebih jelas di sini (boleh dikosongkan):</label>
  <textarea name="cara_{ssid}">{_escape(teks_cara)}</textarea>
  <div class="baris-jawab">
    <span>Jawabanku:</span>
    <input type="text" name="jwb_{ssid}"
           value="{_escape(t.get('jawaban', ''))}" autocomplete="off">
  </div>
  <label class="centang-baris">
    <input type="checkbox" name="blm_{ssid}"{belum} style="width:1.3rem;height:1.3rem">
    belum pernah lihat soal seperti ini
  </label>
</div>""")

    # Konfirmasi setelah simpan. Jumlah soal yang tersimpan disebut angkanya,
    # bukan sekadar "berhasil": anak bisa langsung tahu kalau ada soal yang
    # ia kira sudah diisi tapi ternyata belum.
    kabar = ""
    if tersimpan:
        kabar = (
            f'<div class="tersimpan">Tersimpan ✓ — {tersimpan} soal sudah '
            f"masuk. Boleh lanjut, atau tutup halaman ini.</div>"
        )

    if drill:
        petunjuk = (
            "<p><b>Cara mengerjakan — baca dulu:</b></p>"
            "<p>Kerjakan sebisamu, tulis jawaban di kotak <b>Jawabanku</b>."
            + (" Perhatikan waktunya." if timer_mode == "sesi" else "")
            + "</p>"
            "<p>Kalau ada soal yang belum pernah kamu lihat, centang kotaknya. Itu "
            "<b>bukan</b> salah — itu berguna untuk gurumu.</p>"
            "<p>Tidak apa-apa ada yang kosong. Jangan menebak asal. Kalau sudah selesai, "
            "tekan <b>Simpan jawabanku</b> di paling bawah.</p>"
        )
    else:
        petunjuk = (
            "<p><b>Cara mengerjakan — baca dulu:</b></p>"
            "<p>Tiap soal ada bagian <b>Caraku</b>. Pilih satu yang paling mirip dengan "
            "caramu mendapat jawaban. Kalau mau, tulis juga caranya di kotak tulisan.</p>"
            "<p>Kalau ada soal yang belum pernah kamu lihat, centang kotaknya. Itu "
            "<b>bukan</b> salah — itu berguna untuk gurumu.</p>"
            "<p>Tidak apa-apa ada yang kosong. Jangan menebak asal. Kalau sudah selesai, "
            "tekan <b>Simpan jawabanku</b> di paling bawah.</p>"
        )

    # Timer Latihan Cepat. Per-sesi: strip countdown yang tampil jalan (sticky
    # di atas). Per-soal: internal — tidak ada angka yang tampil, tiap kartu
    # punya catatan yang muncul kalau waktunya habis.
    strip = ""
    if drill and timer_mode == "sesi":
        strip = (
            '<div class="timer-strip hanya-layar" id="timer-strip">'
            "Sisa waktu: <b id=\"timer-tampil\">"
            f"{durasi_menit:02d}:00</b>"
            '<span id="timer-pesan" style="display:none">'
            " — waktu habis, kerjakan sebisanya dan simpan</span></div>"
        )

    skrip = ""
    if drill and timer_mode in ("sesi", "soal"):
        skrip = f"""
<script>
(function(){{
  var MODE = {json.dumps(timer_mode)};
  var DETIK = {durasi_menit * 60};
  var AUTO = {1 if timer_auto else 0};
  var mulai = Date.now();
  function fmt(s){{ return Math.floor(s/60) + ":" + String(s%60).padStart(2,"0"); }}
  if (MODE === "sesi") {{
    var strip = document.getElementById("timer-strip");
    var tampil = document.getElementById("timer-tampil");
    function tick(){{
      var sisa = DETIK - Math.floor((Date.now()-mulai)/1000);
      if (sisa <= 0) {{
        sisa = 0;
        if (AUTO) {{
          var f = document.querySelector("form");
          if (f) {{ f.dataset.kirimOtomatis = "1"; f.submit(); }}
          return;
        }}
        var p = document.getElementById("timer-pesan");
        if (p) p.style.display = "";
        if (strip) strip.className = "timer-strip habis";
      }}
      if (tampil) tampil.textContent = fmt(sisa);
    }}
    tick();
    setInterval(tick, 1000);
  }} else if (MODE === "soal") {{
    var kartu = document.querySelectorAll(".soal");
    var mulaiSoal = {{}};
    document.addEventListener("focusin", function(ev){{
      var k = ev.target.closest ? ev.target.closest(".soal") : null;
      if (!k) return;
      var i = Array.prototype.indexOf.call(kartu, k);
      if (i >= 0 && !(i in mulaiSoal)) mulaiSoal[i] = Date.now();
    }});
    function tick(){{
      var t = Date.now();
      kartu.forEach(function(k, i){{
        if (!(i in mulaiSoal)) return;
        var sisa = DETIK - Math.floor((t - mulaiSoal[i])/1000);
        if (sisa > 0) return;
        if (AUTO) {{
          k.querySelectorAll("input, textarea, button").forEach(function(inp){{
            inp.disabled = true;
          }});
        }}
        var n = k.querySelector(".soal-timer-note");
        if (n) n.style.display = "";
      }});
    }}
    setInterval(tick, 1000);
  }}
}})();
</script>
"""

    # Penjaga kerja anak, selalu terpasang (bukan hanya saat timer):
    #   - tombol simpan mati + berubah "Menyimpan…" saat mengirim, supaya
    #     ketukan ganda tidak mengirim lembar dua kali;
    #   - menutup/meninggalkan halaman dengan isian yang belum disimpan
    #     minta konfirmasi dulu — geser-balik di HP nyata-nya terjadi;
    #   - kirim otomatis timer (form.submit()) tidak melewati event submit,
    #     jadi ditandai data-kirim-otomatis agar lolos dari konfirmasi.
    jaga = """
<script>
(function(){
  var f = document.querySelector('form');
  if (!f) return;
  var kotor = false;
  f.addEventListener('input', function(){ kotor = true; }, true);
  f.addEventListener('change', function(){ kotor = true; }, true);
  f.addEventListener('submit', function(){
    kotor = false;
    var b = f.querySelector('button[type=submit]');
    if (b) { b.disabled = true; b.textContent = 'Menyimpan\u2026'; }
  });
  window.addEventListener('pageshow', function(){
    var b = f.querySelector('button[type=submit]');
    if (b && b.disabled) { b.disabled = false; b.textContent = 'Simpan jawabanku'; }
  });
  window.addEventListener('beforeunload', function(e){
    if (kotor && f.dataset.kirimOtomatis !== '1') {
      e.preventDefault();
      e.returnValue = '';
    }
  });
})();
</script>
"""

    isi = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kerjakan — {topik_paket.judul_lembar}</title>
<style>{CSS_MURID}</style></head><body><div class="wrap">
<div class="murid-header">
  <img src="{icons.OWL}" alt="" class="owl-mascot" width="36" height="36">
  <h1>Halo, {_escape(info['nama'])}</h1>
  <button class="btn secondary hanya-layar" type="button"
          onclick="window.print()">Cetak / PDF</button>
  <a class="btn secondary hanya-layar" href="/murid">Sesi lain</a>
</div>
<p class="meta-sesi-line">{_escape(info['tanggal'])} &middot; level {_escape(info['level'])}
 &middot; {len(daftar)} soal
 {'&middot; Latihan Cepat' if drill else ''}</p>
{strip}
{kabar}
<div class="petunjuk petunjuk-ikon">
  <img src="{icons.BOHLAM}" alt="" class="ikon-petunjuk" width="20" height="20">
  <div>
    {petunjuk}
  </div>
</div>
<form method="post" action="/murid/kerjakan/{sesi_id}">
{"".join(kartu)}
<div class="simpan-strip hanya-layar"><button type="submit" class="btn">Simpan jawabanku</button></div>
</form>
<form method="post" action="/keluar" class="hanya-layar" style="margin-top:1rem"><button class="btn secondary" type="submit">Keluar</button></form>
{jaga}{skrip}
</div></body></html>"""
    return isi.encode()

def halaman_daftar_sesi(kon, siswa_id: int, nama: str, sesi_selesai: int | None = None) -> bytes:
    """Halaman /murid — daftar sesi milik murid ini saja.

    Kartu sesi dirancang seperti mockup (murid-sesiku.png): icon lingkaran
    berwarna di kiri, tanggal + level/topik di tengah, badge pill "N soal"
    + chevron kanan. Badge mengikuti STATUS pengerjaan, bukan tanggal —
    yang dipedulikan anak/guru adalah: sudah dikerjakan? sudah direview?
    berapa nilainya?

    `sesi_selesai` = id sesi yang BARU SAJA dikirim anak; hanya menampilkan
    banner konfirmasi di atas daftar (pengganti halaman /murid/selesai).
    """
    import icons

    _WARNA_ICON = ["#0FA3A3", "#FF6B5B", "#FFB020", "#8B5CF6"]

    baris = kon.execute(
        """SELECT id, tanggal, level, topik, mode,
                  (SELECT COUNT(*) FROM sesi_soal ss WHERE ss.sesi_id = s.id) AS jumlah,
                  s.selesai, s.direview,
                  (SELECT COUNT(*) FROM sesi_soal ss
                   JOIN jawaban j ON j.sesi_soal_id = ss.id
                   WHERE ss.sesi_id = s.id) AS terisi,
                  (SELECT COUNT(*) FROM sesi_soal ss
                   JOIN jawaban j ON j.sesi_soal_id = ss.id
                   JOIN diagnosis d ON d.jawaban_id = j.id
                   WHERE ss.sesi_id = s.id AND d.benar = 1) AS benar
           FROM sesi s WHERE s.siswa_id = ?
           ORDER BY s.id DESC""",
        (siswa_id,),
    ).fetchall()

    kartu = []
    for i, b in enumerate(baris):
        warna = _WARNA_ICON[i % len(_WARNA_ICON)]
        # Badge berbasis status; urutan if = urutan hidup sesi. Subquery di
        # atas sengaja dihitung di sini (bukan lewat view ringkasan_sesi):
        # daftar butuh angka mentah per sesi tanpa GROUP BY gabungan.
        # Tanggal tidak dipakai — sesi kemarin yang belum disentuh tetap
        # "Baru", dan itu yang dimengerti anak.
        if b["terisi"] == 0:
            badge_status = '<span class="badge-baru">Baru</span>'
        elif b["selesai"] is None:
            badge_status = '<span class="badge-kerja">Dikerjakan</span>'
        elif b["direview"] is None:
            badge_status = '<span class="badge-review">Masih di review</span>'
        else:
            badge_status = (
                f'<span class="badge-selesai">Selesai · {b["benar"]}'
                f'/{b["jumlah"]} benar</span>'
            )
        # Tag "latihan" untuk sesi Latihan Cepat (drill) — biar anak tahu
        # sesi ini bukan diagnosa penuh.
        tag_latihan = (
            '<span class="badge-latihan">latihan</span>'
            if b["mode"] == "drill" else ""
        )
        kartu.append(
            f'<a class="kartu-sesi" href="/murid/kerjakan/{b["id"]}">'
            f'<span class="ikon-sesi" style="background:{warna}"></span>'
            f'<span class="isi-sesi">'
            f'<span class="tanggal-sesi">{_escape(b["tanggal"])}</span>'
            f'<span class="meta-sesi">level {_escape(b["level"])} '
            f"&middot; {_escape(_ambil_topik(b))} {tag_latihan}</span>"
            f"</span>"
            f'<span class="badge-soal">{b["jumlah"]} soal</span>'
            f'<span class="ujung-sesi">{badge_status}</span>'
            "</a>"
        )

    kartu_html = "\n".join(kartu) or (
        '<div class="kosong-hint">Belum ada sesi. Minta gurumu membuatkan.</div>'
    )

    # Banner konfirmasi setelah submit penuh (QA): anak dibawa LANGSUNG
    # kembali ke daftar sesi — bukan ke halaman terpisah — dengan kabar yang
    # jelas bahwa semua jawabannya sudah masuk.
    banner = ""
    if sesi_selesai is not None:
        banner = (
            '<div class="tersimpan">🎉 Selesai! Semua jawabanmu sudah masuk.</div>'
        )

    isi = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sesiku</title><style>{CSS_MURID}</style></head><body><div class="wrap">
<div class="murid-header">
  <img src="{icons.OWL}" alt="" class="owl-mascot" width="40" height="40">
  <h1>Halo, {_escape(nama)}!</h1>
</div>
{banner}
<p class="sub-judul">Pilih sesi untuk mulai latihan</p>
<form method="post" action="/keluar" class="keluar-form"><button class="btn secondary" type="submit">Keluar</button></form>
<div class="daftar-sesi-grup">
{kartu_html}
</div>
</div></body></html>"""
    return isi.encode()
