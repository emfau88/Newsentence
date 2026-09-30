# Übertragungsstand – 30. September 2026

Der echte Git-Push ist erfolgreich. Die deutsche Dokumentation wurde auf `main` übertragen und durch einen frischen Clone geprüft. Der erste Dokumentationscommit ist `b6bb6c6c9bf1ec506034424d41e9320f12945955`. `main` ist der Standardbranch; der temporäre Schreibtestbranch wurde wieder entfernt.

Die GitHub-Anmeldung für emfau88 funktioniert außerhalb der Sandbox. Der innerhalb der Sandbox beobachtete HTTP-401-Fehler beschreibt daher nicht den dort verfügbaren Windows-Zugriff. Es ist keine neue GitHub-Freigabe nötig, um diesen bereits bestätigten Git-Push zu wiederholen.

## Noch kein vollständiges Projekt

Die bereitgestellte Datei `C:\Users\madde\Downloads\Neusatz_Hero_LOD_Paket.zip` ist weiterhin unvollständig: 159.646.814 Bytes, unverändert seit 10:12 Uhr, kein ZIP-Abschlussverzeichnis. Python meldet `BadZipFile: File is not a zip file`. Der Eintrag `lod1/neusatz_master.glb` endet vorzeitig; laut lokalem ZIP-Header sollte der vollständige Master 110.712.508 Bytes haben.

Nur vollständige lokale ZIP-Einträge wurden CRC-geprüft extrahiert. Alle 16 LOD0-Kacheln und die Gebäudedatei wurden unabhängig geprüft und nicht verändert. Kachelpositionen und Normalen stimmen exakt überein; Dreieckzahlen, Texturgrößen und lokale Grenzen entsprechen den Paketangaben. Siehe `local_validation.json`.

Die vollständigen Master-/LOD2-Dateien, manifest.json, validation.json, Höhenreferenz, Screenshots, Startskript und Vendor-Dateien fehlen noch aus dem lesbaren ZIP-Teil. Die Viewer-Oberfläche wurde lokal geöffnet; die drei Vendor-Module lieferten HTTP 404. Kein aktueller erfolgreicher 3D-/LOD-Durchlauf, keine aktuelle Screenshot-Bewertung und keine Master-Prüfsumme werden behauptet.

## Nötiger nächster Schritt

Den ursprünglichen ZIP-Download vollständig abschließen oder ein vollständiges Ersatz-ZIP bereitstellen. Danach werden das ganze Archiv und die Paketberichte geprüft, alle Modelle einschließlich Master bytegenau übernommen, die LFS-Kapazität geprüft, echte Vorschaubilder eingebunden, Kamera-/LOD- und Übergangsprüfungen durchgeführt und der vollständige Projektstand auf `main` übertragen und frisch heruntergeladen kontrolliert.

Es wurden bislang nur Dokumentation, LGL-Datenhinweis und Prüfbericht hochgeladen. Keine fehlenden Modell-Pointer, keine kostenpflichtigen Leistungen, kein Force-Push, keine generischen Bäume und keine Modelltransformationen. Die LFS-Konfiguration und der vollständige Projektupload bleiben bis zum fertigen ZIP offen.
