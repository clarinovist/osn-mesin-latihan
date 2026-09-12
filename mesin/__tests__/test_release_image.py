"""Palang verifier image dengan Docker palsu dan probe stdlib tanpa Docker nyata."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
BERKAS = ROOT / 'scripts' / 'verify_release_image.py'
IMAGE = 'ghcr.io/clarinovist/osn-mesin-latihan@sha256:' + 'a' * 64
REVISION = 'b' * 40


@pytest.fixture
def verifier():
    spesifikasi = importlib.util.spec_from_file_location('verifier_rilis_uji', BERKAS)
    modul = importlib.util.module_from_spec(spesifikasi)
    spesifikasi.loader.exec_module(modul)
    return modul


def metadata():
    # Config ID sengaja BUKAN digest manifest; keduanya tidak boleh tertukar.
    return [{'Id': 'sha256:' + 'c' * 64, 'RepoDigests': [IMAGE],
             'Config': {'Labels': {'org.opencontainers.image.revision': REVISION},
                        'Volumes': {'/data': {}}}}]


def docker_palsu(monkeypatch, verifier, *, inspect=None, run=None):
    panggilan = []
    def jalankan(argv, **opsi):
        panggilan.append((argv, opsi))
        assert opsi['shell'] is False
        assert opsi['capture_output'] is True
        assert opsi['check'] is False
        assert opsi['text'] is True
        assert isinstance(argv, list)
        if argv[:3] == ['docker', 'image', 'inspect']:
            return subprocess.CompletedProcess(argv, 0, json.dumps(metadata() if inspect is None else inspect), '')
        if argv[:3] == ['docker', 'container', 'rm']:
            return subprocess.CompletedProcess(argv, 0, '', '')
        assert argv[:2] == ['docker', 'run']
        if isinstance(run, BaseException):
            raise run
        return run or subprocess.CompletedProcess(argv, 0, json.dumps(verifier.RINGKASAN), '')
    monkeypatch.setattr(verifier.subprocess, 'run', jalankan)
    return panggilan


def test_digest_dan_argv_terkunci_tanpa_mount_host(verifier, monkeypatch):
    panggilan = docker_palsu(monkeypatch, verifier)
    hasil = verifier.verifikasi(IMAGE, REVISION)
    assert hasil == {'ok': True, 'image': IMAGE, 'revision': REVISION, 'probe': verifier.RINGKASAN}
    assert len(panggilan) == 2
    assert panggilan[0][0] == ['docker', 'image', 'inspect', IMAGE]
    argv, opsi = panggilan[1]
    nama = argv[argv.index('--name') + 1]
    assert nama.startswith('osn-release-probe-')
    assert argv == [
        'docker', 'run', '--rm', '--interactive', '--pull', 'never', '--name', nama,
        '--network', 'none', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--user', '10001:10001',
        '--tmpfs', '/data:rw,uid=10001,gid=10001', '--tmpfs', '/tmp',
        '--env', 'TMPDIR=/data', '--no-healthcheck', '--workdir', '/app',
        '--entrypoint', 'python', IMAGE, '-B', '-',
    ]
    assert opsi['input'] == verifier.SUMBER_PROBE
    assert opsi['timeout'] == 180
    assert panggilan[0][1]['timeout'] == 30


@pytest.mark.parametrize('image,revision', [
    (IMAGE.replace('@sha256:', ':sha-'), REVISION),
    (IMAGE.split('@')[0] + ':latest', REVISION),
    (IMAGE.replace('clarinovist', 'asing'), REVISION),
    (IMAGE.replace('ghcr.io', 'docker.io'), REVISION),
    (IMAGE.replace('@sha256:', ':tag@sha256:'), REVISION),
    (IMAGE.upper(), REVISION), (IMAGE + '\n', REVISION),
    (IMAGE[:-1], REVISION), ('--privileged', REVISION),
    (IMAGE, REVISION[:7]), (IMAGE, REVISION.upper()),
    (IMAGE, REVISION + '; echo data'), (IMAGE, REVISION + '\n'),
])
def test_rujukan_tidak_sah_tidak_memanggil_docker(verifier, monkeypatch, image, revision):
    panggilan = docker_palsu(monkeypatch, verifier)
    with pytest.raises(verifier.GalatVerifikasi):
        verifier.verifikasi(image, revision)
    assert panggilan == []


@pytest.mark.parametrize('perubahan', ['revision', 'digest', 'digest_string', 'config_id', 'label_hilang', 'volume', 'dua', 'null'])
def test_inspect_salah_menolak_sebelum_run(verifier, monkeypatch, perubahan):
    data = metadata()
    if perubahan == 'revision':
        data[0]['Config']['Labels']['org.opencontainers.image.revision'] = 'd' * 40
    elif perubahan == 'digest':
        data[0]['RepoDigests'] = [IMAGE.replace('a' * 64, 'c' * 64)]
    elif perubahan == 'digest_string':
        data[0]['RepoDigests'] = IMAGE
    elif perubahan == 'config_id':
        data[0]['Id'] = IMAGE
    elif perubahan == 'label_hilang':
        data[0]['Config']['Labels'] = None
    elif perubahan == 'volume':
        data[0]['Config']['Volumes']['/app'] = {}
    elif perubahan == 'dua':
        data *= 2
    else:
        data = {}
    panggilan = docker_palsu(monkeypatch, verifier, inspect=data)
    with pytest.raises(verifier.GalatVerifikasi, match='identitas_image_tidak_cocok'):
        verifier.verifikasi(IMAGE, REVISION)
    assert len(panggilan) == 1


@pytest.mark.parametrize('isi', [
    '', 'bukan-json-sintetis', '[]', '{}', '{"ok": true}',
    '{"ok": false, "kode": "detail-sintetis"}',
])
def test_ringkasan_tidak_lengkap_bukan_lulus(verifier, monkeypatch, capsys, isi):
    docker_palsu(monkeypatch, verifier,
                 run=subprocess.CompletedProcess([], 0, isi, 'stderr-sintetis'))
    assert verifier.main(['--image', IMAGE, '--revision', REVISION]) == 1
    tangkapan = capsys.readouterr()
    assert json.loads(tangkapan.out) == {'ok': False, 'kode': 'ringkasan_tidak_sah'}
    assert tangkapan.err == ''


@pytest.mark.parametrize('ubah', [{'provider_calls': 1}, {'http_checks': 0}, {'skema': 3},
                                   {'skenario_tindakan': 0}, {'records': ['rahasia-sintetis']},
                                   {'ok': 1}, {'provider_calls': False}])
def test_ringkasan_harus_exact_dan_tidak_mengeluarkan_record(verifier, monkeypatch, capsys, ubah):
    docker_palsu(monkeypatch, verifier, run=subprocess.CompletedProcess(
        [], 0, json.dumps({**verifier.RINGKASAN, **ubah}), ''))
    assert verifier.main(['--image', IMAGE, '--revision', REVISION]) == 1
    tangkapan = capsys.readouterr()
    assert json.loads(tangkapan.out) == {'ok': False, 'kode': 'ringkasan_tidak_sah'}
    assert tangkapan.err == ''


def test_inspect_gagal_tidak_run_dan_output_aman(verifier, monkeypatch, capsys):
    panggilan = []
    def gagal(argv, **opsi):
        panggilan.append(argv)
        return subprocess.CompletedProcess(argv, 1, 'record-sintetis', 'record-sintetis')
    monkeypatch.setattr(verifier.subprocess, 'run', gagal)
    assert verifier.main(['--image', IMAGE, '--revision', REVISION]) == 1
    assert panggilan == [['docker', 'image', 'inspect', IMAGE]]
    tangkapan = capsys.readouterr()
    assert json.loads(tangkapan.out) == {'ok': False, 'kode': 'inspect_gagal'}
    assert tangkapan.err == ''


def test_cli_sukses_hanya_json_agregat(verifier, monkeypatch, capsys):
    docker_palsu(monkeypatch, verifier)
    assert verifier.main(['--image', IMAGE, '--revision', REVISION]) == 0
    tangkapan = capsys.readouterr()
    assert json.loads(tangkapan.out) == {
        'ok': True, 'image': IMAGE, 'revision': REVISION, 'probe': verifier.RINGKASAN}
    assert tangkapan.err == ''


def test_gagal_run_dan_timeout_membersihkan_hanya_container_sendiri(verifier, monkeypatch, capsys):
    for kegagalan in (subprocess.CompletedProcess([], 9, 'detail-sintetis', 'detail-sintetis'),
                      subprocess.TimeoutExpired(['docker', 'run'], 180, output='detail-sintetis'),
                      OSError('detail-sintetis')):
        panggilan = docker_palsu(monkeypatch, verifier, run=kegagalan)
        assert verifier.main(['--image', IMAGE, '--revision', REVISION]) == 1
        argv = panggilan[1][0]
        nama = argv[argv.index('--name') + 1]
        assert panggilan[-1][0] == ['docker', 'container', 'rm', '--force', nama]
        tangkapan = capsys.readouterr()
        assert 'detail-sintetis' not in tangkapan.out
        assert json.loads(tangkapan.out)['ok'] is False
        assert tangkapan.err == ''


@pytest.mark.parametrize('argv', [[], ['--image', 'rahasia-sintetis'],
                                  ['--unknown', 'rahasia-sintetis'],
                                  ['--image', IMAGE, '--revision', 'rahasia-sintetis']])
def test_cli_galat_tidak_echo_argumen(verifier, monkeypatch, capsys, argv):
    panggilan = docker_palsu(monkeypatch, verifier)
    assert verifier.main(argv) == 1
    tangkapan = capsys.readouterr()
    assert json.loads(tangkapan.out)['ok'] is False
    assert 'rahasia-sintetis' not in tangkapan.out
    assert tangkapan.err == ''
    assert panggilan == []


def jalankan_probe(tmp_path, sumber=ROOT / 'mesin', *, injeksi='', diagnostik=False):
    """Interpreter baru menjalankan exec probe; tidak ada Docker atau impor DB host."""
    # PYTHONPATH hanya source salinan; env tidak mewarisi credential/proxy host.
    peluncur = (
        'import importlib.util\n'
        's = importlib.util.spec_from_file_location("verifier", ' + repr(str(BERKAS)) + ')\n'
        'm = importlib.util.module_from_spec(s)\n'
        's.loader.exec_module(m)\n'
        'ruang = {"__name__": "probe_uji"}\n'
        'exec(compile(m.SUMBER_PROBE, "<probe>", "exec"), ruang)\n'
        + injeksi + '\n' + (
            'import tempfile\n'
            'from pathlib import Path\n'
            'with tempfile.TemporaryDirectory() as t:\n'
            '    try: ruang["jalankan_probe"](Path(t))\n'
            '    except Exception as e:\n'
            '        print(str(e) if type(e) is RuntimeError and str(e) in ' + repr({
                'skema_bukan_v4', 'sesi_ganda', 'guard_tidak_menolak',
                'aset_hilang', 'provider_dilarang', 'dns_dilarang',
                'network_dilarang',
            }) + ' else "galat_tidak_dikenal")\n'
            '        raise SystemExit(1)\n'
            if diagnostik else 'raise SystemExit(ruang["main"]())\n'
        )
    )
    return subprocess.run([sys.executable, '-B', '-c', peluncur],
        env={'PYTHONPATH': str(sumber), 'TMPDIR': str(tmp_path), 'PYTHONDONTWRITEBYTECODE': '1'},
        cwd=str(tmp_path), capture_output=True, text=True, timeout=90, shell=False, check=False)


def test_probe_sintetis_migrasi_ledger_http_tanpa_docker(verifier, tmp_path):
    hasil = jalankan_probe(tmp_path)
    assert hasil.returncode == 0
    assert json.loads(hasil.stdout) == verifier.RINGKASAN
    assert hasil.stderr == ''
    assert list(tmp_path.iterdir()) == []  # DB/auth/server sekali pakai sudah ditutup.


def salin_sumber(tmp_path):
    sumber = tmp_path / 'source'
    sumber.mkdir()
    for berkas in (ROOT / 'mesin').glob('*.py'):
        shutil.copy2(berkas, sumber / berkas.name)
    shutil.copytree(ROOT / 'mesin' / 'aset', sumber / 'aset')
    return sumber


@pytest.mark.parametrize('mutasi', ['skema', 'sesi_ganda', 'owner', 'consent', 'aset'])
def test_probe_mendeteksi_app_rusak_di_salinan_temp(tmp_path, mutasi):
    sumber = salin_sumber(tmp_path)
    if mutasi == 'skema':
        berkas = sumber / 'assistant_schema.py'
        lama, baru = 'VERSI_SKEMA = 4', 'VERSI_SKEMA = 3'
    elif mutasi == 'sesi_ganda':
        berkas = sumber / 'assistant_actions.py'
        # Fault pada jalur aktual: retry tetap mengembalikan ID ledger lama,
        # tetapi menambah sesi ekstra. Pemeriksaan ID saja tidak cukup.
        lama = '        return sesi_id\n'
        baru = ("        if sekarang >= 9000:\n"
                "            with database.buka() as kon_ganda:\n"
                "                database.buat_sesi_dari_urutan(kon_ganda, siswa_id, 99, ('deret_aritmetika',), level='P3')\n"
                "        return sesi_id\n")
        # Ada return lain pada lookup; mutasi hanya return di fungsi konfirmasi.
        teks = berkas.read_text()
        posisi = teks.index('def konfirmasi_dan_buat_sesi(')
        assert teks[posisi:].count(lama) == 1
        berkas.write_text(teks[:posisi] + teks[posisi:].replace(lama, baru))
    elif mutasi == 'owner':
        berkas = sumber / 'assistant_actions.py'
        lama = '            siswa_id = _pemilik_sumber(kon_data, chat, pemilik)\n            _periksa_izin(kon_pendamping, catatan, chat)'
        baru = ("            # Mutan replay hasil sebelum otorisasi owner.\n"
                "            if kon_data.execute('SELECT pemilik FROM siswa LIMIT 1').fetchone()[0] != pemilik:\n"
                "                return kon_data.execute('SELECT sesi_id FROM eksekusi_pendamping LIMIT 1').fetchone()[0]\n"
                "            siswa_id = _pemilik_sumber(kon_data, chat, pemilik)\n"
                "            _periksa_izin(kon_pendamping, catatan, chat)")
    elif mutasi == 'consent':
        berkas = sumber / 'assistant_actions.py'
        lama = 'def _periksa_izin(kon, catatan, chat) -> None:\n'
        baru = lama + '    return  # mutan mengabaikan pencabutan izin\n'
    else:
        (sumber / 'aset' / 'favicon.svg').unlink()
    if mutasi not in ('sesi_ganda', 'aset'):
        teks = berkas.read_text()
        assert teks.count(lama) == 1
        berkas.write_text(teks.replace(lama, baru))
    hasil = jalankan_probe(tmp_path, sumber)
    assert hasil.returncode == 1
    assert json.loads(hasil.stdout) == {'ok': False, 'kode': 'probe_gagal'}
    assert hasil.stderr == ''
    # Jangan menerima merah karena fixture/import rusak. Identifikasi guard
    # dengan allow-list kode konstan di proses sintetis terpisah, tanpa trace.
    detail = jalankan_probe(tmp_path, sumber, diagnostik=True)
    assert detail.returncode == 1
    assert detail.stdout.strip() == {
        'skema': 'skema_bukan_v4', 'sesi_ganda': 'sesi_ganda',
        'owner': 'guard_tidak_menolak', 'consent': 'guard_tidak_menolak',
        'aset': 'aset_hilang',
    }[mutasi]
    assert detail.stderr == ''


@pytest.mark.parametrize('jenis,kode', [
    ('provider', 'provider_dilarang'), ('dns', 'dns_dilarang'),
    ('connect', 'network_dilarang'), ('connect_ex', 'network_dilarang'),
])
def test_probe_memblokir_provider_dan_network_outbound(tmp_path, jenis, kode):
    # Masuk hook yang dipanggil SETELAH provider/network dikunci oleh probe.
    aksi = {
        'provider': 'import assistant_service; assistant_service.panggil_provider_default([])',
        'dns': 'import socket; socket.getaddrinfo("provider.invalid", 443)',
        'connect': 'import socket; s = socket.socket(); s.connect(("192.0.2.1", 443))',
        'connect_ex': 'import socket; s = socket.socket(); s.connect_ex(("192.0.2.1", 443))',
    }[jenis]
    injeksi = 'def dilarang(*args):\n    ' + aksi + '\nruang["uji_tindakan"] = dilarang\n'
    hasil = jalankan_probe(tmp_path, injeksi=injeksi, diagnostik=True)
    assert hasil.returncode == 1
    assert hasil.stdout.strip() == kode
    assert hasil.stderr == ''


def test_probe_galat_tidak_mencetak_data(tmp_path):
    injeksi = (
        'def gagal(akar):\n'
        '    raise RuntimeError("record-sintetis-jangan-log")\n'
        'ruang["jalankan_probe"] = gagal\n'
    )
    hasil = jalankan_probe(tmp_path, injeksi=injeksi)
    assert hasil.returncode == 1
    assert json.loads(hasil.stdout) == {'ok': False, 'kode': 'probe_gagal'}
    assert hasil.stderr == ''
