#!/usr/bin/env python3
"""Generate mockup UI guru & admin via gpt-image-2 (chenzk.top).

Kunci API dari env — JANGAN pernah menulisnya di file ini (kunci lama
pernah ter-commit dan harus di-revoke):

    export OSN_API_KEY_GAMBAR=sk-...
    python3 gen_guru.py
"""
import json, base64, os, urllib.request, time, sys

KEY = os.environ.get("OSN_API_KEY_GAMBAR", "").strip()
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
        "illustration, app title 'Caraku' in bold teal, tagline 'Latih. Tulis caramu. "
        "Ketahui letak salahmu.' beneath. Right half: a white rounded card centered "
        "vertically with a small lock icon, a single password input labeled 'Sandi', "
        "a primary teal rounded button 'Masuk', and muted helper text below: "
        "'Pakai kata sandi yang diberikan'. Lots of whitespace."
    ),
    "guru-dashboard.png": (
        "landscape", DS,
        "Teacher dashboard home screen, landscape 16:9. Top bar: app wordmark "
        "'Caraku' left in teal; right a user menu showing username 'ortu-a' with a "
        "small teal pill badge 'Orang Tua' and a dropdown chevron. Page header h1 "
        "'Caraku' with muted subtitle 'Pilih sesi untuk memasukkan hasil, atau buka "
        "laporan untuk melihat tren.' Main content: two student cards side by side. "
        "Each card: tinted header strip with title 'Bilal (P5)' and 'Sari (P3)', a "
        "small 'Lihat laporan →' link, a compact table (columns: Sesi | Tanggal | "
        "Level | Topik | Mode | Terisi | Lembar) with two example rows each like "
        "'Sesi #12 | 28 Agu 2026 | P5 | Pola Bilangan | Diagnostik | 10/12 | soal · "
        "kunci' where Mode is a small colored pill, and at card bottom an inline "
        "form 'Topik: [select dropdown]' next to a coral button 'Buat sesi baru'. "
        "Clean data-dense but airy layout."
    ),
    "guru-sesi.png": (
        "landscape", DS,
        "Session detail screen, landscape 16:9, titled 'Sesi #12 — Bilal'. Top bar: "
        "wordmark 'Caraku' left, user menu 'ortu-a' with teal pill 'Orang Tua' right. "
        "Below it a thin breadcrumb 'Dashboard / Sesi #12' and on the right two "
        "buttons: an amber outlined 'variasi cerita ✨' toggle button and a small "
        "'Cetak / PDF' link. Below, a vertical list of 4 compact question rows, each "
        "row: round teal number badge (1..4), the question text (a number sequence "
        "like '2, 5, 8, 11, ...'), and on the right an answer input box plus a small "
        "dropdown for diagnosis with readable options 'Benar', 'K — salah konsep', "
        "'B — salah baca', 'H — salah hitung', 'T — belum pernah lihat', next to a "
        "status pill showing a green check or amber dot. One row is expanded showing "
        "the full question card with extra detail. At very bottom a sticky 'Simpan' "
        "bar. Densed but readable."
    ),
    "guru-laporan.png": (
        "landscape", DS,
        "Student report screen, landscape 16:9, titled 'Laporan — Bilal (P5)'. Top "
        "bar: wordmark 'Caraku' left, user menu 'ortu-a' with teal pill 'Orang Tua' "
        "right. Top row: three small stat cards side by side: '12 sesi', '78% "
        "benar', 'Topik terlemah: deret'. Below: a large white card containing a "
        "simple line trend chart with teal line going up across session numbers "
        "1..8, coral dotted reference line, axis labels 'sesi' (x) and '% benar' "
        "(y) in Indonesian. Right column: a 'Diagnosis' list card with 4 items, "
        "each a row with a colored dot (teal=kuat, amber=lemah, coral=salah-"
        "konsep) and a label like 'Pola naik-tambah: kuat', 'Deret geometri: "
        "lemah', 'Sisa pembagian: salah konsep'. Clean, informational."
    ),
    "guru-akun.png": (
        "landscape", DS,
        "Account & student management screen, landscape 16:9, titled 'Akun & "
        "Siswa'. Top bar: wordmark 'Caraku' left, user menu 'ortu-a' with teal pill "
        "'Orang Tua' right. Sidebar + section layout: a slim left sidebar with "
        "three nav items stacked vertically — 'Akun', 'Siswa', 'Akun murid' — the "
        "active one highlighted teal; the right content pane shows the 'Siswa' "
        "section: a white card listing 3 student rows (name Bilal, Sari, Doni; "
        "tingkat P5, P3, P6; peran pill 'murid'; a small 'Atur' button per row), "
        "and below the table a form with fields 'Nama siswa', 'Tingkat [select]' "
        "and a coral 'Tambah siswa' button. Clean form-heavy layout."
    ),
    "admin-dashboard.png": (
        "landscape", DS,
        "Server admin panel screen, landscape 16:9, titled 'Panel Pengelola'. Top "
        "bar: wordmark 'Caraku' left in teal; right a user menu showing username "
        "'pengelola' with a small amber pill badge 'Pengelola'. Below: a row of "
        "three small stat cards '3 keluarga', '7 siswa', '54 sesi' with large "
        "teal numbers. Main content: a white card with a family table (columns: "
        "Keluarga | Orang Tua | Anak | Sesi), rows like 'Keluarga A | ortu-a | "
        "Bilal, Sari | 21' where the children are teal links. Below it a second "
        "card 'Buat akun orang tua' with fields 'Nama pengguna' and 'Kata sandi', "
        "a coral 'Buat akun' button, and muted helper text 'Orang tua juga bisa "
        "mendaftar sendiri di /daftar'. Admin is read-only over family data — "
        "no edit buttons in the table. Clean, data-dense but airy."
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


if not KEY:
    sys.exit("Kunci API belum diset. Jalankan: export OSN_API_KEY_GAMBAR=sk-...")

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
