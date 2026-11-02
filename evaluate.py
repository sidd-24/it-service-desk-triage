"""
Evaluates the triage on the labelled tickets in data/eval/tickets.json.

    python evaluate.py           # keyword baseline only, no API key needed
    python evaluate.py --llm     # baseline and LLM triage (needs GROQ_API_KEY)

Writes results/eval_report.md and results/eval_results.json.
"""
import argparse
import json
import os
import time
from pathlib import Path

from app import baseline
from app.config import GROQ_MODEL
from app.evaluation import PRIORITIES, score
from app.models import TicketIn
from app.triage import priority_for, triage

TICKETS = Path("data/eval/tickets.json")
RESULTS = Path("results")


def pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def run_baseline(tickets):
    predictions = []
    for t in tickets:
        k = baseline.classify(t["subject"], t["description"])
        predictions.append({**k, "priority": priority_for(k["impact"], k["urgency"])})
    return predictions


def run_llm(tickets):
    predictions = []
    for t in tickets:
        result = triage(TicketIn(subject=t["subject"], description=t["description"]))
        predictions.append(result.model_dump(mode="json"))
        print(f"{t['id']}: expected {t['category']}/{t['priority']}, got {result.category}/{result.priority}"
              f"{' (review)' if result.needs_human_review else ''}")
        time.sleep(1)  # stay under the free-tier rate limit
    return predictions


def confusion_table(confusion):
    lines = ["| Expected \\ Predicted | " + " | ".join(PRIORITIES) + " |", "|---" * (len(PRIORITIES) + 1) + "|"]
    for expected in PRIORITIES:
        lines.append(f"| **{expected}** | " + " | ".join(str(confusion[expected].get(p, "")) for p in PRIORITIES) + " |")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--llm", action="store_true", help="also evaluate the LLM triage")
    args = parser.parse_args()

    tickets = json.loads(TICKETS.read_text(encoding="utf-8"))
    runs = {"Keyword baseline": (run_baseline(tickets), None)}
    if args.llm:
        if not os.getenv("GROQ_API_KEY"):
            raise SystemExit("Set GROQ_API_KEY to evaluate the LLM triage.")
        predictions = run_llm(tickets)
        runs[f"LLM triage ({GROQ_MODEL})"] = (predictions, predictions)

    report = {"tickets": len(tickets)}
    lines = ["# Evaluation report", "",
             f"{len(tickets)} labelled tickets ({sum(t['lang'] == 'de' for t in tickets)} in German), "
             f"{sum(t['priority'] in ('P1', 'P2') for t in tickets)} of them P1/P2.", "",
             "| Metric | " + " | ".join(runs) + " |", "|---" * (len(runs) + 1) + "|"]
    scores = {name: score(tickets, preds) for name, (preds, _) in runs.items()}
    rows = [
        ("Category accuracy", lambda s: pct(s["category_accuracy"])),
        ("Priority exactly right", lambda s: pct(s["priority_accuracy"])),
        ("Priority within one level", lambda s: pct(s["priority_within_one"])),
        ("P1/P2 recognised as P1/P2", lambda s: pct(s["major_recall"])),
        ("P1/P2 under-called", lambda s: f"{len(s['major_under_called'])} of {s['major_incidents']}"),
        ("P4/P5 over-called as P1/P2", lambda s: str(len(s["minor_over_called"]))),
        ("Category and priority right (English)", lambda s: pct(s["by_language"].get("en"))),
        ("Category and priority right (German)", lambda s: pct(s["by_language"].get("de"))),
        ("Sent to human review", lambda s: pct(s.get("review_rate"))),
        ("Accuracy of auto-routed tickets", lambda s: pct(s.get("auto_routed_accuracy"))),
        ("Under-calls caught by review", lambda s: str(len(s["under_calls_caught_by_review"])) if "review_rate" in s else "n/a"),
    ]
    for label, fn in rows:
        lines.append(f"| {label} | " + " | ".join(fn(s) for s in scores.values()) + " |")

    for name, s in scores.items():
        lines += ["", f"## {name}: priority confusion", "", *confusion_table(s["priority_confusion"]),
                  "", f"Under-called P1/P2: {', '.join(s['major_under_called']) or 'none'}. "
                      f"Over-called P4/P5: {', '.join(s['minor_over_called']) or 'none'}."]
        if "under_calls_missed" in s:
            lines.append(f"Under-calls not caught by review: {', '.join(s['under_calls_missed']) or 'none'}.")
    report["scores"] = scores

    for name, (preds, details) in runs.items():
        if details:
            misses = [(t, p) for t, p in zip(tickets, details)
                      if t["category"] != p["category"] or t["priority"] != p["priority"]]
            report["llm_details"] = [{"id": t["id"], **{k: p[k] for k in ("category", "impact", "urgency", "priority",
                                     "confidence", "needs_human_review", "review_reasons", "summary")}}
                                    for t, p in zip(tickets, details)]
            lines += ["", "## LLM misses", "", "| Ticket | Expected | Predicted | Review | Rationale |", "|---|---|---|---|---|"]
            lines += [f"| {t['id']} {t['subject']} | {t['category']} {t['impact']}/{t['urgency']} {t['priority']} | "
                      f"{p['category']} {p['impact']}/{p['urgency']} {p['priority']} | "
                      f"{'yes' if p['needs_human_review'] else 'no'} | {p['rationale']} |" for t, p in misses]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "eval_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (RESULTS / "eval_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
