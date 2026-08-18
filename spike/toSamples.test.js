// Golden test wajib (PRD §8.8) — jalankan: node spike/toSamples.test.js
// Tanpa dependency, tanpa build step.
const assert = require("node:assert/strict");
const { toSamples, akumulasiKoalisi, ringkasKoalisi } = require("./toSamples.js");

const t0 = 1000;

// Fixture: 3 batch pointermove, meniru output event.getCoalescedEvents().
// Batch tengah membawa 3 titik terkoalisi dari satu event frekuensi tinggi
// (historySize > 1) — kasus yang harus tetap terurut dan lengkap.
const eventBatches = [
  [{ clientX: 100, clientY: 200, timeStamp: 1005 }],
  [
    { clientX: 101, clientY: 201, timeStamp: 1008 },
    { clientX: 103, clientY: 203, timeStamp: 1011 },
    { clientX: 106, clientY: 207, timeStamp: 1015 },
  ],
  [{ clientX: 110, clientY: 212, timeStamp: 1019 }],
];

const expected = [
  { x: 100, y: 200, t: 5 },
  { x: 101, y: 201, t: 8 },
  { x: 103, y: 203, t: 11 },
  { x: 106, y: 207, t: 15 },
  { x: 110, y: 212, t: 19 },
];

const actual = eventBatches.flatMap((batch) => toSamples(batch, t0));

assert.deepStrictEqual(actual, expected);
assert.equal(actual.length, expected.length);

const timestamps = actual.map((s) => s.t);
assert.deepStrictEqual(
  timestamps,
  [...timestamps].sort((a, b) => a - b),
  "urutan sampel harus sama dengan urutan waktu, termasuk lintas batch terkoalisi",
);

console.log("toSamples: PASS (%d sampel)", actual.length);

// --- Deteksi koalisi ---
// Alasan test ini ada: golden test di atas menguji fungsi murni di atas
// fixture, jadi ia buta terhadap browser yang diam-diam cuma menyerahkan
// satu titik per frame. Angka inilah yang membedakan alat rusak dari
// prompt lemah. Lihat "Rencana Spike" Bagian 1.

const KOSONG = { jumlah_event: 0, total_titik: 0, maks: 0 };

// Sehat: batch di atas membawa 1, 3, 1 titik.
const sehat = eventBatches.reduce(
  (akum, batch) => akumulasiKoalisi(akum, batch.length),
  KOSONG,
);
const ringkasSehat = ringkasKoalisi(sehat);
assert.equal(ringkasSehat.jumlah_event_pointermove, 3);
assert.equal(ringkasSehat.titik_per_event_maks, 3);
assert.equal(ringkasSehat.titik_per_event_rata2, 1.67, "5 titik / 3 event");

// Fallback diam: browser mengembalikan 1 titik per event, ribuan kali.
// JSON tetap tebal, kanvas tetap mulus, golden test di atas tetap hijau —
// hanya angka inilah yang menangkapnya.
let degradasi = KOSONG;
for (let i = 0; i < 800; i += 1) degradasi = akumulasiKoalisi(degradasi, 1);
const ringkasDegradasi = ringkasKoalisi(degradasi);
assert.equal(ringkasDegradasi.titik_per_event_rata2, 1);
assert.equal(ringkasDegradasi.titik_per_event_maks, 1);
assert.ok(
  ringkasDegradasi.titik_per_event_rata2 < 1.5,
  "rata-rata 1,0 harus jatuh di bawah ambang peringatan 1,5",
);

// Sesi tanpa goresan sama sekali tidak boleh membagi dengan nol.
const ringkasKosong = ringkasKoalisi(KOSONG);
assert.equal(ringkasKosong.titik_per_event_rata2, 0);
assert.equal(ringkasKosong.jumlah_event_pointermove, 0);

// Akumulator harus immutable — akum lama tidak berubah.
const sebelum = { jumlah_event: 2, total_titik: 6, maks: 4 };
const sesudah = akumulasiKoalisi(sebelum, 5);
assert.deepStrictEqual(sebelum, { jumlah_event: 2, total_titik: 6, maks: 4 });
assert.deepStrictEqual(sesudah, { jumlah_event: 3, total_titik: 11, maks: 5 });

console.log(
  "koalisi: PASS (sehat=%s, degradasi=%s)",
  ringkasSehat.titik_per_event_rata2,
  ringkasDegradasi.titik_per_event_rata2,
);
