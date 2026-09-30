"""Run: python start_viewer.py ; open http://localhost:8080"""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import os,webbrowser
from prepare_models import ensure_master
os.chdir(Path(__file__).resolve().parent)
ensure_master()
print('Neusatz 3D: http://localhost:8080')
webbrowser.open('http://localhost:8080')
ThreadingHTTPServer(('127.0.0.1',8080),SimpleHTTPRequestHandler).serve_forever()
