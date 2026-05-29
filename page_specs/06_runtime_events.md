# Page 6 — Runtime Events Timeline

Live-defence posture: which attacks are landing, are they blocked, which
agents see the most heat?

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Runtime events                           [date | event type]       │
├──────────┬──────────┬──────────┬──────────┬────────────────────────────────┤
│ Events   │ Blocked  │ Block    │ Prompt   │ Top under-attack agent (text)  │
│ 30D      │ 30D      │ Rate     │ Injection│                                 │
│  (KPI)   │  (KPI)   │  (KPI %) │ Attempts │                                 │
├──────────┴──────────┴──────────┴──────────┴────────────────────────────────┤
│  Events over time (stacked area by event_type)                             │
├────────────────────────────────────┬───────────────────────────────────────┤
│  Per-attack-class counts (bar)     │  Blocked vs not (donut)               │
├────────────────────────────────────┼───────────────────────────────────────┤
│  Recent events table (last 100):                                           │
│  event_ts | agent | event_type | severity | blocked                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Measures used

- `Total Runtime Events`, `Runtime Events 30D`, `Runtime Events 7D`
- `Blocked Events`, `Block Rate %`
- `Prompt Injection Attempts`, `Jailbreak Attempts`,
  `Tool Misuse Blocks`, `PII Leak Blocks`, `System Prompt Leak Incidents`
- `Attacks Per Agent 30D`

## Slicers

- Date range
- Event type
- Severity
- blocked (true / false)
