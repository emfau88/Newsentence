# Speicherung der Modelle

Alle Modelle sind vollständig im Repository enthalten. Die 18 GLBs von LOD0 und LOD2 liegen direkt vor. Der unveränderte LOD1-Master ist 110.712.508 Bytes groß und überschreitet GitHubs reguläres Dateilimit. Seine Bytes liegen deshalb in drei Binärteilen von höchstens 40 MiB unter `lod1/`; `master_parts.json` enthält Größe und SHA256 jeder Datei.

`python prepare_models.py` prüft die Teile, setzt sie in einer temporären Datei zusammen und überprüft den vollständigen Master, bevor die Datei unter `lod1/neusatz_master.glb` bereitgestellt wird. Eine vorhandene abweichende Masterdatei wird nicht überschrieben. Das Startskript führt die Vorbereitung automatisch durch. Dies funktioniert offline nach einem vollständigen Clone oder Download des Repository-ZIPs.

Master-SHA256:

```
2410276ddc0e2efd73db3ef0f0eb9f64d4cc4f1fc44bec5e68aeef6cdff3e01b
```

Die rekonstruierte Datei wurde byteweise mit dem Original verglichen. Keine Geometrie wurde verändert, neu zentriert, gedreht, skaliert oder vereinfacht. Die erzeugte Masterdatei ist lokal von Git ausgeschlossen; ihre vollständigen Teile sind versioniert. Git LFS wird nicht benötigt, und es gibt keine LFS-Pointer.

LFS wurde als bevorzugte Ablage geprüft. Die Abfrage der Kontonutzung scheiterte mit HTTP 404 und dem Hinweis auf einen fehlenden `user`-Scope. Eine ausreichende kostenlose Restkapazität war damit nicht nachweisbar. Da GitHub LFS abhängig vom Kontingent und Budget abrechnet, wurde die Ablage in normalen Git-Dateien gewählt. Es wurden weder Berechtigungen erweitert noch kostenpflichtige Leistungen aktiviert. [GitHub-Dokumentation zur LFS-Abrechnung](https://docs.github.com/en/billing/concepts/product-billing/git-lfs).
