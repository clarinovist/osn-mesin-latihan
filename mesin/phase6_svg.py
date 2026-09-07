"""Pembungkus SVG deterministik untuk petak dan waktu."""
from __future__ import annotations

import hashlib
import html

import design_tokens as T


def bungkus_svg(isi, ringkasan, namespace, jenis):
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace visual wajib teks")
    try:
        ident = hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:20]
    except UnicodeError as galat:
        raise ValueError("namespace visual tidak valid") from galat
    ident = "visual-" + ident
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="soal-visual" '
        f'viewBox="0 0 {T.FASE6_LEBAR} {T.FASE6_TINGGI}" role="img" '
        f'aria-labelledby="{ident}-judul {ident}-uraian" '
        f'style="display:block;width:100%;max-width:{T.LEBAR_VISUAL_SOAL};height:auto;margin:{T.JARAK_VISUAL_SOAL} auto">'
        f'<title id="{ident}-judul">{html.escape(jenis)}</title>'
        f'<desc id="{ident}-uraian">{html.escape(ringkasan)}</desc>'
        f'{isi}</svg>'
    )
