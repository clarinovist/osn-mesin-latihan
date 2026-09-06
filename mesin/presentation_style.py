"""Gaya penyajian pertanyaan bersama untuk layar dan cetak."""
import design_tokens as T

GAYA_PENYAJIAN = f"""
[data-fingerprint-penyajian] {{ min-width: 0; overflow-wrap: anywhere; }}
[data-fingerprint-penyajian] svg {{
  display: block; width: {T.LEBAR_VISUAL_SOAL}; max-width: 100%; height: auto;
  margin: {T.JARAK_VISUAL_SOAL} auto;
}}
"""
