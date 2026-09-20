from pathlib import Path
import copy
import json
import tempfile
from hkex_audit.artifacts import read, encode, sha
from hkex_audit.adapters.mineru import adapt

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = {'doc_id':'synthetic-document','variant_id':'sample','source_document_sha256':None,'source_provenance':'synthetic'}

def native():
    return read(ROOT/'tests/fixtures/evidence/native.json')

def evidence(value=None):
    value = value if value is not None else native()
    return adapt(value, DOCUMENT, sha(encode(value)))

def selection(path, document=None):
    return {'schema_version':'1.0.0','mode':'native','document':document or DOCUMENT,
            'artifacts':[{'role':'middle_json','path':str(Path(path).resolve()),'sha256':sha(Path(path).read_bytes())}]}

def ir_selection(directory):
    directory = Path(directory)
    manifest=read(directory/'manifest.json')
    return {'schema_version':'1.0.0','mode':'ir','document':manifest['document'],
            **{k:{'path':str((directory/(name+'.json')).resolve()),'sha256':sha((directory/(name+'.json')).read_bytes())}
               for k,name in [('evidence','evidence'),('manifest','manifest')]}}
