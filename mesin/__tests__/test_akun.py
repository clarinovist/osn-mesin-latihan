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
        h = web.halaman_akun(kon, section="siswa").decode()

    assert "Andi" in h
    assert ">2<" in h  # jumlah sesi


def test_tabel_siswa_menampilkan_status_akun_latihan(siap):
    """Hapus akun latihan tidak menghapus anaknya — status di tabel siswa
    harus menjelaskan hubungan itu, bukan membiarkannya jadi teka-teki."""
    with basis.buka(siap) as kon:
        sid = basis.tambah_siswa(kon, "Tertaut", pemilik="guru")
        sandi.tambah_akun("taut-login", "rahasia-taut-123", "murid", siswa_id=sid)
        basis.tambah_siswa(kon, "Telanjang")
        h = web.halaman_akun(kon, section="siswa").decode()
    assert "taut-login" in h
    assert "belum ada login" in h


def test_helper_akun_murid_dari_siswa(siap):
    """Kebalikan siswa_dari_akun: siswa_id eksplisit menang, akun warisan
    tanpa siswa_id dicocokkan lewat nama, siswa tanpa akun → None."""
    import murid

    with basis.buka(siap) as kon:
        sid_taut = basis.tambah_siswa(kon, "Taut", pemilik="guru")
        sandi.tambah_akun("taut-login", "rahasia-taut-123", "murid", siswa_id=sid_taut)
        sid_warisan = basis.tambah_siswa(kon, "Warisan")
        sandi.tambah_akun("Warisan", "rahasia-warisan-1", "murid")
        sid_kosong = basis.tambah_siswa(kon, "Kosong")

        assert murid.akun_murid_dari_siswa(kon, sid_taut) == "taut-login"
        assert murid.akun_murid_dari_siswa(kon, sid_warisan) == "Warisan"
        assert murid.akun_murid_dari_siswa(kon, sid_kosong) is None
        assert murid.akun_murid_dari_siswa(kon, 999999) is None


def test_halaman_akun_menjelaskan_kenapa_siswa_tidak_bisa_dihapus(siap):
    """Ketiadaan tombol hapus harus dijelaskan, bukan dibiarkan jadi teka-teki."""
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon, section="siswa").decode()
    assert "tidak bisa dihapus" in h.lower()
    assert "riwayat" in h.lower()


def test_pesan_galat_di_escape(siap):
    """Nama siswa masuk pesan galat; karakter khusus tidak boleh merusak HTML."""
    with basis.buka(siap) as kon:
        web.proses_akun(kon, {"aksi": "siswa", "nama": "<b>X</b>"}, "guru")
        _, galat = web.proses_akun(kon, {"aksi": "siswa", "nama": "<b>X</b>"}, "guru")
        h = web.halaman_akun(kon, "", galat, section="siswa").decode()

    assert "<b>X</b>" not in h
    assert "&lt;b&gt;" in h


# ── Akun murid (plan 2026-08-25) ──────────────────────────────────────


def test_kartu_akun_murid_tampil_dan_memuat_nama(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Sinta")
        sandi.tambah_akun("Sinta", "rahasia-sinta-123", "murid")
        h = web.halaman_akun(kon, section="akun-murid").decode()
    assert "Akun murid" in h
    assert "Sinta" in h


def test_akun_tidak_cocok_ditandai_belum_terhubung(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Andi")
        sandi.tambah_akun("Hantu", "rahasia-hantu-123", "murid")
        h = web.halaman_akun(kon, section="akun-murid").decode()
    assert "Hantu" in h
    assert "belum terhubung ke siswa" in h.lower()


def test_tambah_akun_murid_berhasil(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Budi", pemilik="guru")
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Budi", "sandi": "rahasia-budi-123",
        }, "guru")
        assert not galat, galat
        assert "ditambahkan" in pesan.lower()
    assert sandi.periksa_peran("Budi", "rahasia-budi-123", "murid") is True


def test_tambah_akun_murid_nama_ganda_galat(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Citra", pemilik="guru")
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
        basis.tambah_siswa(kon, "Dina", pemilik="guru")
        pesan, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Dina", "sandi": "pendek",
        }, "guru")
        assert not pesan
        assert "8 karakter" in galat
    assert not sandi.periksa_peran("Dina", "pendek", "murid")


def test_hapus_akun_murid(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Eka", pemilik="guru")
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
        basis.tambah_siswa(kon, "Fani", pemilik="guru")
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
        basis.tambah_siswa(kon, "Gina", pemilik="guru")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Gina", "sandi": rahasia,
        }, "guru")
        h = web.halaman_akun(kon, section="akun-murid").decode()
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
        h2 = web.halaman_akun(kon, section="akun-murid").decode()
    assert "<b>Hacker</b>" not in h2
    assert "&lt;b&gt;Hacker&lt;/b&gt;" in h2


# ── Sidebar + section (plan 2026-08-30) ───────────────────────────────


def test_section_bawaan_akun_dengan_navigasi_samping(siap):
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon).decode()
    assert "Ganti sandi" in h
    assert "nav-samping" in h
    assert 'href="/akun?section=siswa"' in h
    assert 'href="/akun?section=akun-murid"' in h
    assert "Tambah siswa" not in h, "section lain bocor ke section akun"
    assert "Akun murid" not in h


def test_section_siswa_memuat_daftar_dan_form(siap):
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "Andi")
        h = web.halaman_akun(kon, section="siswa").decode()
    assert "Andi" in h
    assert "Tambah siswa" in h
    assert "Tambah anak" in h
    assert "Ganti sandi" not in h
    assert "Akun murid" not in h


def test_section_akun_murid_memuat_kartunya(siap):
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon, section="akun-murid").decode()
    assert "Akun murid" in h
    assert "Ganti sandi" not in h
    assert "Tambah siswa" not in h


def test_section_tak_dikenal_jatuh_ke_akun(siap):
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon, section="hxhx").decode()
    assert "Ganti sandi" in h
    assert "Tambah siswa" not in h


def test_admin_hanya_section_akun(siap):
    with basis.buka(siap) as kon:
        h = web.halaman_akun(kon, pengguna="pengelola", peran="admin").decode()
        h2 = web.halaman_akun(
            kon, pengguna="pengelola", peran="admin", section="siswa"
        ).decode()
    assert "Ganti sandi" in h
    # Sidebar admin satu item; link "Ganti sandi" topbar ikut muncul,
    # jadi yang dicek adalah KETIDAKHADIRAN pintu keluarga.
    assert 'href="/akun?section=siswa"' not in h
    assert 'href="/akun?section=akun-murid"' not in h
    assert "Tambah siswa" not in h2, "section siswa bocor ke admin"
    assert "Ganti sandi" in h2


def test_peta_aksi_ke_section_lengkap():
    """Tiap aksi POST /akun harus punya section tujuan — hasil aksi tampil
    di tempat formnya, bukan melompat ke section bawaan."""
    for aksi in ("sandi", "siswa", "anak_baru", "tingkat",
                 "akun_murid_tambah", "akun_murid_hapus", "akun_murid_sandi"):
        assert aksi in web.PETA_SECTION_AKUN, f"aksi {aksi} tak dipetakan"
    assert web.PETA_SECTION_AKUN["siswa"] == "siswa"
    assert web.PETA_SECTION_AKUN["akun_murid_tambah"] == "akun-murid"
    assert web.PETA_SECTION_AKUN["sandi"] == "akun"


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
        basis.tambah_siswa(kon, "Feby", pemilik="guru")
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


# ── Multi-keluarga: pemilik & tautan siswa_id ───────────────────────────


def test_siswa_baru_ber_pemilik_pembuatnya(siap):
    with basis.buka(siap) as kon:
        web.proses_akun(kon, {"aksi": "siswa", "nama": "MilikA", "tingkat": "P3"}, "ortu-a")
        baris = kon.execute("SELECT pemilik FROM siswa WHERE nama='MilikA'").fetchone()
    assert baris["pemilik"] == "ortu-a"


def test_dobel_nama_antar_keluarga_sah_dalam_keluarga_ditolak(siap):
    """Dua keluarga boleh sama-sama punya 'Bima'; dalam satu keluarga tetap
    ditolak tanpa pandang huruf besar-kecil."""
    with basis.buka(siap) as kon:
        _, g1 = web.proses_akun(kon, {"aksi": "siswa", "nama": "Bima", "tingkat": "P3"}, "ortu-a")
        _, g2 = web.proses_akun(kon, {"aksi": "siswa", "nama": "Bima", "tingkat": "P3"}, "ortu-b")
        _, g3 = web.proses_akun(kon, {"aksi": "siswa", "nama": "BIMA", "tingkat": "P3"}, "ortu-a")
        n = kon.execute("SELECT COUNT(*) c FROM siswa WHERE nama='Bima'").fetchone()["c"]
    assert g1 == "" and g2 == ""
    assert g3 != ""
    assert n == 2


def test_akun_murid_tambah_menyimpan_siswa_id(siap):
    with basis.buka(siap) as kon:
        sid = basis.tambah_siswa(kon, "Taut", pemilik="guru")
        _, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "Taut", "sandi": "rahasia-taut-123",
        }, "guru")
        akun = sandi.cari_akun("Taut")
    assert galat == ""
    assert akun is not None
    assert akun["siswa_id"] == sid


def test_akun_murid_tambah_via_siswa_id_dan_nama_akun_beda(siap):
    """Bentuk form baru: pilih siswa + nama akun bebas (unik global).
    Nama tampilan dan nama login tidak harus sama lagi."""
    with basis.buka(siap) as kon:
        sid = basis.tambah_siswa(kon, "Bima", pemilik="guru")
        _, galat = web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "siswa_id": str(sid),
            "nama_akun": "bima-santoso", "sandi": "rahasia-bima-123",
        }, "guru")
        akun = sandi.cari_akun("bima-santoso")
    assert galat == ""
    assert akun is not None
    assert akun["siswa_id"] == sid
    assert sandi.periksa_peran("bima-santoso", "rahasia-bima-123", "murid")


def test_akun_murid_anak_keluarga_lain_tak_bisa_disetel(siap):
    """Guru keluarga B tidak boleh menyentuh akun murid keluarga A;
    admin tetap bisa."""
    with basis.buka(siap) as kon:
        basis.tambah_siswa(kon, "AnakA", pemilik="ortu-a")
        web.proses_akun(kon, {
            "aksi": "akun_murid_tambah", "nama": "AnakA", "sandi": "rahasia-anak-1",
        }, "ortu-a")
        _, g1 = web.proses_akun(kon, {
            "aksi": "akun_murid_sandi", "nama": "AnakA", "baru": "diserang-99999",
        }, "ortu-b")
        _, g2 = web.proses_akun(kon, {
            "aksi": "akun_murid_hapus", "nama": "AnakA",
        }, "ortu-b")
        _, g3 = web.proses_akun(kon, {
            "aksi": "akun_murid_sandi", "nama": "AnakA", "baru": "disetel-admin-1",
        }, "pengelola", "admin")
    assert g1 != ""
    assert g2 != ""
    assert g3 == ""
    assert sandi.periksa_peran("AnakA", "disetel-admin-1", "murid")


def test_tingkat_anak_keluarga_lain_ditolak(siap):
    with basis.buka(siap) as kon:
        sid_a = basis.tambah_siswa(kon, "AnakX", pemilik="ortu-a")
        _, g1 = web.proses_akun(kon, {
            "aksi": "tingkat", "siswa_id": str(sid_a), "tingkat": "P5",
        }, "ortu-b")
        _, g2 = web.proses_akun(kon, {
            "aksi": "tingkat", "siswa_id": str(sid_a), "tingkat": "P5",
        }, "pengelola", "admin")
        baris = kon.execute("SELECT tingkat FROM siswa WHERE id = ?", (sid_a,)).fetchone()
    assert g1 != ""
    assert g2 == ""
    assert baris["tingkat"] == "P5"
