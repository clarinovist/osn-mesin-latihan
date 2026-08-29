"""Ikon SVG inline untuk halaman murid.

Disimpan sebagai data-URI supaya tidak ada request HTTP tambahan —
halaman murid tetap satu berkas HTML yang bisa dibaca utuh offline.

Ikon:
  - OWL             : mascot owl dengan topung wisuda, aksen teal+amber
  - BOHLAM          : ikon petunjuk/instruksi
  - CHEVRON_KANAN   : panah kanan untuk kartu sesi
  - BINTANG_ICON    : star challenge (versi SVG, bukan karakter ★)
"""

from __future__ import annotations

import urllib.parse


_OWL = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" '
    'viewBox="0 0 48 48" fill="none">'
    # body
    '<circle cx="24" cy="26" r="18" fill="#0FA3A3"/>'
    # face
    '<circle cx="24" cy="22" r="14" fill="#FFF8EE"/>'
    # eyes
    '<circle cx="18" cy="22" r="5" fill="#fff" stroke="#16213e" stroke-width="1.5"/>'
    '<circle cx="30" cy="22" r="5" fill="#fff" stroke="#16213e" stroke-width="1.5"/>'
    '<circle cx="18" cy="22" r="2.5" fill="#16213e"/>'
    '<circle cx="30" cy="22" r="2.5" fill="#16213e"/>'
    # beak
    '<path d="M21 28 Q24 31 27 28" stroke="#16213e" stroke-width="1.5" '
    'fill="none" stroke-linecap="round"/>'
    # graduation cap
    '<path d="M14 14 L18 8 L30 8 L34 14 Z" fill="#16213e"/>'
    '<rect x="16" y="14" width="16" height="3" fill="#16213e"/>'
    '<circle cx="24" cy="6" r="2.5" fill="#FFB020"/>'
    # feet
    '<path d="M12 40 L14 36 M36 40 L34 36" stroke="#FFB020" '
    'stroke-width="2" stroke-linecap="round"/>'
    "</svg>"
)

_BOHLAM = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" '
    'viewBox="0 0 20 20" fill="none">'
    '<path d="M10 2 C6 2 3 5 3 9 C3 12 5 14 6 15 L6 17 L14 17 L14 15 '
    'C15 14 17 12 17 9 C17 5 14 2 10 2 Z" fill="#FFB020" '
    'stroke="#16213e" stroke-width="1"/>'
    '<rect x="7" y="17" width="6" height="2" rx="0.5" fill="#16213e"/>'
    "</svg>"
)

_CHEVRON_KANAN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 16 16" fill="none">'
    '<path d="M6 3 L11 8 L6 13" stroke="#99a" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg>"
)

_GEMBOK = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" '
    'viewBox="0 0 44 44" fill="none">'
    '<circle cx="22" cy="22" r="20" fill="#e4eef4"/>'
    '<rect x="14" y="20" width="16" height="13" rx="3" fill="#0FA3A3"/>'
    '<path d="M17 20 V16 C17 12 19 10 22 10 C25 10 27 12 27 16 V20" '
    'stroke="#0FA3A3" stroke-width="2.5" fill="none"/>'
    '<circle cx="22" cy="26" r="2" fill="#fff"/>'
    "</svg>"
)


def _data_uri(svg: str) -> str:
    """Bungkus SVG jadi data-URI yang aman untuk CSS background-image."""
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="")


OWL = _data_uri(_OWL)
BOHLAM = _data_uri(_BOHLAM)
CHEVRON_KANAN = _data_uri(_CHEVRON_KANAN)
GEMBOK = _data_uri(_GEMBOK)
