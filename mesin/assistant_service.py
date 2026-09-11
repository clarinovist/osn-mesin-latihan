"""Orkestrasi chat umum Pendamping tanpa menahan transaksi saat network."""

from __future__ import annotations

import json
import os
import time

import assistant_actions
import assistant_catalog
import assistant_client
import assistant_policy
import assistant_store


class GalatPendamping(RuntimeError):
    """Kegagalan aman yang boleh diterjemahkan menjadi pesan UI umum."""


def konfigurasi() -> assistant_client.Konfigurasi:
    return assistant_client.Konfigurasi(
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ.get("DEEPSEEK_API_KEY", "").strip(),
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash").strip(),
    )


def tersedia() -> bool:
    """Konfigurasi chat lengkap dan sah, tanpa melakukan network call."""
    try:
        konfigurasi()
    except ValueError:
        return False
    return True


def panggil_provider_default(pesan):
    return assistant_client.kirim(konfigurasi(), pesan)


def _pesan_provider(
    kon, account_id: str, chat_id: str, teks_baru: str, *, konteks=None
):
    katalog = json.loads(
        assistant_catalog.serialisasi_ringkas(assistant_catalog.buat_katalog())
    )
    memori = [item.isi for item in assistant_store.memori_untuk_chat(
        kon, account_id, chat_id
    )]
    percakapan = [
        {"peran": item.peran, "teks": item.teks}
        for item in assistant_store.daftar_pesan(kon, account_id, chat_id)
    ]
    percakapan.append({"peran": "pengguna", "teks": teks_baru})
    isi = {
        "katalog": katalog,
        "memori": memori,
        "percakapan": percakapan,
    }
    if konteks is not None:
        isi["konteks"] = konteks.muatan
    muatan = json.dumps(isi, ensure_ascii=False, separators=(",", ":"))
    return [
        {"role": "system", "content": assistant_policy.PROMPT_SISTEM},
        {"role": "user", "content": muatan},
    ]


def kirim_pesan(
    kon,
    account_id: str,
    chat_id: str,
    teks: str,
    *,
    request_id: str,
    panggil_provider=None,
    sekarang: int | None = None,
    konteks=None,
    validasi_konteks=None,
) -> str:
    """Simpan pesan, panggil provider di luar transaksi, lalu revalidasi versi."""
    kini = int(time.time()) if sekarang is None else int(sekarang)
    aman = assistant_policy.pastikan_teks_aman(teks)
    if not assistant_store.persetujuan_aktif(
        kon, account_id, kategori="chat_umum", provider_id=assistant_policy.PROVIDER_ID
    ):
        raise GalatPendamping("Persetujuan provider belum diberikan.")

    operasi_lama = kon.execute(
        "SELECT status FROM operasi WHERE request_id = ? AND account_id = ?",
        (request_id, account_id),
    ).fetchone()
    if operasi_lama:
        jawaban_lama = assistant_store.pesan_dari_request(
            kon, account_id, request_id + ":jawaban", peran="asisten"
        )
        if operasi_lama["status"] == "selesai" and jawaban_lama:
            return jawaban_lama.teks
        raise GalatPendamping("Permintaan ini sedang atau sudah gagal diproses.")

    consent_version = assistant_store.versi_persetujuan(kon, account_id)
    memory_version = assistant_store.versi_memori(kon, account_id)
    context_version = (
        assistant_store.versi_persetujuan_konteks(kon, account_id)
        if konteks is not None else 0
    )
    operasi = assistant_store.mulai_operasi(
        kon, account_id, chat_id, request_id,
        consent_version=consent_version,
        memory_version=memory_version,
        context_version=context_version,
        sekarang=kini,
    )
    pesan = _pesan_provider(
        kon, account_id, chat_id, aman, konteks=konteks
    )
    kon.commit()

    pemanggil = panggil_provider or panggil_provider_default
    try:
        mentah = pemanggil(pesan)
        respons = assistant_policy.validasi_respons(mentah)
        konteks_masih_sah = (
            konteks is None
            or (
                validasi_konteks is not None
                and validasi_konteks() == konteks.versi
            )
        )
    except (assistant_client.GalatProvider, ValueError) as galat:
        try:
            with kon:
                assistant_store.gagalkan_operasi(
                    kon, account_id, request_id, sekarang=kini
                )
        except Exception:
            kon.rollback()
        raise GalatPendamping("Pendamping belum bisa menjawab. Coba lagi nanti.") from galat

    try:
        with kon:
            if not konteks_masih_sah:
                raise GalatPendamping(
                    "Konteks belajar berubah. Buka chat baru setelah meninjau ulang."
                )
            if konteks is not None and (
                assistant_store.versi_persetujuan_konteks(
                    kon, account_id
                ) != context_version
                or not assistant_store.persetujuan_konteks_aktif(
                    kon,
                    account_id,
                    jenis=konteks.jenis,
                    resource_id=konteks.resource_id,
                    resource_version=konteks.versi,
                )
            ):
                raise GalatPendamping(
                    "Persetujuan konteks berubah. Buka chat baru."
                )
            if not assistant_store.selesaikan_operasi(
                kon, account_id, request_id,
                chat_version=operasi.chat_version,
                consent_version=consent_version,
                memory_version=memory_version,
                context_version=context_version,
                sekarang=kini,
            ):
                raise GalatPendamping(
                    "Percakapan atau persetujuan berubah. Tinjau lalu kirim lagi."
                )
            assistant_store.tambah_pesan(
                kon, account_id, chat_id, "pengguna", aman,
                request_id=request_id, sekarang=kini,
            )
            assistant_store.tambah_pesan(
                kon, account_id, chat_id, "asisten", respons.jawaban,
                request_id=request_id + ":jawaban", sekarang=kini,
            )
            if respons.usulan_latihan is not None:
                if konteks is None:
                    raise GalatPendamping(
                        "Pilih konteks belajar sebelum meninjau usulan latihan."
                    )
                payload = json.dumps(
                    respons.usulan_latihan.ke_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                assistant_store.simpan_usulan(
                    kon,
                    account_id,
                    chat_id,
                    request_id,
                    payload_json=payload,
                    hash_usulan=assistant_actions.hash_usulan(
                        respons.usulan_latihan
                    ),
                    chat_version=operasi.chat_version + 2,
                    consent_version=consent_version,
                    context_version=context_version,
                    context_resource_version=konteks.versi,
                    sekarang=kini,
                )
            if respons.draft_memori is not None:
                chat = assistant_store.ambil_chat(kon, account_id, chat_id)
                if (
                    chat is None
                    or chat.mode_memori == "tanpa_memori"
                    or not assistant_store.penggunaan_memori_aktif(
                        kon, account_id
                    )
                ):
                    raise GalatPendamping(
                        "Penggunaan memori nonaktif untuk chat ini."
                    )
                assistant_store.tambah_memori(
                    kon,
                    account_id,
                    respons.draft_memori.isi,
                    sumber_chat_id=chat_id,
                    dikonfirmasi=False,
                    sekarang=kini,
                    lingkup=respons.draft_memori.lingkup,
                )
    except GalatPendamping:
        try:
            with kon:
                assistant_store.gagalkan_operasi(
                    kon, account_id, request_id, sekarang=kini
                )
        except Exception:
            kon.rollback()
        raise
    return respons.jawaban
