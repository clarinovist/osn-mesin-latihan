"""Halaman akun (guru) & admin: kelola siswa, akun latihan, sandi.

Dipecah dari web.py (refactor 31 Aug 2026) — fungsi pindah utuh, perilaku
identik. Frame halaman diimpor dari teacher_pages. Admin baca-semua-
tulis-tidak: penulisan tetap ditolak di router (web.py).
"""

from __future__ import annotations

import html

import auth
import database
from generator import LEVEL_BAWAAN
from templates import LEVEL, level_valid
from teacher_pages import _halaman



PETA_SECTION_AKUN = {
    # Aksi POST /akun -> section tempat hasilnya ditampilkan, supaya
    # pengguna kembali ke tempat formnya, bukan melompat ke bawaan.
    "sandi": "akun",
    "anak_baru": "siswa",
    "tingkat": "siswa",
    "siswa_hapus": "siswa",
    "akun_murid_tambah": "akun-murid",
    "akun_murid_hapus": "akun-murid",
    "akun_murid_sandi": "akun-murid",
}

def _kartu_akun_murid(kon, pengguna: str | None = None, peran: str = "guru") -> str:
    """Kartu akun murid di halaman akun.

    Pola persis kartu Siswa: tabel + form di bawahnya. Daftar akun diambil
    dari auth.muat_akun() yang disaring peran == murid. Tiap akun dicek
    kecocokannya dengan tabel siswa lewat students.siswa_dari_akun; kalau tidak
    cocok ditandai jelas "belum terhubung ke siswa" supaya guru tahu kenapa
    anak tidak bisa masuk. Guru hanya melihat & mengelola akun keluarganya;
    panggilan langsung tanpa `pengguna` (mode lokal / test) melihat semua.
    """
    import students as _murid

    filter_siswa = None if (peran == "admin" or pengguna is None) else pengguna
    daftar_siswa = database.daftar_siswa(kon, filter_siswa)
    akun_murid = [a for a in auth.muat_akun() if a.get("peran") == "murid"]
    if pengguna is not None and peran != "admin":
        akun_murid = [
            a
            for a in akun_murid
            if _akun_murid_milik(kon, pengguna, peran, a["pengguna"])
        ]

    if akun_murid:
        baris = ""
        for a in akun_murid:
            nama = a["pengguna"]
            nama_esc = html.escape(nama)
            sid = _murid.siswa_dari_akun(kon, nama)
            if sid is None:
                status = '<span class="status-buruk">belum terhubung ke siswa</span>'
            else:
                status = '<span class="status-ok">terhubung</span>'
            baris += (
                f"<tr><td>{nama_esc}</td><td>{status}</td><td>"
                f'<div class="baris-aksi">'
                f'<form method="post" action="/akun" style="display:inline-flex;gap:.3rem;align-items:center">'
                f'<input type="hidden" name="aksi" value="akun_murid_hapus">'
                f'<input type="hidden" name="nama" value="{nama_esc}">'
                f'<button type="submit" class="tombol-kecil tombol-hapus">Hapus</button>'
                f"</form> "
                f'<form method="post" action="/akun" style="display:inline-flex;gap:.3rem;align-items:center;margin-left:.4rem">'
                f'<input type="hidden" name="aksi" value="akun_murid_sandi">'
                f'<input type="hidden" name="nama" value="{nama_esc}">'
                f'<input type="password" name="baru" placeholder="sandi baru" required style="width:130px;padding:.3rem .5rem">'
                f'<button type="submit" class="tombol-kecil">Setel sandi baru</button>'
                f"</form>"
                f"</div>"
                f"</td></tr>"
            )
    else:
        baris = '<tr><td colspan="3" class="kosong">belum ada akun murid</td></tr>'

    if daftar_siswa:
        opsi = "".join(
            f'<option value="{s["id"]}">{html.escape(s["nama"])}</option>'
            for s in daftar_siswa
        )
        pilih = f'<select name="siswa_id" required><option value="">— pilih siswa —</option>{opsi}</select>'
        dis = ""
    else:
        pilih = '<select name="siswa_id" disabled><option>belum ada siswa</option></select>'
        dis = " disabled"

    tambah = (
        f'<form method="post" action="/akun" style="margin-top:.8rem">'
        f'<input type="hidden" name="aksi" value="akun_murid_tambah">'
        f'<div class="baris">'
        f"<div><label>Siswa</label>"
        f"{pilih}</div>"
        f"<div><label>Nama untuk masuk</label>"
        f'<input type="text" name="nama_akun" placeholder="mis. bima-santoso" required></div>'
        f"</div>"
        f'<div><label>Sandi baru (minimal 8 karakter)</label>'
        f'<input type="password" name="sandi" placeholder="sandi untuk murid" required minlength="8">'
        f"</div>"
        f'<p style="margin-top:.6rem"><button type="submit"{dis}>Tambah akun murid</button></p>'
        f"</form>"
    )

    return (
        f'<div class="kartu"><h2>Akun murid</h2>'
        f"<p class=\"sub\">Akun murid dipakai anak untuk masuk ke /murid. "
        f"Nama untuk masuk harus unik di seluruh aplikasi — kalau sudah "
        f"dipakai keluarga lain, pakai variasi lain (mis. tambah nama belakang).</p>"
        f"<table><tr><th>Nama</th><th>Status</th><th>Aksi</th></tr>{baris}</table>"
        f"{tambah}"
        f"</div>"
    )

def status_akun_latihan(kon, siswa_id: int) -> str:
    """Sel status akun latihan untuk tabel siswa.

    Nama login bila anaknya sudah punya akun, penanda jelas bila belum —
    supaya jelas bahwa menghapus akun latihan tidak menghapus anaknya.
    """
    import students as _murid

    nama = _murid.akun_murid_dari_siswa(kon, siswa_id)
    if nama:
        return f'<span class="status-ok">{html.escape(nama)}</span>'
    return '<span class="status-buruk">belum ada login</span>'

def halaman_akun(
    kon,
    pesan: str = "",
    galat: str = "",
    pengguna: str | None = None,
    peran: str = "guru",
    section: str = "akun",
) -> bytes:
    """Kelola sandi dan daftar siswa — sidebar + section, tanpa JS.

    Satu halaman, tiga section via ?section=: "akun" (ganti sandi),
    "siswa" (daftar anak + hapus aman), "akun-murid" (akun latihan anak).
    Nilai tak dikenal jatuh ke "akun". Admin hanya punya section "akun" —
    data keluarga lain bukan ranahnya (baca-semua-tulis-tidak).

    `pengguna`/`peran` berasal dari sesi: guru melihat & mengelola
    keluarganya saja. Panggilan langsung tanpa `pengguna` (mode lokal,
    test) melihat semuanya — perilaku lama.

    Sandi bisa diganti dari sini supaya sandi acak hasil deploy tidak jadi
    satu-satunya yang pernah ada. Siswa ber-riwayat sengaja tidak bisa
    dihapus dari sini — penjelasannya ada di kartu Catatan, section
    siswa; siswa tanpa riwayat boleh dihapus beserta akun latihannya.
    """
    admin = peran == "admin"
    if admin or section not in ("akun", "siswa", "akun-murid"):
        # Admin cuma punya satu section; nilai asing dari URL jatuh ke bawaan.
        section = "akun"

    daftar = "".join(
        f'<tr><td>{html.escape(s["nama"])}</td>'
        f'<td><form method="post" action="/akun" style="display:flex;gap:.4rem">'
        f'<input type="hidden" name="aksi" value="tingkat">'
        f'<input type="hidden" name="siswa_id" value="{s["id"]}">'
        f'<select name="tingkat" style="width:auto">'
        + "".join(
            f'<option value="{lv}"{" selected" if lv == s["tingkat"] else ""}>{lv}</option>'
            for lv in LEVEL
        )
        + '</select>'
        f'<button type="submit" style="padding:.3rem .7rem;font-size:.85rem">'
        f"Simpan</button></form></td>"
        f'<td class="angka">'
        f'{kon.execute("SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (s["id"],)).fetchone()["n"]}'
        f"</td>"
        f"<td>{status_akun_latihan(kon, s['id'])}</td>"
        f'<td><form method="post" action="/akun" style="display:inline-flex">'
        f'<input type="hidden" name="aksi" value="siswa_hapus">'
        f'<input type="hidden" name="siswa_id" value="{s["id"]}">'
        f'<button type="submit" class="tombol-kecil tombol-hapus">Hapus</button>'
        f"</form></td></tr>"
        for s in database.daftar_siswa(kon, None if peran == "admin" else pengguna)
    )

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    if galat:
        kabar += f'<div class="pesan galat">{html.escape(galat)}</div>'

    if pengguna is not None:
        pengguna_tampil = html.escape(pengguna)
    else:
        d = auth.muat_sandi()
        if not d:
            pengguna_tampil = "(belum disetel)"
        elif "akun" in d:
            g = next((a for a in d["akun"] if a.get("peran") in ("guru", "admin")), None)
            pengguna_tampil = html.escape(g["pengguna"]) if g else "(belum disetel)"
        else:
            pengguna_tampil = html.escape(d["pengguna"])

    kartu_sandi = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🔑</span>'
        f"<h2>Ganti sandi</h2></div>"
        f'<p class="sub">Pengguna saat ini: <b>{pengguna_tampil}</b>. Setelah diganti, '
        f"masuk lagi dengan sandi baru.</p>"
        f'<form method="post" action="/akun">'
        f'<input type="hidden" name="aksi" value="sandi">'
        f"<label>Sandi lama</label>"
        f'<input type="password" name="lama" autocomplete="current-password" required>'
        f"<label>Sandi baru (minimal 12 karakter)</label>"
        f'<input type="password" name="baru" autocomplete="new-password" required>'
        f"<label>Ulangi sandi baru</label>"
        f'<input type="password" name="ulang" autocomplete="new-password" required>'
        f'<p style="margin-top:.8rem">'
        f'<button type="submit" class="tombol-sekunder">Ganti sandi</button></p>'
        f"</form></div>"
    )
    kartu_siswa = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">📚</span>'
        f"<h2>Siswa</h2></div>"
        f'<div class="tabel-wrap"><table><tr><th>Nama</th><th>Tingkat</th>'
        f"<th>Sesi</th><th>Akun latihan</th><th>Aksi</th></tr>{daftar}</table></div>"
        f'<p class="sub" style="margin-top:.7rem">Anak baru ditambahkan dari '
        f'kartu "Tambah anak" di bawah — sekalian dengan akun latihannya.'
        f"</p></div>"
    )
    kartu_anak = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🧒</span>'
        f"<h2>Tambah anak</h2></div>"
        f'<p class="sub">Satu langkah untuk pengguna baru: buat siswa '
        f"sekaligus akun yang dipakai anak untuk masuk ke /murid dari HP. "
        f"Pakai nama panggilan atau inisial, bukan nama lengkap — "
        f"mengurangi dampak bila basis data ini bocor.</p>"
        f'<form method="post" action="/akun">'
        f'<input type="hidden" name="aksi" value="anak_baru">'
        f'<div class="baris">'
        f'<div><label>Nama anak (nama panggilan)</label>'
        f'<input type="text" name="nama" placeholder="mis. Aisha" required></div>'
        f'<div><label>Tingkat</label>'
        f'<select name="tingkat">'
        + "".join(
            f'<option value="{lv}"{" selected" if lv == LEVEL_BAWAAN else ""}>{lv}</option>'
            for lv in LEVEL
        )
        + f"</select></div></div>"
        f"<label>Nama login anak (opsional — bawaan sama dengan nama anak)"
        f"</label>"
        f'<input type="text" name="nama_akun" '
        f'placeholder="diisi bila nama anak sudah dipakai keluarga lain">'
        f"<label>Kata sandi anak (minimal 8 karakter)</label>"
        f'<input type="password" name="sandi_anak" autocomplete="new-password" '
        f'required minlength="8">'
        f'<p style="font-size:.9rem">'
        f'<label style="display:flex;gap:.5rem;align-items:flex-start">'
        f'<input type="checkbox" name="persetujuan_ortu" value="1" style="margin-top:.25rem">'
        f"<span>Saya orang tua/wali anak ini dan menyetujui "
        f'<a href="/kebijakan-privasi">Kebijakan Privasi</a> untuk data anak.</span>'
        f"</label></p>"
        f'<button type="submit" class="tombol-coral">Buat anak &amp; akunnya</button>'
        f"</form></div>"
    )
    kartu_catatan = (
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu amber">💡</span>'
        f"<h2>Catatan</h2></div>"
        f'<p class="sub">Siswa yang masih punya riwayat sesi sengaja tidak '
        f"bisa dihapus: menghapusnya ikut memusnahkan seluruh sesi, "
        f"jawaban, dan diagnosisnya — riwayat yang tidak bisa dibangun "
        f"ulang. Kalau seorang anak berhenti, biarkan saja datanya; ia "
        f"tidak mengganggu apa pun.</p>"
        f'<p class="sub">Siswa tanpa riwayat (salah ketik atau data uji) '
        f"boleh dihapus — akun latihannya ikut dihapus sekalian.</p>"
        f'<p class="sub">Cadangan basis data ditarik otomatis ke Mac tiap '
        f"malam pukul 22:00.</p></div>"
    )

    if section == "siswa":
        isi_section = kartu_siswa + kartu_anak + kartu_catatan
    elif section == "akun-murid":
        isi_section = _kartu_akun_murid(kon, pengguna, peran)
    else:
        isi_section = kartu_sandi

    item = [
        ("akun", "Akun saya"),
        ("siswa", "Siswa"),
        ("akun-murid", "Akun latihan"),
    ]
    if admin:
        item = item[:1]
    nav = "".join(
        f'<a href="/akun?section={sid}"'
        + (' class="aktif"' if sid == section else "")
        + f">{label}</a>"
        for sid, label in item
    )

    return _halaman(
        "Akun",
        f'<div class="jejak"><a href="/">&larr; Semua siswa</a></div>'
        f"<h1>Akun &amp; pengaturan</h1>"
        f"{kabar}"
        f'<div class="layout-samping">'
        f'<nav class="nav-samping">{nav}</nav>'
        f"<div>{isi_section}</div>"
        f"</div>",
        ident=(pengguna or "guru", peran),
    )

def _akun_murid_milik(kon, pengguna: str, peran: str, nama: str) -> bool:
    """Apakah akun murid `nama` boleh dikelola oleh pengguna ini?

    Admin boleh semua. Guru hanya akun murid yang terikat ke siswa
    miliknya — lewat siswa_id eksplisit, atau (akun warisan) lewat nama
    siswa ber-pemilik dirinya.
    """
    if peran == "admin":
        return True
    a = auth.cari_akun(nama)
    if not a or a.get("peran") != "murid":
        return False
    if a.get("siswa_id") is not None:
        return database.siswa_milik(kon, int(a["siswa_id"]), pengguna)
    baris = kon.execute(
        "SELECT 1 FROM siswa WHERE nama = ? COLLATE NOCASE AND pemilik = ?",
        (nama, pengguna),
    ).fetchone()
    return baris is not None

def proses_akun(
    kon, data: dict, pengguna_kini: str, peran: str = "guru"
) -> tuple[str, str]:
    """Jalankan aksi halaman akun. Mengembalikan (pesan, galat).

    Sandi lama SELALU diverifikasi ulang, walaupun pengguna sudah lolos
    palang untuk membuka halaman ini. Peramban menyimpan kredensial Basic
    dan mengirimkannya otomatis, jadi tanpa pemeriksaan ini siapa pun yang
    menemukan laptop dalam keadaan terbuka bisa mengganti sandi tanpa tahu
    yang lama.

    Multi-keluarga: siswa yang dibuat tercatat ber-pemilik pengguna_kini,
    dan aksi ber-id (tingkat, akun murid) hanya menyentuh milik sendiri —
    admin bebas, dengan `peran="admin"`.
    """
    aksi = data.get("aksi", "")

    if aksi == "sandi":
        lama = data.get("lama", "")
        baru = data.get("baru", "")
        ulang = data.get("ulang", "")

        if not auth.periksa(pengguna_kini, lama):
            return "", "Sandi lama salah."
        if baru != ulang:
            return "", "Sandi baru dan ulangannya tidak sama."
        if len(baru) < 12:
            return "", "Sandi baru minimal 12 karakter."
        if baru == lama:
            return "", "Sandi baru sama dengan yang lama."

        auth.simpan_sandi(baru, pengguna_kini)
        return (
            "Sandi diganti. Masuk lagi dengan sandi baru.",
            "",
        )

    if aksi == "anak_baru":
        """Onboarding publik: siswa + akun murid sekaligus (atomic).

        Validasi SEMUA dulu sebelum menulis apa pun — siswa yang dibuat
        lalu akunnya gagal meninggalkan siswa tanpa akun ("anak yatim")
        yang hanya bisa dirapikan manual lewat halaman akun.
        """
        nama = data.get("nama", "").strip()
        tingkat = data.get("tingkat", LEVEL_BAWAAN).strip() or LEVEL_BAWAAN
        sandi_anak = data.get("sandi_anak", "")
        # Nama login boleh beda dari nama anak — jalannya bila nama anak
        # sudah dipakai keluarga lain sebagai login (nama anak tetap unik
        # per keluarga, nama login unik global).
        nama_akun = (data.get("nama_akun") or "").strip() or nama

        if not nama:
            return "", "Nama anak tidak boleh kosong."
        if len(nama) > 40:
            return "", "Nama terlalu panjang."
        if not level_valid(tingkat):
            return "", f"Tingkat harus salah satu dari: {', '.join(LEVEL)}."
        if len(sandi_anak) < 8:
            return "", "Kata sandi anak minimal 8 karakter."
        if kon.execute(
            "SELECT 1 FROM siswa WHERE lower(nama) = lower(?) AND pemilik = ?",
            (nama, pengguna_kini),
        ).fetchone():
            return "", f"Siswa bernama {nama} sudah ada di keluargamu."
        if auth.cari_akun(nama_akun) is not None:
            return "", f"Nama {nama_akun} sudah dipakai akun lain. Pakai nama lain."

        siswa_id = database.tambah_siswa(kon, nama, tingkat, pemilik=pengguna_kini)
        try:
            auth.tambah_akun(nama_akun, sandi_anak, "murid", siswa_id=siswa_id)
        except ValueError as e:
            # Pembuatan akun meledak di tengah: batalkan siswa yang baru
            # dibuat supaya tidak ada anak yatim tanpa akun.
            kon.execute(
                "DELETE FROM siswa WHERE id = ? AND NOT EXISTS "
                "(SELECT 1 FROM sesi WHERE sesi.siswa_id = siswa.id)",
                (siswa_id,),
            )
            return "", str(e)
        catatan = " (persetujuan orang tua dicatat)" if data.get("persetujuan_ortu") else ""
        return (
            f"Anak {nama} ditambahkan ({tingkat}) beserta akun latihannya{catatan}. "
            f"Anak masuk lewat /murid dengan nama {nama_akun}.",
            "",
        )

    if aksi == "tingkat":
        # Menaikkan level anak. Sesi LAMA tidak ikut berubah — levelnya
        # tersimpan di baris sesi masing-masing, jadi riwayat tetap terbaca
        # apa adanya. Yang berubah hanya sesi yang dibuat setelah ini.
        try:
            siswa_id = int(data.get("siswa_id", ""))
        except ValueError:
            return "", "Siswa tidak dikenal."
        tingkat = data.get("tingkat", "").strip()
        if not level_valid(tingkat):
            return "", f"Tingkat harus salah satu dari: {', '.join(LEVEL)}."
        baris = kon.execute(
            "SELECT nama FROM siswa WHERE id = ?", (siswa_id,)
        ).fetchone()
        if not baris or (
            peran != "admin"
            and not database.siswa_milik(kon, siswa_id, pengguna_kini)
        ):
            return "", "Siswa tidak dikenal."
        kon.execute(
            "UPDATE siswa SET tingkat = ? WHERE id = ?", (tingkat, siswa_id)
        )
        return (
            f"{baris['nama']} sekarang {tingkat}. Sesi lama tetap pada "
            f"levelnya masing-masing; yang berubah hanya sesi berikutnya.",
            "",
        )

    if aksi == "siswa_hapus":
        # Pengaman riwayat: menghapus siswa = CASCADE menghapus seluruh
        # sesi, jawaban, dan diagnosisnya. Yang sudah berriwayat sengaja
        # tak bisa dihapus; yang kosong (salah ketik / data uji) boleh,
        # dan akun latihannya ikut dihapus supaya tak ada anak yatim.
        try:
            siswa_id = int(data.get("siswa_id", ""))
        except ValueError:
            return "", "Siswa tidak dikenal."
        baris = kon.execute(
            "SELECT nama FROM siswa WHERE id = ?", (siswa_id,)
        ).fetchone()
        if not baris or (
            peran != "admin"
            and not database.siswa_milik(kon, siswa_id, pengguna_kini)
        ):
            return "", "Siswa tidak dikenal."
        nama = baris["nama"]
        n_sesi = kon.execute(
            "SELECT COUNT(*) AS n FROM sesi WHERE siswa_id = ?", (siswa_id,)
        ).fetchone()["n"]
        if n_sesi:
            return (
                "",
                f"{nama} masih punya {n_sesi} sesi. Siswa ber-riwayat "
                f"sengaja tidak bisa dihapus — sesi, jawaban, dan "
                f"diagnosisnya tidak bisa dibangun ulang.",
            )
        import students as _murid

        login = _murid.akun_murid_dari_siswa(kon, siswa_id)
        if login:
            auth.hapus_akun(login)
        kon.execute("DELETE FROM siswa WHERE id = ?", (siswa_id,))
        return f"Siswa {nama} dihapus beserta akun latihannya.", ""

    if aksi == "akun_murid_tambah":
        nama_siswa = (data.get("nama") or "").strip()
        nama_akun = (data.get("nama_akun") or "").strip()
        sandi_baru = data.get("sandi", "")
        # kalau form lama masih mengirim "baru", dukung juga
        if not sandi_baru:
            sandi_baru = data.get("baru", "")

        siswa_id = None
        if data.get("siswa_id"):
            # Bentuk form baru: pilih siswa dari dropdown milik sendiri,
            # lalu tentukan nama login-nya (boleh berbeda dari nama siswa).
            try:
                siswa_id = int(data["siswa_id"])
            except ValueError:
                return "", "Siswa tidak dikenal."
            if peran != "admin" and not database.siswa_milik(
                kon, siswa_id, pengguna_kini
            ):
                return "", "Siswa tidak dikenal."
            baris = kon.execute(
                "SELECT nama FROM siswa WHERE id = ?", (siswa_id,)
            ).fetchone()
            nama_siswa = baris["nama"]
        elif nama_siswa:
            # Bentuk lama: nama akun = nama siswa. Pencarian dibatasi ke
            # keluarga sendiri supaya nama dobel antar keluarga tak ambigu.
            if peran == "admin":
                baris = kon.execute(
                    "SELECT id, nama FROM siswa WHERE nama = ? COLLATE NOCASE",
                    (nama_siswa,),
                ).fetchone()
            else:
                baris = kon.execute(
                    "SELECT id, nama FROM siswa "
                    "WHERE nama = ? COLLATE NOCASE AND pemilik = ?",
                    (nama_siswa, pengguna_kini),
                ).fetchone()
            if not baris:
                return "", f"Siswa bernama {nama_siswa} tidak ditemukan."
            siswa_id = int(baris["id"])
        else:
            return "", "Pilih siswanya dulu."

        if not nama_akun:
            nama_akun = nama_siswa
        if len(sandi_baru) < 8:
            return "", "Sandi murid minimal 8 karakter."
        try:
            auth.tambah_akun(nama_akun, sandi_baru, "murid", siswa_id=siswa_id)
        except ValueError as e:
            return "", str(e)
        return f"Akun murid {nama_akun} ditambahkan.", ""

    if aksi == "akun_murid_hapus":
        nama = data.get("nama", "").strip()
        if not nama:
            return "", "Nama tidak boleh kosong."
        if not _akun_murid_milik(kon, pengguna_kini, peran, nama):
            return "", f"Akun {nama} tidak ditemukan."
        ok = auth.hapus_akun(nama)
        if not ok:
            return "", f"Akun {nama} tidak ditemukan."
        return f"Akun murid {nama} dihapus.", ""

    if aksi == "akun_murid_sandi":
        nama = data.get("nama", "").strip()
        baru = data.get("baru", "")
        if not nama:
            return "", "Nama tidak boleh kosong."
        if len(baru) < 8:
            return "", "Sandi murid minimal 8 karakter."
        if not _akun_murid_milik(kon, pengguna_kini, peran, nama):
            return "", f"Akun {nama} tidak ditemukan."
        ok = auth.setel_sandi_murid(nama, baru)
        if not ok:
            return "", f"Akun {nama} tidak ditemukan."
        return f"Sandi {nama} diperbarui.", ""

    return "", "Aksi tidak dikenal."

def halaman_admin(
    kon, pesan: str = "", galat: str = "", pengguna: str = ""
) -> bytes:
    """Dashboard admin: ringkasan, daftar keluarga, buat akun orang tua.

    Hanya peran admin yang sampai sini — penjaganya ada di router, dan
    sejak login admin langsung diarahkan ke sini. Kebijakan admin
    baca-semua-tulis-tidak: satu-satunya tulisan di halaman ini adalah
    membuat akun orang tua (domain admin sendiri); data murid hanya bisa
    DIBACA — nama anak jadi tautan ke laporannya, aksi tulis data murid
    ditolak 404 di router.
    """
    akun = auth.muat_akun()
    n_keluarga = sum(1 for a in akun if a.get("peran", "guru") == "guru")
    total_siswa = kon.execute("SELECT COUNT(*) AS n FROM siswa").fetchone()["n"]
    total_sesi = kon.execute("SELECT COUNT(*) AS n FROM sesi").fetchone()["n"]
    ringkas = (
        '<div class="kartu-stat">'
        f'<div class="stat"><div class="angka-besar">{n_keluarga}</div>'
        f'<div class="stat-label">keluarga</div></div>'
        f'<div class="stat"><div class="angka-besar">{total_siswa}</div>'
        f'<div class="stat-label">siswa</div></div>'
        f'<div class="stat"><div class="angka-besar">{total_sesi}</div>'
        f'<div class="stat-label">sesi</div></div>'
        "</div>"
    )

    keluarga = []
    for a in akun:
        if a.get("peran", "guru") not in ("guru", "admin"):
            continue
        nama = a["pengguna"]
        anak = database.daftar_siswa(kon, nama)
        daftar_anak = (
            ", ".join(
                f'<a href="/laporan/{s["id"]}">{html.escape(s["nama"])}</a>'
                for s in anak
            )
            or '<span class="kosong">belum ada anak</span>'
        )
        terakhir = kon.execute(
            """SELECT MAX(s.tanggal) AS t FROM sesi s
               JOIN siswa w ON w.id = s.siswa_id WHERE w.pemilik = ?""",
            (nama,),
        ).fetchone()["t"] or "—"
        peran_label = "Pengelola" if a.get("peran") == "admin" else "Orang Tua"
        keluarga.append(
            f"<tr><td>{html.escape(nama)}</td>"
            f"<td>{peran_label}</td>"
            f'<td class="angka">{len(anak)}</td>'
            f"<td>{daftar_anak}</td>"
            f"<td>{terakhir}</td></tr>"
        )
    tabel = (
        "<table><tr><th>Akun</th><th>Peran</th><th>Jumlah anak</th>"
        f"<th>Nama anak</th><th>Sesi terakhir</th></tr>{''.join(keluarga)}</table>"
    )

    kabar = f'<div class="pesan">{html.escape(pesan)}</div>' if pesan else ""
    if galat:
        kabar += f'<div class="pesan galat">{html.escape(galat)}</div>'

    return _halaman(
        "Panel Pengelola",
        f"<h1>Panel Pengelola</h1>"
        f'{kabar}'
        f"{ringkas}"
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">🏡</span>'
        f"<h2>Keluarga</h2></div>"
        f"{tabel}"
        f"</div>"
        f'<div class="kartu">'
        f'<div class="kartu-judul"><span class="ikon-kartu">➕</span>'
        f"<h2>Buat akun orang tua</h2></div>"
        f'<form method="post" action="/admin">'
        f'<input type="hidden" name="aksi" value="guru_baru">'
        f'<div class="baris">'
        f'<div><label>Nama akun</label>'
        f'<input type="text" name="pengguna" autocomplete="off" required></div>'
        f"<div><label>Kata sandi (minimal 12 karakter)</label>"
        f'<input type="password" name="sandi" autocomplete="new-password" '
        f'required minlength="12"></div>'
        f"</div>"
        f'<p style="margin-top:.8rem">'
        f'<button type="submit" class="tombol-coral">Buat akun</button></p>'
        f"</form>"
        f'<p class="sub">Orang tua juga bisa mendaftar sendiri di '
        f'<a href="/daftar">/daftar</a> — setelah isolasi, pendaftar baru '
        f"tidak melihat data keluarga mana pun.</p>"
        f"</div>",
        ident=(pengguna, "admin") if pengguna else None,
    )
