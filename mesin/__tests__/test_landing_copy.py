"""Narasi publik sesuai produk, tanpa janji pilot atau fitur yang belum dibuka."""
from html.parser import HTMLParser
import re

import pytest

from landing import halaman_landing
from subscription import DURASI_TRIAL, DURASI_KAMPANYE, harga


class _TeksPublik(HTMLParser):
    """Ambil teks terlihat, bukan nama kelas CSS atau skrip kerangka."""

    def __init__(self, sumber):
        super().__init__()
        self.lewati = False
        self.teks = []
        self.meta = {}
        self.feed(sumber)

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self.lewati = True
        if tag == "meta":
            atribut = dict(attrs)
            self.meta[atribut.get("property", atribut.get("name"))] = atribut.get("content", "")

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self.lewati = False

    def handle_data(self, data):
        if not self.lewati:
            self.teks.append(data)


@pytest.fixture
def publik():
    return _TeksPublik(halaman_landing().decode())


def _teks(publik):
    return " ".join(" ".join(publik.teks).split())


def test_tidak_merekrut_pilot_atau_menjanjikan_checkout(publik):
    teks = _teks(publik).lower()
    for lama in ("pilot", "10–20 keluarga", "testimoni", "harga belum diputuskan",
                 "coba gratis sekarang", "qris sudah tersedia"):
        assert lama not in teks
    assert "penawaran belum dibuka" in teks
    assert "tanggal pembukaan belum diumumkan" in teks
    assert "pendaftaran saat ini belum mengaktifkan masa coba atau promo" in teks
    assert "tidak memicu pembayaran" in teks


def test_penawaran_hero_tidak_menjanjikan_aktivasi_saat_daftar():
    sumber = halaman_landing().decode()
    hero = sumber.split('<div class="landing-hero-teks-st">', 1)[1].split('</div>', 1)[0]
    teks = _teks(_TeksPublik(hero)).lower()
    assert "rencana penawaran: coba gratis 30 hari" in teks
    assert "mulai rp15.000/bulan untuk 1 profil anak" in teks
    assert "3 periode berbayar pertama bagi peserta promo" in teks
    assert "penawaran belum dibuka; pendaftaran belum mengaktifkan masa coba atau promo" in teks


def test_rincian_harga_konsisten_dengan_domain():
    sumber = halaman_landing().decode()
    kartu = re.findall(
        r'<section class="landing-kartu-st landing-harga-kartu-st">(.*?)</section>',
        sumber, re.S,
    )
    assert len(kartu) == 3
    for jumlah, isi in enumerate(kartu, start=1):
        teks = _teks(_TeksPublik(isi))
        assert f"{jumlah} profil anak" in teks
        for label, periode in (("Promo", 0), ("Normal", 3)):
            nominal = harga(jumlah, peserta_promo=True, periode_dibayar=periode)
            rupiah = f"Rp{nominal:,}".replace(",", ".")
            assert f"{label} / bulan {rupiah}" in teks


def test_durasi_dan_syarat_promo_tidak_menyesatkan(publik):
    teks = _teks(publik).lower()
    assert f"coba gratis {DURASI_TRIAL // (24 * 60 * 60)} hari" in teks
    assert f"kampanye {DURASI_KAMPANYE // (7 * 24 * 60 * 60)} minggu sejak pembukaan" in teks
    for ketentuan in (
        "100 akun publik baru pertama yang memenuhi syarat",
        "3 periode yang dibayar , bukan 3 bulan sejak daftar",
        "jeda berlangganan tidak mengulang jatah promo",
        "akun lama tidak otomatis mendapat promo",
        "tanpa promo, harga normal berlaku setelah masa coba",
        "total untuk jumlah profil anak yang tercakup",
        "bukan harga per anak", "termasuk pajak bila berlaku",
    ):
        assert ketentuan in teks


def test_faq_biaya_sesuai_harga_dan_status_penawaran():
    sumber = halaman_landing().decode()
    faq = sumber.split('<summary>Bagaimana dengan biaya?</summary>', 1)[1].split('</details>', 1)[0]
    teks = _teks(_TeksPublik(faq)).lower()
    for frasa in ("coba gratis 30 hari", "3 periode berbayar pertama bagi peserta promo",
                  "rp15.000/bulan", "rp35.000/bulan", "penawaran belum dibuka",
                  "belum mengaktifkan masa coba atau promo", "tidak memicu pembayaran"):
        assert frasa in teks
    assert 'href="#harga"' in faq


def test_rencana_melampaui_diagnosis_dan_latihan_ulang(publik):
    teks = _teks(publik).lower()
    for bagian in ("pemetaan", "fokus", "contoh", "latihan terbimbing", "penguatan",
                   "cek berjeda", "cek berkala", "tinjau dan konfirmasi", "latihan manual"):
        assert bagian in teks
    assert "sistem mendiagnosis:" not in teks


def test_langkah_cara_kerja_tidak_memakai_teks_tebal_gelap():
    """CSS existing membuat b gelap dan memisahkannya sebagai item flex."""
    sumber = halaman_landing().decode()
    cara = sumber.split('<section class="landing-kartu-st landing-cara-st">', 1)[1]
    daftar = cara.split("<ol>", 1)[1].split("</ol>", 1)[0]
    assert "Tinjau dan konfirmasi" in daftar
    assert "<b>" not in daftar


def test_penguasaan_bukan_nilai_atau_klaim_seluruh_kurikulum(publik):
    teks = _teks(publik).lower()
    assert "peta penguasaan" in teks
    assert "bisa menjelaskan" in teks
    assert "bukan nilai rapor atau ukuran seluruh kurikulum" in teks


def test_contoh_tidak_memvonis_penyebab_atau_waktu_pemulihan(publik):
    teks = _teks(publik).lower()
    for lama in ("4–6 minggu", "2–3 minggu", "gejala terburu-buru", "caranya sudah benar"):
        assert lama not in teks
    assert "dugaan awal" in teks
    assert "bukan diagnosis dari jawaban akhir saja" in teks
    assert "473" in teks and "463" in teks


def test_pendamping_bersyarat_dan_bukan_pengganti_penilaian(publik):
    teks = _teks(publik).lower()
    assert "pendamping" in teks
    assert "bila fitur aktif dan kamu menyetujui" in teks
    assert "bukan penentu diagnosis atau pengganti tinjauanmu" in teks


def test_privasi_mengungkap_pengiriman_ai_dan_izin(publik):
    teks = _teks(publik).lower()
    assert "server pengelola" in teks
    assert "layanan ai pihak ketiga" in teks
    assert "foto lembar" in teks
    assert "izin orang tua/wali" in teks
    assert "persetujuan terpisah" in teks
    assert "bukan cloud pihak ketiga" not in teks


def test_deskripsi_share_mencerminkan_rencana_dan_penguasaan(publik):
    deskripsi = publik.meta["og:description"].lower()
    assert "rencana belajar" in deskripsi
    assert "peta penguasaan" in deskripsi
    assert "pilot" not in deskripsi
