# Übernahme und Prüfung – 30. September 2026

Die fünf lokalen ZIP-Teile wurden in numerischer Reihenfolge zusammengesetzt. Ergebnis: 277.953.897 Bytes, 70 vollständige Archiveinträge, alle ZIP-CRC-Prüfungen erfolgreich. SHA256 des zusammengesetzten Quellarchivs: `8ffa862eba653d209a3433bb8b943684bb95d7617d624ff1a80f942241d99327`.

Der vollständige Projektstand enthält LOD0, LOD1, LOD2, Texturen, lokalen Three.js-Viewer, Kameravoreinstellungen, Build-Werkzeuge, Höhenreferenz, ursprüngliche Paketberichte und sämtliche ursprünglichen Screenshots. Die ausführliche ursprüngliche README bleibt byteidentisch als TECHNIK.md erhalten. Die neue README enthält eine echte 3D-Vorschau; CINEMATIC.md beschreibt die sichtbaren Grenzen und den bevorzugten Testshot-Workflow.

Alle 19 GLBs wurden gegen das vollständige Quellpaket geprüft und sind byteidentisch. Der Master hat SHA256 `2410276ddc0e2efd73db3ef0f0eb9f64d4cc4f1fc44bec5e68aeef6cdff3e01b`. Er liegt im Repository in drei unveränderten Binärteilen und wird vom Startskript offline zur Originaldatei zusammengesetzt. Die Rekonstruktion wurde byteweise gegen das Original geprüft. Siehe STORAGE.md.

Lokale Geometrieprüfung: 16 Terrain-Kacheln, 7.968.032 Terrain-Dreiecke und 22.833 Gebäudedreiecke; Kachelpositionen und Normalen stimmen exakt überein; alle Terrain-Texturen sind 2499 × 2499 Pixel groß. Die unabhängige Außenrandprüfung zum Master ergibt maximal 0,000030517578125 m Höhenabweichung. Koordinatenformel, Maskierung, Gebäudefilterung, Überlappung, Tiefenbias und Kantenabdichtung bleiben erhalten. Die Viewer-Datei ist gegenüber dem Quellpaket unverändert.

Aktuelle Browserprüfung: LOD0, LOD1 und LOD2 jeweils mit Übersicht, niedrigem Anflug, Dorf-Nahansicht und Randkamera, zwölf gespeicherte Screenshots; Rückwechsel zu LOD0 erfolgreich. Keine Fehler oder Warnungen im erfassten Browserprotokoll. Details: current_browser_validation.json und screenshots/current_lod*.png. Die Prüfung im Codex-Browser ist kein Hardware-Leistungsbenchmark und keine Vermessungskontrolle einzelner Fassaden.

Der reale Git-Schreibzugriff wurde bereits bestätigt. Die Änderungen werden mit erhaltener Commit-Historie auf main übertragen und anschließend durch einen frischen Clone einschließlich Modellrekonstruktion und SHA256-Abgleich kontrolliert. Die endgültige Commit-ID und das Ergebnis der Remote-Prüfung werden im Abschluss genannt.

Keine LFS-Pointer, keine kostenpflichtigen Leistungen, kein Force-Push, keine generischen Bäume, keine Modelltransformationen und keine vollständige Cinematic-Produktion.
