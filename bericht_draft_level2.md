# Kapitel 3: Umsetzung AzureML

**Beschreibung der Umsetzung:**
Für die intelligente Klassifikation der Nutzeraktivitäten in Kategorien wie "Work" oder "Relax" wurde **Azure Machine Learning (AutoML)** eingesetzt. Ziel war es, den manuellen Aufwand der Modellentwicklung durch Automatisierung zu ersetzen.

1.  **Datenbasis:** Ein Datensatz (`activity-mode-data`) mit Features wie `app_name`, `mouse_activity`, `hour` und `day_of_week` wurde erstellt, bereinigt und im Azure ML Workspace registriert.
2.  **Training:** Ein Automated ML Experiment testete parallel verschiedene Klassifikations-Algorithmen. Das System wählte automatisch ein **ExtremeRandomTrees**-Modell als Sieger aus (basierend auf der Metrik `AUC weighted`).
3.  **Deployment:** Das trainierte Modell wurde als skalierbarer **Real-time Endpoint** auf einer `Standard_DS2_v2` Instanz deployt.
4.  **Validierung:** Der Endpoint wurde über ein lokales Jupyter Notebook erfolgreich validiert. Dabei wurden JSON-Daten an die REST-Schnittstelle gesendet, woraufhin der Dienst die korrekte Klassifikation in Echtzeit zurücklieferte.

**Modell (Zusammenhang der Elemente):**
[Lokale Metadaten] --JSON--> [Azure ML Managed Endpoint] --> [AutoML Modell] --> [Response: "Work"/"Relax"]

**Screenvideo:**
Siehe Datei: `MLOps_Azure_Brun.mp4` (Das Video demonstriert den aktiven "Healthy"-Status des Endpoints im Azure Portal und die erfolgreiche Live-Abfrage über das lokale Notebook).