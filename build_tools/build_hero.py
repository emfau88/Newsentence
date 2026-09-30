"""Non-destructive Neusatz LOD0 build. Run from project parent directory."""
import sys,json,hashlib,zipfile,shutil,io,os
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import trimesh
from lxml import etree
import mapbox_earcut
os.chdir(Path(__file__).resolve().parent.parent)
sys.path.insert(0,str(Path('build_tools').resolve()))
import build_neusatz_master as old
from preserve_jpeg import embed_original_jpeg
OUT=Path('.'); OUT.mkdir(exist_ok=True)
(OUT/'lod0').mkdir(exist_ok=True); (OUT/'lod1').mkdir(exist_ok=True);(OUT/'lod2').mkdir(exist_ok=True)
SRC=Path('lod1'); CACHE=Path('source_cache')
B=[461002.5,5406202.5,462998.5,5408198.5]; E0,N0=462000,5407000;Z0=290
master=trimesh.load(SRC/'neusatz_master.glb',force='scene',process=False)
terrain=master.geometry['Terrain_DGM1_DOP20']; bgv=terrain.vertices.reshape(1200,1200,3); bgh=bgv[:,:,1]+Z0
bgimg=np.asarray(terrain.visual.material.baseColorTexture.convert('RGB'))
def coarse(e,n):
 x=(np.asarray(e)-459000.5)/5; y=(np.asarray(n)-5404000.5)/5
 i=np.floor(x).astype(int);j=np.floor(y).astype(int);u=x-i;v=y-j
 a=bgh[j,i];b=bgh[j,i+1];c=bgh[j+1,i];d=bgh[j+1,i+1]
 return np.where(u+v<=1,a+(b-a)*u+(c-a)*v,d+(c-d)*(1-u)+(b-d)*(1-v))
def weight(e,n):
 dist=np.minimum(np.minimum(e-B[0],B[2]-e),np.minimum(n-B[1],B[3]-n))
 t=np.clip(dist/100,0,1);return t*t*(3-2*t)
# Raw source grid: retain 1m raster; reject missing values.
raw=np.full((1997,1997),np.nan,np.float32)
for p in sorted(CACHE.glob('dgm*.zip')):
 a=old._load_xyz_from_zip(p);i=np.rint(a[:,0]-B[0]).astype(int);j=np.rint(a[:,1]-B[1]).astype(int)
 ok=(i>=0)&(i<=1996)&(j>=0)&(j<=1996)
 assert np.max(np.abs(a[ok,0]-B[0]-i[ok]))<1e-5
 raw[j[ok],i[ok]]=a[ok,2];print('DGM',p.name,int(ok.sum()),flush=True)
 del a,i,j,ok
assert np.isfinite(raw).all(),f'Missing DGM: {np.isnan(raw).sum()}'
es=B[0]+np.arange(1997);ns=B[1]+np.arange(1997);E,N=np.meshgrid(es,ns)
w=weight(E,N);co=coarse(E,N);heights=raw*w+co*(1-w)
np.savez_compressed(OUT/'terrain_height_reference.npz',raw_nhn=raw,stitched_nhn=heights.astype('f4'),bounds=B)
# Global normals shared across tile edges.
dn,de=np.gradient(heights);norm=np.stack([-de,np.ones_like(de),dn],axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
# DOP extract georeferenced original TIFs (no giant mosaic).
tifdir=CACHE/'tifs';tifdir.mkdir(exist_ok=True)
for p in sorted(CACHE.glob('dop*.zip')):
 with zipfile.ZipFile(p) as z:
  for name in z.namelist():
   if name.lower().endswith(('.tif','.tiff','.tfw','.prj')) and not (tifdir/name).exists():z.extract(name,tifdir)
tifs=list(tifdir.rglob('*.tif'));assert tifs
rasters=[rasterio.open(p) for p in tifs]
manifest={'bounds_epsg25832':B,'local_origin':[E0,N0,Z0],'coordinate_convention':'X=east-originE, Y=NHN-290, Z=originN-north','terrain_step_m':1,'dop_pixel_m':0.2,'tile_size_m':499,'texture_size_px':2499,'texture_gutter_px':2,'transition_width_m':100,'tiles':[],'attribution':old.ATTRIBUTION,'modified_data':True}
report={'source_files':[], 'dgm_missing':0,'terrain_triangles':7968032,'hero_raw_height_range_nhn':[float(raw.min()),float(raw.max())],'master_sha256':hashlib.sha256((SRC/'neusatz_master.glb').read_bytes()).hexdigest(),'transition_max_height_adjustment_m':float(np.abs(heights-raw).max()),'outer_edge_height_error_m':float(np.max(np.abs((heights-co)[w==0]))),'texture_coverage':[],'tile_seams_max_position_error_m':0.0,'tile_seams_max_normal_error':0.0}
for p in sorted(CACHE.glob('*.zip')):report['source_files'].append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for ty in range(4):
 for tx in range(4):
  left=B[0]+tx*499;bottom=B[1]+ty*499;right=left+499;top=bottom+499
  # two pixel gutters: keep original sampling resolution and avoid filtering seams.
  l,b,r,t=left-.4,bottom-.4,right+.4,top+.4;size=2499
  canvas=np.zeros((size,size,3),np.uint8);cov=np.zeros((size,size),bool)
  for s in rasters:
   bb=s.bounds;il=max(l,bb.left);ir=min(r,bb.right);ib=max(b,bb.bottom);it=min(t,bb.top)
   if ir<=il or it<=ib:continue
   x0=max(0,int(round((il-l)/.2)));x1=min(size,int(round((ir-l)/.2)));y0=max(0,int(round((t-it)/.2)));y1=min(size,int(round((t-ib)/.2)))
   # Snap target bounds to tile pixel grid. Boundless reads preserve exact affine mapping.
   win=from_bounds(l+x0*.2,t-y1*.2,l+x1*.2,t-y0*.2,s.transform)
   data=s.read([1,2,3],window=win,out_shape=(3,y1-y0,x1-x0),resampling=Resampling.bilinear,boundless=True)
   canvas[y0:y1,x0:x1]=data.transpose(1,2,0);cov[y0:y1,x0:x1]=True
  assert cov.all(),f'DOP missing tile {tx} {ty}: {(~cov).sum()}'
  report['texture_coverage'].append({'tile':[tx,ty],'missing_pixels':int((~cov).sum())})
  pe=l+(np.arange(size)+.5)*.2;pn=t-(np.arange(size)+.5)*.2;TE,TN=np.meshgrid(pe,pn);tw=weight(TE,TN)
  if tw.min()<1:
   # Original master texture coordinates, with glTF UV convention and bilinear filtering.
   xx=(TE-459000)/6000*bgimg.shape[1]-.5;yy=(5410000-TN)/6000*bgimg.shape[0]-.5
   for c in range(3):
    bgc=map_coordinates(bgimg[:,:,c].astype('f4'),[yy,xx],order=1,mode='nearest')
    canvas[:,:,c]=np.rint(canvas[:,:,c]*tw+bgc*(1-tw)).astype('u1')
  tex=OUT/'lod0'/f'terrain_{tx}_{ty}.jpg';Image.fromarray(canvas).save(tex,quality=96,subsampling=0)
  j0=ty*499;i0=tx*499;hh=heights[j0:j0+500,i0:i0+500];ee,nn=np.meshgrid(es[i0:i0+500],ns[j0:j0+500])
  vertices=np.stack([ee-E0,hh-Z0,N0-nn],axis=-1).reshape(-1,3).astype('f4')
  jj,ii=np.meshgrid(np.arange(499),np.arange(499),indexing='ij');a=(jj*500+ii).ravel();bb=a+1;c=a+500;d=c+1
  faces=np.empty((498002,3),np.int32);faces[::2]=np.stack([a,bb,c],axis=-1);faces[1::2]=np.stack([bb,d,c],axis=-1)
  uv=np.stack([((ee-left)/.2+2)/size,((nn-bottom)/.2+2)/size],axis=-1).reshape(-1,2).astype('f4')
  mat=trimesh.visual.material.PBRMaterial(name='DOP20',baseColorTexture=Image.open(tex),metallicFactor=0,roughnessFactor=1)
  mesh=trimesh.Trimesh(vertices=vertices,faces=faces,vertex_normals=norm[j0:j0+500,i0:i0+500].reshape(-1,3),visual=trimesh.visual.texture.TextureVisuals(uv=uv,material=mat),process=False)
  sc=trimesh.Scene(mesh);blob=embed_original_jpeg(sc.export(file_type='glb'),tex.read_bytes());path=OUT/'lod0'/f'terrain_{tx}_{ty}.glb';path.write_bytes(blob);tex.unlink()
  manifest['tiles'].append({'url':f'lod0/{path.name}','bounds_epsg25832':[left,bottom,right,top],'triangles':len(faces),'bytes':len(blob)})
  print('TILE',tx,ty,len(blob),flush=True)
# Complete buildings: select each whole Building by intersection, deduplicate gml IDs.
groups={k:{'v':[],'f':[]} for k in ['RoofSurface','WallSurface','GroundSurface']};seen=set();building_bounds=[];skipped=[];polygons=0;holes=0
for zp in sorted(CACHE.glob('LoD*.zip')):
 with zipfile.ZipFile(zp) as z:
  for gn in [n for n in z.namelist() if n.endswith('.gml')]:
   with z.open(gn) as f:root=etree.parse(f,etree.XMLParser(huge_tree=True))
   for building in root.xpath("//*[local-name()='Building']"):
    bid=building.get('{http://www.opengis.net/gml}id');pts=[]
    for p in building.xpath(".//*[local-name()='posList']"):
     arr=np.fromstring(p.text or '',sep=' ')
     if arr.size%3==0 and arr.size:pts.append(arr.reshape(-1,3))
    if not pts:continue
    allp=np.concatenate(pts);lo=allp.min(0);hi=allp.max(0)
    if hi[0]<B[0] or lo[0]>B[2] or hi[1]<B[1] or lo[1]>B[3] or bid in seen:continue
    seen.add(bid);building_bounds.append({'id':bid,'bounds_utm_nhn':[lo.tolist(),hi.tolist()]})
    for kind in groups:
     for poly in building.xpath(f".//*[local-name()='{kind}']//*[local-name()='Polygon']"):
      rings=[]
      for tag in ('exterior','interior'):
       for p in poly.xpath(f"./*[local-name()='{tag}']//*[local-name()='posList']"):
        arr=np.fromstring(p.text or '',sep=' ').reshape(-1,3)
        if np.allclose(arr[0],arr[-1]):arr=arr[:-1]
        rings.append(arr)
      if not rings:continue
      polygons+=1;holes+=len(rings)-1
      normal=np.sum(np.cross(rings[0]-rings[0][0],np.roll(rings[0],-1,axis=0)-rings[0][0]),axis=0)
      drop=int(np.argmax(np.abs(normal)));pts=np.concatenate(rings);p2=np.delete(pts,drop,axis=1)
      tri=mapbox_earcut.triangulate_float64(p2.astype('f8'),np.cumsum([len(q) for q in rings]).astype('u4')).reshape(-1,3)
      if not len(tri):skipped.append(bid);continue
      tv=pts[tri];flip=np.einsum('ij,j->i',np.cross(tv[:,1]-tv[:,0],tv[:,2]-tv[:,0]),normal)<0
      tri[flip]=tri[flip][:,[0,2,1]]
      loc=np.stack([pts[:,0]-E0,pts[:,2]-Z0,N0-pts[:,1]],axis=-1).astype('f4');g=groups[kind];tri+=len(g['v']);g['v'].extend(loc);g['f'].extend(tri)
scene=trimesh.Scene()
for kind,g in groups.items():
 if not g['f']:continue
 colors={'RoofSurface':[.32,.27,.23,1],'WallSurface':[.72,.70,.64,1],'GroundSurface':[.48,.48,.45,1]}
 m=trimesh.Trimesh(vertices=np.array(g['v']),faces=np.array(g['f']),process=False);m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=kind,baseColorFactor=colors[kind],roughnessFactor=.9,metallicFactor=0,doubleSided=True));scene.add_geometry(m,geom_name=kind,node_name=kind)
scene.export(OUT/'lod0/buildings.glb');manifest['buildings']='lod0/buildings.glb';manifest['building_bounds']=building_bounds
report.update(buildings=len(seen),building_polygons=polygons,polygon_holes=holes,untriangulated_polygons=skipped)
assert not skipped
# LOD1 and LOD2 are already present; never overwrite these source files.
assert hashlib.sha256((OUT/'lod1/neusatz_master.glb').read_bytes()).hexdigest()==report['master_sha256']
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print('COMPLETE',report['buildings'],'buildings',flush=True)
