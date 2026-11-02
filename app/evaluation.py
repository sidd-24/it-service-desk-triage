"""
Metrics for data/eval/tickets.json. A prediction is a dict with category,
priority and (for the full triage) needs_human_review.
"""
from collections import Counter

PRIORITIES = ["P1", "P2", "P3", "P4", "P5"]


def rank(priority: str) -> int:
    return int(priority[1])


def score(tickets: list[dict], predictions: list[dict]) -> dict:
    n = len(tickets)
    pairs = list(zip(tickets, predictions))
    major = [(t, p) for t, p in pairs if rank(t["priority"]) <= 2]
    minor = [(t, p) for t, p in pairs if rank(t["priority"]) >= 4]

    # Under-call: a P1/P2 ticket predicted at a lower priority. The costly mistake.
    under = [t["id"] for t, p in major if rank(p["priority"]) > rank(t["priority"])]
    result = {
        "tickets": n,
        "category_accuracy": sum(t["category"] == p["category"] for t, p in pairs) / n,
        "priority_accuracy": sum(t["priority"] == p["priority"] for t, p in pairs) / n,
        "priority_within_one": sum(abs(rank(t["priority"]) - rank(p["priority"])) <= 1 for t, p in pairs) / n,
        "major_incidents": len(major),
        "major_recall": sum(rank(p["priority"]) <= 2 for _, p in major) / len(major),
        "major_under_called": under,
        "minor_over_called": [t["id"] for t, p in minor if rank(p["priority"]) <= 2],
        "by_language": {
            lang: sum(t["category"] == p["category"] and t["priority"] == p["priority"] for t, p in group) / len(group)
            for lang in sorted({t["lang"] for t in tickets})
            for group in [[(t, p) for t, p in pairs if t["lang"] == lang]]
        },
        "priority_confusion": {
            expected: dict(Counter(p["priority"] for t, p in pairs if t["priority"] == expected))
            for expected in PRIORITIES
        },
    }

    if all("needs_human_review" in p for p in predictions):
        reviewed = [(t, p) for t, p in pairs if p["needs_human_review"]]
        auto = [(t, p) for t, p in pairs if not p["needs_human_review"]]
        flagged = {t["id"] for t, p in reviewed}
        result.update({
            "review_rate": len(reviewed) / n,
            # Accuracy of what goes straight to a resolver group without a person checking
            "auto_routed_accuracy": (sum(t["category"] == p["category"] and t["priority"] == p["priority"]
                                         for t, p in auto) / len(auto)) if auto else None,
            "under_calls_caught_by_review": [i for i in under if i in flagged],
            "under_calls_missed": [i for i in under if i not in flagged],
        })
    return result
