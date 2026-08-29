"""Fase 2 — lampiran foto lembar diisi anak → AI vision → konfirmasi guru.

Tiga lapis yang diuji:
  - llm.ekstrak_lembar: baca foto, hasil {nomor, jawaban, caraku},
    gagal-diam seperti seluruh llm.py;
  - basis: simpan/daftar/ambil/tandai lampiran (tabel baru);
  - web: upload multipart, halaman konfirmasi, terapkan → diagnosa.
"""

from __future__ import annotations

import json
import time
import sqlite3
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import basis  # noqa: E402
import lampiran  # noqa: E402
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


# ── 2.3 Upload multipart + serve berkas ───────────────────────────────


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    yield s
    s.berhenti()


def minta_multipart(server, jalur, auth, nama_berkas, mime, isi, nama_field="foto"):
    """POST multipart/form-data lewat socket — pola ServerUji.minta."""
    import base64
    import urllib.error
    import urllib.request

    boundary = "----UjiBoundaryOSN"
    tubuh = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{nama_field}"; '
        f'filename="{nama_berkas}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + isi + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        server.alamat + jalur, data=tubuh, method="POST",
    )
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8"), dict(e.headers)


def test_http_upload_lampiran_mulai_ekstraksi(server, monkeypatch):
    """POST /lampiran/<sesi> + foto -> ekstraksi dipanggil + row tersimpan."""
    hasil_ai = [
        {"nomor": 1, "jawaban": "10", "caraku": "tambah 2"},
        {"nomor": 2, "jawaban": "9", "caraku": "?"},
    ]
    tertangkap: list = []
    monkeypatch.setattr(
        llm, "ekstrak_lembar",
        lambda soal_konteks, b64: (
            tertangkap.append((soal_konteks, b64)) or hasil_ai
        ),
    )
    with server.buka() as kon:
        sid = basis.tambah_siswa(kon, "AnakLamp")
        sesi_id = basis.buat_sesi(kon, sid, seed=7, mode="drill")
        jumlah_soal = len(basis.isi_sesi(kon, sesi_id))

    kode, _, _ = minta_multipart(
        server, f"/lampiran/{sesi_id}",
        ("guru", SANDI_GURU), "lembar.jpg", "image/jpeg",
        b"\xff\xd8\xff\xe0" + b"0" * 100,
    )
    # urllib follow redirect ke halaman konfirmasi
    assert kode == 200
    assert len(tertangkap) == 1
    konteks, b64 = tertangkap[0]
    assert len(konteks) == jumlah_soal
    assert b64  # base64 terkirim
    with server.buka() as kon:
        lampiran = basis.daftar_lampiran(kon, sesi_id)
        assert len(lampiran) == 1
        hasil = json.loads(lampiran[0]["hasil_json"])["soal"]
        assert hasil[0]["jawaban"] == "10"


def test_http_upload_bukan_gambar_ditolak(server):
    """MIME bukan gambar -> 400, tanpa menyentuh AI."""
    with server.buka() as kon:
        sid = basis.tambah_siswa(kon, "AnakLamp")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
    kode, html, _ = minta_multipart(
        server, f"/lampiran/{sesi_id}",
        ("guru", SANDI_GURU), "lembar.exe", "application/x-msdownload",
        b"MZ\x90\x00",
    )
    assert kode == 400
    with server.buka() as kon:
        assert len(basis.daftar_lampiran(kon, sesi_id)) == 0


def test_http_serve_berkas_lampiran(server, monkeypatch):
    """GET /lampiran/berkas/<id> mengirim file dengan mime benar."""
    import lampiran

    direktori_root = server.db.parent / "lampiran-uji"
    monkeypatch.setenv("OSN_DIREKTORI_LAMPIRAN", str(direktori_root))
    with server.buka() as kon:
        sid = basis.tambah_siswa(kon, "AnakLamp")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        lid = basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg")
        direktori = direktori_root / str(sesi_id)
        direktori.mkdir(parents=True, exist_ok=True)
        (direktori / "lembar-1.jpg").write_bytes(b"\xff\xd8\xff\xe0FAKEJPEG")
    kode, isi, header = server.minta(
        f"/lampiran/berkas/{lid}", auth=("guru", SANDI_GURU), biner=True
    )
    assert kode == 200
    assert header.get("Content-Type", "").startswith("image/jpeg")
    assert isi == b"\xff\xd8\xff\xe0FAKEJPEG"


# ── 2.4 Konfirmasi guru + terapkan ────────────────────────────────────


def test_halaman_konfirmasi_menampilkan_foto_dan_usulan(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakKonf")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        hasil = {"soal": [{"nomor": 1, "jawaban": "10", "caraku": "tambah 2"}]}
        lid = basis.simpan_lampiran(
            kon, sesi_id, "lembar-1.jpg",
            hasil_json=json.dumps(hasil),
        )
        html = lampiran.halaman_konfirmasi(kon, lid).decode()
    assert 'name="jwb_' in html
    assert 'value="10"' in html           # usulan AI terlihat
    assert 'value="tambah 2"' in html
    assert "/lampiran/berkas/" in html    # foto ditampilkan


def test_halaman_konfirmasi_lampiran_tanpa_hasil(db):
    """AI gagal baca: halaman tetap tampil, input kosong, guru isi manual."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakKonf2")
        sesi_id = basis.buat_sesi(kon, sid, seed=7)
        lid = basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg", hasil_json="")
        html = lampiran.halaman_konfirmasi(kon, lid).decode()
    assert 'name="jwb_' in html
    assert 'value=""' in html


def test_halaman_konfirmasi_lampiran_asing_404(db):
    with basis.buka(db) as kon:
        assert lampiran.halaman_konfirmasi(kon, 999) is None


def test_terapkan_menulis_jawaban_dan_menjalankan_diagnosa(db):
    """Terapkan: jawaban masuk lewat jalur resmi + diagnosis otomatis."""
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakTerap")
        sesi_id = basis.buat_sesi(kon, sid, seed=7, mode="drill")
        lid = basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg")
        kunci = basis.isi_sesi(kon, sesi_id)[0]["kunci"]
        ssid = basis.isi_sesi(kon, sesi_id)[0]["sesi_soal_id"]

        jumlah, pesan = lampiran.terapkan(
            kon, lid,
            {f"jwb_{ssid}": kunci, f"cara_{ssid}": "tambah 2"},
        )
        b = basis.isi_sesi(kon, sesi_id)[0]
        lamp = basis.ambil_lampiran(kon, lid)
    assert jumlah == 1
    assert "1 soal" in pesan
    assert b["benar"] == 1          # diagnosa jalan (drill, benar)
    assert lamp["status"] == "diterapkan"


def test_terapkan_jawaban_salah_dapat_kode_malrule(db):
    with basis.buka(db) as kon:
        sid = basis.tambah_siswa(kon, "AnakTerap2")
        sesi_id = basis.buat_sesi(kon, sid, seed=7, mode="drill")
        lid = basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg")
        for b in basis.isi_sesi(kon, sesi_id):
            mal = basis.malrule_soal(kon, b["soal_id"])
            if mal:
                jumlah, _ = lampiran.terapkan(
                    kon, lid,
                    {f"jwb_{b['sesi_soal_id']}": mal[0]["jawaban"]},
                )
                hasil = next(
                    x for x in basis.isi_sesi(kon, sesi_id)
                    if x["nomor"] == b["nomor"]
                )
                break
        else:
            pytest.fail("seed 7 tidak punya malrule")
    assert jumlah == 1
    assert hasil["kode_final"] == mal[0]["kode"]  # K/H/E, bukan N
    assert hasil["kode_final"] != "N"


def test_http_terapkan_lewat_form(server):
    """POST /lampiran/<id>/terapkan lewat HTTP nyata.

    Verifikasi utama lewat RESPONS halaman (pesan jumlah soal). Pembacaan
    DB diberi polling singkat: thread server menutup koneksi setelah
    commit; di beberapa mesin pembacaan pertama test bisa bersaing dengan
    penutupan itu (deterministik terlihat sebagai rows lama)."""
    with server.buka() as kon:
        sid = basis.tambah_siswa(kon, "feby")
        sesi_id = basis.buat_sesi(kon, sid, seed=7, mode="drill")
        lid = basis.simpan_lampiran(kon, sesi_id, "lembar-1.jpg")
        kunci = basis.isi_sesi(kon, sesi_id)[0]["kunci"]
        ssid = basis.isi_sesi(kon, sesi_id)[0]["sesi_soal_id"]
    kode, isi, _ = server.minta(
        f"/lampiran/{lid}/terapkan",
        auth=("guru", SANDI_GURU),
        data={f"jwb_{ssid}": kunci, f"cara_{ssid}": "lihat pola"},
    )
    assert kode == 200
    assert "1 soal dari foto masuk" in isi, "halaman tidak mengonfirmasi penerapan"

    # DB: tunggu hingga baris jawaban terlihat (maks 2 detik).
    batas = time.time() + 2.0
    while time.time() < batas:
        with server.buka() as kon:
            b = basis.isi_sesi(kon, sesi_id)[0]
            lamp = basis.ambil_lampiran(kon, lid)
        if b["benar"] == 1 and lamp["status"] == "diterapkan":
            break
        time.sleep(0.05)
    assert b["benar"] == 1
    assert lamp["status"] == "diterapkan"
