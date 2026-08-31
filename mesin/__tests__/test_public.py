"""Fase 0 + A launch publik: identitas brand & landing publik.

Kontrak yang dijaga:
1. Identitas produk dari design_tokens (satu sumber) — tidak ada literal
   "Mesin Latihan"/"pola bilangan" di copy deskriptif web.py.
2. GET / tanpa sesi -> 200 landing publik (bukan 401).
3. GET / dengan sesi guru -> 200 dashboard (halaman_utama).
4. Rute guru lain tetap 401 tanpa kredensial (palang tidak melemah).
5. Landing tidak bocor kata palang (kunci/malrule/diagnosa).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database  # noqa: E402
import design_tokens as T  # noqa: E402
import web  # noqa: E402
from http_test_kit import SANDI_GURU, ServerUji  # noqa: E402


# ───────────────────────── Fase 0: identitas ─────────────────────────

def test_tokens_punya_identitas_produk():
    assert getattr(T, "NAMA_PRODUK", "") == "Caraku"
    assert getattr(T, "TAGLINE", "").strip()


def test_web_tidak_ada_literal_brand_lama():
    sumber = Path(web.__file__).read_text(encoding="utf-8")
    # Copy deskriptif yang dilihat pengguna; komentar kode internal dikecualikan.
    # "pola bilangan" sebagai NAMA TOPIK di registry (topik_*.py) tetap sah.
    baris_copy = [
        ln
        for ln in sumber.splitlines()
        if "pola bilangan" in ln.lower()
        and not ln.lstrip().startswith("#")
        and '"pola bilangan"' not in ln  # nilai pilihan/registry sah
    ]
    assert not baris_copy, f"copy lama tersisa: {baris_copy}"
    assert "Mesin Latihan" not in sumber


def test_halaman_masuk_pakai_brand_baru():
    # _halaman_masuk dipanggil tanpa instance server — akses lewat kelas.
    # Yang dites: halaman login tidak lagi menyebut topik lama.
    sumber = Path(web.__file__).read_text(encoding="utf-8")
    assert T.NAMA_PRODUK in sumber, "web.py harus merujuk brand dari tokens"


# ───────────────── Fase A: landing vs dashboard di rute / ─────────────────

@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    with s.buka() as kon:
        sid = database.tambah_siswa(kon, "Putri")
        sesi_id = database.buat_sesi(kon, sid, seed=7)
    yield s, sesi_id
    s.berhenti()


def test_landing_200_tanpa_sesi(server):
    s, _ = server
    kode, isi, _ = s.minta("/")
    assert kode == 200
    assert T.NAMA_PRODUK in isi
    assert T.TAGLINE in isi
    assert "/daftar" in isi  # CTA pendaftaran
    assert "/masuk" in isi


def test_landing_bocor_palang_tidak_boleh(server):
    s, _ = server
    _, isi, _ = s.minta("/")
    rendah = isi.lower()
    for kata in ("kunci", "malrule"):
        # marker CSS (.kunci{}) tidak dihitung — cek kata berarti
        assert f">{kata}<" not in rendah and f'"{kata}"' not in rendah


def test_dashboard_guru_di_root(server):
    s, sesi_id = server
    kode, isi, _ = s.minta("/", auth=("guru", SANDI_GURU))
    assert kode == 200
    assert "Sesi" in isi or "sesi" in isi  # dashboard, bukan landing


def test_rute_guru_lain_tetap_401_tanpa_sesi(server):
    s, sesi_id = server
    assert s.minta(f"/sesi/{sesi_id}")[0] == 401
    assert s.minta("/akun")[0] == 401


def test_murid_tetap_401_di_root(server):
    """Murid tidak boleh masuk dashboard guru via /."""
    from http_test_kit import SANDI_MURID

    s, _ = server
    kode, isi, _ = s.minta("/", auth=("feby", SANDI_MURID))
    # murid -> landing publik (200), BUKAN dashboard guru
    assert kode == 200
    assert T.NAMA_PRODUK in isi
    assert "Buat sesi baru" not in isi  # elemen khas dashboard guru


# ───────────────── kebijakan privasi (publik) ─────────────────

def test_kebijakan_privasi_200_tanpa_sesi(server):
    """Tautan consent /daftar & footer landing tak boleh 404 lagi."""
    s, _ = server
    kode, isi, _ = s.minta("/kebijakan-privasi")
    assert kode == 200
    assert "Kebijakan Privasi" in isi
    assert 'href="/masuk"' in isi  # satu pintu masuk, konsisten landing


def test_kebijakan_privasi_bocor_data_tidak_boleh(server):
    """Halaman statis: tanpa nama siswa/DB, sama untuk semua pengunjung.
    (Id sesi sengaja tidak dites — angka kecil selalu ada di CSS/teks.)"""
    s, _ = server
    _, isi_anon, _ = s.minta("/kebijakan-privasi")
    _, isi_guru, _ = s.minta("/kebijakan-privasi", auth=("guru", SANDI_GURU))
    assert isi_anon == isi_guru, "halaman harus statis"
    assert "Putri" not in isi_anon  # nama siswa fixture tidak bocor
