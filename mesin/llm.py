"""Klien DeepSeek — pembungkus cerita soal waktu-jalan (opsi B2, plan Fase 5).

Peran LLM di mesin ini SANGAT terbatas dan itu disengaja:

  - Python (templates.py) tetap menghitung parameter, kunci, dan malrule.
  - LLM HANYA menulis ulang kalimat soalnya jadi cerita yang berbeda-beda,
    supaya anak tidak menebak pola dari bunyi soal yang selalu sama.
  - Kalimat hasil LLM diverifikasi: setiap angka di dalamnya harus cocok
    dengan angka di parameter/kunci soal asli. Gagal verifikasi -> None,
    pemanggil memakai kalimat bawaan dari template.

Dua garis yang tidak boleh dilanggar modul ini:

  1. Kunci dan malrule TIDAK PERNAH dikirim ke API. Yang keluar hanya
     kalimat soal asli + parameternya, dan prompt melarang model menjawab.
  2. Gagal-diam: tanpa DEEPSEEK_API_KEY semua fungsi langsung pulang
     tanpa network call dan tanpa exception. Fitur mati, aplikasi jalan.

Klien ini stdlib-murni (urllib) dan TERISOLASI: tidak mengubah modul lain.
Pemanggil yang menyambungkannya ke web.py/generator.py — bukan modul ini.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
from typing import Any

from templates import Soal

# ── Konfigurasi lingkungan ──────────────────────────────────────────────

ENV_BASE_URL = "DEEPSEEK_BASE_URL"
ENV_API_KEY = "DEEPSEEK_API_KEY"
ENV_MODEL = "DEEPSEEK_MODEL"
ENV_VISION_MODEL = "DEEPSEEK_VISION_MODEL"
ENV_SALDO_MIN = "DEEPSEEK_SALDO_MIN"

BASE_URL_BAWAAN = "https://api.deepseek.com"
MODEL_BAWAAN = "deepseek-chat"
VISION_MODEL_BAWAAN = "deepseek-v4-flash-vision-exp"

# Request singkat: soal dibungkus saat lembar disusun, menggantung lebih
# dari ini lebih baik dibuang daripada membuat murid menunggu.
BATAS_WAKTU_DETIK = 20

# max_tokens harus menampung reasoning model: deepseek-v4-flash menulis
# reasoning_content SEBELUM konten (terukur: +-825 reasoning token untuk
# 6 soal). Batas lama 200 membuat konten sering kosong dan fitur gagal
# diam-diam. Cerita 1 kalimat tetap pendek — kelebihan kuota tidak
# berarti teks lebih panjang, dan cache membuat biaya dibayar sekali.
MAX_TOKENS = 2000

# Vision (lampiran foto): deepseek-v4-flash-vision-exp juga reasoning model
# — terukur 718 reasoning token untuk 6 soal. 3000 menyisakan ruang untuk
# lembar 12 soal + JSON hasil.
MAX_TOKENS_VISION = 3000

# Naikkan versi ini kalau prompt berubah — kunci cache ikut berubah,
# jadi kalimat lama tidak dipakai ulang untuk soal berprompt baru.
VERSI_PROMPT = "b2-cerita-v1"


def konfigurasi() -> dict[str, str]:
    """Baca env SAAT DIPANGGIL (bukan saat impor) supaya bisa diuji."""
    return {
        "base_url": os.environ.get(ENV_BASE_URL, BASE_URL_BAWAAN).rstrip("/"),
        "api_key": os.environ.get(ENV_API_KEY, "").strip(),
        "model": os.environ.get(ENV_MODEL, MODEL_BAWAAN),
    }


def aktif() -> bool:
    """True hanya jika API key ada dan tidak kosong. Tanpa network call."""
    return bool(konfigurasi()["api_key"])


# ── Cache ───────────────────────────────────────────────────────────────
#
# Satu soal tidak pernah dibayar dua kali: kalimat hasil LLM disimpan
# berkunci hash(parameter + versi_prompt + model). Tabelnya dibuat oleh
# PEMANGGIL lewat ensure_table(kon), pola yang sama dengan skema di
# schema.py/database.py — modul ini tidak menyentuh skema milik orang lain.


def ensure_table(kon: sqlite3.Connection) -> None:
    """Buat tabel llm_cache bila belum ada. Aman dijalankan berulang."""
    kon.execute(
        """CREATE TABLE IF NOT EXISTS llm_cache (
               kunci_hash TEXT PRIMARY KEY,
               kalimat    TEXT NOT NULL,
               model      TEXT NOT NULL,
               dibuat     TEXT NOT NULL DEFAULT (datetime('now'))
           )"""
    )


def kunci_cache(parameter: dict[str, Any], model: str | None = None) -> str:
    """Sidik jari cache: parameter + versi prompt + model.

    Parameter diurutkan agar {"awal": 2, "beda": 3} dan {"beda": 3,
    "awal": 2} berbagi entri cache — soal yang sama, bayar sekali.
    """
    if model is None:
        model = konfigurasi()["model"]
    butir = json.dumps(
        {
            "parameter": parameter,
            "versi_prompt": VERSI_PROMPT,
            "model": model,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(butir.encode("utf-8")).hexdigest()


# ── Verifikasi angka (murni, tanpa network) ────────────────────────────


_POLA_ANGKA = re.compile(r"-?\d+(?:\.\d+)?")


def angka_dalam(teks: str) -> set[float]:
    """Semua angka (int/desimal) di sebuah teks, sebagai himpunan float."""
    return {float(m.group()) for m in _POLA_ANGKA.finditer(teks)}


def sumber_angka(soal: Soal) -> set[float]:
    """Angka yang BOLEH muncul di kalimat hasil LLM.

    Sumbernya dua, keduanya sudah dilihat anak di kalimat asli:

      1. nilai parameter,
      2. angka di kalimat soal asli — penting: banyak template menampilkan
         suku-suku deret yang dihitung dari parameter (mis. 2, 5, 8, 11),
         bukan parameternya sendiri. Menulis ulang cerita pasti memakai
         angka-angka itu lagi.

    Angka KUNCI SENGAJA TIDAK ADA DI SINI.

    Versi pertama memasukkannya (mengikuti kontrak "angka harus cocok
    dengan parameter/kunci") dan itu membuka lubang paling mahal di
    seluruh aplikasi: kalimat "Jawabannya 4193." lolos verifikasi, karena
    4193 memang kunci yang sah. Anak membaca soal beserta jawabannya, dan
    dua kode yang tidak bisa dipulihkan dari data mana pun (N menebak,
    T belum pernah lihat) mati diam-diam — laporan tetap tampak normal.

    Kunci yang kebetulan sama dengan angka yang memang tampil di soal
    (mis. pola siklus) tetap lolos lewat jalur nomor 2, jadi pembatasan
    ini tidak menolak kalimat yang sah.
    """
    diizinkan: set[float] = set()
    for nilai in soal.parameter.values():
        diizinkan |= angka_dalam(str(nilai))
    diizinkan |= angka_dalam(soal.teks)
    return diizinkan


def verifikasi(kalimat: str, soal: Soal) -> bool:
    """Terima kalimat pengganti hanya jika semua angkanya sah.

    Murni dan bisa dites tanpa network. Tiga penolakan, masing-masing
    menutup kerusakan yang berbeda:

      1. kosong / multiline — yang diminta SATU kalimat;
      2. ada angka yang bukan dari soal — model mengarang;
      3. angka soal yang HILANG — subset saja tidak cukup. Himpunan kosong
         adalah subset dari apa pun, jadi "Ada pola bilangan, berapa suku
         berikutnya?" lolos aturan subset padahal soalnya jadi tidak bisa
         dikerjakan sama sekali. Kalimat pengganti wajib membawa kembali
         setiap angka yang tampil di kalimat asli.
    """
    if not kalimat or not kalimat.strip():
        return False
    bersih = kalimat.strip()
    if "\n" in bersih:
        return False

    ada = angka_dalam(bersih)
    if not (ada <= sumber_angka(soal)):
        return False  # mengarang angka

    wajib = angka_dalam(soal.teks)
    if not (wajib <= ada):
        return False  # menghilangkan angka yang dibutuhkan anak

    # Kunci tidak boleh muncul kecuali ia memang bagian dari soal aslinya.
    kunci_angka = angka_dalam(soal.kunci)
    if kunci_angka and not (kunci_angka <= wajib) and (kunci_angka & ada):
        return False

    # Kunci non-angka (huruf siklus, nama hari, pecahan) — periksa teksnya.
    if not kunci_angka and soal.kunci and len(soal.kunci) >= 2:
        if soal.kunci.lower() in bersih.lower() and soal.kunci not in soal.teks:
            return False

    return True


# ── Prompt & respons ───────────────────────────────────────────────────


def _buat_prompt(soal: Soal) -> list[dict[str, str]]:
    """Pesan untuk /chat/completions. Kunci & malrule sengaja tidak dikirim."""
    sistem = (
        "Kamu penulis soal matematika untuk anak SD Indonesia. "
        "Tugasmu HANYA menulis ulang SATU kalimat soal yang diberikan "
        "menjadi kalimat soal PENGGANTI dengan latar cerita yang berbeda. "
        "Aturan mutlak: jenis pertanyaan dan SEMUA angka harus persis sama; "
        "jangan menjawab soal, memberi petunjuk jawaban, menambah "
        "pertanyaan lain, atau mengubah angka apa pun. Jawab hanya dengan "
        "satu kalimat soal, tanpa penjelasan."
    )
    parameter = ", ".join(f"{k}={soal.parameter[k]}" for k in sorted(soal.parameter))
    pengguna = json.dumps(
        {
            "kalimat_soal_asli": soal.teks,
            "parameter": parameter,
            "tugas": (
                "Tulis satu kalimat soal pengganti, "
                "angkanya sama persis dengan kalimat asli."
            ),
        },
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": sistem},
        {"role": "user", "content": pengguna},
    ]


def parse_respons(data: bytes | bytearray | str | dict) -> str | None:
    """Ambil isi jawaban dari format OpenAI-compatible.

    Struktur yang diharapkan:
      {"choices": [{"message": {"content": "..."}}]}
    Apa pun yang menyimpang -> None, bukan exception.
    """
    try:
        if isinstance(data, dict):
            muatan = data
        else:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")
            muatan = json.loads(data)
        konten = muatan["choices"][0]["message"]["content"]
        if not isinstance(konten, str):
            return None
        if not konten.strip():
            # Reasoning model (v4-flash) yang kehabisan max_tokens di
            # reasoning_content mengirim content kosong. Itu kegagalan
            # permintaan, bukan kalimat sah berupa string kosong.
            return None
        return konten.strip()
    except (KeyError, IndexError, TypeError, ValueError, UnicodeDecodeError):
        return None


# ── Network ────────────────────────────────────────────────────────────


def _panggil(pesan: list[dict[str, str]]) -> str | None:
    """POST /chat/completions. Error apa pun -> None, jangan raise."""
    cfg = konfigurasi()
    url = cfg["base_url"] + "/chat/completions"
    tubuh = json.dumps(
        {
            "model": cfg["model"],
            "messages": pesan,
            "temperature": 1.0,
            "max_tokens": MAX_TOKENS,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=tubuh,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=BATAS_WAKTU_DETIK) as resp:
            return parse_respons(resp.read())
    except (urllib.error.URLError, OSError, ValueError):
        # HTTPError turunan URLError; socket.timeout turunan OSError;
        # JSON rusak tertangani parse_respons, ValueError sisa pengaman.
        return None


# ── Vision — baca lembar foto (Fase 2, lampiran) ──────────────────────
#
# Peran vision SANGAT mirip peran cerita: Python tetap pemegang kebenaran.
# AI vision HANYA membaca foto lembar yang sudah diisi anak dan mengusulkan
# {nomor, jawaban, caraku} per soal — guru WAJIB konfirmasi sebelum data
# masuk. Garis yang tidak boleh dilanggar: jawaban yang keluar dari model
# TIDAK pernah langsung jadi data; ia hanya bahan di halaman konfirmasi.


def konfigurasi_vision() -> dict[str, str]:
    """Konfigurasi model vision — key sama, model berbeda dari cerita."""
    cfg = konfigurasi()
    return {
        "base_url": cfg["base_url"],
        "api_key": cfg["api_key"],
        "model": os.environ.get(ENV_VISION_MODEL, VISION_MODEL_BAWAAN),
    }


def parse_ekstraksi(konten: str) -> list[dict] | None:
    """Ubah konten model (mungkin dibungkus ```json) jadi daftar hasil.

    Format yang diterima:
      {"soal": [{"nomor": 1, "jawaban": "10", "caraku": "tambah 2"}, ...]}

    Apa pun yang menyimpang -> None, bukan exception. Dua garis kebenaran:
      - nomor wajib bilangan bulat >= 1;
      - jawaban/caraku wajib string (boleh kosong — anak melewati soal).
    """
    bersih = konten.strip()
    # Lepas fence ```json ... ```
    if bersih.startswith("```"):
        baris = bersih.splitlines()
        if baris and baris[0].strip().startswith("```"):
            baris = baris[1:]
        if baris and baris[-1].strip().startswith("```"):
            baris = baris[:-1]
        bersih = "\n".join(baris).strip()
    mulai, akhir = bersih.find("{"), bersih.rfind("}")
    if mulai == -1 or akhir <= mulai:
        return None
    try:
        data = json.loads(bersih[mulai : akhir + 1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    daftar = data.get("soal")
    if not isinstance(daftar, list) or not daftar:
        return None
    keluar: list[dict] = []
    for butir in daftar:
        if not isinstance(butir, dict):
            return None
        try:
            nilai_nomor = butir.get("nomor")
            if nilai_nomor is None:
                return None
            nomor = int(nilai_nomor)
            jawaban = str(butir.get("jawaban") or "").strip()
            caraku = str(butir.get("caraku") or "").strip()
        except (TypeError, ValueError):
            return None
        if nomor < 1:
            return None
        keluar.append({"nomor": nomor, "jawaban": jawaban, "caraku": caraku})
    return keluar


def verifikasi_ekstraksi(hasil: list[dict], jumlah_soal: int) -> bool:
    """Hasil hanya sah kalau nomornya 1..N lengkap, tanpa nomor asing.

    Nomor asing (99) atau hilang (hanya 1..5 dari 6) berarti model tidak
    benar-benar membaca lembar — hasilnya tidak layak ditampilkan ke guru.
    Isi jawaban TIDAK diverifikasi di sini: guru yang menilai di halaman
    konfirmasi.
    """
    if not hasil:
        return False
    nomor = {h["nomor"] for h in hasil}
    return nomor == set(range(1, jumlah_soal + 1))


def ekstrak_lembar(soal_konteks: list[str], gambar_b64: str) -> list[dict] | None:
    """Baca satu foto lembar -> daftar {nomor, jawaban, caraku} per soal.

    Gagal-diam (pola seluruh modul): tanpa key / network error / parse gagal
    / verifikasi gagal -> None, pemanggil menampilkan pesan "tidak terbaca".

    `soal_konteks` adalah teks tiap soal (berurutan 1..N) — dikirim ke model
    supaya ia memetakan jawaban ke nomor yang benar dan tidak mengarang soal.
    """
    cfg = konfigurasi_vision()
    if not cfg["api_key"]:
        return None

    daftar_soal = "\n".join(
        f"{i + 1}. {teks}" for i, teks in enumerate(soal_konteks)
    )
    prompt = (
        "Berikut daftar soal di lembar ini:\n"
        f"{daftar_soal}\n\n"
        "Baca FOTO lembar yang sudah diisi anak. Untuk SETIAP nomor 1.."
        f"{len(soal_konteks)}:\n"
        "- jawaban: angka yang anak tulis di kotak Jawabanku (kalau kosong, \"\").\n"
        "- caraku: teks di kotak Caraku. Coretan tak terbaca tulis \"?\"; "
        "kotak kosong tulis \"\".\n"
        'Keluarkan HANYA JSON: {"soal": [{"nomor": 1, "jawaban": "...", '
        '"caraku": "..."}]} tanpa penjelasan.'
    )
    pesan = [
        {
            "role": "system",
            "content": (
                "Kamu membaca lembar jawaban matematika anak SD dari foto. "
                "Jawab hanya JSON, tanpa penjelasan."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{gambar_b64}"
                    },
                },
                {"type": "text", "text": prompt},
            ],
        },
    ]
    tubuh = json.dumps(
        {
            "model": cfg["model"],
            "messages": pesan,
            "temperature": 0,
            "max_tokens": MAX_TOKENS_VISION,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        cfg["base_url"] + "/chat/completions",
        data=tubuh,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            req, timeout=BATAS_WAKTU_DETIK * 4
        ) as resp:
            konten = parse_respons(resp.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None
    if konten is None:
        return None
    hasil = parse_ekstraksi(konten)
    if hasil is None or not verifikasi_ekstraksi(hasil, len(soal_konteks)):
        return None
    return hasil


# ── Gerbang biaya (opsional) ───────────────────────────────────────────


def cek_saldo(minimal: float | None = None) -> bool:
    """Cek saldo DeepSeek terhadap ambang DEEPSEEK_SALDO_MIN (default 0).

    Mengembalikan False (= fitur dianggap nonaktif) kalau:
      - ambang > 0 tapi API key tidak ada,
      - saldo tak bisa dipastikan (network error, format tak dikenal),
      - saldo terkonfirmasi di bawah ambang.
    Ambang <= 0 / env kosong berarti gerbang biaya dimatikan -> True.
    """
    if minimal is None:
        mentah = os.environ.get(ENV_SALDO_MIN, "").strip()
        if not mentah:
            return True
        try:
            ambang = float(mentah)
        except ValueError:
            return False
    else:
        ambang = float(minimal)
    if ambang <= 0:
        return True
    if not aktif():
        return False

    cfg = konfigurasi()
    req = urllib.request.Request(
        cfg["base_url"] + "/user/balance",
        headers={"Authorization": f"Bearer {cfg['api_key']}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=BATAS_WAKTU_DETIK) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("is_available") is False:
            return False
        total = float(data["balance_infos"][0]["total_balance"])
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError,
            TypeError, AttributeError):
        return False
    return total >= ambang


# ── Pintu masuk utama (B2) ─────────────────────────────────────────────


def bungkus(kon: sqlite3.Connection, soal: Soal) -> str | None:
    """Kalimat soal versi cerita, atau None = pakai kalimat bawaan.

    Urutan keputusannya:
      1. tanpa API key -> None seketika, nol network call (gagal-diam);
      2. cache hit    -> kalimat tersimpan, nol network call;
      3. panggil API  -> verifikasi angka -> simpan cache -> kalimat;
      4. gagal di mana pun -> None.
    """
    if not aktif():
        return None

    hash_kunci = kunci_cache(soal.parameter)
    baris = kon.execute(
        "SELECT kalimat FROM llm_cache WHERE kunci_hash = ?", (hash_kunci,)
    ).fetchone()
    if baris is not None:
        return str(baris[0])

    kalimat = _panggil(_buat_prompt(soal))
    if kalimat is None or not verifikasi(kalimat, soal):
        return None

    kon.execute(
        """INSERT OR REPLACE INTO llm_cache (kunci_hash, kalimat, model)
           VALUES (?, ?, ?)""",
        (hash_kunci, kalimat, konfigurasi()["model"]),
    )
    # Commit sendiri: kalimat yang sudah dibayar tidak boleh hilang hanya
    # karena transaksi pemanggil (mis. penyimpanan sesi) di-rollback.
    kon.commit()
    return kalimat


def bungkus_sesi(kon, sesi_id: int, ambil_soal) -> tuple[int, int, str]:
    """Buat variasi cerita untuk seluruh soal satu sesi.

    Mengembalikan (berhasil, dicoba, catatan).

    `ambil_soal` adalah fungsi yang mengubah satu baris DB jadi objek Soal
    (web._soal_dari_baris) — disuntik dari luar supaya modul ini tetap
    tidak bergantung pada web.py, dan tetap bisa diuji tanpa HTTP.

    Soal yang SUDAH punya cerita dilewati: kalimatnya sudah dibayar, dan
    yang lebih penting anak mungkin sudah mengerjakannya. Mengganti kalimat
    di tengah jalan membuat guru menilai soal yang tidak dikerjakan anak.
    """
    if not aktif():
        return 0, 0, "Fitur cerita tidak aktif (kunci DeepSeek belum dipasang)."
    if not cek_saldo():
        return 0, 0, "Saldo DeepSeek di bawah ambang — permintaan ditahan."

    ensure_table(kon)
    berhasil = dicoba = 0
    for b in kon.execute(
        """SELECT s.id, s.template_id, s.parameter, s.kunci, s.level,
                  s.bagian, s.tantangan, s.cerita
           FROM soal s JOIN sesi_soal ss ON ss.soal_id = s.id
           WHERE ss.sesi_id = ? ORDER BY ss.nomor""",
        (sesi_id,),
    ).fetchall():
        if (b["cerita"] or "").strip():
            continue
        dicoba += 1
        kalimat = bungkus(kon, ambil_soal(b))
        if kalimat:
            kon.execute(
                "UPDATE soal SET cerita = ? WHERE id = ?", (kalimat, b["id"])
            )
            berhasil += 1
    kon.commit()

    if dicoba == 0:
        return 0, 0, "Semua soal sudah punya versi cerita."
    if berhasil == 0:
        return 0, dicoba, (
            f"{dicoba} soal dicoba, tidak ada yang lolos verifikasi angka — "
            "kalimat bawaan tetap dipakai."
        )
    return berhasil, dicoba, f"{berhasil} dari {dicoba} soal dapat versi cerita."
