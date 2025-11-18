# 1. Starte mit einem offiziellen Python-Image
FROM python:3.11-slim

# 2. Installiere die System-Abhängigkeit, die PyAudio braucht
RUN apt-get update && apt-get install -y portaudio19-dev

# 3. Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# 4. Kopiere die requirements.txt und installiere die Python-Pakete
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5. Kopiere den Rest deines Codes
COPY . .

# *** NEUE ZEILE: Gehe in den Code-Ordner ***
WORKDIR /app/"Mode_Recorder"

# 6. Definiere den Befehl, der beim Start ausgeführt wird
CMD ["uvicorn", "mode_recorder:app", "--host", "0.0.0.0", "--port", "10000"]