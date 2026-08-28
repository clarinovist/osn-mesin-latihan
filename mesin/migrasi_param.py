"""Migrasi parameter JSON murni (A4): bentuk lama → list, sekali jalan.

Kontrak bank soal sampai Fase A4: parameter berstruktur disimpan sebagai
string per-template ("ABCC" / "hijau,kuning" / "2,3,4"), lalu dibongkar
lagi di web._soal_dari_baris dengan cabang `if template_id`. Template baru
dengan parameter berstruktur harus MENAMBAH cabang itu untuk bisa
direstorasi — dan yang lupa tidak gagal saat test, tapi saat halaman guru
menampilkan soal yang salah.

Kontrak baru: parameter tersimpan apa adanya (list = list). Restorasi
`REGISTRI[id](**json.loads(parameter))` tunggal tanpa cabang.

Migrasi mengubah HANYA bentuk, tidak pernah nilai:

  - `pola` string gabung ("ABCC")       → ["A", "B", "C", "C"]
  - `pola` string koma ("hijau,kuning") → ["hijau", "kuning"]
  - `pola` string koma angka ("2,3,4")  → [2, 3, 4]

tanda_tangan dihitung ulang (bentuk parameter ikut di dalamnya), dan kunci
lama diverifikasi tetap sama dengan rekonstruksi dari bentuk baru sebelum
baris ditulis ulang. Baris yang tidak bisa diverifikasi MENGHENTIKAN
migrasi dengan pengecualian — bank soal adalah data diagnosis, bukan data
yang boleh ditulis ulang diam-diam.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable

from templates import REGISTRI

# Template dengan parameter `pola` berstruktur yang tersimpan sebagai
# string. Dua rasa bentuk lama: gabung tanpa pemisah (huruf) dan koma
# (warna/angka). Dipetakan eksplisit — bukan tebakan.
_BENTUK_LAMA: dict[str, Callable[[str], list]] = {
    "siklus_huruf": lambda p: list(str(p)),
    "siklus_warna": lambda p: str(p).split(","),
    "jumlah_siklus": lambda p: [int(x) for x in str(p).split(",")],
    "sisa_bagi_siklus": lambda p: list(str(p)),
}

# Id template berklausul — dipakai test untuk memastikan seed uji
# benar-benar mewakili semua bentuk lama yang dimigrasi.
KLAUSUL: tuple[str, ...] = tuple(_BENTUK_LAMA)


def _tanda_tangan(level: str, template_id: str, parameter: dict) -> str:
    """Format tanda_tangan — aturan yang sama dengan Soal.tanda_tangan."""
    butir = ",".join(f"{k}={parameter[k]}" for k in sorted(parameter))
    return f"{level}|{template_id}({butir})"


def jalankan(kon: sqlite3.Connection) -> int:
    """Migrasi sekali-jalan, idempoten. Kembalikan jumlah baris diubah.

    Seluruh verifikasi dilakukan SEBELUM satu UPDATE pun dijalankan: kalau
    satu baris pun tidak cocok, pengecualiannya naik tanpa ada yang
    tertulis — pemanggil memutus transaksi, bank tetap utuh.
    """
    baris_baris = kon.execute(
        f"""SELECT id, template_id, parameter, kunci, level FROM soal
            WHERE template_id IN ({",".join("?" for _ in _BENTUK_LAMA)})""",
        tuple(_BENTUK_LAMA),
    ).fetchall()

    rencana: list[tuple[int, str, str]] = []
    for b in baris_baris:
        param = json.loads(b["parameter"])
        if not isinstance(param.get("pola"), str):
            continue  # sudah bentuk baru — inilah yang membuatnya idempoten

        param_baru = dict(param)
        param_baru["pola"] = _BENTUK_LAMA[b["template_id"]](param["pola"])

        # Verifikasi: bangun ulang soal dari bentuk baru. Kuncinya WAJIB
        # sama dengan yang tersimpan — kalau beda, datanya sudah melenceng
        # dari definisi template dan menulis ulang justru menutup jejaknya.
        soal = REGISTRI[b["template_id"]](**param_baru)
        if soal.kunci != b["kunci"]:
            raise AssertionError(
                f"soal id {b['id']} ({b['template_id']}): kunci bank "
                f"{b['kunci']!r} != kunci rekonstruksi {soal.kunci!r} — "
                "migrasi dihentikan, tidak ada yang ditulis"
            )

        rencana.append(
            (
                b["id"],
                json.dumps(param_baru, ensure_ascii=False, sort_keys=True),
                _tanda_tangan(b["level"], b["template_id"], param_baru),
            )
        )

    for soal_id, parameter_baru, tt_baru in rencana:
        kon.execute(
            "UPDATE soal SET parameter = ?, tanda_tangan = ? WHERE id = ?",
            (parameter_baru, tt_baru, soal_id),
        )
    return len(rencana)
