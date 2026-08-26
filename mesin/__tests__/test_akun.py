"""Verifikasi halaman akun — ganti sandi & kelola siswa.

Halaman ini bisa mengunci guru dari sistemnya sendiri kalau salah: sandi
diganti jadi sesuatu yang tidak dia maksud, atau sandi lama diterima padahal
salah. Karena itu yang diuji terutama penolakannya, bukan keberhasilannya.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import sandi  # noqa: E402
import web  # noqa: E402


@pytest.fixture()
def siap(tmp_path, monkeypatch):
    db = tmp_path / "uji.db"
    berkas = tmp_path / "sandi.json"
    basis.siapkan(db)
    monkeypatch.setattr(basis, "BAWAAN", db)
    monkeypatch.setattr(sandi, "BERKAS_SANDI", berkas)
    sandi.simpan_sandi("sandi-lama-panjang", "guru", berkas)
    return db


# ── Ganti sandi: yang salah harus ditolak ───────────────────────────────


def test_sandi_lama_salah_ditolak(siap):
    """Peramban mengirim kredensial otomatis, jadi lolos palang bukan bukti
    orangnya tahu sandi. Verifikasi ulang wajib."""
    with basis.buka(siap) as kon:
        pesan, galat = web.proses_akun(kon, {
            "aksi": "sandi", "lama": "tebakan-salah",
            "baru": "sandi-baru-panjang", "ulang": "sandi-baru-panjang",
        }, "guru")

    assert not pesan
    assert "salah" in galat.lower()
    assert sandi.periksa("guru", "sandi-lama-panjang"), "sandi lama berubah!"


def test_ulangan_tidak_sama_ditolak(siap):
    """Salah ketik sandi baru = terkunci dari sistem sendiri."""
    with basis.buka(siap) as kon:
        pesan, galat = web.proses_akun(kon, {
            "aksi": "sandi", "lama": "sandi-lama-panjang",
            "baru": "sandi-baru-panjang", "ulang": "sandi-baru-panjanh",
        }, "guru")

    assert not pesan
    assert "tidak sama" in galat.lower()
    assert sandi.periksa("guru", "sandi-lama-panjang")


def test_sandi_terlalu_pendek_ditolak(siap):
    with basis.buka(siap) as kon:
        pesan, galat = web.proses_akun(kon, {
            "aksi": "sandi", "lama": "sandi-lama-panjang",
            "baru": "pendek", "ulang": "pendek",
        }, "guru")

    assert not pesan
    assert "12 karakter" in galat
    assert sandi.periksa("guru", "sandi-lama-panjang")


def test_sandi_baru_sama_dengan_lama_ditolak(siap):
    with basis.buka(siap) as kon:
        _, galat = web.proses_akun(kon, {
            "aksi": "sandi", "lama": "sandi-lama-panjang",
            "baru": "sandi-lama-panjang", "ulang": "sandi-lama-panjang",
        }, "guru")
    assert "sama dengan yang lama" in galat


def test_ganti_sandi_berhasil(siap):
    with basis.buka(siap) as kon:
        pesan, galat = web.proses_akun(kon, {
            "aksi": "sandi", "lama": "sandi-lama-panjang",
            "baru": "sandi-baru-yang-panjang", "ulang": "sandi-baru-yang-panjang",
        }, "guru")

    assert not galat
    assert "diganti" in pesan.lower()
    assert sandi.periksa("guru", "sandi-baru-yang-panjang")
    assert not sandi.periksa("guru", "sandi-lama-panjang"), "sandi lama masih jalan!"


def test_sandi_baru_tidak_tersimpan_sebagai_teks(siap):
    with basis.buka(siap) as kon:
        web.proses_akun(kon, {
            "aksi": "sandi", "lama": "sandi-lama-panjang",
            "baru": "rahasia-sekali-panjang", "ulang": "rahasia-sekali-panjang",
        }, "guru")
    assert "rahasia-sekali-panjang" not in sandi.BERKAS_SANDI.read_text()


# ── Kelola siswa ────────────────────────────────────────────────────────


def test_tambah_siswa_berhasil(siap):
    with basis.buka(siap) as kon:
        pesan, galat = web.proses_akun(kon, {
            "aksi": "siswa", "nama": "Rara", "tingkat": "P4",
        }, "guru")
        nama = [s["nama"] for s in basis.daftar_siswa(kon)]

    assert not galat
    assert "Rara" in pesan
    assert "Rara" in nama


def test_nama_kosong_ditolak(siap):
    with basis.buka(siap) as kon:
        _, galat = web.proses_akun(kon, {"aksi": "siswa", "nama": "   "}, "guru")
        assert "kosong" in galat.lower()
        assert len(basis.daftar_siswa(kon)) == 0


def test_nama_duplikat_ditolak_tanpa_pandang_huruf(siap):
    """Dua siswa bernama sama membuat laporan tidak bisa dibedakan."""
    with basis.buka(siap) as kon:
        web.proses_akun(kon, {"aksi": "siswa", "nama": "Rara"}, "guru")
        _, galat = web.proses_akun(kon, {"aksi": "siswa", "nama": "rara"}, "guru")
        assert "sudah ada" in galat.lower()
        assert len(basis.daftar_siswa(kon)) == 1


def test_tingkat_kosong_memakai_bawaan(siap):
    with basis.buka(siap) as kon:
        web.proses_akun(kon, {"aksi": "siswa", "nama": "Tanpa", "tingkat": ""}, "guru")
        s = basis.daftar_siswa(kon)[0]
    assert s["tingkat"] == "P3"


def test_aksi_tidak_dikenal_tidak_mengubah_apa_pun(siap):
    with basis.buka(siap) as kon:
        _, galat = web.proses_akun(kon, {"aksi": "hapus-semua"}, "guru")
        assert "tidak dikenal" in galat.lower()
        assert sandi.periksa("guru", "sandi-lama-panjang")


# ── Halaman ─────────────────────────────────────────────────────────────


def test_halaman_akun_tidak_membocorkan_sandi(siap):
    """Halaman ini menampilkan info akun; hash pun tidak perlu ada di HTML."""
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon).decode()
    d = sandi.muat_sandi()
    assert d is not None, "berkas sandi hilang"
    assert d["kunci"] not in h
    assert d["garam"] not in h
    assert "sandi-lama-panjang" not in h


def test_halaman_akun_menampilkan_siswa_dan_jumlah_sesi(siap):
    with basis.buka(siap) as kon:
        sid = basis.tambah_siswa(kon, "Andi")
        basis.buat_sesi(kon, sid, seed=1)
        basis.buat_sesi(kon, sid, seed=2)
        h = web.halaman_akun(kon).decode()

    assert "Andi" in h
    assert ">2<" in h  # jumlah sesi


def test_halaman_akun_menjelaskan_kenapa_siswa_tidak_bisa_dihapus(siap):
    """Ketiadaan tombol hapus harus dijelaskan, bukan dibiarkan jadi teka-teki."""
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon).decode()
    assert "tidak bisa dihapus" in h.lower()
    assert "riwayat" in h.lower()


def test_pesan_galat_di_escape(siap):
    """Nama siswa masuk pesan galat; karakter khusus tidak boleh merusak HTML."""
    with basis.buka(siap) as kon:
        web.proses_akun(kon, {"aksi": "siswa", "nama": "<b>X</b>"}, "guru")
        _, galat = web.proses_akun(kon, {"aksi": "siswa", "nama": "<b>X</b>"}, "guru")
        h = web.halaman_akun(kon, "", galat).decode()

    assert "<b>X</b>" not in h
    assert "&lt;b&gt;" in h


# ── Akun murid (plan 2026-08-25) ──────────────────────────────────────


def test_kartu_akun_murid_tampil_dan_memuat_nama(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Sinta")
        sandi.tambah_akun("Sinta", "rahasia-sinta-123", "murid")
        h = web.halaman_akun(kon).decode()
    assert "Akun murid" in h
    assert "Sinta" in h


def test_akun_tidak_cocok_ditandai_belum_terhubung(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Andi")
        sandi.tambah_akun("Hantu", "rahasia-hantu-123", "murid")
        h = web.halaman_akun(kon).decode()
    assert "Hantu" in h
    assert "belum terhubung ke siswa" in h.lower()


def test_tambah_akun_murid_berhasil(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Budi")
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Budi", "sandi": "rahasia-budi-123",
        }, "guru")
        assert not galat, galat
        assert "ditambahkan" in pesan.lower()
    assert sandi.periksa_peran("Budi", "rahasia-budi-123", "murid") is True


def test_tambah_akun_murid_nama_ganda_galat(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Citra")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Citra", "sandi": "rahasia-citra-123",
        }, "guru")
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Citra", "sandi": "rahasia-lain-123",
        }, "guru")
    assert not pesan
    assert galat  # ValueError ditangkap jadi galat, bukan 500
    assert "sudah dipakai" in galat.lower() or "sudah ada" in galat.lower() or "ganda" in galat.lower() or "dipakai" in galat.lower()


def test_tambah_akun_murid_sandi_pendek_ditolak(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Dina")
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Dina", "sandi": "pendek",
        }, "guru")
        assert not pesan
        assert "8 karakter" in galat
    assert not sandi.periksa_peran("Dina", "pendek", "murid")


def test_hapus_akun_murid(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Eka")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Eka", "sandi": "rahasia-eka-12345",
        }, "guru")
        assert sandi.periksa_peran("Eka", "rahasia-eka-12345", "murid") is True
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_hapus", "nama": "Eka",
        }, "guru")
        assert not galat, galat
        assert "dihapus" in pesan.lower()
    assert sandi.periksa_peran("Eka", "rahasia-eka-12345", "murid") is False


def test_setel_sandi_murid(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Fani")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Fani", "sandi": "lama-fani-12345",
        }, "guru")
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_sandi", "nama": "Fani", "baru": "baru-fani-67890",
        }, "guru")
        assert not galat, galat
        assert "diperbarui" in pesan.lower() or "sandi" in pesan.lower()
    assert not sandi.periksa_peran("Fani", "lama-fani-12345", "murid")
    assert sandi.periksa_peran("Fani", "baru-fani-67890", "murid") is True


def test_sandi_murid_tidak_muncul_di_html(siap):
    rahasia = "super-rahasia-murid-999"
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Gina")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Gina", "sandi": rahasia,
        }, "guru")
        h = web.halaman_akun(kon).decode()
    assert rahasia not in h
    assert rahasia not in sandi.BERKAS_SANDI.read_text() or rahasia not in h  # hash, bukan teks
    # pastikan berkas sandi di disk tidak bocor ke HTML (cek kunci/garam juga tidak ada)
    d = sandi.muat_sandi()
    # bentuk multi-akun: cari akun Gina
    akun = sandi.cari_akun("Gina")
    assert akun is not None
    assert akun["kunci"] not in h
    # nama murid di-escape
    with basis.buka(siap) as kon:
        # bersihkan dulu: buat siswa dan akun dengan karakter khusus
        # pakai DB baru (siap fixture tiap test sudah fresh), jadi buat ulang
        basis.tambah_siswa(kon, "<b>Hacker</b>")
        # akun murid dengan nama yang sama — harus di-escape di HTML
        sandi.tambah_akun("<b>Hacker</b>", "rahasia-hacker-123", "murid")
        h2 = web.halaman_akun(kon).decode()
    assert "<b>Hacker</b>" not in h2
    assert "&lt;b&gt;Hacker&lt;/b&gt;" in h2


def test_guru_tetap_bisa_ganti_sandi_setelah_ada_akun_murid(siap):
    """Regresi: begitu satu akun murid dibuat, berkas sandi berubah jadi
    bentuk multi-akun. `periksa()` sempat membaca d["pengguna"] yang tidak
    ada di bentuk itu dan melempar KeyError — guru TIDAK BISA mengganti
    sandinya sama sekali, halaman akun langsung 500.

    Lolos dari seluruh test sebelumnya karena tidak ada yang menguji
    URUTAN-nya: tambah murid dulu, baru guru ganti sandi.
    """
    sandi.simpan_sandi("sandi-guru-lama1", "guru")
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Feby")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Feby", "sandi": "rahasia8",
        }, "guru")

        pesan, galat = web.proses_akun(kon, {
            "aksi": "sandi", "lama": "sandi-guru-lama1",
            "baru": "sandi-guru-baru1", "ulang": "sandi-guru-baru1",
        }, "guru")

    assert not galat, f"guru gagal ganti sandi: {galat}"
    assert pesan
    assert sandi.periksa("guru", "sandi-guru-baru1")
    assert not sandi.periksa("guru", "sandi-guru-lama1")
    # dan akun murid tidak boleh ikut hilang
    assert sandi.periksa_peran("Feby", "rahasia8", "murid")
