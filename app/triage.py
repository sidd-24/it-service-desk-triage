"""
Combines the LLM output with the fixed service desk rules: ITIL priority,
resolver group, SLA deadlines and when a person has to check the result.
"""
from datetime import datetime, timedelta, timezone

from app import baseline
from app.config import CATEGORIES, PRIORITY_MATRIX, REVIEW_CONFIDENCE, SLA_HOURS
from app.llm import call_llm
from app.models import TicketIn, TriageResult


def priority_for(impact: str, urgency: str) -> str:
    return PRIORITY_MATRIX[(impact, urgency)]


def rank(priority: str) -> int:
    """P1 -> 1, ..., P5 -> 5"""
    return int(priority[1])


def triage(ticket: TicketIn, llm=call_llm, now: datetime | None = None) -> TriageResult:
    created = ticket.created_at or now or datetime.now(timezone.utc)
    keywords = baseline.classify(ticket.subject, ticket.description)
    reasons = []

    try:
        result = llm(ticket.subject, ticket.description).model_dump()
        source = "llm"
    except Exception as error:
        # The desk keeps working without the LLM; a person checks every fallback result
        result = {**keywords, "affected_service": "", "summary": ticket.subject, "language": "",
                  "confidence": 0.0, "rationale": "Keyword rules", "draft_reply": ""}
        source = "keyword_fallback"
        reasons.append(f"LLM unavailable, keyword rules used ({type(error).__name__})")

    priority = priority_for(result["impact"], result["urgency"])

    if source == "llm":
        if result["confidence"] < REVIEW_CONFIDENCE:
            reasons.append(f"Low confidence ({result['confidence']:.2f})")
        # Safety net: an under-called incident is the costly mistake, so a
        # second opinion from the keywords triggers a review
        if keywords["category"] == "security_incident" and result["category"] != "security_incident":
            reasons.append("Keywords suggest a security incident")
        if rank(priority_for(keywords["impact"], keywords["urgency"])) <= 2 and rank(priority) >= 4:
            reasons.append("Keywords suggest a higher priority")
    if result["category"] == "other":
        reasons.append("No matching category")
    # ITIL: a major incident is confirmed by the incident manager. The ticket is
    # still routed at once; the check catches a false P1 before people are paged.
    if priority == "P1":
        reasons.append("P1: incident manager to confirm major incident")

    response_hours, resolution_hours = SLA_HOURS[priority]
    return TriageResult(
        **result,
        priority=priority,
        resolver_group=CATEGORIES[result["category"]][1],
        first_response_due=created + timedelta(hours=response_hours),
        resolution_due=created + timedelta(hours=resolution_hours),
        needs_human_review=bool(reasons),
        review_reasons=reasons,
        source=source,
    )
