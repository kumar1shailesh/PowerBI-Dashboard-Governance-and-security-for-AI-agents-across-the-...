# DAX measures — overview

Every measure below should be created in a measure table called
`_Measures` so the field list stays clean. Paste each block into Power BI
Desktop via **Modeling → New measure**, or use Tabular Editor for bulk
import.

| File | What it covers |
| --- | --- |
| `01_risk_measures.dax` | Composite agent risk score, risk bucket, top-N risky agents |
| `02_violation_measures.dax` | Open / closed counts, MTTR, SLA breach |
| `03_token_measures.dax` | Token volumes, cost USD, MoM growth, top consumers |
| `04_compliance_measures.dax` | Compliance % per framework, control coverage |
| `05_fpa_measures.dax` | Function-point analysis for remediation effort + cost |
| `06_runtime_measures.dax` | Runtime events, block rate, attack-attempt rate |

## Parameter table

Create a what-if parameter (Modeling → New parameter) called
`HourlyRateUSD` with default 75 — used by the FPA cost measure.
