"""Keputusan cakupan Fase 6; teks disengaja bukan renderer yang terlupakan."""
from types import MappingProxyType

CAKUPAN = MappingProxyType({
    "jam_selesai": ("visual", "Waktu awal atau akhir dinyatakan pada jam; target tidak digambar dari jawabannya."),
    "skala_peta": ("visual", "Skema dua kota menampilkan besaran diketahui; panjang gambar bukan alat ukur fisik."),
    "jam_menit_detik": ("teks", "Konversi satu nilai tidak membutuhkan jam analog; gambar tangga akan memberi faktor konversi."),
    "satuan_waktu_lama": ("teks", "Diagram abad dan windu akan memberikan hubungan konversi yang justru sedang diuji anak."),
    "satuan_kuantitas": ("teks", "Gambar bundel lusin atau rim memberikan isi satuan yang harus diketahui untuk menjawab."),
    "tangga_satuan_campuran": ("teks", "Tangga dengan faktor dan arah perpindahan merupakan langkah bantuan, bukan informasi awal soal."),
    "satuan_luas_volume": ("teks", "Diagram unit kuadrat atau kubik adalah bantuan faktor konversi; simpan untuk permukaan pembahasan."),
    "jalur_petak": ("visual", "Petak memperlihatkan konektivitas serta arah gerak yang diketahui tanpa menampilkan satu pun rute solusi."),
    "inklusi_eksklusi_2": ("visual", "Dua lingkaran menunjukkan hubungan kelompok dengan total dan irisan diberikan, tanpa nilai eksklusif turunan."),
    "susun_bilangan": ("visual", "Kartu digit tersedia dan slot kosong menyatakan ruang susunan tanpa menghitung pilihan tiap posisi."),
    "susun_bilangan_syarat": ("visual", "Digit lengkap tetap ditampilkan; syarat genap atau batas bilangan tidak diselesaikan menjadi pilihan terfilter."),
    "permutasi_urutan": ("visual", "Kartu orang dan posisi kosong menunjukkan urutan yang diberikan tanpa mengenumerasi susunan yang sah."),
    "permutasi_blok": ("visual", "Objek tersedia serta syarat berdampingan dipertahankan, tanpa gambar penggabungan blok sebagai strategi solusi."),
    "kombinasi_pilih": ("visual", "Kartu orang dan area tim tanpa posisi bernomor mempertahankan sifat pemilihan tidak berurutan."),
    "aturan_tambah": ("teks", "Kedua banyak pilihan sudah diberikan; ilustrasi kelompok hanya menduplikasi dua angka tanpa tugas visual tambahan."),
    "aturan_kali": ("teks", "Pohon atau seluruh pasangan akan menyajikan enumerasi jawaban; dua kartu angka saja bersifat dekoratif."),
    "jabat_tangan": ("teks", "Graf lengkap memberi semua pasangan solusi; menampilkan hingga dua ratus lima puluh orang tidak terbaca."),
    "sarang_merpati": ("teks", "Menaruh merpati ke sangkar tertentu memberi konstruksi pembagian sebagai solusi, bukan fakta awal soal."),
})
