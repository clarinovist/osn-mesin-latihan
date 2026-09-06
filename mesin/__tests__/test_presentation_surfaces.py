"""Kontrak Fase 2: snapshot yang sama di setiap permukaan sesi."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import attachments
import database
import question_views
import student_pages
import students
import teacher_pages


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "permukaan.db"
    database.siapkan(path)
    monkeypatch.setattr(database, "BAWAAN", path)
    return path


def _sesi(kon):
    siswa = database.tambah_siswa(kon, "Fixture visual", pemilik="guru")
    sesi = database.buat_sesi(kon, siswa, seed=42)
    return siswa, sesi


def test_adapter_guru_membawa_snapshot_bukan_rekonstruksi_visual(db):
    with database.buka(db) as kon:
        _, sesi = _sesi(kon)
        baris = database.isi_sesi(kon, sesi)[0]
        soal = question_views.soal_dari_baris(baris)
        assert getattr(soal, "penyajian", None) == question_views.penyajian_dari_baris(baris)


def test_semua_permukaan_memakai_fingerprint_snapshot_yang_sama(db):
    with database.buka(db) as kon:
        siswa, sesi = _sesi(kon)
        baris = database.isi_sesi(kon, sesi)
        sidik = [b["fingerprint_penyajian"] for b in baris]
        halaman = [
            student_pages.halaman_kerja(kon, siswa, sesi),
            teacher_pages.halaman_sesi(kon, sesi),
            teacher_pages.halaman_lembar(kon, sesi),
        ]
        kon.execute("UPDATE sesi SET direview = '2026-09-07' WHERE id = ?", (sesi,))
        halaman.append(student_pages.halaman_hasil_murid(kon, siswa, sesi))
        for isi in halaman:
            teks = isi.decode() if isinstance(isi, bytes) else isi
            for fingerprint in sidik:
                assert f'data-fingerprint-penyajian="{fingerprint}"' in teks


def test_soal_murid_menyertakan_kontrak_beku_tanpa_parameter(db):
    with database.buka(db) as kon:
        siswa, sesi = _sesi(kon)
        butir = students.soal_murid(kon, sesi, siswa)[0]
        assert "penyajian" in butir
        assert butir["penyajian"].teks_soal == butir["teks"]
        assert not {"parameter", "kunci", "malrule", "diagnosis"} & set(butir)


def test_cetak_snapshot_nonvisual_tidak_menambahkan_svg_lama(db):
    with database.buka(db) as kon:
        _, sesi = _sesi(kon)
        assert any(b["template_id"] == "korek_api" for b in database.isi_sesi(kon, sesi))
        html = teacher_pages.halaman_lembar(kon, sesi).decode()
        assert "data-gambar=" not in html


def test_semua_stylesheet_memuat_svg_proporsional():
    from style_stitch import GAYA_STITCH
    from teacher_style import GAYA_GURU
    from screen_style import GAYA_LAYAR
    from print_style import GAYA_CETAK
    for css in (GAYA_STITCH, GAYA_GURU, GAYA_LAYAR, GAYA_CETAK, student_pages.CSS_MURID):
        assert '[data-fingerprint-penyajian] svg' in css
        blok = css.split('[data-fingerprint-penyajian] svg', 1)[1].split('}', 1)[0]
        assert 'height: auto' in blok


def test_konfirmasi_lampiran_memakai_snapshot_lengkap(db):
    with database.buka(db) as kon:
        _, sesi = _sesi(kon)
        lid = database.simpan_lampiran(kon, sesi, "fixture.jpg", mime="image/jpeg", hasil_json="")
        sidik = database.isi_sesi(kon, sesi)[0]["fingerprint_penyajian"]
        isi = attachments.halaman_konfirmasi(kon, lid).decode()
        assert f'data-fingerprint-penyajian="{sidik}"' in isi


def test_konteks_lampiran_tidak_membaca_kolom_rahasia(db):
    with database.buka(db) as kon:
        _, sesi = _sesi(kon)
        harapan = [b["teks_soal"] for b in database.isi_sesi(kon, sesi)]
        dilarang = {"kunci", "malrule_id", "kode_usulan", "kode_final", "alasan"}
        def palang(aksi, tabel, kolom, nama_db, pemicu):
            if aksi == sqlite3.SQLITE_READ and (kolom in dilarang or tabel in {"diagnosis", "malrule"}):
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        kon.set_authorizer(palang)
        assert attachments._teks_konteks(kon, sesi) == harapan
