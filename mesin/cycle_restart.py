"""Pembukaan putaran kekambuhan tanpa menimpa histori keberhasilan."""
import json

import database
import learning_cycle as lc


def mulai_putaran_baru(kon, siswa_id):
    """Hitung ulang kekambuhan; simpan penutup dan provenance secara atomik."""
    kon.execute("SAVEPOINT mulai_putaran_baru")
    try:
        hasil = _mulai(kon, siswa_id)
        kon.execute("RELEASE SAVEPOINT mulai_putaran_baru")
        return hasil
    except Exception:
        kon.execute("ROLLBACK TO SAVEPOINT mulai_putaran_baru")
        kon.execute("RELEASE SAVEPOINT mulai_putaran_baru")
        raise


def _mulai(kon, siswa_id):
    from cycle_carry import bukti_lanjutan

    bukti = bukti_lanjutan(database.muat_bukti_siklus(kon, siswa_id))
    aktif = lc._putaran_dengan_override(lc._putaran_aktif(bukti), bukti.kejadian)
    rencana = lc.rencana_berikutnya(bukti, siswa_id)
    if aktif is None:
        raise ValueError("putaran aktif tidak ditemukan")
    if rencana.tindakan != "putaran_baru":
        if any(e.putaran_id == aktif.id and e.jenis == "putaran_kambuh_dibuka"
               for e in bukti.kejadian):
            return aktif.id
        raise ValueError("belum ada kekambuhan yang perlu putaran baru")
    if rencana.putaran is None or not rencana.putaran.fokus:
        raise ValueError("rekomendasi kekambuhan tidak lengkap")
    kambuh = tuple(f.kunci for f in rencana.putaran.fokus)
    diteruskan = tuple(k for k in aktif.fokus if k not in kambuh)
    fokus = (*kambuh, *diteruskan)
    sumber = tuple(s for s in bukti.sesi
                   if s.putaran_id == aktif.id and s.selesai is not None
                   and s.dikonfirmasi is not None and s.dibatalkan is None
                   and any(k in s.target_fokus or any(lc._kunci_outcome(o) == k
                           for o in s.outcomes) for k in fokus))
    if not sumber:
        raise ValueError("kekambuhan tidak mempunyai bukti sah")
    baru = database.buat_putaran_fokus(kon, siswa_id, bukti.level_aktif)
    for kunci in fokus:
        database.tambah_anggota_fokus(kon, baru, *kunci, [s.id for s in sumber],
                                      izinkan_provenance_historis=True)
    for putaran_id, jenis, data in (
        (aktif.id, "putaran_ditutup", {"alasan": "kekambuhan", "putaran_baru": baru}),
        (baru, "putaran_kambuh_dibuka", {"putaran_lama": aktif.id,
         "konfirmasi_ids": [s.konfirmasi_id for s in sumber], "fokus": fokus,
         "fokus_diteruskan": diteruskan}),
    ):
        kon.execute("""INSERT INTO kejadian_belajar (siswa_id, putaran_id, jenis, data)
                       VALUES (?, ?, ?, ?)""",
                    (siswa_id, putaran_id, jenis, json.dumps(data, sort_keys=True)))
    return baru
