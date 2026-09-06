"""Proyeksi bukti fokus yang diteruskan saat fokus pasangannya kambuh."""
from dataclasses import replace


def bukti_lanjutan(bukti):
    """Proyeksikan referensi append-only tanpa menyalin snapshot ke database."""
    hasil = bukti
    for event in sorted(bukti.kejadian, key=lambda e: e.id):
        if event.jenis != "putaran_kambuh_dibuka":
            continue
        fokus = tuple(tuple(k) for k in event.nilai("fokus_diteruskan", ()))
        sumber = event.nilai("putaran_lama")
        tujuan = event.putaran_id
        if not fokus or sumber == tujuan:
            continue
        putaran = {p.id: p for p in hasil.putaran}
        if (sumber not in putaran or tujuan not in putaran
                or putaran[sumber].level != putaran[tujuan].level):
            continue
        sesi = tuple(_salin(s, fokus, tujuan) for s in hasil.sesi
                     if s.putaran_id == sumber and set(s.target_fokus) & set(fokus))
        sudah = {(s.id, s.putaran_id) for s in hasil.sesi}
        tambahan = tuple(s for s in sesi if (s.id, s.putaran_id) not in sudah)
        ids = {s.id for s in tambahan}
        kejadian = tuple(replace(e, putaran_id=tujuan) for e in hasil.kejadian
                         if e.putaran_id == sumber and e.id < event.id
                         and ((e.jenis == "intervensi_selesai"
                               and tuple(e.nilai("fokus", ())) in fokus)
                              or (e.sesi_id in ids and e.jenis in {
                                  "sesi_dibuat", "hasil_dikonfirmasi", "konfirmasi_dibatalkan"})))
        lama = {(e.id, e.putaran_id) for e in hasil.kejadian}
        hasil = replace(hasil, sesi=(*hasil.sesi, *tambahan),
                        kejadian=(*hasil.kejadian, *(e for e in kejadian
                                   if (e.id, e.putaran_id) not in lama)))
    return hasil


def _salin(sesi, fokus, tujuan):
    target = tuple(k for k in sesi.target_fokus if k in fokus)
    outcomes = tuple(o for o in sesi.outcomes
                     if o.target_fokus in target
                     or (o.target_fokus is None and len(sesi.target_fokus) == 1))
    return replace(sesi, putaran_id=tujuan, target_fokus=target, outcomes=outcomes)
