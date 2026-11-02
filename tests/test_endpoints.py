"""Tests for the triage rules, the LLM call handling, the API and the metrics. No API key or network needed."""
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import baseline
from app.evaluation import score
from app.llm import TriageError, call_llm
from app.main import app
from app.models import LLMTriage, TicketIn
from app.triage import priority_for, triage

CREATED = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)


def llm_returning(**overrides):
    fields = {"category": "network_connectivity", "impact": "high", "urgency": "high", "affected_service": "LAN",
              "summary": "Building B has no network.", "language": "en", "confidence": 0.9,
              "rationale": "80 users cannot work.", "draft_reply": "We are on it."}
    return lambda subject, description: LLMTriage(**{**fields, **overrides})


def ticket(subject="No network in building B", description="Nobody in building B has network."):
    return TicketIn(subject=subject, description=description, created_at=CREATED)


# ─── Triage rules ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("impact, urgency, expected", [
    ("high", "high", "P1"), ("high", "medium", "P2"), ("medium", "high", "P2"),
    ("medium", "medium", "P3"), ("low", "high", "P3"), ("low", "low", "P5"),
])
def test_itil_priority_matrix(impact, urgency, expected):
    assert priority_for(impact, urgency) == expected


def test_priority_routing_and_sla_come_from_the_rules():
    result = triage(ticket(), llm=llm_returning())
    assert (result.priority, result.resolver_group) == ("P1", "Network Operations")
    assert result.first_response_due == datetime(2026, 11, 2, 9, 15, tzinfo=timezone.utc)
    assert result.resolution_due == datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc)
    assert result.review_reasons == ["P1: incident manager to confirm major incident"]


def test_confident_non_major_ticket_is_routed_without_review():
    result = triage(ticket(), llm=llm_returning(impact="low", urgency="high"))
    assert result.priority == "P3" and not result.needs_human_review and result.source == "llm"


def test_low_confidence_goes_to_review():
    result = triage(ticket(), llm=llm_returning(confidence=0.4))
    assert result.needs_human_review and "Low confidence" in result.review_reasons[0]


def test_keyword_safety_net_flags_a_possible_under_call():
    # The LLM files a ransomware ticket as a minor hardware issue; the keywords disagree
    t = ticket("Strange files", "All files on the share are encrypted, ransomware note, production stopped, urgent")
    result = triage(t, llm=llm_returning(category="hardware_endpoint", impact="low", urgency="low"))
    assert result.priority == "P5" and result.needs_human_review
    assert "Keywords suggest a security incident" in result.review_reasons
    assert "Keywords suggest a higher priority" in result.review_reasons


def test_keyword_fallback_when_llm_fails():
    def broken(subject, description):
        raise ConnectionError("Groq unreachable")
    result = triage(ticket("VPN down", "VPN not working at all for everyone in sales, urgent"), llm=broken)
    assert result.source == "keyword_fallback" and result.needs_human_review
    assert (result.category, result.priority) == ("network_connectivity", "P1")


# ─── LLM call ──────────────────────────────────────────────────────────────────

class FakeClient:
    """Mimics groq.Groq: client.chat.completions.create(...) returns queued replies."""
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.replies.pop(0)
        return type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": content})()})()]})()


VALID = json.dumps({"category": "hardware_endpoint", "impact": "low", "urgency": "low", "affected_service": "Mouse",
                    "summary": "Squeaky mouse wheel.", "language": "en", "confidence": 0.95,
                    "rationale": "Single user, cosmetic.", "draft_reply": "Thanks, we will replace it."})


def test_invalid_json_is_retried_with_the_error():
    client = FakeClient(['{"category": "printer"}', VALID])
    result = call_llm("Mouse", "Wheel squeaks", client=client)
    assert result.category == "hardware_endpoint" and len(client.calls) == 2
    assert "invalid" in client.calls[1]["messages"][-1]["content"]
    assert client.calls[0]["response_format"] == {"type": "json_object"}


def test_gives_up_after_one_retry():
    with pytest.raises(TriageError):
        call_llm("Mouse", "Wheel squeaks", client=FakeClient(["not json", "still not json"]))


# ─── API ───────────────────────────────────────────────────────────────────────

client = TestClient(app)


def test_root_and_taxonomy():
    assert client.get("/").json()["status"] == "ok"
    taxonomy = client.get("/taxonomy").json()
    assert taxonomy["priority_matrix"]["high/high"] == "P1"
    assert taxonomy["categories"]["security_incident"]["resolver_group"] == "Security Operations Center"


def test_triage_endpoint(monkeypatch):
    monkeypatch.delenv("SERVICE_API_KEY", raising=False)
    monkeypatch.setattr("app.main.triage", lambda t: triage(t, llm=llm_returning()))
    response = client.post("/triage", json={"subject": "No network", "description": "Building B is offline."})
    assert response.status_code == 200 and response.json()["priority"] == "P1"


def test_service_api_key_is_enforced_when_set(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "secret")
    monkeypatch.setattr("app.main.triage", lambda t: triage(t, llm=llm_returning()))
    body = {"subject": "No network", "description": "Building B is offline."}
    assert client.post("/triage", json=body).status_code == 401
    assert client.post("/triage", json=body, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/triage", json=body, headers={"X-API-Key": "secret"}).status_code == 200


def test_empty_ticket_is_rejected():
    assert client.post("/triage", json={"subject": "", "description": "x"}).status_code == 422


# ─── Baseline and metrics ──────────────────────────────────────────────────────

@pytest.mark.parametrize("subject, description, category", [
    ("Phishing", "I clicked a link in a suspicious email", "security_incident"),
    ("Drucker", "Der Drucker im 2. Stock druckt nicht", "hardware_endpoint"),
    ("Passwort", "Mein Konto ist gesperrt", "access_identity"),
])
def test_baseline_categories(subject, description, category):
    assert baseline.classify(subject, description)["category"] == category


def test_score_counts_under_calls_and_review():
    tickets = [{"id": "1", "lang": "en", "category": "a", "priority": "P1"},
               {"id": "2", "lang": "de", "category": "b", "priority": "P5"}]
    predictions = [{"category": "a", "priority": "P3", "needs_human_review": True},
                   {"category": "b", "priority": "P5", "needs_human_review": False}]
    s = score(tickets, predictions)
    assert s["major_under_called"] == ["1"] and s["under_calls_caught_by_review"] == ["1"]
    assert s["category_accuracy"] == 1.0 and s["priority_accuracy"] == 0.5 and s["auto_routed_accuracy"] == 1.0
