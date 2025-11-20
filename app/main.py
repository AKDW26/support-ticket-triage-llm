import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.orchestrator import process_ticket, load_kb
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Ticket Triage Agent (LLM)")

@app.on_event("startup")
async def startup_event():
    kb_path = os.path.join(os.path.dirname(__file__), '..', 'kb', 'known_issues.json')
    if os.path.exists(kb_path):
        load_kb(kb_path)

class TriageRequest(BaseModel):
    description: str

@app.post("/triage")
async def triage(req: TriageRequest):
    if not req.description or not req.description.strip():
        raise HTTPException(status_code=400, detail="description is required")
    try:
        result = process_ticket(req.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result
