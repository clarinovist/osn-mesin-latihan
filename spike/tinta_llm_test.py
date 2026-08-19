#!/usr/bin/env python3
"""Test tinta_llm.py — Rencana Spike Hari 4 (sore).

Jalankan: ./.venv/bin/python tinta_llm_test.py

NOL panggilan API sungguhan. Memakai klien palsu yang menghitung berapa kali
dipanggil — itulah cara membuktikan cache benar-benar bekerja, bukan sekadar
"kelihatannya cepat".
"""
import json
import shutil
import tempfile
from pathlib import Path

import tinta_llm as tl


class KlienPalsu:
    """Meniru Anthropic client. Mencatat jumlah panggilan."""

    def __init__(self, balasan=None, teks_mentah=None):
        self.panggilan = 0
        self.balasan = balasan or {
            "kode": "K",
            "keyakinan": "sedang",
            "bukti": "langkah kedua mengalikan penyebut secara terpisah",
            "diagnosis": "Anak menjumlahkan pecahan dengan cara yang belum tepat.",
            "topik": "pecahan",
            "terbaca": True,
        }
        self.teks_mentah = teks_mentah
        self.messages = self

    def create(self, **kwargs):
        self.panggilan += 1
        self.terakhir = kwargs
        teks = self.teks_mentah if self.teks_mentah is not None else json.dumps(self.balasan)

        class Blok:
            def __init__(self, t):
                self.type = "text"
                self.text = t

        class Resp:
            def __init__(self, t):
                self.content = [Blok(t)]

        return Resp(teks)


def soal_turunan(soal_id=2):
    return {
        "soal_id": soal_id,
        "jawaban_diketik": "4/5",
        "jeda_sebelum_goresan_pertama_ms": 3200,
        "durasi_per_langkah_ms": [
            {"indeks": 0, "durasi_ms": 8000},
            {"indeks": 1, "durasi_ms": 6000},
        ],
        "jumlah_hapus_per_langkah": [
            {"indeks": 0, "jumlah": 0},
            {"indeks": 1, "jumlah": 2},
        ],
        "jawaban_ditulis_sebelum_langkah_selesai": False,
        "jawaban_ditulis_pada_ms": 14000,
        "selesai_ms": 15000,
    }


def entri_template():
    return {
        "template_id": "pecahan_operasi_campuran",
        "soal_id": 2,
        "parameter": {"suku": [
            {"n": 2, "d": 3, "tanda": 1},
            {"n": 3, "d": 4, "tanda": 1},
            {"n": 1, "d": 2, "tanda": -1},
        ]},
        "jawaban_benar": "11/12",
        "malrule": [{
            "id": "pecahan.operasi_pembilang_penyebut_terpisah",
            "kode": "K",
            "alasan_singkat": "pembilang & penyebut dioperasikan sendiri-sendiri",
        }],
    }


def tes_susun_konteks():
    k = tl.susun_konteks(soal_turunan(), entri_template())
    assert "11/12" in k, k
    assert "4/5" in k, k
    assert "3.2 detik" in k, k
    assert "Total menghapus: 2" in k, k
    # Malrule + prediksinya ikut dikirim (Bagian 2, "Yang diterima tinta_llm").
    assert "pecahan.operasi_pembilang_penyebut_terpisah" in k, k
    assert 'memprediksi "4/5"' in k, k
    print("susun_konteks: PASS")


def tes_konteks_tanpa_malrule():
    """Soal tanpa malrule (mis. soal 8 dan 15) tidak boleh crash."""
    k = tl.susun_konteks(soal_turunan(8), {"soal_id": 8, "jawaban_benar": "126", "malrule": []})
    assert "126" in k, k
    assert "terdokumentasi" not in k, k
    print("konteks tanpa malrule: PASS")


def tes_validasi_menolak_yang_cacat():
    kasus = [
        ({"kode": "Z", "keyakinan": "tinggi", "bukti": "x", "diagnosis": "y", "topik": "z", "terbaca": True}, "kode"),
        ({"kode": "K", "keyakinan": "yakin", "bukti": "x", "diagnosis": "y", "topik": "z", "terbaca": True}, "keyakinan"),
        ({"kode": "K", "keyakinan": "tinggi", "bukti": "x", "diagnosis": "y", "topik": "z", "terbaca": "ya"}, "terbaca"),
        ({"kode": "K", "keyakinan": "tinggi", "bukti": "x", "diagnosis": "y"}, "topik"),
    ]
    for data, kolom in kasus:
        try:
            tl.validasi_hasil(data)
        except ValueError as e:
            assert kolom in str(e), f"pesan error tidak menyebut {kolom}: {e}"
        else:
            raise AssertionError(f"seharusnya ditolak: {data}")
    print("validasi menolak respons cacat: PASS")


def tes_cache_mencegah_panggilan_kedua(tmp):
    """Inti Hari 4: jalankan sekali, jalankan ulang, API tidak boleh dipanggil lagi."""
    klien = KlienPalsu()
    folder = tmp / "sesi"
    folder.mkdir(parents=True, exist_ok=True)

    h1 = tl.diagnosa_soal(soal_turunan(), entri_template(), folder, klien, cache_dir=tmp / "cache")
    assert klien.panggilan == 1, klien.panggilan
    assert h1["dari_cache"] is False, h1
    assert h1["kode"] == "K", h1
    assert h1["prompt_versi"] == tl.PROMPT_VERSI, h1
    assert h1["model"] == tl.MODEL, h1

    h2 = tl.diagnosa_soal(soal_turunan(), entri_template(), folder, klien, cache_dir=tmp / "cache")
    assert klien.panggilan == 1, f"cache tidak dipakai, API dipanggil {klien.panggilan}x"
    assert h2["dari_cache"] is True, h2
    assert h2["kode"] == h1["kode"], (h1, h2)
    print("cache mencegah panggilan kedua: PASS")


def tes_cache_tanpa_klien(tmp):
    """Setelah tersimpan, hasil harus terbaca walau tidak ada klien sama sekali."""
    folder = tmp / "sesi"
    h = tl.diagnosa_soal(soal_turunan(), entri_template(), folder, None, cache_dir=tmp / "cache")
    assert h["dari_cache"] is True, h
    print("cache terbaca tanpa klien: PASS")


def tes_tanpa_cache_tanpa_klien_gagal_jelas(tmp):
    folder = tmp / "sesi"
    try:
        tl.diagnosa_soal(soal_turunan(99), {"soal_id": 99}, folder, None, cache_dir=tmp / "cache")
    except RuntimeError as e:
        assert "ANTHROPIC_API_KEY" in str(e), e
    else:
        raise AssertionError("seharusnya gagal dengan pesan jelas")
    print("tanpa cache tanpa klien -> error jelas: PASS")


def tes_prompt_versi_membatalkan_cache(tmp):
    """Ganti prompt_versi = entri cache lama tidak boleh dipakai.

    Ini yang membuat 'maksimal 3 putaran perbaikan prompt' bisa dihitung:
    tiap putaran benar-benar memanggil ulang, bukan membaca hasil lama.
    """
    klien = KlienPalsu()
    folder = tmp / "sesi"
    tl.diagnosa_soal(soal_turunan(), entri_template(), folder, klien, cache_dir=tmp / "cache2")
    assert klien.panggilan == 1

    asli = tl.PROMPT_VERSI
    tl.PROMPT_VERSI = "tinta-llm-v2"
    try:
        h = tl.diagnosa_soal(soal_turunan(), entri_template(), folder, klien, cache_dir=tmp / "cache2")
        assert klien.panggilan == 2, "prompt_versi baru harus memanggil ulang API"
        assert h["prompt_versi"] == "tinta-llm-v2", h
    finally:
        tl.PROMPT_VERSI = asli
    print("prompt_versi membatalkan cache: PASS")


def tes_data_beda_kunci_beda(tmp):
    """Ringkasan waktu berbeda harus menghasilkan kunci cache berbeda."""
    a = tl.kunci_cache(2, tl.susun_konteks(soal_turunan(), entri_template()), [])
    lain = soal_turunan()
    lain["jeda_sebelum_goresan_pertama_ms"] = 15000
    b = tl.kunci_cache(2, tl.susun_konteks(lain, entri_template()), [])
    assert a != b, "data berbeda tidak boleh berbagi entri cache"

    # Gambar berbeda juga harus memisahkan kunci.
    c = tl.kunci_cache(2, tl.susun_konteks(soal_turunan(), entri_template()), [b"png-a"])
    d = tl.kunci_cache(2, tl.susun_konteks(soal_turunan(), entri_template()), [b"png-b"])
    assert c != d, "coretan berbeda tidak boleh berbagi entri cache"
    print("data beda -> kunci beda: PASS")


def tes_respons_terbungkus_markdown(tmp):
    """Model kadang membungkus JSON dalam ```json — harus tetap terbaca."""
    balasan = {
        "kode": "H", "keyakinan": "tinggi", "bukti": "b",
        "diagnosis": "d", "topik": "t", "terbaca": True,
    }
    klien = KlienPalsu(teks_mentah="```json\n" + json.dumps(balasan) + "\n```")
    h = tl.diagnosa_soal(soal_turunan(3), entri_template(), tmp / "sesi", klien, cache_dir=tmp / "cache3")
    assert h["kode"] == "H", h
    print("respons terbungkus markdown: PASS")


def tes_terbaca_false_dihormati(tmp):
    """Model boleh menyerah — dan itu harus lolos validasi, bukan ditolak."""
    klien = KlienPalsu(balasan={
        "kode": "K", "keyakinan": "rendah", "bukti": "coretan tidak terbaca",
        "diagnosis": "Tulisannya tidak cukup jelas untuk disimpulkan.",
        "topik": "tidak diketahui", "terbaca": False,
    })
    h = tl.diagnosa_soal(soal_turunan(4), entri_template(), tmp / "sesi", klien, cache_dir=tmp / "cache4")
    assert h["terbaca"] is False, h
    assert h["keyakinan"] == "rendah", h
    print("terbaca=false dihormati: PASS")


def tes_palang_izin_menahan_secara_default():
    """Tanpa izin eksplisit, klien tidak boleh terbentuk — walau API key ada.

    Ini penjaga PRD §7.1. Dua syarat sengaja dipisah: kunci API bisa saja
    sudah ada di environment untuk keperluan lain, dan kealpaan seperti itu
    tidak boleh berujung terkirimnya tulisan tangan anak ke pihak ketiga.
    """
    import os

    asli_izin = os.environ.pop("OSN_IZIN_KIRIM_DATA_ANAK", None)
    asli_key = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "sk-palsu-untuk-test"
    try:
        try:
            tl.buat_klien()
        except SystemExit as e:
            assert "§7.1" in str(e), e
            assert "--dry-run" in str(e), e
        else:
            raise AssertionError("palang izin tidak menahan — data anak bisa terkirim tanpa keputusan sadar")

        # Dengan izin eksplisit, palang membuka (kunci palsu -> klien tetap terbentuk).
        os.environ["OSN_IZIN_KIRIM_DATA_ANAK"] = "1"
        klien = tl.buat_klien()
        assert klien is not None, "izin diberikan tapi klien tidak terbentuk"
    finally:
        os.environ.pop("OSN_IZIN_KIRIM_DATA_ANAK", None)
        if asli_izin is not None:
            os.environ["OSN_IZIN_KIRIM_DATA_ANAK"] = asli_izin
        if asli_key is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = asli_key
    print("palang izin menahan secara default: PASS")


def main():
    tes_susun_konteks()
    tes_konteks_tanpa_malrule()
    tes_validasi_menolak_yang_cacat()
    tes_palang_izin_menahan_secara_default()

    tmp = Path(tempfile.mkdtemp(prefix="spike-llm-test-"))
    try:
        tes_cache_mencegah_panggilan_kedua(tmp)
        tes_cache_tanpa_klien(tmp)
        tes_tanpa_cache_tanpa_klien_gagal_jelas(tmp)
        tes_prompt_versi_membatalkan_cache(tmp)
        tes_data_beda_kunci_beda(tmp)
        tes_respons_terbungkus_markdown(tmp)
        tes_terbaca_false_dihormati(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nSemua test tinta_llm OK, nol panggilan API sungguhan.")


if __name__ == "__main__":
    main()
