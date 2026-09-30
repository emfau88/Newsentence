"""Restore the exact master GLB from the repository's binary parts, offline."""
from pathlib import Path
import hashlib
import json
import shutil


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ensure_master(project=None):
    root = Path(project) if project is not None else Path(__file__).resolve().parent
    folder = root / 'lod1'
    info = json.loads((folder / 'master_parts.json').read_text(encoding='utf-8'))
    target = folder / info['filename']
    if target.exists():
        if target.stat().st_size != info['bytes'] or digest(target) != info['sha256']:
            raise RuntimeError(f'{target}: Master-Pruefsumme stimmt nicht. Vorhandene Datei wird nicht ersetzt.')
        return target
    parts = []
    for item in info['parts']:
        part = folder / item['filename']
        if not part.is_file() or part.stat().st_size != item['bytes'] or digest(part) != item['sha256']:
            raise RuntimeError(f'{part}: Master-Teil fehlt oder ist beschaedigt. Repository vollstaendig herunterladen.')
        parts.append(part)
    temporary = target.with_suffix(target.suffix + '.tmp')
    try:
        with temporary.open('wb') as output:
            for part in parts:
                with part.open('rb') as source:
                    shutil.copyfileobj(source, output)
        if temporary.stat().st_size != info['bytes'] or digest(temporary) != info['sha256']:
            raise RuntimeError('Zusammengesetzter Master stimmt nicht mit der Original-Pruefsumme ueberein.')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'Master bytegenau wiederhergestellt: {target.name} ({info["sha256"]})')
    return target


if __name__ == '__main__':
    ensure_master()
