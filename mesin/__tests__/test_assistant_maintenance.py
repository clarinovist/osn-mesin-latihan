"""Pemeliharaan retensi Pendamping tidak membaca atau mencetak isi privat."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import assistant_maintenance  # noqa: E402
import assistant_schema  # noqa: E402
import assistant_store  # noqa: E402


AKUN = "akun_" + "a" * 32


def test_maintenance_idempoten_dan_memori_terkonfirmasi_tetap_ada(
    tmp_path, monkeypatch
):
    path = tmp_path / "pendamping.db"
    monkeypatch.setattr(assistant_schema, "BAWAAN", path)
    assistant_schema.siapkan(path)
    with assistant_schema.buka(path) as kon:
        chat = assistant_store.buat_chat(kon, AKUN, "aktif", sekarang=100)
        memori = assistant_store.tambah_memori(
            kon, AKUN, "Jawab singkat.", sumber_chat_id=chat.id,
            dikonfirmasi=True, sekarang=100,
        )
        operasi = assistant_store.mulai_operasi(
            kon, AKUN, chat.id, "req_gagal", consent_version=0,
            memory_version=1, context_version=0, sekarang=100,
        )
        assert assistant_store.gagalkan_operasi(
            kon, AKUN, operasi.request_id, sekarang=101
        )

    kini = 100 + assistant_store.RETENSI_CHAT_DETIK
    assert assistant_maintenance.jalankan(sekarang=kini) == (1, 1, 0)
    assert assistant_maintenance.jalankan(sekarang=kini) == (0, 0, 0)
    with assistant_schema.buka(path) as kon:
        tersisa = assistant_store.daftar_memori(kon, AKUN)
        assert [item.id for item in tersisa] == [memori.id]
        assert tersisa[0].sumber_chat_id is None
        assert kon.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert kon.execute("PRAGMA foreign_key_check").fetchall() == []
