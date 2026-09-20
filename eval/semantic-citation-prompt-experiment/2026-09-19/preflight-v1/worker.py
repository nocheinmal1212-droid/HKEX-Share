"""Experiment worker. Never detaches: the single outer supervisor owns every descendant."""
import base64
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PACKET=Path(__file__).resolve().parent
ROOT=PACKET.parents[3]
PREP=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19/prepared-v1'

def boot(arm):
    sys.path.insert(0,str(PREP/arm/'runtime-snapshot/src'))

def offline_guard(event,args):
    if event in {'socket.__new__','socket.connect','socket.getaddrinfo'}:
        raise PermissionError('offline experiment denies network')

def send(job,prefix,deadline,fixture=None):
    from hkex_audit import semantic_cli as cli
    from hkex_audit.artifacts import write_new, loads
    if fixture is None:
        return cli.send_transport(job,prefix,deadline)
    # Explicit authored replacement, not a patched production transport.
    if time.monotonic()>=deadline.work_end:
        return {'transport_status':'budget_exhausted','request_started':False}
    write_new(Path(str(prefix)+'-launch.json'),{'mode':job['mode'],'role':job['role'],
        'state':'launch_intent','issued_http_calls':'unknown_until_return','maximum_http_calls':1,'authored':True})
    from hkex_audit.semantic_deadline import DeadlineExpired
    try:
        timeout=deadline.remaining(60)
        p=subprocess.run([sys.executable,'-I','-B',str(PACKET/'offline_transport.py')],
            input=json.dumps({'job':{**job,'deadline_monotonic':deadline.work_end},'fixture':fixture,'prefix':str(prefix)}),
            text=True,capture_output=True,env={},timeout=timeout,close_fds=True)
        record=loads(p.stdout) if p.returncode==0 else {'transport_status':'transport_error','authored_fixture_error':p.stderr}
    except (subprocess.TimeoutExpired,DeadlineExpired):
        record={'transport_status':'timeout'}
    write_new(Path(str(prefix)+'-return.json'),record)
    return record

def metadata_valid(record,config):
    data=json.loads(base64.b64decode(record['body_base64']))['data']
    assert record['transport_status']=='ok' and data['id']==config['model']
    endpoints=[e for e in data['endpoints'] if e.get('tag')==config['route'] and e.get('status')==0]
    assert len(endpoints)==1
    ep=endpoints[0]
    assert ep['provider_name']==config['served_provider']
    assert {'structured_outputs','response_format','temperature','max_tokens'}<=set(ep['supported_parameters'])
    price=ep['pricing']
    for key,cap in [('prompt','.000005'),('completion','.000020')]:
        v=Decimal(price[key]);assert v.is_finite() and 0<=v<=Decimal(cap)
    assert Decimal(str(price.get('request',0)))==0
    assert Decimal(str(price.get('internal_reasoning',price['completion'])))<=Decimal('.000020')

def pair(payload):
    arm=payload['arm'];boot(arm)
    from hkex_audit import semantic_cli as cli
    from hkex_audit.artifacts import read, write_new
    from hkex_audit.semantic_attempt import CONFIGS,Store,request
    from hkex_audit.semantic_deadline import Deadline
    deadline=Deadline(payload['started'],payload['seconds'])
    deadline.remaining(180)
    if payload['offline']: sys.addaudithook(offline_guard)
    else: assert set(payload)<= {'action','arm','case','output','started','seconds','offline','reservation'}
    name=payload['case'];output=Path(payload['output']);nonce=output.name
    selection=read(PREP/'selection.json')
    spec=next(s for s in read(PREP/'queries.json') if s['name']==name)
    prepared=cli.isolated('prepare_worker',{'selection':selection,'specs':[spec]},timeout=deadline.remaining(180))
    query=prepared['queries'][0]
    assert query==read(PREP/arm/name/'query.json')
    for role in CONFIGS:
        assert request(query,role,nonce)==read(PREP/arm/name/(role+'-request.json'))
        (output/role/name).mkdir(parents=True)
    dest=output/'operational'/name;dest.mkdir(parents=True)
    write_new(output/(name+'-reservations.json'),payload['reservation'])
    fixture=payload.get('fixture') if payload['offline'] else None
    def transport(role):
        return lambda req: send({'mode':'completion','role':role,'payload':req['payload']},
            output/role/name/'transport',deadline,fixture)
    result=cli.paired(query,nonce,Store(output/'primary'/name),Store(output/'research'/name),
        transport('primary'),transport('research'),
        lambda:cli.isolated('consume_worker',{'selection':selection,'spec':spec,'batch':str(output),
            'output':str(dest),'nonce':nonce},timeout=deadline.remaining(180)))
    deadline.remaining(180)
    write_new(output/(name+'-summary.json'),result)

def experiment(payload):
    boot('A')
    from hkex_audit import semantic_cli as cli
    from hkex_audit.artifacts import read,write_new,encode
    from hkex_audit.semantic_attempt import CONFIGS
    from hkex_audit.semantic_deadline import Deadline
    deadline=Deadline(payload['started'],payload['seconds'])
    deadline.remaining(180)
    offline=payload['offline']
    if offline: sys.addaudithook(offline_guard)
    else: assert set(payload)=={'action','output','started','seconds','offline'}
    proposal=read(PACKET/'launch-proposal.json'); arms=read(PACKET/'arms.json')
    if not offline: assert payload['output']==proposal['output'] and payload['seconds']==900
    output=cli.new_directory(payload['output'])
    write_new(output/'launch.json',{'started_monotonic':deadline.started,'deadline_monotonic':deadline.end,
        'work_cutoff_monotonic':deadline.work_end,'state':'incomplete_until_supervisor_receipt',
        'version':'prompt-factorial-1.0.0','authored':offline})
    reserved=Decimal(0); count=0
    for role,config in CONFIGS.items():
        deadline.remaining(60);count+=1
        write_new(output/('metadata-'+role+'-reservation.json'),{'http_calls_reserved':count})
        record=send({'mode':'metadata','role':role},output/('metadata-'+role),deadline,
                    payload.get('fixture',{}) if offline else None)
        metadata_valid(record,config)  # Either unavailable route stops this experiment.
    for index,slot in enumerate(proposal['schedule']):
        deadline.remaining(180)
        arm=slot['arm'];name=slot['case'];allocation={}
        for role in CONFIGS:
            req=read(PREP/arm/name/(role+'-request.json'))
            estimate=Decimal(len(encode(req['payload']))+4096)*Decimal('.000010')+Decimal(4096)*Decimal('.000020')
            assert count<18 and reserved+estimate<=Decimal('16')
            count+=1;reserved+=estimate
            allocation[role]={'reserved_cost_usd':str(estimate),'http_calls_reserved':count}
        write_new(output/('slot-'+str(index)+'-reservation.json'),{'slot':slot,'roles':allocation,
            'aggregate_cost_reserved_usd':str(reserved),'aggregate_http_calls_reserved':count})
        data={'action':'pair',**slot,'output':str(output/arms[arm]['nonce']),
            'started':deadline.started,'seconds':payload['seconds'],'offline':offline,'reservation':allocation}
        if offline: data['fixture']=payload.get('fixture',{})
        # Inherit session, never start_new_session: the outer deadline includes child/thread cleanup.
        # Only the key is forwarded during live operation; offline children get an empty environment.
        env={} if offline else {'OPENROUTER_API_KEY':os.environ['OPENROUTER_API_KEY']}
        p=subprocess.run([sys.executable,'-I','-B',str(PACKET/'worker.py')],input=json.dumps(data),
            text=True,capture_output=True,close_fds=True,env=env,timeout=deadline.remaining(899))
        write_new(output/('slot-'+str(index)+'-return.json'),{'returncode':p.returncode,'stderr':p.stderr,'stdout':p.stdout})
        assert p.returncode==0, 'slot interrupted; no replacement or subsequent slots'
    deadline.remaining(180)
    write_new(output/'summary.json',{'http_calls_reserved':count,'cost_reserved_usd':str(reserved),
        'schedule':proposal['schedule'],'authored':offline,'elapsed_seconds':time.monotonic()-deadline.started})

if __name__=='__main__':
    p=json.load(sys.stdin)
    {'experiment':experiment,'pair':pair}[p['action']](p)
