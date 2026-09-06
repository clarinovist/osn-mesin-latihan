"""Origin privat sah tanpa membuka formulir lintas situs."""
import io
import urllib.parse
from email import message_from_string
from types import SimpleNamespace

import pytest

import interventions
from learning_cycle_http import GalatForm, _baca_form
from test_learning_cycle_http import (
    server, _buat_sesi_rencana_awal, _payload_benar, _siapkan_putaran_fokus,
)
from test_learning_cycle_routes import _post


@pytest.mark.parametrize("asal,situs,sah", [
    ("null", "same-origin", True),
    ("null", None, False),
    ("null", "", False),
    ("null", "same-site", False),
    ("null", "cross-site", False),
    ("null", "none", False),
    ("null", "same-origin, cross-site", False),
    ("null", "Same-Origin", False),
    ("https://osn.example", "same-origin", True),
    ("https://osn.example", None, True),
    ("https://osn.example", "cross-site", False),
    ("https://asing.invalid", "same-origin", False),
    ("https://asing.invalid", None, False),
    ("https://osn.example:444", "same-origin", False),
    (None, None, True),
    (None, "cross-site", False),
])
def test_matriks_asal_formulir(asal, situs, sah):
    tajuk = {"Host": "osn.example", "Content-Length": "0",
             "Content-Type": "application/x-www-form-urlencoded"}
    tambahan = {k: v for k, v in (("Origin", asal), ("Sec-Fetch-Site", situs))
                if v is not None}
    pesan = "\n".join(f"{k}: {v}" for k, v in {**tajuk, **tambahan}.items())
    penangan = SimpleNamespace(headers=message_from_string(pesan), rfile=io.BytesIO())
    if sah:
        assert _baca_form(penangan) == {}
    else:
        with pytest.raises(GalatForm, match="berasal dari situs ini") as galat:
            _baca_form(penangan)
        assert galat.value.status == 403


def _siapkan_aksi(kon, ids, aksi):
    """Payload sah dan kueri bukti untuk masing-masing jalur HTTP."""
    siswa = ids["siswa_buat"]
    sesi = ids["sesi_a"]
    if aksi == "buat":
        return (f"/siklus/{siswa}/buat", {},
                "SELECT COUNT(*) FROM sesi WHERE siswa_id = ?", (siswa,))
    if aksi == "konfirmasi":
        _, data = _payload_benar(kon, sesi)
        return (f"/sesi/{sesi}/konfirmasi", data,
                "SELECT COUNT(*) FROM snapshot_outcome", ())
    if aksi == "batalkan":
        sesi = _buat_sesi_rencana_awal(kon, siswa)
        return (f"/sesi/{sesi}/batalkan", {"alasan": "uji asal formulir"},
                "SELECT COUNT(*) FROM sesi WHERE id = ? AND dibatalkan IS NOT NULL",
                (sesi,))
    putaran, fokus = _siapkan_putaran_fokus(kon, siswa)
    pendekatan = interventions.pilihan_untuk_fokus(fokus)[0].pendekatan_id
    data = {"aksi": "intervensi_selesai", "putaran_id": str(putaran),
            "template_id": fokus[0], "kode_intervensi": fokus[1],
            "malrule_id": "", "pendekatan_id": pendekatan}
    return (f"/siklus/{siswa}/aksi", data,
            "SELECT COUNT(*) FROM kejadian_belajar WHERE jenis = 'intervensi_selesai'",
            ())


@pytest.mark.parametrize("aksi", ["buat", "konfirmasi", "batalkan", "aksi"])
def test_asal_privat_same_origin_menyimpan_hasil(server, aksi):
    s, ids = server
    with s.buka() as kon:
        jalur, data, kueri, parameter = _siapkan_aksi(kon, ids, aksi)
        assert kon.execute(kueri, parameter).fetchone()[0] == 0
    kode, _, tajuk = _post(s, jalur, urllib.parse.urlencode(data).encode(),
                          {"Origin": "null", "Sec-Fetch-Site": "same-origin"})
    assert kode == 303
    assert tajuk["Location"].startswith(("/sesi/", "/anak/"))
    with s.buka() as kon:
        assert kon.execute(kueri, parameter).fetchone()[0] == 1


@pytest.mark.parametrize("aksi", ["buat", "konfirmasi", "batalkan", "aksi"])
@pytest.mark.parametrize("tajuk", [
    {"Origin": "null"},
    {"Origin": "null", "Sec-Fetch-Site": "same-site"},
    {"Origin": "null", "Sec-Fetch-Site": "cross-site"},
    {"Origin": "null", "Sec-Fetch-Site": "none"},
    {"Origin": "https://asing.invalid", "Sec-Fetch-Site": "same-origin"},
    {"Sec-Fetch-Site": "cross-site"},
])
def test_asal_tidak_sah_tanpa_mutasi(server, aksi, tajuk):
    s, ids = server
    with s.buka() as kon:
        jalur, data, _, _ = _siapkan_aksi(kon, ids, aksi)
        sebelum = tuple(kon.iterdump())
    kode, isi, _ = _post(s, jalur, urllib.parse.urlencode(data).encode(), tajuk)
    assert kode == 403
    assert "Permintaan harus berasal dari situs ini." in isi
    with s.buka() as kon:
        assert tuple(kon.iterdump()) == sebelum
