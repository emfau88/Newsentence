import json, struct

def embed_original_jpeg(blob, jpeg):
    json_len,json_type=struct.unpack_from('<I4s',blob,12)
    assert json_type==b'JSON'
    tree=json.loads(blob[20:20+json_len])
    pos=20+json_len
    bin_len,bin_type=struct.unpack_from('<I4s',blob,pos)
    assert bin_type==b'BIN\x00'
    binary=blob[pos+8:pos+8+bin_len]
    assert len(tree['images'])==1
    image=tree['images'][0]
    view=tree['bufferViews'][image['bufferView']]
    start=view.get('byteOffset',0)
    oldlen=view['byteLength']
    oldpad=(oldlen+3)//4*4
    replacement=jpeg+b'\x00'*((-len(jpeg))%4)
    delta=len(replacement)-oldpad
    binary=binary[:start]+replacement+binary[start+oldpad:]
    for other in tree['bufferViews']:
        if other is not view and other.get('byteOffset',0)>start:
            other['byteOffset']+=delta
    view['byteLength']=len(jpeg)
    image['mimeType']='image/jpeg'
    tree['buffers'][0]['byteLength']=len(binary)
    encoded=json.dumps(tree,separators=(',',':'),ensure_ascii=True).encode()
    encoded+=b' '*((-len(encoded))%4)
    binary+=b'\x00'*((-len(binary))%4)
    size=12+8+len(encoded)+8+len(binary)
    return struct.pack('<4sII',b'glTF',2,size)+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\x00')+binary

if __name__=='__main__':
    from pathlib import Path
    for name,size in [('neusatz_master.glb',8192),('neusatz_web.glb',4096)]:
        p=Path(name)
        blob=embed_original_jpeg(p.read_bytes(),Path(f'.neusatz_work/neusatz_dop20_{size}.jpg').read_bytes())
        p.write_bytes(blob)
        print(name,len(blob)/1048576,'MiB')
