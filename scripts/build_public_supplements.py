"""Rebuild additional public observations from six immutable, externally saved originals.

No network access. Restore raw inputs first; do not fabricate substitutes for missing
files. Existing data.json is the exact pilot mesh allowlist and population denominator.
"""
from pathlib import Path
import hashlib
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = yaml.safe_load((ROOT / 'data/manifests/public_supplements.yml').read_text())
    assert manifest['n03_used'] is False
    assert len(manifest['artifacts']) == 6
    for artifact in manifest['artifacts']:
        raw = (ROOT / artifact['path']).read_bytes()
        assert len(raw) == artifact['byte_size'], artifact['path']
        assert hashlib.sha256(raw).hexdigest() == artifact['sha256'], artifact['path']
        assert artifact['reuse_status'] == 'accepted_official_eStat_terms_with_attribution'
    for args in [
        ['scripts/build_student_residence.py'],
        ['scripts/build_cafe_asset.py'],
        ['scripts/extract_commercial_districts.py',
         'data/raw/supplements/economic-commercial-districts-2021.xlsx',
         'dist/commercial-districts.json'],
    ]:
        subprocess.run([sys.executable, *args], cwd=ROOT, check=True)
    print('PASS: six exact-byte supplemental originals rebuilt')


if __name__ == '__main__':
    main()
