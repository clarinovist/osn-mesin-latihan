"""Urutan bukti pemulihan setelah evaluasi gagal, tanpa akses database."""
from dataclasses import replace


def intervensi_setelah_gagal(bukti, putaran, kunci, evaluasi):
    """Ambil pendekatan berbeda yang benar-benar terjadi setelah hasil gagal."""
    if not evaluasi or evaluasi[-1][1]:
        return None
    sesi = evaluasi[-1][0]
    konfirmasi = next((e for e in bukti.kejadian
                       if e.jenis == "hasil_dikonfirmasi"
                       and e.sesi_id == sesi.id
                       and e.konfirmasi_id == sesi.konfirmasi_id), None)
    batas = (konfirmasi.tanggal, konfirmasi.id) if konfirmasi else (sesi.tanggal, float("inf"))
    semua = tuple(e for e in bukti.kejadian
                  if e.putaran_id == putaran.id and e.jenis == "intervensi_selesai"
                  and tuple(e.nilai("fokus", ())) == kunci)
    sebelumnya = {e.nilai("pendekatan_id") for e in semua
                  if (e.tanggal, e.id) <= batas}
    tersedia = dict(bukti.pendekatan_tersedia).get(kunci, ())
    return next((e for e in sorted(semua, key=lambda e: (e.tanggal, e.id))
                 if (e.tanggal, e.id) > batas
                 and e.nilai("pendekatan_id") in tersedia
                 and e.nilai("pendekatan_id") not in sebelumnya), None)


def bukti_setelah_intervensi(bukti, intervensi):
    """Latihan baru wajib dibuat setelah intervensi alternatif, bukan dikoreksi saja."""
    if intervensi is None:
        return bukti
    pembuatan = {e.sesi_id: e for e in bukti.kejadian if e.jenis == "sesi_dibuat"}

    def baru(sesi):
        event = pembuatan.get(sesi.id)
        if event is not None:
            return (event.tanggal, event.id) > (intervensi.tanggal, intervensi.id)
        return sesi.tanggal > intervensi.tanggal

    return replace(bukti, sesi=tuple(s for s in bukti.sesi
                                    if s.tujuan not in {"latihan_terbimbing", "penguatan"}
                                    or baru(s)))
