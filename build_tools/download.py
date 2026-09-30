from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests, zipfile, os
os.chdir(Path(__file__).resolve().parent.parent)
Path('source_cache').mkdir(exist_ok=True)
urls=[]
for y in (5406,5408):
 for k,stem in [('dgm','dgm1'),('dop20','dop20rgb'),('lod2','LoD2')]:
  urls.append(f'https://opengeodata.lgl-bw.de/data/{k}/{stem}_32_461_{y}_2_bw.zip')
def get(u):
 p=Path('source_cache')/u.split('/')[-1]
 if not p.exists():
  with requests.get(u,stream=True,timeout=(30,300)) as r:
   r.raise_for_status()
   with p.with_suffix('.part').open('wb') as f:
    for b in r.iter_content(1048576):f.write(b)
  p.with_suffix('.part').rename(p)
 with zipfile.ZipFile(p) as z: print(p.name,p.stat().st_size,z.namelist()[:5],flush=True)
with ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(get,urls))
