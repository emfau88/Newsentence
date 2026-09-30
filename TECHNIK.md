# Neusatz – Hero-Zone und LOD-Testviewer

## Start

ZIP vollständig entpacken. Unter Windows `Start_Viewer.bat` öffnen (Python 3 erforderlich), andernfalls im Paketordner `python start_viewer.py`. Im Browser http://localhost:8080 öffnen. Nicht per Doppelklick auf index.html starten: GLB-Laden benötigt HTTP. Three.js liegt lokal bei; der Viewer braucht kein CDN und keine externen Assets.

Drehen: linke Maustaste / ein Finger. Verschieben: rechte Maustaste / zwei Finger. Zoom: Mausrad / Pinch. Die vier Kameratasten erlauben direkte Kontrolle von Übersicht, niedrigem Anflug, Dorf und Übergangsrand. Detailstufen werden manuell umgeschaltet. Kamera bleibt beim Wechsel identisch. Drahtgitter betrifft nur das Gelände.

## Gelieferte Daten

| Ebene | Gebiet / Auflösung | Dateien |
|---|---|---|
| LOD0 Hero | 1.996 × 1.996 m, DGM1 1-m-Raster, DOP20 0,20 m/Pixel | 16 Terrain-GLBs à 499 × 499 m; separat buildings.glb |
| LOD1 Background | vorhandener 6 × 6 km Master, 5-m-Raster, 8192² Luftbild | lod1/neusatz_master.glb, bytegenau unverändert |
| LOD2 Fernansicht | vorhandene leichtere 6 × 6 km Fassung, 10-m-Raster, 4096² Luftbild | lod2/neusatz_web.glb |

LOD0 umfasst 7.968.032 Terrain-Dreiecke und 816 vollständige Gebäude mit 22.833 Dreiecken. Alle 9.601 ausgewählten Gebäudepolygone wurden trianguliert; die Auswahl erfolgt auf ganzen Gebäudeobjekten einschließlich BuildingParts. Gebäude, die den Ausschnitt schneiden, bleiben vollständig erhalten. Dächer, Wände und Grundflächen sind separat gruppiert. Geometrie und amtliche Höhen werden nicht dekorativ verändert.

16 Texturen von 2499 × 2499 Pixeln, inklusive je zwei Randpixeln gegen Filterartefakte. Die eigentliche Fläche einer Kachel entspricht 2495 × 2495 DOP-Pixeln. Keine riesige Sammeltextur. JPEG Qualität 96, ohne Farbunterabtastung; Original-TIFs werden beim Build kleinräumig mit 20-cm-Zielraster gelesen. Die ursprüngliche Pixelgröße bleibt erhalten; JPEG und die notwendige Verschiebung des Texturrasters sind keine verlustfreie Übernahme der Originalpixel.

## Georeferenzierung

ETRS89 / UTM32N, EPSG:25832. Hero-Ausdehnung: E 461002,5 bis 462998,5; N 5406202,5 bis 5408198,5. Mittelpunkt E 462000,5 / N 5407200,5; etwa 25 m östlich / 2 m nördlich des Mittelpunktes im ursprünglichen Manifest.

Alle GLBs verwenden direkt dieselbe Transformationskonvention wie der Master:

- X = E − 462000
- Y = Höhe NHN − 290
- Z = 5407000 − N

Keine zusätzliche Skalierung, Rotation oder Verschiebung nötig. In Blender glTF regulär importieren; keine Einzeldatei danach manuell neu zentrieren. Der Importer übernimmt Y-up nach Blender-Z-up.

## Übergänge: wichtig für die spätere Szene

Die inneren 1.796 × 1.796 m behalten die DGM1-Höhen und die DOP20-Auflösung vollständig. Im äußeren 100-m-Ring werden die Höhen sanft auf die **wirklichen Dreiecksflächen** des bestehenden Masters geführt. Stärkste Anpassung im Ring: 1,532 m. Die Luftbildtextur wird im gleichen Ring sanft an die bestehende Master-Textur angeglichen. Die effektive Bildschärfe nimmt daher im Randring bewusst ab.

Nach unabhängiger Prüfung beträgt die größte Höhenabweichung am gesamten Außenrand etwa 0,000031 m (Float32-Rundung). Zwischen Hero-Kacheln stimmen exportierte Positionen und Normalen exakt überein.

**Hero und Background dürfen nicht einfach vollflächig übereinander gerendert werden.** Im Viewer wird der Background unter der Hero-Zone zur Laufzeit ausgespart und die doppelten Gebäudeflächen werden ausgeblendet. Die Dateien selbst bleiben unverändert. Eine 5-cm-Überlappung, minimaler Tiefenbias und schmale, 0,5 m nach unten reichende Kachelschürzen verhindern subpixelgroße Rasterlücken. Die Schürzen werden nur im Viewer zur Laufzeit erzeugt; die amtliche Oberflächengeometrie in den GLBs bleibt unverändert. Für eigene WebGL-Viewer dieselbe Kantenabdichtung übernehmen. In einer Blender/Cinematic-Szene muss ebenfalls der Background im Hero-Bereich ausgeschnitten bzw. maskiert werden; diese Compositing-Regel ist Teil der LOD-Struktur. Das Original wird dabei als unveränderte Quelldatei behalten.

## Prüfung und Screenshots

`screenshots/lod0_overview_3d.png`, `lod0_approach_3d.png`, `lod0_village_3d.png` und `lod0_seam_3d.png` sind echte WebGL-Renderings. Entsprechende Dateien für LOD1 und LOD2 erlauben Vergleich mit identischer Kamera. Varianten ohne `_3d` zeigen die Viewer-Oberfläche. `mobile_village.png` prüft einen 390 × 844 Browser-Viewport, nicht die Leistung eines echten Smartphones.

`validation.json` dokumentiert Rohdatenabdeckung, Prüfsummen, Kachelränder, Höhenübergang und Gebäudeprüfung. `browser_validation.json` dokumentiert die tatsächlichen Kamera-/LOD-Durchläufe und Browserfehler. Gerendert mit Chrome und Software-WebGL (SwiftShader); kein Hardware-Performance-Benchmark.

## Grenzen der amtlichen Grundlage

DGM1 beschreibt den Boden, nicht die Baumkronen. Wälder im Luftbild bleiben deshalb flache Bildstrukturen; es wurden keine 3D-Bäume oder Dekoration ergänzt. LoD2 enthält Dach- und Baukörpergeometrie, aber keine detaillierten Fenster oder fotorealistischen Fassaden. Materialien sind einfache neutrale Prüfmaterialien. Diese Basis ist geographisch detaillierter, aber alleine noch kein fotorealistischer fertiger Cinematic.

Quelldatenstand laut Archivnamen: DGM1 2020, DOP20 2024, LoD2-Ausgabe 2026. Unterschiedliche Aufnahmezeiten, Orthophoto-Parallaxe und ebene Gebäudegrundflächen können lokal Abweichungen gegenüber dem Gelände/Luftbild verursachen. Die mediane absolute Abweichung der LoD2-Grundflächenpunkte zum DGM1 beträgt 0,37 m; 95 % liegen unter 2,32 m. Amtliche Gebäudekoordinaten wurden nicht künstlich auf das Terrain gezogen.

LOD0 ist ein Qualitäts-Master und lädt alle 16 Kacheln für die Prüfung. Für einen späteren mobilen Produktionsviewer sind Sichtbarkeitsstreaming und komprimierte GPU-Texturen sinnvoll; die Kacheln ermöglichen das. Der Testviewer rendert bei Kamerabewegung und Bedienung, statt permanent Bilder zu berechnen.

## Reproduzierbarer Build

Die vollständigen Roharchive sind nicht im ZIP enthalten; die exakten Original-URLs stehen in build_tools/download.py, die SHA256-Prüfsummen in validation.json. Zum Neuaufbau (vorher Kopie des Pakets erstellen):

```
python -m pip install -r build_tools/requirements.txt
python build_tools/download.py
python build_tools/build_hero.py
python build_tools/validate_hero.py
python build_tools/verify_perimeter.py
```

Der Builder verwendet die beiliegende LOD1-Datei als unveränderte Referenz und erzeugt LOD0 neu. Download benötigt ca. 480 MB, mit entpackten TIFs und Build mindestens 2 GB freien Speicher. Für neue Browser-Screenshots: Viewer starten, `python -m playwright install chromium`, dann `python build_tools/capture.py`. Ein optionaler eigener Chrome-Pfad kann über `CHROME_EXECUTABLE` angegeben werden.

Datenquelle: LGL, www.lgl-bw.de, dl-de/by-2-0. Bearbeitete Daten: Ausschnitt, lokale Koordinaten, Triangulierung, DOP-Resampling/JPEG, Randangleichung. Siehe build_tools/LGL_DATA_LICENSE.txt. Three.js: MIT, Lizenz unter vendor/THREE_LICENSE.txt.
