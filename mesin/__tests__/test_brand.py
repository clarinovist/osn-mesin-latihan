"""Rute aset brand (/aset/<nama>) + tag kepala favicon/meta.

Palang yang dijaga:
1. Publik — favicon dibutuhkan sebelum login, jadi 200 tanpa kredensial.
2. Allow-list, bukan path gabung: traversal `../` mustahil.
3. MIME benar per ekstensi; cache panjang & immutable.
4. Tidak menyentuh basis data sama sekali.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brand  # noqa: E402
import database  # noqa: E402
import design_tokens as T  # noqa: E402
from http_test_kit import SANDI_GURU, ServerUji  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    with s.buka() as kon:
        # pemilik distempel eksplisit — palang kepemilikan menolak id yang
        # bukan milik guru dengan 404, dan itu bukan yang sedang diuji.
        sid = database.tambah_siswa(kon, "Putri", pemilik="guru")
        s.sesi_id = database.buat_sesi(kon, sid, seed=7)
        # Akun murid "feby" harus punya siswa dengan nama yang sama, kalau
        # tidak /murid menjatuhkan ke halaman "Belum terhubung" dan test
        # brand mengukur halaman yang salah.
        sid_feby = database.tambah_siswa(kon, "feby", pemilik="guru")
        database.buat_sesi(kon, sid_feby, seed=11)
    yield s
    s.berhenti()


# ───────────────────────── berkas aset ada ─────────────────────────

def test_folder_aset_lengkap():
    """Allow-list dan isi folder harus sinkron: nama yang diizinkan rute
    benar-benar ada sebagai berkas, dan tidak ada berkas liar di luar
    allow-list yang diam-diam ikut ke image."""
    folder = ROOT / "aset"
    assert folder.is_dir(), "mesin/aset/ belum ada"
    di_disk = {p.name for p in folder.iterdir() if p.is_file()}
    assert set(brand.ASET) == di_disk, (
        f"allow-list vs disk beda: hanya-allow={set(brand.ASET) - di_disk}, "
        f"hanya-disk={di_disk - set(brand.ASET)}"
    )


def test_aset_wajib_ada_semua():
    wajib = (
        "mark-sederhana.svg",
        "mark-penuh.svg",
        "mark-tinta.svg",
        "lockup-horizontal.svg",
        "lockup-cetak.svg",
        "lockup-hero.svg",
        "favicon.svg",
        "favicon.ico",
        "apple-touch-180.png",
        "pwa-192.png",
        "pwa-512.png",
        "og-image.png",
    )
    for nama in wajib:
        assert nama in brand.ASET, f"{nama} tidak ada di allow-list"
        assert (ROOT / "aset" / nama).is_file(), f"{nama} tidak ada di disk"


# ───────────────────────── rute publik ─────────────────────────

def test_favicon_publik_tanpa_kredensial(server):
    """Favicon dibutuhkan browser SEBELUM login — kalau kena palang guru,
    tab menampilkan ikon kosong di halaman landing dan masuk."""
    kode, isi, hdr = server.minta("/aset/favicon.ico", biner=True)
    assert kode == 200
    assert isi == (ROOT / "aset" / "favicon.ico").read_bytes()
    assert hdr["Content-Type"] == "image/x-icon"
    assert "immutable" in hdr["Cache-Control"]


def test_semua_aset_terlayani_dan_mime_benar(server):
    harapan = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
        ".json": "application/json",
    }
    for nama in brand.ASET:
        kode, isi, hdr = server.minta(f"/aset/{nama}", biner=True)
        assert kode == 200, f"{nama} -> {kode}"
        ext = Path(nama).suffix
        assert hdr["Content-Type"].startswith(harapan[ext]), f"{nama}: {hdr}"
        assert isi, f"{nama} kosong"


def test_traversal_ditolak(server):
    """Allow-list, bukan path gabung. Semua bentuk traversal -> 404, dan
    yang penting: TIDAK ada isi berkas sistem yang terkirim."""
    jahat = (
        "/aset/../../etc/passwd",
        "/aset/..%2f..%2fetc%2fpasswd",
        "/aset/web.py",
        "/aset/../design_tokens.py",
        "/aset/latihan.db",
        "/aset/",
    )
    for jalur in jahat:
        kode, isi, _ = server.minta(jalur, biner=True)
        assert kode == 404, f"{jalur} -> {kode} (harus 404)"
        assert b"root:" not in isi and b"NAMA_PRODUK" not in isi, (
            f"{jalur} membocorkan isi berkas"
        )


def test_manifest_pwa_dari_tokens(server):
    """manifest.json di-generate, bukan berkas statis: nama & warna harus
    ikut design_tokens supaya brand tidak punya dua sumber kebenaran."""
    kode, isi, hdr = server.minta("/aset/manifest.json")
    assert kode == 200
    assert hdr["Content-Type"].startswith("application/json")
    data = json.loads(isi)
    assert data["name"] == T.NAMA_PRODUK
    assert data["short_name"] == T.NAMA_PRODUK
    assert data["display"] == "standalone"
    assert data["theme_color"] == T.AKSEN_MURID_UTAMA
    src = [i["src"] for i in data["icons"]]
    assert "/aset/pwa-192.png" in src and "/aset/pwa-512.png" in src


def test_aset_tidak_menyentuh_basis_data(server, monkeypatch):
    """Rute publik ini hanya melayani berkas brand. Kalau ia membuka DB,
    permukaan publik tanpa palang jadi bersentuhan dengan data anak."""
    import database as db_mod

    def meledak(*a, **k):
        raise AssertionError("rute /aset tidak boleh membuka basis data")

    monkeypatch.setattr(db_mod, "buka", meledak)
    assert server.minta("/aset/favicon.svg", biner=True)[0] == 200


def test_aset_tetap_publik_untuk_murid_dan_guru(server):
    from http_test_kit import SANDI_MURID

    for kred in (None, ("guru", SANDI_GURU), ("feby", SANDI_MURID)):
        kode, _, _ = server.minta("/aset/mark-sederhana.svg", auth=kred, biner=True)
        assert kode == 200, f"{kred} -> {kode}"


def test_dockerfile_menyalin_folder_aset():
    """COPY *.py adalah wildcard .py saja — berkas non-.py tidak ikut.
    Tanpa baris COPY aset/, favicon 404 di produksi meski hijau di lokal
    (pola insiden 25 Agustus 2026, kali ini untuk berkas biner)."""
    isi = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "aset/" in isi, "Dockerfile tidak menyalin folder aset/"


# ───────────────────────── favicon di SEMUA halaman ─────────────────────────

# Halaman yang dilayani lewat HTTP. Guard ini menutup celah "template baru
# lahir tanpa favicon": sebelumnya tidak SATU pun halaman punya favicon.
JALUR_PUBLIK = ("/", "/masuk", "/daftar", "/kebijakan-privasi", "/lupa-sandi")
JALUR_GURU = ("/akun",)


def _jalur_guru_berdata(sesi_id: int) -> tuple[str, ...]:
    """Halaman guru yang butuh id — sengaja ikut diuji: justru di sinilah
    template baru biasanya lahir (halaman sesi, cetak, laporan)."""
    return (
        f"/sesi/{sesi_id}",
        f"/sesi/{sesi_id}/cetak",
        f"/sesi/{sesi_id}/lampiran",
        f"/laporan/{sesi_id}",
    )


def test_semua_halaman_publik_punya_favicon(server):
    for jalur in JALUR_PUBLIK:
        kode, isi, _ = server.minta(jalur)
        assert kode == 200, f"{jalur} -> {kode}"
        assert 'rel="icon"' in isi, f"{jalur} tanpa favicon"
        assert 'rel="manifest"' in isi, f"{jalur} tanpa manifest"
        assert 'name="theme-color"' in isi, f"{jalur} tanpa theme-color"


def test_semua_halaman_guru_punya_favicon(server):
    for jalur in JALUR_GURU + _jalur_guru_berdata(server.sesi_id):
        kode, isi, _ = server.minta(jalur, auth=("guru", SANDI_GURU))
        assert kode == 200, f"{jalur} -> {kode}"
        assert 'rel="icon"' in isi, f"{jalur} tanpa favicon"


def test_halaman_murid_punya_favicon(server):
    from http_test_kit import SANDI_MURID

    kode, isi, _ = server.minta("/murid", auth=("feby", SANDI_MURID))
    assert kode == 200
    assert 'rel="icon"' in isi, "halaman murid tanpa favicon"


def test_lembar_cetak_punya_favicon_tanpa_og():
    """Kertas A4 tidak di-share ke WhatsApp — og:* di sana hanya sampah."""
    import render
    from generator import buat_lembar

    lembar = buat_lembar(seed=3, jumlah_soal=2)
    for fn in (render.lembar_soal, render.lembar_penilaian):
        halaman = fn(list(lembar.soal), nama="Putri", tanggal="1 Jan")
        assert 'rel="icon"' in halaman, f"{fn.__name__} tanpa favicon"
        assert "og:image" not in halaman, f"{fn.__name__} tidak perlu og:*"


def test_landing_punya_meta_share_absolut(server):
    """Crawler WhatsApp/Facebook menolak path relatif — og:image & og:url
    wajib absolut. Satu konstanta brand.URL_SITUS supaya pindah domain
    nanti = ubah satu baris."""
    kode, isi, _ = server.minta("/")
    assert kode == 200
    assert f'content="{brand.URL_SITUS}/aset/og-image.png"' in isi
    assert f'property="og:url" content="{brand.URL_SITUS}' in isi
    assert 'name="twitter:card" content="summary_large_image"' in isi
    assert f'property="og:title" content="' in isi
    assert brand.URL_SITUS.startswith("https://")


def test_tag_kepala_dipakai_bukan_disalin():
    """Blok favicon harus datang dari brand.tag_kepala(), bukan disalin
    per template — kalau disalin, template ke-15 lahir tanpa favicon dan
    tidak ada yang sadar."""
    for nama in (
        "landing.py",
        "web.py",
        "teacher_pages.py",
        "student_pages.py",
        "attachments.py",
        "render.py",
    ):
        sumber = (ROOT / nama).read_text(encoding="utf-8")
        assert "tag_kepala" in sumber, f"{nama} tidak memakai brand.tag_kepala()"
        assert 'rel="icon"' not in sumber, (
            f"{nama} menyalin blok favicon — pakai brand.tag_kepala()"
        )


MODUL_HALAMAN = (
    "landing.py",
    "web.py",
    "teacher_pages.py",
    "student_pages.py",
    "attachments.py",
    "render.py",
)


def test_setiap_head_memanggil_tag_kepala():
    """Guard STRUKTURAL, bukan lewat HTTP.

    Test lewat HTTP hanya menyentuh halaman yang punya rute aktif — halaman
    legacy dan cabang jarang lolos begitu saja. Terbukti: menghapus satu
    sisipan di student_pages.py (halaman kerja legacy) tidak membuat satu
    pun test HTTP merah. Guard ini menghitung <head> di sumber, jadi
    template mana pun yang lahir tanpa favicon langsung ketahuan.
    """
    kurang: list[str] = []
    for nama in MODUL_HALAMAN:
        sumber = (ROOT / nama).read_text(encoding="utf-8")
        n_head = sumber.count("<head>")
        n_tag = sumber.count("brand.tag_kepala(")
        if n_head != n_tag:
            kurang.append(f"{nama}: {n_head} <head> tapi {n_tag} tag_kepala()")
    assert not kurang, "head tanpa favicon:\n" + "\n".join(kurang)


# ───────────────────── satu lambang, bukan empat ─────────────────────

# Audit 3 Sep: EMPAT lambang berbeda dipakai sebagai logo — 'school' (topi
# wisuda), 'pets' (jejak kaki), SVG owl icons.py, dan teks polos tanpa ikon.
# Anak melihat jejak kaki, orang tua melihat topi wisuda.
GLYPH_LOGO_LAMA = (">school<", ">pets<")


def test_tidak_ada_glyph_logo_lama():
    """Glyph Material Symbols tidak boleh lagi dipakai SEBAGAI LOGO.

    icons.OWL sendiri tidak dihapus — masih dipakai halaman murid legacy
    dan modulnya menyediakan ikon lain (bohlam, chevron, bintang).
    """
    tersangka: list[str] = []
    for nama in MODUL_HALAMAN:
        sumber = (ROOT / nama).read_text(encoding="utf-8")
        for ln_no, ln in enumerate(sumber.splitlines(), 1):
            if any(g in ln for g in GLYPH_LOGO_LAMA):
                tersangka.append(f"{nama}:{ln_no}: {ln.strip()}")
    assert not tersangka, (
        "glyph logo lama masih dipakai — pakai brand.mark():\n"
        + "\n".join(tersangka)
    )


def test_token_ukuran_logo_ada():
    """Ukuran logo lewat token, bukan angka acak per CSS (audit menemukan
    20,8px vs 21,6px untuk ikon brand yang sama)."""
    for nama in ("LOGO_TOPBAR", "LOGO_BADGE", "LOGO_HERO", "WARNA_WORDMARK"):
        assert getattr(T, nama, None), f"token {nama} belum ada"


def test_warna_wordmark_satu_nilai():
    """Audit: wordmark dirender #0FA3A3 di satu tempat dan #0a7d7d di
    tempat lain — nama produk berganti rona antar halaman.

    Dua jebakan yang sudah kena saat menulis guard ini:
    1. Assert "token ada di CSS" TIDAK cukup — nilainya sama dengan
       AKSEN_MURID_UTAMA yang muncul di puluhan aturan lain, jadi test
       tetap hijau meski wordmark di-hardcode kembali.
    2. Memeriksa CSS yang sudah dirender juga sia-sia: di sana token SUDAH
       jadi hex. Yang harus diperiksa adalah SUMBER stylesheet.
    """
    import re

    from style_stitch import gaya_stitch

    assert T.WARNA_WORDMARK in gaya_stitch()

    tersangka: list[str] = []
    for nama in ("style_stitch.py", "teacher_style.py"):
        sumber = (ROOT / nama).read_text(encoding="utf-8")
        for blok in re.finditer(r"([^{}\n]*)\{\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\}", sumber):
            selektor, isi = blok.group(1), blok.group(2)
            if "brand" not in selektor and "wordmark" not in selektor:
                continue
            for hexa in re.findall(r"#[0-9a-fA-F]{3,8}\b", isi):
                tersangka.append(f"{nama}: {selektor.strip()} -> {hexa}")
    assert not tersangka, (
        "hex hardcoded di aturan brand — pakai T.WARNA_WORDMARK:\n"
        + "\n".join(tersangka)
    )


def test_mark_dipakai_di_semua_permukaan_brand(server):
    """Landing, masuk, dashboard guru, dan halaman anak memakai mark yang
    SAMA — satu lambang, bukan empat."""
    from http_test_kit import SANDI_MURID

    permukaan = (
        ("/", None),
        ("/masuk", None),
        ("/daftar", None),
        ("/", ("guru", SANDI_GURU)),
        ("/murid", ("feby", SANDI_MURID)),
    )
    for jalur, kred in permukaan:
        kode, isi, _ = server.minta(jalur, auth=kred)
        assert kode == 200, f"{jalur} -> {kode}"
        assert "/aset/mark-" in isi, f"{jalur} tanpa mark brand"


def test_topbar_guru_legacy_punya_mark():
    """Topbar guru non-Stitch dulu teks polos tanpa ikon sama sekali —
    lambang keempat dari audit."""
    import teacher_pages

    bar = teacher_pages._topbar("guru", "guru")
    assert "/aset/mark-" in bar, "topbar legacy tanpa mark"
    assert T.NAMA_PRODUK in bar


# ───────────────────────── judul halaman seragam ─────────────────────────

def test_judul_helper_pola_tunggal():
    """Satu pola: "<Halaman> · Jagomat". Landing cukup nama produk saja."""
    assert brand.judul("Akun") == f"Akun · {T.NAMA_PRODUK}"
    assert brand.judul("") == T.NAMA_PRODUK
    assert brand.judul(T.NAMA_PRODUK) == T.NAMA_PRODUK
    # pemisah lama (— dan ·) dinormalisasi, bukan ditumpuk
    assert brand.judul(f"Daftar — {T.NAMA_PRODUK}") == f"Daftar · {T.NAMA_PRODUK}"
    assert brand.judul(f"Sesiku · {T.NAMA_PRODUK}") == f"Sesiku · {T.NAMA_PRODUK}"
    assert brand.judul("Sesi #1 — Cetak") == f"Sesi #1 — Cetak · {T.NAMA_PRODUK}"


def test_semua_judul_halaman_menyebut_brand(server):
    """Audit 3 Sep: 6 halaman tanpa nama brand sama sekali di tab browser
    (Akun, Laporan Putri, Panel Pengelola, Sesi #1 — Cetak, Sesi #1 —
    Lampiran, Hapus sesi #3?), dan pemisah campur — vs ·."""
    import re

    from http_test_kit import SANDI_MURID

    permukaan = [(j, None) for j in JALUR_PUBLIK]
    permukaan += [(j, ("guru", SANDI_GURU)) for j in JALUR_GURU]
    permukaan += [
        (j, ("guru", SANDI_GURU)) for j in _jalur_guru_berdata(server.sesi_id)
    ]
    permukaan += [("/murid", ("feby", SANDI_MURID))]

    for jalur, kred in permukaan:
        kode, isi, _ = server.minta(jalur, auth=kred)
        assert kode == 200, f"{jalur} -> {kode}"
        m = re.search(r"<title>(.*?)</title>", isi, re.S)
        assert m, f"{jalur} tanpa <title>"
        judul = m.group(1)
        assert T.NAMA_PRODUK in judul, f"{jalur}: judul '{judul}' tanpa brand"
        if judul.strip() != T.NAMA_PRODUK:
            assert f"· {T.NAMA_PRODUK}" in judul, (
                f"{jalur}: '{judul}' tidak memakai pemisah tunggal '·'"
            )


def test_judul_lembar_cetak_menyebut_brand():
    import render
    from generator import buat_lembar

    lembar = buat_lembar(seed=5, jumlah_soal=2)
    for fn in (render.lembar_soal, render.lembar_penilaian):
        halaman = fn(list(lembar.soal), nama="Putri", tanggal="1 Jan")
        judul = halaman.split("<title>")[1].split("</title>")[0]
        assert f"· {T.NAMA_PRODUK}" in judul, f"{fn.__name__}: '{judul}'"


# ───────────────────────── maskot ayam jago ─────────────────────────

def test_maskot_aset_ada_dan_transparan():
    """Maskot wajib PNG beralpha. Aset asalnya latar putih solid
    (hasAlpha: no) — kalau yang itu yang terpasang, anak melihat kotak
    putih di halaman cream."""
    from struct import unpack

    for pose in brand.POSE_MASKOT:
        for px in (240, 96):
            nama = f"maskot-{pose}-{px}.png"
            assert nama in brand.ASET, f"{nama} tidak di allow-list"
            p = ROOT / "aset" / nama
            assert p.is_file(), f"{nama} tidak ada di disk"
            data = p.read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{nama} bukan PNG"
            # IHDR: lebar, tinggi, bit depth, color type
            lebar, tinggi = unpack(">II", data[16:24])
            jenis_warna = data[25]
            assert max(lebar, tinggi) == px, f"{nama}: {lebar}x{tinggi} != {px}"
            # 3 = palette (alpha lewat tRNS), 6 = RGBA
            assert jenis_warna in (3, 6), f"{nama}: color type {jenis_warna}"
            if jenis_warna == 3:
                assert b"tRNS" in data, f"{nama}: palette tanpa tRNS = tak transparan"


def test_maskot_ringan():
    """Halaman anak sering dibuka di HP. Aset mentah 132 KB per pose;
    setelah crop+kuantisasi harus jauh di bawah itu."""
    total = 0
    for pose in brand.POSE_MASKOT:
        for px in (240, 96):
            n = (ROOT / "aset" / f"maskot-{pose}-{px}.png").stat().st_size
            batas = 15_000 if px == 240 else 5_000
            assert n < batas, f"maskot-{pose}-{px}.png {n}B melebihi {batas}B"
            total += n
    assert total < 40_000, f"total maskot {total}B terlalu berat"


def test_maskot_helper_menolak_pose_dan_ukuran_asing():
    """Pose 'berpikir' sengaja tidak ada (crop-nya cacat). Helper harus
    MENOLAK keras, bukan diam-diam menyajikan 404 ke anak."""
    import pytest as _pytest

    assert "berpikir" not in brand.POSE_MASKOT
    with _pytest.raises(ValueError):
        brand.maskot("berpikir")
    with _pytest.raises(ValueError):
        brand.maskot("netral", 512)
    for pose in brand.POSE_MASKOT:
        assert f"/aset/maskot-{pose}-240.png" in brand.maskot(pose)


def test_maskot_alt_kosong_default():
    """Maskot hiasan, bukan informasi: pembaca layar harus melewatinya,
    supaya anak tidak mendengar 'gambar ayam' sebelum tiap sapaan."""
    assert 'alt=""' in brand.maskot()
    assert 'alt="Ayam jago merayakan"' in brand.maskot(
        "merayakan", alt="Ayam jago merayakan"
    )


def test_maskot_lazy_load():
    """Maskot tidak boleh memblokir render halaman anak."""
    m = brand.maskot()
    assert 'loading="lazy"' in m and 'decoding="async"' in m


def test_maskot_terlayani_lewat_rute_aset(server):
    for pose in brand.POSE_MASKOT:
        for px in (240, 96):
            kode, isi, hdr = server.minta(f"/aset/maskot-{pose}-{px}.png", biner=True)
            assert kode == 200, f"maskot-{pose}-{px} -> {kode}"
            assert hdr["Content-Type"] == "image/png"
            assert isi[:8] == b"\x89PNG\r\n\x1a\n"


def test_maskot_tidak_dicetak():
    """Keputusan 3 Sep: kertas A4 tetap fokus ke soal, hemat tinta warna."""
    import render
    from generator import buat_lembar

    lembar = buat_lembar(seed=9, jumlah_soal=2)
    for fn in (render.lembar_soal, render.lembar_penilaian):
        halaman = fn(list(lembar.soal), nama="Putri", tanggal="1 Jan")
        assert "maskot-" not in halaman, f"{fn.__name__} memuat maskot"
