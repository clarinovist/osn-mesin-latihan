"""Diagram Venn mempertahankan total himpunan sebagai fakta, bukan hasil antara."""
import design_tokens as T
from combinatorics_visual_data import validasi_venn
from phase6_svg import bungkus_svg
from plane_geometry_svg_primitives import teks
from visual_contract import DescriptorVisual


def proyeksi_venn(parameter):
    validasi_venn(parameter)
    data = {nama: parameter[nama] for nama in ("a", "b", "c")}
    return ("Perhatikan dua kelompok pada diagram. Anggota dapat mengikuti keduanya.\n"
            "Berapa banyak anggota yang mengikuti kelompok A atau B (atau keduanya)?",
            DescriptorVisual("venn_dua", 1, data))


def ringkasan_venn(data):
    validasi_venn(data)
    return (f"Total kelompok A {data['a']} anggota; total kelompok B {data['b']} anggota; "
            f"{data['c']} anggota mengikuti keduanya. Total mencakup anggota irisan.")


def render_venn(data, namespace):
    validasi_venn(data)
    lingkaran = "".join(
        f'<circle class="himpunan" cx="{x}" cy="{T.VENN_PUSAT_Y}" r="{T.VENN_RADIUS}" '
        f'fill="none" stroke="{T.TEKS_UTAMA}" stroke-width="{T.GEO_GARIS}"/>'
        for x in T.VENN_PUSAT_X)
    label = "".join(teks(x, T.VENN_TOTAL_Y, f"Total {nama.upper()} = {data[nama]}", "total-himpunan")
                    + teks(x, T.VENN_NAMA_Y, nama.upper())
                    for x, nama in zip(T.VENN_PUSAT_X, ("a", "b")))
    irisan = (teks(T.FASE6_LEBAR/2, T.VENN_IRISAN_Y, data["c"], "irisan-diberikan")
              + teks(T.FASE6_LEBAR/2, T.VENN_IRISAN_LABEL_Y, "Angka di irisan = mengikuti keduanya"))
    return bungkus_svg(lingkaran + label + irisan, ringkasan_venn(data), namespace, "Dua kelompok")
