"""
Service desk configuration: categories, resolver groups, the ITIL priority
matrix and SLA targets. Change these to match your own service catalogue.
"""
import os

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Category -> (description for the LLM, resolver group)
CATEGORIES = {
    "access_identity": ("Passwords, account lockouts, MFA, permissions and access rights", "Identity & Access Management"),
    "hardware_endpoint": ("Laptops, PCs, monitors, docking stations, printers, phones", "Endpoint Support"),
    "network_connectivity": ("VPN, Wi-Fi, LAN, internet access, network outages", "Network Operations"),
    "business_application": ("Errors or outages in business applications such as SAP ERP, CRM or HR systems", "Application Support"),
    "email_collaboration": ("Email, calendar, Teams, SharePoint, file shares", "Workplace Services"),
    "security_incident": ("Phishing, malware, ransomware, lost or stolen devices, suspected data breaches", "Security Operations Center"),
    "ot_production": ("Production machines, line scanners, PLCs, MES and other shop-floor systems", "OT Support"),
    "service_request": ("Requests for new software, equipment or a new joiner setup, with nothing broken", "Service Desk Fulfilment"),
    "other": ("Anything that fits no other category", "Service Desk L1"),
}

LEVELS = ["high", "medium", "low"]

# ITIL priority matrix: (impact, urgency) -> priority. P1 is the most urgent.
PRIORITY_MATRIX = {
    ("high", "high"): "P1", ("high", "medium"): "P2", ("high", "low"): "P3",
    ("medium", "high"): "P2", ("medium", "medium"): "P3", ("medium", "low"): "P4",
    ("low", "high"): "P3", ("low", "medium"): "P4", ("low", "low"): "P5",
}

# SLA targets in calendar hours: (first response, resolution)
SLA_HOURS = {
    "P1": (0.25, 4),
    "P2": (0.5, 8),
    "P3": (4, 24),
    "P4": (8, 72),
    "P5": (24, 120),
}

# Tickets below this LLM confidence go to a person before routing
REVIEW_CONFIDENCE = 0.6
