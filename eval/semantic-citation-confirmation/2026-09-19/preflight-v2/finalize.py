"""Offline final freeze. Does not launch, call a transport or refresh historical hashes."""
import os
os.environ={}
from datetime import datetime,timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
PACKET=Path(__file__).resolve().parent
BASE=ROOT/'runs/semantic-citation-confirmation-2026-09-19'
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,sha,write_new
identity=read(PACKET/'execution-identity.json')
assert all(sha((ROOT/p).read_bytes())==h for p,h in identity['runtime_files'].items())
assert 'Ran 52 tests' in (BASE/'deadline-diagnostics-v2/tests-controlled-environment.txt').read_text()
assert (BASE/'deadline-diagnostics-v2/tests-controlled-environment.txt').read_text().rstrip().endswith('OK')
assert len(read(BASE/'deadline-diagnostics-v2/final-results-controlled.json')['real_tests'])==10
assert read(BASE/'diagnostics-v2-followup/baseline-evaluation.json')['complete_primary_successes']==2
assert len(read(BASE/'diagnostics-v2-followup/role-isolation.json'))==6
matrix=read(BASE/'diagnostics-v2-followup/case-matrix.json')
unit=next(r['evaluation'] for r in matrix if r['variant']=='unit_plus_lease')
assert unit['host_accepted'] and unit['required_source_support_present'] and not unit['exact_reviewed_contributors_and_state'] and not unit['success']
assert len(read(BASE/'snapshot-replay-v2/verification.json'))==2
for name in ('live-v1','live-v2'):assert not (BASE/name).exists()
# Include old files in the successor with explicit current bindings; the old freeze's
# own hashes are never edited. Its historical verification is separately retained.
files={p:sha((ROOT/p).read_bytes()) for p in read(PACKET.with_name('preflight-v1')/'freeze.json')['files']}
for folder in [PACKET,BASE/'prepared-v2',BASE/'prepared-v2-before-review',BASE/'deadline-diagnostics-v2',
               BASE/'diagnostics-v2',BASE/'diagnostics-v2-followup',BASE/'snapshot-replay-v2']:
    for p in sorted(folder.rglob('*')):
        if p.is_file():files[str(p.relative_to(ROOT))]=sha(p.read_bytes())
for p in [*identity['runtime_files'],'docs/development-logs.md','docs/semantic-citation-deadline-correction-results-2026-09-19.md',
          'spec/paired-semantic-attempts-1.2.md','tests/test_semantic_deadline.py',
          'eval/semantic-citation-confirmation/2026-09-19/preflight-v1/freeze.json',
          'runs/semantic-citation-confirmation-2026-09-19/freeze-checks-v1/verification-receipt.json']:
    files[p]=sha((ROOT/p).read_bytes())
write_new(PACKET/'freeze.json',{'version':'two-query-confirmation-preflight-2.0.0',
    'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'readiness':'GO_PENDING_EXPLICIT_LIVE_APPROVAL',
    'blocking_reason':None,'case_order':['total','period_groups'],'nonce':'live-v2','live_output':str(BASE/'live-v2'),
    'prepared_path':str((BASE/'prepared-v2').relative_to(ROOT)),'files':files,'members':len(files),
    'historical_no_go_sha256':'f98cab8947112698dc2e8d58ba30441dc6d8f40f3d1a35125994ce50a34e7643',
    'classification':'Exposed development cases; authored offline correction tests; no live inference authorization',
    'review':'same-agent inspection, not independent approval','future_model_outputs_exposed':False,
    'source_expectations_unchanged':True,'self_hash_omitted':True,
    'post_freeze_receipts':'runs/semantic-citation-confirmation-2026-09-19/freeze-checks-v2',
    'approval':'NONE; explicit owner approval and immediate prelaunch binding check required',
    'amendments':'new version required; never regenerate requests or refresh hashes silently'})
print('freeze_sha256='+sha((PACKET/'freeze.json').read_bytes()))
print('members='+str(len(files)))
