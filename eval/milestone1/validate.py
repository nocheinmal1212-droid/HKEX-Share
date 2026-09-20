"""Local M1 native/IR checks. No PDFs, raw injector records or model calls."""
import argparse
import json
from pathlib import Path
import tempfile
from hkex_audit.artifacts import encode, write_new, sha, require
from packet import review_read as read, review_bytes
from hkex_audit.cli import launch
from hkex_audit.evidence import validate_evidence
from eval_intake.runtime_selection import project
from eval_intake.isolation import check as isolation_check

ROOT=Path(__file__).resolve().parents[2]


def ir_selection(directory):
    manifest=read(directory/'manifest.json')
    return {'schema_version':'1.0.0','mode':'ir','document':manifest['document'],
            **{name:{'path':str((directory/(name+'.json')).resolve()),'sha256':sha((directory/(name+'.json')).read_bytes())} for name in ['evidence','manifest']}}


def verified_intake():
    cfg=read(ROOT/'eval/milestone1/selection.json');ready=read(ROOT/cfg['ready_selector'])
    require(set(c['error_id'] for c in cfg['cases'])==set(ready['error_ids']),'case selection differs from ready subset')
    for key in ['records','locations','splits','review']:
        require(sha(review_bytes(ROOT/ready[key+'_path']))==ready[key+'_sha256'],'ready-selector hash mismatch: '+key)
    records={}
    for line in review_bytes(ROOT/ready['records_path']).decode('utf-8').splitlines():
        record=json.loads(line)
        if record['error_id'] in ready['error_ids']:
            require(record['ingestion_status']=='ready' and record['split']=='dev','unready/non-development fixture')
            records[record['error_id']]=record
    require(len(records)==4,'ready subset is incomplete')
    return cfg,ready,records


def literal_inventory(native):
    expected={}
    def visit(obj,ptr):
        if isinstance(obj,dict):
            for key,value in obj.items():
                child=ptr+'/'+key.replace('~','~0').replace('/','~1')
                if key in {'content','html'} and isinstance(value,str):expected[child]=value
                visit(value,child)
        elif isinstance(obj,list):
            for i,value in enumerate(obj):visit(value,ptr+'/'+str(i))
    for i,page in enumerate(native['pdf_info']):
        for branch in ['preproc_blocks','discarded_blocks']:visit(page[branch],f'/pdf_info/{i}/{branch}')
    return expected


def run_checks(output):
    cfg,ready,records=verified_intake();sources=read(ROOT/cfg['source_config']);manifest=read(ROOT/cfg['source_manifest'])
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    variants={}
    # Native runtime workers see one variant each; evaluation occurs only afterwards.
    for export in sources['exports']:
        variant=export['variant_id'];selection=project(ROOT,manifest,sources['doc_id'],variant,export['middle_json'])
        selection_path=output/(variant+'-native-selection.json');write_new(selection_path,selection)
        run_dir=output/variant
        require(launch('ingest',selection_path,run_dir)==0,'native runtime failed')
        variants[variant]={'run_dir':str(run_dir),'selection':str(selection_path)}
    for variant,entry in variants.items():
        directory=Path(entry['run_dir']);selection=read(entry['selection']);evidence=read(directory/'evidence.json');inventory=read(directory/'inventory.json')
        raw=read(selection['artifacts'][0]['path']);validate_evidence(evidence,raw)
        expected=literal_inventory(raw);actual={s['pointer']:s['text'] for s in evidence['sources'] if s['format'] in {'text','html'}}
        require(actual==expected,'native literal inventory differs from IR')
        require((inventory['pages'],inventory['table_regions'],inventory['cells'])==(cfg['expected_pages_per_run'],cfg['expected_table_regions_per_run'],cfg['expected_cells_per_run']),'source-backed inventory mismatch')
        run=read(directory/'run.json');allowed={selection['artifacts'][0]['path']}
        require({x['path'] for x in run['access_attempts'] if x.get('access')=='read'}==allowed,'adapter read unselected data')
        require(launch('ingest',entry['selection'],output/(variant+'-repeat'))==0,'repeat ingestion failed')
        require((directory/'evidence.json').read_bytes()==(output/(variant+'-repeat/evidence.json')).read_bytes(),'nondeterministic IR')
        replay_selection=output/(variant+'-ir-selection.json');write_new(replay_selection,ir_selection(directory))
        replay=output/(variant+'-replay');require(launch('inspect',replay_selection,replay)==0,'IR replay failed')
        require((directory/'context.json').read_bytes()==(replay/'context.json').read_bytes(),'context replay mismatch')
        replay_inventory=read(replay/'inventory.json');require({k:v for k,v in replay_inventory.items() if k!='native_fidelity'}=={k:v for k,v in inventory.items() if k!='native_fidelity'},'inventory replay mismatch')
        replay_run=read(replay/'run.json');require(not replay_run['adapter_imported'],'IR replay imported adapter')
        require({x['path'] for x in replay_run['access_attempts'] if x.get('access')=='read'}=={str(directory/'evidence.json'),str(directory/'manifest.json')},'IR consumer read unselected data')
        entry.update(inventory=inventory,evidence_sha256=sha((directory/'evidence.json').read_bytes()),manifest_sha256=sha((directory/'manifest.json').read_bytes()),
                     literal_pointer_count=len(expected),replay='byte_identical_evidence_and_context',isolation=isolation_check(ROOT,Path(entry['selection']),manifest))
    report={'structural_status':'passed','review_status':'pending','publication_status':'UNGATED','headline':None,'variants':variants,
            'ready_records':len(records),'pending_intake_records':44,'limitations':['No new PDF fidelity approval.','No semantic/check execution.','IR/fixture acceptance requires owner review.']}
    write_new(output/'verification.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.output:
        report=run_checks(args.output)
    else:
        with tempfile.TemporaryDirectory(prefix='m1-local-') as tmp:report=run_checks(Path(tmp))
    print(json.dumps({'status':report['structural_status'],'review_status':report['review_status'],'variants':{k:v['inventory'] for k,v in report['variants'].items()}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
