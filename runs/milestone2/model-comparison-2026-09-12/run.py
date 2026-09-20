"""Owner-requested synthetic comparison; no report inputs or shell credential evaluation."""
import importlib.util
import os
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('probe', 'tools/probe_openrouter.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
if not os.environ.get('OPENROUTER_API_KEY'):
    for line in Path('.env').read_text().splitlines():
        name, sep, value = line.strip().partition('=')
        if sep and name.strip() in ('OPENROUTER_API_KEY', 'export OPENROUTER_API_KEY'):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ['OPENROUTER_API_KEY'] = value
            break
key = os.environ.get('OPENROUTER_API_KEY')
if not key:
    raise SystemExit('Credential unavailable')
model, directory = sys.argv[1:]
out = Path(__file__).parent / directory
out.mkdir(exist_ok=False)
report = probe.run_probe(key, model=model)
probe.write_new(out / 'probe.json', report)
print(model, report['status'])
for case in report['cases']:
    print(case['case'], case['status'], case.get('validated_output'), case.get('observed_identity'))
