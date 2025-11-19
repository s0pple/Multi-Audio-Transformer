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

## 5. Ergebnis
Der Service läuft nun in einem maßgeschneiderten Docker-Container, der alle System-Abhängigkeiten kapselt. Die API ist via HTTPS erreichbar.