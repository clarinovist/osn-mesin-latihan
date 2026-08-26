"""Halaman murid — anak mengerjakan langsung di browser (Fase 4).

Palang keras yang menegakkan halaman ini:

  Rute murid tidak boleh pernah menyentuh kunci, malrule, diagnosis,
  atau laporan. Bukan niat baik — ditegakkan test
  (__tests__/test_murid.py::test_palang_murid) yang mem-blokir akses
  kolom-kolom itu di level sqlite3.Row dan mengintip setiap HTML yang
  keluar dari fungsi halaman.

Arsitektur datanya sengaja tipis: jawaban anak disimpan lewat
basis.simpan_jawaban() yang sama dengan yang dipakai alur kertas-guru.
Tidak ada tabel baru, tidak ada jalur simpan kedua — satu fakta, satu
tempat. Yang berbeda hanya siapa yang mengetik: guru tidak lagi menjadi
perantara ketikan.
"""

from __future__ import annotations

import html

from basis import isi_sesi
from templates import Soal


def _escape(t: str) -> str:
    return html.escape(str(t))


def sesi_murid(kon, siswa_id: int, sesi_id: int) -> dict | None:
    """Data sesi versi murid — TANPA kunci/malrule/diagnosis.

    Satu-satunya fungsi pengambil data untuk seluruh rute murid. Test palang
    mengawasi persis fungsi ini: kalau suatu hari seseorang menambah SELECT
    kunci ke dalamnya, test akan gagal sebelum sampai produksi.
    """
    baris = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, w.nama, w.id AS siswa_id
           FROM sesi s JOIN siswa w ON w.id = s.siswa_id
           WHERE s.id = ? AND s.siswa_id = ?""",
        (sesi_id, siswa_id),
    ).fetchone()
    if not baris:
        return None  # bukan sesi milik murid ini ATAU tidak ada
    return dict(baris)


def soal_murid(kon, sesi_id: int, siswa_id: int) -> list[dict]:
    """Daftar soal versi murid: identitas + teks saja, tanpa kunci.

    Teks soal dibangun ulang dari parameter (aturan yang sama dengan halaman
    guru), lalu objek Soal-nya langsung dipangkas: hanya template_id dan teks
    yang boleh keluar. Kalau besok Soal mendapat field baru yang sensitif,
    daftar putih ini tetap aman — yang tidak disebut, tidak lolos.
    """
    from web import _soal_dari_baris  # impor terlambat: hindari siklus impor

    baris_baris = isi_sesi(kon, sesi_id)
    # pastikan sesi ini benar milik murid sebelum satu pun soal dikirim
    if not sesi_murid(kon, siswa_id, sesi_id):
        return []
    keluar: list[dict] = []
    for b in baris_baris:
        soal: Soal = _soal_dari_baris(b)
        jawab = kon.execute(
            """SELECT restatement, cara, jawaban, belum_pernah
               FROM jawaban j JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
               WHERE ss.sesi_id = ? AND ss.nomor = ?""",
            (sesi_id, b["nomor"]),
        ).fetchone()
        keluar.append(
            {
                "nomor": b["nomor"],
                "sesi_soal_id": b["sesi_soal_id"],
                "template_id": b["template_id"],
                "teks": soal.teks,
                "bagian": soal.bagian,
                "tantangan": soal.tantangan,
                "minta_restatement": soal.minta_restatement,
                "terjawab": dict(jawab) if jawab else None,
            }
        )
    return keluar


CSS_MURID = """
.murid-header { display: flex; align-items: center; gap: .8rem; margin-bottom: 1rem; }
.murid-header h1 { margin: 0; flex: 1; }
.btn {
  display: inline-block; padding: .7rem 1.2rem; border-radius: 9px;
  border: none; background: #16213e; color: #fff; font-size: 1rem;
  text-decoration: none; cursor: pointer;
}
.btn.secondary { background: #eef1f6; color: #16213e; border: 1px solid #ccd3dd; }
.soal-murid textarea {
  width: 100%; min-height: 84px; border: 1.5px dashed #99a;
  border-radius: 8px; padding: .6rem; font-size: 1rem; font-family: inherit;
  background: #fafafc;
}
.soal-murid input[type=text] {
  font-size: 1.15rem; padding: .55rem .7rem; border: 2px solid #333;
  border-radius: 8px; min-width: 7rem;
}
.baris-jawab { display: flex; align-items: baseline; gap: .6rem; margin-top: .7rem; }
.centang-baris {
  display: flex; align-items: center; gap: .5rem; margin-top: .7rem;
  font-size: .95rem; color: #444;
}
.simpan-strip { position: sticky; bottom: 0; padding: .8rem 0; background: #f0f1f4; }
.simpan-strip .btn { width: 100%; font-size: 1.1rem; padding: .95rem; }

/* Pilihan cepat "Caraku" — target sentuh penuh, bukan lingkaran radio kecil.
   Seluruh kotak bisa di-tap; anak tidak perlu membidik titik 20px. */
.pilih-cara-grup {
  display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: .8rem;
}
.pilih-cara {
  display: flex; align-items: center; gap: .45rem;
  border: 1.5px solid #ccd3dd; border-radius: 999px;
  padding: .55rem .9rem; min-height: 44px;
  background: #fff; cursor: pointer; font-size: .95rem;
}
.pilih-cara input { width: 1.2rem; height: 1.2rem; flex: none; }
/* :has() didukung Safari 15.4+ dan Chrome 105+; kalau peramban lebih tua,
   yang hilang hanya penandaan warna — radio-nya tetap berfungsi. */
.pilih-cara:has(input:checked) {
  border-color: #16213e; background: #eef3fb; font-weight: 600;
}

/* Konfirmasi setelah simpan. Tanpa ini anak tidak tahu jawabannya masuk,
   lalu menekan tombol berulang kali atau mengira kerjanya hilang. */
.tersimpan {
  background: #e8f6ec; border: 1px solid #9ed4b0; color: #14532d;
  border-radius: 10px; padding: .8rem 1rem; margin-bottom: 1rem;
  font-size: .98rem;
}
"""


def halaman_kerja(
    kon, siswa_id: int, sesi_id: int, tersimpan: int = 0
) -> bytes | None:
    """Lembar interaktif murid: baca soal, tulis caraku + jawaban."""
    info = sesi_murid(kon, siswa_id, sesi_id)
    if not info:
        return None
    daftar = soal_murid(kon, sesi_id, siswa_id)

    kartu: list[str] = []
    bagian_kini = None
    for s in daftar:
        if s["bagian"] != bagian_kini:
            bagian_kini = s["bagian"]
            kartu.append(f'<div class="bagian">Bagian {bagian_kini}</div>')
        t = s["terjawab"] or {}
        restate = ""
        if s["minta_restatement"]:
            nilai = _escape(t.get("restatement", ""))
            restate = (
                '<label class="label">Soal ini mintanya apa? '
                "(tulis pakai kalimatmu sendiri)</label>"
                f'<textarea name="restate_{s["sesi_soal_id"]}">{nilai}</textarea>'
            )
        belum = " checked" if t.get("belum_pernah") else ""

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

        ssid = s["sesi_soal_id"]
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
  <div class="teks-soal">{_escape(s['teks'])}</div>
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

    isi = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kerjakan — Latihan Pola Bilangan</title>
<style>{CSS_MURID}</style></head><body><div class="wrap">
<div class="murid-header">
  <h1>Halo, {_escape(info['nama'])}</h1>
  <a class="btn secondary" href="/murid">Sesi lain</a>
</div>
<p>{_escape(info['tanggal'])} &middot; level {_escape(info['level'])}
 &middot; {len(daftar)} soal</p>
{kabar}
<form method="post" action="/murid/kerjakan/{sesi_id}">
{"".join(kartu)}
<div class="simpan-strip"><button type="submit" class="btn">Simpan jawabanku</button></div>
</form>
<form method="post" action="/keluar" style="margin-top:1rem"><button class="btn secondary" type="submit">Keluar</button></form>
</div></body></html>"""
    return isi.encode()


def halaman_daftar_sesi(kon, siswa_id: int, nama: str) -> bytes:
    """/murid — daftar sesi milik murid ini saja."""
    baris = kon.execute(
        """SELECT id, tanggal, level,
                  (SELECT COUNT(*) FROM sesi_soal ss WHERE ss.sesi_id = s.id) AS jumlah
           FROM sesi s WHERE s.siswa_id = ?
           ORDER BY s.id DESC""",
        (siswa_id,),
    ).fetchall()
    kartu = "".join(
        f'<a class="soal daftar-sesi" href="/murid/kerjakan/{b["id"]}">'
        f"<b>{_escape(b['tanggal'])}</b> &middot; level {_escape(b['level'])}"
        f" &middot; {b['jumlah']} soal"
        f"</a>"
        for b in baris
    ) or "<p>Belum ada sesi. Minta gurumu membuatkan.</p>"
    isi = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sesiku</title><style>{CSS_MURID}</style></head><body><div class="wrap">
<h1>Halo, {_escape(nama)}</h1>
<form method="post" action="/keluar" style="margin:.6rem 0"><button class="btn secondary" type="submit">Keluar</button></form>
{kartu}
</div></body></html>"""
    return isi.encode()


def simpan_jawaban_murid(kon, siswa_id: int, sesi_id: int, data: dict) -> int | None:
    """Simpan jawaban dari form murid. Palang: hanya sesi miliknya sendiri.

    Mengembalikan JUMLAH soal yang tersimpan, atau None kalau sesi bukan
    milik murid ini — pemanggil harus menolak, bukan diam-diam menyimpan ke
    sesi orang lain.

    Jumlahnya dipakai halaman untuk memberi tahu anak berapa soal yang
    benar-benar masuk. "Berhasil" saja tidak cukup: anak yang mengira sudah
    mengisi 12 soal tapi ternyata 9 perlu tahu sekarang, bukan nanti.
    """
    if not sesi_murid(kon, siswa_id, sesi_id):
        return None
    kode_sah = {k for k, _ in PILIHAN_CARA}
    jumlah = 0
    for b in isi_sesi(kon, sesi_id):
        ssid = b["sesi_soal_id"]
        jawaban = data.get(f"jwb_{ssid}", "").strip()
        teks_cara = data.get(f"cara_{ssid}", "").strip()
        pilihan = data.get(f"pilih_{ssid}", "").strip()
        restate = data.get(f"restate_{ssid}", "").strip()
        belum = f"blm_{ssid}" in data

        # Pilihan cepat digabung ke kolom `cara` yang sama, bukan kolom baru.
        # Alasannya: seluruh alur diagnosis (diagnosa.py) dan laporan guru
        # sudah membaca `cara`; kolom baru berarti dua tempat yang harus
        # diingat, dan yang terlupa akan gagal senyap.
        #
        # Pilihan yang tidak dikenal DIBUANG, bukan disimpan apa adanya:
        # nilainya datang dari form dan tidak boleh dipercaya.
        if pilihan and pilihan in kode_sah:
            cara = AWALAN_PILIHAN + pilihan
            if teks_cara:
                cara += " — " + teks_cara
        else:
            cara = teks_cara

        if not (jawaban or cara or restate or belum):
            continue  # soal dilewati anak: biarkan kosong, jangan buat baris
        from basis import simpan_jawaban

        simpan_jawaban(
            kon,
            ssid,
            jawaban=jawaban,
            cara=cara,
            restatement=restate,
            belum_pernah=belum,
        )
        jumlah += 1
    return jumlah


# Nama siswa yang terhubung ke akun murid dicari lewat tabel siswa:
# nama akun == nama siswa. Sengaja begitu supaya guru tidak perlu mengelola
# pemetaan dua arah — satu nama, dua tempat yang harus cocok.


def siswa_dari_akun(kon, pengguna: str) -> int | None:
    """ID siswa untuk nama akun murid ini, atau None kalau belum ada."""
    baris = kon.execute(
        "SELECT id FROM siswa WHERE nama = ? COLLATE NOCASE", (pengguna.strip(),)
    ).fetchone()
    return int(baris["id"]) if baris else None


# Pilihan cepat "Caraku" — dibaca bersama diagnosa.py.
#
# Kotak Caraku yang KOSONG membuat diagnosis mati: `diagnosa()` menandai
# "ada jawaban tanpa Caraku" sebagai N (menebak). Di kertas itu masuk akal —
# anak yang mengerjakan pasti meninggalkan coretan. Di HP tidak: mengetik
# kalimat di keyboard ponsel jauh lebih mahal daripada mencoret di kertas,
# dan anak yang PAHAM pun sering melewatinya.
#
# Terkonfirmasi saat uji di HP nyata (25 Agustus 2026): "caraku sering
# kosong". Artinya anak yang tahu caranya tercatat sebagai penebak, lalu
# tindak lanjutnya meleset arah.
#
# Pilihan yang bisa di-tap membuat kekosongan berhenti ambigu. Ia bukan
# pengganti coretan — teksnya tetap ada dan tetap lebih berharga — tapi satu
# ketukan sudah cukup memisahkan "aku hitung satu-satu" (H, wajar untuk
# levelnya) dari "aku tebak" (N, jujur) dari "aku pakai rumus" (siap naik).
#
# Nilai disimpan ke kolom `cara` yang sama, diberi awalan "[pilihan]" supaya
# guru bisa membedakannya dari tulisan anak sendiri saat membaca laporan.
PILIHAN_CARA: tuple[tuple[str, str], ...] = (
    ("hitung_satu_satu", "Aku hitung satu per satu"),
    ("lihat_pola", "Aku lihat polanya"),
    ("pakai_rumus", "Aku pakai cara cepat / rumus"),
    ("tanya_ingat", "Aku ingat dari soal yang mirip"),
    ("tebak", "Aku tebak saja"),
    ("bingung", "Aku bingung"),
)

AWALAN_PILIHAN = "[pilihan] "


def label_pilihan(kode: str) -> str:
    """Label yang dibaca guru untuk sebuah kode pilihan."""
    for k, teks in PILIHAN_CARA:
        if k == kode:
            return teks
    return kode
