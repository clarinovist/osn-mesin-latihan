"""Verifikasi halaman guru — terutama rekonstruksi soal dari basis data.

Titik paling rapuh di lapisan ini: teks soal TIDAK disimpan, hanya
parameternya. Halaman guru membangun ulang soalnya lewat REGISTRI. Kalau
rekonstruksi meleset, guru menilai jawaban terhadap soal yang salah — dan
kesalahan itu senyap, karena halamannya tetap tampil normal.

Parameter bertipe tuple (pola siklus) melewati JSON sebagai string, jadi
harus dikembalikan ke bentuk semula. Itu yang paling mudah salah.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import web  # noqa: E402
from generator import buat_lembar  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    return p


# ── Rekonstruksi soal ───────────────────────────────────────────────────


@pytest.mark.parametrize("seed", [1, 12, 77, 404, 2026])
def test_soal_dibangun_ulang_persis_sama(db, seed):
    """Soal hasil rekonstruksi harus identik dengan yang dicetak di kertas.

    Kalau berbeda, guru membaca soal yang tidak dikerjakan anak.
    """
    asli = buat_lembar(seed).soal
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Rekon")
        sesi_id = basis.buat_sesi(kon, sid, seed=seed)
        for a, b in zip(asli, basis.isi_sesi(kon, sesi_id)):
            ulang = web._soal_dari_baris(b)
            assert ulang.teks == a.teks, f"teks {a.template_id} berbeda"
            assert ulang.kunci == a.kunci
            assert ulang.minta_restatement == a.minta_restatement
            assert ulang.tanda_tangan == a.tanda_tangan


def test_pola_siklus_terrestorasi_tanpa_konversi_khusus(db):
    """Soal siklus direstorasi dari bank tanpa konversi apa pun: parameter
    tersimpan JSON murni (A4) dan template menerima bentuk itu langsung."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Tuple")
        sesi_id = basis.buat_sesi(kon, sid, seed=88)
        for b in basis.isi_sesi(kon, sesi_id):
            if b["template_id"] in ("siklus_huruf", "siklus_warna", "jumlah_siklus"):
                s = web._soal_dari_baris(b)
                assert s.kunci == b["kunci"]


# ── Alur simpan + diagnosis ─────────────────────────────────────────────


def _isi(kon, sesi_id, jawaban_per_nomor, extra=None):
    data = {}
    for b in basis.isi_sesi(kon, sesi_id):
        n = b["nomor"]
        if n in jawaban_per_nomor:
            data[f"jwb_{b['sesi_soal_id']}"] = jawaban_per_nomor[n]
            data[f"cara_{b['sesi_soal_id']}"] = "ada coretan"
        if extra:
            for k, v in extra.get(n, {}).items():
                data[f"{k}_{b['sesi_soal_id']}"] = v
    return data


def test_jawaban_benar_tercatat_benar(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Benar")
        sesi_id = basis.buat_sesi(kon, sid, seed=5)
        isi = basis.isi_sesi(kon, sesi_id)
        data = _isi(kon, sesi_id, {b["nomor"]: b["kunci"] for b in isi})

        web.simpan_sesi(kon, sesi_id, data)
        r = basis.ringkasan(kon, sid)[0]

    assert r["benar"] == 12


def test_malrule_menghasilkan_kode_otomatis(db):
    """Inti penghematan waktu guru: kode muncul tanpa diketik."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Auto")
        sesi_id = basis.buat_sesi(kon, sid, seed=6)

        jawaban, harapan = {}, {}
        for b in basis.isi_sesi(kon, sesi_id):
            mal = basis.malrule_soal(kon, b["soal_id"])
            if mal:
                jawaban[b["nomor"]] = mal[0]["jawaban"]
                harapan[b["nomor"]] = mal[0]["kode"]

        web.simpan_sesi(kon, sesi_id, _isi(kon, sesi_id, jawaban))

        for b in basis.isi_sesi(kon, sesi_id):
            if b["nomor"] in harapan:
                assert b["kode_final"] == harapan[b["nomor"]], (
                    f"soal {b['nomor']} ({b['template_id']}): "
                    f"kode {b['kode_final']} != {harapan[b['nomor']]}"
                )


def test_guru_bisa_menimpa_usulan_mesin(db):
    """Guru melihat coretan; mesin tidak. Keputusan guru harus menang."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Timpa")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        b = basis.isi_sesi(kon, sesi_id)[0]
        mal = basis.malrule_soal(kon, b["soal_id"])

        data = {
            f"jwb_{b['sesi_soal_id']}": mal[0]["jawaban"],
            f"cara_{b['sesi_soal_id']}": "coretan",
            f"kode_{b['sesi_soal_id']}": "E",  # guru memutuskan lain
        }
        web.simpan_sesi(kon, sesi_id, data)
        hasil = basis.isi_sesi(kon, sesi_id)[0]

    assert hasil["kode_final"] == "E"
    assert hasil["kode_usulan"] == mal[0]["kode"]  # usulan mesin tetap tersimpan
    assert hasil["manual"] == 1


def test_guru_bisa_menandai_benar_walau_mesin_bilang_salah(db):
    """Anak bisa benar dengan cara tak terduga; mesin tidak boleh memaksa."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Sah")
        sesi_id = basis.buat_sesi(kon, sid, seed=8)
        b = basis.isi_sesi(kon, sesi_id)[0]
        data = {
            f"jwb_{b['sesi_soal_id']}": "bentuk lain",
            f"cara_{b['sesi_soal_id']}": "cara alternatif",
            f"kode_{b['sesi_soal_id']}": "benar",
        }
        web.simpan_sesi(kon, sesi_id, data)
        hasil = basis.isi_sesi(kon, sesi_id)[0]

    assert hasil["benar"] == 1
    assert hasil["kode_final"] is None


def test_soal_dilewati_tidak_membuat_baris_kosong(db):
    """Guru sering mengisi sebagian dulu; sisanya tidak boleh tercatat
    sebagai 'sudah dinilai' dengan data kosong."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Sebagian")
        sesi_id = basis.buat_sesi(kon, sid, seed=9)
        isi = basis.isi_sesi(kon, sesi_id)
        data = {
            f"jwb_{isi[0]['sesi_soal_id']}": isi[0]["kunci"],
            f"cara_{isi[0]['sesi_soal_id']}": "coretan",
        }
        web.simpan_sesi(kon, sesi_id, data)
        n = kon.execute("SELECT COUNT(*) AS n FROM jawaban").fetchone()["n"]

    assert n == 1


def test_centang_belum_pernah_lihat_jadi_kode_t(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Tidak")
        sesi_id = basis.buat_sesi(kon, sid, seed=10)
        b = basis.isi_sesi(kon, sesi_id)[-1]
        web.simpan_sesi(kon, sesi_id, {f"belum_{b['sesi_soal_id']}": "on"})
        hasil = basis.isi_sesi(kon, sesi_id)[-1]

    assert hasil["kode_final"] == "T"


# ── Halaman tampil ──────────────────────────────────────────────────────


def test_halaman_utama_menampilkan_siswa(db):
    with basis.buka(db) as kon:
        basis.tambah_siswa(kon, "Andi")
        basis.tambah_siswa(kon, "Bila")
        h = web.halaman_utama(kon).decode()
    assert "Andi" in h
    assert "Bila" in h


def test_halaman_sesi_menampilkan_kunci_untuk_guru(db):
    """Kebalikan lembar anak: guru justru harus melihat kuncinya."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Lihat")
        sesi_id = basis.buat_sesi(kon, sid, seed=13)
        isi = basis.isi_sesi(kon, sesi_id)
        h = web.halaman_sesi(kon, sesi_id).decode()
    for b in isi:
        assert b["kunci"] in h


def test_laporan_menonjolkan_k_bukan_skor(db):
    """Metrik utama proyek ini jumlah K, dan halamannya harus mengatakan itu
    dengan jelas — guru secara naluriah menghitung jawaban benar."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Lapor")
        basis.buat_sesi(kon, sid, seed=14)
        h = web.halaman_laporan(kon, sid).decode()
    assert "jumlah <b>K</b>" in h or "jumlah K" in h
    assert "bukan skor" in h.lower()


def test_halaman_tidak_error_saat_sesi_kosong(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Kosong")
        h = web.halaman_laporan(kon, sid).decode()
    assert "belum ada" in h.lower()


def test_nama_siswa_di_html_di_escape(db):
    """Nama anak masuk HTML; karakter khusus tidak boleh merusak halaman."""
    with basis.buka(db) as kon:
        basis.tambah_siswa(kon, "A<script>x</script>")
        h = web.halaman_utama(kon).decode()
    assert "<script>x</script>" not in h
    assert "&lt;script&gt;" in h


# ── Dashboard: skor, mode, durasi, tanpa kolom lembar ───────────────────


def test_dashboard_menampilkan_skor_benar(db):
    """Kolom Benar = jumlah soal terdiagnosis benar / total soal sesi.

    Skenarionya sengaja dibuat beda dari kolom Terisi (3 terisi, 2 benar)
    supaya angka yang ditemukan benar-benar kolom Benar, bukan Terisi.
    """
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Skor")
        sesi_id = basis.buat_sesi(kon, sid, seed=5)
        isi = basis.isi_sesi(kon, sesi_id)
        data = _isi(
            kon, sesi_id,
            {1: isi[0]["kunci"], 2: isi[1]["kunci"], 3: "pasti salah"},
            {3: {"kode": "H"}},  # guru paksa salah hitung
        )
        web.simpan_sesi(kon, sesi_id, data)
        h = web.halaman_utama(kon).decode()
    assert ">3/12<" in h, "Terisi harus 3/12"
    assert ">2/12<" in h, "Benar harus 2/12"


def test_dashboard_tanpa_kolom_lembar(db):
    """Lembar soal/kunci cukup satu pintu: dari halaman sesi. Dashboard
    yang menampilkan keduanya terasa redundant."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Lembar")
        sesi_id = basis.buat_sesi(kon, sid, seed=5)
        h = web.halaman_utama(kon).decode()
        hs = web.halaman_sesi(kon, sesi_id).decode()
    assert 'href="/lembar/' not in h
    assert 'href="/lembar/' in hs


def test_dashboard_badge_mode_hanya_untuk_drill(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "ModeDrill")
        basis.buat_sesi(kon, sid, seed=5, mode="drill")
        basis.buat_sesi(kon, sid, seed=6)  # diagnostik
        h = web.halaman_utama(kon).decode()
    assert h.count('class="badge-mode"') == 1


def test_dashboard_menampilkan_durasi_sesi_selesai(db):
    """Waktu = selesai − mulai (mm:ss), hanya bila keduanya tercatat."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Durasi")
        basis.buat_sesi(kon, sid, seed=5)
        kon.execute(
            "UPDATE sesi SET mulai = '2026-08-30 10:00:00', "
            "selesai = '2026-08-30 10:12:30'"
        )
        h = web.halaman_utama(kon).decode()
    assert "12:30" in h


def test_dashboard_tanpa_waktu_menampilkan_strip(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "TanpaWaktu")
        basis.buat_sesi(kon, sid, seed=5)
        h = web.halaman_utama(kon).decode()
    assert ">12:30<" not in h
