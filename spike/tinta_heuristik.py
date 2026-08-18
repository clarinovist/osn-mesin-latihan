#!/usr/bin/env python3
"""Tahap B, implementasi 1 — `tinta_heuristik` (Rencana Spike Hari 4, pagi).

Aturan if-then murni atas turunan waktu. Nol panggilan API, nol jaringan,
deterministik: input yang sama selalu memberi keluaran yang sama.

Tujuannya BUKAN menang melawan LLM. Tujuannya menetapkan **lantai** — berapa
yang bisa dicapai tanpa AI sama sekali. Kalau lantai ini sudah >=7/10 dengan
nol false-K, LLM keluar dari lingkup v1 (lihat "Gerbang" di Rencana Spike).

Kode mengikuti Panduan Orang Tua:
    B = salah membaca soal
    K = salah konsep
    H = salah hitung

Ditulis SEBELUM melihat hasil apa pun dari tinta_llm. Urutan ini disengaja:
menulis baseline setelah melihat hasil LLM adalah cara paling mudah untuk
tanpa sadar membuatnya kalah.

Batas yang dipegang (aturan yang tidak boleh dilanggar, Bagian 2):
benar/salah TIDAK PERNAH ditentukan di sini — itu datang dari jawaban yang
diketik anak, dicocokkan di Tahap A. Modul ini hanya menebak *jenis* kesalahan
dari bentuk prosesnya.
"""

ATURAN_VERSI = "heuristik-v1"

# Ambang batas. Dikumpulkan di satu tempat supaya bisa disetel tanpa
# menyentuh logika, dan supaya jelas apa saja yang sebenarnya arbitrer.
JEDA_PANJANG_MS = 8000       # jeda awal >= ini = anak tertahan di depan soal
JEDA_PENDEK_MS = 3000        # jeda awal <= ini = langsung mengerjakan
HAPUS_BANYAK = 2             # total hapus >= ini = ragu-ragu / mengoreksi
DURASI_SANGAT_CEPAT_MS = 6000  # total waktu <= ini = nyaris tanpa pengerjaan


def _total(daftar, kunci):
    return sum(d[kunci] for d in daftar)


def ekstrak_sinyal(turunan_soal):
    """turunan.yaml satu soal -> sinyal mentah yang dipakai aturan.

    Dipisah dari `diagnosa()` supaya bisa diuji sendiri dan supaya alasan
    yang dikembalikan bisa menyebut angka yang sebenarnya dilihat.
    """
    durasi = turunan_soal.get("durasi_per_langkah_ms") or []
    hapus = turunan_soal.get("jumlah_hapus_per_langkah") or []

    return {
        "jeda_awal_ms": turunan_soal.get("jeda_sebelum_goresan_pertama_ms"),
        "jumlah_langkah": len(durasi),
        "durasi_total_ms": _total(durasi, "durasi_ms") if durasi else 0,
        "hapus_total": _total(hapus, "jumlah") if hapus else 0,
        "jawaban_duluan": turunan_soal.get("jawaban_ditulis_sebelum_langkah_selesai"),
        "ada_goresan": turunan_soal.get("jeda_sebelum_goresan_pertama_ms") is not None,
    }


def diagnosa(turunan_soal, kode_tahap_a=None):
    """Kembalikan {kode, keyakinan, alasan, aturan_versi}.

    `kode_tahap_a` opsional: kalau Tahap A sudah memutuskan (mis. "benar" atau
    malrule yang cocok), heuristik tidak menimpanya. Tahap B hanya bekerja di
    wilayah yang Tahap A serahkan.
    """
    # Tahap A menang. Ambiguitas malrule ("tidak_pasti") justru diserahkan
    # ke sini, jadi itu tidak dihitung sebagai keputusan.
    if kode_tahap_a and kode_tahap_a not in ("tidak_pasti", "tidak_ada_template"):
        return {
            "kode": kode_tahap_a,
            "keyakinan": "tinggi",
            "alasan": "diputuskan Tahap A (malrule), heuristik tidak menimpa",
            "aturan_versi": ATURAN_VERSI,
        }

    s = ekstrak_sinyal(turunan_soal)

    # Tidak ada goresan sama sekali: tidak ada proses untuk dibaca.
    # Ini bukan "menebak" — bisa saja soal dilewati. Jangan mengarang kode.
    if not s["ada_goresan"]:
        return {
            "kode": "tidak_pasti",
            "keyakinan": "rendah",
            "alasan": "tidak ada goresan sama sekali — tidak ada proses yang bisa dibaca",
            "aturan_versi": ATURAN_VERSI,
        }

    # --- Sinyal kuat: jawaban ditulis sebelum langkah selesai ---
    # Anak menuliskan jawaban lalu (mungkin) merapikan langkah belakangan.
    # Condong menebak; dalam kosakata Panduan ini paling dekat ke B.
    if s["jawaban_duluan"] and s["durasi_total_ms"] <= DURASI_SANGAT_CEPAT_MS:
        return {
            "kode": "B",
            "keyakinan": "sedang",
            "alasan": (
                f"jawaban ditulis sebelum langkah selesai, total pengerjaan hanya "
                f"{s['durasi_total_ms']/1000:.1f} detik — condong menebak/tidak membaca cermat"
            ),
            "aturan_versi": ATURAN_VERSI,
        }

    # --- Jeda awal panjang: tertahan di depan soal, belum mulai menulis ---
    # Tidak tahu harus mulai dari mana = lebih dekat ke konsep daripada hitung.
    if s["jeda_awal_ms"] is not None and s["jeda_awal_ms"] >= JEDA_PANJANG_MS:
        return {
            "kode": "K",
            "keyakinan": "sedang",
            "alasan": (
                f"jeda {s['jeda_awal_ms']/1000:.1f} detik sebelum goresan pertama — "
                f"tertahan sebelum mulai, condong tidak tahu caranya"
            ),
            "aturan_versi": ATURAN_VERSI,
        }

    # --- Lancar tapi salah: mulai cepat, sedikit hapus, tetap keliru ---
    # Anak yakin dan mengerjakan mulus — keyakinan yang keliru = salah konsep.
    if (
        s["jeda_awal_ms"] is not None
        and s["jeda_awal_ms"] <= JEDA_PENDEK_MS
        and s["hapus_total"] == 0
    ):
        return {
            "kode": "K",
            "keyakinan": "sedang",
            "alasan": (
                f"mulai menulis setelah {s['jeda_awal_ms']/1000:.1f} detik tanpa menghapus — "
                f"lancar tapi jawabannya salah, condong keyakinan yang keliru"
            ),
            "aturan_versi": ATURAN_VERSI,
        }

    # --- Banyak koreksi: tahu arahnya, tersandung di eksekusi ---
    if s["hapus_total"] >= HAPUS_BANYAK:
        return {
            "kode": "H",
            "keyakinan": "sedang",
            "alasan": (
                f"{s['hapus_total']} kali menghapus di {s['jumlah_langkah']} langkah — "
                f"mengoreksi berulang, condong tersandung di hitungan bukan konsep"
            ),
            "aturan_versi": ATURAN_VERSI,
        }

    # --- Sinyal campur atau lemah ---
    # Sengaja menyerah. Menebak di sini persis yang dilarang gerbang
    # (false-K adalah kegagalan paling mahal).
    return {
        "kode": "tidak_pasti",
        "keyakinan": "rendah",
        "alasan": (
            f"sinyal campur (jeda {s['jeda_awal_ms']}ms, {s['hapus_total']} hapus, "
            f"{s['jumlah_langkah']} langkah) — tidak cukup untuk memilih B/K/H"
        ),
        "aturan_versi": ATURAN_VERSI,
    }


def diagnosa_sesi(turunan, kode_tahap_a_per_soal=None):
    """Jalankan heuristik atas seluruh soal dalam satu turunan.yaml."""
    kode_tahap_a_per_soal = kode_tahap_a_per_soal or {}
    hasil = []
    for soal in turunan["soal"]:
        d = diagnosa(soal, kode_tahap_a_per_soal.get(soal["soal_id"]))
        d["soal_id"] = soal["soal_id"]
        d["jawaban_diketik"] = soal.get("jawaban_diketik")
        hasil.append(d)
    return hasil


def ringkas(hasil):
    hitung = {}
    for h in hasil:
        hitung[h["kode"]] = hitung.get(h["kode"], 0) + 1
    return hitung
