"""Label tahap aman untuk anak; tidak bergantung pada bukti diagnosis."""

_LABEL = (
    ("pemetaan", "Latihan campuran"),
    ("latihan_terbimbing", "Pelajari bersama"),
    ("penguatan", "Coba mandiri"),
    ("evaluasi", "Coba kembali"),
    ("checkpoint", "Latihan berkala"),
    ("pengenalan", "Kenali hal baru"),
    ("maintenance", "Latihan campuran"),
)


def label_tahap(tujuan: str) -> str:
    """Hanya tampilkan label pra-tulis, bukan nilai tujuan mentah."""
    return next((label for kode, label in _LABEL if kode == tujuan), "")


def penanda_tahap(tujuan: str) -> str:
    """Markup netral; sesi bebas/warisan tidak mendapat penanda tambahan."""
    label = label_tahap(tujuan)
    return f'<span class="label-tahap-murid">{label}</span>' if label else ""
