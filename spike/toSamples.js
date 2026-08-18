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
    root.verdictKoalisi = api.verdictKoalisi;
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
      total_titik: akum.total_titik,
    };
  }

  // Verdict atas ringkasan koalisi. Dipisah dari UI supaya ikut ter-test.
  //
  // Ditambahkan 18 Agustus setelah ditemukan lubang: guard lama berbunyi
  // `rata > 0 && rata < 1.5`, sehingga rata-rata TEPAT 0,0 — event pointermove
  // terkirim tapi tidak satu titik pun terekam — lolos tanpa peringatan apa pun.
  // Itu justru kegagalan terparah, bukan kondisi aman. Tiga kemungkinan yang
  // harus dibedakan, bukan dua:
  //   - "kosong"   : belum ada pointermove sama sekali (sesi belum digores)
  //   - "rusak"    : ada event, nol titik -> perekaman gagal total
  //   - "degradasi": ada titik tapi ~1 per event -> resolusi antar-frame hilang
  function verdictKoalisi(ringkas) {
    if (ringkas.jumlah_event_pointermove === 0) {
      return {
        status: "kosong",
        pesan: "Belum ada goresan terekam — tidak ada yang bisa dinilai.",
      };
    }
    if (ringkas.total_titik === 0 || ringkas.titik_per_event_rata2 === 0) {
      return {
        status: "rusak",
        pesan:
          "⛔ " + ringkas.jumlah_event_pointermove + " event pointermove, NOL titik terekam — " +
          "perekaman gagal total. Data ini tidak bisa dipakai; cek Bagian 1 rencana spike.",
      };
    }
    if (ringkas.titik_per_event_rata2 < 1.5) {
      return {
        status: "degradasi",
        pesan:
          "⚠ titik/event " + ringkas.titik_per_event_rata2 +
          " — resolusi antar-frame nyaris hilang, cek Bagian 1 rencana spike.",
      };
    }
    return {
      status: "sehat",
      pesan: "Titik/event: " + ringkas.titik_per_event_rata2 + ".",
    };
  }

  return {
    toSamples: toSamples,
    akumulasiKoalisi: akumulasiKoalisi,
    ringkasKoalisi: ringkasKoalisi,
    verdictKoalisi: verdictKoalisi,
  };
});
