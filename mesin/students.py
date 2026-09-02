"""Lapisan data sisi anak: ambil soal, simpan jawaban, kepemilikan akun.

Dipecah dari students.py (refactor 31 Aug 2026): halaman-halamannya pindah
ke student_pages.py; modul ini kini murni data + pembatasan akun, tanpa
HTML. Palang tetap: tidak pernah membaca kolom kunci/malrule untuk anak —
dijaga test_palang_* (monkeypatch sqlite3.Row).
"""

from __future__ import annotations

import html

import auth
from database import isi_sesi
from templates import Soal
from topics import dari_sesi



def _escape(t: str) -> str:
    return html.escape(str(t))

def _ambil_topik(baris) -> str:
    """Label topik untuk baris sesi; kolom belum ada / aneh -> bawaan."""
    try:
        nilai = baris["topik"]
    except (IndexError, KeyError):
        return dari_sesi(None).id
    return dari_sesi(nilai).id

def sesi_murid(kon, siswa_id: int, sesi_id: int) -> dict | None:
    """Data sesi versi murid — TANPA kunci/malrule/diagnosis.

    Satu-satunya fungsi pengambil data untuk seluruh rute murid. Test palang
    mengawasi persis fungsi ini: kalau suatu hari seseorang menambah SELECT
    kunci ke dalamnya, test akan gagal sebelum sampai produksi.
    """
    baris = kon.execute(
        """SELECT s.id, s.tanggal, s.seed, s.level, s.topik,
                  s.mode, s.timer_mode, s.durasi_menit, s.timer_auto,
                  w.nama, w.id AS siswa_id
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

    # pastikan sesi ini benar milik murid SEBELUM satu pun baris dibaca
    if not sesi_murid(kon, siswa_id, sesi_id):
        return []
    baris_baris = isi_sesi(kon, sesi_id)
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

def hasil_murid(kon, siswa_id: int, sesi_id: int) -> dict | None:
    """Hasil + PEMBAHASAN satu sesi untuk ANAK (poin b feedback Filia).

    Ini SATU-SATUNYA fungsi sisi anak yang boleh menyentuh kebenaran
    jawaban, dan syaratnya ketat:

      - Sesi wajib milik anak ini (lewat sesi_murid) -> None kalau bukan.
      - Sesi wajib SUDAH DIREVIEW guru (`sesi.direview` terisi) -> None
        kalau belum. Tanpa pagar ini, anak bisa membuka pembahasan (yang
        memuat jawaban akhir) sebelum pekerjaannya dinilai — itu sama
        dengan membocorkan kunci.

    Yang dikembalikan per soal: nomor, teks, jawaban anak sendiri,
    benar/salah, dan pembahasan. Yang SENGAJA TIDAK dikembalikan: kode
    diagnosis (K/H/E/N/B), malrule_id, dan alasan. Itu bahasa kerja guru;
    anak butuh tahu letak salahnya, bukan label tipe kesalahannya.

    Catatan palang: fungsi ini memang membaca kolom yang diblokir fixture
    `db_terjaga` (kunci lewat _soal_dari_baris, benar dari diagnosis),
    jadi ia TIDAK boleh dipanggil dari halaman kerja/daftar sesi. Halaman
    hasil adalah permukaan terpisah dengan gerbang direview di atas.
    """
    from teacher_pages import _soal_dari_baris  # late import: hindari siklus

    info = sesi_murid(kon, siswa_id, sesi_id)
    if not info:
        return None
    ditinjau = kon.execute(
        "SELECT direview FROM sesi WHERE id = ?", (sesi_id,)
    ).fetchone()
    if not ditinjau or not ditinjau["direview"]:
        return None

    butir: list[dict] = []
    benar = 0
    for b in isi_sesi(kon, sesi_id):
        soal: Soal = _soal_dari_baris(b)
        ini_benar = bool(b["benar"])
        if ini_benar:
            benar += 1
        butir.append(
            {
                "nomor": b["nomor"],
                "teks": soal.teks,
                "jawabanku": (b["jawaban"] or ""),
                "benar": ini_benar,
                "dijawab": b["jawaban_id"] is not None,
                "pembahasan": soal.pembahasan or "",
            }
        )
    return {
        "sesi_id": sesi_id,
        "tanggal": info["tanggal"],
        "level": info["level"],
        "nama": info["nama"],
        "jumlah": len(butir),
        "benar": benar,
        "soal": butir,
    }


def semua_terisi(kon, siswa_id: int, sesi_id: int) -> bool:
    """True bila SEMUA soal sesi ini sudah punya isian.

    Sebuah soal dianggap terisi kalau ada baris jawaban dengan setidaknya
    satu kolom tidak kosong (jawaban, cara, restate, atau belum_pernah).
    Definisi ini KONSISTEN dengan simpan_jawaban_murid yang hanya menyimpan
    soal bila (jawaban or cara or restate or belum).

    Kalau sesi bukan milik murid → False (palang).
    """
    if not sesi_murid(kon, siswa_id, sesi_id):
        return False
    ada_kosong = kon.execute(
        """SELECT COUNT(*) FROM sesi_soal ss
           WHERE ss.sesi_id = ?
             AND NOT EXISTS (
               SELECT 1 FROM jawaban j WHERE j.sesi_soal_id = ss.id
                 AND (TRIM(IFNULL(j.jawaban,'')) <> ''
                      OR TRIM(IFNULL(j.cara,'')) <> ''
                      OR TRIM(IFNULL(j.restatement,'')) <> ''
                      OR j.belum_pernah = 1)
             )""",
        (sesi_id,),
    ).fetchone()[0]
    return ada_kosong == 0

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
        # Alasannya: seluruh alur diagnosis (diagnosis.py) dan laporan guru
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
        from database import simpan_jawaban

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

def siswa_dari_akun(kon, pengguna: str) -> int | None:
    """ID siswa untuk akun murid ini, atau None kalau belum terhubung."""
    akun = auth.cari_akun(pengguna)
    if akun and akun.get("siswa_id") is not None:
        baris = kon.execute(
            "SELECT id FROM siswa WHERE id = ?", (int(akun["siswa_id"]),)
        ).fetchone()
        return int(baris["id"]) if baris else None
    baris = kon.execute(
        "SELECT id FROM siswa WHERE nama = ? COLLATE NOCASE", (pengguna.strip(),)
    ).fetchone()
    return int(baris["id"]) if baris else None

def akun_murid_dari_siswa(kon, siswa_id: int) -> str | None:
    """Nama login akun murid yang terikat ke siswa ini, atau None.

    Kebalikan siswa_dari_akun: siswa_id eksplisit menang, akun warisan
    tanpa siswa_id dicocokkan lewat nama siswa seperti dulu.
    """
    baris = kon.execute(
        "SELECT nama FROM siswa WHERE id = ?", (int(siswa_id),)
    ).fetchone()
    nama = baris["nama"].strip().lower() if baris else None
    warisan = None
    for a in auth.muat_akun():
        if a.get("peran") != "murid":
            continue
        if a.get("siswa_id") is not None:
            if int(a["siswa_id"]) == int(siswa_id):
                return a["pengguna"]
        elif nama and a["pengguna"].strip().lower() == nama:
            warisan = a["pengguna"]
    return warisan

PILIHAN_CARA: tuple[tuple[str, str], ...] = (
    ("hitung_satu_satu", "Aku hitung satu per satu"),
    ("lihat_pola", "Aku lihat polanya"),
    ("pakai_rumus", "Aku pakai cara cepat / rumus"),
    ("tanya_ingat", "Aku ingat dari soal yang mirip"),
    ("tebak", "Aku tebak saja"),
    ("bingung", "Aku bingung"),
)

AWALAN_PILIHAN = "[pilihan] "

AWALAN_DRILL = "[drill] "

def label_pilihan(kode: str) -> str:
    """Label yang dibaca guru untuk sebuah kode pilihan."""
    for k, teks in PILIHAN_CARA:
        if k == kode:
            return teks
    return kode
