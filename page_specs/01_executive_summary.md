# Page 1 — Executive Summary

The board-room view. Everything else drills down from here.

## Layout (16:9, 1920×1080)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: AI Agent Governance — Executive Summary       [date-slicer | env]  │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────────┤
│ Total    │ Critical │ Open     │ SLA      │ Cost     │ Block rate          │
│ Agents   │ Agents   │ Violatns │ Breaches │ MTD ($)  │ (runtime)           │
│  (KPI)   │  (KPI)   │  (KPI)   │  (KPI)   │  (KPI)   │  (KPI gauge)        │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────────────────┤
│  Compliance % by framework            │ Top 10 risky agents (bar)          │
│  (clustered bar: OWASP/ATLAS/         │                                    │
│   NIST/EUAI/ISO)                      │                                    │
├──────────────────────────────────────┼─────────────────────────────────────┤
│  Open violations by severity         │ Token cost trend (last 30 days)    │
│  (donut)                              │ (line)                             │
└──────────────────────────────────────┴─────────────────────────────────────┘
```

## Visuals + measures

| Visual | Type | Measure / field |
| --- | --- | --- |
| Total Agents | Card | `DISTINCTCOUNT( dim_agent[agent_id] )` |
| Critical Agents | Card | `Critical Agents Count` |
| Open Violations | Card | `Open Violations` |
| SLA Breaches | Card with red conditional | `SLA Breach Count` |
| Cost MTD | Card | `Cost USD MTD` |
| Block rate | Gauge (0-100%) | `Block Rate %` |
| Compliance by framework | Clustered bar | rows = `dim_framework[name]`, value = `Compliance %` |
| Top 10 risky agents | Bar with data label | rows = `dim_agent[name]`, value = `Risk Score`, top 10 |
| Violations by severity | Donut | legend = `dim_severity[severity]`, value = `Open Violations`, colour from `dim_severity[color_hex]` |
| Token cost trend | Line | x = `dim_date[date]`, value = `Total Cost USD`, last 30 days |

## Slicers

- Date range (top-right)
- Environment (prod / uat / dev)
- Business Unit (multi-select)
- Platform (Copilot / Claude / OpenAI / LangGraph / Custom)

## Drill-through targets

- Click an agent row in the "Top 10 risky agents" bar → page 9 (Agent
  Drill-Through).
- Click a framework bar in the compliance chart → page 3 (Framework
  Compliance) with the framework slicer pre-set.
