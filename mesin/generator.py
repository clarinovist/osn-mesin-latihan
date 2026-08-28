"""Generator lembar latihan — mesin umum, isi ditentukan paket topik.

Seed menentukan parameter, parameter menentukan soal. Sejak Fase A (registry
topik) generator TIDAK tahu apa-apa tentang pola bilangan: template, batas
angka, dan komposisi lembar datang dari paket topik (topik.py).

Kontrak determinisme yang diuji di __tests__/test_generator.py dan
__tests__/test_identitas_refactor.py:
  - seed sama + topik sama -> lembar identik (bisa dicetak ulang persis)
  - seed beda -> parameter beda (bank soal benar-benar tumbuh)
  - tiap malrule menghasilkan jawaban != kunci (kalau sama, malrule itu bug)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from templates import Soal
from topik import TOPIK_BAWAAN, Topik, ambil

LEVEL_BAWAAN = "P3"


def profil(level: str) -> dict:
    """Batas angka untuk satu level — milik paket topik sejak Fase A.

    Kontrak lama dipertahankan: level tak dikenal jatuh ke P3 (bukan
    exception), karena `siswa.tingkat` adalah kolom teks bebas yang sudah
    terisi di basis data produksi. Yang salah levelnya lebih baik daripada
    yang tidak ada lembarnya.
    """
    return paket_bawaan().profil_untuk(level)


def paket_bawaan() -> Topik:
    from topik import paket_bawaan as _paket_bawaan

    return _paket_bawaan()


@dataclass(frozen=True)
class Lembar:
    seed: int
    soal: tuple[Soal, ...]
    level: str = LEVEL_BAWAAN

    @property
    def tanda_tangan(self) -> str:
        return "|".join(s.tanda_tangan for s in self.soal)


def buat_lembar(
    seed: int,
    urutan: tuple[str, ...] | None = None,
    level: str = LEVEL_BAWAAN,
    topik: str = TOPIK_BAWAAN,
) -> Lembar:
    """Bangun satu lembar penuh dari seed. Deterministik.

    Urutan soal ditentukan level kalau tidak disebut eksplisit. Argumen
    `urutan` tetap ada supaya pemanggil bisa menyusun lembar khusus (mis.
    drill satu tipe), dan supaya test bisa memaksa komposisi tertentu.
    Topik tak dikenal melempar KeyError — salah ketik id topik adalah bug
    pemanggil, bukan data produksi yang perlu dimaafkan.
    """
    paket = ambil(topik)
    rng = random.Random(seed)
    if urutan is None:
        urutan = paket.komposisi_untuk(level)
    soal = tuple(_soal_layak(paket, t, rng, level) for t in urutan)
    return Lembar(seed=seed, soal=soal, level=level)


def _soal_layak(
    paket: Topik,
    template_id: str,
    rng: random.Random,
    level: str = LEVEL_BAWAAN,
    batas: int = 40,
) -> Soal:
    """Ambil parameter sampai dapat soal yang benar-benar bisa mendiagnosis.

    Beberapa kombinasi parameter menghasilkan soal yang sah tapi tumpul:
    seluruh malrule-nya bertabrakan dengan kunci atau satu sama lain, lalu
    dibuang oleh `saring_malrule`. Sisanya soal tanpa satu pun jalur
    diagnosis — anak tetap harus mengerjakannya, tapi jawaban salahnya tidak
    memberi tahu apa-apa. Itu beban menulis tanpa imbalan informasi.

    Contoh nyata: siklus huruf 'CBC' dengan posisi kelipatan 3. Kunci 'C',
    dan "ambil unsur terakhir siklus" juga 'C' — satu-satunya malrule
    terbuang, soal jadi kosong.

    Karena rng dipakai berurutan, penolakan tetap deterministik: seed yang
    sama menghasilkan lembar yang sama.
    """
    if paket.parameter_untuk is None:
        raise RuntimeError(
            f"topik {paket.id!r} tidak mendefinisikan parameter_untuk — "
            "paket tidak bisa menghasilkan soal"
        )
    for _ in range(batas):
        soal = paket.templates[template_id](
            **paket.parameter_untuk(template_id, rng, level)
        )
        if soal.malrule:
            # Level ditempelkan di sini, bukan di dalam template: definisi
            # soal tidak perlu tahu untuk siapa ia dipakai. Pemisahan yang
            # sama dengan alasan generator.py terpisah dari templates.py.
            return replace(soal, level=level)
    raise RuntimeError(
        f"{template_id}: {batas} percobaan tanpa satu pun malrule bertahan — "
        "periksa definisi malrule template ini"
    )


def buat_soal(
    template_id: str,
    seed: int,
    level: str = LEVEL_BAWAAN,
    topik: str = TOPIK_BAWAAN,
) -> Soal:
    """Satu soal saja — untuk menambal bank soal per tipe."""
    return _soal_layak(ambil(topik), template_id, random.Random(seed), level)
