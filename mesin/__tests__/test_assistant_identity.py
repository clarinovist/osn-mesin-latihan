"""Identitas akun stabil yang menjadi principal privat Pendamping."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import auth  # noqa: E402
import sessions  # noqa: E402


@pytest.fixture()
def berkas(tmp_path):
    return tmp_path / "sandi.json", tmp_path / "sesi.json"


def test_akun_baru_mendapat_id_stabil_dan_reset_tidak_mengubahnya(berkas):
    sandi, _ = berkas
    auth.tambah_akun("Ortu", "sandi-awal-123", "guru", sandi)
    pertama = auth.cari_akun("ortu", sandi)["id_akun"]

    assert auth.setel_sandi_guru("ORTU", "sandi-baru-456", sandi)
    kedua = auth.cari_akun("ortu", sandi)["id_akun"]

    assert auth.id_akun_sah(pertama)
    assert kedua == pertama


def test_hapus_lalu_buat_username_sama_mendapat_id_baru(berkas):
    sandi, _ = berkas
    auth.tambah_akun("ortu", "sandi-awal-123", "guru", sandi)
    lama = auth.cari_akun("ortu", sandi)["id_akun"]

    assert auth.hapus_akun_guru("ortu", sandi)
    auth.tambah_akun("ORTU", "sandi-baru-456", "guru", sandi)

    assert auth.cari_akun("ortu", sandi)["id_akun"] != lama


def test_migrasi_lama_atomik_idempoten_dan_mempertahankan_hash(berkas):
    sandi, _ = berkas
    sebelum = {"pengguna": "guru", **auth.buat_hash("rahasia-123")}
    sandi.write_text(json.dumps(sebelum), encoding="utf-8")

    assert auth.pastikan_id_akun(sandi) is True
    pertama = json.loads(sandi.read_text())
    assert auth.pastikan_id_akun(sandi) is False
    kedua = json.loads(sandi.read_text())

    assert pertama == kedua
    assert auth.id_akun_sah(pertama["id_akun"])
    for kunci in ("pengguna", "garam", "kunci", "iterasi"):
        assert pertama[kunci] == sebelum[kunci]
    assert oct(sandi.stat().st_mode)[-3:] == "600"
    assert not list(sandi.parent.glob(".sandi-*"))


def test_migrasi_multiakun_memberi_id_unik_dan_menjaga_field_asing(berkas):
    sandi, _ = berkas
    mentah = {
        "versi": 7,
        "akun": [
            {"pengguna": "ortu", "peran": "guru", "garam": "aa", "kunci": "bb", "catatan": "tetap"},
            {"pengguna": "anak", "peran": "murid", "garam": "cc", "kunci": "dd", "siswa_id": 9},
        ],
    }
    sandi.write_text(json.dumps(mentah), encoding="utf-8")

    assert auth.pastikan_id_akun(sandi)
    hasil = json.loads(sandi.read_text())

    assert hasil["versi"] == 7
    assert hasil["akun"][0]["catatan"] == "tetap"
    assert hasil["akun"][1]["siswa_id"] == 9
    assert len({akun["id_akun"] for akun in hasil["akun"]}) == 2


def test_migrasi_rusak_gagal_tertutup_tanpa_mengubah_berkas(berkas):
    sandi, _ = berkas
    isi = b'{"akun": [rusak]}'
    sandi.write_bytes(isi)

    with pytest.raises(ValueError, match="berkas akun tidak sah"):
        auth.pastikan_id_akun(sandi)

    assert sandi.read_bytes() == isi
    assert not list(sandi.parent.glob(".sandi-*"))


def test_migrasi_menolak_id_duplikat_tanpa_mengubah_berkas(berkas):
    sandi, _ = berkas
    sama = "akun_" + "a" * 32
    isi = json.dumps({"akun": [
        {"pengguna": "a", "peran": "guru", "id_akun": sama},
        {"pengguna": "b", "peran": "guru", "id_akun": sama},
    ]}).encode()
    sandi.write_bytes(isi)

    with pytest.raises(ValueError, match="id_akun duplikat"):
        auth.pastikan_id_akun(sandi)
    assert sandi.read_bytes() == isi


def test_sesi_baru_membawa_id_dan_principal_tervalidasi(berkas):
    sandi, sesi = berkas
    auth.tambah_akun("ortu", "sandi-awal-123", "guru", sandi)
    akun = auth.cari_akun("ortu", sandi)
    token = sessions.buat("ortu", "guru", id_akun=akun["id_akun"], path=sesi)

    principal = sessions.ambil_principal_pendamping(
        token, path=sesi, path_akun=sandi
    )
    assert principal is not None
    assert principal.pengguna == "ortu"
    assert principal.peran == "guru"
    assert principal.id_akun == akun["id_akun"]
    assert sessions.ambil(token, path=sesi) == ("ortu", "guru")


def test_sesi_lama_tanpa_id_ditolak_khusus_pendamping(berkas):
    sandi, sesi = berkas
    auth.tambah_akun("ortu", "sandi-awal-123", "guru", sandi)
    token = sessions.buat("ortu", "guru", path=sesi)

    assert sessions.ambil(token, path=sesi) == ("ortu", "guru")
    assert sessions.ambil_principal_pendamping(token, path=sesi, path_akun=sandi) is None


def test_sesi_lama_ditolak_setelah_akun_dibuat_ulang(berkas):
    sandi, sesi = berkas
    auth.tambah_akun("ortu", "sandi-awal-123", "guru", sandi)
    lama = auth.cari_akun("ortu", sandi)["id_akun"]
    token = sessions.buat("ortu", "guru", id_akun=lama, path=sesi)

    assert auth.hapus_akun_guru("ortu", sandi)
    auth.tambah_akun("ortu", "sandi-baru-456", "guru", sandi)

    assert sessions.ambil(token, path=sesi) == ("ortu", "guru")
    assert sessions.ambil_principal_pendamping(token, path=sesi, path_akun=sandi) is None


def test_principal_menolak_id_atau_peran_yang_tidak_cocok(berkas):
    sandi, sesi = berkas
    auth.tambah_akun("ortu", "sandi-awal-123", "guru", sandi)
    akun = auth.cari_akun("ortu", sandi)
    token_id_salah = sessions.buat(
        "ortu", "guru", id_akun="akun_" + "f" * 32, path=sesi
    )
    token_peran_salah = sessions.buat(
        "ortu", "admin", id_akun=akun["id_akun"], path=sesi
    )

    assert sessions.ambil_principal_pendamping(
        token_id_salah, path=sesi, path_akun=sandi
    ) is None
    assert sessions.ambil_principal_pendamping(
        token_peran_salah, path=sesi, path_akun=sandi
    ) is None
    with pytest.raises(ValueError, match="id_akun sesi tidak sah"):
        sessions.buat("ortu", "guru", id_akun="bukan-id", path=sesi)


def test_principal_hanya_guru_dengan_berkas_akun_nyata(berkas):
    sandi, sesi = berkas
    for nama, peran in (("anak", "murid"), ("pengelola", "admin")):
        auth.tambah_akun(nama, "sandi-awal-123", peran, sandi)
        akun = auth.cari_akun(nama, sandi)
        token = sessions.buat(nama, peran, id_akun=akun["id_akun"], path=sesi)
        assert sessions.ambil_principal_pendamping(
            token, path=sesi, path_akun=sandi
        ) is None

    token_lokal = sessions.buat(
        "guru", "guru", id_akun="akun_" + "e" * 32, path=sesi
    )
    sandi.unlink()
    assert sessions.ambil_principal_pendamping(
        token_lokal, path=sesi, path_akun=sandi
    ) is None


def test_case_username_tidak_membuat_id_kedua(berkas):
    sandi, _ = berkas
    auth.tambah_akun("Ortu", "sandi-awal-123", "guru", sandi)
    pertama = auth.cari_akun("ortu", sandi)["id_akun"]

    with pytest.raises(ValueError, match="sudah dipakai"):
        auth.tambah_akun("ORTU", "sandi-baru-456", "guru", sandi)

    assert auth.cari_akun("OrTu", sandi)["id_akun"] == pertama


def test_principal_mewajibkan_case_username_kanonik(berkas):
    sandi, sesi = berkas
    auth.tambah_akun("Ortu", "sandi-awal-123", "guru", sandi)
    akun = auth.cari_akun("ortu", sandi)
    salah_case = sessions.buat(
        "ortu", "guru", id_akun=akun["id_akun"], path=sesi
    )
    kanonik = sessions.buat(
        akun["pengguna"], "guru", id_akun=akun["id_akun"], path=sesi
    )

    assert sessions.ambil_principal_pendamping(
        salah_case, path=sesi, path_akun=sandi
    ) is None
    assert sessions.ambil_principal_pendamping(
        kanonik, path=sesi, path_akun=sandi
    ) is not None
