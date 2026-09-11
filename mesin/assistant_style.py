"""Gaya halaman Pendamping, seluruh warna dan ukuran dari design tokens."""

import design_tokens as T

GAYA_PENDAMPING = f"""
.pendamping-halaman *, .pendamping-halaman *::before, .pendamping-halaman *::after {{ box-sizing:border-box; }}
html, body.pendamping-halaman {{ max-width:100%; overflow-x:hidden; }}
.pendamping-halaman {{ min-height:100vh; margin:0; background:{T.LATAR_MURID}; color:{T.TEKS_JUDUL}; }}
.pendamping-bungkus {{ box-sizing:border-box; width:100%; max-width:58rem; margin:0 auto; padding:{T.SP_4}; overflow-wrap:anywhere; }}
.pendamping-kepala {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:{T.SP_3}; margin-bottom:{T.SP_5}; }}
.pendamping-kepala a {{ color:{T.AKSEN_TEAL_TUA}; font-weight:700; }}
.pendamping-panel {{ min-width:0; max-width:100%; overflow-wrap:anywhere; word-break:break-word; background:{T.LATAR_KARTU}; border:1px solid {T.BORDER_CATATAN}; border-radius:{T.RADIUS_KARTU}; padding:{T.SP_5}; }}
.pendamping-kepala nav {{ display:flex; flex-wrap:wrap; gap:{T.SP_3}; align-items:center; }}
.pendamping-kosong {{ min-height:55vh; display:grid; place-content:center; text-align:center; }}
.pendamping-kosong form {{ width:min(100%, 38rem); }}
.pendamping-label {{ display:block; font-weight:700; margin-bottom:{T.SP_2}; }}
.pendamping-input {{ box-sizing:border-box; width:100%; min-height:7rem; resize:vertical; border:1px solid {T.BORDER_KUAT}; border-radius:{T.RADIUS_SEDANG}; padding:{T.SP_3}; font:inherit; background:{T.LATAR_KARTU}; color:{T.TEKS_JUDUL}; }}
.pendamping-input-pendek {{ min-height:{T.TARGET_SENTUH}; }}
.pendamping-tombol {{ min-height:{T.TARGET_SENTUH}; border:0; border-radius:{T.RADIUS_KECIL}; padding:{T.SP_2} {T.SP_4}; background:{T.AKSEN_TEAL_TUA}; color:{T.TEKS_PUTIH}; font:inherit; font-weight:700; cursor:pointer; }}
.pendamping-tombol:focus-visible, .pendamping-input:focus-visible, .pendamping-halaman a:focus-visible {{ outline:3px solid {T.AKSEN_MURID_AMBER}; outline-offset:2px; }}
.pendamping-form {{ display:grid; min-width:0; gap:{T.SP_3}; margin-top:{T.SP_4}; }}
.pendamping-pesan {{ width:fit-content; max-width:100%; min-width:0; margin:{T.SP_3} 0; padding:{T.SP_3} {T.SP_4}; border-radius:{T.RADIUS_KARTU}; white-space:normal; overflow-wrap:anywhere; word-break:break-word; }}
.pendamping-pesan.pengguna {{ margin-left:auto; background:{T.LATAR_KARTU_SEKUNDER}; }}
.pendamping-pesan.asisten {{ background:{T.LATAR_KARTU}; border:1px solid {T.BORDER_CATATAN}; }}
.pendamping-pesan b {{ display:block; margin-bottom:{T.SP_2}; }}
.pendamping-riwayat {{ margin-bottom:{T.SP_4}; }}
.pendamping-riwayat summary {{ min-height:{T.TARGET_SENTUH}; display:flex; align-items:center; cursor:pointer; font-weight:700; }}
.pendamping-riwayat a {{ display:block; padding:{T.SP_2}; }}
.pendamping-galat {{ border-left:4px solid {T.AKSEN_MURID_KORAL}; padding:{T.SP_3}; background:{T.LATAR_KARTU}; }}
.pendamping-catatan {{ color:{T.TEKS_VARIAN}; font-size:1rem; line-height:1.5; }}
.pendamping-memori {{ margin:{T.SP_4} 0; display:grid; gap:{T.SP_2}; }}
.pendamping-memori form {{ display:grid; gap:{T.SP_2}; margin-top:{T.SP_3}; }}
@media (max-width: 40rem) {{
  .pendamping-bungkus {{ padding:{T.SP_3}; }}
  .pendamping-panel {{ padding:{T.SP_3}; }}
  .pendamping-kepala {{ align-items:flex-start; flex-direction:column; }}
}}
"""
