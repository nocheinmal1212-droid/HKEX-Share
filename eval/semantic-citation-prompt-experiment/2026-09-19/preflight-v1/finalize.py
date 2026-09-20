"""Freeze only after reviewed offline evidence; exclusive write, never launch."""
import importlib.util
import json
from pathlib import Path

PACKET=Path(__file__).resolve().parent;ROOT=PACKET.parents[3]
s=importlib.util.spec_from_file_location('prep',PACKET/'prepare.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def main():
    after=p.preservation()
    assert after==p.read(p.RUNS/'checks-v1/preservation-before.json')
    assert not p.LIVE.exists()
    p.put(p.RUNS/'checks-v1/preservation-after.json',after)
    files={}
    for item in after:
        manifest=ROOT/item['manifest'];files[str(manifest.relative_to(ROOT))]=p.sha(manifest)
        files.update(p.read(manifest)['files'])
    for directory in (PACKET,p.PREP,p.RUNS/'checks-v1',p.RUNS/'diagnostics-v1'):
        for f in directory.rglob('*'):
            if f.is_file():files[str(f.relative_to(ROOT))]=p.sha(f)
    report=ROOT/'docs/semantic-citation-prompt-experiment-preparation-2026-09-19.md'
    files[str(report.relative_to(ROOT))]=p.sha(report)
    p.put(PACKET/'freeze.json',{'version':'prompt-factorial-freeze-1.0.0','readiness':'GO_PENDING_EXPLICIT_LIVE_APPROVAL',
        'prepared_path':str(p.PREP.relative_to(ROOT)),'files':files,'members':len(files),
        'scope':'Four prompt arms, two exposed cases, 16 completions; no live calls authorized',
        'review':'same-agent inspection; no independent approval'})
    print(json.dumps({'freeze_sha256':p.sha(PACKET/'freeze.json'),'members':len(files)}))

if __name__=='__main__':main()
