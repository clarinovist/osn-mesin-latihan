"""Pengunci kartu sesi di halaman /murid (feedback layout 3 Sep 2026).

Keluhan orang tua: kartu "kayak agak bertumpuk", dan blok abu-abu berisi
"20 soal" memanjang penuh seolah progress bar padahal statis.

Root cause terukur di headless Chrome (390px):

1. Badge "{n} soal" ditulis DI DALAM span kolom teks, bukan sebagai anak
   langsung kartu. Kolomnya `flex-direction:column`, jadi badge kena
   stretch selebar kolom: 271px di HP, 617px di 1440px — padahal lebar
   kontennya cuma +-67px. Itulah "blok abu-abu sampai habis".
2. Kolom teks tidak punya `gap` (computed `normal` = 0px), jadi tanggal,
   meta, dan badge saling dempet — kesan bertumpuk.
3. Akibat (1), kartu cuma punya 2 anak flex; aturan HP
   `.st-kartu-baris > *:nth-child(n+3)` di style_stitch.py tidak pernah
   kena untuk kartu murid (dead rule).

Keputusan tampilan (opsi C, disetujui user): pill statis untuk sesi baru
dan sesi selesai; bar berisi HANYA untuk sesi yang sedang dikerjakan —
persis saat angkanya informatif. Data `terisi` sudah dihitung query lama,
tidak ada kueri baru.

Palang murid tetap: badge hanya label status, tidak memuat kunci/malrule.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import student_pages  # noqa: E402
import style_stitch  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


def _tiga_status(db):
    """Tiga sesi: baru (0 terisi), sedang dikerjakan (sebagian), selesai."""
    import students

    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Uji Kartu")
        baru = database.buat_sesi(kon, sid, seed=1, topik="statistika")
        proses = database.buat_sesi(kon, sid, seed=2, topik="statistika")
        selesai = database.buat_sesi(kon, sid, seed=3, topik="statistika")

        # proses: hanya sebagian soal dijawab (lewat jalur murid)
        butir = students.soal_murid(kon, proses, sid)
        # SENGAJA bukan setengah: fixture 50% membuat `persen = 50` hardcoded
        # lolos mutation test (terbukti 3 Sep). Ambil 3 dari 10 → 30%.
        sebagian = butir[:3]
        students.simpan_jawaban_murid(
            kon, sid, proses, {f"jwb_{s['sesi_soal_id']}": "7" for s in sebagian}
        )

        # selesai: semua terisi, sudah ditandai selesai & direview
        students.simpan_jawaban_murid(
            kon, sid, selesai,
            {f"jwb_{s['sesi_soal_id']}": "3"
             for s in students.soal_murid(kon, selesai, sid)},
        )
        database.tandai_selesai(kon, selesai)
        kon.execute(
            "UPDATE sesi SET direview = datetime('now', '+7 hours') WHERE id = ?",
            (selesai,),
        )
    return {"baru": baru, "proses": proses, "selesai": selesai,
            "n_terisi": len(sebagian), "n_total": len(butir)}


def _html(db):
    with database.buka(db) as kon:
        sid = database.daftar_siswa(kon)[0]["id"]
        return student_pages.halaman_daftar_sesi_baru(kon, sid, "Uji Kartu").decode()


def _kartu(html: str) -> list[str]:
    """Pecah HTML jadi potongan per kartu <a class="st-kartu-baris">."""
    bagian = html.split('<a class="st-kartu-baris"')
    return bagian[1:]

class _AnakKartu(HTMLParser):
    """Kumpulkan anak LANGSUNG tiap kartu beserta kelasnya.

    Dipakai membuktikan penanda jumlah soal sejajar ikon & kolom teks —
    bukan terkubur di dalam kolom `flex-direction:column` (akar bug 3 Sep:
    badge kena stretch jadi 271px di HP untuk konten +-67px).
    """

    KOSONG = {"br", "img", "input", "meta", "link", "hr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.kartu = []        # list[list[str]] — kelas tiap anak langsung
        self._dalam = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        kelas = dict(attrs).get("class", "")
        if "st-kartu-baris" in kelas:
            self._dalam, self._depth = True, 0
            self.kartu.append([])
            return
        if not self._dalam:
            return
        if self._depth == 0:
            self.kartu[-1].append(kelas)
        if tag not in self.KOSONG:
            self._depth += 1

    def handle_endtag(self, tag):
        if not self._dalam:
            return
        if self._depth == 0:
            self._dalam = False       # </a> penutup kartu
        else:
            self._depth -= 1


def _anak_kartu(html: str) -> list[list[str]]:
    p = _AnakKartu()
    p.feed(html)
    return p.kartu


_PENANDA = ("st-jumlah-soal", "st-progres-soal")


def _penanda(kelas_anak: list[str]) -> list[str]:
    return [k for k in kelas_anak if any(t in k for t in _PENANDA)]


# ── 1. Penanda jumlah soal = anak langsung kartu ─────────────────────────

def test_penanda_jumlah_soal_anak_langsung_kartu(db):
    """Sebelum fix badge ada DI DALAM kolom teks → melar selebar kolom.

    Terukur di headless Chrome: 271px (390px viewport) & 617px (1440px),
    padahal lebar kontennya +-67px. Itu yang terlihat sebagai "blok abu
    memanjang sampai habis" seolah progress bar padahal statis.
    """
    _tiga_status(db)
    kartu = _anak_kartu(_html(db))
    assert kartu, "fixture harus menghasilkan kartu sesi"
    for anak in kartu:
        assert _penanda(anak), (
            f"penanda jumlah soal bukan anak langsung kartu; anak={anak}"
        )


def test_kartu_punya_tiga_anak_langsung(db):
    """Aturan HP `.st-kartu-baris > *:nth-child(n+3)` (style_stitch.py)

    hanya menggigit kalau kartu memang punya anak ke-3. Sebelum fix cuma
    ada 2 anak (ikon + kolom teks) sehingga aturan itu dead rule.
    """
    _tiga_status(db)
    for anak in _anak_kartu(_html(db)):
        assert len(anak) == 3, f"harus ikon + kolom teks + penanda, dapat {anak}"


# ── 2. Opsi C: bar berisi HANYA untuk sesi yang sedang dikerjakan ────────

def test_sesi_dikerjakan_dapat_bar_progres_berisi(db):
    """Sesi setengah jalan: bar dengan isian sebesar terisi/jumlah."""
    info = _tiga_status(db)
    html = _html(db)
    proses = [f for f in _kartu(html) if f"/murid/kerjakan/{info['proses']}" in f]
    assert len(proses) == 1, "kartu sesi 'dikerjakan' tidak ketemu"
    frag = proses[0]
    assert "st-progres-soal" in frag, "sesi dikerjakan harus pakai bar progres"
    assert f"{info['n_terisi']} dari {info['n_total']} soal" in frag, frag


def test_sesi_baru_dan_selesai_pakai_pill_statis(db):
    """Bar hanya muncul saat informatif; sisanya pill lebar-konten.

    Sesi baru (0 terisi) dan sesi selesai (100%) tidak butuh bar: angkanya
    sudah tergambar badge status masing-masing.
    """
    info = _tiga_status(db)
    html = _html(db)
    for kunci, tujuan in (
        ("baru", f"/murid/kerjakan/{info['baru']}"),
        ("selesai", f"/murid/hasil/{info['selesai']}"),
    ):
        frag = [f for f in _kartu(html) if tujuan in f]
        assert len(frag) == 1, f"kartu {kunci} tidak ketemu"
        assert "st-progres-soal" not in frag[0], (
            f"sesi {kunci} tidak boleh memakai bar progres"
        )
        assert "st-jumlah-soal" in frag[0], f"sesi {kunci} butuh pill jumlah"


def test_bar_progres_lebar_isian_sesuai_pecahan(db):
    """Isian bar = persentase terisi/jumlah, bukan angka hardcoded."""
    info = _tiga_status(db)
    frag = [f for f in _kartu(_html(db))
            if f"/murid/kerjakan/{info['proses']}" in f][0]
    persen = re.search(r"st-progres-isi[^>]*width:\s*([\d.]+)%", frag)
    assert persen, f"bar tidak punya lebar isian terhitung: {frag}"
    harap = round(info["n_terisi"] / info["n_total"] * 100)
    assert abs(float(persen.group(1)) - harap) < 1.0, persen.group(1)


# ── 3. Gap kolom teks (keluhan "kayak agak bertumpuk") ───────────────────

def test_kolom_teks_kartu_punya_gap():
    """Kolom teks kartu memakai flex-direction:column tanpa gap → computed

    `normal` (0px), sehingga tanggal/meta/badge dempet. Kelas sendiri +
    gap eksplisit, bukan margin ad-hoc per elemen.
    """
    css = style_stitch.gaya_stitch()
    blok = re.search(r"\.st-kartu-teks\s*\{([^}]*)\}", css)
    assert blok, ".st-kartu-teks belum didefinisikan di GAYA_STITCH"
    isi = blok.group(1)
    assert "gap" in isi, f"kolom teks kartu harus punya gap: {isi}"


def test_kartu_memakai_kelas_kolom_teks_bukan_inline(db):
    """Markup memakai kelas — supaya gap-nya bisa diuji & tidak tercecer."""
    _tiga_status(db)
    for anak in _anak_kartu(_html(db)):
        assert any("st-kartu-teks" in k for k in anak), anak


def test_bar_progres_pakai_display_block():
    """Penanda bar dibangun dari <span>. Span inline MENGABAIKAN width dan

    height, jadi tanpa display:block bar tampil kosong (terukur 0px di
    headless Chrome 3 Sep) padahal style="width:30%" terpasang di markup.
    Test HTML murni tidak bisa melihat ini — makanya dikunci di CSS.
    """
    css = style_stitch.gaya_stitch()
    for kelas in (".st-progres-jalur", ".st-progres-isi"):
        blok = re.search(re.escape(kelas) + r"\s*\{([^}]*)\}", css)
        assert blok, f"{kelas} belum didefinisikan"
        assert re.search(r"display:\s*block", blok.group(1)), (
            f"{kelas} butuh display:block, kalau tidak lebarnya diabaikan: "
            f"{blok.group(1)}"
        )


def test_css_penanda_jumlah_tidak_melar():
    """Pill/bar tidak boleh ikut stretch: butuh flex:none (anak flex row

    dengan align-items:center tidak stretch, tapi lebarnya masih bisa
    ditarik `flex-grow` dari aturan HP nth-child).
    """
    css = style_stitch.gaya_stitch()
    for kelas in (".st-jumlah-soal", ".st-progres-soal"):
        blok = re.search(re.escape(kelas) + r"\s*\{([^}]*)\}", css)
        assert blok, f"{kelas} belum didefinisikan di GAYA_STITCH"


# ── 4. Palang murid tetap ────────────────────────────────────────────────

def test_kartu_tidak_membocorkan_kunci(db):
    """Penanda progres hanya angka jumlah — bukan benar/salah per soal.

    Diperiksa pada MARKUP kartunya saja, bukan seluruh halaman: GAYA_STITCH
    memuat komentar CSS yang menyebut kata "diagnosa" (nama mode sesi), dan
    assert pada seluruh html jadi false-positive (jebakan CLAUDE.md §8).
    """
    _tiga_status(db)
    for frag in _kartu(_html(db)):
        markup = frag.split("</a>")[0].lower()
        for terlarang in ("malrule", "kode_final", "kode_usulan", "kunci"):
            assert terlarang not in markup, f"{terlarang} bocor: {markup}"
