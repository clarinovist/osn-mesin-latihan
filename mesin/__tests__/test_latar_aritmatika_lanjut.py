"""Latar berputar untuk template yang kalimatnya mati — gelombang 2.

Terukur 2 Sep 2026, sesudah gelombang 1: 43 dari 85 template di SELURUH
aplikasi hanya melahirkan <= 2 bentuk kalimat, karena ceritanya ditulis
mati di dalam f-string. Aritmatika-lanjut menyumbang 8 dari 11
templatenya, dan seluruh delapan memang bercerita — jadi latar berputar
adalah obat yang tepat di sini (beda dari "hitung murni" seperti
`Berapa KPK dari 190 dan 108?`, yang justru dikaburkan oleh cerita).

Baseline yang diperbaiki paket ini:

    18 bentuk  aritmatika-lanjut P5
    22 bentuk  aritmatika-lanjut P6

Test di berkas ini mengunci ALASAN perubahan, bukan cuma "kode jalan":
ambang bentuk kalimat per level, jumlah cerita per template, dan tiga
kontrak `templates.putar` (deterministik atas parameter, bukan hash()
bawaan, tanpa parameter baru).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import buat_lembar, buat_soal  # noqa: E402

# Delapan template aritmatika-lanjut yang dulu punya satu kalimat mati.
# `persen_untung_rugi` punya dua (untung/rugi) tapi keduanya satu latar
# "sebuah barang"; ia ikut karena latar barangnya sendiri yang monoton.
BERLATAR = (
    "berpapasan",
    "kerja_bersama",
    "menyusul",
    "perbandingan_berbalik",
    "perbandingan_senilai",
    "persen_bertingkat",
    "persen_diskon",
    "persen_untung_rugi",
)

# Level tempat masing-masing template dipakai komposisi. Dipakai supaya
# sweep tidak meminta parameter level yang tidak menyediakannya.
LEVEL_UJI = {
    "berpapasan": "P6",
    "menyusul": "P6",
    "persen_untung_rugi": "P6",
    "persen_bertingkat": "P6",
}


def _pola(teks: str) -> str:
    """Metrik monoton: teks dengan seluruh angka dinormalkan jadi N."""
    return re.sub(r"-?\d+(?:[.,]\d+)?", "N", teks)


@pytest.mark.parametrize("template_id", BERLATAR)
def test_template_berlatar_punya_beberapa_cerita(template_id):
    """Satu template harus melahirkan lebih dari satu bentuk kalimat.

    Ambang 3 (bukan 5) dipilih supaya test tidak pecah kalau kelak satu
    latar dibuang karena tidak sahih untuk anak SD — yang dikunci adalah
    "tidak lagi satu kalimat mati", bukan jumlah persisnya.
    """
    level = LEVEL_UJI.get(template_id, "P5")
    bentuk = {
        _pola(
            buat_soal(
                template_id, seed, level=level, topik="aritmatika-lanjut"
            ).teks
        )
        for seed in range(1, 200)
    }
    assert len(bentuk) >= 3, f"{template_id}: cuma {len(bentuk)} cerita"


@pytest.mark.parametrize("template_id", BERLATAR)
def test_latar_deterministik_atas_parameter(template_id):
    """Latar HARUS turunan parameter, bukan rng atau hash() bawaan.

    Kalau tidak, mencetak ulang lembar lama dari bank soal (parameter
    sama, proses berbeda) melahirkan kalimat yang berbeda — guru menilai
    soal yang tidak dikerjakan anak.
    """
    from templates import REGISTRI

    fn = REGISTRI[template_id]
    level = LEVEL_UJI.get(template_id, "P5")
    for seed in range(1, 40):
        asli = buat_soal(template_id, seed, level=level, topik="aritmatika-lanjut")
        ulang = fn(**asli.parameter)
        assert ulang.teks == asli.teks, asli.parameter
        assert ulang.kunci == asli.kunci


def test_latar_tidak_menambah_parameter():
    """Parameter ikut Soal.tanda_tangan: menambah kunci 'latar' akan
    membatalkan seluruh bank soal yang sudah tersimpan."""
    for template_id, diharap in (
        ("berpapasan", {"jarak", "v1", "v2"}),
        ("menyusul", {"jarak", "v1", "v2"}),
        ("kerja_bersama", {"a", "b"}),
        ("perbandingan_senilai", {"p", "q", "n"}),
        ("perbandingan_berbalik", {"a1", "b1", "a2"}),
        ("persen_diskon", {"harga", "d"}),
        ("persen_untung_rugi", {"jenis", "modal", "persen"}),
        ("persen_bertingkat", {"harga", "d1", "d2"}),
    ):
        level = LEVEL_UJI.get(template_id, "P5")
        s = buat_soal(template_id, 5, level=level, topik="aritmatika-lanjut")
        assert set(s.parameter) == diharap, s.parameter


@pytest.mark.parametrize(
    "level,baseline", (("P5", 18), ("P6", 22))
)
def test_ambang_bentuk_kalimat_aritmatika_lanjut(level, baseline):
    """Pengunci ALASAN seluruh perubahan ini, bukan cuma mekanismenya.

    Ambang 25 adalah garis yang dipakai gelombang 1 untuk menyebut satu
    topik×level "tidak lagi monoton". Baseline sebelum latar berputar
    ditulis di parameter supaya kalau test ini gagal, angka lamanya
    terbaca langsung di pesan kegagalan.
    """
    bentuk = set()
    for seed in range(300):
        for s in buat_lembar(seed, level=level, topik="aritmatika-lanjut").soal:
            bentuk.add(_pola(s.teks))
    assert len(bentuk) >= 25, (
        f"aritmatika-lanjut {level} cuma {len(bentuk)} bentuk kalimat "
        f"(baseline {baseline})"
    )


@pytest.mark.parametrize("template_id", BERLATAR)
def test_latar_tidak_merusak_malrule(template_id):
    """Latar hanya mengganti kalimat. Kunci dan jalur diagnosis K/H harus
    utuh — kalau salah satu hilang, laporan guru kehilangan maknanya."""
    level = LEVEL_UJI.get(template_id, "P5")
    for seed in range(1, 120):
        s = buat_soal(template_id, seed, level=level, topik="aritmatika-lanjut")
        assert s.malrule, f"{template_id}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}/{seed}"
        assert s.kunci not in [m.jawaban for m in s.malrule]


@pytest.mark.parametrize("template_id", BERLATAR)
def test_angka_soal_tetap_muncul_di_kalimat(template_id):
    """Latar tidak boleh menelan angka soalnya.

    Kerusakan yang dicegah: latar yang menukar urutan kalimat pernah
    membuat satu parameter tidak lagi tertulis, sehingga soal tidak bisa
    dikerjakan sama sekali (angka yang diminta tidak ada di teks).
    """
    level = LEVEL_UJI.get(template_id, "P5")
    for seed in range(1, 60):
        s = buat_soal(template_id, seed, level=level, topik="aritmatika-lanjut")
        for nama, nilai in s.parameter.items():
            if isinstance(nilai, int):
                assert str(nilai) in s.teks, (
                    f"{template_id}/{seed}: {nama}={nilai} hilang dari teks"
                )


# ── Kesahihan latar ────────────────────────────────────────────────────
#
# Latar bukan hiasan bebas: ia membuat KLAIM tentang dunia. Dua klaim
# salah sempat lolos saat menulis paket ini dan dibuang setelah membaca
# keluaran nyatanya — keduanya dikunci di bawah supaya tidak kembali.


def test_latar_kecepatan_tidak_memakai_pelaku_lambat():
    """v ∈ 40..80 km/jam, jadi pelakunya harus kendaraan bermotor.

    Percobaan pertama memakai "Pelari"/"pesepeda" dan melahirkan
    "Pelari melaju 78 km/jam" — fakta yang salah. Soal yang faktanya
    keliru mengajari anak hal keliru, dan membuat guru meragukan seluruh
    lembar.
    """
    lambat = ("pelari", "pesepeda", "pejalan", "sepeda ontel", "becak")
    for template_id in ("berpapasan", "menyusul"):
        for seed in range(1, 120):
            teks = buat_soal(
                template_id, seed, level="P6", topik="aritmatika-lanjut"
            ).teks.lower()
            for kata in lambat:
                assert kata not in teks, f"{template_id}/{seed}: {kata}"


def test_nama_tempat_tidak_berulang_jenisnya():
    """"Jarak kota Kota Delima" — jenis tempat tertulis dua kali.

    Ketahuan hanya dengan MEMBACA keluaran nyatanya, bukan dari test yang
    ada: nama di `_RUTE` sudah memuat "Kota"/"Desa", jadi kalimatnya
    tidak boleh menambahkan kata itu lagi di depan. Anak membaca soal
    yang bahasanya janggal dan mulai meragukan soalnya, bukan jawabannya.
    """
    for template_id in ("berpapasan", "menyusul"):
        for seed in range(1, 120):
            teks = buat_soal(
                template_id, seed, level="P6", topik="aritmatika-lanjut"
            ).teks
            assert "kota Kota" not in teks, f"{template_id}/{seed}: {teks}"
            assert "kota Desa" not in teks, f"{template_id}/{seed}: {teks}"


def test_nama_kota_perjalanan_fiktif():
    """Jarak dihitung dari parameter (40–480 km), bukan dari peta.

    Memakai kota nyata berarti soal mengklaim jarak nyata yang sering
    salah ("Bogor–Sukabumi 480 km"). Nama fiktif menghindari klaim itu
    tanpa mengurangi satu pun bentuk kalimat.
    """
    nyata = (
        "bandung", "jakarta", "surabaya", "medan", "semarang",
        "solo", "malang", "bogor", "sukabumi", "cirebon",
    )
    for template_id in ("berpapasan", "menyusul"):
        for seed in range(1, 120):
            teks = buat_soal(
                template_id, seed, level="P6", topik="aritmatika-lanjut"
            ).teks.lower()
            for kota in nyata:
                assert kota not in teks, f"{template_id}/{seed}: {kota}"

