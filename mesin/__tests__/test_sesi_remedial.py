"""Poin a feedback Filia — sesi REMEDIAL otomatis dari kesalahan anak.

Lanjutan poin b. Setelah anak tahu letak salahnya, guru butuh satu klik
untuk melatih ulang HAL YANG SAMA dengan angka baru:

  "setelah mengetahui hasil anak, next nya apa yang harus kita lakukan?"

Kontrak yang dikunci:
  1. Sasaran remedial diambil dari DATA nyata (template yang dijawab
     salah / didiagnosis K), bukan tebakan.
  2. Sesi remedial memakai template yang sama tapi SOAL BARU (seed lain)
     — melatih konsep, bukan menghafal jawaban lembar lama.
  3. Anak yang tidak punya kesalahan tercatat -> tidak ada sesi remedial
     (jangan mengarang latihan tanpa dasar).
  4. Palang kepemilikan sama ketat dengan rute guru lain.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
from http_test_kit import SANDI_GURU, ServerUji  # noqa: E402


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    yield s
    s.berhenti()


def _sesi_dengan_kesalahan(kon, nama="AnakRemedial"):
    """Sesi yang sudah dinilai: soal 1 benar, soal 2 & 3 salah."""
    import reports

    sid = database.tambah_siswa(kon, nama, pemilik="guru")
    sesi_id = database.buat_sesi(kon, sid, seed=7, jumlah_soal=4)
    baris = database.isi_sesi(kon, sesi_id)
    database.simpan_jawaban(kon, baris[0]["sesi_soal_id"],
                            jawaban=baris[0]["kunci"], cara="hitung")
    for b in baris[1:3]:
        database.simpan_jawaban(kon, b["sesi_soal_id"],
                                jawaban="999999", cara="hitung")
    reports.diagnosa_murid(kon, sesi_id)
    return sid, sesi_id


# ── 1. Sasaran remedial dari data nyata ───────────────────────────────


def test_sasaran_remedial_hanya_template_yang_salah(db):
    with database.buka(db) as kon:
        sid, sesi_id = _sesi_dengan_kesalahan(kon)
        baris = database.isi_sesi(kon, sesi_id)
        sasaran = database.sasaran_remedial(kon, sid)
    salah = {b["template_id"] for b in baris[1:3]}
    benar_saja = baris[0]["template_id"]
    assert set(sasaran) == salah or salah <= set(sasaran)
    # template yang HANYA dijawab benar tidak ikut dilatih ulang
    if benar_saja not in salah:
        assert benar_saja not in sasaran


def test_sasaran_remedial_kosong_kalau_semua_benar(db):
    import reports

    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "AnakSempurna", pemilik="guru")
        sesi_id = database.buat_sesi(kon, sid, seed=7, jumlah_soal=3)
        for b in database.isi_sesi(kon, sesi_id):
            database.simpan_jawaban(kon, b["sesi_soal_id"],
                                    jawaban=b["kunci"], cara="hitung")
        reports.diagnosa_murid(kon, sesi_id)
        assert database.sasaran_remedial(kon, sid) == []


def test_sasaran_remedial_terpisah_per_anak(db):
    with database.buka(db) as kon:
        _sid_a, _ = _sesi_dengan_kesalahan(kon, "AnakA")
        sid_b = database.tambah_siswa(kon, "AnakB", pemilik="guru")
        assert database.sasaran_remedial(kon, sid_b) == []


# ── 2. Sesi remedial: template sama, SOAL BARU ────────────────────────


def test_sesi_remedial_hanya_berisi_template_yang_salah(db):
    with database.buka(db) as kon:
        sid, sesi_id = _sesi_dengan_kesalahan(kon, "AnakR2")
        sasaran = set(database.sasaran_remedial(kon, sid))
        rem = database.buat_sesi_remedial(kon, sid, seed=99, jumlah_soal=6)
        isi = database.isi_sesi(kon, rem)
    assert rem is not None
    assert len(isi) == 6
    assert {b["template_id"] for b in isi} <= sasaran


def test_sesi_remedial_soalnya_baru_bukan_ulangan_lembar_lama(db):
    """Konsep sama, angka baru — melatih konsep, bukan hafalan jawaban."""
    with database.buka(db) as kon:
        sid, sesi_id = _sesi_dengan_kesalahan(kon, "AnakR3")
        lama = {b["kunci"] for b in database.isi_sesi(kon, sesi_id)}
        param_lama = {b["parameter"] for b in database.isi_sesi(kon, sesi_id)}
        rem = database.buat_sesi_remedial(kon, sid, seed=12345, jumlah_soal=6)
        baru = database.isi_sesi(kon, rem)
    # setidaknya ada soal yang parameternya berbeda dari lembar lama
    assert any(b["parameter"] not in param_lama for b in baru), (
        "sesi remedial mengulang soal identik — seharusnya angka baru"
    )


def test_sesi_remedial_none_kalau_tak_ada_kesalahan(db):
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "AnakBersih", pemilik="guru")
        assert database.buat_sesi_remedial(kon, sid, seed=5) is None
        # dan tidak ada sesi yang terlanjur dibuat
        n = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (sid,)
        ).fetchone()["n"]
    assert n == 0


def test_sesi_remedial_deterministik(db):
    """Seed sama -> lembar sama (kontrak generator tidak boleh rusak)."""
    with database.buka(db) as kon:
        sid, _ = _sesi_dengan_kesalahan(kon, "AnakR4")
        a = database.buat_sesi_remedial(kon, sid, seed=777, jumlah_soal=5)
        b = database.buat_sesi_remedial(kon, sid, seed=777, jumlah_soal=5)
        ta = [x["kunci"] for x in database.isi_sesi(kon, a)]
        tb = [x["kunci"] for x in database.isi_sesi(kon, b)]
    assert ta == tb


# ── 3. Tombol + rute HTTP ─────────────────────────────────────────────


def _anak_dengan_kesalahan(server, nama="feby"):
    with server.buka() as kon:
        sid, _ = _sesi_dengan_kesalahan(kon, nama)
    return sid


def test_tombol_latihan_ulang_muncul_kalau_ada_kesalahan(server):
    sid = _anak_dengan_kesalahan(server, "AnakTombolR")
    kode, isi, _ = server.minta(f"/anak/{sid}", auth=("guru", SANDI_GURU))
    assert kode == 200
    assert f'action="/sesi-remedial/{sid}"' in isi
    assert "Buat latihan ulang" in isi


def test_tombol_latihan_ulang_absen_kalau_belum_ada_kesalahan(server):
    """Tanpa dasar data, jangan menawarkan remedial."""
    with server.buka() as kon:
        sid = database.tambah_siswa(kon, "AnakBaruBanget", pemilik="guru")
    kode, isi, _ = server.minta(f"/anak/{sid}", auth=("guru", SANDI_GURU))
    assert kode == 200
    assert "/sesi-remedial/" not in isi


def test_http_buat_latihan_ulang(server):
    sid = _anak_dengan_kesalahan(server, "AnakHttpR")
    with server.buka() as kon:
        sasaran = set(database.sasaran_remedial(kon, sid))
        sebelum = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (sid,)
        ).fetchone()["n"]
    kode, isi, _ = server.minta(
        f"/sesi-remedial/{sid}", auth=("guru", SANDI_GURU),
        data={"jumlah_soal": "10"},
    )
    assert kode == 200                       # 303 diikuti ke /anak/<id>
    assert "Latihan ulang untuk" in isi
    with server.buka() as kon:
        sesudah = kon.execute(
            "SELECT id FROM sesi WHERE siswa_id = ? ORDER BY id DESC", (sid,)
        ).fetchall()
        assert len(sesudah) == sebelum + 1
        isi_baru = database.isi_sesi(kon, int(sesudah[0]["id"]))
    assert len(isi_baru) == 10
    assert {b["template_id"] for b in isi_baru} <= sasaran


def test_http_latihan_ulang_tanpa_dasar_tidak_membuat_sesi(server):
    with server.buka() as kon:
        sid = database.tambah_siswa(kon, "AnakKosongR", pemilik="guru")
    kode, isi, _ = server.minta(
        f"/sesi-remedial/{sid}", auth=("guru", SANDI_GURU), data={}
    )
    assert kode == 200
    assert "Belum ada kesalahan tercatat" in isi
    with server.buka() as kon:
        n = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (sid,)
        ).fetchone()["n"]
    assert n == 0


def test_http_latihan_ulang_anak_keluarga_lain_404(server):
    """Palang kepemilikan: guru lain tidak boleh membuat sesi untuk anak ini.

    Assertion WAJIB memeriksa efek sampingnya (jumlah sesi tidak bertambah),
    bukan hanya kode 404: mutation test membuktikan versi yang hanya
    meng-assert 404 tetap lolos walau palangnya dihapus, karena kode 404
    bisa datang dari cabang lain.
    """
    with server.buka() as kon:
        sid, _ = _sesi_dengan_kesalahan(kon, "AnakOrangLainR")
        kon.execute("UPDATE siswa SET pemilik = 'guru2' WHERE id = ?", (sid,))
        sebelum = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (sid,)
        ).fetchone()["n"]
    kode, _, _ = server.minta(
        f"/sesi-remedial/{sid}", auth=("guru", SANDI_GURU), data={}
    )
    assert kode == 404
    with server.buka() as kon:
        sesudah = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (sid,)
        ).fetchone()["n"]
    assert sesudah == sebelum, "sesi terbuat padahal bukan anak keluarganya"


# ── 4. Lintas topik — akar 502 produksi (3 Sep 2026) ──────────────────
#
# Sasaran remedial diambil dari SEMUA sesi anak, jadi template-nya bisa
# milik topik mana pun. Sebelum perbaikan ini `buat_sesi_remedial` selalu
# memakai paket bawaan (pola-bilangan), sehingga template topik lain
# (`soal_umur`, `tabel_penalaran`, ...) tidak ada di `paket.templates` dan
# generator melempar KeyError -> handler POST mati -> Caddy menjawab 502.
# Test lama tidak menangkapnya karena fixture-nya selalu memakai topik
# bawaan; di sini sesi sumbernya sengaja topik lain.


def _sesi_salah_topik(kon, nama, topik, level, jumlah=4):
    """Sesi topik NON-bawaan yang seluruh jawabannya salah."""
    import reports

    sid = database.tambah_siswa(kon, nama, pemilik="guru", tingkat=level)
    sesi_id = database.buat_sesi(
        kon, sid, seed=7, topik=topik, level=level, jumlah_soal=jumlah
    )
    for b in database.isi_sesi(kon, sesi_id):
        database.simpan_jawaban(kon, b["sesi_soal_id"],
                                jawaban="999999", cara="hitung")
    reports.diagnosa_murid(kon, sesi_id)
    return sid, sesi_id


def test_remedial_topik_selain_bawaan_tidak_meledak(db):
    """Regresi 502: anak yang salah di topik logika harus tetap dapat sesi."""
    with database.buka(db) as kon:
        sid, _ = _sesi_salah_topik(kon, "AnakLogika", "logika", "P5")
        sasaran = set(database.sasaran_remedial(kon, sid))
        assert sasaran, "prasyarat: harus ada kesalahan tercatat"
        rem = database.buat_sesi_remedial(
            kon, sid, seed=4242, level="P5", jumlah_soal=6
        )
        isi = database.isi_sesi(kon, rem)
    assert rem is not None
    assert len(isi) == 6
    assert {b["template_id"] for b in isi} <= sasaran


def test_remedial_lintas_dua_topik_sekaligus(db):
    """Kesalahan di dua topik berbeda tetap satu sesi remedial."""
    import reports

    with database.buka(db) as kon:
        sid, _ = _sesi_salah_topik(kon, "AnakDuaTopik", "logika", "P5")
        sesi2 = database.buat_sesi(
            kon, sid, seed=11, topik="statistika", level="P5", jumlah_soal=3
        )
        for b in database.isi_sesi(kon, sesi2):
            database.simpan_jawaban(kon, b["sesi_soal_id"],
                                    jawaban="999999", cara="hitung")
        reports.diagnosa_murid(kon, sesi2)

        sasaran = set(database.sasaran_remedial(kon, sid))
        rem = database.buat_sesi_remedial(
            kon, sid, seed=555, level="P5", jumlah_soal=8
        )
        isi = database.isi_sesi(kon, rem)
    assert len(isi) == 8
    assert {b["template_id"] for b in isi} <= sasaran


def test_remedial_level_anak_tidak_didukung_topik_sasaran(db):
    """`siswa.tingkat` teks bebas: level yang tak didukung paket sasaran
    tidak boleh meledak — kontrak yang sama dengan komposisi_untuk()."""
    with database.buka(db) as kon:
        sid, _ = _sesi_salah_topik(kon, "AnakP4", "logika", "P5")
        # logika hanya punya P3/P5/P6; anak dipindah ke P4
        kon.execute("UPDATE siswa SET tingkat = 'P4' WHERE id = ?", (sid,))
        rem = database.buat_sesi_remedial(
            kon, sid, seed=606, level="P4", jumlah_soal=5
        )
        isi = database.isi_sesi(kon, rem)
    assert rem is not None
    assert len(isi) == 5


def test_remedial_topik_tersimpan_bisa_dibaca_ulang(db):
    """Kolom sesi.topik sesi remedial harus bisa direkonstruksi paketnya,
    supaya halaman lembar/cetak tidak jatuh ke paket bawaan yang salah."""
    import topics

    with database.buka(db) as kon:
        sid, _ = _sesi_salah_topik(kon, "AnakTopikSimpan", "logika", "P5")
        rem = database.buat_sesi_remedial(
            kon, sid, seed=808, level="P5", jumlah_soal=4
        )
        nilai = kon.execute(
            "SELECT topik FROM sesi WHERE id = ?", (rem,)
        ).fetchone()["topik"]
        template = {b["template_id"] for b in database.isi_sesi(kon, rem)}
    paket = topics.dari_sesi(nilai)
    assert template <= set(paket.templates), (
        f"paket {nilai!r} tidak memuat template sesinya sendiri"
    )


def test_http_remedial_lintas_topik_tidak_500(server):
    """Jalur HTTP penuh — inilah yang di produksi menjadi 502."""
    with server.buka() as kon:
        sid, _ = _sesi_salah_topik(kon, "AnakHttpLintas", "logika", "P5")
    kode, isi, _ = server.minta(
        f"/sesi-remedial/{sid}", auth=("guru", SANDI_GURU),
        data={"jumlah_soal": "10"},
    )
    assert kode == 200, f"rute remedial gagal (kode {kode})"
    assert "Latihan ulang untuk" in isi
    with server.buka() as kon:
        terakhir = kon.execute(
            "SELECT id FROM sesi WHERE siswa_id = ? ORDER BY id DESC", (sid,)
        ).fetchone()["id"]
        assert len(database.isi_sesi(kon, int(terakhir))) == 10
