"""Template soal pola bilangan — fungsi atas parameter, bukan tabel literal.

Tiap template menghitung TIGA hal dari satu set parameter:

  1. teks soal
  2. kunci jawaban
  3. daftar malrule — jawaban salah yang bisa diprediksi + kode diagnosisnya

Poin (3) yang membuat bank soal ini berbeda dari daftar soal biasa. Karena
malrule ikut dihitung dari parameter, soal dengan angka baru tetap punya
tabel diagnosis yang sahih — tidak perlu ditulis ulang tiap generate.

Sumber malrule: latihan/2026-08-20-p3-pola-bilangan-PENILAIAN.md, yang
disusun dari bentuk soalnya. Sebagian belum diuji ke anak nyata; lihat
bagian "Perkiraan yang belum terverifikasi" di berkas itu.

Kode diagnosis (taksonomi B/K/H/E/T/N, Rencana Produk - Peta Jalan §02):
  B salah baca soal | K salah konsep | H salah hitung
  E salah tulis akhir | T tidak tahu | N menebak
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Level yang didukung, urut dari termudah.
#
# Dipakai sebagai daftar tertutup di banyak tempat (validasi form, profil
# parameter, komposisi lembar). Ditulis sekali di sini supaya menambah level
# tidak berarti berburu string "P3" di seluruh berkas.
LEVEL = ("P3", "P4", "P5", "P6")


def level_valid(level: str) -> bool:
    return level in LEVEL


@dataclass(frozen=True)
class Malrule:
    """Satu kesalahan yang bisa diprediksi dari bentuk soal."""

    id: str
    jawaban: str
    kode: str
    alasan: str


@dataclass(frozen=True)
class Soal:
    """Hasil render satu template dengan parameter tertentu."""

    template_id: str
    parameter: dict[str, Any]
    teks: str
    kunci: str
    malrule: tuple[Malrule, ...] = ()
    minta_restatement: bool = False
    bagian: str = ""
    tantangan: bool = False
    level: str = "P3"

    @property
    def tanda_tangan(self) -> str:
        """Sidik jari untuk mendeteksi soal duplikat di bank.

        Level ikut masuk, dan itu bukan hiasan: template yang sama dengan
        parameter yang sama bisa muncul di dua level (mis. `titik_segitiga`
        gambar_ke=12 sah di P3 maupun P4). Tanpa level di sidik jari,
        keduanya bertabrakan jadi satu baris bank, dan statistik "soal P5
        yang pernah dikerjakan" jadi tidak bisa dihitung.
        """
        butir = ",".join(f"{k}={self.parameter[k]}" for k in sorted(self.parameter))
        return f"{self.level}|{self.template_id}({butir})"


def _deret(awal: int, beda: int, n: int) -> list[int]:
    return [awal + beda * i for i in range(n)]


def saring_malrule(kunci: str, kandidat: list[Malrule]) -> tuple[Malrule, ...]:
    """Buang malrule yang tidak bisa membedakan benar dari salah.

    Dua penyakit yang disaring di sini, keduanya merusak diagnosis:

    1. **Malrule menebak jawaban yang BENAR.** Terjadi pada kasus tepi —
       mis. siklus dengan sisa 0: "ambil unsur terakhir siklus" kebetulan
       memberi jawaban yang sama dengan kunci. Kalau dibiarkan, anak yang
       menjawab benar tercatat punya miskonsepsi. Ini kerusakan terparah:
       laporan jadi tidak bisa dipercaya.

    2. **Dua malrule menebak jawaban yang sama.** Satu jawaban salah memetakan
       ke dua kode berbeda, dan sistem tidak punya dasar memilih — hasilnya
       tebakan yang menyamar sebagai diagnosis.

    Disaring terpusat, bukan di tiap template, supaya template baru otomatis
    ikut terlindungi tanpa penulisnya perlu ingat aturan ini.
    """
    bersih: list[Malrule] = []
    terpakai: set[str] = {kunci}
    for m in kandidat:
        if m.jawaban in terpakai:
            continue
        terpakai.add(m.jawaban)
        bersih.append(m)
    return tuple(bersih)



# ── Jalur kompatibilitas Fase A ─────────────────────────────────────────
#
# Konten di atas (Soal, Malrule, saring_malrule, LEVEL) tetap milik modul
# ini — dipakai semua topik. Konten KHAS pola bilangan (16 template,
# REGISTRI, komposisi lembar, susun_lembar) sudah pindah ke paket topik
# (topic_number_patterns.py). Akses lama `from templates import REGISTRI`
# dst. tetap bekerja lewat atribut-malas di bawah: dimuat sekali saat
# pertama kali disentuh, lalu di-cache.


_DARI_PAKET = frozenset(
    {"REGISTRI", "URUTAN_LEMBAR", "URUTAN_PER_LEVEL", "susun_lembar"}
)


def __getattr__(nama: str):
    # Dunder (mis. __path__ yang selalu ditanyakan sistem impor saat
    # `from templates import x`) ditolak bersih — melempar AttributeError
    # adalah kontrak yang diharapkan hasattr(). Menyentuh topik di sini
    # juga membentuk rekursi saat paket sedang mengimpor modul ini.
    if nama.startswith("__") or nama in _DARI_PAKET:
        if nama in _DARI_PAKET:
            import topics

            pb = topics.paket_bawaan()
            if nama == "REGISTRI":
                nilai: Any = topics.registri()
            elif nama == "URUTAN_PER_LEVEL":
                nilai = pb.komposisi
            elif nama == "URUTAN_LEMBAR":
                nilai = pb.komposisi_untuk("P3")
            else:
                nilai = pb.susun_lembar
            globals()[nama] = nilai
            return nilai
        raise AttributeError(
            f"modul {__name__!r} tidak punya atribut {nama!r}"
        )

    import topics

    gabungan = topics.registri()
    if nama in gabungan:
        nilai = gabungan[nama]
        globals()[nama] = nilai
        return nilai
    raise AttributeError(
        f"modul {__name__!r} tidak punya atribut {nama!r} — "
        "isi khas pola bilangan sudah pindah ke topic_number_patterns"
    )

