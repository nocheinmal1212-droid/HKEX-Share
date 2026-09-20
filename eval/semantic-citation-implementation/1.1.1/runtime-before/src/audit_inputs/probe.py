"""Isolated initial consumer probe. Run in a fresh interpreter, never the host process.

This is an accidental-access regression harness, not a hostile-code security sandbox.
Native libraries and later extractor subprocesses require their own instrumentation.
"""
import io
import json
import os
from pathlib import Path
import sys


def main():
    payload=json.load(sys.stdin)
    from audit_inputs.guard import install
    install(payload["allowed"])
    results=[]
    for path in payload['probes']:
        methods={}
        for method in ['open','pathlib','io','os.open']:
            try:
                if method=='pathlib': Path(path).read_bytes()
                elif method=='os.open':
                    fd=os.open(path,os.O_RDONLY)
                    try: os.read(fd,1)
                    finally: os.close(fd)
                else:
                    with (io.open if method=='io' else open)(path,'rb') as stream: stream.read(1)
                methods[method]='allowed'
            except PermissionError: methods[method]='denied'
        results.append({'path':path,'methods':methods})
    print(json.dumps(results))


if __name__=='__main__': main()
