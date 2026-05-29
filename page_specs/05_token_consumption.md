# Page 5 — Token Consumption & Cost

Per-agent cost telemetry — the page the finance team will reach for
first.

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Token consumption & cost                    [date | model | bu]    │
├────────────┬────────────┬────────────┬────────────┬────────────────────────┤
│ Cost MTD   │ Cost YTD   │ Cost MoM%  │ Per-agent  │ Cost per 1K requests   │
│  (KPI)     │  (KPI)     │  (KPI)     │   (KPI)    │  (KPI)                 │
├────────────┴────────────┴────────────┴────────────┴────────────────────────┤
│  Daily cost trend (line)            │  Cost by model (pie)                 │
├─────────────────────────────────────┼──────────────────────────────────────┤
│  Top 15 agents by cost (bar)        │  Cost anomalies (table)              │
│                                     │  agent | date | cost | 7D avg | flag │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

## Measures used

- `Total Cost USD`, `Cost USD MTD`, `Cost USD YTD`
- `Cost USD MoM %`
- `Cost Per Agent`, `Cost Per 1K Requests`
- `Daily Cost`, `7D Avg Daily Cost`, `Cost Anomaly Flag`
- `Top 5 Agents By Cost` (string for caption)

## Anomaly table setup

- Table visual.
- Rows: agent_id, date, daily cost, 7D average, ratio.
- Filter to `Cost Anomaly Flag = "Spike"`.
- Sort: date desc.

## Slicers

- Date range (default last 30 days)
- Model
- Platform
- Business unit
