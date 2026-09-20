"""Read-only accounting. Launch intent and reservations are not proven HTTP calls."""
import json
from pathlib import Path
import sys

def inspect(output):
    rows=[]
    prefixes=[output/('metadata-'+r) for r in ('primary','research')]
    prefixes += [output/('live-v1-'+a)/r/n/'transport' for a in 'ABCD'
                 for n in ('total','period_groups') for r in ('primary','research')]
    for prefix in prefixes:
        launch=Path(str(prefix)+'-launch.json');returned=Path(str(prefix)+'-return.json')
        record={}
        try:record=json.loads(returned.read_bytes())
        except (OSError,ValueError):pass
        intent={}
        try:intent=json.loads(launch.read_bytes())
        except (OSError,ValueError):pass
        issued=record.get('request_started')
        if issued is True:low=high=1;state='entered_http_boundary'
        elif issued is False:low=high=0;state='prevented_before_http_boundary'
        elif not launch.exists() and not returned.exists():low=high=0;state='no_launch_record'
        else:low=0;high=1;state='unknown_incomplete'
        rows.append({'prefix':str(prefix.relative_to(output)),'issued_min':low,'issued_max':high,'state':state,
                     'authored_transport':intent.get('authored',False)})
    return {'http_calls_min':sum(r['issued_min'] for r in rows),'http_calls_max':sum(r['issued_max'] for r in rows),
            'entries':rows,'remote_acceptance':'Not established by entering the local HTTP boundary',
            'new_calls_on_inspection':0,'authored_note':'Authored transport rows count simulated boundaries, not real HTTP calls.'}

if __name__=='__main__':print(json.dumps(inspect(Path(sys.argv[1]))))
