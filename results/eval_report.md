# Evaluation report

60 labelled tickets (11 in German), 16 of them P1/P2.

| Metric | Keyword baseline | LLM triage (openai/gpt-oss-120b) |
|---|---|---|
| Category accuracy | 68% | 97% |
| Priority exactly right | 35% | 78% |
| Priority within one level | 78% | 97% |
| P1/P2 recognised as P1/P2 | 31% | 100% |
| P1/P2 under-called | 12 of 16 | 0 of 16 |
| P4/P5 over-called as P1/P2 | 1 | 0 |
| Category and priority right (English) | 22% | 78% |
| Category and priority right (German) | 27% | 73% |
| Sent to human review | n/a | 25% |
| Accuracy of auto-routed tickets | n/a | 78% |
| Under-calls caught by review | n/a | 0 |

## Keyword baseline: priority confusion

| Expected \ Predicted | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| **P1** | 3 | 1 | 5 | 1 |  |
| **P2** |  | 1 |  | 5 |  |
| **P3** |  |  | 6 | 10 |  |
| **P4** |  | 1 | 2 | 8 |  |
| **P5** |  |  | 1 | 13 | 3 |

Under-called P1/P2: N2, N6, B4, E5, S1, S3, S4, S7, S8, O1, O3, O6. Over-called P4/P5: E3.

## LLM triage (openai/gpt-oss-120b): priority confusion

| Expected \ Predicted | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| **P1** | 10 |  |  |  |  |
| **P2** | 4 | 2 |  |  |  |
| **P3** |  | 3 | 13 |  |  |
| **P4** |  |  | 3 | 7 | 1 |
| **P5** |  |  | 2 |  | 15 |

Under-called P1/P2: none. Over-called P4/P5: none.
Under-calls not caught by review: none.

## LLM misses

| Ticket | Expected | Predicted | Review | Rationale |
|---|---|---|---|---|
| A5 Sales team cannot sign in | access_identity medium/high P2 | access_identity high/high P1 | yes | A whole sales team is blocked from work, stopping customer appointments. |
| H2 Printer on 2nd floor jams | hardware_endpoint low/low P5 | hardware_endpoint medium/medium P3 | no | Several users are affected by the printer jam, but an alternative printer is available. |
| H5 Docking stations in meeting rooms | hardware_endpoint medium/medium P3 | hardware_endpoint medium/high P2 | no | Several teams rely on the rooms daily, so the outage disrupts meetings immediately. |
| N5 WLAN im Besprechungsraum | network_connectivity low/high P3 | network_connectivity medium/high P2 | no | Ein wichtiges Kundentreffen steht heute an (hohe Dringlichkeit), aber das Problem betrifft nur einen Raum/Team (mittlerer Impact). |
| B6 Fehler beim Buchen von Rechnungen | business_application low/medium P4 | business_application medium/medium P3 | no | Only one user is affected but the task is business‑critical with a deadline this Friday, so impact and urgency are medium. |
| E3 No audio in Teams meetings | email_collaboration low/medium P4 | email_collaboration low/high P3 | no | Only one user is affected but meetings are halted today, requiring immediate attention. |
| E5 Project SharePoint site blank | email_collaboration medium/high P2 | email_collaboration high/high P1 | yes | All project members cannot access a critical site needed for tomorrow's cutover, stopping the process. |
| E7 Supplier emails rejected | email_collaboration medium/medium P3 | email_collaboration medium/high P2 | no | Two users cannot receive critical supplier emails, and a deadline this week creates high urgency. |
| S3 Laptop stolen from car | security_incident medium/high P2 | security_incident high/high P1 | yes | Stolen device with sensitive data poses a high business impact and requires immediate action. |
| S5 Antivirus removed a threat | security_incident low/medium P4 | security_incident low/low P5 | no | Only one user affected and the issue appears resolved, so impact and urgency are low. |
| O4 Etikettendrucker Linie 5 unscharf | ot_production low/low P5 | ot_production medium/medium P3 | no | Nur eine Produktionslinie ist betroffen, die Arbeit läuft weiter, aber die Qualität ist beeinträchtigt. |
| O5 Remote access for press maintenance | ot_production low/medium P4 | service_request medium/medium P3 | no | A single production press requires remote access for tomorrow, affecting one machine but important for scheduled maintenance. |
| O6 Packaging line PLC alarms | ot_production high/medium P2 | ot_production high/high P1 | yes | A whole production line is repeatedly stopping, causing significant output loss, so impact and urgency are high. |
| X1 Excel training | other low/low P5 | service_request low/low P5 | no | A single user is requesting information, no service is broken. |
