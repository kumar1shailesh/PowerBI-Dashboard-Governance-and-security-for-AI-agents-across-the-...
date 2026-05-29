# Page 3 — Framework Compliance

How does the agent fleet stack up against every active framework? One
control = one cell.

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Framework compliance                  [framework slicer | platform]│
├──────────────────────────────────┬──────────────────────────────────────────┤
│ KPI strip:                       │                                          │
│   OWASP LLM 10                   │   Coverage heatmap                       │
│   MITRE ATLAS                    │   rows = dim_agent[name]                 │
│   NIST AI RMF                    │   cols = dim_control[control_code]       │
│   EU AI Act                      │   value = Coverage Cell                  │
│   ISO 42001                      │   (red = open violation, green = clean)  │
├──────────────────────────────────┴──────────────────────────────────────────┤
│  Design vs runtime split           │  Per-control violations               │
│  (clustered column)                │  (top 10 violated controls)           │
└────────────────────────────────────┴────────────────────────────────────────┘
```

## Measures used

- `Compliance % OWASP`
- `Compliance % ATLAS`
- `Compliance % NIST`
- `Compliance % EU AI Act`
- `Compliance % ISO 42001`
- `Compliance % Design`
- `Compliance % Runtime`
- `Coverage Cell`
- `Coverage Cell Color`

## Coverage heatmap setup

1. Add **Matrix** visual.
2. Rows: `dim_agent[name]`.
3. Columns: `dim_control[control_code]`.
4. Values: `Coverage Cell`.
5. Format → Conditional formatting → Background color → Field value =
   `Coverage Cell Color`. Hide the data label so only the colour shows.

## Drill-through

Right-click any red cell → drill through to the Violations &
Remediation page (filtered to that agent + control).
