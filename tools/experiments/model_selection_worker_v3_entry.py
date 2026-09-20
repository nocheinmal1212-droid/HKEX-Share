"""Explicit trusted-module bootstrap for the isolated (-I) transport worker."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_selection_worker_v3 import base, Transport

if __name__ == '__main__':
    base.Transport = Transport
    base.main()
