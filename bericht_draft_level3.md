# Erweiterung: LLMOps mit Azure AI

**Beschreibung der Umsetzung:**
Als dritter Schritt wurde ein LLM-basierter Assistent ("AI Mode Analyst") implementiert, um die gesammelten Daten interaktiv auszuwerten.

1.  **Infrastruktur:** Im Azure AI Foundry wurde ein Projekt erstellt und ein **GPT-4o** Modell deployt.
2.  **Daten-Integration (RAG-Alternative):** Da die Bereitstellung eines dedizierten Azure AI Search Services für eine klassische RAG-Architektur (Retrieval Augmented Generation) aufgrund von Berechtigungseinschränkungen nicht möglich war, wurde ein **In-Context Learning** Ansatz gewählt.
3.  **Prompt Engineering:** Die Aktivitätsdaten wurden als strukturierter Kontext in den System-Prompt des Modells injiziert. Der System-Prompt instruiert das Modell, ausschliesslich auf Basis dieser Daten zu antworten und als Analyst zu agieren.
4.  **Validierung:** Der Chatbot konnte komplexe Fragen (z.B. "Analysiere meine Work-Life-Balance") korrekt beantworten, indem er Muster in den CSV-Daten erkannte.

**Modell:**
[User Query] --> [Azure OpenAI Chat Playground] --> [System Prompt + CSV Daten] --> [GPT-4o] --> [Antwort]

**Screenvideo:**
Siehe Datei: `LLMOps_Azure_Brun.mp4` (Zeigt die Konfiguration des System-Prompts im Azure AI Studio und den Dialog mit dem Bot über die eigenen Daten).