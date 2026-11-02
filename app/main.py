import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException

from app.config import CATEGORIES, PRIORITY_MATRIX, SLA_HOURS
from app.models import TicketIn, TriageResult
from app.triage import triage


app = FastAPI(
    title="IT Service Desk Triage",
    description="Classifies IT tickets, sets the ITIL priority, routes them to a resolver group "
                "and calculates SLA deadlines.",
    version="2.0.0",
)


def check_api_key(x_api_key: str | None = Header(None)):
    """If SERVICE_API_KEY is set, callers must send it in the X-API-Key header."""
    expected = os.getenv("SERVICE_API_KEY")
    if expected and not (x_api_key and secrets.compare_digest(x_api_key, expected)):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@app.get("/")
def root():
    return {"status": "ok", "message": "IT Service Desk Triage is running.",
            "llm_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.get("/taxonomy")
def taxonomy():
    """Categories, resolver groups, priority matrix and SLA targets the service uses."""
    return {
        "categories": {name: {"description": d, "resolver_group": g} for name, (d, g) in CATEGORIES.items()},
        "priority_matrix": {f"{impact}/{urgency}": p for (impact, urgency), p in PRIORITY_MATRIX.items()},
        "sla_hours": {p: {"first_response": r, "resolution": s} for p, (r, s) in SLA_HOURS.items()},
    }


@app.post("/triage", response_model=TriageResult, dependencies=[Depends(check_api_key)])
def triage_ticket(ticket: TicketIn):
    return triage(ticket)
