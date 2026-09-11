"""Pemeliharaan retensi DB Pendamping yang aman dijalankan berkala."""

from __future__ import annotations

import argparse
import time

import assistant_schema
import assistant_store


def jalankan(*, sekarang: int | None = None) -> tuple[int, int, int]:
    """Jadwalkan dan purge data lewat transaksi singkat yang idempoten."""
    kini = int(time.time()) if sekarang is None else int(sekarang)
    assistant_schema.siapkan()
    with assistant_schema.buka() as kon:
        dijadwalkan = assistant_store.jadwalkan_retensi_chat(
            kon, sekarang=kini
        )
        chat = assistant_store.purge(kon, sekarang=kini)
        operasi = assistant_store.purge_operasi(kon, sekarang=kini)
    return dijadwalkan, chat, operasi


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jalankan retensi Pendamping tanpa mencetak isi privat."
    )
    parser.parse_args()
    dijadwalkan, chat, operasi = jalankan()
    print(
        "Retensi Pendamping selesai: "
        f"{dijadwalkan} chat dijadwalkan, {chat} chat dipurge, "
        f"{operasi} operasi dipurge."
    )


if __name__ == "__main__":
    main()
