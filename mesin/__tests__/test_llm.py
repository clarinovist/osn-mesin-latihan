"""Uji klien DeepSeek (llm.py) — semuanya dengan network di-mock.

Yang dibuktikan di sini adalah kontrak desain plan Fase 5, bukan API
sungguhan:

  - gagal-diam: tanpa DEEPSEEK_API_KEY, nol network call, nol exception;
  - verifikasi angka murni: menolak angka karangan, menerima kalimat sah;
  - cache: soal yang sama hanya dibayar sekali (sqlite in-memory);
  - parsing respons OpenAI-compatible yang baik dan yang rusak;
  - kunci/malrule tidak pernah keluar dalam body request.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import unittest.mock as mock
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm  # noqa: E402
from templates import deret_aritmetika  # noqa: E402

KUNCI_API = "sk-uji-123"


# ── Perlengkapan ───────────────────────────────────────────────────────


@pytest.fixture()
def kon():
    """Koneksi sqlite in-memory dengan tabel llm_cache siap."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    llm.ensure_table(c)
    yield c
    c.close()


@pytest.fixture()
def soal():
    """Soal sungguhan dari template: 2, 5, 8, 11, ___ (kunci 14, 17)."""
    return deret_aritmetika(awal=2, beda=3, n_tampil=4, n_minta=2)


class ResponsPalsu:
    """Pengganti hasil urllib.request.urlopen (context manager + read)."""

    def __init__(self, muatan: dict):
        self._byte = json.dumps(muatan).encode("utf-8")

    def read(self) -> bytes:
        return self._byte

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def respons_chat(kalimat: str) -> dict:
    """Format OpenAI-compatible standar /chat/completions."""
    return {"choices": [{"message": {"role": "assistant", "content": kalimat}}]}


def pasang_api(monkeypatch, muatan=None, galat=None):
    """Pasang urlopen palsu; kembalikan daftar request yang tertangkap."""
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


@pytest.fixture()
def api_aktif(monkeypatch):
    monkeypatch.setenv(llm.ENV_API_KEY, KUNCI_API)


# ── Gagal-diam ─────────────────────────────────────────────────────────


def test_gagal_diam_tanpa_kunci(monkeypatch, kon, soal):
    monkeypatch.delenv(llm.ENV_API_KEY, raising=False)
    panggilan = pasang_api(monkeypatch)  # harusnya tak pernah dipanggil

    assert llm.aktif() is False
    assert llm.bungkus(kon, soal) is None
    assert panggilan == []


def test_gagal_diam_kunci_kosong(monkeypatch, kon, soal):
    monkeypatch.setenv(llm.ENV_API_KEY, "   ")
    assert llm.aktif() is False
    assert llm.bungkus(kon, soal) is None


def test_aktif_dengan_kunci(monkeypatch):
    monkeypatch.setenv(llm.ENV_API_KEY, KUNCI_API)
    assert llm.aktif() is True


def test_error_network_tidak_raise(monkeypatch, api_aktif, kon, soal):
    pasang_api(
        monkeypatch,
        galat=urllib.error.URLError("koneksi ditolak"),
    )
    assert llm.bungkus(kon, soal) is None


# ── Verifikasi angka (murni) ───────────────────────────────────────────


def test_verifikasi_menolak_kalimat_yang_membocorkan_kunci(soal):
    """Kunci tidak boleh muncul di kalimat pengganti.

    Versi pertama verifikasi memasukkan angka kunci ke daftar yang sah,
    sehingga kalimat seperti ini lolos dan anak membaca soal beserta
    jawabannya. Itu lubang paling mahal di aplikasi ini — test ini
    menguncinya tertutup permanen.
    """
    bocor = f"Perhatikan bilangan 2, 5, 8, 11. Lanjutkan hingga {soal.kunci}!"
    assert llm.verifikasi(bocor, soal) is False


def test_verifikasi_menerima_cerita_baru_yang_angkanya_lengkap(soal):
    sah = "Perhatikan bilangan 2, 5, 8, 11 pada deret tangga itu."
    assert llm.verifikasi(sah, soal) is True


def test_verifikasi_menolak_kalimat_tanpa_angka(soal):
    """Himpunan kosong adalah subset dari apa pun: aturan subset saja
    menerima kalimat tanpa satu angka pun, padahal soalnya jadi tak bisa
    dikerjakan."""
    assert llm.verifikasi("Perhatikan deret bilangan berikut.", soal) is False


def test_verifikasi_menolak_angka_liar(soal):
    # 999 tidak ada di parameter, teks asli, maupun kunci.
    assert (
        llm.verifikasi(
            "Ani menghitung 2, 5, 8, 11 lalu berhenti di 999.", soal
        )
        is False
    )


def test_verifikasi_menolak_kalimat_kosong_dan_multiline(soal):
    assert llm.verifikasi("", soal) is False
    assert llm.verifikasi("   ", soal) is False
    assert llm.verifikasi("Kalimat pertama.\nKalimat kedua 3.", soal) is False


def test_verifikasi_murni_tanpa_network(monkeypatch, soal):
    # Fungsi verifikasi tidak boleh menyentuh network sama sekali.
    monkeypatch.delenv(llm.ENV_API_KEY, raising=False)
    panggilan = pasang_api(monkeypatch)
    llm.verifikasi("angka 5 saja", soal)
    assert panggilan == []


# ── Parsing respons ────────────────────────────────────────────────────


def test_parse_respons_format_openai(api_aktif):
    assert (
        llm.parse_respons(respons_chat("  satu kalimat. ")) == "satu kalimat."
    )
    assert llm.parse_respons(json.dumps(respons_chat("dari bytes"))) == (
        "dari bytes"
    )
    assert llm.parse_respons(json.dumps(respons_chat("x")).encode()) == "x"


def test_parse_respons_rusak_tetap_none():
    for rusak in (
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": 42}}]},
        "bukan json",
        b"\xff\xfe",
        None,
    ):
        assert llm.parse_respons(rusak) is None


def test_parse_respons_konten_kosong_reasoning_model_tetap_none():
    """v4-flash adalah reasoning model: kalau max_tokens habis di
    reasoning_content, content datang kosong. Konten kosong harus dianggap
    gagal (None), bukan kalimat sah berupa string kosong."""
    muatan = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "reasoning_content": "kita perlu menjawab dalam bahasa "
                    "indonesia ... (habis di sini)",
                }
            }
        ]
    }
    assert llm.parse_respons(muatan) is None


def test_parse_respons_reasoning_content_tidak_mengganggu_konten():
    """Saat reasoning selesai dan konten ada, kehadiran reasoning_content
    tidak boleh mengubah hasil."""
    muatan = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "kalimat sah.",
                    "reasoning_content": "pikir dulu ...",
                }
            }
        ]
    }
    assert llm.parse_respons(muatan) == "kalimat sah."


def test_max_tokens_menampung_reasoning_model(monkeypatch, api_aktif, kon, soal):
    """Reasoning v4-flash memakan token sebelum konten muncul (terukur:
    6 soal butuh +-825 reasoning token). max_tokens 200 membuat konten
    sering kosong dan verifikasi gagal diam-diam."""
    panggilan = pasang_api(monkeypatch, muatan=respons_chat("kalimat."))
    llm.bungkus(kon, soal)

    tubuh = json.loads(panggilan[0].data)
    assert tubuh["max_tokens"] == 2000


# ── Cache ──────────────────────────────────────────────────────────────


def test_cache_miss_lalu_hit(monkeypatch, api_aktif, kon, soal):
    panggilan = pasang_api(monkeypatch, muatan=respons_chat("Pola 2, 5, 8, 11."))

    pertama = llm.bungkus(kon, soal)
    assert pertama == "Pola 2, 5, 8, 11."
    assert len(panggilan) == 1

    # Soal identik: dijawab dari cache, API tidak disentuh lagi.
    kedua = llm.bungkus(kon, soal)
    assert kedua == pertama
    assert len(panggilan) == 1


def test_cache_berbeda_parameter_berbeda_entri(monkeypatch, api_aktif, kon, soal):
    lain = deret_aritmetika(awal=4, beda=3, n_tampil=4, n_minta=2)

    # Muatan mock harus SAH untuk soal yang sedang dibungkus — kalimat
    # soal A ditolak verifikasi kalau dipakai untuk soal B (angkanya
    # berbeda), dan yang gagal verifikasi memang tidak masuk cache.
    pasang_api(
        monkeypatch, muatan=respons_chat("Perhatikan bilangan 2, 5, 8, 11.")
    )
    llm.bungkus(kon, soal)
    pasang_api(
        monkeypatch, muatan=respons_chat("Perhatikan bilangan 4, 7, 10, 13.")
    )
    llm.bungkus(kon, lain)
    assert kon.execute("SELECT COUNT(*) FROM llm_cache").fetchone()[0] == 2


def test_verifikasi_gagal_tak_masuk_cache(monkeypatch, api_aktif, kon, soal):
    # Model mengarang angka liar -> dibuang -> pemanggil pakai kalimat
    # bawaan, dan cache tetap kosong supaya dicoba lagi nanti.
    panggilan = pasang_api(
        monkeypatch, muatan=respons_chat("Angkanya 999 semua.")
    )

    assert llm.bungkus(kon, soal) is None
    assert kon.execute("SELECT COUNT(*) FROM llm_cache").fetchone()[0] == 0

    # Percobaan berikutnya benar-benar memanggil API lagi (bukan cache None).
    assert llm.bungkus(kon, soal) is None
    assert len(panggilan) == 2


def test_template_beda_parameter_sama_tidak_berbagi_cache(monkeypatch, api_aktif, kon):
    """Bug 2 Sep 2026: kunci cache dulu hanya parameter + prompt + model.

    Di bank soal nyata ada 354 pasang parameter identik yang dipakai dua
    template berbeda (mis. {"a": 9, "b": 24} pada `angka_satuan_pangkat`
    dan `kerja_bersama`). Karena cache hit pulang TANPA verifikasi ulang,
    soal yang satu tampil memakai cerita milik soal yang lain — anak
    membaca soal yang tidak nyambung dengan pertanyaannya.
    """
    a = llm.kunci_cache({"a": 9, "b": 24}, template_id="angka_satuan_pangkat")
    b = llm.kunci_cache({"a": 9, "b": 24}, template_id="kerja_bersama")
    assert a != b, "dua template berbeda berbagi entri cache"


def test_latar_berputar_memberi_entri_cache_berbeda(soal):
    """Satu soal boleh punya lebih dari satu cerita: latar yang berbeda
    harus jatuh ke entri cache yang berbeda, kalau tidak putaran kedua
    hanya mengembalikan kalimat yang sama."""
    l0 = llm.pilih_latar(soal, 0)
    l1 = llm.pilih_latar(soal, 1)
    assert l0 != l1
    k0 = llm.kunci_cache(soal.parameter, template_id=soal.template_id, latar=l0)
    k1 = llm.kunci_cache(soal.parameter, template_id=soal.template_id, latar=l1)
    assert k0 != k1


def test_latar_deterministik_antar_proses(soal):
    """Latar dipilih dari SHA-256, bukan hash() bawaan yang diacak per
    proses lewat PYTHONHASHSEED. Kalau latar berubah tiap restart, seluruh
    cache jadi sia-sia dan tiap generate membayar ulang."""
    import subprocess

    kode = (
        "import sys; sys.path.insert(0, %r);"
        "import llm; from templates import deret_aritmetika;"
        "s = deret_aritmetika(awal=2, beda=3, n_tampil=4, n_minta=2);"
        "print(llm.pilih_latar(s, 0))"
    ) % str(Path(__file__).resolve().parent.parent)
    hasil = set()
    for benih in ("0", "1", "12345"):
        keluar = subprocess.run(
            [sys.executable, "-c", kode],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": benih},
        )
        hasil.add(keluar.stdout.strip())
    assert len(hasil) == 1, f"latar berubah antar PYTHONHASHSEED: {hasil}"
    assert hasil == {llm.pilih_latar(soal, 0)}


def test_latar_disebut_di_prompt(monkeypatch, api_aktif, kon, soal):
    """Tanpa arahan latar, model punya beberapa cerita favorit dan
    monotonnya cuma pindah dari template ke LLM."""
    panggilan = pasang_api(monkeypatch, muatan=respons_chat("ok."))
    llm.bungkus(kon, soal)
    tubuh = panggilan[0].data.decode("utf-8")
    assert llm.pilih_latar(soal, 0) in tubuh


def test_ensure_table_idempoten(kon):
    llm.ensure_table(kon)
    llm.ensure_table(kon)  # tidak boleh raise
    assert kon.execute("SELECT COUNT(*) FROM llm_cache").fetchone()[0] == 0


# ── Privasi & bentuk prompt ────────────────────────────────────────────


def test_kunci_dan_malrule_tidak_dikirim(monkeypatch, api_aktif, kon, soal):
    panggilan = pasang_api(monkeypatch, muatan=respons_chat("kalimat."))
    llm.bungkus(kon, soal)

    tubuh = panggilan[0].data.decode("utf-8")
    assert str(soal.kunci) not in tubuh
    for m in soal.malrule:
        assert m.jawaban not in tubuh
    # Kalimat soal asli memang dikirim — itulah yang ditulis ulang.
    assert soal.teks in tubuh


# ── Gerbang biaya ──────────────────────────────────────────────────────


def test_cek_saldo_tanpa_ambang_selalu_aktif(monkeypatch):
    monkeypatch.delenv(llm.ENV_SALDO_MIN, raising=False)
    monkeypatch.delenv(llm.ENV_API_KEY, raising=False)
    assert llm.cek_saldo() is True


def test_cek_saldo_cukup(monkeypatch, api_aktif):
    monkeypatch.setenv(llm.ENV_SALDO_MIN, "10")
    pasang_api(
        monkeypatch,
        muatan={
            "is_available": True,
            "balance_infos": [{"currency": "CNY", "total_balance": "103.89"}],
        },
    )
    assert llm.cek_saldo() is True


def test_cek_saldo_kurang(monkeypatch, api_aktif):
    monkeypatch.setenv(llm.ENV_SALDO_MIN, "200")
    pasang_api(
        monkeypatch,
        muatan={
            "is_available": True,
            "balance_infos": [{"currency": "CNY", "total_balance": "103.89"}],
        },
    )
    assert llm.cek_saldo() is False


def test_cek_saldo_tak_bisa_dipastikan_anggap_nonaktif(monkeypatch, api_aktif):
    monkeypatch.setenv(llm.ENV_SALDO_MIN, "10")
    pasang_api(monkeypatch, galat=urllib.error.URLError("mati"))
    assert llm.cek_saldo() is False


def test_cek_saldo_tanpa_kunci_dan_ambang_terisi(monkeypatch):
    monkeypatch.delenv(llm.ENV_API_KEY, raising=False)
    monkeypatch.setenv(llm.ENV_SALDO_MIN, "10")
    pasang_api(monkeypatch)  # tak boleh tersentuh
    assert llm.cek_saldo() is False


# ── Konfigurasi env ────────────────────────────────────────────────────


def test_konfigurasi_default(monkeypatch):
    for nama in (llm.ENV_BASE_URL, llm.ENV_MODEL, llm.ENV_API_KEY):
        monkeypatch.delenv(nama, raising=False)
    cfg = llm.konfigurasi()
    assert cfg["base_url"] == "https://api.deepseek.com"
    assert cfg["model"] == "deepseek-chat"
    assert cfg["api_key"] == ""


def test_konfigurasi_dari_env(monkeypatch):
    monkeypatch.setenv(llm.ENV_BASE_URL, "https://proxy.example.com/")
    monkeypatch.setenv(llm.ENV_MODEL, "deepseek-reasoner")
    cfg = llm.konfigurasi()
    assert cfg["base_url"] == "https://proxy.example.com"  # slash akhir rapi
    assert cfg["model"] == "deepseek-reasoner"


def test_request_ke_endpoint_chat_completions(monkeypatch, api_aktif, kon, soal):
    panggilan = pasang_api(monkeypatch, muatan=respons_chat("ok."))
    llm.bungkus(kon, soal)

    req = panggilan[0]
    assert req.full_url == "https://api.deepseek.com/chat/completions"
    assert req.get_method() == "POST"
    assert req.headers.get("Authorization") == f"Bearer {KUNCI_API}"
