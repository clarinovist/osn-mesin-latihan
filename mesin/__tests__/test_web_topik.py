"""A3: sesi.topik nyata — guru memilih topik, UI menampilkan dari paket.

Titik rapuh: `sesi.topik` tadinya kolom mati (ditulis, tak pernah dibaca).
Kalau form guru tidak meneruskan pilihannya, atau laporan tidak
menampilkannya, kolomnya mati lagi — dan Fase B (topik kedua) akan diam-diam
menampilkan soal topik salah. Test ini mengunci jalurnya ujung ke ujung.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import murid  # noqa: E402
import web  # noqa: E402
from uji_http import SANDI_GURU, SANDI_MURID, ServerUji  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    return p


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    yield s
    s.berhenti()


# ── Rute POST /sesi-baru (socket sungguhan) ─────────────────────────────


def test_post_sesi_baru_menyimpan_topik_eksplisit(server):
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "Topik Eksplisit")
    # urlopen mengikuti 303 sampai halaman sesi — yang dicek adalah
    # tempat akhir (halaman sesi) + nilai yang tersimpan di basis data.
    kode, isi, _ = server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "pola-bilangan"},
    )
    assert kode == 200
    assert "Sesi #" in isi
    with server.buka() as kon:
        topik = kon.execute(
            """SELECT topik FROM sesi WHERE siswa_id = ?
               ORDER BY id DESC LIMIT 1""",
            (siswa_id,),
        ).fetchone()["topik"]
    assert topik == "pola-bilangan"


def test_post_sesi_baru_tanpa_topik_pakai_bawaan_kanonik(server):
    """Form tanpa pilihan topik tetap menyimpan id kanonik — bukan nilai
    lama 'pola bilangan' dengan spasi."""
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "Topik Default")
    kode, isi, _ = server.minta(
        f"/sesi-baru/{siswa_id}", auth=("guru", SANDI_GURU), data={}
    )
    assert kode == 200
    assert "Sesi #" in isi
    with server.buka() as kon:
        topik = kon.execute(
            """SELECT topik FROM sesi WHERE siswa_id = ?
               ORDER BY id DESC LIMIT 1""",
            (siswa_id,),
        ).fetchone()["topik"]
    assert topik == "pola-bilangan"


def test_post_sesi_baru_topik_tak_dikenal_ditolak_400(server):
    """Topik asing = salah ketik pemanggil — ditolak jelas, bukan diam-diam
    jadi pola bilangan (kontrak beda dari level yang sengaja fallback)."""
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "Topik Aneh")
    kode, isi, _ = server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "topik-hantu"},
    )
    assert kode == 400
    assert "topik-hantu" in isi


# ── UI guru: pilihan topik + tampilan ───────────────────────────────────


def test_halaman_utama_menyediakan_pilihan_topik_dari_registry(db):
    """Dropdown lahir dari registry — Fase B tinggal daftar, UI ikut."""
    with basis.buka(db) as kon:
        basis.tambah_siswa(kon, "Pilih Topik")
        isi = web.halaman_utama(kon).decode()
    assert '<select name="topik"' in isi
    assert 'value="pola-bilangan"' in isi


def test_siswa_p3_tidak_ditawari_dan_tidak_bisa_memilih_aritmetika(server):
    """Topik P5/P6 tidak boleh memicu error server untuk siswa P3."""
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "Topik P3", "P3")
        isi = web.halaman_utama(kon).decode()
    assert 'value="aritmetika-dasar"' not in isi

    kode, isi, _ = server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "aritmetika-dasar"},
    )
    assert kode == 400
    assert "tidak tersedia" in isi


def test_siswa_level_teks_lama_tetap_ditawari_dan_bisa_membuat_sesi(server):
    """Kolom tingkat lama yang bebas teks tetap mendapat fallback pola P3."""
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "Topik Level Lama", "tingkat-lama")
        isi = web.halaman_utama(kon).decode()
    assert 'value="pola-bilangan"' in isi
    assert 'value="aritmetika-dasar"' not in isi

    kode, isi, _ = server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "pola-bilangan"},
    )
    assert kode == 200
    assert "Sesi #" in isi
    with server.buka() as kon:
        level = kon.execute(
            "SELECT level FROM sesi WHERE siswa_id = ? ORDER BY id DESC LIMIT 1",
            (siswa_id,),
        ).fetchone()["level"]
    assert level == "P3"


def test_halaman_utama_daftar_sesi_memuat_kolom_topik(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Daftar Bertopik")
        basis.buat_sesi(kon, sid, seed=77)
        isi = web.halaman_utama(kon).decode()
    assert "Topik" in isi
    assert "pola-bilangan" in isi


def test_halaman_sesi_menampilkan_topik(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Sesi Bertopik")
        sesi_id = basis.buat_sesi(kon, sid, seed=78)
        isi = web.halaman_sesi(kon, sesi_id).decode()
    assert "pola-bilangan" in isi


def test_laporan_menampilkan_kolom_topik(db):
    """Tren per sesi wajib menampilkan topiknya — laporan lintas-topik
    yang tercampur diam-diam adalah kegagalan desain (aturan plan §4)."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Laporan Bertopik")
        basis.buat_sesi(kon, sid, seed=79)
        isi = web.halaman_laporan(kon, sid).decode()
    assert "<th>Topik</th>" in isi
    assert "pola-bilangan" in isi


def test_alur_aritmetika_memakai_judul_dan_laporan_topik_sendiri(server):
    """Topik kedua harus melewati jalur guru, murid, cetak, dan laporan.

    Test ini memakai socket sungguhan: dropdown yang berisi ID topik saja
    belum cukup kalau sesi, lembar, atau laporan masih diam-diam memilih
    paket pola bilangan.
    """
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "feby", "P5")

    kode, isi, _ = server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "aritmetika-dasar"},
    )
    assert kode == 200
    assert "aritmetika-dasar" in isi

    with server.buka() as kon:
        sesi_id = kon.execute(
            "SELECT id FROM sesi WHERE siswa_id = ? ORDER BY id DESC LIMIT 1",
            (siswa_id,),
        ).fetchone()["id"]
        assert len(basis.isi_sesi(kon, sesi_id)) == 6
        lembar = web.halaman_lembar(kon, sesi_id)
        assert lembar is not None
        assert "Latihan Aritmetika Dasar" in lembar.decode()

    kode, isi, _ = server.minta(
        f"/murid/kerjakan/{sesi_id}", auth=("feby", SANDI_MURID)
    )
    assert kode == 200
    assert "Latihan Aritmetika Dasar" in isi

    kode, isi, _ = server.minta(f"/laporan/{siswa_id}", auth=("guru", SANDI_GURU))
    assert kode == 200
    assert "aritmetika-dasar" in isi


def test_laporan_detail_menampilkan_topik_pada_dua_tabel(db):
    """Query detail sudah memisahkan topik; UI wajib membuatnya terlihat."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Detail Topik", "P5")
        pola = basis.buat_sesi(kon, sid, seed=77, topik="pola-bilangan")
        aritmetika = basis.buat_sesi(
            kon, sid, seed=78, level="P5", topik="aritmetika-dasar"
        )
        for sesi_id, kode in ((pola, "K"), (aritmetika, "T")):
            baris = basis.isi_sesi(kon, sesi_id)[0]
            jawaban_id = basis.simpan_jawaban(kon, baris["sesi_soal_id"], "0")
            basis.simpan_diagnosis(
                kon,
                jawaban_id,
                benar=False,
                kode_usulan=kode,
                kode_final=kode,
                malrule_id="uji.topik" if kode == "K" else None,
                alasan="uji topik",
            )
        isi = web.halaman_laporan(kon, sid).decode()

    assert isi.count("<th>Topik</th>") == 3
    assert "aritmetika-dasar" in isi
    assert "pola-bilangan" in isi


# ── Judul dari paket topik (murid + lembar) ─────────────────────────────


def test_halaman_kerja_murid_judul_dari_paket(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Murid Judul")
        sesi_id = basis.buat_sesi(kon, sid, seed=80)
        isi = murid.halaman_kerja(kon, sid, sesi_id)
    assert isi is not None, "halaman kerja tidak terbangkit"
    assert "<title>Kerjakan — Latihan Pola Bilangan</title>" in isi.decode()


def test_halaman_lembar_web_judul_dari_topik_sesi(db):
    """Lembar dibangkitkan ulang dari seed — judulnya harus mengikuti topik
    yang tersimpan di sesi, bukan paket bawaan yang selalu menang."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Lembar Bertopik")
        sesi_id = basis.buat_sesi(kon, sid, seed=81)
        isi = web.halaman_lembar(kon, sesi_id, untuk_guru=False).decode()
        isi_guru = web.halaman_lembar(kon, sesi_id, untuk_guru=True).decode()
    assert "Latihan Pola Bilangan" in isi
    assert "Penilaian — Pola Bilangan" in isi_guru


def test_murid_daftar_sesi_memuat_topik(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "Murid Daftar")
        basis.buat_sesi(kon, sid, seed=82)
        isi = murid.halaman_daftar_sesi(kon, sid, "Murid Daftar").decode()
    teks = re.sub(r"<[^>]+>", " ", isi)
    assert "pola-bilangan" in teks


# ── Alur penuh: guru buat → murid jawab → laporan guru ──────────────────


def test_alur_guru_murid_jawab_laporan_bertopik(server):
    """Sesi bertopik eksplisit dilalui ujung ke ujung lewat socket:
    laporan tetap utuh dan topiknya tampil, bukan tercampur diam-diam."""
    with server.buka() as kon:
        siswa_id = basis.tambah_siswa(kon, "feby")  # nama == akun murid uji

    server.minta(
        f"/sesi-baru/{siswa_id}",
        auth=("guru", SANDI_GURU),
        data={"topik": "pola-bilangan"},
    )
    with server.buka() as kon:
        sesi_id = kon.execute(
            """SELECT id FROM sesi WHERE siswa_id = ?
               ORDER BY id DESC LIMIT 1""",
            (siswa_id,),
        ).fetchone()["id"]
        ssid = basis.isi_sesi(kon, sesi_id)[0]["sesi_soal_id"]

    kode, _, _ = server.minta(
        f"/murid/kerjakan/{sesi_id}",
        auth=("feby", SANDI_MURID),
        data={f"jwb_{ssid}": "42", f"cara_{ssid}": "aku hitung"},
    )
    assert kode == 200

    kode, isi, _ = server.minta(f"/laporan/{siswa_id}", auth=("guru", SANDI_GURU))
    assert kode == 200
    assert "<th>Topik</th>" in isi
    assert "pola-bilangan" in isi
