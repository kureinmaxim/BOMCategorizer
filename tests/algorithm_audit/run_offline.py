"""Run selected audit/tests offline, with an isolated copy of the local database."""
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'docs' / 'algorithm_audit_evidence'
OUT.mkdir(exist_ok=True)
os.environ['PYTHONIOENCODING'] = 'utf-8'
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8')

def deny_network(*args, **kwargs):
    raise RuntimeError('Network disabled for algorithm audit')

socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network

from bom_categorizer import component_database
db_copy = OUT / 'isolated_database.json'
shutil.copyfile(ROOT / 'component_database.json', db_copy)
component_database.get_database_path = lambda: str(db_copy)

if sys.argv[1:2] == ['--script']:
    runpy.run_path(sys.argv[2], run_name='__main__')
else:
    import pytest
    raise SystemExit(pytest.main(['-p', 'no:cacheprovider', *sys.argv[1:]]))
