"""Kontrak HTTP Fase 3 untuk konfirmasi dan orkestrator siklus belajar.

Semua perilaku target ditempuh melalui server HTTP sungguhan. Fixture hanya
menyiapkan data awal sintetis dan membaca efek akhirnya dari basis data uji.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import auth  # noqa: E402
import database  # noqa: E402
import interventions  # noqa: E402
from http_test_kit import SANDI_GURU, ServerUji  # noqa: E402

SANDI_GURU_B = "sandi-guru-b-panjang-456"
SANDI_ADMIN = "sandi-pengelola-panjang-789"


@pytest.fixture()
def server(tmp_path, monkeypatch):
    s = ServerUji(tmp_path, monkeypatch)
    auth.tambah_akun(
        "guru-b", SANDI_GURU_B, "guru", path=auth.BERKAS_SANDI
    )
    auth.tambah_akun(
        "pengelola", SANDI_ADMIN, "admin", path=auth.BERKAS_SANDI
    )
    with s.buka() as kon:
        siswa_a = database.tambah_siswa(
            kon, "Anak A", "P3", pemilik="guru"
        )
        siswa_b = database.tambah_siswa(
            kon, "Anak B", "P3", pemilik="guru-b"
        )
        siswa_buat = database.tambah_siswa(
            kon, "Anak Rencana", "P3", pemilik="guru"
        )
        sesi_a = _buat_sesi_selesai(kon, siswa_a, seed=11)
        sesi_a_lain = _buat_sesi_selesai(kon, siswa_a, seed=12)
        sesi_b = _buat_sesi_selesai(kon, siswa_b, seed=21)
    yield s, {
        "siswa_a": siswa_a,
        "siswa_b": siswa_b,
        "siswa_buat": siswa_buat,
        "sesi_a": sesi_a,
        "sesi_a_lain": sesi_a_lain,
        "sesi_b": sesi_b,
    }
    s.berhenti()


def _buat_sesi_selesai(kon, siswa_id, seed):
    sesi_id = database.buat_sesi(
        kon, siswa_id, seed=seed, level="P3", jumlah_soal=1
    )
    butir = database.isi_sesi(kon, sesi_id)[0]
    jawaban_id = database.simpan_jawaban(
        kon, butir["sesi_soal_id"], jawaban="0", cara="cara awal"
    )
    database.simpan_diagnosis(
        kon,
        jawaban_id,
        benar=False,
        kode_usulan="K",
        kode_final="K",
        malrule_id="salah-awal",
        alasan="diagnosis awal",
    )
    database.tandai_selesai(kon, sesi_id)
    return sesi_id


def _buat_sesi_rencana_awal(kon, siswa_id):
    """Setup via layanan domain; perilaku batal/retry tetap diuji via HTTP."""
    from learning_cycle import rencana_berikutnya

    putaran_id = database.buat_putaran_fokus(kon, siswa_id, "P3")
    bukti = database.muat_bukti_siklus(kon, siswa_id)
    rencana = rencana_berikutnya(bukti, siswa_id)
    return database.buat_sesi_dari_rencana(
        kon, siswa_id, rencana, putaran_id=putaran_id, seed=701
    )


def _payload_benar(kon, sesi_id, *, sertakan=False):
    butir = database.isi_sesi(kon, sesi_id)[0]
    sid = int(butir["sesi_soal_id"])
    data = {
        f"jwb_{sid}": butir["kunci"],
        f"cara_{sid}": "dihitung ulang oleh guru",
        f"kode_{sid}": "benar",
        f"cek_pemahaman_{sid}": "bisa_menjelaskan",
    }
    if sertakan:
        data["sertakan_pemetaan"] = "1"
    return sid, data


def _jumlah_bukti(kon, sesi_id):
    return {
        "konfirmasi": kon.execute(
            "SELECT COUNT(*) FROM konfirmasi_hasil WHERE sesi_id = ?",
            (sesi_id,),
        ).fetchone()[0],
        "snapshot": kon.execute(
            """SELECT COUNT(*) FROM snapshot_outcome so
               JOIN konfirmasi_hasil kh ON kh.id = so.konfirmasi_id
               WHERE kh.sesi_id = ?""",
            (sesi_id,),
        ).fetchone()[0],
        "kejadian": kon.execute(
            "SELECT COUNT(*) FROM kejadian_belajar WHERE sesi_id = ?",
            (sesi_id,),
        ).fetchone()[0],
    }


def test_get_hasil_tidak_mengonfirmasi_sesi(server):
    s, data = server

    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_a']}", auth=("guru", SANDI_GURU)
    )

    with s.buka() as kon:
        cache = kon.execute(
            """SELECT direview, dikonfirmasi_guru, fingerprint_konfirmasi
               FROM sesi WHERE id = ?""",
            (data["sesi_a"],),
        ).fetchone()
        bukti = _jumlah_bukti(kon, data["sesi_a"])

    assert kode == 200
    assert cache["direview"] is not None
    assert cache["dikonfirmasi_guru"] is None
    assert cache["fingerprint_konfirmasi"] is None
    assert bukti == {"konfirmasi": 0, "snapshot": 0, "kejadian": 0}


def test_marker_transport_konfirmasi_divalidasi_lalu_tidak_masuk_domain(server):
    s, data = server
    with s.buka() as kon:
        sid, payload = _payload_benar(kon, data["sesi_a"], sertakan=True)
    marker = {
        "hadir_sertakan_pemetaan": "1",
        f"hadir_dilewati_{sid}": "1",
        f"hadir_belum_{sid}": "1",
    }
    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_a']}/konfirmasi",
        auth=("guru", SANDI_GURU), data={**payload, **marker},
    )
    assert kode == 200

    with s.buka() as kon:
        jumlah = kon.execute(
            "SELECT COUNT(*) FROM konfirmasi_hasil WHERE sesi_id=?", (data["sesi_a"],)
        ).fetchone()[0]
    rusak = dict(payload, hadir_dilewati_999999="1")
    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_a']}/konfirmasi",
        auth=("guru", SANDI_GURU), data=rusak,
    )
    assert kode == 400
    with s.buka() as kon:
        assert kon.execute(
            "SELECT COUNT(*) FROM konfirmasi_hasil WHERE sesi_id=?", (data["sesi_a"],)
        ).fetchone()[0] == jumlah


def test_post_konfirmasi_menyimpan_snapshot_event_cache_dan_opt_in(server):
    s, data = server
    with s.buka() as kon:
        sid, payload = _payload_benar(kon, data["sesi_a"], sertakan=True)

    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_a']}/konfirmasi",
        auth=("guru", SANDI_GURU),
        data=payload,
    )

    with s.buka() as kon:
        sesi = kon.execute(
            """SELECT tujuan, dikonfirmasi_guru, fingerprint_konfirmasi
               FROM sesi WHERE id = ?""",
            (data["sesi_a"],),
        ).fetchone()
        konfirmasi = kon.execute(
            "SELECT id, fingerprint FROM konfirmasi_hasil WHERE sesi_id = ?",
            (data["sesi_a"],),
        ).fetchone()
        snapshot = kon.execute(
            """SELECT sesi_soal_id, benar, kode_final, malrule_id,
                      cek_pemahaman
               FROM snapshot_outcome WHERE konfirmasi_id = ?""",
            (konfirmasi["id"],),
        ).fetchone() if konfirmasi else None
        kejadian = kon.execute(
            """SELECT jenis, konfirmasi_id FROM kejadian_belajar
               WHERE sesi_id = ? ORDER BY id""",
            (data["sesi_a"],),
        ).fetchall()

    assert kode == 200
    assert sesi["tujuan"] == "bebas"
    assert sesi["dikonfirmasi_guru"] is not None
    assert sesi["fingerprint_konfirmasi"] == konfirmasi["fingerprint"]
    assert dict(snapshot) == {
        "sesi_soal_id": sid,
        "benar": 1,
        "kode_final": None,
        "malrule_id": None,
        "cek_pemahaman": "bisa_menjelaskan",
    }
    assert [(e["jenis"], e["konfirmasi_id"]) for e in kejadian] == [
        ("hasil_dikonfirmasi", konfirmasi["id"]),
        ("sertakan_pemetaan", konfirmasi["id"]),
    ]


def test_payload_butir_asing_ditolak_tanpa_koreksi_parsial(server):
    s, data = server
    with s.buka() as kon:
        sid_sah, payload = _payload_benar(kon, data["sesi_a"])
        sid_asing, payload_asing = _payload_benar(kon, data["sesi_a_lain"])
        payload.update(payload_asing)
        sebelum = dict(kon.execute(
            """SELECT j.jawaban, d.benar, d.kode_final, d.malrule_id
               FROM jawaban j JOIN diagnosis d ON d.jawaban_id = j.id
               WHERE j.sesi_soal_id = ?""",
            (sid_sah,),
        ).fetchone())

    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_a']}/konfirmasi",
        auth=("guru", SANDI_GURU),
        data=payload,
    )

    with s.buka() as kon:
        sesudah = dict(kon.execute(
            """SELECT j.jawaban, d.benar, d.kode_final, d.malrule_id
               FROM jawaban j JOIN diagnosis d ON d.jawaban_id = j.id
               WHERE j.sesi_soal_id = ?""",
            (sid_sah,),
        ).fetchone())
        bukti = _jumlah_bukti(kon, data["sesi_a"])

    assert sid_asing != sid_sah
    assert kode == 400
    assert sesudah == sebelum
    assert bukti == {"konfirmasi": 0, "snapshot": 0, "kejadian": 0}


def test_kepemilikan_lintas_keluarga_404_tanpa_efek(server):
    s, data = server
    with s.buka() as kon:
        sid, payload = _payload_benar(kon, data["sesi_b"], sertakan=True)
        sebelum = dict(kon.execute(
            """SELECT j.jawaban, d.benar, d.kode_final, d.malrule_id
               FROM jawaban j JOIN diagnosis d ON d.jawaban_id = j.id
               WHERE j.sesi_soal_id = ?""",
            (sid,),
        ).fetchone())

    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_b']}/konfirmasi",
        auth=("guru", SANDI_GURU),
        data=payload,
    )

    with s.buka() as kon:
        sesudah = dict(kon.execute(
            """SELECT j.jawaban, d.benar, d.kode_final, d.malrule_id
               FROM jawaban j JOIN diagnosis d ON d.jawaban_id = j.id
               WHERE j.sesi_soal_id = ?""",
            (sid,),
        ).fetchone())
        bukti = _jumlah_bukti(kon, data["sesi_b"])
        cache = kon.execute(
            "SELECT dikonfirmasi_guru FROM sesi WHERE id = ?",
            (data["sesi_b"],),
        ).fetchone()[0]

    assert kode == 404
    assert sesudah == sebelum
    assert cache is None
    assert bukti == {"konfirmasi": 0, "snapshot": 0, "kejadian": 0}


def test_post_buat_menghitung_rencana_server_side_dan_idempoten(server):
    s, data = server
    jalur = f"/siklus/{data['siswa_buat']}/buat"

    kode_1, _, _ = s.minta(
        jalur, auth=("guru", SANDI_GURU), data={}
    )
    kode_2, _, _ = s.minta(
        jalur, auth=("guru", SANDI_GURU), data={}
    )

    with s.buka() as kon:
        sesi = kon.execute(
            """SELECT id, tujuan, putaran_id, kunci_idempotensi
               FROM sesi WHERE siswa_id = ? ORDER BY id""",
            (data["siswa_buat"],),
        ).fetchall()
        jumlah_soal = (
            kon.execute(
                "SELECT COUNT(*) FROM sesi_soal WHERE sesi_id = ?",
                (sesi[0]["id"],),
            ).fetchone()[0]
            if sesi else 0
        )

    assert kode_1 == kode_2 == 200
    assert len(sesi) == 1
    assert sesi[0]["tujuan"] == "pemetaan"
    assert sesi[0]["putaran_id"] is not None
    assert sesi[0]["kunci_idempotensi"] is not None
    assert jumlah_soal == 15


def test_batalkan_non_destruktif_dan_retry_membuat_sesi_baru(server):
    s, data = server
    jalur_buat = f"/siklus/{data['siswa_buat']}/buat"
    with s.buka() as kon:
        pertama = _buat_sesi_rencana_awal(kon, data["siswa_buat"])
        jumlah_soal_lama = kon.execute(
            "SELECT COUNT(*) FROM sesi_soal WHERE sesi_id = ?", (pertama,)
        ).fetchone()[0]

    kode_batal, _, _ = s.minta(
        f"/sesi/{pertama}/batalkan",
        auth=("guru", SANDI_GURU),
        data={"alasan": "lembar rusak"},
    )
    kode_retry, _, _ = s.minta(
        jalur_buat, auth=("guru", SANDI_GURU), data={}
    )

    with s.buka() as kon:
        semua = kon.execute(
            """SELECT id, dibatalkan, kunci_idempotensi FROM sesi
               WHERE siswa_id = ? ORDER BY id""",
            (data["siswa_buat"],),
        ).fetchall()
        soal_lama_masih_ada = kon.execute(
            "SELECT COUNT(*) FROM sesi_soal WHERE sesi_id = ?", (pertama,)
        ).fetchone()[0]
        event_batal = kon.execute(
            """SELECT jenis FROM kejadian_belajar
               WHERE sesi_id = ? AND jenis = 'sesi_dibatalkan'""",
            (pertama,),
        ).fetchall()

    assert kode_batal == kode_retry == 200
    assert len(semua) == 2
    assert semua[0]["id"] == pertama
    assert semua[0]["dibatalkan"] is not None
    assert semua[1]["id"] != pertama
    assert semua[1]["dibatalkan"] is None
    assert semua[0]["kunci_idempotensi"] == semua[1]["kunci_idempotensi"]
    assert soal_lama_masih_ada == jumlah_soal_lama > 0
    assert [e["jenis"] for e in event_batal] == ["sesi_dibatalkan"]


def _siapkan_putaran_fokus(kon, siswa_id):
    sesi_sumber = database.buat_sesi(
        kon, siswa_id, seed=801, level="P3", jumlah_soal=1
    )
    putaran_id = database.buat_putaran_fokus(
        kon, siswa_id, "P3", sesi_ids=[sesi_sumber]
    )
    fokus = ("deret_aritmetika", "K", None)
    database.tambah_anggota_fokus(
        kon, putaran_id, fokus[0], fokus[1], fokus[2], [sesi_sumber]
    )
    return putaran_id, fokus


def test_halaman_hasil_memuat_kontrol_konfirmasi_dan_opt_in(server):
    s, data = server

    kode, isi, _ = s.minta(
        f"/sesi/{data['sesi_a']}", auth=("guru", SANDI_GURU)
    )

    assert kode == 200
    assert f'action="/sesi/{data["sesi_a"]}/konfirmasi"' in isi
    assert "Konfirmasi hasil" in isi
    assert 'name="cek_pemahaman_' in isi
    assert 'name="sertakan_pemetaan"' in isi


def test_admin_dapat_mengonfirmasi_sesi_semua_keluarga(server):
    s, data = server
    with s.buka() as kon:
        _, payload = _payload_benar(kon, data["sesi_b"])

    kode, _, _ = s.minta(
        f"/sesi/{data['sesi_b']}/konfirmasi",
        auth=("pengelola", SANDI_ADMIN),
        data=payload,
    )

    with s.buka() as kon:
        dikonfirmasi = kon.execute(
            "SELECT dikonfirmasi_guru FROM sesi WHERE id = ?", (data["sesi_b"],)
        ).fetchone()[0]
    assert kode == 200
    assert dikonfirmasi is not None


def test_payload_orkestrator_asing_ditolak_tanpa_membuat_sesi(server):
    s, data = server

    kode, _, _ = s.minta(
        f"/siklus/{data['siswa_buat']}/buat",
        auth=("guru", SANDI_GURU),
        data={"tindakan": "evaluasi", "putaran_id": "999"},
    )

    with s.buka() as kon:
        jumlah = kon.execute(
            "SELECT COUNT(*) FROM sesi WHERE siswa_id = ?", (data["siswa_buat"],)
        ).fetchone()[0]
        putaran = kon.execute(
            "SELECT COUNT(*) FROM putaran_fokus WHERE siswa_id = ?",
            (data["siswa_buat"],),
        ).fetchone()[0]
    assert kode == 400
    assert jumlah == 0
    assert putaran == 0


def test_intervensi_selesai_memvalidasi_fokus_dan_pendekatan(server):
    s, data = server
    with s.buka() as kon:
        putaran_id, fokus = _siapkan_putaran_fokus(kon, data["siswa_buat"])
        pendekatan = interventions.pilihan_untuk_fokus(fokus)[0].pendekatan_id

    kode, _, _ = s.minta(
        f"/siklus/{data['siswa_buat']}/aksi",
        auth=("guru", SANDI_GURU),
        data={
            "aksi": "intervensi_selesai",
            "putaran_id": str(putaran_id),
            "template_id": fokus[0],
            "kode_intervensi": fokus[1],
            "malrule_id": "",
            "pendekatan_id": pendekatan,
        },
    )

    with s.buka() as kon:
        event = kon.execute(
            """SELECT jenis, data FROM kejadian_belajar
               WHERE putaran_id = ? AND jenis = 'intervensi_selesai'""",
            (putaran_id,),
        ).fetchone()
    assert kode == 200
    assert event["jenis"] == "intervensi_selesai"
    assert pendekatan in event["data"]


def test_intervensi_asing_ditolak_tanpa_event(server):
    s, data = server
    with s.buka() as kon:
        putaran_id, fokus = _siapkan_putaran_fokus(kon, data["siswa_buat"])

    kode, _, _ = s.minta(
        f"/siklus/{data['siswa_buat']}/aksi",
        auth=("guru", SANDI_GURU),
        data={
            "aksi": "intervensi_selesai",
            "putaran_id": str(putaran_id),
            "template_id": fokus[0],
            "kode_intervensi": fokus[1],
            "malrule_id": "asing",
            "pendekatan_id": "palsu",
        },
    )

    with s.buka() as kon:
        jumlah = kon.execute(
            """SELECT COUNT(*) FROM kejadian_belajar
               WHERE putaran_id = ? AND jenis = 'intervensi_selesai'""",
            (putaran_id,),
        ).fetchone()[0]
    assert kode == 400
    assert jumlah == 0


def test_override_setelah_intervensi_menutup_putaran_dan_membatalkan_turunan(server):
    s, data = server
    with s.buka() as kon:
        putaran_id, fokus = _siapkan_putaran_fokus(kon, data["siswa_buat"])
        pendekatan = interventions.pilihan_untuk_fokus(fokus)[0].pendekatan_id
        kon.execute(
            """INSERT INTO kejadian_belajar
                   (siswa_id, putaran_id, jenis, data)
               VALUES (?, ?, 'intervensi_selesai', ?)""",
            (
                data["siswa_buat"],
                putaran_id,
                '{"fokus":["deret_aritmetika","K",null],'
                f'"pendekatan_id":"{pendekatan}"}}',
            ),
        )
        from learning_cycle import PutaranFokus, RencanaBelajar, StatusFokus

        rencana = RencanaBelajar(
            "latihan_terbimbing",
            "uji",
            putaran=PutaranFokus(
                putaran_id, "P3", (StatusFokus(fokus, "perlu_dipelajari"),)
            ),
            kandidat=(fokus,),
        )
        turunan = database.buat_sesi_dari_rencana(
            kon,
            data["siswa_buat"],
            rencana,
            putaran_id=putaran_id,
            seed=802,
        )

    kode, _, _ = s.minta(
        f"/siklus/{data['siswa_buat']}/aksi",
        auth=("guru", SANDI_GURU),
        data={
            "aksi": "ubah_fokus",
            "template_id": "soal_umur",
            "kode_intervensi": "H",
            "malrule_id": "",
        },
    )

    with s.buka() as kon:
        putaran = kon.execute(
            "SELECT id FROM putaran_fokus WHERE siswa_id = ? ORDER BY id",
            (data["siswa_buat"],),
        ).fetchall()
        event = kon.execute(
            """SELECT jenis FROM kejadian_belajar
               WHERE putaran_id = ? AND jenis = 'override_ditutup'""",
            (putaran_id,),
        ).fetchone()
        batal = kon.execute(
            "SELECT dibatalkan FROM sesi WHERE id = ?", (turunan,)
        ).fetchone()[0]
        fokus_baru = kon.execute(
            """SELECT template_id, kode_intervensi FROM anggota_fokus
               WHERE putaran_id = ?""",
            (putaran[-1]["id"],),
        ).fetchone()
    assert kode == 200
    assert len(putaran) == 2
    assert event["jenis"] == "override_ditutup"
    assert batal is not None
    assert tuple(fokus_baru) == ("soal_umur", "H")
