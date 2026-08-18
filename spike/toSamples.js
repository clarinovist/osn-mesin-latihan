// Fungsi murni: array titik mentah (dari event.getCoalescedEvents()) -> Sample[].
// Terpisah dari DOM handler supaya testable dengan fixture array biasa,
// tanpa mock PointerEvent penuh. Lihat "Rencana Spike" Bagian 1.
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory();
  } else {
    var api = factory();
    root.toSamples = api.toSamples;
    root.akumulasiKoalisi = api.akumulasiKoalisi;
    root.ringkasKoalisi = api.ringkasKoalisi;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function toSamples(points, t0) {
    return points.map(function (p) {
      return { x: p.clientX, y: p.clientY, t: p.timeStamp - t0 };
    });
  }

  // Akumulator koalisi: mendeteksi getCoalescedEvents yang gagal diam-diam.
  // Kalau rata-rata titik per event ≈ 1,0 maka perekam ini setara pointermove
  // polling biasa dan resolusi antar-frame hilang. Lihat "Rencana Spike"
  // Bagian 1, "Risiko — fallback yang gagal diam-diam".
  function akumulasiKoalisi(akum, jumlahTitik) {
    return {
      jumlah_event: akum.jumlah_event + 1,
      total_titik: akum.total_titik + jumlahTitik,
      maks: Math.max(akum.maks, jumlahTitik),
    };
  }

  function ringkasKoalisi(akum) {
    var rata = akum.jumlah_event === 0 ? 0 : akum.total_titik / akum.jumlah_event;
    return {
      titik_per_event_rata2: Math.round(rata * 100) / 100,
      titik_per_event_maks: akum.maks,
      jumlah_event_pointermove: akum.jumlah_event,
    };
  }

  return {
    toSamples: toSamples,
    akumulasiKoalisi: akumulasiKoalisi,
    ringkasKoalisi: ringkasKoalisi,
  };
});
