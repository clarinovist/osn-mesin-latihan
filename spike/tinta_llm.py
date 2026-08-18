#!/usr/bin/env python3
"""Tahap B, implementasi 2 — `tinta_llm` (Rencana Spike Hari 4, sore).

PNG per langkah + ringkasan waktu + malrule yang berlaku -> LLM -> JSON
diagnosis sesuai skema Bagian 2 ("Yang harus dikembalikan model").

Tiga hal yang bukan hiasan:

1. **Cache berkunci `hash(data + prompt_versi + model)`.** Memutar ulang 10
   soal harus gratis dan hasilnya harus persis sama. Tanpa ini, angka gerbang
   tidak bisa direproduksi dan tiap iterasi prompt membakar biaya.

2. **Jejak versi di tiap hasil** (`aturan_versi`, `prompt_versi`, `model`).
   Batas maksimal 3 putaran perbaikan prompt tidak bisa ditegakkan — bahkan
   tidak bisa dihitung — kalau hasil tidak membawa identitas aturan yang
   menghasilkannya.

3. **Kolom `terbaca`.** Model harus boleh menyerah. Diagnosis percaya diri di
   atas tulisan yang tidak terbaca jauh lebih berbahaya daripada mengaku
   tidak tahu; berapa sering kolom ini `false` adalah salah satu hasil utama
   spike.

Aturan yang tidak boleh dilanggar (Bagian 2): OCR tidak pernah menentukan
benar atau salah. Benar-salah datang dari kotak jawaban yang diketik anak.
Karena itu `jawaban_benar` dan `jawaban_diketik` dikirim apa adanya, dan
model diminta mendiagnosis PROSES, bukan menilai hasil.

Pemakaian:
    export ANTHROPIC_API_KEY=...
    ./.venv/bin/python tinta_llm.py turunan/<sesi>/turunan.yaml
    ./.venv/bin/python tinta_llm.py <...> --dry-run   # tanpa API, lihat prompt
"""
import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

import yaml

import tahap_a

SPIKE_DIR = Path(__file__).resolve().parent
CACHE_DIR = SPIKE_DIR / "cache_llm"

# Naikkan setiap kali teks prompt berubah. Ini yang dihitung sebagai
# "putaran perbaikan prompt" (maks 3 sebelum keputusan final).
PROMPT_VERSI = "tinta-llm-v1"
MODEL = "claude-opus-5"
ATURAN_VERSI = "llm-v1"

MAX_TOKENS = 2000

SKEMA = {
    "type": "object",
    "properties": {
        "kode": {"type": "string", "enum": ["B", "K", "H", "benar"]},
        "keyakinan": {"type": "string", "enum": ["tinggi", "sedang", "rendah"]},
        "bukti": {"type": "string"},
        "diagnosis": {"type": "string"},
        "topik": {"type": "string"},
        "terbaca": {"type": "boolean"},
    },
    "required": ["kode", "keyakinan", "bukti", "diagnosis", "topik", "terbaca"],
    "additionalProperties": False,
}

INSTRUKSI = """Kamu membantu seorang ayah membaca proses berpikir anaknya (kelas 5 SD) \
dari coretan pengerjaan soal matematika.

Yang kamu terima: soal, jawaban benar, jawaban yang diketik anak, gambar coretan \
per langkah secara berurutan, ringkasan waktu pengerjaan, dan (kalau ada) pola \
kesalahan yang sudah terdokumentasi untuk soal ini.

Tugasmu: menentukan JENIS kesalahannya, bukan benar-salahnya.

    B = salah membaca soal   (mengerjakan hal yang tidak ditanyakan)
    K = salah konsep         (caranya memang belum dipahami)
    H = salah hitung         (caranya benar, tersandung di aritmetika)
    benar = jawabannya memang benar

Benar atau salah SUDAH ditentukan dari jawaban yang diketik anak — jangan \
menilainya ulang dari tulisan tangan. Tulisan tangan hanya bahan untuk membaca \
proses.

Aturan penting:

- Kalau tulisannya tidak cukup terbaca untuk menyimpulkan apa pun, set \
`terbaca: false` dan `keyakinan: rendah`. Mengaku tidak tahu jauh lebih baik \
daripada diagnosis meyakinkan di atas pembacaan yang keliru.
- Jangan menyebut K kalau langkah-langkahnya menunjukkan caranya sudah benar \
dan hanya hasil aritmetikanya meleset — itu H. Salah tuduh konsep mengirim anak \
mengulang materi yang sebenarnya sudah dipahami, dan itu kesalahan paling mahal.
- `diagnosis` ditulis untuk orang tua: satu kalimat, bahasa Indonesia biasa, \
tanpa istilah teknis.
- `bukti` menyebut apa yang benar-benar terlihat di goresan atau waktunya."""


def _fmt_ms(ms):
    if ms is None:
        return "tidak tercatat"
    return f"{ms/1000:.1f} detik"


def susun_konteks(turunan_soal, entri_template):
    """Bagian teks dari prompt untuk satu soal."""
    t = turunan_soal
    durasi = t.get("durasi_per_langkah_ms") or []
    hapus = t.get("jumlah_hapus_per_langkah") or []

    baris = [
        f"Jawaban benar   : {entri_template.get('jawaban_benar', '?')}",
        f"Jawaban anak    : {t.get('jawaban_diketik') or '(kosong)'}",
        "",
        "Ringkasan waktu:",
        f"- Jeda sebelum mulai menulis: {_fmt_ms(t.get('jeda_sebelum_goresan_pertama_ms'))}",
        f"- Jumlah langkah: {len(durasi)}",
    ]
    for d in durasi:
        baris.append(f"  - langkah {d['indeks'] + 1}: {_fmt_ms(d['durasi_ms'])}")
    baris.append(f"- Total menghapus: {sum(h['jumlah'] for h in hapus)}")
    for h in hapus:
        if h["jumlah"]:
            baris.append(f"  - langkah {h['indeks'] + 1}: {h['jumlah']} kali")

    duluan = t.get("jawaban_ditulis_sebelum_langkah_selesai")
    if duluan is True:
        baris.append("- Jawaban akhir ditulis SEBELUM langkah terakhir selesai")
    elif duluan is False:
        baris.append("- Jawaban akhir ditulis setelah langkah terakhir selesai")

    malrule = entri_template.get("malrule") or []
    if malrule:
        baris.append("")
        baris.append("Pola kesalahan yang sudah terdokumentasi untuk soal ini:")
        for m in malrule:
            try:
                prediksi = tahap_a.PREDIKSI[m["id"]](entri_template["parameter"])
            except Exception:
                prediksi = "?"
            baris.append(f"- {m['id']} -> memprediksi \"{prediksi}\" (kode {m['kode']}): {m['alasan_singkat']}")
        baris.append(
            "Kalau jawaban anak tidak cocok dengan satu pun pola di atas, "
            "jangan dipaksakan — baca goresannya sendiri."
        )
    return "\n".join(baris)


def kunci_cache(soal_id, konteks, gambar_bytes):
    """hash(data mentah + prompt_versi + model).

    Gambar ikut di-hash: dua sesi dengan ringkasan waktu identik tapi coretan
    berbeda TIDAK boleh berbagi entri cache.
    """
    h = hashlib.sha256()
    h.update(str(soal_id).encode())
    h.update(konteks.encode())
    for g in gambar_bytes:
        h.update(hashlib.sha256(g).digest())
    h.update(PROMPT_VERSI.encode())
    h.update(MODEL.encode())
    h.update(INSTRUKSI.encode())
    return h.hexdigest()[:32]


def baca_cache(kunci, cache_dir=None):
    p = Path(cache_dir or CACHE_DIR) / f"{kunci}.json"
    if p.is_file():
        return json.loads(p.read_text())
    return None


def tulis_cache(kunci, nilai, cache_dir=None):
    d = Path(cache_dir or CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{kunci}.json").write_text(json.dumps(nilai, ensure_ascii=False, indent=2))


def validasi_hasil(data):
    """Pastikan respons model benar-benar sesuai skema sebelum dipakai."""
    if not isinstance(data, dict):
        raise ValueError(f"respons bukan objek: {type(data).__name__}")
    for kolom in SKEMA["required"]:
        if kolom not in data:
            raise ValueError(f"kolom wajib hilang: {kolom}")
    if data["kode"] not in ("B", "K", "H", "benar"):
        raise ValueError(f"kode tidak dikenal: {data['kode']!r}")
    if data["keyakinan"] not in ("tinggi", "sedang", "rendah"):
        raise ValueError(f"keyakinan tidak dikenal: {data['keyakinan']!r}")
    if not isinstance(data["terbaca"], bool):
        raise ValueError(f"terbaca harus boolean, dapat {type(data['terbaca']).__name__}")
    return data


def _muat_gambar(folder_soal):
    if not folder_soal.is_dir():
        return []
    return [p.read_bytes() for p in sorted(folder_soal.glob("langkah-*.png"))]


def _panggil_api(klien, konteks, gambar_bytes):
    isi = [{"type": "text", "text": konteks}]
    for i, g in enumerate(gambar_bytes):
        isi.append({"type": "text", "text": f"Langkah {i + 1}:"})
        isi.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64.b64encode(g).decode(),
            },
        })
    isi.append({
        "type": "text",
        "text": "Balas HANYA dengan satu objek JSON sesuai skema, tanpa teks lain.",
    })

    resp = klien.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=INSTRUKSI,
        messages=[{"role": "user", "content": isi}],
    )
    teks = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    teks = teks.strip()
    if teks.startswith("```"):
        teks = teks.split("```")[1]
        teks = teks[4:] if teks.startswith("json") else teks
    return json.loads(teks)


def diagnosa_soal(turunan_soal, entri_template, folder_sesi, klien=None, cache_dir=None):
    """Satu soal -> hasil diagnosis. Membaca cache kalau ada."""
    soal_id = turunan_soal["soal_id"]
    konteks = susun_konteks(turunan_soal, entri_template)
    gambar = _muat_gambar(Path(folder_sesi) / f"soal-{soal_id}")
    kunci = kunci_cache(soal_id, konteks, gambar)

    tersimpan = baca_cache(kunci, cache_dir)
    if tersimpan is not None:
        tersimpan["dari_cache"] = True
        return tersimpan

    if klien is None:
        raise RuntimeError(
            f"soal {soal_id}: tidak ada di cache dan tidak ada klien API. "
            f"Set ANTHROPIC_API_KEY, atau jalankan --dry-run."
        )

    mentah = _panggil_api(klien, konteks, gambar)
    hasil = validasi_hasil(mentah)
    hasil.update({
        "soal_id": soal_id,
        "aturan_versi": ATURAN_VERSI,
        "prompt_versi": PROMPT_VERSI,
        "model": MODEL,
        "jumlah_gambar": len(gambar),
    })
    tulis_cache(kunci, hasil, cache_dir)
    hasil["dari_cache"] = False
    return hasil


def diagnosa_sesi(turunan_path, klien=None, cache_dir=None):
    turunan_path = Path(turunan_path)
    turunan = yaml.safe_load(turunan_path.read_text())
    template_list = tahap_a.muat_template()
    per_id = {t["soal_id"]: t for t in template_list}

    hasil = []
    for soal in turunan["soal"]:
        entri = per_id.get(soal["soal_id"], {})
        hasil.append(diagnosa_soal(soal, entri, turunan_path.parent, klien, cache_dir))
    return turunan.get("sesi_id", "?"), hasil


def buat_klien():
    kunci = os.environ.get("ANTHROPIC_API_KEY")
    if not kunci:
        return None
    from anthropic import Anthropic

    return Anthropic(api_key=kunci)


def main():
    ap = argparse.ArgumentParser(description="Tahap B — tinta_llm")
    ap.add_argument("turunan", help="path ke turunan.yaml")
    ap.add_argument("--dry-run", action="store_true", help="cetak prompt soal pertama, tanpa API")
    ap.add_argument("--cache-dir", default=None)
    args = ap.parse_args()

    if args.dry_run:
        turunan = yaml.safe_load(Path(args.turunan).read_text())
        per_id = {t["soal_id"]: t for t in tahap_a.muat_template()}
        soal = turunan["soal"][0]
        konteks = susun_konteks(soal, per_id.get(soal["soal_id"], {}))
        gambar = _muat_gambar(Path(args.turunan).parent / f"soal-{soal['soal_id']}")
        print("=== SYSTEM ===")
        print(INSTRUKSI)
        print(f"\n=== KONTEKS soal {soal['soal_id']} ===")
        print(konteks)
        print(f"\n[{len(gambar)} gambar langkah akan dilampirkan]")
        print(f"kunci cache: {kunci_cache(soal['soal_id'], konteks, gambar)}")
        print(f"prompt_versi={PROMPT_VERSI} model={MODEL}")
        return

    klien = buat_klien()
    if klien is None:
        print("ANTHROPIC_API_KEY tidak diset — hanya soal yang sudah ada di cache yang bisa dibaca.\n")

    sesi_id, hasil = diagnosa_sesi(args.turunan, klien, args.cache_dir)

    print(f"Sesi: {sesi_id}")
    print(f"{'soal':>5}  {'kode':<7} {'yakin':<8} {'terbaca':<8} {'cache':<6} diagnosis")
    print("-" * 100)
    for h in hasil:
        print(
            f"{h['soal_id']:>5}  {h['kode']:<7} {h['keyakinan']:<8} "
            f"{str(h['terbaca']):<8} {'ya' if h.get('dari_cache') else 'tidak':<6} "
            f"{h['diagnosis'][:44]}"
        )

    tidak_terbaca = sum(1 for h in hasil if not h["terbaca"])
    dari_cache = sum(1 for h in hasil if h.get("dari_cache"))
    print(f"\nterbaca=false: {tidak_terbaca}/{len(hasil)} (gerbang gagal kalau >4)")
    print(f"dibaca dari cache: {dari_cache}/{len(hasil)}")
    print(f"prompt_versi={PROMPT_VERSI} model={MODEL}")


if __name__ == "__main__":
    sys.exit(main())
