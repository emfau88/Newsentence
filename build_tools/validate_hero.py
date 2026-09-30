import json,struct,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent.parent;report=json.loads((P/'validation.json').read_text())
def read(p):
 b=p.read_bytes();l=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+l]);start=28+l
 def arr(a):
  q=g['accessors'][a];v=g['bufferViews'][q['bufferView']];types={5126:'<f4',5125:'<u4',5123:'<u2'};sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[q['type']]
  return np.frombuffer(b,dtype=types[q['componentType']],count=q['count']*sz,offset=start+v.get('byteOffset',0)+q.get('byteOffset',0)).reshape(-1,sz)
 pr=g['meshes'][0]['primitives'][0];return arr(pr['attributes']['POSITION']).reshape(500,500,3),arr(pr['attributes']['NORMAL']).reshape(500,500,3),g
pos={};norm={};me=ne=0.;image_sizes=[]
from PIL import Image
import io
for y in range(4):
 for x in range(4):
  p=P/f'lod0/terrain_{x}_{y}.glb';v,n,g=read(p);pos[x,y]=v;norm[x,y]=n
  b=p.read_bytes();l=struct.unpack_from('<I',b,12)[0];im=g['images'][0];bv=g['bufferViews'][im['bufferView']];o=28+l+bv.get('byteOffset',0)
  a=Image.open(io.BytesIO(b[o:o+bv['byteLength']]));image_sizes.append(a.size);assert a.size==(2499,2499)
  if x:
   me=max(me,float(np.abs(pos[x-1,y][:,-1]-v[:,0]).max()));ne=max(ne,float(np.abs(norm[x-1,y][:,-1]-n[:,0]).max()))
  if y:
   me=max(me,float(np.abs(pos[x,y-1][-1,:]-v[0,:]).max()));ne=max(ne,float(np.abs(norm[x,y-1][-1,:]-n[0,:]).max()))
assert me==0 and ne<1e-6
# Validate exported outer perimeter against exact old 5m triangles.
z=np.load(P/'terrain_height_reference.npz');h=z['stitched_nhn'];exports=np.concatenate([pos[x,0][0,:,1]+290 for x in range(4)])
ref=np.concatenate([h[0,x*499:x*499+500] for x in range(4)])
assert np.max(np.abs(exports-ref))<.0001
report['tile_seams_max_position_error_m']=me;report['tile_seams_max_normal_error']=ne;report['exported_south_edge_height_error_m']=float(np.abs(exports-ref).max());report['texture_dimensions_verified']=image_sizes;report['master_identical_to_input']=hashlib.sha256((P/'lod1/neusatz_master.glb').read_bytes()).hexdigest()==report['master_sha256'];assert report['master_identical_to_input']
(P/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_files','texture_coverage','texture_dimensions_verified']},indent=2))
