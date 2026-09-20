"""Read-only evaluator-side issued-call uncertainty; never used in model/consumer inputs."""
import json
from pathlib import Path


def inspect(batch):
    batch=Path(batch)
    rows=[]
    for mode,role,name,prefix in [
        *[('metadata',r,None,batch/('metadata-'+r)) for r in ('primary','research')],
        *[('completion',r,n,batch/r/n/'transport') for n in ('total','period_groups') for r in ('primary','research')]]:
        launch=Path(str(prefix)+'-launch.json');returned=Path(str(prefix)+'-return.json')
        state='not_launched'; lower=upper=0
        if launch.exists():
            state='unknown';upper=1
            try:
                record=json.loads(returned.read_bytes())
                if record.get('request_started') is False:
                    state='prevented';upper=0
                elif record.get('request_started') is True:
                    state='request_boundary_entered';lower=1
            except (OSError,ValueError,TypeError):pass
        rows.append({'mode':mode,'role':role,'case':name,'state':state,'lower':lower,'upper':upper})
    reservations={}
    for name in ('total','period_groups'):
        try:reservations[name]=json.loads((batch/(name+'-reservations.json')).read_bytes())
        except (OSError,ValueError):reservations[name]=None
    return {'http_boundary_lower_bound':sum(r['lower'] for r in rows),
            'http_boundary_upper_bound':sum(r['upper'] for r in rows),
            'remote_acceptance':'not established by entry into request boundary',
            'calls':rows,'completion_reservations':reservations,'new_http_calls':0}
