"""Komponen kartu rencana belajar untuk permukaan guru."""

from __future__ import annotations

import html
from datetime import date
from typing import Optional, Tuple

import database
import interventions
import topics
from learning_cycle import BuktiSiklus, RencanaBelajar, StatusFokus, rencana_berikutnya
from learning_history import catatan_histori_beda_level

KunciFokus = Tuple[str, str, Optional[str]]

_LABEL_TAHAP = ("Pemetaan", "Pelajari", "Latihan", "Evaluasi", "Checkpoint", "Lanjut")
_TINDAKAN_BUAT = {
    "pemetaan",
    "probe_diagnostik",
    "latihan_terbimbing",
    "penguatan",
    "evaluasi",
    "checkpoint",
    "probe_setelah_pengenalan",
    "mixed_maintenance",
}
_TAHAP_TINDAKAN = {
    "pemetaan": 0,
    "tunggu_pemetaan": 0,
    "probe_diagnostik": 0,
    "intervensi": 1,
    "pengenalan": 1,
    "latihan_terbimbing": 2,
    "penguatan": 2,
    "tunggu_evaluasi": 3,
    "evaluasi": 3,
    "tunggu_checkpoint": 4,
    "checkpoint": 4,
    "mixed_maintenance": 5,
    "putaran_baru": 5,
    "eskalasi": 5,
}


def _nama_template(template_id: str) -> str:
    khusus = {
        "median_modus": "Median & modus",
        "diagram_batang_garis": "Diagram batang & garis",
        "soal_umur": "Soal tentang umur",
    }
    return khusus.get(template_id, template_id.replace("_", " ").capitalize())


def _fokus_utama(rencana: RencanaBelajar) -> Optional[KunciFokus]:
    if rencana.kandidat:
        return rencana.kandidat[0]
    if rencana.putaran and rencana.putaran.fokus:
        return rencana.putaran.fokus[0].kunci
    return None


def _status_fokus(rencana: RencanaBelajar, fokus: KunciFokus) -> Optional[StatusFokus]:
    if not rencana.putaran:
        return None
    return next((item for item in rencana.putaran.fokus if item.kunci == fokus), None)


def _tujuan_sesi_aktif(rencana: RencanaBelajar, bukti: BuktiSiklus) -> Optional[str]:
    if rencana.sesi_id is None:
        return None
    sesi = next((item for item in bukti.sesi if item.id == rencana.sesi_id), None)
    return sesi.tujuan if sesi else None


def _tahap_efektif(rencana: RencanaBelajar, bukti: BuktiSiklus) -> str:
    if rencana.tindakan in {"lanjutkan_sesi", "konfirmasi_hasil"}:
        return _tujuan_sesi_aktif(rencana, bukti) or rencana.tindakan
    return rencana.tindakan


def _judul(rencana: RencanaBelajar, fokus: Optional[KunciFokus], bukti: BuktiSiklus) -> str:
    tindakan = rencana.tindakan
    tujuan = _tujuan_sesi_aktif(rencana, bukti)
    if tindakan in {"lanjutkan_sesi", "konfirmasi_hasil"} and tujuan:
        tahap = {
            "pemetaan": "Pemetaan",
            "latihan_terbimbing": "Latihan terbimbing",
            "penguatan": "Penguatan mandiri",
            "evaluasi": "Evaluasi berjeda",
            "checkpoint": "Checkpoint",
            "pengenalan": "Pengenalan materi",
            "maintenance": "Latihan campuran",
        }.get(tujuan, "Sesi terpandu")
        awalan = "Lanjutkan sesi" if tindakan == "lanjutkan_sesi" else "Tinjau dan konfirmasi hasil"
        return f"{awalan} — {tahap}"
    if tindakan == "pemetaan":
        jumlah = len(set(rencana.putaran.tanggal_pemetaan)) if rencana.putaran else 0
        return "Mulai pemetaan" if jumlah == 0 else "Lanjutkan pemetaan"
    if tindakan == "tunggu_pemetaan":
        return "Lanjutkan pemetaan besok"
    if tindakan == "lanjutkan_sesi":
        return "Lanjutkan sesi terpandu"
    if tindakan == "konfirmasi_hasil":
        return "Tinjau dan konfirmasi hasil"
    if tindakan == "intervensi":
        kode = fokus[1] if fokus else ""
        return {
            "B": "Pelajari cara membaca soal",
            "K": "Pelajari konsep bersama",
            "H": "Pelajari cara memeriksa hitungan",
            "E": "Pelajari cara memeriksa jawaban akhir",
            "N": "Pelajari cara menjelaskan jawaban",
            "T": "Kenalkan materi baru",
        }.get(kode, "Pelajari bersama")
    return {
        "probe_diagnostik": "Periksa lagi kandidat fokus",
        "latihan_terbimbing": "Coba latihan terbimbing",
        "penguatan": "Coba mandiri",
        "tunggu_evaluasi": "Tunggu evaluasi berjeda",
        "evaluasi": "Lakukan evaluasi berjeda",
        "tunggu_checkpoint": "Tunggu checkpoint berikutnya",
        "checkpoint": "Lakukan checkpoint",
        "probe_setelah_pengenalan": "Periksa pemahaman materi baru",
        "pengenalan": "Kenalkan materi baru",
        "mixed_maintenance": "Lanjutkan latihan campuran",
        "putaran_baru": "Mulai putaran belajar baru",
        "eskalasi": "Periksa prasyarat bersama",
    }.get(tindakan, "Lanjutkan rencana belajar")


def _alasan(rencana: RencanaBelajar, fokus: Optional[KunciFokus]) -> str:
    if fokus:
        status = _status_fokus(rencana, fokus)
        if status and status.jumlah_sesi:
            nama = _nama_template(fokus[0])
            jenis = {
                "B": "Salah memahami soal",
                "K": "Salah konsep",
                "H": "Salah hitung",
                "E": "Salah menulis jawaban akhir",
                "N": "Cara menjawab belum terlihat",
                "T": "Materi belum dikenalkan",
            }.get(fokus[1], "Pola yang sama")
            return f"{jenis} pada {nama} muncul di {status.jumlah_sesi} sesi terkonfirmasi."
    return rencana.alasan.rstrip(".") + "."


def _progres(rencana: RencanaBelajar, bukti: BuktiSiklus) -> str:
    tujuan = _tujuan_sesi_aktif(rencana, bukti)
    if rencana.tindakan == "putaran_baru":
        return "Fokus kambuh — mulai putaran baru"
    if tujuan:
        return {
            "pemetaan": "Tahap pemetaan",
            "latihan_terbimbing": "Tahap latihan terbimbing",
            "penguatan": "Tahap penguatan mandiri",
            "evaluasi": "Tahap evaluasi berjeda",
            "checkpoint": "Tahap checkpoint",
            "pengenalan": "Tahap pengenalan materi",
            "maintenance": "Tahap latihan campuran",
        }.get(tujuan, "Sesi terpandu aktif")
    if rencana.tindakan == "mixed_maintenance":
        return "Pemetaan selesai — tidak ada fokus aktif"
    if rencana.putaran:
        jumlah = min(3, len(set(rencana.putaran.tanggal_pemetaan)))
        if jumlah < 3 or rencana.tindakan in {"pemetaan", "tunggu_pemetaan", "probe_diagnostik"}:
            return f"Pemetaan {jumlah} dari 3"
        fokus = _fokus_utama(rencana)
        if fokus:
            status_fokus = _status_fokus(rencana, fokus)
            if status_fokus:
                status = status_fokus.status.replace("_", " ")
                return "Fokus: " + status.capitalize()
        if rencana.putaran.fokus:
            status = rencana.putaran.fokus[0].status.replace("_", " ")
            return "Fokus: " + status.capitalize()
        return "Pemetaan selesai — tidak ada fokus aktif"
    return "Pemetaan 0 dari 3"


def _tanggal_indonesia(nilai: date) -> str:
    bulan = (
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    )
    return f"{nilai.day} {bulan[nilai.month - 1]} {nilai.year}"


def _strip_tahap(rencana: RencanaBelajar, bukti: BuktiSiklus) -> str:
    efektif = _tahap_efektif(rencana, bukti)
    aktif = _TAHAP_TINDAKAN.get(efektif, {
        "latihan_terbimbing": 2,
        "penguatan": 2,
        "evaluasi": 3,
        "checkpoint": 4,
        "pengenalan": 1,
        "maintenance": 5,
    }.get(efektif, 0))
    bagian = []
    for indeks, label in enumerate(_LABEL_TAHAP):
        kelas = " aktif" if indeks == aktif else (" selesai" if indeks < aktif else "")
        bagian.append(
            f'<li class="tahap-rencana-st{kelas}"'
            + (' aria-current="step"' if indeks == aktif else "")
            + f'>{html.escape(label)}</li>'
        )
    return '<ol class="strip-rencana-st" aria-label="Tahap rencana belajar">' + "".join(bagian) + "</ol>"


def _materi(rencana: RencanaBelajar, fokus: Optional[KunciFokus]):
    if rencana.tindakan not in {"intervensi", "pengenalan"} or fokus is None:
        return None
    pilihan = interventions.pilihan_untuk_fokus(fokus)
    status = _status_fokus(rencana, fokus)
    id_pilihan = status.pendekatan_berikutnya if status else None
    return next((item for item in pilihan if item.pendekatan_id == id_pilihan), pilihan[0])


def _tindakan_orang_tua(rencana: RencanaBelajar, materi) -> str:
    if materi is not None:
        return materi.instruksi_orang_tua
    return {
        "lanjutkan_sesi": "Dampingi anak menyelesaikan sesi yang sudah dimulai.",
        "konfirmasi_hasil": "Periksa hasil dan cara anak, lalu konfirmasi agar menjadi bukti belajar.",
        "pemetaan": "Pilih waktu singkat saat anak siap; biarkan ia menunjukkan caranya sendiri.",
        "tunggu_pemetaan": "Beri jeda sampai tanggal berikutnya agar pemetaan tidak menumpuk di satu hari.",
        "probe_diagnostik": "Ajak anak mengerjakan probe baru tanpa memberi tahu jawaban sebelumnya.",
        "latihan_terbimbing": "Kerjakan contoh pertama bersama, lalu minta anak menjelaskan tiap langkah.",
        "penguatan": "Biarkan anak mencoba mandiri; bantu hanya ketika ia benar-benar tersendat.",
        "tunggu_evaluasi": "Jangan mengulang soal fokus dulu; beri jeda agar evaluasi mengukur ingatan yang bertahan.",
        "evaluasi": "Minta anak mengerjakan tanpa melihat contoh, lalu cek apakah ia bisa menjelaskan.",
        "tunggu_checkpoint": "Pertahankan latihan ringan biasa sampai checkpoint jatuh tempo.",
        "checkpoint": "Jalankan sesi pendek tanpa membuka kembali contoh lama.",
        "probe_setelah_pengenalan": "Minta anak mencoba soal baru setelah materi dikenalkan.",
        "mixed_maintenance": "Pilih sesi campuran ringan untuk menjaga materi yang sudah dipelajari.",
        "putaran_baru": "Mulai lagi dari fokus yang kambuh tanpa menghapus keberhasilan sebelumnya.",
        "eskalasi": "Cek prasyarat dasarnya atau lakukan uji ulang lisan sebelum menambah latihan.",
    }.get(rencana.tindakan, "Dampingi anak mengikuti langkah yang disarankan.")


def _form_intervensi(
    rencana: RencanaBelajar,
    siswa_id: int,
    fokus: Optional[KunciFokus],
    materi,
) -> str:
    if fokus is None or materi is None or not materi.tersedia or not rencana.putaran:
        return ""
    aksi = "pengenalan_selesai" if rencana.tindakan == "pengenalan" else "intervensi_selesai"
    label = "Tandai sudah dikenalkan" if aksi == "pengenalan_selesai" else "Tandai sudah dipelajari"
    return (
        f'<form method="post" action="/siklus/{siswa_id}/aksi" class="rencana-form-st">'
        f'<input type="hidden" name="aksi" value="{aksi}">'
        f'<input type="hidden" name="putaran_id" value="{rencana.putaran.id}">'
        f'<input type="hidden" name="template_id" value="{html.escape(fokus[0], quote=True)}">'
        f'<input type="hidden" name="kode_intervensi" value="{html.escape(fokus[1], quote=True)}">'
        f'<input type="hidden" name="malrule_id" value="{html.escape(fokus[2] or "", quote=True)}">'
        f'<input type="hidden" name="pendekatan_id" value="{html.escape(materi.pendekatan_id, quote=True)}">'
        f'<button type="submit" class="rencana-cta-utama-st">{label}</button></form>'
    )


def _pengenalan_siap_ditandai(
    rencana: RencanaBelajar,
    bukti: BuktiSiklus,
    fokus: Optional[KunciFokus],
) -> bool:
    if rencana.tindakan != "pengenalan" or fokus is None or not rencana.putaran:
        return False
    sudah_event = any(
        event.jenis == "pengenalan_selesai"
        and event.putaran_id == rencana.putaran.id
        and event.nilai("fokus", ()) == fokus
        for event in bukti.kejadian
    )
    if sudah_event:
        return False
    return any(
        sesi.putaran_id == rencana.putaran.id
        and sesi.tujuan == "pengenalan"
        and sesi.dibatalkan is None
        and sesi.dikonfirmasi is not None
        and fokus in sesi.target_fokus
        for sesi in bukti.sesi
    )


def _cta(rencana: RencanaBelajar, bukti: BuktiSiklus, siswa_id: int, fokus, materi) -> str:
    if rencana.tindakan in {"lanjutkan_sesi", "konfirmasi_hasil"} and rencana.sesi_id:
        label = "Lanjutkan sesi" if rencana.tindakan == "lanjutkan_sesi" else "Tinjau hasil"
        return f'<a class="rencana-cta-utama-st" href="/sesi/{rencana.sesi_id}">{label}</a>'
    if rencana.tindakan in {"intervensi", "pengenalan"}:
        if rencana.tindakan == "pengenalan":
            if _pengenalan_siap_ditandai(rencana, bukti, fokus):
                return _form_intervensi(rencana, siswa_id, fokus, materi)
            return (
                f'<form method="post" action="/siklus/{siswa_id}/buat" class="rencana-form-st">'
                '<button type="submit" class="rencana-cta-utama-st">Buat sesi pengenalan</button>'
                "</form>"
            )
        return _form_intervensi(rencana, siswa_id, fokus, materi)
    if rencana.tindakan == "putaran_baru":
        return (
            f'<form method="post" action="/siklus/{siswa_id}/aksi" class="rencana-form-st">'
            '<input type="hidden" name="aksi" value="mulai_putaran_baru">'
            '<button type="submit" class="rencana-cta-utama-st">Mulai putaran baru</button></form>'
        )
    if rencana.tindakan in _TINDAKAN_BUAT:
        return (
            f'<form method="post" action="/siklus/{siswa_id}/buat" class="rencana-form-st">'
            '<button type="submit" class="rencana-cta-utama-st">Buat sesi berikutnya</button>'
            "</form>"
        )
    return ""


def _override(rencana: RencanaBelajar, siswa_id: int) -> str:
    if not rencana.putaran or rencana.tindakan not in {"intervensi", "latihan_terbimbing", "penguatan"}:
        return ""
    template_ids = sorted({
        template_id
        for topik_id in topics.daftar_topik()
        if topik_id != "campuran"
        for template_id in topics.ambil(topik_id).komposisi.get(rencana.putaran.level, ())
    })
    opsi_template = "".join(
        f'<option value="{html.escape(template_id, quote=True)}">'
        f'{html.escape(_nama_template(template_id))}</option>'
        for template_id in template_ids
    )
    return (
        '<details class="ubah-fokus-st"><summary>Ubah fokus terpandu</summary>'
        '<p>Mengubah fokus setelah tahap belajar dimulai akan menutup konfigurasi lama '
        'dan membatalkan sesi turunannya tanpa menghapus riwayat.</p>'
        f'<form method="post" action="/siklus/{siswa_id}/aksi">'
        '<input type="hidden" name="aksi" value="ubah_fokus">'
        f'<label>Materi<select name="template_id" required>{opsi_template}</select></label>'
        '<label>Jenis dukungan<select name="kode_intervensi" required>'
        '<option value="K">Pelajari konsep</option><option value="H">Periksa hitungan</option>'
        '<option value="B">Baca ulang soal</option><option value="E">Periksa jawaban akhir</option>'
        '<option value="N">Jelaskan cara</option><option value="T">Kenalkan materi</option>'
        '</select></label><input type="hidden" name="malrule_id" value="">'
        '<label class="konfirmasi-dampak-st">'
        '<input id="konfirmasi-dampak" type="checkbox" required> '
        'Saya memahami konfigurasi lama dapat ditutup.</label>'
        '<button type="submit">Ganti fokus terpandu</button></form></details>'
    )


def _visual_materi(rencana, materi, siswa_id):
    """Bantuan hanya di kartu belajar, tidak pernah di pertanyaan sesi."""
    if (rencana.tindakan not in {"intervensi", "pengenalan"}
            or materi is None or not materi.tersedia or materi.bantuan is None):
        return ""
    from learning_visuals import render_bantuan
    return render_bantuan(
        materi.bantuan, konteks="pelajari_bersama",
        namespace=f"rencana-{siswa_id}-{materi.pendekatan_id}",
    )


def render_rencana(rencana: RencanaBelajar, bukti: BuktiSiklus, siswa_id: int) -> str:
    """Render satu rekomendasi tanpa menulis state domain."""
    if bukti.siswa_id != siswa_id:
        raise ValueError("bukti bukan milik siswa")
    fokus = _fokus_utama(rencana)
    materi = _materi(rencana, fokus)
    tanggal = (
        '<p class="tanggal-rencana-st">Tersedia pada '
        + html.escape(_tanggal_indonesia(rencana.tersedia_pada))
        + ".</p>"
        if rencana.tersedia_pada else ""
    )
    materi_tidak_tersedia = bool(materi is not None and not materi.tersedia)
    contoh = (
        '<div class="contoh-rencana-st"><b>Contoh terbimbing</b>'
        f'<p>{html.escape(materi.contoh_terbimbing)}</p>'
        + _visual_materi(rencana, materi, siswa_id) + '</div>'
        if materi is not None and materi.tersedia and materi.contoh_terbimbing else ""
    )
    catatan_materi = (
        '<p class="rencana-peringatan-st">' + html.escape(materi.instruksi_orang_tua) + "</p>"
        if materi is not None and not materi.tersedia else ""
    )
    instruksi = "" if materi_tidak_tersedia else _tindakan_orang_tua(rencana, materi)
    tindakan = (
        '<div class="tindakan-rencana-st"><b>Yang bisa dilakukan orang tua</b>'
        f'<p>{html.escape(instruksi)}</p></div>' if instruksi else ""
    )
    catatan_histori = "".join(
        f'<p class="sub catatan-histori-level-st">{html.escape(teks)}</p>'
        for teks in catatan_histori_beda_level(
            bukti,
            mulai_dari_awal=(
                rencana.tindakan == "pemetaan"
                and bool(rencana.putaran)
                and not rencana.putaran.tanggal_pemetaan
            ),
        )
    )
    return (
        '<section class="kartu-rencana-st" aria-labelledby="judul-rencana-belajar">'
        '<p class="label-rencana-st">Rencana belajar hari ini</p>'
        f'<h2 class="st" id="judul-rencana-belajar">{html.escape(_judul(rencana, fokus, bukti))}</h2>'
        f'<p class="alasan-rencana-st">{html.escape(_alasan(rencana, fokus))}</p>'
        f'<p class="progres-rencana-st">{html.escape(_progres(rencana, bukti))}</p>'
        f'{catatan_histori}{_strip_tahap(rencana, bukti)}{tindakan}{contoh}{catatan_materi}{tanggal}'
        f'{_cta(rencana, bukti, siswa_id, fokus, materi)}{_override(rencana, siswa_id)}'
        "</section>"
    )


def kartu_rencana(kon, siswa_id: int) -> str:
    """Muat bukti sah dan render rekomendasi reducer pada GET profil."""
    bukti = database.muat_bukti_siklus(kon, siswa_id)
    rencana = rencana_berikutnya(bukti, siswa_id)
    return render_rencana(rencana, bukti, siswa_id)
