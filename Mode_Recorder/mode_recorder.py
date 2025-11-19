from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI()

# Das Datenmodell für deine Status-Updates
class ActivityLog(BaseModel):
    app_name: str
    window_title: Optional[str] = None
    mouse_activity: Optional[int] = 0 # Skala 1-10
    timestamp: Optional[str] = None

# In-Memory Speicher (für Level 1 reicht das völlig)
logs = []

@app.get("/")
def read_root():
    return {"status": "AI Mode Assistant is running", "logs_count": len(logs)}

@app.post("/log_activity")
def log_activity(log: ActivityLog):
    # Zeitstempel setzen, falls nicht gesendet
    if not log.timestamp:
        log.timestamp = datetime.now().isoformat()

    logs.append(log)

    # Hier würde später der Aufruf an Azure ML (Level 2) passieren
    # prediction = azure_ml_service.predict(log)

    return {"message": "Activity logged", "current_mode": "Unknown (ML Model pending)"}

@app.get("/get_logs")
def get_logs():
    return logs