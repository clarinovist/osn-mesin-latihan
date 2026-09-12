"""Kontrak CI persiapan v4: build teruji tanpa deploy tak sengaja."""
from pathlib import Path
import re
import itertools
import pytest

AKAR = Path(__file__).resolve().parents[2]
WORKFLOW = AKAR / '.github/workflows/deploy.yml'
RECOVERY_SHA = 'be4ab003f926382238ea9e7153f063b9c50e9e75'


def _job(teks, nama):
    cocok = re.search(r'^  '+nama+r':\n(.*?)(?=^  [a-z_]+:\n|\Z)', teks, re.M|re.S)
    assert cocok, nama
    return cocok.group(1)


def test_pasang_tertahan_sampai_rollout_dan_deployer_v2_siap():
    teks=WORKFLOW.read_text()
    pasang=_job(teks,'pasang')
    assert "if: ${{ vars.PENDAMPING_ROLLOUT_SIAP == '1' && github.ref == 'refs/heads/main' }}" in pasang
    assert 'needs: bangun' in pasang
    assert 'deploy-v2 ' in pasang
    assert '${{ needs.bangun.outputs.digest }}' in pasang
    assert '${{ needs.bangun.outputs.recovery_digest }}' in pasang
    assert 'cancel-in-progress: false' in teks


def test_build_candidate_dan_recovery_pakai_digest_yang_sama_untuk_verifikasi():
    teks=WORKFLOW.read_text()
    uji=_job(teks,'uji');bangun=_job(teks,'bangun')
    assert 'needs: uji' in bangun
    assert RECOVERY_SHA in uji and RECOVERY_SHA in bangun
    assert 'recovery_digest: ${{ steps.recovery.outputs.digest }}' in bangun
    assert 'digest: ${{ steps.dorong.outputs.digest }}' in bangun
    assert 'scripts/verify_release_image.py' in bangun
    assert '${{ steps.dorong.outputs.digest }}' in bangun
    assert '${{ steps.recovery.outputs.digest }}' in bangun
    assert '--revision "$GITHUB_SHA"' in bangun
    assert '--revision "$RECOVERY_SHA"' in bangun
    assert 'python -m pytest mesin/__tests__/' in uji
    assert 'working-directory: recovery' in uji
    assert 'python -m pytest --rootdir . mesin/__tests__/' in uji
    assert 'Canary: import recovery terisolasi, schema v4' in uji
    assert 'VPS_DEPLOY_KEY' not in uji+bangun


def test_persiapan_tidak_memutakhirkan_latest_atau_memakai_tag_berubah():
    teks=WORKFLOW.read_text()
    bangun=_job(teks,'bangun')
    assert 'value=latest' not in bangun
    assert ':latest' not in bangun
    assert 'recovery-${{ env.RECOVERY_SHA }}' in bangun
    assert 'sha-${{ github.sha }}' in bangun
    assert 'publish-prod' not in bangun
    assert '--network' not in _job(teks,'pasang')  # sandbox image ada di probe, bukan mount produksi CI


@pytest.mark.parametrize('flag,ref', tuple(itertools.product(
    ('', '0', 'false', '1 ', '1'), ('refs/heads/main', 'refs/heads/persiapan')
)))
def test_gate_job_hanya_menerima_izin_exact_dan_main(flag, ref):
    pasang=_job(WORKFLOW.read_text(),'pasang')
    expr=re.search(r'    if: \$\{\{ (.+) \}\}',pasang).group(1)
    # Evaluasi subset ekspresi yang sengaja sempit, bukan parser YAML/deploy baru.
    assert expr == "vars.PENDAMPING_ROLLOUT_SIAP == '1' && github.ref == 'refs/heads/main'"
    bagian=expr.split(' && ')
    nilai={'vars.PENDAMPING_ROLLOUT_SIAP':flag,'github.ref':ref}
    lolos=all(nilai[k.strip()]==v.strip().strip("'") for k,v in (b.split(' == ') for b in bagian))
    assert lolos == (flag=='1' and ref=='refs/heads/main')


def test_dependencies_gagal_tidak_dibypass_ke_build_atau_deploy():
    teks=WORKFLOW.read_text()
    for nama in ('uji','bangun','pasang'):
        job=_job(teks,nama)
        assert 'continue-on-error:' not in job
        assert 'always()' not in job and '|| true' not in job
    assert teks.index('Verifikasi image berdasarkan digest') < teks.index('  pasang:')
    assert 'if:' not in _job(teks,'bangun')  # Tak ada bypass verifikasi image.
    assert 'working-directory: recovery' in _job(teks,'uji')


def test_healthcheck_publik_tiga_permukaan_tetap_diperiksa():
    pasang=_job(WORKFLOW.read_text(),'pasang')
    assert 'https://jagomat.id' in pasang
    assert '/akun' in pasang and '/murid/' in pasang
    assert '401' in pasang and '303' in pasang and '200' in pasang
