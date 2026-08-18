#!/usr/bin/env bash
# Jalankan seluruh test spike. Nol panggilan API, nol dependency jaringan.
#
#   bash spike/test.sh
#
# Butuh .venv (pyyaml + pillow) dan node. Lihat requirements.txt.
set -euo pipefail

cd "$(dirname "$0")"

PY=./.venv/bin/python
if [ ! -x "$PY" ]; then
  echo "⛔ .venv belum ada. Buat dulu:"
  echo "   python3 -m venv spike/.venv && spike/.venv/bin/pip install -r spike/requirements.txt"
  exit 1
fi

echo "=== toSamples + koalisi + verdict (JS) ==="
node toSamples.test.js

echo
echo "=== render.py — hitung_turunan + render 10 soal ==="
"$PY" render_test.py

echo
echo "=== tahap_a.py — malrule deterministik ==="
"$PY" tahap_a.py

echo
echo "=== tinta_heuristik.py — Tahap B baseline (Hari 4 pagi) ==="
"$PY" tinta_heuristik_test.py

echo
echo "=== tinta_llm.py — prompt, skema, cache (Hari 4 sore) ==="
"$PY" tinta_llm_test.py

echo
echo "Semua test spike hijau."
