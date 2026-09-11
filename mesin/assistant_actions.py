"""Validasi usulan dan eksekusi latihan manual Pendamping.

Model hanya boleh mengusulkan nilai dari katalog aktif. Modul ini memvalidasi
ulang seluruh nilai dan membuat sesi ``bebas`` secara idempoten setelah
konfirmasi orang tua; ia tidak menulis bukti atau kejadian siklus belajar.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Optional

import assistant_catalog
import assistant_policy
import assistant_store
import database
import topics


JUMLAH_SOAL_SAH = (10, 15, 20, 25, 30)


@dataclass(frozen=True)
class UsulanLatihan:
    topik_id: str
    template_ids: tuple[str, ...]
    level: str
    jumlah_soal: int

    def ke_dict(self) -> dict:
        return {
            "topik_id": self.topik_id,
            "template_ids": list(self.template_ids),
            "level": self.level,
            "jumlah_soal": self.jumlah_soal,
        }


class GalatTindakan(ValueError):
    """Usulan atau konfirmasi tidak lagi aman untuk dijalankan."""


def validasi_usulan(data) -> UsulanLatihan:
    """Terima hanya kombinasi topik/template/level/jumlah dari katalog aktif."""
    if type(data) is not dict or set(data) != {
        "topik_id", "template_ids", "level", "jumlah_soal"
    }:
        raise GalatTindakan("Usulan latihan tidak sesuai kontrak.")
    if (
        type(data["topik_id"]) is not str
        or type(data["level"]) is not str
        or type(data["jumlah_soal"]) is not int
        or type(data["template_ids"]) is not list
        or not data["template_ids"]
        or len(data["template_ids"]) > 8
        or any(type(item) is not str for item in data["template_ids"])
        or len(set(data["template_ids"])) != len(data["template_ids"])
    ):
        raise GalatTindakan("Parameter usulan latihan tidak sah.")
    if data["jumlah_soal"] not in JUMLAH_SOAL_SAH:
        raise GalatTindakan("Jumlah soal usulan tidak tersedia.")

    katalog = assistant_catalog.buat_katalog()
    topik = {item.id: item for item in katalog.topik}.get(data["topik_id"])
    template = {item.id: item for item in katalog.template}
    if topik is None or data["level"] not in topik.level:
        raise GalatTindakan("Topik atau level usulan tidak tersedia.")
    for template_id in data["template_ids"]:
        item = template.get(template_id)
        if (
            item is None
            or item.topik_id != topik.id
            or data["level"] not in item.level
        ):
            raise GalatTindakan("Template usulan tidak tersedia untuk pilihan ini.")
    return UsulanLatihan(
        topik_id=topik.id,
        template_ids=tuple(data["template_ids"]),
        level=data["level"],
        jumlah_soal=data["jumlah_soal"],
    )


def hash_usulan(usulan: UsulanLatihan) -> str:
    mentah = json.dumps(
        usulan.ke_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(mentah.encode("utf-8")).hexdigest()


def _siswa_dari_konteks(kon, chat, *, pemilik: str) -> Optional[int]:
    """Petakan konteks yang sudah diotorisasi ke satu anak tanpa fallback."""
    try:
        if chat.context_kind == "anak":
            siswa_id = int(chat.context_id)
        elif chat.context_kind in ("sesi", "soal"):
            sesi_id = int(chat.context_id.split(":", 1)[0])
            baris = kon.execute(
                """SELECT s.siswa_id FROM sesi s JOIN siswa w ON w.id = s.siswa_id
                   WHERE s.id = ? AND w.pemilik = ?""",
                (sesi_id, pemilik),
            ).fetchone()
            return int(baris["siswa_id"]) if baris is not None else None
        else:
            return None
    except (TypeError, ValueError, OverflowError):
        return None
    return siswa_id if database.siswa_milik(kon, siswa_id, pemilik) else None


def _urutan(usulan: UsulanLatihan) -> tuple[str, ...]:
    dasar = usulan.template_ids
    return tuple(dasar[indeks % len(dasar)] for indeks in range(usulan.jumlah_soal))


def konfirmasi_dan_buat_sesi(
    kon_pendamping,
    account_id: str,
    pemilik: str,
    usulan_id: str,
    *,
    versi: int,
    hash_diharapkan: str,
    request_id: str,
    sekarang: int,
) -> int:
    """Revalidasi konfirmasi lalu buat maksimum satu sesi manual/bebas."""
    catatan = assistant_store.ambil_usulan(
        kon_pendamping, account_id, usulan_id
    )
    if catatan is None:
        raise LookupError("usulan tidak ditemukan")
    if (
        catatan.versi != versi
        or catatan.hash_usulan != hash_diharapkan
        or catatan.request_id_konfirmasi not in (None, request_id)
    ):
        raise GalatTindakan("Usulan berubah. Tinjau ulang sebelum mengonfirmasi.")
    if catatan.sesi_id is not None:
        return catatan.sesi_id
    if not assistant_store.persetujuan_aktif(
        kon_pendamping,
        account_id,
        kategori="chat_umum",
        provider_id=assistant_policy.PROVIDER_ID,
    ) or assistant_store.versi_persetujuan(
        kon_pendamping, account_id
    ) != catatan.consent_version:
        raise GalatTindakan("Persetujuan berubah. Tinjau ulang usulan.")

    chat = assistant_store.ambil_chat(
        kon_pendamping, account_id, catatan.chat_id
    )
    if (
        chat is None
        or chat.versi != catatan.chat_version
        or chat.context_kind is None
        or chat.context_version != catatan.context_version
        or chat.context_resource_version != catatan.context_resource_version
        or not assistant_store.persetujuan_konteks_aktif(
            kon_pendamping,
            account_id,
            jenis=chat.context_kind,
            resource_id=chat.context_id,
            resource_version=chat.context_resource_version,
            versi=chat.context_version,
        )
    ):
        raise GalatTindakan("Konteks berubah. Tinjau ulang usulan.")

    usulan = validasi_usulan(json.loads(catatan.payload_json))
    if hash_usulan(usulan) != catatan.hash_usulan:
        raise GalatTindakan("Isi usulan tidak cocok dengan hash tinjauan.")
    kunci = hashlib.sha256(
        ("pendamping-bebas-v1|" + account_id + "|" + usulan_id + "|" + catatan.hash_usulan)
        .encode("utf-8")
    ).hexdigest()
    seed = int(kunci[:15], 16)

    try:
        with database.buka() as kon_data:
            lama = kon_data.execute(
                "SELECT id FROM sesi WHERE kunci_pendamping = ? AND dibatalkan IS NULL",
                (kunci,),
            ).fetchone()
            if lama is not None:
                sesi_id = int(lama["id"])
            else:
                siswa_id = _siswa_dari_konteks(kon_data, chat, pemilik=pemilik)
                if siswa_id is None:
                    raise GalatTindakan("Konteks tidak lagi dapat digunakan.")
                import assistant_context

                versi_resource = assistant_context.versi_resource(
                    kon_data, chat.context_kind, chat.context_id, pemilik=pemilik
                )
                if versi_resource != chat.context_resource_version:
                    raise GalatTindakan("Konteks berubah. Tinjau ulang usulan.")
                sesi_id = database.buat_sesi_dari_urutan(
                    kon_data,
                    siswa_id,
                    seed,
                    _urutan(usulan),
                    topik=topics.ambil(usulan.topik_id),
                    level=usulan.level,
                    mode="diagnostik",
                    jenis="biasa",
                )
                hasil = kon_data.execute(
                    """UPDATE sesi SET tujuan = 'bebas', putaran_id = NULL,
                              bagian_checkpoint = NULL, kunci_pendamping = ?
                       WHERE id = ? AND tujuan = 'bebas' AND putaran_id IS NULL
                         AND kunci_idempotensi IS NULL""",
                    (kunci, sesi_id),
                )
                if hasil.rowcount != 1:
                    raise GalatTindakan("Sesi manual tidak dapat dikunci dengan aman.")
    except sqlite3.IntegrityError:
        # Konfirmasi paralel dapat kalah pada indeks unik data utama. Transaksi
        # yang kalah sudah rollback; baca sesi pemenang sebagai hasil idempoten.
        with database.buka() as kon_data:
            lama = kon_data.execute(
                "SELECT id FROM sesi WHERE kunci_pendamping = ? AND dibatalkan IS NULL",
                (kunci,),
            ).fetchone()
        if lama is None:
            raise
        sesi_id = int(lama["id"])

    if not assistant_store.selesaikan_usulan(
        kon_pendamping,
        account_id,
        usulan_id,
        versi_diharapkan=versi,
        hash_diharapkan=hash_diharapkan,
        request_id=request_id,
        sesi_id=sesi_id,
        sekarang=sekarang,
    ):
        ulang = assistant_store.ambil_usulan(kon_pendamping, account_id, usulan_id)
        if ulang is None or ulang.sesi_id != sesi_id:
            raise GalatTindakan("Hasil konfirmasi tidak dapat disimpan.")
    return sesi_id
