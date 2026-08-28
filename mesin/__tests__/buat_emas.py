"""Cetak emas identitas refactor Fase A: tanda tangan lembar dari kode LAMA.

Dibuat SEBELUM refactor paket topik (Task A1-A2). Setiap perubahan perilaku
— bukan sekadar pemindahan kode — harus mengubah angka di sini secara
sengaja, bukan diam-diam.

Regenerasi: python __tests__/buat_emas.py  (jalankan di kode pra-refactor,
lalu tempel hasilnya ke EMAS di __tests__/test_identitas_refactor.py).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import buat_lembar, buat_soal  # noqa: E402
from templates import LEVEL, REGISTRI  # noqa: E402

SEEDS = [1, 7, 42, 2026, 99999]
LEMBAR = {}
for level in LEVEL:
    for seed in SEEDS:
        LEMBAR[f"{level}|{seed}"] = buat_lembar(seed, level=level).tanda_tangan

SOAL = {}
for level in LEVEL:
    for tid in sorted(REGISTRI):
        SOAL[f"{level}|{tid}|7"] = buat_soal(tid, 7, level).tanda_tangan

emas = {"lembar": LEMBAR, "soal": SOAL}
print(json.dumps(emas, ensure_ascii=False, indent=1, sort_keys=True))
