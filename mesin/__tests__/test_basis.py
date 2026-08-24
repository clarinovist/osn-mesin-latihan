"""Uji alur penuh: sesi -> jawaban -> diagnosis -> laporan.

Memakai basis data sementara, bukan latihan.db, supaya data anak yang
sungguhan tidak tersentuh test.

Yang dibuktikan di sini bukan tiap fungsi bekerja sendiri-sendiri (itu tugas
test lain), melainkan bahwa rangkaiannya menghasilkan laporan yang benar —
termasuk aturan pencatatan yang mudah salah: satu miskonsepsi yang muncul di
beberapa soal tetap dihitung satu.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
from diagnosa import diagnosa  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    return p


def test_sesi_berisi_dua_belas_soal(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Uji")
        sesi_id = basis.buat_sesi(kon, sid, seed=555)
        isi = basis.isi_sesi(kon, sesi_id)
    assert len(isi) == 12
    assert [r["nomor"] for r in isi] == list(range(1, 13))


def test_bank_soal_tidak_menggandakan_soal_yang_sama(db):
    """Seed sama dipakai dua siswa -> bank tetap 12, bukan 24.

    Kalau bank menggandakan, statistik "berapa varian yang sudah dipakai"
    jadi bohong dan tidak bisa dipakai memutuskan kapan menambah template.
    """
    with basis.buka(db) as kon:
        a = basis.tambah_siswa(kon, "A")
        b = basis.tambah_siswa(kon, "B")
        basis.buat_sesi(kon, a, seed=777)
        basis.buat_sesi(kon, b, seed=777)
        total = sum(r["jumlah"] for r in basis.statistik_bank(kon))
    assert total == 12


def test_bank_tumbuh_saat_seed_berbeda(db):
    """Inti kebutuhan: tiap generate menambah kekayaan bank."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Tumbuh")
        for seed in (1, 2, 3, 4, 5):
            basis.buat_sesi(kon, sid, seed=seed)
        total = sum(r["jumlah"] for r in basis.statistik_bank(kon))
    # 5 sesi x 12 soal = 60 maksimum; sebagian template bervarian sedikit
    # sehingga tabrakan wajar, tapi harus tumbuh jauh di atas 12.
    assert 30 < total <= 60


def test_seed_sama_menghasilkan_soal_identik(db):
    """Lembar bisa dicetak ulang persis — penting kalau kertasnya hilang."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Ulang")
        s1 = basis.buat_sesi(kon, sid, seed=99)
        s2 = basis.buat_sesi(kon, sid, seed=99)
        a = [r["soal_id"] for r in basis.isi_sesi(kon, s1)]
        b = [r["soal_id"] for r in basis.isi_sesi(kon, s2)]
    assert a == b


def test_alur_penuh_sampai_ringkasan(db):
    """Jalankan seluruh rantai dengan jawaban yang dirancang.

    Skenario: anak menjawab benar sebagian, sisanya salah dengan cara yang
    persis diprediksi malrule pertama tiap soal. Ringkasan harus mencatat
    kodenya, bukan sekadar skor.
    """
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Alur")
        sesi_id = basis.buat_sesi(kon, sid, seed=321)

        for i, baris in enumerate(basis.isi_sesi(kon, sesi_id)):
            mal = basis.malrule_soal(kon, baris["soal_id"])
            # soal genap dijawab benar, ganjil dijawab sesuai malrule pertama
            if i % 2 == 0:
                jwb = baris["kunci"]
            else:
                jwb = mal[0]["jawaban"] if mal else "999"

            jid = basis.simpan_jawaban(
                kon, baris["sesi_soal_id"], jawaban=jwb, cara="ada coretan"
            )
            u = diagnosa(baris["kunci"], jwb, "ada coretan", "", False, mal, False)
            basis.simpan_diagnosis(
                kon, jid, u.benar, u.kode, u.kode, u.malrule_id, u.alasan
            )

        r = basis.ringkasan(kon, sid)[0]

    assert r["jumlah_soal"] == 12
    assert r["benar"] == 6
    # sisanya harus terkode, bukan menggantung tanpa diagnosis
    assert (r["k"] or 0) + (r["b"] or 0) + (r["h"] or 0) == 6


def test_miskonsepsi_sama_lintas_sesi_terhitung_sebagai_satu(db):
    """Aturan pencatatan yang paling mudah salah.

    Anak mengulang miskonsepsi yang SAMA di dua sesi dengan angka berbeda.
    Laporan harus menyebutnya satu miskonsepsi yang muncul di 2 sesi —
    bukan dua masalah terpisah. Inilah alasan yang dibandingkan malrule_id,
    bukan nomor soal atau angkanya.
    """
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Ulangi")

        for seed in (11, 22):  # dua sesi, angka soal berbeda
            sesi_id = basis.buat_sesi(kon, sid, seed=seed, tanggal=f"2026-09-{seed:02d}")
            for baris in basis.isi_sesi(kon, sesi_id):
                if baris["template_id"] != "deret_geometri":
                    continue
                mal = [
                    m for m in basis.malrule_soal(kon, baris["soal_id"])
                    if m["kode"] == "K"
                ]
                if not mal:
                    continue
                m = mal[0]
                jid = basis.simpan_jawaban(
                    kon, baris["sesi_soal_id"], jawaban=m["jawaban"], cara="coretan"
                )
                basis.simpan_diagnosis(
                    kon, jid, False, "K", "K", m["malrule_id"], m["alasan"]
                )

        hasil = basis.miskonsepsi_berulang(kon, sid)

    assert len(hasil) == 1, "miskonsepsi yang sama harus menyatu jadi satu baris"
    assert hasil[0]["jumlah_sesi"] == 2
    assert hasil[0]["kemunculan"] == 2


def test_materi_bertanda_t_masuk_peta_bukan_nilai(db):
    """T bukan kegagalan — dikumpulkan sebagai daftar materi yang belum diajar."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "PetaT")
        sesi_id = basis.buat_sesi(kon, sid, seed=404)
        baris = basis.isi_sesi(kon, sesi_id)[-1]  # soal tantangan

        jid = basis.simpan_jawaban(
            kon, baris["sesi_soal_id"], jawaban="", belum_pernah=True
        )
        u = diagnosa(baris["kunci"], "", "", "", True, [], False)
        basis.simpan_diagnosis(kon, jid, u.benar, u.kode, u.kode, None, u.alasan)

        peta = basis.peta_materi_baru(kon, sid)

    assert len(peta) == 1
    assert peta[0]["kali"] == 1


def test_jawaban_bisa_diperbarui_tanpa_menggandakan(db):
    """Guru salah ketik lalu memperbaiki — tidak boleh jadi dua baris."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Ralat")
        sesi_id = basis.buat_sesi(kon, sid, seed=808)
        ss = basis.isi_sesi(kon, sesi_id)[0]["sesi_soal_id"]

        id1 = basis.simpan_jawaban(kon, ss, jawaban="salah ketik")
        id2 = basis.simpan_jawaban(kon, ss, jawaban="sudah benar")
        n = kon.execute(
            "SELECT COUNT(*) AS n FROM jawaban WHERE sesi_soal_id = ?", (ss,)
        ).fetchone()["n"]
        isi = kon.execute(
            "SELECT jawaban FROM jawaban WHERE id = ?", (id2,)
        ).fetchone()["jawaban"]

    assert id1 == id2
    assert n == 1
    assert isi == "sudah benar"


def test_menghapus_sesi_membersihkan_jawaban_dan_diagnosis(db):
    """Kalau sesi dibatalkan, jejaknya tidak boleh tertinggal jadi data yatim."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Hapus")
        sesi_id = basis.buat_sesi(kon, sid, seed=606)
        ss = basis.isi_sesi(kon, sesi_id)[0]["sesi_soal_id"]
        jid = basis.simpan_jawaban(kon, ss, jawaban="x", cara="y")
        basis.simpan_diagnosis(kon, jid, False, "K", "K", None, "uji")

        kon.execute("DELETE FROM sesi WHERE id = ?", (sesi_id,))

        sisa_j = kon.execute("SELECT COUNT(*) AS n FROM jawaban").fetchone()["n"]
        sisa_d = kon.execute("SELECT COUNT(*) AS n FROM diagnosis").fetchone()["n"]
        # soal tetap di bank — itu aset, bukan data anak
        sisa_s = kon.execute("SELECT COUNT(*) AS n FROM soal").fetchone()["n"]

    assert sisa_j == 0
    assert sisa_d == 0
    assert sisa_s == 12


# ── Konfigurasi lewat lingkungan (dipakai saat deploy) ──────────────────


def test_lokasi_basis_data_bisa_disetel_lewat_lingkungan(tmp_path, monkeypatch):
    """Regresi deploy: container gagal start karena basis data menunjuk /app.

    Di dalam container /app dimiliki root dan read-only, sehingga basis data
    WAJIB tinggal di volume. Sebelum ada OSN_BERKAS_DB, `basis.BAWAAN`
    dihitung sekali dari lokasi berkas sumber dan tidak bisa dialihkan —
    container mati berulang dengan "unable to open database file".

    Kegagalan seperti ini tidak pernah muncul saat dijalankan lokal, jadi
    satu-satunya cara menahannya adalah test yang meniru kondisi deploy.
    """
    import importlib

    tujuan = tmp_path / "volume" / "latihan.db"
    tujuan.parent.mkdir()
    monkeypatch.setenv("OSN_BERKAS_DB", str(tujuan))

    import basis as basis_modul

    importlib.reload(basis_modul)
    try:
        assert basis_modul.BAWAAN == tujuan
        basis_modul.siapkan()
        with basis_modul.buka() as kon:
            basis_modul.tambah_siswa(kon, "Volume")
            assert [r["nama"] for r in basis_modul.daftar_siswa(kon)] == ["Volume"]
        assert tujuan.exists(), "basis data tidak dibuat di lokasi yang disetel"
    finally:
        monkeypatch.delenv("OSN_BERKAS_DB", raising=False)
        importlib.reload(basis_modul)


def test_lokasi_berkas_sandi_bisa_disetel_lewat_lingkungan(tmp_path, monkeypatch):
    """Alasan yang sama dengan basis data: sandi harus tinggal di volume,
    kalau tidak ia hilang tiap container diganti dan palangnya mati."""
    import importlib

    tujuan = tmp_path / "volume" / "sandi.json"
    tujuan.parent.mkdir()
    monkeypatch.setenv("OSN_BERKAS_SANDI", str(tujuan))

    import sandi as sandi_modul

    importlib.reload(sandi_modul)
    try:
        assert sandi_modul.BERKAS_SANDI == tujuan
        sandi_modul.simpan_sandi("uji-volume", "guru")
        assert tujuan.exists()
        assert sandi_modul.wajib_sandi()
        assert sandi_modul.periksa("guru", "uji-volume")
    finally:
        monkeypatch.delenv("OSN_BERKAS_SANDI", raising=False)
        importlib.reload(sandi_modul)


def test_folder_lembar_bisa_disetel_lewat_lingkungan(tmp_path, monkeypatch):
    """Regresi deploy ketiga dari kelas yang sama.

    Setelah basis data dan berkas sandi, `buat_lembar.py` masih menulis ke
    /app/lembar dan gagal dengan "Permission denied" di container. Pola yang
    berulang: apa pun yang DITULIS aplikasi harus bisa diarahkan ke volume,
    karena /app read-only.

    Test ini menahan jalur ketiga; kalau nanti ada jalur tulis baru, ia harus
    ikut daftar di test_semua_jalur_tulis_bisa_diarahkan().
    """
    import importlib

    tujuan = tmp_path / "volume" / "lembar"
    monkeypatch.setenv("OSN_FOLDER_LEMBAR", str(tujuan))

    import buat_lembar as bl

    importlib.reload(bl)
    try:
        assert bl.KELUARAN == tujuan
    finally:
        monkeypatch.delenv("OSN_FOLDER_LEMBAR", raising=False)
        importlib.reload(bl)


def test_semua_jalur_tulis_bisa_diarahkan(tmp_path, monkeypatch):
    """Daftar tunggal semua lokasi yang ditulis aplikasi.

    Tiga kali berturut-turut deploy gagal karena satu jalur tulis terlewat:
    basis data, lalu berkas sandi, lalu folder lembar. Masing-masing hanya
    ketahuan setelah container mati di VPS, tidak pernah saat dijalankan di
    Mac.

    Test ini menjadi tempat tunggal untuk memeriksanya. Menambah jalur tulis
    baru tanpa mendaftarkannya di sini berarti mengulang kesalahan yang sama
    untuk keempat kalinya.
    """
    import importlib

    jalur = [
        ("OSN_BERKAS_DB", "basis", "BAWAAN", tmp_path / "v" / "x.db"),
        ("OSN_BERKAS_SANDI", "sandi", "BERKAS_SANDI", tmp_path / "v" / "s.json"),
        ("OSN_FOLDER_LEMBAR", "buat_lembar", "KELUARAN", tmp_path / "v" / "lembar"),
    ]

    for env, nama_modul, atribut, tujuan in jalur:
        monkeypatch.setenv(env, str(tujuan))
        modul = importlib.import_module(nama_modul)
        importlib.reload(modul)
        try:
            assert getattr(modul, atribut) == tujuan, (
                f"{nama_modul}.{atribut} tidak menghormati {env} — "
                f"akan gagal di container"
            )
        finally:
            monkeypatch.delenv(env, raising=False)
            importlib.reload(modul)
