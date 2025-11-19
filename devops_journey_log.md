# DevOps Journey Log: Multi-Audio-Transformer
**Status:** Level 1 (DevOps Local & Cloud)
**Datum:** 18.11.2025

## 1. Lokale Entwicklung & Initialisierung
*   **Ziel:** Python-Skript (`mode_recorder.py`) in eine API umwandeln.
*   **Aktion:** Integration von `FastAPI` und `Uvicorn`.
*   **Problem:** Code lief lokal, war aber nicht versioniert.
*   **Lösung:** Git Repository initialisiert (`git init`), `.gitignore` für `.venv` erstellt, erster Commit.

## 2. Cloud Deployment Versuch 1 (Native Python Environment)
*   **Plattform:** Render.com (Web Service).
*   **Ansatz:** Standard Python Environment von Render nutzen via `requirements.txt`.
*   **Fehler:** `Failed building wheel for PyAudio`.
*   **Ursache:** `PyAudio` benötigt Systembibliotheken (`PortAudio`), die im Standard-Linux-Image von Render fehlen.
*   **Learning:** Python-Pakete, die C-Bindings haben, brauchen oft OS-Level Abhängigkeiten.

## 3. Umstellung auf Docker (Containerisierung)
*   **Strategie:** Wechsel von "Native Python" auf "Docker Runtime", um volle Kontrolle über das OS zu haben.
*   **Aktion:** Erstellung `Dockerfile`.
*   **Fehler 1 (Build):** `error: command 'gcc' failed`.
    *   *Ursache:* Das `python:3.11-slim` Image ist so minimal, dass kein Compiler (`gcc`) installiert ist. `PyAudio` muss aber kompiliert werden.
    *   *Lösung:* Installation von `build-essential` im Dockerfile (`RUN apt-get install ...`).
*   **Fehler 2 (Pathing):** `Exited with status 128`.
    *   *Ursache:* Der Ordnername "Mode Recorder" enthielt ein Leerzeichen. Docker und Uvicorn hatten Probleme, den Pfad im `CMD` korrekt aufzulösen.
    *   *Lösung:* Refactoring der Ordnerstruktur. Umbenennung zu `Mode_Recorder` und Anpassung des `COPY` Befehls im Dockerfile, um den Code direkt ins Root (`/app`) des Containers zu kopieren.
*   **Fehler 3 (Runtime GUI):** `ImportError: libtk8.6.so`.
    *   *Ursache:* Der Code importierte `tkinter` (GUI). Der Cloud-Server ist "headless" (hat keinen Bildschirm/GUI-Framework).
    *   *Lösung:* Code-Anpassung (`mode_recorder.py`), um `tkinter` nur bedingt zu importieren (Try/Except Block) oder für das Deployment auszukommentieren.

## 4. Finale Runtime Hürden (Audio Services)
*   **Fehler:** `OSError: cannot load library 'libpulse.so'` und Warnung zu `ffmpeg`.
*   **Ursache:** Die Audio-Processing-Bibliotheken (`soundcard`, `pydub`) benötigen laufende Audio-Daemons (PulseAudio) und Codecs (FFmpeg), die im Slim-Image fehlten.
*   **Finale Lösung:** Dockerfile erweitert um `libpulse-dev` und `ffmpeg`.

## 5. Strategiewechsel & Refactoring (Pivot)
*   **Problem:** Die Verarbeitung von Audio-Streams (PyAudio/FFmpeg) auf der Free-Tier Cloud-Infrastruktur erwies sich als instabil (Timeouts) und zu ressourcenintensiv für den Scope.
*   **Entscheidung:** Architekturwechsel von "Heavy Processing" zu "Metadata Controller". Die Cloud-App (Render) dient nun als zentrale Steuerungs-API, die Metadaten empfängt, nicht mehr Rohdaten.
*   **Aktion:**
    *   Entfernung von Systemabhängigkeiten (`libpulse`, `ffmpeg`) aus Dockerfile -> schnellerer Build, kleineres Image.
    *   Anpassung der API-Logik auf Empfang von JSON-Statusdaten statt Audio-Blobs.
*   **Ergebnis:** Stabiles, schnelles Deployment. Perfekte Basis für die Anbindung von Azure ML (Klassifikation der Metadaten).

## 6. MLOps mit Azure ML (Level 2)
*   **Ziel:** Trainieren und Deployen eines eigenen ML-Modells zur Klassifikation der "Modes".
*   **Vorbereitung:**
    *   Erstellung eines Azure ML Workspaces.
    *   Herausforderung: Fehlende Berechtigungen ("You do not have permissions").
    *   Lösung: Aktivierung der Rollen (Reader/Contributor) via **PIM (Privileged Identity Management)** für 8 Stunden.
*   **Daten:** Erstellung eines synthetischen Datasets `activity_data.csv` (Features: App, Maus, Zeit -> Target: Mode).
    *   Problem: AutoML verweigerte den Start wegen zu weniger Daten (<50 Zeilen).
    *   Lösung: Data Augmentation (Vervielfachung der Zeilen) auf >50 Einträge.
*   **Training:** Start eines Automated ML Jobs (`ai-mode-exp`) auf einem `Standard_DS11_v2` Compute Cluster.
    *   Ergebnis: Mehrere Modelle mit 100% Accuracy (aufgrund der simplen synthetischen Daten). Bestes Modell: `ExtremeRandomTrees`.
*   **Deployment:**
    *   Bereitstellung des besten Modells als **Real-time Endpoint** (`Managed Online Endpoint`).
    *   Konfiguration: `Standard_DS2_v2`, 1 Instanz (zur Kostenoptimierung).
*   **Test:**
    *   Erfolgreicher Aufruf des Endpoints via Jupyter Notebook mit API-Key und REST-URL.
    *   Klassifikation von Test-Szenarien (z.B. "Netflix am Abend" -> "Relax") war korrekt.
*   **Cleanup:** Sofortige Löschung des Endpoints nach dem Videobeweis, um unnötige Kosten zu vermeiden.

## 7. LLMOps mit Azure AI Foundry (Level 3)
*   **Ziel:** Integration eines Large Language Models (LLM), um die gesammelten Aktivitätsdaten natürlichsprachlich abzufragen ("Chat with your Data").
*   **Plattform:** Azure AI Foundry (ehemals AI Studio).
*   **Vorbereitung:**
    *   Erstellung eines AI Hubs und Projekts (`Multi-Audio-Transformer`).
    *   Berechtigungen: Erneute Hürde mit RBAC. Der Zugriff auf den neuen "Agent Builder" war gesperrt (`PermissionDenied` für `agents/write`).
    *   Lösung: Wechsel auf den klassischen **Chat Playground**, der weniger Rechte erfordert.
*   **Modell-Deployment:**
    *   Versuch 1: Deployment von `gpt-4o`. Erfolgreich deployed, aber Zugriff im Chat teilweise eingeschränkt.
    *   Versuch 2: Fallback auf `gpt-35-turbo` (wurde nicht benötigt, da Workaround funktionierte).
*   **RAG (Retrieval Augmented Generation):**
    *   Versuch: Nutzung der Funktion "Add your data" zum Hochladen der CSV.
    *   Fehler: `No Azure AI Search resources found`. Das Erstellen eines Search Services ist im Student-Subscription-Modell oft blockiert oder kostenpflichtig.
    *   **Lösung (In-Context Learning):** Anwendung von **Prompt Engineering**. Die CSV-Daten wurden direkt in den System-Prompt ("Context") des Modells integriert. Dies simuliert RAG für kleinere Datenmengen effektiv.
*   **Ergebnis:** Ein funktionierender Chatbot, der Fragen wie "Wann arbeite ich am meisten?" basierend auf den eigenen Log-Daten korrekt beantwortet.