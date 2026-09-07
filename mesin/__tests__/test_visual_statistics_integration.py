"""Integrasi opt-in statistika visual sampai permukaan HTTP."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import llm  # noqa: E402
import question_views  # noqa: E402
import share_links  # noqa: E402
import topic_number_patterns  # noqa: E402
import topic_statistics  # noqa: E402
from http_test_kit import SANDI_GURU, SANDI_MURID, ServerUji  # noqa: E402
from visual_contract import deserialisasi_penyajian  # noqa: E402
from visual_renderer import render_pertanyaan, ringkasan_pertanyaan  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    jalur = tmp_path / "statistika-visual.db"
    database.siapkan(jalur)
    return jalur


@pytest.fixture()
def server(tmp_path, monkeypatch):
    layanan = ServerUji(tmp_path, monkeypatch)
    try:
        yield layanan
    finally:
        layanan.berhenti()


def _soal_statistika():
    return (
        topic_statistics.diagram_batang_garis("jumlah", [10, 15, 20]),
        topic_statistics.tabel_turus(
            "jumlah", ["Apel", "Jeruk", "Mangga"], [4, 7, 9]
        ),
        topic_statistics.piktogram(
            "total", 2, [3, 4, 5], ["Buku", "Pensil", "Penghapus"]
        ),
        topic_statistics.diagram_lingkaran("cari_nilai", 90, 40),
    )


def _buat_sesi_pilihan(kon, siswa, soal):
    soal = tuple(soal)
    return database.buat_sesi_dari_urutan(
        kon,
        siswa,
        seed=20260907,
        urutan=tuple(b.template_id for b in soal),
        topik="statistika-pengukuran",
        level="P3",
        soal_terpilih=soal,
    )


def test_default_tetap_teks_dan_golden_generator_tidak_berubah(monkeypatch):
    monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
    soal = topic_statistics.diagram_batang_garis("baca", [10, 15, 20], 1)
    tanda_tangan = soal.tanda_tangan

    penyajian = question_views.penyajian_dari_soal(soal)

    assert penyajian.teks_soal == soal.teks
    assert penyajian.status_visual == "tanpa_visual"
    assert penyajian.mode_representasi == "teks-v1"
    assert penyajian.descriptor is None
    assert soal.tanda_tangan == tanda_tangan


@pytest.mark.parametrize(
    ("soal", "jenis"),
    zip(_soal_statistika(), ("batang", "turus", "piktogram", "lingkaran")),
)
def test_opt_in_memproyeksikan_dan_reload_descriptor_statistika(
    db, monkeypatch, soal, jenis
):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, f"Anak {jenis}")
        sesi = _buat_sesi_pilihan(kon, siswa, (soal,))
        baris = database.isi_sesi(kon, sesi)[0]
        sidik = baris["fingerprint_penyajian"]
        snapshot = deserialisasi_penyajian(baris["penyajian_json"])

        assert snapshot.status_visual == "siap"
        assert snapshot.mode_representasi == f"{jenis}-v1"
        assert snapshot.descriptor is not None
        assert snapshot.descriptor.jenis == jenis
        assert snapshot.fingerprint_penyajian == sidik

        monkeypatch.delenv("OSN_VISUAL_KELUARGA")
        muat_ulang = question_views.penyajian_dari_baris(
            database.isi_sesi(kon, sesi)[0]
        )

    assert muat_ulang == snapshot
    for gaya in ("cetak", "murid", "stitch", "guru"):
        html = render_pertanyaan(muat_ulang, gaya=gaya, namespace=f"uji-{gaya}")
        assert "<svg" in html
        assert f'data-fingerprint-penyajian="{sidik}"' in html


def test_snapshot_teks_lama_stabil_saat_opt_in_dinyalakan(db, monkeypatch):
    monkeypatch.delenv("OSN_VISUAL_KELUARGA", raising=False)
    soal = topic_statistics.diagram_batang_garis("baca", [10, 15, 20], 1)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Anak lama")
        sesi = _buat_sesi_pilihan(kon, siswa, (soal,))
        sebelum = database.isi_sesi(kon, sesi)[0]

        monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
        sesudah = database.isi_sesi(kon, sesi)[0]
        penyajian = question_views.penyajian_dari_baris(sesudah)

    assert sesudah["penyajian_json"] == sebelum["penyajian_json"]
    assert sesudah["fingerprint_penyajian"] == sebelum["fingerprint_penyajian"]
    assert penyajian.mode_representasi == "teks-v1"
    assert penyajian.descriptor is None


def test_keluarga_opt_in_tidak_dikenal_gagal_tertutup_dan_rollback_sesi(
    db, monkeypatch
):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika-typo")
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Atomik")
        sebelum_soal = kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0]

        with pytest.raises(ValueError, match="keluarga visual tidak dikenal"):
            _buat_sesi_pilihan(kon, siswa, _soal_statistika()[:2])

        assert kon.execute("SELECT COUNT(*) FROM sesi").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM sesi_soal").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == sebelum_soal
        assert kon.execute(
            "SELECT COUNT(*) FROM siswa WHERE id = ?", (siswa,)
        ).fetchone()[0] == 1


def test_visual_tidak_valid_di_butir_kedua_rollback_seluruh_sesi(
    db, monkeypatch
):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
    asli = question_views.proyeksi_statistika
    panggilan = 0

    def proyeksi_dengan_butir_rusak(template_id, parameter):
        nonlocal panggilan
        panggilan += 1
        if panggilan == 2:
            raise ValueError("descriptor visual statistika tidak valid")
        return asli(template_id, parameter)

    monkeypatch.setattr(
        question_views, "proyeksi_statistika", proyeksi_dengan_butir_rusak
    )
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Visual rusak")
        sebelum_soal = kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0]

        with pytest.raises(ValueError, match="descriptor visual"):
            _buat_sesi_pilihan(kon, siswa, _soal_statistika()[:2])

        assert panggilan == 2
        assert kon.execute("SELECT COUNT(*) FROM sesi").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM sesi_soal").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM soal").fetchone()[0] == sebelum_soal


def test_ringkasan_statistika_hanya_menyebut_fakta_visual_bukan_hasil(
    monkeypatch,
):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
    harapan_tidak_ada = ("45", "20", "24", "10 siswa")

    for soal, hasil in zip(_soal_statistika(), harapan_tidak_ada):
        ringkasan = ringkasan_pertanyaan(
            question_views.penyajian_dari_soal(soal)
        )
        assert "Fakta visual:" in ringkasan
        assert hasil not in ringkasan
        assert "jawabannya" not in ringkasan.lower()


def test_llm_melewati_visual_esensial_dengan_hitungan_dan_catatan_eksplisit(
    db, monkeypatch
):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-uji")
    monkeypatch.setattr(llm, "cek_saldo", lambda: True)
    dipanggil = []

    def bungkus_palsu(_kon, soal, putaran=0):
        dipanggil.append((soal.template_id, putaran))
        return "Cerita aman: " + soal.teks.replace("\n", " ")

    monkeypatch.setattr(llm, "bungkus", bungkus_palsu)
    visual = topic_statistics.diagram_batang_garis("baca", [10, 15, 20], 1)
    teks = topic_number_patterns.deret_aritmetika(2, 3, 4, 1)

    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Campuran")
        sesi = _buat_sesi_pilihan(kon, siswa, (visual, teks))
        berhasil, dicoba, catatan = llm.bungkus_sesi(
            kon, sesi, question_views.soal_dari_baris
        )
        baris = database.isi_sesi(kon, sesi)

    assert (berhasil, dicoba) == (1, 1)
    assert dipanggil == [("deret_aritmetika", 0)]
    assert "1 soal visual dilewati" in catatan
    assert baris[0]["asal_teks"] == "bawaan"
    assert baris[0]["status_visual"] == "siap"
    assert baris[1]["asal_teks"] == "cerita"


def test_sesi_visual_tidak_menawarkan_variasi_cerita_tanpa_sasaran(db, monkeypatch):
    import teacher_pages
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
    monkeypatch.setattr(llm, "aktif", lambda: True)
    with database.buka(db) as kon:
        siswa = database.tambah_siswa(kon, "Fixture")
        sesi = _buat_sesi_pilihan(kon, siswa, _soal_statistika())
        isi = teacher_pages._tombol_cerita(kon, sesi)
    assert f'action="/cerita/{sesi}"' not in isi
    assert "4 soal visual" in isi


def test_http_opt_in_statistika_konsisten_di_semua_permukaan_dan_reload(
    server, monkeypatch
):
    monkeypatch.setenv("OSN_VISUAL_KELUARGA", "statistika")
    with server.buka() as kon:
        siswa = database.tambah_siswa(kon, "feby", pemilik="guru")
        sesi = _buat_sesi_pilihan(kon, siswa, _soal_statistika())
        token = share_links.buat(kon, sesi)
        sidik = [b["fingerprint_penyajian"] for b in database.isi_sesi(kon, sesi)]

    monkeypatch.delenv("OSN_VISUAL_KELUARGA")
    target = (
        (f"/mulai/{token}", None),
        (f"/murid/kerjakan/{sesi}", ("feby", SANDI_MURID)),
        (f"/sesi/{sesi}", ("guru", SANDI_GURU)),
        (f"/lembar/{sesi}", ("guru", SANDI_GURU)),
    )
    himpunan_svg = []
    for jalur, identitas in target:
        kode, isi, _ = server.minta(jalur, auth=identitas)
        assert kode == 200
        assert all(f'data-fingerprint-penyajian="{nilai}"' in isi for nilai in sidik)
        svg = re.findall(r'<svg[^>]*role="img".*?</svg>', isi, flags=re.S)
        assert len(svg) >= 4
        himpunan_svg.append(svg)

    assert all(svg == himpunan_svg[0] for svg in himpunan_svg)
    with server.buka() as kon:
        ssid = database.isi_sesi(kon, sesi)[0]["sesi_soal_id"]
    kode, _, _ = server.minta(f"/mulai/{token}", data={f"jwb_{ssid}": "17"})
    assert kode == 200
    kode, isi, _ = server.minta(f"/mulai/{token}")
    assert kode == 200
    assert all(f'data-fingerprint-penyajian="{nilai}"' in isi for nilai in sidik)

    with server.buka() as kon:
        assert kon.execute(
            "SELECT jawaban FROM jawaban WHERE sesi_soal_id = ?", (ssid,)
        ).fetchone()[0] == "17"
        tersimpan = database.isi_sesi(kon, sesi)
        assert [b["fingerprint_penyajian"] for b in tersimpan] == sidik
        assert [
            json.loads(b["penyajian_json"])["descriptor"]["jenis"] for b in tersimpan
        ] == ["batang", "turus", "piktogram", "lingkaran"]
