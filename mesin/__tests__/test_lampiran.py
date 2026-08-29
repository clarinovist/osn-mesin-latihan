"""Fase 2 — lampiran foto lembar diisi anak → AI vision → konfirmasi guru.

Tiga lapis yang diuji:
  - llm.ekstrak_lembar: baca foto, hasil {nomor, jawaban, caraku},
    gagal-diam seperti seluruh llm.py;
  - basis: simpan/daftar/ambil/tandai lampiran (tabel baru);
  - web: upload multipart, halaman konfirmasi, terapkan → diagnosa.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import llm  # noqa: E402
import web  # noqa: E402
from uji_http import SANDI_GURU, SANDI_MURID, ServerUji  # noqa: E402

KUNCI_API = "sk-uji-123"
GAMBAR_UJI = "aGVsbG8="  # base64 "hello" — isi gambar tak penting untuk mock

CONTOH_HASIL = {
    "soal": [
        {"nomor": 1, "jawaban": "10", "caraku": "tambah 2"},
        {"nomor": 2, "jawaban": "9", "caraku": "?"},
    ]
}


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / "uji.db"
    basis.siapkan(p)
    monkeypatch.setattr(basis, "BAWAAN", p)
    return p


@pytest.fixture()
def api_aktif(monkeypatch):
    monkeypatch.setenv(llm.ENV_API_KEY, KUNCI_API)


class ResponsPalsu:
    def __init__(self, muatan: dict):
        self._byte = json.dumps(muatan).encode("utf-8")

    def read(self) -> bytes:
        return self._byte

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def pasang_api(monkeypatch, muatan=None, galat=None):
    tertangkap: list = []

    def urlopen_palsu(req, timeout=None, **kwargs):
        tertangkap.append(req)
        if galat is not None:
            raise galat
        return ResponsPalsu(muatan)

    monkeypatch.setattr(
        llm.urllib.request, "urlopen", urlopen_palsu, raising=True
    )
    return tertangkap


def respons_chat(konten: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": konten}}]}


# ── 2.1 llm.ekstrak_lembar ────────────────────────────────────────────


def test_ekstrak_gagal_diam_tanpa_kunci(monkeypatch):
    monkeypatch.delenv(llm.ENV_API_KEY, raising=False)
    panggilan = pasang_api(monkeypatch)
    assert llm.ekstrak_lembar(["soal 1"], GAMBAR_UJI) is None
    assert panggilan == []


def test_ekstrak_error_network_tidak_raise(monkeypatch, api_aktif):
    pasang_api(monkeypatch, galat=urllib.error.URLError("ditolak"))
    assert llm.ekstrak_lembar(["soal 1"], GAMBAR_UJI) is None


def test_ekstrak_hasil_valid_diparse(monkeypatch, api_aktif):
    pasang_api(
        monkeypatch,
        muatan=respons_chat(json.dumps(CONTOH_HASIL)),
    )
    hasil = llm.ekstrak_lembar(["soal 1", "soal 2"], GAMBAR_UJI)
    assert hasil == [
        {"nomor": 1, "jawaban": "10", "caraku": "tambah 2"},
        {"nomor": 2, "jawaban": "9", "caraku": "?"},
    ]


def test_ekstrak_hasil_dalam_code_fence(monkeypatch, api_aktif):
    pasang_api(
        monkeypatch,
        muatan=respons_chat(
            "```json\n" + json.dumps(CONTOH_HASIL) + "\n```"
        ),
    )
    hasil = llm.ekstrak_lembar(["soal 1", "soal 2"], GAMBAR_UJI)
    assert hasil is not None and len(hasil) == 2


def test_ekstrak_nomor_tidak_lengkap_ditolak(monkeypatch, api_aktif):
    pasang_api(
        monkeypatch,
        muatan=respons_chat(
            json.dumps({"soal": [{"nomor": 1, "jawaban": "10", "caraku": ""}]})
        ),
    )
    # 2 soal diharapkan tapi hanya nomor 1 -> verifikasi gagal
    assert llm.ekstrak_lembar(["soal 1", "soal 2"], GAMBAR_UJI) is None


def test_ekstrak_nomor_aneh_ditolak(monkeypatch, api_aktif):
    pasang_api(
        monkeypatch,
        muatan=respons_chat(
            json.dumps(
                {"soal": [
                    {"nomor": 99, "jawaban": "x", "caraku": ""},
                    {"nomor": 2, "jawaban": "9", "caraku": ""},
                ]}
            )
        ),
    )
    assert llm.ekstrak_lembar(["soal 1", "soal 2"], GAMBAR_UJI) is None


def test_ekstrak_bukan_json_ditolak(monkeypatch, api_aktif):
    pasang_api(monkeypatch, muatan=respons_chat("maaf, tidak bisa membaca"))
    assert llm.ekstrak_lembar(["soal 1"], GAMBAR_UJI) is None


def test_ekstrak_jawaban_kosong_diterima(monkeypatch, api_aktif):
    """Anak melewati soal: jawaban boleh kosong, nomor tetap lengkap."""
    pasang_api(
        monkeypatch,
        muatan=respons_chat(
            json.dumps(
                {"soal": [
                    {"nomor": 1, "jawaban": "", "caraku": ""},
                    {"nomor": 2, "jawaban": "9", "caraku": "?"},
                ]}
            )
        ),
    )
    hasil = llm.ekstrak_lembar(["soal 1", "soal 2"], GAMBAR_UJI)
    assert hasil is not None
    assert hasil[0]["jawaban"] == ""


# ── 2.2 Tabel lampiran + fungsi basis ─────────────────────────────────


def test_siapkan_membuat_tabel_lampiran(db):
    with basis.buka(db) as kon:
        baris = kon.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lampiran'"
        ).fetchone()
        assert baris is not None


def test_simpan_dan_daftar_lampiran(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakLamp")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        lid = basis.simpan_lampiran(
            kon, sesi_id, "lembar-1.jpg", mime="image/jpeg",
            hasil_json='{"soal": []}',
        )
        daftar = basis.daftar_lampiran(kon, sesi_id)
        satu = basis.ambil_lampiran(kon, lid)
    assert len(daftar) == 1
    assert daftar[0]["status"] == "baru"
    assert satu["nama_berkas"] == "lembar-1.jpg"
    assert satu["mime"] == "image/jpeg"
    assert json.loads(satu["hasil_json"]) == {"soal": []}


def test_tandai_lampiran_diterapkan(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakLamp2")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        lid = basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg")
        basis.tandai_lampiran(kon, lid, "diterapkan")
        satu = basis.ambil_lampiran(kon, lid)
    assert satu["status"] == "diterapkan"


def test_hapus_sesi_membersihkan_lampiran(db):
    """Lampiran ikut terhapus saat sesi dihapus (ON DELETE CASCADE)."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakLamp3")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg")
        kon.execute("DELETE FROM sesi WHERE id = ?", (sesi_id,))
        sisa = kon.execute("SELECT COUNT(*) AS n FROM lampiran").fetchone()
    assert sisa["n"] == 0
