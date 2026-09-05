"""Laporan ramah orang tua — ringkasan, kamus kode, detail teknis.

Bahasa teknis (B/K/H/E/T/N, miskonsepsi, malrule) membingungkan orang tua:
laporan kini dibuka dengan ringkasan 3 kalimat + kamus arti nilai, dan
tabel teknisnya dilipat di <details> (tetap ada untuk guru).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import reports  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    import auth

    berkas = tmp_path / "sandi.json"
    monkeypatch.setattr(auth, "BERKAS_SANDI", berkas)
    auth.simpan_sandi("sandi-lama-panjang", "guru", berkas)
    d = tmp_path / "uji.db"
    database.siapkan(d)
    return d


def _sesi_dinilai(kon, sid, benar=8, jumlah=10, kode="K"):
    """Satu sesi berisi + diagnosis manual, tanpa lewat HTTP."""
    import teacher_pages

    sesi_id = database.buat_sesi(kon, sid, seed=jumlah * 100 + benar)
    isi = database.isi_sesi(kon, sesi_id)
    data = {}
    for i, b in enumerate(isi[:jumlah]):
        if i < benar:
            data[f"jwb_{b['sesi_soal_id']}"] = b["kunci"]
            data[f"cara_{b['sesi_soal_id']}"] = "coretan"
        else:
            data[f"jwb_{b['sesi_soal_id']}"] = "pasti salah"
            data[f"cara_{b['sesi_soal_id']}"] = "coretan"
            data[f"kode_{b['sesi_soal_id']}"] = kode
    teacher_pages.simpan_sesi(kon, sesi_id, data)
    return sesi_id


def test_ringkasan_ortu_menyebut_nama_dan_kondisi(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Bima")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        _sesi_dinilai(kon, sid, benar=7, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Ringkasan untuk orang tua" in h
    assert "Bima" in h
    assert "perlu dilatih" in h.lower() or "konsep" in h.lower()


def test_ringkasan_merayakan_tanpa_kata_teknis(db):
    """K=0: kalimat perayaan, tanpa kata yang menakuti (miskonsepsi).

    CSS global ikut ter-render di <style> (kata "diagnosis" ada di nama
    kelas), jadi yang dicek hanya ISI laporan — setelah </style>.
    """
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Rara")
        _sesi_dinilai(kon, sid, benar=10, jumlah=10)
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Ringkasan untuk orang tua" in h
    isi = h.split("</style>", 1)[1]
    assert "miskonsepsi" not in isi.lower()
    assert "malrule" not in isi.lower()


def test_kamus_tanpa_jargon(db):
    """Enam kode dijelaskan bahasa sehari-hari, tanpa kata teknis.

    Seperti test di atas: CSS ikut ter-render, jadi cek isi saja.
    """
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Kamus")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Cara membaca laporan" in h
    for kata in ("salah konsep", "salah baca", "salah hitung",
                 "salah tulis", "belum pernah", "menebak"):
        assert kata in h.lower(), f"kamus kehilangan '{kata}'"
    # kamus & ringkasan bebas jargon teknis
    atas = h.split("</style>", 1)[1].split("Detail per sesi")[0]
    assert "malrule" not in atas.lower()
    assert "miskonsepsi" not in atas.lower()


def test_topik_tampil_nama_ramah(db):
    """Id teknis (pola-bilangan) tampil sebagai nama ramah (Pola Bilangan)."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Topik")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Pola Bilangan" in h


def test_kartu_perhatian_tidak_bilang_kuat_saat_ada_k(db):
    """Regresi dari screenshot: ringkasan bilang 6 K tapi kartu bilang
    'belum ada kekeliruan' — K manual tanpa malrule tak masuk miskonsepsi."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Kontradiksi")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    isi = h.split("</style>", 1)[1].split("Detail per sesi")[0]
    assert "Belum ada kekeliruan" not in isi
    assert "kekeliruan konsep" in isi


def test_tabel_teknis_dilipat_tapi_tetap_ada(db):
    """Guru tetap dapat tabelnya: markup utuh di dalam <details>."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Lipat")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()
    assert "<details" in h
    assert '<th scope="col">Topik</th>' in h
    assert h.index("<details") < h.index('<th scope="col">Topik</th>')


def test_topik_tak_dikenal_tidak_500(db):
    """Sesi warisan ber-topik asing: laporan tetap 200, tampil apa adanya."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Warisan")
        sesi_id = database.buat_sesi(kon, sid, seed=5)
        kon.execute("UPDATE sesi SET topik = ? WHERE id = ?", ("topik-hantu", sesi_id))
        h = reports.halaman_laporan(kon, sid).decode()
    assert "Ringkasan untuk orang tua" in h
    assert "topik-hantu" in h


def test_nama_tipe_soal_menerjemahkan_id_internal():
    assert reports._nama_tipe_soal("benar_salah_pengandaian") == (
        "Pengandaian benar atau salah"
    )
    assert reports._nama_tipe_soal("luas_kotak_satuan") == (
        "Menghitung luas dengan kotak satuan"
    )
    assert reports._nama_tipe_soal("tipe_warisan_asing") == "Tipe warisan asing"


def test_tanggal_laporan_pendek_dan_aman_untuk_data_lama():
    assert reports._tanggal_pendek("2026-09-04") == (
        '<time class="tanggal-ringkas" datetime="2026-09-04">4 Sep 2026</time>'
    )
    assert reports._tanggal_pendek("tanggal lama") == (
        '<span class="tanggal-ringkas">tanggal lama</span>'
    )


def _beri_diagnosis(kon, sesi_id, indeks, kode, malrule_id=None, alasan=""):
    baris = database.isi_sesi(kon, sesi_id)[indeks]
    jawaban_id = database.simpan_jawaban(
        kon,
        baris["sesi_soal_id"],
        jawaban="0",
        belum_pernah=kode == "T",
    )
    database.simpan_diagnosis(
        kon,
        jawaban_id,
        benar=False,
        kode_usulan=kode,
        kode_final=kode,
        malrule_id=malrule_id,
        alasan=alasan,
    )
    return baris["template_id"]


def test_laporan_memisahkan_prioritas_dari_materi_baru(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Aksi")
        sesi_k1 = database.buat_sesi(kon, sid, seed=77, topik="logika")
        sesi_k2 = database.buat_sesi(kon, sid, seed=79, topik="logika")
        sesi_t = database.buat_sesi(kon, sid, seed=78, topik="geometri-datar")
        tipe_k = _beri_diagnosis(
            kon,
            sesi_k1,
            0,
            "K",
            malrule_id="uji.pengandaian",
            alasan="menganggap kebalikan pernyataan selalu benar",
        )
        _beri_diagnosis(
            kon,
            sesi_k2,
            0,
            "K",
            malrule_id="uji.pengandaian",
            alasan="menganggap kebalikan pernyataan selalu benar",
        )
        tipe_t = _beri_diagnosis(kon, sesi_t, 0, "T")
        h = reports.halaman_laporan(kon, sid).decode()

    utama = h.split("Detail per sesi", 1)[0]
    assert "Prioritas latihan" in utama
    assert "Materi berikutnya untuk dikenalkan" in utama
    assert utama.index("Prioritas latihan") < utama.index(
        "Materi berikutnya untuk dikenalkan"
    )
    assert "Yang bisa dilakukan" in utama
    assert "bukan kesalahan" in utama.lower()
    assert tipe_k not in utama
    assert tipe_t not in utama
    assert "_" not in reports._nama_tipe_soal(tipe_k)
    assert "_" not in reports._nama_tipe_soal(tipe_t)


def test_prioritas_belum_menganggap_satu_sesi_sebagai_pola_berulang(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Belum Berulang")
        sesi_id = database.buat_sesi(kon, sid, seed=80, topik="logika")
        tipe = _beri_diagnosis(
            kon,
            sesi_id,
            0,
            "K",
            malrule_id="uji.sekali",
            alasan="baru muncul sekali",
        )
        h = reports.halaman_laporan(kon, sid).decode()

    utama = h.split("Materi berikutnya untuk dikenalkan", 1)[0]
    assert reports._nama_tipe_soal(tipe) not in utama
    assert "polanya belum berulang" in utama
    assert "belum cukup data" in utama.lower()
    assert "Mulai dari topik" not in utama


def test_label_singkatan_dan_alasan_tidak_dirusak(db):
    assert reports._nama_tipe_soal("fpb_kpk_hubungan") == "Hubungan FPB dan KPK"
    assert reports._rapikan_kalimat("menggunakan FPB & KPK.") == (
        "Menggunakan FPB & KPK."
    )


def test_ringkasan_memasangkan_tipe_dengan_topik_fokus(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Fokus Konsisten", "P5")
        # Logika dibuat lebih dulu agar berada di belakang urutan DESC.
        sesi_logika_1 = database.buat_sesi(kon, sid, seed=90, topik="logika")
        sesi_logika_2 = database.buat_sesi(kon, sid, seed=91, topik="logika")
        _beri_diagnosis(
            kon, sesi_logika_1, 0, "K", "uji.logika", "keliru logika"
        )
        _beri_diagnosis(
            kon, sesi_logika_2, 0, "K", "uji.logika", "keliru logika"
        )
        for seed in (92, 93, 94):
            sesi_geo = database.buat_sesi(
                kon, sid, seed=seed, level="P5", topik="geometri-datar"
            )
            _beri_diagnosis(
                kon, sesi_geo, 0, "K", "uji.geometri", "keliru geometri"
            )
        pola_geo = {
            reports._nama_tipe_soal(str(m["template_id"]))
            for m in database.miskonsepsi_berulang(kon, sid)
            if m["topik"] == "geometri-datar" and m["jumlah_sesi"] > 1
        }
        h = reports.halaman_laporan(kon, sid).decode()

    ringkasan = h.split('<div class="kartu-stat">', 1)[0]
    assert "Geometri Datar" in ringkasan
    assert pola_geo
    assert any(nama in ringkasan for nama in pola_geo)
    assert "Pengandaian benar atau salah" not in ringkasan


def test_hierarki_utama_mengutamakan_konsep_bukan_persentase(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Hierarki")
        _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        h = reports.halaman_laporan(kon, sid).decode()

    utama = h.split("Detail per sesi", 1)[0]
    assert "sesi diikuti" in utama
    assert "kekeliruan konsep" in utama
    assert "fokus latihan" in utama
    assert "% jawaban tepat" in utama
    assert '<details class="kartu cara-baca-laporan">' in utama
    assert "<summary><h2" in utama
    assert "Cara membaca laporan" in utama
    assert "Arti nilai anak" not in utama


def test_detail_teknis_semantik_dan_legenda_dekat_tabel(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Teknis")
        sesi_id = _sesi_dinilai(kon, sid, benar=6, jumlah=10, kode="K")
        kon.execute(
            "UPDATE sesi SET tanggal = ? WHERE id = ?", ("2026-09-04", sesi_id)
        )
        h = reports.halaman_laporan(kon, sid).decode()

    detail = h.split("Detail per sesi", 1)[1]
    assert "K = keliru konsep" in detail
    assert '<th scope="col">Tanggal</th>' in detail
    assert "<thead>" in detail and "<tbody>" in detail
    assert '<time class="tanggal-ringkas" datetime="2026-09-04">4 Sep 2026</time>' in detail
