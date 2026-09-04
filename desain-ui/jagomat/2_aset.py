import pathlib
D = pathlib.Path(__file__).resolve().parent
raw = (D / "_wordmark_raw.txt").read_text().splitlines()
LEBAR, CAP, UPM = float(raw[0]), float(raw[1]), float(raw[2])
GLYPHS = "\n    ".join(raw[3:])

HEAD = '<svg xmlns="http://www.w3.org/2000/svg"'

# Mark: coretan -> garis lurus. Dua varian, sesuai sistem dua-mark.
MARK_SIMPLE = (
    '<path d="M6 30 C 10 18, 15 18, 19 27 C 22 34, 26 32, 28 26" '
    'stroke="{c}" stroke-width="6" stroke-linecap="round" '
    'stroke-linejoin="round"/>'
    '<path d="M30 24 H 42" stroke="{c}" stroke-width="6" '
    'stroke-linecap="round"/>'
)
MARK_FULL = (
    '<path d="M5 29 C 7.5 21, 10 21, 12 27 C 14 33, 16.5 33, 18.5 27 '
    'C 20.5 21, 23 21, 25 26" stroke="{c}" stroke-width="4.5" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M27 24 H 43" stroke="{c}" stroke-width="4.5" '
    'stroke-linecap="round"/>'
)

TEAL, INK = "#0FA3A3", "#16213e"


def tulis(nama, isi):
    (D / nama).write_text(isi, encoding="utf-8")
    print(f"  {nama:28} {len(isi):5} byte")


def mark(varian, warna):
    """Mark berdiri sendiri, artboard 48x48."""
    return (
        f'{HEAD} viewBox="0 0 48 48" width="48" height="48" fill="none"\n'
        f'     role="img" aria-label="Jagomat">\n  '
        + varian.format(c=warna)
        + "\n</svg>\n"
    )


def lockup(varian, warna, tinggi_mark=34.0):
    """Lockup horizontal: mark + wordmark, rata CAP HEIGHT (bukan baseline).

    Wordmark sudah berupa path — aman di cetak & file:// tanpa font CDN.
    """
    s = tinggi_mark / CAP                      # skala glyph -> tinggi mark
    w_kata = LEBAR * s
    jarak = tinggi_mark * 0.42
    x_kata = 48 + jarak
    total = x_kata + w_kata
    # Mark artboard 48 tingginya; pusatkan thd cap height wordmark.
    y_base = 24 + tinggi_mark / 2              # baseline teks
    return (
        f'{HEAD} viewBox="0 0 {total:.0f} 48" width="{total:.0f}" '
        f'height="48" fill="none" role="img" aria-label="Jagomat">\n  '
        + varian.format(c=warna)
        + f'\n  <g fill="{warna}" transform="translate({x_kata:.1f} '
        f'{y_base:.1f}) scale({s:.5f} -{s:.5f})">\n    {GLYPHS}\n  </g>\n</svg>\n'
    )


print("Aset Jagomat:")
tulis("mark-sederhana.svg", mark(MARK_SIMPLE, TEAL))
tulis("mark-penuh.svg", mark(MARK_FULL, TEAL))
tulis("mark-sederhana-tinta.svg", mark(MARK_SIMPLE, INK))
tulis("lockup-horizontal.svg", lockup(MARK_SIMPLE, TEAL))
tulis("lockup-horizontal-cetak.svg", lockup(MARK_SIMPLE, INK))
tulis("lockup-hero.svg", lockup(MARK_FULL, TEAL))
