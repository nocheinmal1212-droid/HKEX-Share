"""Portable schema-only check; deliberately does not claim raw-source verification."""
import argparse
from pathlib import Path
from .common import lines, read, require
from .validation import authorities, schema


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));args=p.parse_args()
    authorities(args.root)
    paths=sorted((args.root/'eval/records').rglob('*.jsonl'));require(paths,'no canonical records discovered')
    count=0
    for path in paths:
        for record in lines(path):schema(args.root,'error_record',record);count+=1
    for glob,name in [('eval/manifests/*.json','intake_manifest'),('eval/locations/*.json','intake_locations'),('eval/splits/*.json','intake_split')]:
        for path in args.root.glob(glob):schema(args.root,name,read(path))
    print(f'Schema-only validation: taxonomy and {count} records in {len(paths)} revisions. Source integrity/readiness require eval-intake validate.')


if __name__=='__main__':main()
