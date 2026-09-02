"""Latar objek nyata untuk geometri-datar — gelombang 2, Langkah 3.

Lima dari dua belas template paket ini menulis bentuk geometri telanjang:
"Persegi panjang panjangnya N cm dan lebarnya N cm." Terukur 2 Sep 2026:
geometri-datar P4 hanya 11 bentuk kalimat, P5 dan P6 masing-masing 21 —
ketiganya di bawah ambang 25.

Kebijakan yang dipakai (dikonfirmasi pemilik produk): objek nyata BOLEH,
karena begitulah soal OSN sendiri ditulis — "sebuah kebun berbentuk
persegi panjang", bukan "persegi panjang". Bedanya dengan membungkus soal
hitung murni jadi cerita: di sini objeknya TIDAK menambah langkah baca,
ia hanya memberi nama pada bangun yang sudah ada di soal.

Yang TIDAK diberi objek dan alasannya ada di komentar modulnya.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import buat_lembar, buat_soal  # noqa: E402

BERLATAR = (
    "keliling_luas_datar",
    "luas_segitiga_jajargenjang",
    "jumlah_sudut_segitiga",
    "sudut_luar_segitiga",
)

LEVEL_UJI = {
    "sudut_luar_segitiga": "P5",
}


def _soal(template_id: str, seed: int, level: str | None = None):
    return buat_soal(
        template_id,
        seed,
        level=level or LEVEL_UJI.get(template_id, "P4"),
        topik="geometri-datar",
    )


def _pola(teks: str) -> str:
    return re.sub(r"-?\d+(?:[.,]\d+)?", "N", teks)


@pytest.mark.parametrize("template_id", BERLATAR)
def test_template_berlatar_punya_beberapa_bentuk_kalimat(template_id):
    """Satu template harus melahirkan lebih dari satu bunyi soal.

    Ambang 3, bukan angka persisnya: yang dikunci "tidak lagi satu
    kalimat mati", supaya membuang satu objek yang ternyata tidak sahih
    untuk anak SD tidak memecahkan test.
    """
    bentuk = {_pola(_soal(template_id, seed).teks) for seed in range(1, 200)}
    assert len(bentuk) >= 3, f"{template_id}: cuma {len(bentuk)} bentuk"


@pytest.mark.parametrize("template_id", BERLATAR)
def test_latar_deterministik_atas_parameter(template_id):
    """Latar HARUS turunan parameter, bukan rng atau hash() bawaan —
    mencetak ulang lembar lama dari bank soal harus memberi kalimat yang
    sama persis, kalau tidak guru menilai soal yang tidak dikerjakan."""
    from templates import REGISTRI

    fn = REGISTRI[template_id]
    for seed in range(1, 40):
        asli = _soal(template_id, seed)
        ulang = fn(**asli.parameter)
        assert ulang.teks == asli.teks, asli.parameter
        assert ulang.kunci == asli.kunci


@pytest.mark.parametrize("template_id", BERLATAR)
def test_latar_tidak_menambah_parameter(template_id):
    """Parameter ikut Soal.tanda_tangan: menambah kunci 'latar' akan
    membatalkan seluruh bank soal yang sudah tersimpan."""
    diharap = {
        "keliling_luas_datar": ({"varian", "p", "l"}, {"varian", "p", "K"}),
        "luas_segitiga_jajargenjang": ({"varian", "a", "t", "s"},),
        "jumlah_sudut_segitiga": None,
        "sudut_luar_segitiga": ({"a", "b"},),
    }[template_id]
    for seed in range(1, 60):
        p = set(_soal(template_id, seed).parameter)
        assert "latar" not in p and "objek" not in p, p
        if diharap is not None:
            assert p in diharap, p


@pytest.mark.parametrize("template_id", BERLATAR)
def test_latar_tidak_merusak_malrule(template_id):
    """Latar hanya mengganti kalimat. Kunci dan jalur K/H harus utuh."""
    for seed in range(1, 120):
        s = _soal(template_id, seed)
        assert s.malrule, f"{template_id}/{seed} malrule kosong"
        assert {"K", "H"} <= {m.kode for m in s.malrule}, f"{template_id}/{seed}"
        assert s.kunci not in [m.jawaban for m in s.malrule]


@pytest.mark.parametrize("template_id", BERLATAR)
def test_angka_soal_tetap_muncul_di_kalimat(template_id):
    """Latar tidak boleh menelan angka soalnya — soal yang kehilangan
    satu angka tidak bisa dikerjakan sama sekali."""
    for seed in range(1, 60):
        s = _soal(template_id, seed)
        for nama, nilai in s.parameter.items():
            if isinstance(nilai, int):
                assert str(nilai) in s.teks, f"{template_id}/{seed}: {nama}={nilai}"


def test_satuan_tetap_cm_dan_derajat():
    """Objek nyata tidak boleh mengubah satuan yang dipakai kunci.

    Kerusakan yang dicegah: "sebuah lapangan panjangnya 12 cm" janggal,
    tapi mengubahnya jadi meter membuat kunci (yang dihitung dari angka
    apa adanya) tidak lagi cocok dengan satuan di soal. Jadi objeknya
    yang harus dipilih seukuran cm — kertas, ubin, foto — bukan
    satuannya yang diubah.
    """
    besar = ("lapangan", "sawah", "kolam renang", "stadion", "kebun")
    for template_id in ("keliling_luas_datar", "luas_segitiga_jajargenjang"):
        for seed in range(1, 120):
            teks = _soal(template_id, seed).teks.lower()
            assert "cm" in teks
            for kata in besar:
                assert kata not in teks, f"{template_id}/{seed}: {kata} diukur cm"


def test_benda_tidak_bertentangan_dengan_bangunnya():
    """"Penggaris segitiga berbentuk jajargenjang" — kalimat yang
    bertentangan dengan dirinya sendiri.

    Lolos versi pertama karena satu daftar benda dipakai untuk DUA
    bentuk; ketahuan hanya dengan membaca keluaran nyatanya. Anak yang
    membaca soal seperti ini berhenti mempercayai soalnya.
    """
    for seed in range(1, 200):
        s = _soal("luas_segitiga_jajargenjang", seed)
        teks = s.teks.lower()
        if s.parameter["varian"] != "segitiga":
            assert "penggaris segitiga" not in teks, teks
            assert "rambu" not in teks, teks
        # bentuknya cuma boleh disebut sekali, tidak boleh dua-duanya
        assert not ("segitiga dengan" in teks and "jajargenjang" in teks), teks


@pytest.mark.parametrize("template_id", BERLATAR)
def test_kalimat_soal_bisa_dibaca(template_id):
    """Cegah kalimat gado-gado hasil menyisipkan latar ke tengah frasa.

    Dua kejanggalan nyata yang pernah lolos: "Keliling sebuah ubin lantai
    yang berbentuk persegi panjang 84 cm" (dari varian balik-arah) dan
    "Jarak kota Kota Delima" di paket lain. Keduanya hanya terlihat kalau
    keluarannya dibaca, jadi bentuk-bentuk itu dikunci di sini.
    """
    for seed in range(1, 120):
        teks = _soal(template_id, seed).teks
        assert "  " not in teks, teks
        assert " ." not in teks and " ?" not in teks, teks
        assert "berbentuk berbentuk" not in teks, teks
        # angka tidak boleh langsung menempel di belakang kata "panjang"
        # tanpa kata hubung — tanda frasa yang tersambung salah
        assert not re.search(r"persegi panjang \d", teks), teks
        assert teks[0].isupper(), teks
        assert teks.endswith("?"), teks


@pytest.mark.parametrize("level,baseline", (("P4", 11), ("P5", 21), ("P6", 21)))
def test_ambang_bentuk_kalimat_geometri_datar(level, baseline):
    """Pengunci ALASAN seluruh perubahan ini, bukan mekanismenya."""
    bentuk = set()
    for seed in range(300):
        for s in buat_lembar(seed, level=level, topik="geometri-datar").soal:
            bentuk.add(_pola(s.teks))
    assert len(bentuk) >= 25, (
        f"geometri-datar {level} cuma {len(bentuk)} bentuk kalimat "
        f"(baseline {baseline})"
    )
