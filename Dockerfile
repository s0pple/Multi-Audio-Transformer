# 1. Starte mit einem offiziellen Python-Image
FROM python:3.11-slim

# 2. Installiere ALLE notwendigen System-Tools (PortAudio UND den Compiler)
#    (Wir installieren beides in einem Schritt, um das Image effizienter zu halten)
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    build-essential

# 3. Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# 4. Kopiere die requirements.txt und installiere die Python-Pakete
COPY requirements.txt .
RUN pip install -r requirements.txt

# *** KRITISCHE ÄNDERUNG: Kopiere nur den INHALT des Code-Ordners
# *** (Der Ordner Mode_Recorder liegt im Root des Repos)
COPY Mode_Recorder/ .

# 6. Definiere den Befehl, der beim Start ausgeführt wird
#    Da mode_recorder.py jetzt direkt in /app liegt, entfällt der Ordnerpfad.
CMD ["uvicorn", "mode_recorder:app", "--host", "0.0.0.0", "--port", "10000"]