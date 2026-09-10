"""Halaman sisi anak: kerjakan sesi, daftar sesi ber-status.

Dipecah dari students.py (refactor 31 Aug 2026) — fungsi pindah utuh,
perilaku identik. students.py kini lapisan data; modul ini lapisan tampilan
dan mengimpor dari sana (satu arah). Palang tetap: halaman anak TIDAK boleh
menampilkan kunci, malrule, atau diagnosis — dijaga test_palang_*.
"""

from __future__ import annotations

import json

import brand
import visual_renderer
import design_tokens as T
from presentation_style import GAYA_PENYAJIAN
from templates import label_kelas
from learning_stage_labels import penanda_tahap
from topics import Topik, dari_sesi
from students import (
    AWALAN_PILIHAN,
    PILIHAN_CARA,
    _ambil_topik,
    _escape,
    hasil_murid,
    sesi_murid,
    soal_murid,
)


def _nama_fokus_remedial(kon, sesi_id: int) -> str:
    """Nama tipe soal aman untuk metadata kartu murid, tanpa diagnosis/kunci."""
    nama_khusus = {"soal_umur": "Soal tentang umur"}
    rows = kon.execute(
        """SELECT DISTINCT so.template_id
           FROM sesi_soal ss JOIN soal so ON so.id = ss.soal_id
           WHERE ss.sesi_id = ? ORDER BY ss.nomor""",
        (sesi_id,),
    ).fetchall()
    return " & ".join(
        nama_khusus.get(
            str(r["template_id"]),
            str(r["template_id"]).replace("_", " ").capitalize(),
        )
        for r in rows
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
{GAYA_PENYAJIAN}
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
.hint-silap {{ font-size: .78rem; color: {T.TEKS_SUBTLE}; }}

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
    detik_lalu = int(info.get("detik_lalu") or 0)

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
  {visual_renderer.render_pertanyaan(s['penyajian'], gaya='murid', namespace=str(s['nomor']))}
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
  {visual_renderer.render_pertanyaan(s['penyajian'], gaya='murid', namespace=str(s['nomor']))}
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
            "tekan <b>Selesai &amp; kirim</b> di paling bawah. Kamu juga bisa menyimpan sementara dulu.</p>"
        )
    else:
        petunjuk = (
            "<p><b>Cara mengerjakan — baca dulu:</b></p>"
            "<p>Tiap soal ada bagian <b>Caraku</b>. Pilih satu yang paling mirip dengan "
            "caramu mendapat jawaban. Kalau mau, tulis juga caranya di kotak tulisan.</p>"
            "<p>Kalau ada soal yang belum pernah kamu lihat, centang kotaknya. Itu "
            "<b>bukan</b> salah — itu berguna untuk gurumu.</p>"
            "<p>Tidak apa-apa ada yang kosong. Jangan menebak asal. Kalau sudah selesai, "
            "tekan <b>Selesai &amp; kirim</b> di paling bawah. Kamu juga bisa menyimpan sementara dulu.</p>"
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
  var DETIK_LALU = {detik_lalu};
  var AUTO = {1 if timer_auto else 0};
  var mulai = Date.now() - DETIK_LALU * 1000;
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
          if (f) {{
            f.dataset.kirimOtomatis = "1";
            var a = document.createElement("input");
            a.type = "hidden"; a.name = "aksi"; a.value = "selesai";
            f.appendChild(a); f.submit();
          }}
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
<title>{brand.judul(f"Kerjakan — {topik_paket.judul_lembar}")}</title>
{brand.tag_kepala()}
<style>{CSS_MURID}</style></head><body><div class="wrap">
<div class="murid-header">
  <img src="{icons.OWL}" alt="" class="owl-mascot" width="36" height="36">
  <h1>Halo, {_escape(info['nama'])}</h1>
  <button class="btn secondary hanya-layar" type="button"
          onclick="window.print()">Cetak / PDF</button>
  <a class="btn secondary hanya-layar" href="/murid">Sesi lain</a>
</div>
<p class="meta-sesi-line">{_escape(info['tanggal'])} &middot; {_escape(label_kelas(info['level']))}
 &middot; {len(daftar)} soal {penanda_tahap(info.get('tujuan', 'bebas'))}
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

def _ikon_beranda(nama: str) -> str:
    """Ikon dekoratif lokal; setiap kontrol tetap punya nama berupa teks."""
    bentuk = {
        "panah": '<path d="M4 12h15m-6-6 6 6-6 6"/>',
        "buku": '<path d="M12 6c-3-2-7-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-2-1-6-1-9 1Zm0 0v14"/>',
        "grafik": '<path d="M4 20h17M7 16v-5m5 5V5m5 11V8"/>',
        "bilangan": '<rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 7h8M8 12h1m6 0h1m-8 5h1m6 0h1"/>',
        "jam": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "lipat": '<path d="m9 5 7 7-7 7"/>',
    }
    return (
        '<svg class="murid-ikon-st" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{bentuk[nama]}</svg>'
    )


def _tanggal_beranda(nilai: str) -> str:
    """Tanggal manusiawi; nilai warisan yang bukan ISO tetap di-escape caller."""
    from datetime import date
    bulan = ("Januari", "Februari", "Maret", "April", "Mei", "Juni",
             "Juli", "Agustus", "September", "Oktober", "November", "Desember")
    try:
        tanggal = date.fromisoformat(str(nilai)[:10])
    except ValueError:
        return str(nilai)
    return f"{tanggal.day} {bulan[tanggal.month - 1]} {tanggal.year}"


def _judul_beranda(sesi: dict) -> tuple[str, str]:
    """Topik dan ikon stabil, tidak berubah ketika urutan daftar berubah."""
    paket = dari_sesi(sesi["topik"])
    if paket.id == "campuran":
        return "Latihan campuran", "buku"
    if paket.id.startswith("gabungan:"):
        return "Latihan gabungan", "buku"
    ikon = "grafik" if paket.id == "statistika" else (
        "bilangan" if paket.id in {"pola-bilangan", "teori-bilangan",
                                  "aritmetika-dasar", "aritmatika-lanjut"} else "buku"
    )
    return paket.nama[:1].upper() + paket.nama[1:].lower(), ikon


def _tahap_beranda(sesi: dict) -> str:
    """Sesi bebas dan warisan juga memakai istilah netral untuk anak."""
    tahap = penanda_tahap(sesi["tujuan"])
    if tahap:
        return tahap
    if sesi["jenis"] == "remedial":
        return "Latihan terarah"
    return "Latihan Cepat" if sesi["mode"] == "drill" else "Latihan campuran"


def _penanda_beranda(sesi: dict) -> str:
    """Progres hanya untuk sesi yang masih dikerjakan, bukan nilai benar."""
    n, jumlah = sesi["terisi"], sesi["jumlah"]
    if sesi["selesai"] is None and n > 0 and jumlah > 0:
        persen = round(min(n, jumlah) / jumlah * 100, 1)
        return (
            '<span class="st-progres-label">'
            f'{n} dari {jumlah} soal tersimpan</span>'
            '<span class="st-progres-jalur" role="progressbar" '
            f'aria-label="Soal tersimpan" aria-valuemin="0" aria-valuemax="{jumlah}" '
            f'aria-valuenow="{min(n, jumlah)}">'
            f'<span class="st-progres-isi" style="width:{persen}%"></span>'
            '</span>'
        )
    return f'<span class="murid-jumlah-st">{jumlah} soal</span>'


def _kartu_beranda(sesi: dict, utama: bool = False) -> str:
    """Satu tautan per sesi, tanpa tombol/link bersarang di kartu utama."""
    judul, ikon = _judul_beranda(sesi)
    tahap = _tahap_beranda(sesi)
    selesai = sesi["selesai"] is not None
    direview = selesai and sesi["direview"] is not None
    if direview:
        label, kelas = "Selesai · sudah diperiksa", "diagnostik"
        aksi, jalur = "Lihat hasil", f"/murid/hasil/{sesi['id']}"
    elif selesai:
        label, kelas = "Menunggu diperiksa", "review"
        aksi, jalur = "", ""
    elif sesi["terisi"]:
        label, kelas = "Sedang dikerjakan", "selesai"
        aksi, jalur = "Lanjutkan", f"/murid/kerjakan/{sesi['id']}"
    else:
        label, kelas = "Belum dimulai", "baru"
        aksi, jalur = "Mulai", f"/murid/kerjakan/{sesi['id']}"
    badge = f'<span class="st-badge {kelas}">{label}</span>'
    penanda = _penanda_beranda(sesi)
    kelas_penanda = (
        "st-progres-soal"
        if not selesai and sesi["terisi"] > 0 and sesi["jumlah"] > 0
        else "st-jumlah-soal"
    )
    tanggal = _escape(_tanggal_beranda(sesi["tanggal"]))
    meta = f'{_escape(label_kelas(sesi["level"]))} · {tanggal}'
    # Marker tiga anak kartu dipertahankan: ikon, kolom teks, penanda.
    if utama:
        label_utama = "Lanjutkan latihanmu" if sesi["terisi"] else "Latihan untukmu"
        aksi = "Lanjutkan latihan" if sesi["terisi"] else "Mulai latihan"
        ilustrasi = (
            '<span class="murid-ilustrasi-st" aria-hidden="true">'
            '<span class="murid-lingkaran-st"></span>'
            f'{brand.maskot("menunjuk", 240)}</span>'
        )
        teks = (
            '<span class="st-kartu-teks">'
            f'<span class="murid-label-utama-st">{label_utama}</span>'
            f'<span class="murid-tahap-st">{tahap}</span>'
            f'<span class="murid-judul-sampul-st" role="heading" aria-level="2">{_escape(judul)}</span>'
            '<span class="murid-sub-sampul-st">Kerjakan pelan-pelan, ya.</span>'
            f'<span class="murid-meta-st">{meta}</span></span>'
        )
        ujung = (
            f'<span class="murid-lanjut-bawah-st {kelas_penanda}">' + penanda
            + f'<span class="murid-tombol-utama-st">{aksi}{_ikon_beranda("panah")}</span>'
            + ('<span class="murid-aman-st">Jawaban tersimpan aman</span>' if sesi["terisi"] else '')
            + '</span>'
        )
        return (
            f'<a class="st-kartu-baris" data-utama="true" href="{jalur}">'
            f'{ilustrasi}{teks}{ujung}</a>'
        )
    teks = (
        '<span class="st-kartu-teks">'
        f'<span class="murid-judul-kartu-st">{_escape(judul)}</span>'
        f'<span class="murid-tahap-st">{tahap}</span>'
        f'<span class="murid-meta-st">{meta}</span>{badge}</span>'
    )
    ujung = f'<span class="murid-ujung-st {kelas_penanda}">' + penanda
    if aksi:
        ujung += f'<span class="murid-aksi-st">{aksi}{_ikon_beranda("panah")}</span>'
    ujung += '</span>'
    tag = "a" if jalur else "div"
    href = f' href="{jalur}"' if jalur else ''
    return (
        f'<{tag} class="st-kartu-baris"{href}>'
        f'<span class="murid-ikon-topik-st">{_ikon_beranda(ikon)}</span>'
        f'{teks}{ujung}</{tag}>'
    )


def halaman_daftar_sesi_baru(kon, siswa_id: int, nama: str, sesi_selesai: int | None = None) -> bytes:
    """Beranda buku belajar: satu sesi utama, tugas lain, kabar, dan riwayat."""
    from style_stitch import gaya_stitch
    from students import beranda_murid

    data = beranda_murid(kon, siswa_id)
    daftar = data["sesi"]
    utama = next((s for s in daftar if s["id"] == data["utama_id"]), None)
    tugas = [s for s in daftar if s["selesai"] is None and s is not utama]
    menunggu = [s for s in daftar if s["selesai"] is not None and s["direview"] is None]
    riwayat = [s for s in daftar if s["selesai"] is not None and s["direview"] is not None]
    banner = ""
    if any(s["id"] == sesi_selesai and s["selesai"] is not None for s in daftar):
        banner = (
            '<div class="st-banner-sukses" role="status">'
            f'{brand.maskot("merayakan", 96, kelas="maskot-banner")}'
            '<span>Selesai! Latihanmu sudah dikirim.</span></div>'
        )
    kolom = _kartu_beranda(utama, True) if utama else ""
    if not utama:
        if not daftar:
            judul, pesan = "Siap untuk latihan pertama?", (
                "Belum ada sesi latihan yang disiapkan. Minta orang tua atau gurumu membuatkan, ya."
            )
        elif tugas:
            judul, pesan = "Belajar selangkah lagi", (
                "Gurumu akan menyiapkan langkah berikutnya. Latihan lain yang tersedia tetap bisa kamu buka di bawah."
            )
        elif menunggu:
            judul, pesan = "Terima kasih sudah mencoba!", (
                "Latihanmu sudah dikirim. Sekarang boleh istirahat dulu."
            )
        else:
            judul, pesan = "Latihanmu sudah diperiksa", (
                "Kamu bisa membuka hasil latihan sebelumnya di bawah."
            )
        kolom = (
            '<section class="murid-keadaan-st">'
            f'{brand.maskot("netral", 240)}'
            f'<div><h2>{judul}</h2><p>{pesan}</p></div></section>'
        )
    if tugas:
        kolom += (
            '<section class="murid-latihan-lain-st" aria-labelledby="judul-lain">'
            '<div class="murid-kepala-bagian-st"><h2 id="judul-lain">Latihan lainnya</h2>'
            f'<span>{len(tugas)} latihan</span></div>'
            + ''.join(_kartu_beranda(s) for s in tugas) + '</section>'
        )
    pendamping = ""
    if menunggu:
        pendamping += (
            '<section class="murid-menunggu-st" aria-labelledby="judul-menunggu">'
            f'<h2 id="judul-menunggu">{_ikon_beranda("jam")}Menunggu diperiksa</h2>'
            '<h3>Jawabanmu sudah masuk.</h3>'
            '<p>Gurumu akan memeriksanya. Kamu tidak perlu mengirim ulang.</p>'
            + ''.join(_kartu_beranda(s) for s in menunggu) + '</section>'
        )
    if riwayat:
        pendamping += (
            '<details class="murid-riwayat-st"><summary>'
            f'{_ikon_beranda("buku")}<span><b>Latihan selesai</b>'
            f'<span>{len(riwayat)} latihan sudah diperiksa</span></span>{_ikon_beranda("lipat")}'
            '</summary><div class="murid-riwayat-isi-st">'
            + ''.join(_kartu_beranda(s) for s in riwayat) + '</div></details>'
        )
    grid = "murid-grid-st" + (" satu-kolom" if not pendamping else "")
    isi = f'''<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand.judul("Ruang belajarku")}</title>{brand.tag_kepala()}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{gaya_stitch()}</style></head><body class="st murid-beranda-st">
<a class="murid-lewati-st" href="#utama">Lewati ke latihan</a>
<header class="murid-kepala-st"><div>
<span class="murid-brand-st">{brand.mark("topbar")}<span>{T.NAMA_PRODUK}</span></span>
<form method="post" action="/keluar"><button type="submit">Keluar</button></form>
</div></header>
<main id="utama" class="murid-kanvas-st">
<section class="murid-sapaan-st" aria-labelledby="judul-sapaan">
<p class="murid-alis-st">RUANG BELAJARKU · {_escape(label_kelas(data["level"]))}</p>
<h1 id="judul-sapaan">Halo, {_escape(nama)}!</h1><p>Sedikit demi sedikit, makin mengerti.</p>
<span class="murid-akun-hint-st">Bukan kamu? Tekan Keluar dulu.</span></section>
{banner}<div class="{grid}"><div class="murid-kolom-utama-st">{kolom}</div>
{'<aside class="murid-pendamping-st" aria-label="Kabar latihanmu">' + pendamping + '</aside>' if pendamping else ''}
</div></main><footer class="murid-kaki-st">{T.TAGLINE} <span aria-hidden="true">✦</span> Satu langkah setiap kali.</footer>
</body></html>'''
    return isi.encode()


def _badan_teks_st(teks: str) -> str:
    """Saudara _badan_teks untuk kelas Stitch (.kerja-teks-st / .kerja-tanya-st).

    Dipisah supaya kartu Stitch memakai kelasnya sendiri — kelas lama (.teks /
    .tanya) hidup di CSS_MURID yang TIDAK diimpor halaman Stitch.
    """
    baris = [b.strip() for b in teks.split("\n") if b.strip()]
    if len(baris) == 1:
        return f'<div class="kerja-teks-st">{_escape(baris[0])}</div>'
    return "".join(
        f'<div class="{"kerja-tanya-st" if i == len(baris) - 1 else "kerja-teks-st"}">'
        f"{_escape(b)}</div>"
        for i, b in enumerate(baris)
    )


def halaman_kerja_baru(
    kon, siswa_id: int, sesi_id: int, tersimpan: int = 0,
    topik_paket: Topik | None = None, kabar_foto: str = "",
    jalur_aksi: str | None = None, akses_tautan: bool = False,
) -> bytes | None:
    """Versi Stitch dari halaman kerja murid (S4).

    ``akses_tautan`` dipakai untuk tautan satu-sesi tanpa login. Data yang
    dirender tetap melewati palang siswa+sesi yang sama; yang berubah hanya
    tujuan form dan hilangnya navigasi menuju area akun/sesi lain.

    Logika data, struktur kartu, mode drill, timer, jaga (guard submit/
    beforeunload) — SEMUA persis sama dengan halaman_kerja; yang berubah hanya
    markup + kelas CSS (mengadopsi GAYA_STITCH). Palang mutlak: TIDAK memuat
    kata kunci/malrule/diagnosa.

    Sumber visual (arsip lokal): ~/Documents/osn-referensi/desain-ui/stitch/murid_kerjakan_soal_mobile/screen.png
    — topbar sticky teal+coral, timer strip teal, kartu soal putih dgn nomor
    badge bulat teal menggantung, Jawabanku input pusat, Caraku pil 2-kolom
    radio, save strip sticky bawah coral penuh.
    """
    from style_stitch import gaya_stitch

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
    detik_lalu = int(info.get("detik_lalu") or 0)
    sudah_dikirim = bool(info.get("selesai"))

    if sudah_dikirim:
        if akses_tautan:
            return None
        isi = f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand.judul("Jawaban sudah dikirim")}</title>{brand.tag_kepala()}
<style>{gaya_stitch()}</style></head><body class="st kerja-editorial-st">
<main class="kerja-badan-st kerja-selesai-st" aria-labelledby="judul-kerja">
<p class="kerja-alis-st">CATATAN LATIHAN</p>
<h1 id="judul-kerja">Selesai untuk sekarang.</h1>
<div class="kerja-tersimpan-st" role="status">
<span class="ikon">✓</span><span><b>Jawabanmu sudah dikirim.</b><br>
Gurumu akan memeriksanya. Kamu tidak perlu mengirim ulang.</span></div>
<p><a class="kerja-btn-sekunder-st" href="/murid">Kembali ke sesi lain</a></p>
</main></body></html>"""
        return isi.encode()

    kartu: list[str] = []
    bagian_kini = None
    for s in daftar:
        if s["bagian"] != bagian_kini:
            bagian_kini = s["bagian"]
            judul = topik_paket.judul_bagian.get(
                bagian_kini, f"Bagian {bagian_kini}"
            )
            kartu.append(f'<div class="kerja-bagian-st">{judul}</div>')
            if bagian_kini in topik_paket.catatan_bagian:
                kartu.append(
                    f'<div class="kerja-catatan-bagian-st">'
                    f"{topik_paket.catatan_bagian[bagian_kini]}</div>"
                )
        t = s["terjawab"] or {}
        ssid = s["sesi_soal_id"]
        belum = " checked" if t.get("belum_pernah") else ""
        bintang = '<span class="kerja-bintang-st">★</span>' if s["tantangan"] else ""
        nomor = f'<span class="kerja-nomor-st">{s["nomor"]}</span>'
        teks = visual_renderer.render_pertanyaan(
            s["penyajian"], gaya="stitch", namespace=str(s["nomor"])
        )

        if drill:
            catatan_soal = ""
            if timer_mode == "soal":
                catatan_soal = (
                    '<div class="catatan-soal-timer-st" style="display:none">'
                    "Waktu untuk soal ini habis — lanjut ke soal berikutnya.</div>"
                )
            kartu.append(f"""
<div class="kerja-soal-st drill">
  {nomor}{bintang}
  {teks}
  <div class="kerja-jawab-st">
    <label class="head-jawab" for="jawab-{ssid}">Jawabanku</label>
    <input type="text" id="jawab-{ssid}" name="jwb_{ssid}"
           value="{_escape(t.get('jawaban', ''))}" autocomplete="off">
  </div>
  <label class="kerja-centang-st">
    <input type="checkbox" name="blm_{ssid}"{belum}>
    belum pernah lihat soal seperti ini
  </label>
  {catatan_soal}
</div>""")
            continue

        restate = ""
        if s["minta_restatement"]:
            nilai = _escape(t.get("restatement", ""))
            restate = (
                f'<label class="kerja-label-st" for="restate-{ssid}">Soal ini mintanya apa? '
                "(tulis pakai kalimatmu sendiri)</label>"
                f'<textarea class="kerja-restate-st" id="restate-{ssid}" name="restate_{ssid}">{nilai}</textarea>'
            )

        cara_tersimpan = t.get("cara", "") or ""
        pilihan_kini = ""
        teks_cara = cara_tersimpan
        if cara_tersimpan.startswith(AWALAN_PILIHAN):
            sisa = cara_tersimpan[len(AWALAN_PILIHAN):]
            pilihan_kini, _, teks_cara = sisa.partition(" — ")
            pilihan_kini = pilihan_kini.strip()
            teks_cara = teks_cara.strip()

        tombol = "".join(
            f'<label class="kerja-pill-st">'
            f'<input type="radio" name="pilih_{ssid}" value="{kode}"'
            f'{" checked" if kode == pilihan_kini else ""}>'
            f"<span>{_escape(teks)}</span></label>"
            for kode, teks in PILIHAN_CARA
        )

        kartu.append(f"""
<div class="kerja-soal-st">
  {nomor}{bintang}
  {teks}
  {restate}
  <fieldset class="kerja-cara-pilih-st">
  <legend class="kerja-label-st">Caraku — pilih dulu yang paling mirip:</legend>
  <div class="kerja-pill-grup-st">{tombol}</div>
  </fieldset>
  <label class="kerja-label-st" for="cara-{ssid}">Kalau mau, tulis lebih jelas di sini (boleh dikosongkan):</label>
  <textarea class="kerja-cara-st" id="cara-{ssid}" name="cara_{ssid}">{_escape(teks_cara)}</textarea>
  <div class="kerja-jawab-st">
    <label class="head-jawab" for="jawab-{ssid}">Jawabanku</label>
    <input type="text" id="jawab-{ssid}" name="jwb_{ssid}"
           value="{_escape(t.get('jawaban', ''))}" autocomplete="off">
  </div>
  <label class="kerja-centang-st">
    <input type="checkbox" name="blm_{ssid}"{belum}>
    belum pernah lihat soal seperti ini
  </label>
</div>""")

    # Konfirmasi setelah simpan.
    kabar = ""
    if tersimpan:
        kabar = (
            '<div class="kerja-tersimpan-st">'
            '<span class="ikon">✓</span>'
            f"<span>Tersimpan ✓ — {tersimpan} soal sudah "
            f"masuk. Boleh lanjut, atau tutup halaman ini.</span></div>"
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
            "tekan <b>Selesai &amp; kirim</b> di paling bawah. Kamu juga bisa menyimpan sementara dulu.</p>"
        )
    else:
        petunjuk = (
            "<p><b>Cara mengerjakan — baca dulu:</b></p>"
            "<p>Tiap soal ada bagian <b>Caraku</b>. Pilih satu yang paling mirip dengan "
            "caramu mendapat jawaban. Kalau mau, tulis juga caranya di kotak tulisan.</p>"
            "<p>Kalau ada soal yang belum pernah kamu lihat, centang kotaknya. Itu "
            "<b>bukan</b> salah — itu berguna untuk gurumu.</p>"
            "<p>Tidak apa-apa ada yang kosong. Jangan menebak asal. Kalau sudah selesai, "
            "tekan <b>Selesai &amp; kirim</b> di paling bawah. Kamu juga bisa menyimpan sementara dulu.</p>"
        )

    # Timer Latihan Cepat — strip id timer-strip & timer-tampil dipertahankan
    # supaya test drill & JS tetap mengenali elemen yang sama.
    strip = ""
    if drill and timer_mode == "sesi":
        strip = (
            '<div class="kerja-timer-st hanya-layar" id="timer-strip">'
            '<span class="material-symbols-outlined" style="font-size:1.1rem">schedule</span>'
            "Sisa waktu: <b id=\"timer-tampil\">"
            f"{durasi_menit:02d}:00</b>"
            '<span id="timer-pesan" style="display:none">'
            " — waktu habis, kerjakan sebisanya dan simpan</span></div>"
        )

    # JS timer & jaga — persis sama dengan halaman_kerja (perilaku tidak berubah).
    skrip = ""
    if drill and timer_mode in ("sesi", "soal"):
        skrip = f"""
<script>
(function(){{
  var MODE = {json.dumps(timer_mode)};
  var DETIK = {durasi_menit * 60};
  var DETIK_LALU = {detik_lalu};
  var AUTO = {1 if timer_auto else 0};
  var mulai = Date.now() - DETIK_LALU * 1000;
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
          if (f) {{
            f.dataset.kirimOtomatis = "1";
            var a = document.createElement("input");
            a.type = "hidden"; a.name = "aksi"; a.value = "selesai";
            f.appendChild(a); f.submit();
          }}
          return;
        }}
        var p = document.getElementById("timer-pesan");
        if (p) p.style.display = "";
        if (strip) strip.className = "kerja-timer-st habis hanya-layar";
      }}
      if (tampil) tampil.textContent = fmt(sisa);
    }}
    tick();
    setInterval(tick, 1000);
  }} else if (MODE === "soal") {{
    var kartu = document.querySelectorAll(".kerja-soal-st");
    var mulaiSoal = {{}};
    document.addEventListener("focusin", function(ev){{
      var k = ev.target.closest ? ev.target.closest(".kerja-soal-st") : null;
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
        var n = k.querySelector(".catatan-soal-timer-st");
        if (n) n.style.display = "";
      }});
    }}
    setInterval(tick, 1000);
  }}
}})();
</script>
"""

    jaga = """
<script>
(function(){
  var f = document.querySelector('form');
  if (!f) return;
  var kotor = false;
  f.addEventListener('input', function(){ kotor = true; }, true);
  f.addEventListener('change', function(){ kotor = true; }, true);
  f.addEventListener('submit', function(e){
    var pemicu = e.submitter;
    kotor = false;
    if (pemicu) {
      if (pemicu.name) {
        var aksi = document.createElement('input');
        aksi.type = 'hidden'; aksi.name = pemicu.name; aksi.value = pemicu.value;
        f.appendChild(aksi);
      }
      pemicu.disabled = true;
      pemicu.dataset.labelAsli = pemicu.textContent;
      pemicu.textContent = 'Menyimpan\\u2026';
    }
  });
  window.addEventListener('pageshow', function(){
    var tombol = f.querySelectorAll('button[type=submit]');
    for (var i=0;i<tombol.length;i++) {
      tombol[i].disabled = false;
      if (tombol[i].dataset.labelAsli) tombol[i].textContent = tombol[i].dataset.labelAsli;
    }
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

    # Kirim foto cara pengerjaan hanya tersedia untuk akun murid. Tautan
    # berbagi sengaja hanya memberi kapabilitas mengerjakan satu sesi; upload
    # berkas merupakan permukaan terpisah dan tidak ikut dibuka.
    blok_foto = ""
    if not akses_tautan:
        daftar_foto = ""
        kabar_foto_html = ""
        if kabar_foto:
            kabar_foto_html = (
                f'<p class="kerja-foto-kabar-st" role="status">{_escape(kabar_foto)}</p>'
            )
        n_foto = kon.execute(
            "SELECT COUNT(*) AS n FROM lampiran WHERE sesi_id = ?", (sesi_id,)
        ).fetchone()["n"]
        if n_foto:
            daftar_foto = (
                f'<p class="kerja-foto-jumlah-st">Sudah terkirim: {n_foto} foto. '
                "Boleh kirim lagi kalau ada lembar lain.</p>"
            )
        blok_foto = f"""
<div class="kerja-foto-st hanya-layar">
  <div class="kerja-foto-kepala-st">
    <span class="material-symbols-outlined">photo_camera</span>
    <b>Kerjakan di kertas? Kirim fotonya</b>
  </div>
  <p class="kerja-foto-sub-st">Foto lembar yang sudah kamu isi (boleh
  tulisan tangan). Gurumu yang akan memeriksa — kamu tidak perlu
  mengetik ulang.</p>
  {kabar_foto_html}
  {daftar_foto}
  <form method="post" action="/murid/foto/{sesi_id}"
        enctype="multipart/form-data" class="kerja-foto-form-st">
    <label class="kerja-label-st" for="foto-cara">Pilih foto lembar</label>
    <input type="file" id="foto-cara" name="foto" accept="image/*" capture="environment">
    <button type="submit" class="kerja-btn-sekunder-st">Kirim foto caraku</button>
  </form>
</div>"""

    aksi = _escape(jalur_aksi or f"/murid/kerjakan/{sesi_id}")
    tautan_tutup = "" if akses_tautan else (
        '<a class="cta-keluar hanya-layar" href="/murid">'
        '<span class="material-symbols-outlined" style="font-size:1.1rem">close</span> Tutup</a>'
    )
    script_mulai = ""
    if akses_tautan:
        script_mulai = (
            "<script>fetch(" + json.dumps(aksi)
            + ", {method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},"
            "body:'aksi=mulai',keepalive:true}).catch(function(){});</script>"
        )
    navigasi_bawah = "" if akses_tautan else (
        '<div class="kerja-navigasi-st hanya-layar">'
        '<button class="kerja-btn-sekunder-st" type="button" onclick="window.print()">'
        '<span class="material-symbols-outlined" style="font-size:1.1rem">print</span> Cetak / PDF</button></div>'
        '<form method="post" action="/keluar" class="hanya-layar" style="margin-top:0.7rem">'
        '<button class="kerja-btn-sekunder-st" type="submit">Keluar</button></form>'
    )

    isi = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand.judul(f"Kerjakan — {_escape(topik_paket.judul_lembar)}")}</title>
{brand.tag_kepala()}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
<style>{gaya_stitch()}</style></head><body class="st kerja-editorial-st">
<header class="kerja-topbar-st">
  <div class="brand">
    {brand.mark("topbar", kelas="ik-owl")}
    <span class="nama-osn">{T.NAMA_PRODUK}</span>
  </div>
  {tautan_tutup}
</header>
<main class="kerja-badan-st" aria-labelledby="judul-kerja">
<header class="kerja-pembuka-st">
<p class="kerja-alis-st">LEMBAR LATIHAN</p>
<h1 id="judul-kerja">{'Latihan cepat' if drill else 'Tunjukkan caramu.'}</h1>
<p class="kerja-meta-st"><b>Halo, {_escape(info['nama'])}</b> &middot; {_escape(info['tanggal'])}
 &middot; {_escape(label_kelas(info['level']))} &middot; {len(daftar)} soal {penanda_tahap(info.get('tujuan', 'bebas'))}
 {'&middot; Latihan Cepat' if drill else ''}</p>
</header>
{strip}
{kabar}
<div class="kerja-petunjuk-st">
  <div class="baris-petunjuk">
    <span class="material-symbols-outlined" style="color:{T.AKSEN_MURID_UTAMA};flex:none">lightbulb</span>
    <div>
      {petunjuk}
    </div>
  </div>
</div>
<form method="post" action="{aksi}">
{" ".join(kartu)}
<div class="kerja-simpan-strip-st hanya-layar">
  <button type="submit" name="aksi" value="simpan" class="sekunder">Simpan sementara</button>
  <button type="submit" name="aksi" value="selesai">Selesai &amp; kirim
    <span class="material-symbols-outlined">arrow_forward</span></button>
</div>
</form>
{navigasi_bawah}
{blok_foto}
{jaga}{skrip}{script_mulai}
</main></body></html>"""
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
        """SELECT id, tanggal, level, topik, mode, jenis, tujuan,
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
        tag_latihan = penanda_tahap(b["tujuan"])
        if not tag_latihan and b["jenis"] == "remedial":
            fokus = _nama_fokus_remedial(kon, int(b["id"]))
            tag_latihan = (
                '<span class="badge-latihan">Remedial</span> '
                f'<span>Fokus {_escape(fokus)}</span>'
            )
        elif not tag_latihan and b["mode"] == "drill":
            tag_latihan = '<span class="badge-latihan">latihan</span>'
        kartu.append(
            f'<a class="kartu-sesi" href="/murid/kerjakan/{b["id"]}">'
            f'<span class="ikon-sesi" style="background:{warna}"></span>'
            f'<span class="isi-sesi">'
            f'<span class="tanggal-sesi">{_escape(b["tanggal"])}</span>'
            f'<span class="meta-sesi">{_escape(label_kelas(b["level"]))} '
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
<title>{brand.judul("Sesiku")}</title>
{brand.tag_kepala()}<style>{CSS_MURID}</style></head><body><div class="wrap">
<div class="murid-header">
  <img src="{icons.OWL}" alt="" class="owl-mascot" width="40" height="40">
  <h1>Halo, {_escape(nama)}!</h1>
  <span class="hint-silap">Bukan kamu? Tekan Keluar dulu.</span>
</div>
{banner}
<p class="sub-judul">Pilih sesi untuk mulai latihan</p>
<form method="post" action="/keluar" class="keluar-form"><button class="btn secondary" type="submit">Keluar</button></form>
<div class="daftar-sesi-grup">
{kartu_html}
</div>
</div></body></html>"""
    return isi.encode()


def halaman_hasil_murid(kon, siswa_id: int, sesi_id: int) -> bytes | None:
    """Halaman /murid/hasil/<id> — anak melihat letak salahnya.

    Poin b feedback Filia ("apa yang aplikasi bisa bantu agar anak mampu
    meningkatkan nilainya"): benar/salah saja tidak mengajari apa pun.
    Halaman ini menampilkan, per soal: jawaban anak sendiri, benar/salah,
    dan LANGKAH pengerjaan yang benar (Soal.pembahasan).

    Hanya terbuka setelah guru mereview — gerbangnya di students.hasil_murid
    (None = belum direview / bukan miliknya), dan pemanggil menjawab 404.

    Yang sengaja TIDAK ditampilkan: kode diagnosis K/H/E/N/B, malrule, dan
    alasan. Anak butuh tahu letak salahnya, bukan label tipe kesalahannya.
    """
    from style_stitch import gaya_stitch

    hasil = hasil_murid(kon, siswa_id, sesi_id)
    if hasil is None:
        return None

    kartu = []
    for b in hasil["soal"]:
        if not b["dijawab"]:
            status = '<span class="st-badge selesai">Belum dijawab</span>'
            kelas = "hasil-soal-st kosong"
        elif b["benar"]:
            status = '<span class="st-badge diagnostik">Benar</span>'
            kelas = "hasil-soal-st benar"
        else:
            status = '<span class="st-badge baru">Belum tepat</span>'
            kelas = "hasil-soal-st salah"

        jawabku = ""
        if b["dijawab"]:
            jawabku = (
                f'<p class="hasil-jawabku-st">Jawabanmu: '
                f'<b>{_escape(b["jawabanku"])}</b></p>'
            )

        # Pembahasan = langkah menuju jawaban. Ditampilkan untuk SEMUA soal
        # (termasuk yang benar): anak yang benar karena menebak tetap perlu
        # melihat caranya. Kalau template belum punya pembahasan, blok ini
        # tidak muncul sama sekali — lebih baik kosong daripada basa-basi.
        langkah = ""
        if b["pembahasan"]:
            langkah = (
                '<div class="hasil-langkah-st">'
                '<span class="material-symbols-outlined">lightbulb</span>'
                f'<div><b>Caranya:</b> {_escape(b["pembahasan"])}</div></div>'
            )

        kartu.append(
            f'<div class="{kelas}">'
            f'<div class="hasil-kepala-st">'
            f'<span class="hasil-nomor-st">{b["nomor"]}</span>{status}</div>'
            f'<div class="hasil-teks-st">{visual_renderer.render_pertanyaan(b["penyajian"], gaya="stitch", namespace=str(b["nomor"]))}</div>'
            f"{jawabku}{langkah}</div>"
        )

    n_benar, n_soal = hasil["benar"], hasil["jumlah"]
    # Nada ringkasan sengaja tidak menghakimi: yang ditonjolkan adalah
    # "sudah dikoreksi, ini caranya", bukan skor telanjang.
    if n_benar == n_soal:
        pesan = "Semua benar! Baca juga caranya supaya makin mantap."
    elif n_benar == 0:
        pesan = "Belum ada yang tepat — tidak apa-apa. Baca caranya, lalu coba lagi."
    else:
        pesan = "Yang belum tepat ada caranya di bawah. Baca pelan-pelan, ya."

    # Kartu rumus (poin c feedback Filia): hanya untuk konsep yang anak
    # BELUM tepat. Diletakkan di atas daftar soal, saat anak paling siap
    # menerimanya — bukan sebagai modul teori terpisah yang harus dibaca
    # sebelum boleh berlatih (anak SD tidak membaca teori yang tidak
    # sedang ia butuhkan). Semua benar -> tidak ada kartu, jangan
    # menyodorkan teori tanpa keperluan.
    import rumus as modul_rumus

    salah_ids = [
        b["template_id"] for b in hasil["soal"]
        if b["dijawab"] and not b["benar"]
    ]
    from learning_visuals import render_bantuan

    kartu_rumus = modul_rumus.kartu_untuk_banyak(salah_ids)
    blok_rumus = ""
    if kartu_rumus:
        isi_kartu = "".join(
            '<div class="rumus-kartu-st">'
            f'<div class="rumus-judul-st">{_escape(k.judul)}</div>'
            f'<div class="rumus-inti-st">{_escape(k.inti)}</div>'
            + (
                f'<div class="rumus-contoh-st">Contoh: {_escape(k.contoh)}</div>'
                if k.contoh else ""
            )
            + (render_bantuan(k.bantuan, konteks="hasil_sah",
                              namespace=f"hasil-{sesi_id}-kartu-{indeks}")
               if k.bantuan is not None else "")
            + "</div>"
            for indeks, k in enumerate(kartu_rumus)
        )
        blok_rumus = (
            '<div class="rumus-blok-st">'
            '<div class="rumus-kepala-st">'
            '<span class="material-symbols-outlined">menu_book</span>'
            "<b>Ingat rumusnya dulu</b></div>"
            f"{isi_kartu}</div>"
        )

    isi = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand.judul("Hasil &amp; cara")}</title>
{brand.tag_kepala()}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
<style>{gaya_stitch()}</style></head><body class="st hasil-editorial-st">
<header class="kerja-topbar-st">
  <div class="brand">
    {brand.mark("topbar", kelas="ik-owl")}
    <span class="nama-osn">{T.NAMA_PRODUK}</span>
  </div>
  <a class="cta-keluar hanya-layar" href="/murid"><span aria-hidden="true">←</span> Sesi lain</a>
</header>
<main class="kerja-badan-st" aria-labelledby="judul-hasil">
<header class="kerja-pembuka-st">
<p class="kerja-alis-st">CATATAN LATIHAN</p>
<h1 id="judul-hasil">Lihat hasil &amp; caranya.</h1>
<p class="kerja-meta-st"><b>Halo, {_escape(hasil['nama'])}</b> &middot;
 {_escape(hasil['tanggal'])} &middot; {_escape(label_kelas(hasil['level']))}</p>
</header>
<div class="hasil-ringkas-st">
  <div class="hasil-skor-st">{n_benar}<span>/{n_soal}</span><small>jawaban benar</small></div>
  <div class="hasil-pesan-st">{pesan}</div>
</div>
{blok_rumus}
{"".join(kartu)}
<div class="kerja-navigasi-st hanya-layar">
  <a class="kerja-btn-sekunder-st" href="/murid/kerjakan/{sesi_id}">Lihat lembarku</a>
</div>
</main></body></html>"""
    return isi.encode()
