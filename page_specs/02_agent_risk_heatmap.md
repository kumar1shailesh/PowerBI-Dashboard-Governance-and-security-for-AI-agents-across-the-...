# Page 2 — Agent Risk Heat Map

One row per agent, columns for each risk driver. Conditional formatting
turns the cell colour from green → red so leadership can spot hotspots
without reading the numbers.

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Agent risk heatmap                  [platform | bu | criticality]   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Matrix:                                                                    │
│    Rows: agent name + platform                                              │
│    Columns: Risk score, Open C/H, SLA breaches, Attempts 30D,               │
│             Excessive-agency, Tools count, Last 30D cost                    │
│    Values: each is a measure with conditional formatting (color scale)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Matrix configuration

Use a **Matrix** visual (not Table) so the column headers behave
properly.

| Column | Measure | Conditional format |
| --- | --- | --- |
| Risk score | `Risk Score` | Color scale: 0 = green (#548235) → 100 = red (#C00000) |
| Open C/H | `Open Critical High Violations` | Same gradient, 0-10 |
| SLA breaches | `SLA Breach Count` | Same gradient, 0-5 |
| Attempts 30D | `Runtime Attack Attempts 30D` | Same gradient, 0-200 |
| Excessive-agency | `Open Excessive Agency Findings` | Same gradient, 0-5 |
| Tools count | `dim_agent[tools_count]` SUM | Static — flag if > 6 |
| Cost 30D | `Total Cost USD` last 30 days | Same gradient, 0 → max |

## Slicers

- Platform (multi-select)
- Business unit
- Criticality
- Environment

## Sorting

Default sort by `Risk Score` desc. Right-click the column header → Sort.
