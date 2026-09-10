"""Bingkai presentasional untuk pesan singkat; tanpa akses data atau routing."""

import html

import brand
import design_tokens as T
from style_stitch import gaya_stitch


def halaman_pesan(judul: str, isi: str) -> bytes:
    """Bungkus markup tepercaya dari router tanpa mengubah pesan atau aksinya.

    ``isi`` sudah di-escape oleh pemanggil bila memuat nilai dinamis. Tidak
    menambah tautan: kapabilitas halaman token tetap terbatas pada sesi itu.
    Input sama menghasilkan body identik, termasuk semua jalur 404.
    """
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(brand.judul(judul))}</title>
{brand.tag_kepala()}<style>{gaya_stitch()}</style></head>
<body class="st"><main class="pesan-editorial-st">
<header class="pesan-brand-st">{brand.mark("topbar")}<span>{html.escape(T.NAMA_PRODUK)}</span></header>
<section class="pesan-catatan-st">
<p class="pesan-alis-st">CATATAN DARI {html.escape(T.NAMA_PRODUK.upper())}</p>
{isi}
</section>
</main></body></html>""".encode()
