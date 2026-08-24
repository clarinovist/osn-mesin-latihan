"""Skema basis data mesin latihan.

Keputusan bentuk data yang menentukan seluruh sisanya:

**Yang disimpan adalah parameter, bukan teks soal.** Tabel `soal` menyimpan
`template_id` + `parameter` + `kunci`, dan teks soalnya dibangkitkan ulang
saat perlu. Konsekuensinya: soal dengan angka berbeda tetap bisa
dibandingkan lewat `template_id`, dan bank soal tumbuh sendiri tiap
generate tanpa duplikat (dijaga `tanda_tangan` yang UNIQUE).

**Diagnosis dipisah dari jawaban.** Satu jawaban bisa didiagnosis ulang
kalau guru berubah pikiran, tanpa kehilangan jawaban aslinya. Kolom
`kode_usulan` (dari mesin) dan `kode_final` (dari guru) sengaja terpisah —
supaya nanti bisa diukur seberapa sering mesin salah menebak.

**Miskonsepsi dicatat sebagai malrule_id, bukan nomor soal.** Ini yang
membuat "satu miskonsepsi yang muncul di tiga soal" terhitung satu, sesuai
aturan di lembar penilaian.
"""

SKEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Anak. Disimpan inisial/nama panggilan saja, bukan nama lengkap:
-- mengurangi dampak kalau basis data ini bocor.
CREATE TABLE IF NOT EXISTS siswa (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nama        TEXT    NOT NULL UNIQUE,
    tingkat     TEXT    NOT NULL DEFAULT 'P3',
    dibuat      TEXT    NOT NULL DEFAULT (datetime('now', '+7 hours'))
);

-- Bank soal. Tumbuh tiap generate; tanda_tangan mencegah duplikat.
CREATE TABLE IF NOT EXISTS soal (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tanda_tangan  TEXT    NOT NULL UNIQUE,
    template_id   TEXT    NOT NULL,
    parameter     TEXT    NOT NULL,          -- JSON
    kunci         TEXT    NOT NULL,
    bagian        TEXT    NOT NULL DEFAULT '',
    tantangan     INTEGER NOT NULL DEFAULT 0,
    dibuat        TEXT    NOT NULL DEFAULT (datetime('now', '+7 hours'))
);

CREATE INDEX IF NOT EXISTS idx_soal_template ON soal(template_id);

-- Malrule per soal: jawaban salah yang bisa diprediksi + kodenya.
-- Disimpan (bukan dihitung saat baca) supaya diagnosis lama tetap terbaca
-- apa adanya kalau definisi malrule di kode berubah kemudian.
CREATE TABLE IF NOT EXISTS malrule (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    soal_id    INTEGER NOT NULL REFERENCES soal(id) ON DELETE CASCADE,
    malrule_id TEXT    NOT NULL,
    jawaban    TEXT    NOT NULL,
    kode       TEXT    NOT NULL CHECK (kode IN ('B','K','H','E','T','N')),
    alasan     TEXT    NOT NULL DEFAULT '',
    UNIQUE (soal_id, malrule_id)
);

-- Satu kali latihan. seed disimpan supaya lembarnya bisa dicetak ulang persis.
CREATE TABLE IF NOT EXISTS sesi (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    siswa_id  INTEGER NOT NULL REFERENCES siswa(id) ON DELETE CASCADE,
    seed      INTEGER NOT NULL,
    topik     TEXT    NOT NULL DEFAULT 'pola bilangan',
    tanggal   TEXT    NOT NULL DEFAULT (date('now', '+7 hours')),
    mulai     TEXT,
    selesai   TEXT,
    catatan   TEXT    NOT NULL DEFAULT '',
    dibuat    TEXT    NOT NULL DEFAULT (datetime('now', '+7 hours'))
);

CREATE INDEX IF NOT EXISTS idx_sesi_siswa ON sesi(siswa_id, tanggal);

-- Urutan soal dalam satu sesi.
CREATE TABLE IF NOT EXISTS sesi_soal (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    sesi_id  INTEGER NOT NULL REFERENCES sesi(id) ON DELETE CASCADE,
    soal_id  INTEGER NOT NULL REFERENCES soal(id),
    nomor    INTEGER NOT NULL,
    UNIQUE (sesi_id, nomor)
);

-- Jawaban anak. Empat kotak dari format lembar diagnostik:
--   restatement    -> "soal ini mintanya apa?"  (memisahkan B)
--   cara           -> kotak "Caraku"            (memisahkan K dari H)
--   jawaban        -> jawaban akhir             (memisahkan E)
--   belum_pernah   -> centang "belum pernah lihat" (memisahkan T dari N)
CREATE TABLE IF NOT EXISTS jawaban (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sesi_soal_id  INTEGER NOT NULL UNIQUE REFERENCES sesi_soal(id) ON DELETE CASCADE,
    restatement   TEXT    NOT NULL DEFAULT '',
    cara          TEXT    NOT NULL DEFAULT '',
    jawaban       TEXT    NOT NULL DEFAULT '',
    belum_pernah  INTEGER NOT NULL DEFAULT 0,
    detik         INTEGER,
    dicatat       TEXT    NOT NULL DEFAULT (datetime('now', '+7 hours'))
);

-- Diagnosis. kode_usulan dari mesin, kode_final dari guru.
-- Dipisah supaya akurasi mesin bisa diukur belakangan.
CREATE TABLE IF NOT EXISTS diagnosis (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    jawaban_id    INTEGER NOT NULL UNIQUE REFERENCES jawaban(id) ON DELETE CASCADE,
    benar         INTEGER NOT NULL DEFAULT 0,
    kode_usulan   TEXT    CHECK (kode_usulan IS NULL OR kode_usulan IN ('B','K','H','E','T','N')),
    kode_final    TEXT    CHECK (kode_final  IS NULL OR kode_final  IN ('B','K','H','E','T','N')),
    malrule_id    TEXT,
    alasan        TEXT    NOT NULL DEFAULT '',
    manual        INTEGER NOT NULL DEFAULT 0,   -- guru mengubah usulan mesin
    catatan       TEXT    NOT NULL DEFAULT '',
    didiagnosis   TEXT    NOT NULL DEFAULT (datetime('now', '+7 hours'))
);

-- Ringkasan per sesi supaya laporan tidak perlu menghitung ulang tiap buka.
CREATE VIEW IF NOT EXISTS ringkasan_sesi AS
SELECT
    s.id                                              AS sesi_id,
    s.siswa_id,
    w.nama                                            AS siswa,
    s.tanggal,
    s.seed,
    COUNT(ss.id)                                      AS jumlah_soal,
    SUM(COALESCE(d.benar, 0))                         AS benar,
    SUM(CASE WHEN d.kode_final = 'K' THEN 1 ELSE 0 END) AS k,
    SUM(CASE WHEN d.kode_final = 'B' THEN 1 ELSE 0 END) AS b,
    SUM(CASE WHEN d.kode_final = 'H' THEN 1 ELSE 0 END) AS h,
    SUM(CASE WHEN d.kode_final = 'E' THEN 1 ELSE 0 END) AS e,
    SUM(CASE WHEN d.kode_final = 'T' THEN 1 ELSE 0 END) AS t,
    SUM(CASE WHEN d.kode_final = 'N' THEN 1 ELSE 0 END) AS n
FROM sesi s
JOIN siswa w        ON w.id = s.siswa_id
LEFT JOIN sesi_soal ss ON ss.sesi_id = s.id
LEFT JOIN jawaban j    ON j.sesi_soal_id = ss.id
LEFT JOIN diagnosis d  ON d.jawaban_id = j.id
GROUP BY s.id;
"""
