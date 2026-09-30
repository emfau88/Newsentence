from pathlib import Path
import struct,json,numpy as np
P=Path(__file__).resolve().parent.parent;b=(P/'lod1/neusatz_master.glb').read_bytes();l=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+l]);a=g['accessors'][g['meshes'][0]['primitives'][0]['attributes']['POSITION']];v=g['bufferViews'][a['bufferView']];pos=np.frombuffer(b,dtype='<f4',count=a['count']*3,offset=28+l+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(1200,1200,3);h=pos[:,:,1]+290
z=np.load(P/'terrain_height_reference.npz');B=z['bounds'];hero=z['stitched_nhn'];es=B[0]+np.arange(1997);ns=B[1]+np.arange(1997)
def coarse(e,n):
 x=(e-459000.5)/5;y=(n-5404000.5)/5;i=np.floor(x).astype(int);j=np.floor(y).astype(int);u=x-i;v=y-j;a=h[j,i];b=h[j,i+1];c=h[j+1,i];d=h[j+1,i+1];return np.where(u+v<=1,a+(b-a)*u+(c-a)*v,d+(c-d)*(1-u)+(b-d)*(1-v))
errors=[np.abs(hero[0]-coarse(es,np.full_like(es,B[1]))).max(),np.abs(hero[-1]-coarse(es,np.full_like(es,B[3]))).max(),np.abs(hero[:,0]-coarse(np.full_like(ns,B[0]),ns)).max(),np.abs(hero[:,-1]-coarse(np.full_like(ns,B[2]),ns)).max()]
r=json.loads((P/'validation.json').read_text());r['independent_perimeter_max_height_error_m']=float(max(errors));assert max(errors)<.0001;r['runtime_edge_overlap_m']=.05;r['runtime_depth_bias']='Hero polygonOffsetFactor=-2, units=-2, avoids subpixel cracks';(P/'validation.json').write_text(json.dumps(r,indent=2));print('Independent full perimeter errors:',errors)
