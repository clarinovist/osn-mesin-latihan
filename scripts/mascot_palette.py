"""Kuantisasi maskot RGBA tanpa dithering; alat ekspor, bukan runtime aplikasi.

Master/crop tetap lokal. Palet median-cut hanya memilih warna perwakilan;
setiap piksel kemudian dipetakan ke warna palet terdekat, bukan ke kotak
partisinya. Pemetaan kotak bisa menghasilkan bintik pada area yang mulus.
"""
from collections import Counter


def kuantisasi(piksel):
    """Kembalikan palet maksimal 32 warna dan indeks untuk piksel RGBA 8-bit.

    Indeks nol khusus transparansi penuh. Jarak kuadrat RGBA menjaga warna
    sekaligus antialias; jarak seri memilih indeks terkecil secara deterministik.
    """
    frekuensi = Counter(w for w in piksel if w[3])
    if not frekuensi:
        return [(0, 0, 0, 0)], [0] * len(piksel)
    kotak = [list(frekuensi)]
    while len(kotak) < 31:
        kandidat = [
            (max(max(w[d] for w in k) - min(w[d] for w in k)
                 for d in range(4)), i)
            for i, k in enumerate(kotak) if len(k) > 1
        ]
        if not kandidat:
            break
        _, i = max(kandidat)
        warna = kotak.pop(i)
        dim = max(range(4), key=lambda d: max(w[d] for w in warna)
                  - min(w[d] for w in warna))
        warna.sort(key=lambda w: w[dim])
        tengah = sum(frekuensi[w] for w in warna) / 2
        jumlah = 0
        batas = 1
        for j, w in enumerate(warna[:-1], 1):
            jumlah += frekuensi[w]
            batas = j
            if jumlah >= tengah:
                break
        kotak.extend((warna[:batas], warna[batas:]))
    palet = [(0, 0, 0, 0)]
    for warna in kotak:
        jumlah = sum(frekuensi[w] for w in warna)
        pusat = tuple(round(sum(w[d] * frekuensi[w] for w in warna) / jumlah)
                      for d in range(4))
        palet.append(pusat)
    # Kotak median-cut bukan sel jarak terdekat: wajib petakan ulang tanpa noise.
    peta = {
        w: min(range(1, len(palet)), key=lambda i:
               sum((w[d] - palet[i][d]) ** 2 for d in range(4)))
        for w in frekuensi
    }
    return palet, [peta[w] if w[3] else 0 for w in piksel]
