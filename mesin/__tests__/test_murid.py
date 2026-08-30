"""Fase 4 — palang keras sisi murid.

Yang dijaga di sini bukan kenyamanan, tapi kontrak data:

  Rute & fungsi murid tidak boleh pernah menyentuh kunci, malrule,
  diagnosis, atau laporan.

Cara menegakkannya bukan membaca kode dan berdoa: kolom-kolom sensitif
diblokir di level sqlite3.Row lewat monkeypatch, sehingga kalau satu pun
fungsi halaman murid mencoba SELECT/akses kolom itu, test meledak — apa pun
jalurnya, sekarang atau lima bulan lagi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import murid  # noqa: E402
import sandi  # noqa: E402
from uji_http import SANDI_GURU, SANDI_MURID, ServerUji  # noqa: E402


KOLOM_TERLARANG = {"kunci", "malrule_id", "kode_usulan", "kode_final", "alasan"}


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """Basis data biasa, TANPA palang Row.

    Dipakai test yang memang perlu membaca kunci dari sudut pandang guru
    (mis. memeriksa isi HTML murid terhadap kunci sebenarnya). Palang ada
    di fixture `db_terjaga` — memasangnya di sini akan membuat test yang
    sah ikut meledak, dan itu sempat terjadi.
    """
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    return p


@pytest.fixture()
def db_terjaga(db, monkeypatch):
    """Basis data + palang level-Row.

    Akses ke kolom terlarang dari kode mana pun yang berjalan di bawah
    fixture ini akan meledak. Karena seluruh rute murid diuji lewat
    fixture ini, satu SELECT kunci yang tidak sengaja ditambahkan lima
    bulan lagi akan gagal di CI, bukan di tangan anak.
    """
    import sqlite3

    asli = sqlite3.Row

    class RowTerjaga(asli):
        def __getitem__(self, kunci):
            if isinstance(kunci, str) and kunci in KOLOM_TERLARANG:
                raise AssertionError(
                    f"KODE MURID MENGAKSES '{kunci}' — palang Fase 4"
                )
            return super().__getitem__(kunci)

    monkeypatch.setattr(sqlite3, "Row", RowTerjaga)
    return db


@pytest.fixture()
def db_dengan_sesi(db_terjaga):
    with basis.buka(db_terjaga) as kon:
        siswa_id = basis.tambah_siswa(kon, "AnakUji")
        sesi_id = basis.buat_sesi(kon, siswa_id, seed=42)
    return db_terjaga, siswa_id, sesi_id


# ── Palang data ──────────────────────────────────────────────────────────


def test_palang_halaman_kerja_tidak_menyentuh_kunci(db_dengan_sesi):
    db, siswa_id, sesi_id = db_dengan_sesi
    with basis.buka(db) as kon:
        isi = murid.halaman_kerja(kon, siswa_id, sesi_id)  # tidak boleh raise


def test_palang_daftar_sesi_tidak_menyentuh_diagnosis(db_dengan_sesi):
    db, siswa_id, _ = db_dengan_sesi
    with basis.buka(db) as kon:
        murid.halaman_daftar_sesi(kon, siswa_id, "AnakUji")


def test_palang_soal_murid_tanpa_kunci(db_dengan_sesi):
    """soal_murid mengirim soal ke browser anak — satu field pun bocor,
    anak tinggal view-source."""
    db, siswa_id, sesi_id = db_dengan_sesi
    with basis.buka(db) as kon:
        for s in murid.soal_murid(kon, sesi_id, siswa_id):
            assert not set(s) & {"kunci", "malrule"}, f"field terlarang: {set(s)}"


# ── Isolasi antar murid ────────────────────────────────────────────────


def test_murid_tidak_bisa_buka_sesi_anak_lain(db_terjaga):
    """Dua anak. B menebak alamat sesi A. Harus ditolak — bukan dibisukan,
    ditolak: None agar handler mengirim 404/403."""
    with basis.buka(db_terjaga) as kon:
        a = basis.tambah_siswa(kon, "AnakA")
        b = basis.tambah_siswa(kon, "AnakB")
        sesi_a = basis.buat_sesi(kon, a, seed=7)
        assert murid.sesi_murid(kon, b, sesi_a) is None
        assert murid.soal_murid(kon, sesi_a, b) == []
        assert murid.halaman_kerja(kon, b, sesi_a) is None


def test_simpan_jawaban_menolak_sesi_orang_lain(db_terjaga):
    with basis.buka(db_terjaga) as kon:
        a = basis.tambah_siswa(kon, "AnakA")
        b = basis.tambah_siswa(kon, "AnakB")
        sesi_a = basis.buat_sesi(kon, a, seed=7)
        assert not murid.simpan_jawaban_murid(kon, b, sesi_a, {})


# ── Jawaban tersimpan benar (dan bisa didiagnosis guru kemudian) ───────


def test_jawaban_murid_masuk_jalur_yang_sama_dengan_guru(db_dengan_sesi):
    """Jawaban anak disimpan lewat basis.simpan_jawaban yang sama. Guru
    membukanya dari halaman sesi seperti biasa — tidak ada jalur kedua yang
    bisa salah bentuk."""
    db, siswa_id, sesi_id = db_dengan_sesi
    with basis.buka(db) as kon:
        daftar = murid.soal_murid(kon, sesi_id, siswa_id)
        ssid = daftar[0]["sesi_soal_id"]
        ok = murid.simpan_jawaban_murid(
            kon, siswa_id, sesi_id, {f"jwb_{ssid}": "24", f"cara_{ssid}": "dikali 3"}
        )
        assert ok
        baris = kon.execute(
            """SELECT j.jawaban, j.cara FROM jawaban j
               JOIN sesi_soal ss ON ss.id = j.sesi_soal_id
               WHERE ss.id = ?""",
            (ssid,),
        ).fetchone()
        assert baris["jawaban"] == "24"
        assert baris["cara"] == "dikali 3"


def test_soal_dilewati_tidak_membuat_baris_kosong(db_dengan_sesi):
    db, siswa_id, sesi_id = db_dengan_sesi
    with basis.buka(db) as kon:
        murid.simpan_jawaban_murid(kon, siswa_id, sesi_id, {})
        n = kon.execute("SELECT COUNT(*) AS n FROM jawaban").fetchone()["n"]
        assert n == 0


# ── Peran & akun ────────────────────────────────────────────────────────


def test_akun_murid_dan_guru_hidup_bersebelahan(tmp_path):
    p = tmp_path / "sandi.json"
    sandi.simpan_sandi("rahasia-guru", "guru", path=p)      # bentuk lama
    sandi.tambah_akun("Feby", "rahasia-anak", "murid", path=p)

    assert sandi.periksa_peran("guru", "rahasia-guru", "guru", path=p)
    assert not sandi.periksa_peran("guru", "rahasia-guru", "murid", path=p)
    assert sandi.periksa_peran("feby", "rahasia-anak", "murid", path=p)
    assert not sandi.periksa_peran("Feby", "rahasia-anak", "guru", path=p)
    # sandi guru tidak membuka pintu murid, sandi murid tidak membuka guru
    assert sandi.peran_dari("guru", "rahasia-guru", path=p) == "guru"
    assert sandi.peran_dari("Feby", "rahasia-anak", path=p) == "murid"


def test_nama_pengguna_case_insensitive(tmp_path):
    p = tmp_path / "sandi.json"
    sandi.tambah_akun("Putri", "sandi123", "murid", path=p)
    assert sandi.cari_akun("putri", path=p) is not None
    assert sandi.cari_akun("PUTRI", path=p) is not None


def test_nama_ganda_ditolak(tmp_path):
    p = tmp_path / "sandi.json"
    sandi.tambah_akun("ika", "s1", "murid", path=p)
    with pytest.raises(ValueError):
        sandi.tambah_akun("Ika", "s2", "murid", path=p)


def test_peran_aneh_ditolak(tmp_path):
    p = tmp_path / "sandi.json"
    # "admin" kini peran sah (multi-keluarga); contoh peran asing diganti.
    with pytest.raises(ValueError):
        sandi.tambah_akun("hantu", "s3", "bos", path=p)


# ── Tautan akun murid → siswa (multi-keluarga) ──────────────────────────


def test_siswa_dari_akun_memakai_siswa_id_eksplisit(db, tmp_path, monkeypatch):
    """Akun dengan siswa_id menang: nama login tak harus sama dengan nama
    siswa mana pun (dua keluarga boleh punya anak bernama sama)."""
    berkas = tmp_path / "sandi.json"
    monkeypatch.setattr(sandi, "BERKAS_SANDI", berkas)
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakLain", pemilik="ortu-a")
    sandi.tambah_akun("feby2", "sandi-feby-12345", "murid", siswa_id=sid)
    with basis.buka(db) as kon:
        assert murid.siswa_dari_akun(kon, "feby2") == sid


def test_siswa_dari_akun_fallback_nama_untuk_akun_warisan(db, tmp_path, monkeypatch):
    """Akun lama tanpa siswa_id tetap terhubung lewat pencocokan nama."""
    berkas = tmp_path / "sandi.json"
    monkeypatch.setattr(sandi, "BERKAS_SANDI", berkas)
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "feby")
    sandi.tambah_akun("feby", "sandi-feby-12345", "murid")
    with basis.buka(db) as kon:
        assert murid.siswa_dari_akun(kon, "feby") == sid


# ── Halaman HTML murid bersih dari jejak jawaban ───────────────────────


def test_html_kerja_tanpa_kunci_dalam_form(db):
    """Input value= tidak boleh pernah memuat kunci — anak yang lihat source
    mendapat jawabannya gratis, dan semua kode diagnosis mati.

    Test ini TIDAK memakai fixture palang (kunci dibaca langsung di sini,
    peran guru) supaya yang diuji adalah isi HTML-nya, bukan jalur akses.
    """
    basis.siapkan(db)
    with basis.buka(db) as kon:
        siswa_id = basis.tambah_siswa(kon, "AnakHtml")
        sesi_id = basis.buat_sesi(kon, siswa_id, seed=42)
        halaman = murid.halaman_kerja(kon, siswa_id, sesi_id)
        assert halaman is not None
        isi = halaman.decode()
        for b in basis.isi_sesi(kon, sesi_id):
            kunci = b["kunci"]
            if len(kunci) >= 2:
                assert f'value="{kunci}"' not in isi


# ── Pilihan cepat "Caraku" (uji HP nyata: caraku sering kosong) ────────


def test_pilihan_cara_tersimpan_ke_kolom_cara(db_terjaga):
    """Pilihan digabung ke kolom `cara` yang sama, bukan kolom baru:
    diagnosa.py dan laporan guru sudah membaca kolom itu."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        ssid = murid.soal_murid(kon, ses, sid)[0]["sesi_soal_id"]
        n = murid.simpan_jawaban_murid(kon, sid, ses, {
            f"jwb_{ssid}": "24", f"pilih_{ssid}": "hitung_satu_satu",
        })
        assert n == 1
        r = kon.execute(
            "SELECT cara FROM jawaban WHERE sesi_soal_id = ?", (ssid,)
        ).fetchone()
        assert r["cara"] == murid.AWALAN_PILIHAN + "hitung_satu_satu"


def test_pilihan_palsu_dari_form_dibuang(db_terjaga):
    """Nilai datang dari form; yang tidak dikenal tidak boleh tersimpan."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        ssid = murid.soal_murid(kon, ses, sid)[0]["sesi_soal_id"]
        murid.simpan_jawaban_murid(kon, sid, ses, {
            f"jwb_{ssid}": "24", f"pilih_{ssid}": "<script>jahat</script>",
        })
        r = kon.execute(
            "SELECT cara FROM jawaban WHERE sesi_soal_id = ?", (ssid,)
        ).fetchone()
        assert "script" not in r["cara"]
        assert r["cara"] == ""


def test_pilihan_dan_teks_bisa_berdampingan(db_terjaga):
    """Anak boleh memilih DAN menulis. Teksnya lebih berharga, jadi jangan
    sampai pilihan menimpanya."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        ssid = murid.soal_murid(kon, ses, sid)[0]["sesi_soal_id"]
        murid.simpan_jawaban_murid(kon, sid, ses, {
            f"jwb_{ssid}": "24", f"pilih_{ssid}": "pakai_rumus",
            f"cara_{ssid}": "aku kali 3 terus tambah 2",
        })
        r = kon.execute(
            "SELECT cara FROM jawaban WHERE sesi_soal_id = ?", (ssid,)
        ).fetchone()
        assert "pakai_rumus" in r["cara"]
        assert "aku kali 3 terus tambah 2" in r["cara"]


def test_mengaku_menebak_jadi_kode_n(db_terjaga):
    """Inti seluruh fitur ini: pengakuan anak menggantikan kekosongan yang
    ambigu. Sebelumnya kotak kosong -> N (mesin menduga menebak); sekarang
    anak bisa menyatakannya sendiri."""
    from diagnosa import diagnosa

    u = diagnosa("24", "27", murid.AWALAN_PILIHAN + "tebak", "", False, [])
    assert u.kode == "N"
    assert not u.benar


def test_menebak_tapi_kebetulan_benar_tetap_n(db_terjaga):
    """Jawaban benar hasil tebakan adalah tanda bahaya yang paling mudah
    hilang dari data — pengakuan diperiksa SEBELUM kunci dibandingkan."""
    from diagnosa import diagnosa

    u = diagnosa("24", "24", murid.AWALAN_PILIHAN + "tebak", "", False, [])
    assert u.kode == "N", "menebak lalu benar tetap harus tercatat menebak"
    assert not u.benar


def test_mengaku_bingung_jadi_kode_t(db_terjaga):
    """Bingung bukan menebak dan bukan salah konsep: ia peta materi."""
    from diagnosa import diagnosa

    u = diagnosa("24", "", murid.AWALAN_PILIHAN + "bingung", "", False, [])
    assert u.kode == "T"


def test_konfirmasi_tersimpan_muncul_dengan_jumlah(db_terjaga):
    """Tanpa konfirmasi, anak tidak tahu jawabannya masuk lalu menekan
    tombol berulang atau mengira kerjanya hilang."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        html = murid.halaman_kerja(kon, sid, ses, tersimpan=3).decode()
    assert "Tersimpan" in html
    assert "3 soal" in html


def test_konfirmasi_tidak_muncul_saat_pertama_buka(db_terjaga):
    """Halaman yang baru dibuka belum menyimpan apa pun."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        html = murid.halaman_kerja(kon, sid, ses).decode()
    assert "Tersimpan" not in html


def test_pilihan_tampil_kembali_saat_dibuka_lagi(db_terjaga):
    """Anak yang membuka lagi harus melihat pilihannya masih tercentang.

    Kalau tidak, ia mengira jawabannya hilang lalu mengisi ulang dari nol —
    dan pengisian ulang itu biasanya lebih asal daripada yang pertama.
    """
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        ssid = murid.soal_murid(kon, ses, sid)[0]["sesi_soal_id"]
        murid.simpan_jawaban_murid(
            kon, sid, ses, {f"jwb_{ssid}": "24", f"pilih_{ssid}": "lihat_pola"}
        )
        html = murid.halaman_kerja(kon, sid, ses).decode()

    assert 'value="lihat_pola" checked' in html
    # dan pilihan lain tidak ikut tercentang
    assert 'value="tebak" checked' not in html


def test_semua_pilihan_muncul_di_halaman(db_terjaga):
    """Kalau satu pilihan hilang dari HTML, anak tidak punya cara
    menyatakannya dan datanya jatuh kembali jadi kekosongan ambigu."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "Anak")
        ses = basis.buat_sesi(kon, sid, seed=42)
        html = murid.halaman_kerja(kon, sid, ses).decode()

    for kode, label in murid.PILIHAN_CARA:
        assert f'value="{kode}"' in html, f"pilihan {kode} hilang"
        assert label in html, f"label {label!r} hilang"


# ── Halaman Selesai (setelah semua soal terisi) ─────────────────────────


def test_semua_terisi_false_saat_kosong(db_terjaga):
    """Belum ada satu jawaban pun → belum selesai."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "AnakSelesai")
        ses = basis.buat_sesi(kon, sid, seed=42)
        assert murid.semua_terisi(kon, sid, ses) is False


def test_semua_terisi_false_saat_sebagian(db_dengan_sesi):
    """Satu soal terisi dari 12 → masih ada yang kosong, belum selesai."""
    db, siswa_id, sesi_id = db_dengan_sesi
    with basis.buka(db) as kon:
        ssid = murid.soal_murid(kon, sesi_id, siswa_id)[0]["sesi_soal_id"]
        murid.simpan_jawaban_murid(kon, siswa_id, sesi_id, {f"jwb_{ssid}": "24"})
        assert murid.semua_terisi(kon, siswa_id, sesi_id) is False


def test_semua_terisi_true_saat_semua_soal_terisi(db_terjaga):
    """Semua soal sesi diisi (jawaban minimal) → selesai = True."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "AnakSelesai")
        ses = basis.buat_sesi(kon, sid, seed=42)
        daftar = murid.soal_murid(kon, ses, sid)
        data = {f"jwb_{s['sesi_soal_id']}": "1" for s in daftar}
        murid.simpan_jawaban_murid(kon, sid, ses, data)
        assert murid.semua_terisi(kon, sid, ses) is True


def test_semua_terisi_false_untuk_sesi_orang_lain(db_terjaga):
    """Sesi anak lain tidak boleh dianggap selesai oleh murid ini —
    konsisten dengan simpan_jawaban_murid yang menolak sesi orang lain."""
    with basis.buka(db_terjaga) as kon:
        sid_a = basis.tambah_siswa(kon, "AnakA")
        sid_b = basis.tambah_siswa(kon, "AnakB")
        ses_a = basis.buat_sesi(kon, sid_a, seed=42)
        assert murid.semua_terisi(kon, sid_b, ses_a) is False


def test_halaman_selesai_muncul_untuk_sesi_miliknya(db_dengan_sesi):
    """Halaman selesai render untuk murid yang punya sesi itu."""
    db, siswa_id, sesi_id = db_dengan_sesi
    with basis.buka(db) as kon:
        daftar = murid.soal_murid(kon, sesi_id, siswa_id)
        data = {f"jwb_{s['sesi_soal_id']}": "1" for s in daftar}
        murid.simpan_jawaban_murid(kon, siswa_id, sesi_id, data)
        html = murid.halaman_selesai(kon, siswa_id, sesi_id).decode()
    assert "Selesai" in html
    assert "Simpan jawabanku" not in html, (
        "halaman selesai tidak boleh menyuruh anak menyimpan lagi"
    )
    assert 'name="jwb_' not in html, (
        "halaman selesai tidak boleh memuat form jawaban"
    )


def test_halaman_selesai_none_untuk_sesi_orang_lain(db_terjaga):
    """Murid lain tidak boleh membuka halaman selesai sesi orang lain."""
    with basis.buka(db_terjaga) as kon:
        sid_a = basis.tambah_siswa(kon, "AnakA")
        sid_b = basis.tambah_siswa(kon, "AnakB")
        ses_a = basis.buat_sesi(kon, sid_a, seed=42)
        assert murid.halaman_selesai(kon, sid_b, ses_a) is None


def test_halaman_selesai_palang_bersih(db_terjaga):
    """Halaman selesai tidak boleh membocorkan kunci/malrule/diagnosa —
    diuji lewat fixture palang yang meledak pada kolom terlarang."""
    with basis.buka(db_terjaga) as kon:
        sid = basis.tambah_siswa(kon, "AnakSelesai")
        ses = basis.buat_sesi(kon, sid, seed=42)
        daftar = murid.soal_murid(kon, ses, sid)
        data = {f"jwb_{s['sesi_soal_id']}": "1" for s in daftar}
        murid.simpan_jawaban_murid(kon, sid, ses, data)
        html = murid.halaman_selesai(kon, sid, ses).decode()
    for kata in ("kunci", "malrule", "diagnosa", "jawaban_benar"):
        assert kata.lower() not in html.lower()


# ── E2E HTTP: alur simpan → selesai ───────────────────────────────────


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    yield s
    s.berhenti()


def _bikin_sesi_untuk_feby(server) -> int:
    """Guru buat sesi untuk 'feby' (akun murid uji) → kembalikan sesi_id."""
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "feby", pemilik="guru")
    server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "pola-bilangan"},
    )
    with server.buka() as kon:
        return kon.execute(
            "SELECT id FROM sesi WHERE siswa_id = ? ORDER BY id DESC LIMIT 1",
            (siswa_id,),
        ).fetchone()["id"]


def test_http_simpan_semua_soal_diarahkan_ke_halaman_selesai(server):
    """Murid mengisi SEMUA soal → setelah POST diarahkan ke halaman selesai,
    bukan kembali ke lembar kerja dengan banner tersimpan."""
    sesi_id = _bikin_sesi_untuk_feby(server)
    with server.buka() as kon:
        daftar = basis.isi_sesi(kon, sesi_id)
        data = {f"jwb_{b['sesi_soal_id']}": "1" for b in daftar}

    kode, isi, _ = server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data=data,
    )
    assert kode == 200
    assert "Selesai" in isi, "semua soal terisi harus diarahkan ke halaman selesai"
    assert "Tersimpan" not in isi, (
        "halaman selesai tidak boleh menampilkan banner tersimpan"
    )


def test_http_simpan_sebagian_tetap_di_lembar_dengan_banner(server):
    """Murid mengisi SEBAGIAN soal → kembali ke lembar + banner tersimpan,
    supaya bisa lanjut mengerjakan sisanya."""
    sesi_id = _bikin_sesi_untuk_feby(server)
    with server.buka() as kon:
        daftar = basis.isi_sesi(kon, sesi_id)
        satu = {f"jwb_{daftar[0]['sesi_soal_id']}": "24"}

    kode, isi, _ = server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data=satu,
    )
    assert kode == 200
    assert "Tersimpan" in isi, "simpan sebagian harus tetap menampilkan banner"
    assert "Selesai" not in isi, (
        "belum semua soal terisi — jangan arahkan ke halaman selesai"
    )


# ── Pencatatan waktu pengerjaan (kolom mulai/selesai sesi) ────────────


def test_http_post_pertama_mencatat_mulai(server):
    """POST jawaban pertama = anak mulai mengerjakan. Selesai tetap kosong
    sampai SEMUA soal terisi — durasi setengah jalan menyesatkan."""
    sesi_id = _bikin_sesi_untuk_feby(server)
    with server.buka() as kon:
        b = basis.isi_sesi(kon, sesi_id)[0]

    server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data={f"jwb_{b['sesi_soal_id']}": "1"},
    )
    with server.buka() as kon:
        baris = kon.execute(
            "SELECT mulai, selesai FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()
    assert baris["mulai"] is not None
    assert baris["selesai"] is None


def test_http_post_kedua_tidak_menggeser_mulai(server):
    """Idempoten lewat HTTP: POST berulang dari HP tidak boleh menggeser
    mulai, kalau tidak, durasi pengerjaan jadi bohong. Nilai mulai dipaksa
    ke angka pasti supaya dua POST di detik yang sama pun tetap terdeteksi
    kalau pelindungnya hilang."""
    sesi_id = _bikin_sesi_untuk_feby(server)
    with server.buka() as kon:
        b = basis.isi_sesi(kon, sesi_id)[0]
        ssid = b["sesi_soal_id"]

    server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data={f"jwb_{ssid}": "1"},
    )
    with server.buka() as kon:
        kon.execute(
            "UPDATE sesi SET mulai = '2026-08-01 08:00:00' WHERE id = ?",
            (sesi_id,),
        )
    server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data={f"jwb_{ssid}": "2"},
    )
    with server.buka() as kon:
        mulai = kon.execute(
            "SELECT mulai FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()["mulai"]
    assert mulai == "2026-08-01 08:00:00", "POST kedua menggeser mulai"


def test_tandai_mulai_tidak_menggeser_yang_sudah_ada(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "IdemMulai")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        kon.execute(
            "UPDATE sesi SET mulai = '2026-08-01 08:00:00' WHERE id = ?",
            (sesi_id,),
        )
        basis.tandai_mulai(kon, sesi_id)
        m = kon.execute(
            "SELECT mulai FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()["mulai"]
        basis.tandai_mulai(kon, 99999)  # sesi tak dikenal: no-op, tidak meledak
    assert m == "2026-08-01 08:00:00"


def test_tandai_selesai_tidak_menggeser_yang_sudah_ada(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "IdemSelesai")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        kon.execute(
            "UPDATE sesi SET selesai = '2026-08-01 09:00:00' WHERE id = ?",
            (sesi_id,),
        )
        basis.tandai_selesai(kon, sesi_id)
        s = kon.execute(
            "SELECT selesai FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()["selesai"]
        basis.tandai_selesai(kon, 99999)
    assert s == "2026-08-01 09:00:00"


def test_http_semua_terisi_mencatat_selesai(server):
    """Alur penuh: isi semua → mulai dan selesai keduanya tercatat, sehingga
    dashboard guru bisa menampilkan durasi pengerjaan."""
    sesi_id = _bikin_sesi_untuk_feby(server)
    with server.buka() as kon:
        daftar = basis.isi_sesi(kon, sesi_id)
        data = {f"jwb_{b['sesi_soal_id']}": "1" for b in daftar}

    server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data=data,
    )
    with server.buka() as kon:
        baris = kon.execute(
            "SELECT mulai, selesai FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()
    assert baris["mulai"] is not None
    assert baris["selesai"] is not None


def test_http_post_ulang_setelah_selesai_tidak_menggeser_selesai(server):
    """Anak iseng menekan simpan lagi setelah halaman selesai — selesai
    yang tercatat saat semua soal terisi tetap yang pertama."""
    sesi_id = _bikin_sesi_untuk_feby(server)
    with server.buka() as kon:
        daftar = basis.isi_sesi(kon, sesi_id)
        data = {f"jwb_{b['sesi_soal_id']}": "1" for b in daftar}

    server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data=data,
    )
    server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data=data,
    )
    with server.buka() as kon:
        baris = kon.execute(
            "SELECT selesai FROM sesi WHERE id = ?", (sesi_id,)
        ).fetchone()
    assert baris["selesai"] is not None  # dijaga WHERE selesai IS NULL
