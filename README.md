# Neusatz – Cinematic-Projekt

Geografisch detaillierte Grundlage für einen vorgerenderten Neusatz-Cinematic mit einer knapp 2 × 2 km großen Hero-Zone und einem 6 × 6 km großen Hintergrund.

**Übernahme läuft: Die vollständigen Modelldaten sind noch nicht hochgeladen.** Das bereitgestellte ZIP ist derzeit unvollständig; es endet mitten in `neusatz_master.glb`. Der GitHub-Push wurde erfolgreich getestet. Dieses erste Commit enthält die vorbereitete Dokumentation und den tatsächlichen lokalen Prüfstand. Es enthält keine LFS-Pointer auf fehlende Modelle.

| Stufe | Vorgesehener Paketinhalt |
| --- | --- |
| LOD0 | 16 Hero-Terrain-Kacheln mit 1-m-Raster, DOP20 mit 20 cm/Pixel, vollständige LoD2-Gebäude |
| LOD1 | Bytegenau erhaltener 6 × 6 km Background-Master |
| LOD2 | Leichtere Fernansicht |

Zusätzlich vorgesehen: lokaler Three.js-Testviewer, Kameravoreinstellungen, Build-Werkzeuge, Prüfberichte und echte WebGL-Vorschaubilder. Die vollständigen Roharchive gehören nicht zum Paket.

## Start nach vollständiger Übernahme

Nach vollständigem Download aller Projektdateien und gegebenenfalls LFS-Objekte unter Windows `Start_Viewer.bat` öffnen oder im Projektordner `python start_viewer.py` ausführen (Python 3 erforderlich). Dann <http://localhost:8080> öffnen. Diese Startdateien werden mit der noch fehlenden ZIP-Hälfte übernommen; der aktuelle Dokumentationsstand ist noch nicht startbar.

## Qualität und Prüfung

Die bereits vollständig extrahierten LOD0-Dateien wurden unverändert geprüft: 16 Terrain-Kacheln mit insgesamt 7.968.032 Dreiecken, Gebäude mit 22.833 Dreiecken, exakt übereinstimmende Kachelpositionen und Normalen, 16 Texturen mit jeweils 2499 × 2499 Pixeln. [Lokaler Prüfbericht](local_validation.json). Master-Prüfsumme, Background-Übergang, aktuelle Kamera-/LOD-Durchläufe und echte Vorschaubilder bleiben bis zum vollständigen ZIP offen.

Die geografische Genauigkeit ersetzt keinen Fotorealismus: Vegetation, Fassadenoberflächen, Licht und Kamera müssen für den sichtbaren Bereich ausgearbeitet werden. Der bevorzugte nächste Qualitätsschritt ist ein vollständig ausgearbeiteter Blender-Testshot von 5–10 Sekunden. [Cinematic-Prioritäten](CINEMATIC.md).

Die ausführliche ursprüngliche README wurde bytegenau als [TECHNIK.md](TECHNIK.md) erhalten. Sie beschreibt den vollständigen vorgesehenen Paketstand und seine bisherigen Prüfungen, nicht einen bereits abgeschlossenen Upload. Modelle werden weder neu zentriert noch gedreht, skaliert oder vereinfacht. Die vorhandene Background-Maskierung und Kantenabdichtung müssen erhalten bleiben.

## Datenquelle

Datenquelle: LGL, www.lgl-bw.de, dl-de/by-2-0. Bearbeitete Geodaten: Ausschnitt, lokale Koordinaten, Triangulierung, DOP-Resampling/JPEG und Randangleichung. [LGL-Datenhinweis](build_tools/LGL_DATA_LICENSE.txt).
