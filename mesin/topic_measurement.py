"""Paket topik pengukuran — Fase 8 plan 30 Aug 2026.

Tiga template menutup cakupan pengukuran OSN SD yang belum tercakup Fase 4/6:
skala peta, satuan waktu lama, jam/menit/detik. Level P4/P5/P6 (P3 tidak).
"""

from __future__ import annotations

import random

from templates import Malrule, Soal, saring_malrule
from topics import Topik, daftarkan


# ── Bagian A — Skala peta ──────────────────────────────────────────────


def skala_peta(varian: str, sebenarnya: int, peta: int, skala: int) -> Soal:
    """Skala = peta:sebenarnya (cm:cm). Dua arah: cari skala, peta, atau sebenarnya."""
    # skala = peta:sebenarnya_cm — sebenarnya dalam km, konversi ke cm ×100.000
    sebenarnya_cm = sebenarnya * 100000
    if varian == "cari_skala":
        # skala = peta : sebenarnya_cm → sederhanakan
        kunci = f"1:{skala}"
        teks = (f"Jarak dua kota sebenarnya {sebenarnya} km. Pada peta "
                f"jaraknya {peta} cm. Berapa skala peta tersebut?")
        k_terbalik = f"{skala}:1"
        h = f"1:{skala + 1}"
        mal = [
            Malrule("skala.terbalik", k_terbalik, "K", "membalik skala — peta:sebenarnya bukan sebenarnya:peta"),
            Malrule("skala.lupa_km_ke_cm", f"1:{peta * sebenarnya}", "K", "lupa mengubah km ke cm (×100.000)"),
            Malrule("skala.kurang_satu", h, "H", "skala benar, meleset satu pada penyebut"),
        ]
    elif varian == "cari_peta":
        kunci = str(peta)
        # peta = sebenarnya_cm / skala
        teks = (f"Jarak dua kota sebenarnya {sebenarnya} km. Skala peta "
                f"1:{skala}. Berapa jarak pada peta (cm)?")
        k_terbalik = str(sebenarnya * 100000 // skala * skala)  # salah
        k_lupa = str(sebenarnya)  # lupa km→cm
        mal = [
            Malrule("skala.peta_terbalik", str(sebenarnya * 100000), "K", "menjawab jarak sebenarnya dalam cm, bukan jarak peta"),
            Malrule("skala.peta_lupa_km", k_lupa, "K", "lupa mengubah km ke cm"),
            Malrule("skala.peta_kurang_satu", str(peta - 1), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
    else:  # cari_sebenarnya
        kunci = str(sebenarnya)
        teks = (f"Jarak dua kota pada peta {peta} cm. Skala peta "
                f"1:{skala}. Berapa jarak sebenarnya (km)?")
        k_lupa_bagi = str(peta * skala)  # lupa ÷100.000
        k_terbalik = str(peta // skala)  # bagi dengan skala, bukan kali
        mal = [
            Malrule("skala.sebenarnya_lupa_bagi", k_lupa_bagi, "K", "menghitung peta×skala tanpa mengubah ke km"),
            Malrule("skala.sebenarnya_terbalik", k_terbalik, "K", "membagi dengan skala padahal harus dikali"),
            Malrule("skala.sebenarnya_kurang_satu", str(sebenarnya - 1), "H", "perhitungan benar, hasilnya meleset satu"),
        ]
    return Soal(
        "skala_peta",
        {"varian": varian, "sebenarnya": sebenarnya, "peta": peta, "skala": skala},
        teks,
        kunci,
        saring_malrule(kunci, mal),
        minta_restatement=True,
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Cocokkan dengan caramu sendiri, ya."
        ),
        bagian="A",
    )


# ── Bagian B — Waktu & konversi ────────────────────────────────────────


def satuan_waktu_lama(varian: str, nilai: int, hasil: int) -> Soal:
    """Konversi satuan waktu lama: abad, windu, lustrum, dasawarsa, tahun."""
    SATUAN = {
        "abad_ke_tahun": ("abad", "tahun", 100),
        "tahun_ke_abad": ("tahun", "abad", 1 / 100),
        "windu_ke_tahun": ("windu", "tahun", 8),
        "tahun_ke_windu": ("tahun", "windu", 1 / 8),
        "lustrum_ke_tahun": ("lustrum", "tahun", 5),
        "tahun_ke_lustrum": ("tahun", "lustrum", 1 / 5),
        "dasawarsa_ke_tahun": ("dasawarsa", "tahun", 10),
        "tahun_ke_dasawarsa": ("tahun", "dasawarsa", 1 / 10),
        "windu_ke_lustrum": ("windu", "lustrum", 8 / 5),
        "abad_ke_dasawarsa": ("abad", "dasawarsa", 10),
    }
    src, dst, faktor = SATUAN[varian]
    if faktor >= 1:
        kunci = str(int(nilai * faktor))
        teks = f"{nilai} {src} = berapa {dst}?"
        k_salah_arah = str(nilai // int(faktor)) if int(faktor) != 0 else "0"
        k_lupa = str(nilai)
    else:
        kunci = str(hasil)
        teks = f"{nilai} {src} = berapa {dst}?"
        k_salah_arah = str(nilai * int(1 / faktor))
        k_lupa = str(nilai)

    if k_salah_arah == kunci:
        k_salah_arah = str(int(kunci) + 1)
    if k_lupa == kunci or k_lupa == k_salah_arah:
        k_lupa = str(int(kunci) + 2)

    mal = [
        Malrule(f"waktu.salah_arah_{varian}", k_salah_arah, "K", "membalik arah konversi (dikali/dibagi yang salah)"),
        Malrule(f"waktu.lupa_{varian}", k_lupa, "K", "lupa mengkonversi — menjawab angka yang sama"),
        Malrule(f"waktu.kurang_satu", str(int(kunci) - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    return Soal(
        "satuan_waktu_lama",
        {"varian": varian, "nilai": nilai, "hasil": hasil},
        teks,
        kunci,
        saring_malrule(kunci, mal),
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Cocokkan dengan caramu sendiri, ya."
        ),
        bagian="B",
    )


def jam_menit_detik(varian: str, jam: int, menit: int, detik: int) -> Soal:
    """Konversi jam↔menit↔detik; varian durasi (jam:menit ke menit total)."""
    if varian == "jam_ke_menit":
        kunci = str(jam * 60)
        teks = f"{jam} jam = berapa menit?"
        k_terbalik = str(jam // 60)
        k_lupa = str(jam)
    elif varian == "menit_ke_jam":
        kunci = str(menit // 60)
        teks = f"{menit} menit = berapa jam?"
        k_terbalik = str(menit * 60)
        k_lupa = str(menit)
    elif varian == "menit_ke_detik":
        kunci = str(menit * 60)
        teks = f"{menit} menit = berapa detik?"
        k_terbalik = str(menit // 60)
        k_lupa = str(menit)
    elif varian == "detik_ke_menit":
        kunci = str(detik // 60)
        teks = f"{detik} detik = berapa menit?"
        k_terbalik = str(detik * 60)
        k_lupa = str(detik)
    elif varian == "jam_ke_detik":
        kunci = str(jam * 3600)
        teks = f"{jam} jam = berapa detik?"
        k_terbalik = str(jam // 3600)
        k_lupa = str(jam)
    elif varian == "detik_ke_jam":
        kunci = str(detik // 3600)
        teks = f"{detik} detik = berapa jam?"
        k_terbalik = str(detik * 3600)
        k_lupa = str(detik)
    elif varian == "durasi_ke_menit":
        kunci = str(jam * 60 + menit)
        teks = f"{jam} jam {menit} menit = berapa menit?"
        k_terbalik = str(jam + menit // 60)
        k_lupa = str(jam)
    else:  # durasi_ke_detik
        kunci = str(jam * 3600 + menit * 60 + detik)
        teks = f"{jam} jam {menit} menit {detik} detik = berapa detik?"
        k_terbalik = str(jam * 60 + menit)
        k_lupa = str(jam * 3600 + menit * 60)

    if k_terbalik == kunci:
        k_terbalik = str(int(kunci) + 1)
    if k_lupa == kunci or k_lupa == k_terbalik:
        k_lupa = str(int(kunci) + 2)

    mal = [
        Malrule(f"jam.terbalik_{varian}", k_terbalik, "K", "membalik arah konversi"),
        Malrule(f"jam.lupa_{varian}", k_lupa, "K", "lupa mengkonversi — menjawab angka yang sama"),
        Malrule(f"jam.kurang_satu", str(int(kunci) - 1), "H", "perhitungan benar, hasilnya meleset satu"),
    ]
    return Soal(
        "jam_menit_detik",
        {"varian": varian, "jam": jam, "menit": menit, "detik": detik},
        teks,
        kunci,
        saring_malrule(kunci, mal),
        pembahasan=(
            f"Langkah: jawaban benar = "
            + str(kunci)
            + ". Cocokkan dengan caramu sendiri, ya."
        ),
        bagian="B",
    )


# ── Registry ─────────────────────────────────────────────────────────────

REGISTRI_TOPIK = {
    "skala_peta": skala_peta,
    "satuan_waktu_lama": satuan_waktu_lama,
    "jam_menit_detik": jam_menit_detik,
}

KOMPOSISI = {
    "P4": (
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
        "satuan_waktu_lama", "jam_menit_detik",
    ),
    "P5": (
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta",
    ),
    "P6": (
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta", "satuan_waktu_lama", "jam_menit_detik",
        "skala_peta",
    ),
}

JUDUL_BAGIAN = {
    "A": "Bagian A — Skala peta",
    "B": "Bagian B — Waktu & konversi",
}

CATATAN_BAGIAN = {
    "A": "Skala = jarak peta : jarak sebenarnya. Ubah km ke cm dulu (×100.000).",
    "B": "1 abad=100 tahun, 1 windu=8 tahun, 1 lustrum=5 tahun, 1 dasawarsa=10 tahun.",
}


def _parameter(template_id: str, rng: random.Random, level: str) -> dict:
    if template_id == "skala_peta":
        varian = rng.choice(("cari_skala", "cari_peta", "cari_sebenarnya"))
        # pilih skala dan jarak peta yang menghasilkan jarak sebenarnya bulat
        skala = rng.choice((100000, 250000, 500000, 1000000, 2000000, 5000000))
        peta = rng.randint(1, 50)
        sebenarnya = peta * skala // 100000  # km
        return {"varian": varian, "sebenarnya": sebenarnya, "peta": peta, "skala": skala}
    if template_id == "satuan_waktu_lama":
        varian = rng.choice((
            "abad_ke_tahun", "tahun_ke_abad",
            "windu_ke_tahun", "tahun_ke_windu",
            "lustrum_ke_tahun", "tahun_ke_lustrum",
            "dasawarsa_ke_tahun", "tahun_ke_dasawarsa",
            "windu_ke_lustrum", "abad_ke_dasawarsa",
        ))
        if varian == "windu_ke_lustrum":
            # 1 windu = 8/5 lustrum = 1,6 lustrum
            # pilih n kelipatan 5 → n×8/5 bulat; rentang lebar supaya ≥200 combo
            nilai = rng.randint(1, 50) * 5
            hasil = nilai * 8 // 5
        elif varian == "abad_ke_dasawarsa":
            # 1 abad = 10 dasawarsa (integer)
            nilai = rng.randint(1, 50)
            hasil = nilai * 10
        elif varian in ("abad_ke_tahun", "windu_ke_tahun", "lustrum_ke_tahun", "dasawarsa_ke_tahun"):
            # besar → kecil: ×faktor (integer)
            faktor = {"abad_ke_tahun": 100, "windu_ke_tahun": 8, "lustrum_ke_tahun": 5, "dasawarsa_ke_tahun": 10}[varian]
            nilai = rng.randint(1, 100)
            hasil = nilai * faktor
        else:
            # kecil → besar: ÷faktor (integer). Pilih nilai kelipatan faktor.
            faktor = {"tahun_ke_abad": 100, "tahun_ke_windu": 8, "tahun_ke_lustrum": 5, "tahun_ke_dasawarsa": 10}[varian]
            nilai = rng.randint(1, 50) * faktor
            hasil = nilai // faktor
        return {"varian": varian, "nilai": nilai, "hasil": hasil}
    if template_id == "jam_menit_detik":
        varian = rng.choice((
            "jam_ke_menit", "menit_ke_jam",
            "menit_ke_detik", "detik_ke_menit",
            "jam_ke_detik", "detik_ke_jam",
            "durasi_ke_menit", "durasi_ke_detik",
        ))
        jam = rng.randint(1, 23)
        menit = rng.randint(0, 59)
        detik = rng.randint(0, 59)
        if varian in ("menit_ke_jam", "detik_ke_menit", "detik_ke_jam"):
            menit = rng.randint(60, 600)  # menit/detik besar untuk dibagi
            detik = rng.randint(60, 3600)
            jam = 1
        return {"varian": varian, "jam": jam, "menit": menit, "detik": detik}
    raise KeyError(f"template tidak dikenal: {template_id}")


TOPIK = Topik(
    id="pengukuran",
    nama="Pengukuran",
    judul_lembar="Latihan Pengukuran",
    judul_penilaian="Penilaian — Pengukuran",
    templates=REGISTRI_TOPIK,
    komposisi=KOMPOSISI,
    profil={"P4": {}, "P5": {}, "P6": {}},
    judul_bagian=JUDUL_BAGIAN,
    catatan_bagian=CATATAN_BAGIAN,
    parameter_untuk=_parameter,
)

daftarkan(TOPIK)