# Kapitel 1: Umsetzung DevOps lokal

**Beschreibung der Umsetzung:**
Für die lokale Umsetzung wurde der "AI Mode Assistant" entwickelt – ein Microservice zur Erfassung von Arbeitsplatz-Metadaten. Ursprünglich als reiner Audio-Recorder geplant, wurde die Architektur zugunsten von Stabilität und Skalierbarkeit auf einen metadatenbasierten Ansatz umgestellt.

Die Applikation basiert auf **FastAPI**. Sie stellt Endpunkte bereit, um Aktivitätsdaten (z.B. genutzte Applikation, Mausaktivität) entgegenzunehmen (`/log_activity`) und zu speichern. Dies bildet die Datengrundlage für die spätere KI-Klassifikation.

Der Server wird lokal mittels **Uvicorn** betrieben. Die Abhängigkeiten (`fastapi`, `pydantic`) sind strikt in einer `requirements.txt` definiert.

**Modell (Zusammenhang der Elemente):**
[Lokaler Client (Script)] --JSON--> [API Endpunkt /log_activity] --> [FastAPI Server] --> [In-Memory Log Storage]

**Screenvideo:**
Siehe Datei: `DevOps_Lokal_Brun.mp4` (Zeigt lokalen Start des Servers und das Senden eines Test-Logs via Swagger UI).

---

# Kapitel 2: Umsetzung DevOps cloud

**Beschreibung der Umsetzung:**
Das Cloud-Deployment erfolgte auf **Render.com**, direkt gekoppelt an das GitHub-Repository. Dies realisiert eine CI/CD-Pipeline: Jeder Push auf den Main-Branch triggert automatisch Build und Deployment.

**Herausforderungen & Lösungen (Containerisierung & Pivot):**
Ein initialer Versuch, Audio-Verarbeitung direkt in der Cloud durchzuführen, zeigte die Grenzen der Free-Tier-Infrastruktur auf (fehlende System-Bibliotheken, Timeouts). Dies führte zu einer bewussten **Architekturentscheidung (Pivot)**:

1.  **Containerisierung:** Einsatz eines **Dockerfiles**, um eine schlanke, isolierte Python-Umgebung ohne unnötigen Ballast zu schaffen.
2.  **Optimierung:** Entfernung schwerer Audio-Bibliotheken zugunsten einer reinen JSON-Schnittstelle. Dies reduzierte die Image-Grösse und die Build-Zeit drastisch.

Der Service ist nun als hochverfügbare API öffentlich erreichbar und bereit, als "Gehirn" für die kommenden MLOps-Schritte (Azure ML Anbindung) zu fungieren.

**Screenvideo:**
Siehe Datei: `DevOps_Cloud_Brun.mp4` (Zeigt Render Dashboard, den erfolgreichen "Live"-Status und einen API-Call über die öffentliche URL).