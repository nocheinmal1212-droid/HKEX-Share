"""Reproduce the unresolved late-write/replay defect in a NEW supplied output directory."""
import argparse
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / 'tools/experiments'))
import direct_contributor_boundary as boundary
from run_direct_contributor_boundaries import envelope


class LateFailure(boundary.Store):
    def write(self, name, data):
        super().write(name, data)
        if name == 'result.json':
            raise OSError('Injected error after result bytes were written')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('new_output', type=Path)
    args = parser.parse_args()
    args.new_output.mkdir(exist_ok=False)
    prior = RUN / 'boundaries-r2/C01_selected'
    source = json.loads((prior / 'source.json').read_bytes())
    job = json.loads((prior / 'request.json').read_bytes())
    output = {'action': 'select', 'target_id': 'r05', 'contributor_ids': ['r01', 'r04'],
              'support_ids': ['s05', 's01', 's02', 's03', 's04'], 'reason': 'supported_direct_breakdown'}
    result = boundary.dispatch(source, job['identity'], job, lambda _: envelope(output),
                               LateFailure(args.new_output), {'model': 'offline_stub'})
    replay = boundary.replay(args.new_output)
    print(json.dumps({'dispatch': result['state'], 'replay': replay['state'],
                      'requirement_passed': replay['state'] == 'incomplete_attempt'}, indent=2))
    return 0 if replay['state'] == 'incomplete_attempt' else 1


if __name__ == '__main__':
    raise SystemExit(main())
