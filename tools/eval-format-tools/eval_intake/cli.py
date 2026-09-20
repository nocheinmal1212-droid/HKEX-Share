"""Explicit, reproducible local evaluation-preparation commands."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
from .common import digest, lines, read, require, write_once
from .importer import import_records
from .inventory import inventory, verify_sources
from .validation import authorities, schema, validate_records
from .splits import freeze


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    sub=p.add_subparsers(dest='command',required=True)
    inv=sub.add_parser('inventory'); inv.add_argument('--config',required=True,type=Path); inv.add_argument('--output',required=True,type=Path)
    for name in ['import','validate','review-packet','isolation-check']:
        c=sub.add_parser(name); c.add_argument('--manifest',required=True,type=Path)
        if name=='import':
            c.add_argument('--config',required=True,type=Path); c.add_argument('--proposals',type=Path)
        elif name!='isolation-check': c.add_argument('--records',required=True,type=Path)
        if name!='isolation-check':
            c.add_argument('--locations',type=Path); c.add_argument('--splits',type=Path); c.add_argument('--review',type=Path)
        else: c.add_argument('--selection',required=True,type=Path)
        c.add_argument('--output',type=Path,required=name in {'import','review-packet'})
        if name=='validate': c.add_argument('--require-ready',action='store_true')
        if name=='review-packet': c.add_argument('--selection',required=True,type=Path)
    f=sub.add_parser('split-freeze')
    for name in ['grouping','manifest','locations','output']: f.add_argument('--'+name,type=Path,required=True)
    f.add_argument('--previous',type=Path)
    f.add_argument('--salt',default='hkex-intake-v2-001'); f.add_argument('--bootstrap-seed',type=int,default=0)
    return p


def main(argv=None):
    args=parser().parse_args(argv); root=args.root.resolve()
    try:
        if args.command=='inventory':
            out=inventory(root,args.config); schema(root,'intake_manifest',out); write_once(args.output,out)
            report={'files':len(out['files']),'source_manifest':str(args.output)}
        else:
            manifest=read(args.manifest); schema(root,'intake_manifest',manifest); verify_sources(root,manifest)
            if args.command=='isolation-check':
                from .isolation import check
                report=check(root,args.selection,manifest)
                if args.output: write_once(args.output,report)
            elif args.command=='split-freeze':
                grouping=read(args.grouping); locations=read(args.locations)
                schema(root,'intake_grouping',grouping); schema(root,'intake_locations',locations)
                require(locations['manifest_sha256']==digest(args.manifest),'stale mapping manifest')
                out=freeze(root,grouping,args.grouping,args.manifest,args.locations,locations,args.salt,args.bootstrap_seed)
                existing=[p for p in (root/'eval/splits').glob('*.json') if p.resolve()!=args.output.resolve() and read(p).get('bundle_id')==out['bundle_id']]
                if existing:
                    require(args.previous is not None, 'bundle already frozen; mapping-only revision requires --previous')
                if args.previous:
                    prior=read(args.previous)
                    require(prior['assignments']==out['assignments'] and prior['salt']==out['salt'] and prior['bootstrap_seed']==out['bootstrap_seed'], 'cannot reroll or regroup a frozen bundle')
                    require(prior['contract_hashes']==out['contract_hashes'], 'contract migration cannot be disguised as a mapping revision')
                    out.update(revision=prior['revision']+1,predecessor=digest(args.previous),revision_reason='Mapping refinement; original assignments, salt, seed and contract hashes preserved.')
                schema(root,'intake_split',out); write_once(args.output,out)
                report={'groups':len({a['split_group_id'] for a in out['assignments']}),'frozen_split':str(args.output)}
            else:
                locations=read(args.locations) if args.locations else None
                splits=read(args.splits) if args.splits else None
                review=read(args.review) if args.review else None
                if args.command=='import':
                    config=read(args.config)
                    require(digest(args.config)==manifest['source_config_sha256'],'source config differs from manifest')
                    taxonomy,scored=authorities(root)
                    records=import_records(root,config,manifest,taxonomy,scored)
                    entries={e['error_id']:e for e in locations['entries']} if locations else {}
                    assignments={a['site_id']:a for a in splits['assignments']} if splits else {}
                    for r in records:
                        if r['error_id'] in entries:
                            e=entries[r['error_id']]; r.update(site_id=e['site_id'],location=e['location'],secondary_locations=e['secondary_locations'])
                            if e['site_id'] in assignments:
                                a=assignments[e['site_id']]; r.update(split=a['split'],split_group_id=a['split_group_id'])
                    if args.proposals:
                        proposals=lines(args.proposals); ids=[r['error_id'] for r in proposals]
                        require(len(ids)==len(set(ids)) and set(ids)<={r['error_id'] for r in records},'invalid proposal IDs')
                        proposed={r['error_id']:r for r in proposals}
                        require(all(r['ingestion_status']=='pending' for r in proposals),'proposals must remain pending')
                        records=[proposed.get(r['error_id'],r) for r in records]
                    if review:
                        approvals={d['error_id'] for d in review['decisions'] if d['decision']=='approve'}
                        records=[dict(r,ingestion_status='ready') if r['error_id'] in approvals else r for r in records]
                else: records=lines(args.records)
                report=validate_records(root,records,manifest,locations,splits,review,args.manifest,args.locations,args.splits)
                if args.command=='import':
                    from eval_formatter.formatting import format_jsonl
                    content=b''.join(json.dumps(r,ensure_ascii=False,allow_nan=False).encode()+b'\n' for r in records)
                    write_once(args.output,format_jsonl(content)[0])
                elif args.command=='review-packet':
                    from .packet import packet
                    require(locations and splits, 'packet requires frozen split and mappings')
                    packet(root,records,manifest,locations,splits,read(args.selection),args.output)
                    report['packet']=str(args.output/'index.html')
                elif args.output: write_once(args.output,report)
                if args.command=='validate' and args.require_ready and report['pending']:
                    print(json.dumps(report,indent=2)); return 3
        print(json.dumps(report,indent=2)); return 0
    except (ValueError, OSError, KeyError, TypeError, IndexError, subprocess.SubprocessError) as exc:
        print(f'error: {exc}',file=sys.stderr); return 2


if __name__=='__main__': raise SystemExit(main())
