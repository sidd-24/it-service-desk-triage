"""
Keyword baseline: a rule-based triage like many service desks use before
any AI. It is the comparison point in the evaluation and the fallback when
the LLM is unavailable. Keywords cover English and German tickets.
"""
import re

# Checked in this order; the first category with a match wins. Security
# comes first so "phishing email" is not filed under email.
CATEGORY_KEYWORDS = [
    ("security_incident", ["phishing", "malware", "virus", "ransomware", "trojan", "hacked", "suspicious",
                           "stolen", "lost my laptop", "lost laptop", "data breach", "data leak",
                           "verdächtig", "gestohlen", "verloren", "datenleck", "schadsoftware", "verschlüsselt"]),
    ("ot_production", ["production line", "machine", "plc", "scanner", "mes", "shop floor", "assembly line",
                       "fertigung", "produktion", "maschine", "anlage", "linie", "sps"]),
    ("access_identity", ["password", "locked out", "lockout", "account locked", "mfa", "authenticator",
                         "permission", "access denied", "cannot log in", "can't log in", "login",
                         "passwort", "kennwort", "gesperrt", "berechtigung", "anmelden", "zugriff verweigert"]),
    ("network_connectivity", ["vpn", "wifi", "wi-fi", "wlan", "network", "internet", "no connection", "lan",
                              "netzwerk", "keine verbindung", "verbindung"]),
    ("email_collaboration", ["outlook", "email", "e-mail", "mailbox", "teams", "sharepoint", "calendar",
                             "shared drive", "postfach", "kalender", "laufwerk"]),
    ("business_application", ["sap", "erp", "crm", "workday", "invoice", "purchase order", "transaction",
                              "rechnung", "bestellung", "buchung"]),
    ("hardware_endpoint", ["laptop", "notebook", "monitor", "screen", "printer", "keyboard", "mouse",
                           "docking", "battery", "drucker", "bildschirm", "tastatur", "akku"]),
    ("service_request", ["request", "new employee", "new joiner", "install", "please provide", "order a",
                         "need a new", "antrag", "neuer mitarbeiter", "installieren", "bitte um", "benötige"]),
]

HIGH_IMPACT = ["all users", "everyone", "whole department", "entire", "whole plant", "production line",
               "production stopped", "customers", "all of us", "nobody can", "site-wide", "data breach",
               "ransomware", "alle", "gesamte", "ganze abteilung", "niemand", "produktion steht", "kunden"]
MEDIUM_IMPACT = ["team", "several", "multiple", "colleagues", "department", "group",
                 "mehrere", "kollegen", "abteilung"]

HIGH_URGENCY = ["urgent", "asap", "immediately", "stopped", "down", "outage", "cannot work", "can't work",
                "blocked", "not working at all", "right now", "critical", "emergency",
                "dringend", "sofort", "steht", "ausgefallen", "kann nicht arbeiten", "notfall", "kritisch"]
LOW_URGENCY = ["when you have time", "no rush", "not urgent", "next week", "question", "would like",
               "nice to have", "keine eile", "nicht dringend", "nächste woche", "frage", "hätte gern"]


def _has(text, words):
    return any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", text) for w in words)


def classify(subject: str, description: str) -> dict:
    """Returns category, impact and urgency from keywords."""
    text = f"{subject} {description}".lower()
    category = next((c for c, words in CATEGORY_KEYWORDS if _has(text, words)), "other")
    impact = "high" if _has(text, HIGH_IMPACT) else "medium" if _has(text, MEDIUM_IMPACT) else "low"
    urgency = "high" if _has(text, HIGH_URGENCY) else "low" if _has(text, LOW_URGENCY) else "medium"
    return {"category": category, "impact": impact, "urgency": urgency}
