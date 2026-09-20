"""Credential bootstrap for the authorized fixed live run. Never prints secret values."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path('/private/tmp/audit-direct-contributor-live-v2-2026-09-17')
RUN = ROOT / 'runs/milestone2/direct-contributor-live-v2-2026-09-17'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    env = {'PATH': '/usr/bin:/bin'}
    if not args.preflight:
        key = os.environ.get('OPENROUTER_API_KEY')
        if not key:
            for line in (ROOT / '.env').read_text().splitlines():
                line = line.strip()
                if line.startswith('export '):
                    line = line[7:].lstrip()
                name, sep, value = line.partition('=')
                if sep and name.strip() == 'OPENROUTER_API_KEY':
                    key = value.strip().strip('\"\'')
                    break
        if not key:
            raise SystemExit('Credential unavailable')
        env['OPENROUTER_API_KEY'] = key
    command = ['/usr/bin/sandbox-exec', '-f', str(STAGE / 'sandbox.sb'), str(Path(sys.executable).resolve()),
               '-I', '-B', str(STAGE / 'direct_contributor_live_v2.py'),
               '--manifest', str(STAGE / 'manifest.json'), '--out', str(RUN / 'attempts')]
    if args.preflight:
        command.append('--preflight')
    raise SystemExit(subprocess.run(command, cwd=STAGE, env=env, close_fds=True).returncode)


if __name__ == '__main__':
    main()
