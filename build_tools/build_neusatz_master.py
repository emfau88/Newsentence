#!/usr/bin/env python3
"""
Neusatz WebGL Master Builder
============================

Erzeugt aus offiziellen Open-GeoData-Daten des LGL Baden-Württemberg
einen browserfreundlichen, georeferenzierten 3D-Masterausschnitt von
Neusatz (Bad Herrenalb) als GLB.

Datenquellen:
- LoD2 CityGML: 9 x 2-km-Kacheln
- DGM1:         9 x 2-km-Kacheln
- DOP20 RGB:    9 x 2-km-Bundles / darin typischerweise 1-km-Bilder

Gebiet:
E 459000..465000
N 5404000..5410000
ETRS89 / UTM Zone 32N (EPSG:25832)

Die Rohdaten bleiben im Cache erhalten. Der GLB-Master nutzt bewusst
eine reduzierte Terrain-Geometrie, damit er in WebGL sinnvoll nutzbar
bleibt. Die volle DGM1-Auflösung dient beim Build als Quelle.

Lizenzhinweis für LGL-Daten:
"Datenquelle: LGL, www.lgl-bw.de, dl-de/by-2-0"
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import requests
from lxml import etree
from PIL import Image
import rasterio
from rasterio.enums import Resampling
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Polygon
from shapely.ops import triangulate
import trimesh


MIN_E, MAX_E = 459000.0, 465000.0
MIN_N, MAX_N = 5404000.0, 5410000.0
ORIGIN_E, ORIGIN_N = 462000.0, 5407000.0
XS = (459, 461, 463)
YS = (5404, 5406, 5408)
ATTRIBUTION = "Datenquelle: LGL, www.lgl-bw.de, dl-de/by-2-0"


def tile_urls():
    out = []
    for y in YS:
        for x in XS:
            out.append({
                "x": x,
                "y": y,
                "lod2": f"https://opengeodata.lgl-bw.de/data/lod2/LoD2_32_{x}_{y}_2_bw.zip",
                "dgm1": f"https://opengeodata.lgl-bw.de/data/dgm/dgm1_32_{x}_{y}_2_bw.zip",
                "dop20": f"https://opengeodata.lgl-bw.de/data/dop20/dop20rgb_32_{x}_{y}_2_bw.zip",
            })
    return out


def download(url: str, target: Path, force: bool = False) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1024 and not force:
        print(f"[cache] {target.name}")
        return target

    tmp = target.with_suffix(target.suffix + ".part")
    headers = {
        "User-Agent": "Neusatz-WebGL-Master/1.0 (+OpenData LGL BW)"
    }
    print(f"[download] {url}")
    with requests.get(url, stream=True, timeout=(20, 300), headers=headers) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r           {done/1048576:7.1f} / {total/1048576:7.1f} MiB", end="")
        if total:
            print()
    tmp.replace(target)
    return target


def fetch_sources(cache_dir: Path, force: bool = False):
    paths = {"lod2": [], "dgm1": [], "dop20": []}
    for t in tile_urls():
        for kind in ("lod2", "dgm1", "dop20"):
            url = t[kind]
            name = url.rsplit("/", 1)[-1]
            p = download(url, cache_dir / kind / name, force=force)
            paths[kind].append(p)
        time.sleep(0.15)
    return paths


def _first_data_line(zf: zipfile.ZipFile, name: str) -> str:
    with zf.open(name, "r") as f:
        for _ in range(50):
            raw = f.readline()
            if not raw:
                break
            line = raw.decode("utf-8", "replace").strip()
            if line and not line.startswith("#"):
                return line
    return ""


def _load_xyz_from_zip(zip_path: Path) -> np.ndarray:
    """
    Lädt genau eine DGM1-Kachel. Es wird nur eine Kachel gleichzeitig
    im RAM gehalten. Das ist absichtlich konservativ.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        candidates = [n for n in zf.namelist()
                      if n.lower().endswith((".xyz", ".txt", ".asc")) and not n.endswith("/")]
        if not candidates:
            raise RuntimeError(f"Keine XYZ/TXT-Datei in {zip_path.name} gefunden")
        xyz = [n for n in candidates if n.lower().endswith(".xyz")]
        arrays = []
        for name in xyz or candidates:
            first = _first_data_line(zf, name)
            delim = ";" if ";" in first else None
            with zf.open(name, "r") as f:
                arr = np.loadtxt(f, dtype=np.float64, delimiter=delim, comments="#")
            if arr.ndim != 2 or arr.shape[1] < 3:
                raise RuntimeError(f"Unerwartetes DGM-Format: {zip_path.name}/{name}")
            arrays.append(arr[:, :3])
        return np.concatenate(arrays, axis=0)


def build_dgm_grid(dgm_zips: list[Path], step: int, work_dir: Path):
    if step < 1:
        raise ValueError("terrain step muss >= 1 m sein")
    print(f"\n[DGM1] Erzeuge {step}-m Terrain-Raster aus 1-m-Quelldaten ...")

    # LGL Rasterpunkte liegen seit Rastermodell-Umstellung typischerweise
    # im Pixelzentrum. Den tatsächlichen Offset bestimmen wir aus den Daten.
    probe = _load_xyz_from_zip(dgm_zips[0])
    frac_e = float(np.median(probe[: min(len(probe), 1000), 0] % 1.0))
    frac_n = float(np.median(probe[: min(len(probe), 1000), 1] % 1.0))
    del probe

    start_e = MIN_E + frac_e
    start_n = MIN_N + frac_n
    nx = int(math.floor((MAX_E - start_e) / step)) + 1
    ny = int(math.floor((MAX_N - start_n) / step)) + 1

    h_path = work_dir / "terrain_heights.dat"
    h = np.memmap(h_path, dtype="float32", mode="w+", shape=(ny, nx))
    h[:] = np.nan

    for zi, zp in enumerate(dgm_zips, 1):
        print(f"  [{zi}/{len(dgm_zips)}] {zp.name}")
        arr = _load_xyz_from_zip(zp)
        x, y, z = arr[:, 0], arr[:, 1], arr[:, 2]

        ix_f = (x - start_e) / step
        iy_f = (y - start_n) / step
        ix = np.rint(ix_f).astype(np.int32)
        iy = np.rint(iy_f).astype(np.int32)

        # Nur Punkte übernehmen, die auf dem Zielraster liegen.
        mask = (
            (np.abs(ix_f - ix) < 0.03) &
            (np.abs(iy_f - iy) < 0.03) &
            (ix >= 0) & (ix < nx) &
            (iy >= 0) & (iy < ny)
        )
        h[iy[mask], ix[mask]] = z[mask]
        del arr, x, y, z, ix_f, iy_f, ix, iy, mask

    missing = np.isnan(h)
    miss_count = int(missing.sum())
    if miss_count:
        ratio = miss_count / h.size
        if ratio > 0.001:
            raise RuntimeError(f"Unvollständiges Gelände: {ratio:.2%} fehlen; Build abgebrochen")
        print(f"  Hinweis: {miss_count:,} Rasterpunkte fehlen ({ratio:.4%}); fülle per nächstem Nachbarn.")
        # nearest-neighbour indices for NaNs
        inds = distance_transform_edt(
            missing, return_distances=False, return_indices=True
        )
        filled = h[tuple(inds)]
        h[:] = filled[:]
        del filled, inds

    z_min = float(np.nanmin(h))
    z_max = float(np.nanmax(h))
    z_base = math.floor(z_min / 10.0) * 10.0
    print(f"  Höhe: {z_min:.2f} .. {z_max:.2f} m NHN; lokaler Z-Nullpunkt: {z_base:.1f} m")

    easting = start_e + np.arange(nx, dtype=np.float64) * step
    northing = start_n + np.arange(ny, dtype=np.float64) * step
    return h, easting, northing, z_base, z_min, z_max


def build_dop_texture(dop_zips: list[Path], out_path: Path, size: int, quality: int):
    print(f"\n[DOP20] Mosaik -> {size}x{size}px JPEG ...")
    if size > 16384:
        print("  WARNUNG: >16384 px überschreitet die maximale Texturgröße vieler GPUs.")

    mmap_path = out_path.with_suffix(".rgb")
    canvas = np.memmap(mmap_path, dtype="uint8", mode="w+", shape=(size, size, 3))
    canvas[:] = 0
    coverage = np.zeros((size, size), dtype=bool)

    extent_w = MAX_E - MIN_E
    extent_h = MAX_N - MIN_N

    with tempfile.TemporaryDirectory(prefix="neusatz_dop_") as td:
        temp_root = Path(td)
        for zi, zp in enumerate(dop_zips, 1):
            print(f"  [{zi}/{len(dop_zips)}] {zp.name}")
            tile_dir = temp_root / f"z{zi}"
            tile_dir.mkdir()
            with zipfile.ZipFile(zp, "r") as zf:
                # TIF + Worldfiles zusammen extrahieren.
                useful = [
                    n for n in zf.namelist()
                    if n.lower().endswith((".tif", ".tiff", ".tfw", ".tifw", ".wld", ".prj"))
                ]
                for n in useful:
                    zf.extract(n, tile_dir)

            tifs = list(tile_dir.rglob("*.tif")) + list(tile_dir.rglob("*.tiff"))
            for tif in tifs:
                with rasterio.open(tif) as src:
                    b = src.bounds
                    left = max(b.left, MIN_E)
                    right = min(b.right, MAX_E)
                    bottom = max(b.bottom, MIN_N)
                    top = min(b.top, MAX_N)
                    if right <= left or top <= bottom:
                        continue

                    px0 = max(0, int(math.floor((left - MIN_E) / extent_w * size)))
                    px1 = min(size, int(math.ceil((right - MIN_E) / extent_w * size)))
                    py0 = max(0, int(math.floor((MAX_N - top) / extent_h * size)))
                    py1 = min(size, int(math.ceil((MAX_N - bottom) / extent_h * size)))
                    if px1 <= px0 or py1 <= py0:
                        continue

                    # Rasterio-Fenster aus geographischer Überlappung.
                    win = rasterio.windows.from_bounds(left, bottom, right, top, transform=src.transform)
                    h = py1 - py0
                    w = px1 - px0
                    indexes = [1, 2, 3] if src.count >= 3 else [1]
                    data = src.read(
                        indexes=indexes,
                        window=win,
                        out_shape=(len(indexes), h, w),
                        resampling=Resampling.lanczos,
                        boundless=True,
                        fill_value=0,
                    )
                    if data.shape[0] == 1:
                        data = np.repeat(data, 3, axis=0)
                    rgb = np.moveaxis(data[:3], 0, -1)
                    canvas[py0:py1, px0:px1, :] = rgb.astype(np.uint8, copy=False)
                    coverage[py0:py1, px0:px1] = True

            shutil.rmtree(tile_dir, ignore_errors=True)

    uncovered = int((~coverage).sum())
    if uncovered:
        raise RuntimeError(f"Unvollständige Luftbildtextur: {uncovered} Pixel ohne Quelldaten")
    print("  Luftbildabdeckung: 100 %")
    canvas.flush()
    img = Image.fromarray(np.asarray(canvas), mode="RGB")
    img.save(out_path, format="JPEG", quality=quality, subsampling=0, optimize=True)
    del img, canvas
    try:
        mmap_path.unlink()
    except OSError:
        pass
    print(f"  gespeichert: {out_path} ({out_path.stat().st_size/1048576:.1f} MiB)")


def terrain_mesh(h, eastings, northings, z_base: float, texture_path: Path):
    print("\n[Mesh] Terrain ...")
    ny, nx = h.shape

    # Vertices: glTF/Three.js-freundlich Y-up.
    # X = Ost, Y = Höhe, Z = -Nord.
    E, N = np.meshgrid(eastings, northings)
    verts = np.empty((nx * ny, 3), dtype=np.float32)
    verts[:, 0] = (E.ravel() - ORIGIN_E)
    verts[:, 1] = (np.asarray(h).ravel() - z_base)
    verts[:, 2] = -(N.ravel() - ORIGIN_N)

    # UVs: Süden=0, Norden=1. Textur selbst ist north-up.
    uv = np.empty((nx * ny, 2), dtype=np.float32)
    uv[:, 0] = (E.ravel() - MIN_E) / (MAX_E - MIN_E)
    uv[:, 1] = (N.ravel() - MIN_N) / (MAX_N - MIN_N)

    # 2 Dreiecke je Gridzelle, winding -> +Y.
    j = np.arange(ny - 1, dtype=np.int64)[:, None]
    i = np.arange(nx - 1, dtype=np.int64)[None, :]
    a = (j * nx + i).ravel()
    b = (j * nx + i + 1).ravel()
    c = ((j + 1) * nx + i).ravel()
    d = ((j + 1) * nx + i + 1).ravel()
    faces = np.empty((a.size * 2, 3), dtype=np.int64)
    faces[0::2] = np.stack([a, b, c], axis=1)
    faces[1::2] = np.stack([b, d, c], axis=1)

    image = Image.open(texture_path).convert("RGB")
    image.info["original_jpeg"] = texture_path.read_bytes()
    material = trimesh.visual.material.PBRMaterial(
        name="DOP20_ground",
        baseColorTexture=image,
        metallicFactor=0.0,
        roughnessFactor=1.0,
    )
    visual = trimesh.visual.texture.TextureVisuals(uv=uv, material=material)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, visual=visual, process=False)
    mesh.metadata["source"] = "LGL DGM1 + DOP20"
    mesh.metadata["attribution"] = ATTRIBUTION
    return mesh


def _lname(el):
    try:
        return etree.QName(el).localname
    except Exception:
        return ""


def _extract_ring(poly_el) -> Optional[np.ndarray]:
    # bevorzugt exterior/LinearRing/posList
    poslists = poly_el.xpath(
        ".//*[local-name()='exterior']//*[local-name()='LinearRing']/*[local-name()='posList']"
    )
    if not poslists:
        poslists = poly_el.xpath(".//*[local-name()='posList']")
    if poslists:
        el = poslists[0]
        vals = np.fromstring((el.text or "").replace(",", " "), sep=" ", dtype=np.float64)
        dim = int(el.get("srsDimension") or 3)
        if dim < 3 and vals.size % 3 == 0:
            dim = 3
        if vals.size < 9 or vals.size % dim:
            return None
        pts = vals.reshape(-1, dim)[:, :3]
    else:
        poses = poly_el.xpath(
            ".//*[local-name()='exterior']//*[local-name()='LinearRing']/*[local-name()='pos']"
        )
        pts_list = []
        for p in poses:
            vals = np.fromstring((p.text or "").replace(",", " "), sep=" ")
            if vals.size >= 3:
                pts_list.append(vals[:3])
        if len(pts_list) < 3:
            return None
        pts = np.asarray(pts_list, dtype=np.float64)

    if len(pts) >= 2 and np.linalg.norm(pts[0] - pts[-1]) < 1e-6:
        pts = pts[:-1]
    if len(pts) < 3:
        return None
    return pts


def _project_polygon(pts: np.ndarray):
    # Newell normal
    n = np.zeros(3, dtype=np.float64)
    for i in range(len(pts)):
        p = pts[i]
        q = pts[(i + 1) % len(pts)]
        n[0] += (p[1] - q[1]) * (p[2] + q[2])
        n[1] += (p[2] - q[2]) * (p[0] + q[0])
        n[2] += (p[0] - q[0]) * (p[1] + q[1])
    drop = int(np.argmax(np.abs(n)))
    if drop == 0:
        p2 = pts[:, [1, 2]]
    elif drop == 1:
        p2 = pts[:, [0, 2]]
    else:
        p2 = pts[:, [0, 1]]
    return p2


def triangulate_surface(pts: np.ndarray):
    p2 = _project_polygon(pts)
    poly = Polygon(p2)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.area < 1e-8:
        return []

    tris = []
    for tri in triangulate(poly):
        if not poly.covers(tri):
            continue
        coords = np.asarray(tri.exterior.coords[:-1], dtype=np.float64)
        idxs = []
        for q in coords:
            d2 = np.sum((p2 - q) ** 2, axis=1)
            idxs.append(int(np.argmin(d2)))
        if len(set(idxs)) == 3:
            normal = np.sum(np.cross(pts - pts[0], np.roll(pts, -1, axis=0) - pts[0]), axis=0)
            a, b, c = idxs
            if np.dot(np.cross(pts[b]-pts[a], pts[c]-pts[a]), normal) < 0:
                idxs = [a, c, b]
            tris.append(idxs)
    return tris


def build_building_meshes(lod_zips: list[Path], z_base: float):
    print("\n[LoD2] CityGML -> Mesh ...")
    groups = {
        "RoofSurface": {"v": [], "f": [], "color": [0.32, 0.27, 0.23, 1.0]},
        "WallSurface": {"v": [], "f": [], "color": [0.72, 0.70, 0.64, 1.0]},
        "GroundSurface": {"v": [], "f": [], "color": [0.48, 0.48, 0.45, 1.0]},
        "Other": {"v": [], "f": [], "color": [0.62, 0.62, 0.58, 1.0]},
    }

    total_surfaces = 0
    total_tris = 0

    def add_polygon(kind, pts):
        nonlocal total_surfaces, total_tris
        # clip by bbox using at least one point or centroid in requested region
        cen = pts.mean(axis=0)
        if not (MIN_E - 5 <= cen[0] <= MAX_E + 5 and MIN_N - 5 <= cen[1] <= MAX_N + 5):
            return

        tris = triangulate_surface(pts)
        if not tris:
            return

        g = groups[kind if kind in groups else "Other"]
        base = len(g["v"])
        local = np.empty_like(pts, dtype=np.float32)
        local[:, 0] = pts[:, 0] - ORIGIN_E
        local[:, 1] = pts[:, 2] - z_base
        local[:, 2] = -(pts[:, 1] - ORIGIN_N)

        g["v"].extend(local.tolist())
        g["f"].extend([[base + a, base + b, base + c] for a, b, c in tris])
        total_surfaces += 1
        total_tris += len(tris)

    for zi, zp in enumerate(lod_zips, 1):
        print(f"  [{zi}/{len(lod_zips)}] {zp.name}")
        with zipfile.ZipFile(zp, "r") as zf:
            gmls = [n for n in zf.namelist()
                    if n.lower().endswith((".gml", ".xml")) and not n.endswith("/")]
            if not gmls:
                raise RuntimeError(f"Keine CityGML-Datei in {zp.name}")
            for gml_name in gmls:
                with zf.open(gml_name, "r") as f:
                    tree = etree.parse(f, etree.XMLParser(huge_tree=True, recover=True))
                root = tree.getroot()

                for kind in ("RoofSurface", "WallSurface", "GroundSurface"):
                    surfaces = root.xpath(f"//*[local-name()='{kind}']")
                    for surface in surfaces:
                        polys = surface.xpath(".//*[local-name()='Polygon']")
                        for poly in polys:
                            pts = _extract_ring(poly)
                            if pts is not None:
                                add_polygon(kind, pts)
                del tree, root

    meshes = {}
    for kind, g in groups.items():
        if not g["f"]:
            continue
        mat = trimesh.visual.material.PBRMaterial(
            name=kind,
            baseColorFactor=g["color"],
            metallicFactor=0.0,
            roughnessFactor=0.86 if kind != "RoofSurface" else 0.75,
        )
        mesh = trimesh.Trimesh(
            vertices=np.asarray(g["v"], dtype=np.float32),
            faces=np.asarray(g["f"], dtype=np.int64),
            process=False,
        )
        valid = mesh.area_faces > 1e-8
        if not valid.all():
            print(f"  {kind}: entferne {int((~valid).sum())} degenerierte Dreiecke")
            mesh.update_faces(valid)
        mesh.visual = trimesh.visual.TextureVisuals(material=mat)
        mesh.metadata["source"] = "LGL LoD2"
        mesh.metadata["surface_type"] = kind
        mesh.metadata["attribution"] = ATTRIBUTION
        meshes[kind] = mesh

    print(f"  {total_surfaces:,} Flächen / {total_tris:,} Dreiecke")
    return meshes


def export_scene(output: Path, terrain, building_meshes, meta: dict):
    print("\n[GLB] Export ...")
    scene = trimesh.Scene()
    scene.add_geometry(terrain, geom_name="Terrain_DGM1_DOP20", node_name="Terrain")
    for kind, mesh in building_meshes.items():
        scene.add_geometry(mesh, geom_name=f"Buildings_{kind}", node_name=f"Buildings_{kind}")

    scene.metadata.update(meta)
    blob = scene.export(file_type="glb")
    from preserve_jpeg import embed_original_jpeg
    blob = embed_original_jpeg(blob, terrain.visual.material.baseColorTexture.info["original_jpeg"])
    output.write_bytes(blob)
    print(f"  {output} ({output.stat().st_size/1048576:.1f} MiB)")


def write_build_report(path: Path, args, z_min, z_max, z_base, output: Path):
    report = {
        "project": "Neusatz WebGL Master",
        "output": str(output),
        "extent_epsg25832": [MIN_E, MIN_N, MAX_E, MAX_N],
        "local_origin_epsg25832": [ORIGIN_E, ORIGIN_N],
        "coordinate_convention": "glTF Y-up; X=east, Z=-north, Y=elevation-z_base",
        "terrain_step_m": args.terrain_step,
        "texture_size_px": args.texture_size,
        "vertical_base_nhn": z_base,
        "height_min_m_nhn": z_min,
        "height_max_m_nhn": z_max,
        "source": {
            "LoD2": "LGL Baden-Württemberg CityGML",
            "DGM1": "LGL Baden-Württemberg 1m terrain model",
            "DOP20": "LGL Baden-Württemberg 20cm RGB orthophotos",
        },
        "attribution": ATTRIBUTION,
        "modified_data": True,
    }
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="neusatz_master.glb")
    ap.add_argument("--cache", default="cache_lgl")
    ap.add_argument(
        "--terrain-step", type=int, default=5,
        help="Terrain-Mesh Raster in Metern. 5 = hochwertiger Web-Master; 2 = sehr schwer; 10 = leichter."
    )
    ap.add_argument(
        "--texture-size", type=int, default=8192,
        choices=(4096, 8192, 16384),
        help="DOP20-Mosaikgröße. 8192 empfohlen; 16384 = Ultra."
    )
    ap.add_argument("--jpeg-quality", type=int, default=94)
    ap.add_argument("--force-download", action="store_true")
    ap.add_argument("--download-only", action="store_true")
    args = ap.parse_args()

    here = Path.cwd()
    cache = (here / args.cache).resolve()
    output = (here / args.output).resolve()
    work = here / ".neusatz_work"
    work.mkdir(exist_ok=True)

    print("Neusatz WebGL Master Builder")
    print("============================")
    print("Gebiet: 6 x 6 km")
    print(f"UTM32: E {MIN_E:.0f}..{MAX_E:.0f}, N {MIN_N:.0f}..{MAX_N:.0f}")
    print(f"Terrain: {args.terrain_step} m, Textur: {args.texture_size}px")
    print(ATTRIBUTION)

    sources = fetch_sources(cache, force=args.force_download)
    if args.download_only:
        print("\nDownload abgeschlossen.")
        return 0

    texture = work / f"neusatz_dop20_{args.texture_size}.jpg"
    if not texture.exists():
        build_dop_texture(sources["dop20"], texture, args.texture_size, args.jpeg_quality)
    else:
        print(f"\n[DOP20] verwende vorhandenes Mosaik: {texture}")

    h, E, N, z_base, z_min, z_max = build_dgm_grid(
        sources["dgm1"], args.terrain_step, work
    )
    terrain = terrain_mesh(h, E, N, z_base, texture)
    buildings = build_building_meshes(sources["lod2"], z_base)

    meta = {
        "title": "Neusatz, Bad Herrenalb – WebGL Master",
        "crs_source": "EPSG:25832",
        "local_origin_easting": ORIGIN_E,
        "local_origin_northing": ORIGIN_N,
        "vertical_base_nhn": z_base,
        "attribution": ATTRIBUTION,
        "modified_data": True,
    }
    export_scene(output, terrain, buildings, meta)
    write_build_report(output.with_suffix(".build.json"), args, z_min, z_max, z_base, output)

    print("\nFERTIG")
    print("======")
    print(f"GLB: {output}")
    print(f"Report: {output.with_suffix('.build.json')}")
    print("\nFür mobile WebGL-Auslieferung anschließend eine zweite, leichtere LOD-Fassung erzeugen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
