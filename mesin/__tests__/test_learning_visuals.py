"""Bantuan pola statis terpisah dari snapshot pertanyaan dan ID lama."""

from dataclasses import FrozenInstanceError, fields
import importlib
import importlib.util
from xml.etree import ElementTree as Pohon

import pytest

import design_tokens as T
import interventions
import rumus
from visual_contract import DescriptorVisual, PenyajianPertanyaan, buat_penyajian
from visual_renderer import render_pertanyaan


@pytest.fixture
def modul():
    assert importlib.util.find_spec("learning_visuals") is not None, (
        "Modul bantuan belajar terpisah belum tersedia"
    )
    return importlib.import_module("learning_visuals")


def _akar(modul, jenis="korek", konteks="hasil_sah", namespace="uji-bantuan"):
    return Pohon.fromstring(modul.render_bantuan(
        modul.BantuanVisual(jenis), konteks=konteks, namespace=namespace,
    ))


def _elemen(akar, nama):
    return tuple(akar.iter("{http://www.w3.org/2000/svg}" + nama))


@pytest.mark.parametrize("jenis", ("korek", "titik"))
def test_model_beku_hanya_jenis_dan_versi(modul, jenis):
    bantuan = modul.BantuanVisual(jenis)
    assert tuple(bagian.name for bagian in fields(bantuan)) == ("jenis", "versi")
    assert bantuan.versi == 1
    assert not isinstance(bantuan, (DescriptorVisual, PenyajianPertanyaan))
    assert hash(bantuan) == hash(modul.BantuanVisual(jenis))
    with pytest.raises(FrozenInstanceError):
        bantuan.jenis = "titik"
    with pytest.raises(FrozenInstanceError):
        bantuan.versi = 2


@pytest.mark.parametrize("jenis", (None, True, 1, [], {}, "", "Korek", "titik ",
                                  '<svg onload="bahaya()">', "kоrek"))
def test_model_menolak_jenis_tidak_valid(modul, jenis):
    with pytest.raises(ValueError):
        modul.BantuanVisual(jenis)


@pytest.mark.parametrize("versi", (None, True, False, 1.0, "1", 0, 2, [], {}))
def test_model_menolak_versi_tidak_valid(modul, versi):
    with pytest.raises(ValueError):
        modul.BantuanVisual("korek", versi)


@pytest.mark.parametrize("nama", ("parameter", "soal", "kunci", "markup"))
def test_model_tidak_menerima_muatan_soal_atau_markup(modul, nama):
    with pytest.raises(TypeError):
        modul.BantuanVisual("korek", **{nama: "muatan"})


@pytest.mark.parametrize("jenis", ("korek", "titik"))
def test_bantuan_ditolak_jalur_pertanyaan_dan_descriptor(modul, jenis):
    bantuan = modul.BantuanVisual(jenis)
    with pytest.raises(ValueError):
        render_pertanyaan(bantuan)
    with pytest.raises(ValueError):
        DescriptorVisual(jenis, 1, bantuan)
    with pytest.raises(ValueError):
        DescriptorVisual(jenis, 1, {"n_tampil": bantuan})
    with pytest.raises(ValueError):
        buat_penyajian(
            template_id="titik_segitiga", level="P3", parameter={},
            teks_soal="Amati pola.", bagian_soal="A", tantangan_soal=False,
            minta_restatement=False, asal_teks="bawaan", status_visual="siap",
            mode_representasi=jenis + "-v1", descriptor=bantuan,
        )


@pytest.mark.parametrize("nilai", (None, "korek", {}, True,
                                  DescriptorVisual("titik", 1, {"n_tampil": 4})))
def test_renderer_menolak_objek_lain(modul, nilai):
    with pytest.raises(ValueError):
        modul.render_bantuan(nilai, konteks="hasil_sah", namespace="uji")


@pytest.mark.parametrize("konteks", ("evaluasi", "checkpoint", "drill", "penguatan",
                                    "latihan_terbimbing", "hasil", "", None, [], {}, True))
def test_konteks_terlarang_ditolak(modul, konteks):
    with pytest.raises(ValueError):
        modul.render_bantuan(modul.BantuanVisual("korek"), konteks=konteks, namespace="uji")


@pytest.mark.parametrize("jenis", ("korek", "titik"))
@pytest.mark.parametrize("konteks", ("hasil_sah", "pelajari_bersama"))
def test_konteks_sah_memiliki_marker_dan_tanpa_diagnosis(modul, jenis, konteks):
    akar = _akar(modul, jenis, konteks)
    assert "bantuan-visual" in akar.attrib["class"].split()
    assert akar.attrib["data-bantuan-visual"] == jenis
    assert len(_elemen(akar, "svg")) == 1
    teks = Pohon.tostring(akar, encoding="unicode")
    assert all(larangan not in teks for larangan in (
        "pendekatan_id", "diagnosis", "malrule", "data-fingerprint-penyajian",
    ))


@pytest.mark.parametrize("namespace", (None, True, 1, [], {}, "", "\ud800"))
def test_namespace_invalid_ditolak_helper_svg(modul, namespace):
    with pytest.raises(ValueError):
        _akar(modul, namespace=namespace)


@pytest.mark.parametrize("jenis", ("korek", "titik"))
def test_namespace_jahat_tidak_menjadi_event_atau_jaringan(modul, jenis):
    muatan = '\"><image href="https://jahat.invalid" onload="bahaya()"/><script>x</script>'
    akar = _akar(modul, jenis, namespace=muatan)
    teks = Pohon.tostring(akar, encoding="unicode")
    assert "jahat.invalid" not in teks and "bahaya" not in teks
    assert {elemen.tag.split("}")[-1] for elemen in akar.iter()} <= {
        "div", "p", "svg", "title", "desc", "g", "line", "circle", "text",
    }
    assert all(not nama.lower().startswith("on") and "href" not in nama
               for elemen in akar.iter() for nama in elemen.attrib)
    assert "url(" not in teks and "javascript:" not in teks
    gambar = _elemen(akar, "svg")[0]
    identitas = {elemen.attrib["id"] for elemen in akar.iter() if "id" in elemen.attrib}
    assert set(gambar.attrib["aria-labelledby"].split()) == identitas
    assert Pohon.tostring(akar) == Pohon.tostring(_akar(modul, jenis, namespace=muatan))
    akar_lain = _akar(modul, jenis, namespace="lain")
    identitas_lain = {elemen.attrib["id"] for elemen in akar_lain.iter() if "id" in elemen.attrib}
    assert identitas.isdisjoint(identitas_lain)


def _ruas(gambar):
    return tuple(((float(garis.attrib["x1"]), float(garis.attrib["y1"])),
                  (float(garis.attrib["x2"]), float(garis.attrib["y2"])))
                 for garis in _elemen(gambar, "line"))


def test_korek_jumlah_geometri_sambungan_dan_tambahan_tebal(modul):
    akar = _akar(modul)
    gambar = _elemen(akar, "g")
    assert len(gambar) == 4
    assert tuple(len(_ruas(satu)) for satu in gambar) == (4, 7, 10, 13)
    for indeks, satu in enumerate(gambar):
        ruas = _ruas(satu)
        assert len(set(ruas)) == len(ruas)
        assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == T.POLA_RUAS
                   for a, b in ruas)
        assert all(awal[1] == lanjut[0] for awal, lanjut in zip(ruas, ruas[1:]))
        sambungan = {(float(titik.attrib["cx"]), float(titik.attrib["cy"]))
                     for titik in _elemen(satu, "circle")}
        assert sambungan == {ujung for pasangan in ruas for ujung in pasangan}
        tebal = tuple(float(garis.attrib["stroke-width"])
                      for garis in _elemen(satu, "line"))
        jumlah_lama = len(_ruas(gambar[indeks - 1])) if indeks else len(ruas)
        assert tebal == (T.POLA_GARIS,) * jumlah_lama + (T.POLA_TEBAL,) * (len(ruas) - jumlah_lama)
        if indeks:
            assert ruas[:jumlah_lama] == _ruas(gambar[indeks - 1])
    teks = " ".join(akar.itertext())
    assert "3 kali penambahan" in teks
    assert "4 + 3 × 3 = 13" in teks
    assert "4 kali penambahan" not in teks
    assert "Contoh" in teks and "batang baru" in teks


def test_titik_jumlah_geometri_baris_baru_dan_bukan_beda_tetap(modul):
    akar = _akar(modul, "titik")
    gambar = _elemen(akar, "g")
    assert len(gambar) == 4
    assert tuple(len(_elemen(satu, "circle")) for satu in gambar) == (1, 3, 6, 10)
    for nomor, satu in enumerate(gambar, 1):
        titik = _elemen(satu, "circle")
        posisi = {(float(satu.attrib["cx"]), float(satu.attrib["cy"])) for satu in titik}
        assert len(posisi) == len(titik)
        for baris in range(nomor):
            ordinat = T.POLA_TITIK_ATAS + baris * T.POLA_TITIK_JARAK
            absis = sorted(x for x, y in posisi if y == ordinat)
            assert len(absis) == baris + 1
            assert sum(absis) / len(absis) == T.POLA_SEL_LEBAR / 2
            assert all(b - a == T.POLA_TITIK_JARAK for a, b in zip(absis, absis[1:]))
        baru = tuple(satu for satu in titik if satu.attrib["fill"] == T.LATAR_KARTU)
        assert len(baru) == nomor
        assert all(float(satu.attrib["cy"]) == T.POLA_TITIK_ATAS + (nomor - 1) * T.POLA_TITIK_JARAK
                   for satu in baru)
        assert all(satu.attrib["stroke"] == T.TEKS_UTAMA for satu in titik)
    teks = " ".join(akar.itertext())
    assert "1 + 2 + 3 + 4 = 10" in teks
    assert "baris baru" in teks and "bukan beda tetap" in teks
    assert "Contoh" in teks


@pytest.mark.parametrize("jenis", ("korek", "titik"))
def test_geometri_dan_label_memakai_token_dalam_area_svg(modul, jenis):
    akar = _akar(modul, jenis)
    assert _elemen(akar, "svg")[0].attrib["viewBox"] == f"0 0 {T.POLA_LEBAR} {T.POLA_TINGGI}"
    for indeks, gambar in enumerate(_elemen(akar, "g")):
        assert gambar.attrib["transform"] == (
            f"translate({(indeks % 2) * T.POLA_SEL_LEBAR} {(indeks // 2) * T.POLA_SEL_TINGGI})"
        )
        for awal, akhir in _ruas(gambar):
            assert all(0 < x < T.POLA_SEL_LEBAR and 0 < y < T.POLA_LABEL_Y
                       for x, y in (awal, akhir))
        for titik in _elemen(gambar, "circle"):
            radius = float(titik.attrib["r"])
            assert radius < float(titik.attrib["cx"]) < T.POLA_SEL_LEBAR - radius
            assert radius < float(titik.attrib["cy"]) < T.POLA_LABEL_Y - radius
        label = _elemen(gambar, "text")
        assert label and any(f"Gambar {indeks + 1}" in (satu.text or "") for satu in label)
        assert all(float(satu.attrib["font-size"]) == T.POLA_FONT for satu in label)
        assert all(float(satu.attrib["y"]) < T.POLA_SEL_TINGGI for satu in label)


@pytest.mark.parametrize("template_id,jenis", (("korek_api", "korek"), ("titik_segitiga", "titik")))
def test_kartu_pola_khusus_tidak_berbagi_kartu_beda_tetap(template_id, jenis):
    kartu = rumus.kartu_untuk(template_id)
    assert kartu is not None and kartu.bantuan is not None
    assert rumus.KONSEP_TEMPLATE[template_id] != "pola_bilangan"
    assert kartu.bantuan.jenis == jenis and kartu.bantuan.versi == 1
    assert "<svg" not in kartu.inti + kartu.contoh
    with pytest.raises(FrozenInstanceError):
        setattr(kartu, "bantuan", None)
    if jenis == "korek":
        assert "3 kali" in kartu.contoh
        assert "4 + 3 × 3 = 13" in kartu.contoh
    else:
        assert "baris" in kartu.inti
        assert "1 + 2 + 3 + 4 = 10" in kartu.contoh
        assert "7, 11, 15" not in kartu.contoh


def test_kartu_lain_tidak_diberi_bantuan_dan_deduplikasi_konsep_tetap():
    target = {rumus.KONSEP_TEMPLATE[nama] for nama in ("korek_api", "titik_segitiga")}
    assert all(kartu.bantuan is None for nama, kartu in rumus.KARTU.items() if nama not in target)
    assert rumus.KARTU["pola_bilangan"].contoh == "7, 11, 15, … beda 4 → berikutnya 15 + 4 = 19."
    kartu = rumus.kartu_untuk_banyak(("korek_api", "titik_segitiga", "deret_aritmetika", "korek_api"))
    assert len(kartu) == 3


@pytest.mark.parametrize("template_id,jenis", (("korek_api", "korek"), ("titik_segitiga", "titik")))
@pytest.mark.parametrize("malrule_id", (None, "m1", "m2"))
def test_id_visual_baru_pertama_dan_id_lama_tetap_tanpa_bantuan(template_id, jenis, malrule_id):
    kunci = (template_id, "K", malrule_id)
    pilihan = interventions.pilihan_untuk_fokus(kunci)
    akhiran = f"{template_id}:{malrule_id or 'umum'}"
    assert tuple(satu.pendekatan_id for satu in pilihan) == (
        f"visual-pola-v1:{akhiran}", f"konsep:{akhiran}", f"jelaskan-balik:{akhiran}",
    )
    kartu = rumus.kartu_untuk(template_id)
    assert kartu is not None and pilihan[0].bantuan is not None
    assert pilihan[0].bantuan.jenis == jenis
    assert pilihan[0].bantuan == kartu.bantuan
    assert all(satu.tersedia for satu in pilihan)
    assert pilihan[1] == interventions.untuk_fokus(kunci)
    assert all(satu.bantuan is None for satu in pilihan[1:])
    with pytest.raises(FrozenInstanceError):
        setattr(pilihan[0], "bantuan", None)


@pytest.mark.parametrize("kode,pendekatan", (
    ("B", "baca-tandai-ulang"), ("H", "tulis-periksa"),
    ("E", "cocokkan-jawaban-akhir"), ("N", "jelaskan-asal-jawaban"),
    ("T", "kenalkan-contoh-awal"),
))
@pytest.mark.parametrize("template_id", ("korek_api", "titik_segitiga", "deret_aritmetika"))
def test_kode_bhent_tidak_berubah(template_id, kode, pendekatan):
    lama = interventions.untuk_fokus(("deret_aritmetika", kode, None))
    pilihan = interventions.pilihan_untuk_fokus((template_id, kode, "m1"))
    assert pilihan == (lama,)
    assert pilihan[0].pendekatan_id == pendekatan
    assert pilihan[0].bantuan is None


def test_pilihan_k_lain_dan_k_tidak_tersedia_tetap():
    kunci = ("deret_aritmetika", "K", None)
    pilihan = interventions.pilihan_untuk_fokus(kunci)
    assert tuple(satu.pendekatan_id for satu in pilihan) == (
        "konsep:deret_aritmetika:umum", "jelaskan-balik:deret_aritmetika:umum",
    )
    assert all(satu.bantuan is None for satu in pilihan)
    kosong = interventions.pilihan_untuk_fokus(("tak_ada", "K", None))
    assert len(kosong) == 1 and not kosong[0].tersedia and kosong[0].bantuan is None
    with pytest.raises(ValueError):
        interventions.pilihan_untuk_fokus(("korek_api", "X", None))
