"""Reproducible evaluation-only PDF correspondence evidence (not approval)."""
import argparse
import hashlib
from pathlib import Path
from pypdf import PdfReader
from decimal import Decimal
from .common import read, write_once, digest, require, within


def inspect_pair(supplied, origin):
    a,b=PdfReader(supplied),PdfReader(origin)
    rows=[]
    for index,(pa,pb) in enumerate(zip(a.pages,b.pages)):
        def content(p):
            stream=p.get_contents()
            return hashlib.sha256(stream.get_data() if stream else b'').hexdigest()
        def geometry(p):return [Decimal(str(x)) for x in p.mediabox]+[Decimal(str(x)) for x in p.cropbox]+[p.rotation]
        ta,tb=pa.extract_text(),pb.extract_text()
        rows.append({'page_index':index,'geometry_equal':geometry(pa)==geometry(pb),'decoded_content_equal':content(pa)==content(pb),'extracted_text_equal':ta==tb,'supplied_text_sha256':hashlib.sha256(ta.encode()).hexdigest(),'origin_text_sha256':hashlib.sha256(tb.encode()).hexdigest()})
    return {'supplied_sha256':digest(supplied),'origin_sha256':digest(origin),'byte_identical':digest(supplied)==digest(origin),'supplied_pages':len(a.pages),'origin_pages':len(b.pages),'page_comparisons':rows,'status':'pending_visual_and_resource_review','limitation':'Content streams/text equality do not by themselves verify fonts/resources or extraction settings.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--config',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    config=read(args.config); docs={d['variant_id']:d['path'] for d in config['documents']}
    result={e['variant_id']:inspect_pair(within(args.root,docs[e['variant_id']]),within(args.root,e['origin_pdf'])) for e in config['exports']}
    write_once(args.output,result)
    for variant,r in result.items(): print(variant,{k:v for k,v in r.items() if k!='page_comparisons'},'all_page_checks_equal',all(p['geometry_equal'] and p['decoded_content_equal'] and p['extracted_text_equal'] for p in r['page_comparisons']))


if __name__=='__main__':main()
