"""Verify preserved evidence and create new bindings without changing an old freeze."""
from pathlib import Path
import sys, subprocess
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'1.1.0'
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,write_new,sha,fingerprint
from hkex_audit.semantic import PROMPT,SCHEMA,VERSION
from hkex_audit.semantic_attempt import CONFIGS,VERSION as ATTEMPT
from hkex_audit.semantic_cli import runtime_identity
from hkex_audit.header_support import policy_identity

def verify(mapping,base=ROOT):
    for p,expected in mapping.items():
        path=base/p
        assert 'corpus' not in path.parts and 'clean' not in path.parts and path.suffix!='.pdf'
        assert sha(path.read_bytes())==expected,p
    return len(mapping)
original=read(OLD/'preservation-verification.json');investigation=read(ROOT/'eval/semantic-citation-investigation/2026-09-19/bundle-integrity.json')
oldbinding=read(OLD/'implementation-bindings.json')
differences={p:{'before':h,'after':sha((ROOT/p).read_bytes())} for p,h in oldbinding['files'].items() if sha((ROOT/p).read_bytes())!=h}
assert set(differences)=={'src/hkex_audit/header_support.py'}
assert sha((HERE/'runtime-before/src/hkex_audit/header_support.py').read_bytes())==oldbinding['files']['src/hkex_audit/header_support.py']
record={'original_retained_verified':verify(original['original_127_hashes']),
 'prior_investigation_verified':verify(investigation['files']),
 'prior_investigation_report_verified':verify({investigation['report']['path']:investigation['report']['sha256']}),
 'protected_current_verified':verify(original['protected_frozen_current_hashes']),
 'original_implementation_artifacts_verified':verify(read(OLD/'artifact-integrity.json')['files']),
 'prior_review_artifacts_verified':verify(read(ROOT/'runs/semantic-citation-review-2026-09-19/review-integrity.json')['files']),
 'new_fixture_freeze_verified':verify(read(HERE/'fixture-freeze.json')['files'],HERE),
 'pre_correction_runtime_verified':verify(read(HERE/'baseline.json')['runtime_files'],HERE/'runtime-before'),
 'expected_old_binding_differences':differences,
 'schema_unchanged':fingerprint(SCHEMA)==oldbinding['schema_sha256'],
 'prompt_unchanged':sha(PROMPT.encode())==oldbinding['prompt_sha256'],
 'configuration_unchanged':CONFIGS==oldbinding['configurations'],
 'policy_resource_unchanged':policy_identity()['sha256']==oldbinding['policy']['sha256'],
 'historical_support_result':'0/4 unchanged','provider_calls':0,'network_calls':0}
assert all(record[k] for k in ['schema_unchanged','prompt_unchanged','configuration_unchanged','policy_resource_unchanged'])
write_new(HERE/'preservation-verification.json',record)
paths=[*oldbinding['files'],'tests/test_presentation_partition.py','spec/header-source-analysis-1.0.1.md','docs/semantic-citation-partition-correction-results-2026-09-19.md','README.md','PLAN.md','docs/development-logs.md']
write_new(HERE/'implementation-bindings.json',{'classification':'approved bounded offline correction; not inference authorization',
 'operation_version':VERSION,'attempt_version':ATTEMPT,'policy':policy_identity(),'prompt_sha256':sha(PROMPT.encode()),'schema_sha256':fingerprint(SCHEMA),
 'runtime_sha256':runtime_identity(),'configurations':CONFIGS,'files':{p:sha((ROOT/p).read_bytes()) for p in paths},
 'prior_binding_sha256':sha((OLD/'implementation-bindings.json').read_bytes()),'fixture_freeze_sha256':sha((HERE/'fixture-freeze.json').read_bytes())})
subprocess.run(['git','diff','--check'],check=True)
run=ROOT/'runs/semantic-citation-correction-1.1.1'
paths=sorted([p for parent in [HERE,run] for p in parent.rglob('*') if p.is_file()])
write_new(HERE/'artifact-integrity.json',{'classification':'post-exposure offline correction evidence','provider_calls':0,'network_calls':0,
 'self_hash_omitted':True,'files':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths}})
print({k:v for k,v in record.items() if k!='expected_old_binding_differences'})
