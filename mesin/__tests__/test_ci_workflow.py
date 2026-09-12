"""Optimasi penjadwalan CI tidak mengurangi test atau melewati gate deploy."""
from pathlib import Path
import shlex


ALUR = Path(__file__).resolve().parents[2] / ".github/workflows/deploy.yml"


def test_ci_menjalankan_seluruh_test_secara_stabil():
    teks = ALUR.read_text()
    bagian = teks.split("- name: Jalankan seluruh test\n", 1)[1]
    baris = bagian.splitlines()[0].strip()
    assert baris.startswith("run: ")
    assert shlex.split(baris[len("run: "):]) == [
        "python", "-m", "pytest", "mesin/__tests__/", "-q", "-W", "error",
    ]


def test_ci_tetap_menguji_sebelum_build_dan_memasang_digest_yang_sama():
    teks = ALUR.read_text()
    assert teks.index("run: python scripts/check_repo.py") < teks.index(
        "- name: Jalankan seluruh test"
    )
    assert "  bangun:\n    name: Build & Push\n    needs: uji\n" in teks
    assert "  pasang:\n    name: Deploy ke VPS\n    needs: bangun\n" in teks
    assert "digest: ${{ steps.dorong.outputs.digest }}" in teks
    assert '"deploy-rutin-v1 ${{ needs.bangun.outputs.digest }} ${{ needs.bangun.outputs.recovery_digest }}"' in teks
    assert "cancel-in-progress: false" in teks
    assert "- name: Pastikan situs hidup dari luar" in teks
