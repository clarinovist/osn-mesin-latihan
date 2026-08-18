#!/usr/bin/env python3
"""Test tinta_heuristik.py — Rencana Spike Hari 4 (pagi).

Jalankan: ./.venv/bin/python tinta_heuristik_test.py

Nol panggilan API. Fixture dirancang per-sinyal supaya tiap aturan diuji
sendiri-sendiri, bukan lewat satu sesi gado-gado di mana kegagalan satu
aturan bisa tertutup aturan lain.
"""
import tinta_heuristik as th


def soal(
    jeda_ms=2000,
    durasi=(5000, 5000),
    hapus=(0, 0),
    jawaban_duluan=False,
    soal_id=1,
    jawaban="42",
):
    return {
        "soal_id": soal_id,
        "jawaban_diketik": jawaban,
        "jeda_sebelum_goresan_pertama_ms": jeda_ms,
        "durasi_per_langkah_ms": [
            {"indeks": i, "durasi_ms": d} for i, d in enumerate(durasi)
        ],
        "jumlah_hapus_per_langkah": [
            {"indeks": i, "jumlah": h} for i, h in enumerate(hapus)
        ],
        "jawaban_ditulis_sebelum_langkah_selesai": jawaban_duluan,
        "jawaban_ditulis_pada_ms": 9000,
        "selesai_ms": 10000,
    }


def tes_ekstrak_sinyal():
    s = th.ekstrak_sinyal(soal(jeda_ms=4000, durasi=(3000, 7000), hapus=(1, 2)))
    assert s["jeda_awal_ms"] == 4000, s
    assert s["jumlah_langkah"] == 2, s
    assert s["durasi_total_ms"] == 10000, s
    assert s["hapus_total"] == 3, s
    assert s["ada_goresan"] is True, s
    print("ekstrak_sinyal: PASS")


def tes_tahap_a_menang():
    """Kalau Tahap A sudah memutuskan, heuristik tidak boleh menimpanya."""
    d = th.diagnosa(soal(jeda_ms=20000), kode_tahap_a="H")
    assert d["kode"] == "H", d
    assert "Tahap A" in d["alasan"], d

    # 'benar' juga tidak boleh ditimpa.
    d = th.diagnosa(soal(), kode_tahap_a="benar")
    assert d["kode"] == "benar", d

    # Tapi 'tidak_pasti' dari Tahap A memang diserahkan ke sini.
    d = th.diagnosa(soal(jeda_ms=20000), kode_tahap_a="tidak_pasti")
    assert d["kode"] == "K", d
    assert "Tahap A" not in d["alasan"], d
    print("tahap A menang: PASS")


def tes_tanpa_goresan():
    """Tidak ada proses = tidak ada yang bisa dibaca. Jangan mengarang kode."""
    s = soal()
    s["jeda_sebelum_goresan_pertama_ms"] = None
    d = th.diagnosa(s)
    assert d["kode"] == "tidak_pasti", d
    assert d["keyakinan"] == "rendah", d
    print("tanpa goresan: PASS")


def tes_jawaban_duluan_dan_cepat():
    d = th.diagnosa(soal(durasi=(2000, 2000), jawaban_duluan=True))
    assert d["kode"] == "B", d
    assert "menebak" in d["alasan"], d
    print("jawaban duluan + cepat -> B: PASS")


def tes_jawaban_duluan_tapi_lama_bukan_B():
    """Menulis jawaban duluan tapi tetap mengerjakan lama bukan menebak.

    Batas ini penting: tanpa syarat durasi, anak yang mencatat dugaan lalu
    benar-benar mengerjakan akan salah dituduh menebak.
    """
    d = th.diagnosa(soal(durasi=(30000, 30000), jawaban_duluan=True, hapus=(2, 1)))
    assert d["kode"] != "B", d
    print("jawaban duluan tapi lama: PASS (tidak dituduh menebak)")


def tes_jeda_panjang():
    d = th.diagnosa(soal(jeda_ms=15000))
    assert d["kode"] == "K", d
    assert "tertahan" in d["alasan"], d
    print("jeda panjang -> K: PASS")


def tes_lancar_tapi_salah():
    d = th.diagnosa(soal(jeda_ms=1500, hapus=(0, 0)))
    assert d["kode"] == "K", d
    assert "lancar" in d["alasan"], d
    print("lancar tanpa hapus -> K: PASS")


def tes_banyak_koreksi():
    """Mulai wajar, banyak menghapus -> tersandung hitungan, bukan konsep.

    Ini garis pertahanan utama terhadap false-K: kasus H tidak boleh
    terbaca sebagai K.
    """
    d = th.diagnosa(soal(jeda_ms=5000, hapus=(2, 2)))
    assert d["kode"] == "H", f"koreksi berulang harus H, bukan K (false-K = kegagalan termahal): {d}"
    assert "mengoreksi" in d["alasan"], d
    print("banyak koreksi -> H: PASS")


def tes_sinyal_campur_menyerah():
    """Sinyal lemah harus menyerah, bukan menebak."""
    d = th.diagnosa(soal(jeda_ms=5000, hapus=(1, 0)))
    assert d["kode"] == "tidak_pasti", d
    assert d["keyakinan"] == "rendah", d
    print("sinyal campur -> tidak_pasti: PASS")


def tes_determinisme():
    """Input sama harus selalu memberi keluaran sama."""
    s = soal(jeda_ms=5000, hapus=(2, 1))
    hasil = [th.diagnosa(s) for _ in range(5)]
    assert all(h == hasil[0] for h in hasil), hasil
    print("determinisme: PASS")


def tes_jejak_versi():
    d = th.diagnosa(soal())
    assert d["aturan_versi"] == th.ATURAN_VERSI, d
    print("jejak versi: PASS")


def tes_sesi_penuh():
    """Sesi 10 soal: campuran sinyal, sebagian sudah diputuskan Tahap A."""
    turunan = {
        "sesi_id": "uji",
        "soal": [
            soal(soal_id=1, jeda_ms=1500, hapus=(0, 0)),
            soal(soal_id=2, jeda_ms=1000, hapus=(0, 0)),
            soal(soal_id=3, jeda_ms=12000),
            soal(soal_id=4, jeda_ms=5000, hapus=(3, 1)),
            soal(soal_id=5, durasi=(2000, 1500), jawaban_duluan=True),
            soal(soal_id=6, jeda_ms=5000, hapus=(1, 0)),
            soal(soal_id=8, jeda_ms=2000, hapus=(0, 0)),
            soal(soal_id=10, jeda_ms=9000),
            soal(soal_id=13, jeda_ms=5000, hapus=(2, 2)),
            soal(soal_id=15, jeda_ms=6000, hapus=(1, 0)),
        ],
    }
    # Tahap A sudah memutuskan sebagian.
    kode_a = {1: "K", 2: "K", 8: "benar"}
    hasil = th.diagnosa_sesi(turunan, kode_a)

    assert len(hasil) == 10, hasil
    assert all("soal_id" in h for h in hasil), hasil

    # Yang sudah diputuskan Tahap A harus lolos apa adanya.
    per_id = {h["soal_id"]: h for h in hasil}
    assert per_id[8]["kode"] == "benar", per_id[8]
    assert per_id[1]["kode"] == "K", per_id[1]

    hitung = th.ringkas(hasil)
    terjawab = sum(v for k, v in hitung.items() if k != "tidak_pasti")
    assert terjawab >= 7, f"baseline terlalu sering menyerah: {hitung}"
    print(f"sesi penuh: PASS ({hitung}, terjawab {terjawab}/10)")


def main():
    tes_ekstrak_sinyal()
    tes_tahap_a_menang()
    tes_tanpa_goresan()
    tes_jawaban_duluan_dan_cepat()
    tes_jawaban_duluan_tapi_lama_bukan_B()
    tes_jeda_panjang()
    tes_lancar_tapi_salah()
    tes_banyak_koreksi()
    tes_sinyal_campur_menyerah()
    tes_determinisme()
    tes_jejak_versi()
    tes_sesi_penuh()
    print("\nSemua test tinta_heuristik OK, nol panggilan API.")


if __name__ == "__main__":
    main()
