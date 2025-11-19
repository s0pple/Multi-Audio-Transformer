# Kapitel 1: Umsetzung DevOps lokal

**Beschreibung der Umsetzung:**
Für die lokale Umsetzung wurde die bestehende Python-Applikation "Multi-Audio-Transformer" (ursprünglich ein lokales Skript zur Audio-Aufnahme) um eine REST-Schnittstelle erweitert. Hierfür wurde das Framework **FastAPI** gewählt, da es eine hohe Performance bietet und automatisch eine API-Dokumentation generiert.

Der Server wird lokal mittels **Uvicorn** (einem ASGI-Server) betrieben. Die Abhängigkeiten wurden in einer `requirements.txt` festgehalten, um die Reproduzierbarkeit der Umgebung sicherzustellen. Die Versionierung des Quellcodes erfolgt über **Git**.

**Modell (Zusammenhang der Elemente):**
[Client/Browser] <--> [Localhost:8000] <--> [Uvicorn Server] <--> [FastAPI App] <--> [Python Logik (Mode Recorder)]

**Screenvideo:**
Siehe Datei: `DevOps_Lokal_Brun.mp4` (Zeigt Start des Servers und Aufruf via Swagger UI).

---

# Kapitel 2: Umsetzung DevOps cloud

**Beschreibung der Umsetzung:**
Für das Cloud-Deployment wurde die Plattform **Render.com** gewählt, die direkt mit dem **GitHub-Repository** verbunden ist. Dies ermöglichte den Aufbau einer CI/CD-Pipeline: Bei jedem `git push` auf den Main-Branch wird automatisch ein neuer Build angestossen.

**Herausforderungen & Lösungen (Containerisierung):**
Da die Applikation spezifische Systemabhängigkeiten für die Audioverarbeitung (`PortAudio`, `FFmpeg`) benötigt, reichte die Standard-Python-Umgebung von Render nicht aus.

Die Lösung war die Erstellung eines **Dockerfiles**. Dies ermöglichte:
1.  Die Installation von Linux-Systempaketen (`build-essential`, `portaudio19-dev`, `libpulse-dev`, `ffmpeg`).
2.  Die saubere Installation der Python-Dependencies (`requirements.txt`).
3.  Das Kapseln der Applikation in einer isolierten Umgebung.

Der Service ist nun öffentlich über eine HTTPS-URL erreichbar. Die grafische Oberfläche (`tkinter`) wurde für den Serverbetrieb deaktiviert ("Headless Mode"), da Cloud-Container keine Bildschirmausgabe unterstützen.

**Screenvideo:**
Siehe Datei: `DevOps_Cloud_Brun.mp4` (Zeigt Render Dashboard, automatischen Deploy nach Push und API-Aufruf über die öffentliche URL).