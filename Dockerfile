# 1. Schlankes Python Image
FROM python:3.11-slim

# 2. Arbeitsverzeichnis
WORKDIR /app

# 3. Requirements installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Code kopieren
COPY Mode_Recorder/ .

# 5. Starten (angepasst auf den neuen Code)
CMD ["uvicorn", "mode_recorder:app", "--host", "0.0.0.0", "--port", "10000"]