# Page 7 — Design-Time Findings

Code- and config-level issues from agent design reviews. These are the
upstream problems — they show up before the agent goes to production.

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Design-time findings                    [date | severity | bu]     │
├────────────────────────────────┬───────────────────────────────────────────┤
│  Open by severity (donut)      │  Open by title (bar, top 10)              │
├────────────────────────────────┼───────────────────────────────────────────┤
│  Findings over time (line)     │  Agents with most design-time findings    │
├────────────────────────────────┴───────────────────────────────────────────┤
│  Findings table:                                                           │
│  finding_id | agent | title | severity | detected_date | status            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Measures

Add this to `01_risk_measures.dax` (it's a fact-design-finding rollup):

```dax
Open Design Findings =
CALCULATE(
    COUNTROWS( fact_design_finding ),
    fact_design_finding[status] IN { "open", "in_progress" }
)

Open Design Findings Critical =
CALCULATE(
    [Open Design Findings],
    fact_design_finding[severity] = "Critical"
)
```

## Slicers

- Date range
- Severity
- Status
- Business unit
- Platform
