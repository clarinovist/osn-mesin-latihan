"""A4: parameter JSON murni — satu bentuk di bank, restorasi tanpa cabang.

Sumber insiden yang ditutup: parameter berstruktur pernah disimpan sebagai
string per-template ("ABCC", "hijau,kuning", "2,3,4") lalu dibongkar lagi
dengan cabang `if template_id` di teacher_pages._soal_dari_baris. Template baru dengan
parameter berstruktur harus MENAMBAH cabang itu untuk bisa direstorasi — dan
yang lupa tidak gagal saat test, tapi saat halaman guru menampilkan soal
yang salah. Kontrak baru: parameter tersimpan apa adanya (list = list), dan
restorasi tidak punya cabang per template sama sekali.
"""

from __future__ import annotations

import inspect
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import web  # noqa: E402
import teacher_pages  # noqa: E402
from generator import buat_lembar  # noqa: E402
from migrate_params import KLAUSUL, jalankan  # noqa: E402

KLAUSUL_IDS = tuple(sorted(KLAUSUL))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    database.siapkan(p)
    monkeypatch.setattr(database, "BAWAAN", p)
    return p


def _baris_klausul(db, pasangan_level_seed):
    """Baris sesi bertemplate berklausul dari beberapa (level, seed).

    Lewat dua level: siklus_huruf/warna/jumlah_siklus hidup di P3,
    sisa_bagi_siklus baru muncul di P4+ — satu level tak pernah
    mewakili keempatnya."""
    hasil = []
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Migrasi", "P3")
        for level, seed in pasangan_level_seed:
            sesi_id = database.buat_sesi(kon, sid, seed=seed, level=level)
            hasil.extend(
                b
                for b in database.isi_sesi(kon, sesi_id)
                if b["template_id"] in KLAUSUL
            )
    return hasil


# ── Soal baru: list JSON-native ─────────────────────────────────────────


def test_soal_baru_menyimpan_pola_sebagai_list_json(db):
    baris_baris = _baris_klausul(db, [("P3", 1), ("P3", 7), ("P5", 88), ("P5", 2026)])
    assert baris_baris, "seed uji tidak menghasilkan template berklausul"
    terlihat = set()
    for b in baris_baris:
        param = json.loads(b["parameter"])
        assert isinstance(param["pola"], list), (
            f"{b['template_id']}: pola tersimpan {param['pola']!r} "
            "(harus list JSON, bukan string)"
        )
        terlihat.add(b["template_id"])
    # Semua 4 template berklausul benar-benar terwakili di seed uji.
    assert terlihat == set(KLAUSUL_IDS)


def test_soal_baru_terrestorasi_identik_tanpa_cabang(db):
    """Restorasi dari bank harus menghasilkan Soal yang persis dengan yang
    dibangkitkan generator — tanpa logika per-template di _soal_dari_baris."""
    with database.buka(db) as kon:
        sid = database.tambah_siswa(kon, "Restorasi")
        sesi_id = database.buat_sesi(kon, sid, seed=77)
        asli = buat_lembar(77).soal
        ulang = [
            teacher_pages._soal_dari_baris(b) for b in database.isi_sesi(kon, sesi_id)
        ]
    for a, u in zip(asli, ulang):
        assert u.teks == a.teks
        assert u.kunci == a.kunci
        assert u.tanda_tangan == a.tanda_tangan


def test_soal_dari_baris_tanpa_cabang_per_template():
    """Gerbang struktural: fungsi restorasi tidak boleh mengenal template."""
    sumber = inspect.getsource(teacher_pages._soal_dari_baris)
    assert "split(" not in sumber, "ada pembongkaran string per template"
    assert 'template_id"] ==' not in sumber, "ada cabang per template"


# ── Migrasi baris lama ──────────────────────────────────────────────────


def _tabel_lama(kon: sqlite3.Connection) -> int:
    """Sisipkan satu soal siklus_huruf BERBENTUK LAMA (pola string) + sesi."""
    kurir = kon.execute(
        """INSERT INTO siswa (nama, tingkat) VALUES ('Lama', 'P3')"""
    )
    siswa_id = kurir.lastrowid
    sesi_id = kon.execute(
        "INSERT INTO sesi (siswa_id, seed) VALUES (?, 123)", (siswa_id,)
    ).lastrowid
    # Bentuk lama persis seperti pra-A4: pola string gabung, tanda_tangan
    # memuat bentuk string itu. Kunci ikut konvensi template 1-based:
    # pola[(posisi - 1) % n] → ABCC posisi 9 = A.
    param_lama = '{"pola": "ABCC", "posisi": 9}'
    tt_lama = "P3|siklus_huruf(pola=ABCC,posisi=9)"
    soal_id = kon.execute(
        """INSERT INTO soal (tanda_tangan, template_id, parameter, kunci,
                             bagian, level)
           VALUES (?, 'siklus_huruf', ?, ?, 'B', 'P3')""",
        (tt_lama, param_lama, "A"),
    ).lastrowid
    kon.execute(
        "INSERT INTO sesi_soal (sesi_id, soal_id, nomor) VALUES (?, ?, 1)",
        (sesi_id, soal_id),
    )
    return soal_id


def test_migrasi_mengubah_baris_lama_jadi_list_dan_re_sign(db):
    with database.buka(db) as kon:
        soal_id = _tabel_lama(kon)

        diubah = jalankan(kon)
        assert diubah == 1

        baris = kon.execute(
            "SELECT * FROM soal WHERE id = ?", (soal_id,)
        ).fetchone()
        param = json.loads(baris["parameter"])
        assert param["pola"] == ["A", "B", "C", "C"]
        # Kunci lama TIDAK berubah — migrasi memindah bentuk, bukan soal.
        assert baris["kunci"] == "A"
        # tanda_tangan dihitung ulang dari bentuk baru.
        assert "pola=['A', 'B', 'C', 'C']" in baris["tanda_tangan"]
        # Baris sesi lama masih bisa direstorasi lewat jalur baru.
        soal = teacher_pages._soal_dari_baris(baris)
        assert soal.kunci == "A"
        assert soal.parameter["pola"] == ["A", "B", "C", "C"]


def test_migrasi_idempoten_dan_tak_menyentuh_baris_lain(db):
    with database.buka(db) as kon:
        soal_id = _tabel_lama(kon)
        assert jalankan(kon) == 1
        tt_sesudah = kon.execute(
            "SELECT tanda_tangan FROM soal WHERE id = ?", (soal_id,)
        ).fetchone()["tanda_tangan"]
    # Koneksi berikutnya (bukan nested — koneksi pertama harus selesai
    # commit dulu, SQLite tidak mengizinkan dua penulis simultan).
    with database.buka(db) as kon2:
        # Idempoten: lari kedua kali tidak mengubah apa pun lagi.
        assert jalankan(kon2) == 0
        assert (
            kon2.execute(
                "SELECT tanda_tangan FROM soal WHERE id = ?", (soal_id,)
            ).fetchone()["tanda_tangan"]
            == tt_sesudah
        )
    # Basis murni baru: nol perubahan.
    with database.buka(db) as kon3:
        assert jalankan(kon3) == 0


def test_migrasi_menolak_baris_yang_kuncinya_beda(db):
    """Baris rusak (kunci tidak cocok dengan parameter) HARUS menghentikan
    migrasi — bukan diam-diam ditulis ulang dengan kunci baru."""
    with database.buka(db) as kon:
        soal_id = _tabel_lama(kon)
        kon.execute(
            "UPDATE soal SET kunci = 'Z' WHERE id = ?", (soal_id,)
        )
        kon.commit()
        with pytest.raises(AssertionError):
            jalankan(kon)
        # Parameter lama tidak diubah.
        param = json.loads(
            kon.execute(
                "SELECT parameter FROM soal WHERE id = ?", (soal_id,)
            ).fetchone()["parameter"]
        )
        assert param["pola"] == "ABCC"
