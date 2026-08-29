#!/usr/bin/env python3
"""Generate guru-side UI mockups for OSN mesin via chenzk.top gpt-image-2."""
import json, base64, urllib.request, time, sys

KEY = "sk-p6uYO2cbw7wNiAdAzamCfxffbNVfhh8aELYHPklFJdMTv6Fc"
URL = "https://chenzk.top/v1/images/generations"
OUT = "/Users/nugroho/Documents/osn/desain-ui"

DS = (
    "Same design system as companion kid-math app mockups: warm cream background "
    "(#FFF8EE), white rounded cards with soft drop shadows, friendly rounded "
    "sans-serif typography, accent palette teal #0FA3A3, coral #FF6B5B, amber "
    "#FFB020. All text in Indonesian, crisp and legible. Realistic desktop browser "
    "screenshot, no watermark, no browser chrome."
)

PAGES = {
    "guru-masuk.png": (
        "landscape", DS,
        "Login screen mockup, landscape 16:9, titled 'Masuk'. Split layout: "
        "left half cream panel with a large friendly minimalist owl-with-graduation-cap "
        "illustration, app title 'Mesin Latihan' in bold teal, tagline 'Latihan soal "
        "pola bilangan untuk SD' beneath. Right half: a white rounded card centered "
        "vertically with a small lock icon, a single password input labeled 'Sandi', "
        "a primary teal rounded button 'Masuk', and muted helper text below: "
        "'Pakai kata sandi yang diberikan'. Lots of whitespace."
    ),
    "guru-dashboard.png": (
        "landscape", DS,
        "Teacher dashboard home screen, landscape 16:9. Top bar: app wordmark "
        "'Mesin Latihan' left in teal; right small text links 'Akun & Siswa' and an "
        "outlined 'Keluar' button. Page header h1 'Mesin Latihan Pola Bilangan' "
        "with muted subtitle 'Pilih sesi untuk memasukkan hasil, atau buka laporan "
        "untuk melihat tren.' Main content: two student cards side by side. Each "
        "card: tinted header strip with title 'Bilal (P5)' and 'Sari (P3)', a small "
        "'Lihat laporan →' link, a compact table (columns: Sesi | Tanggal | Level | "
        "Topik | Terisi | Lembar) with two example rows each like 'Sesi #12 | 28 Agu "
        "2026 | P5 | Pola Bilangan | 10/12 | soal · kunci', and at card bottom an "
        "inline form 'Topik: [select dropdown] [Buat sesi baru] button'. Clean "
        "data-dense but airy layout."
    ),
    "guru-sesi.png": (
        "landscape", DS,
        "Session detail screen, landscape 16:9, titled 'Sesi #12 — Bilal'. Top: a "
        "thin breadcrumb 'Dashboard / Sesi #12' and on the right two buttons: an "
        "amber outlined 'variasi cerita ✨' toggle button and a small 'Cetak / PDF' "
        "link. Below, a vertical list of 4 compact question rows, each row: round "
        "teal number badge (1..4), the question text (a number sequence like "
        "'2, 5, 8, 11, ...'), and on the right an answer input box plus a small "
        "select for diagnosis (' malware' options: 'hitung_satu_satu', 'lihat_pola', "
        "'pakai_rumus') with a status pill showing a green check or amber dot. One "
        "row is expanded showing the full question card with extra detail. "
        "At very bottom a sticky 'Simpan' bar. Densed but readable."
    ),
    "guru-laporan.png": (
        "landscape", DS,
        "Student report screen, landscape 16:9, titled 'Laporan — Bilal (P5)'. "
        "Top row: three small stat cards side by side: '12 sesi', '78% benar', "
        "'Topik terlemah: deret'. Below: a large white card containing a simple line "
        "trend chart with teal line going up across session numbers 1..8, coral "
        "dotted reference line, axis labels 'sesi' (x) and '% benar' (y) in "
        "Indonesian. Right column: a 'Diagnosis' list card with 4 items, each a row "
        "with a colored dot (teal=kuat, amber=lemah, coral=salah-konsep) and a "
        "label like 'Pola naik-tambah: kuat', 'Deret geometri: lemah', "
        "'Sisa pembagian: salah konsep'. Clean, informational."
    ),
    "guru-akun.png": (
        "landscape", DS,
        "Account & student management screen, landscape 16:9, titled 'Akun & "
        "Siswa'. Two-column layout. Left column card 'Akun guru' with rows showing "
        "username, peran, and a 'Ganti sandi' link. Right column card 'Akun murid' "
        "listing 3 student rows: name (Bilal, Sari, Doni), tingkat (P5, P3, P6), "
        "peran pill 'murid', and a small 'Atur' button per row; at bottom of the "
        "card a form with fields 'Nama siswa', 'Tingkat [select]', and an 'Tambah "
        "murid' button. Clean form-heavy layout."
    ),
}


def gen(prompt, size):
    body = {"model": "gpt-image-2", "prompt": prompt,
            "size": size, "quality": "medium", "n": 1}
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"})
    t = time.time()
    d = json.loads(urllib.request.urlopen(req, timeout=300).read())
    item = d["data"][0]
    b64 = item.get("b64_json", "")
    if not b64:
        raise RuntimeError("no b64: " + json.dumps(d)[:300])
    return b64, time.time() - t


for name, (orient, sysline, desc) in PAGES.items():
    size = "1536x1024" if orient == "landscape" else "1024x1536"
    full = f"{desc}\n\n{sysline}"
    print(f"[{name}] start ...", flush=True)
    try:
        b64, dt = gen(full, size)
        p = f"{OUT}/{name}"
        open(p, "wb").write(base64.b64decode(b64))
        print(f"[{name}] OK b64={len(b64)} in {dt:.0f}s -> {p}", flush=True)
    except Exception as e:
        print(f"[{name}] FAIL: {e}", flush=True)
print("DONE", flush=True)
