# Page 8 — FPA Effort & Capacity Planning

Quantitative answer to "how many engineer-weeks to clear this backlog?".
Built around function-point analysis with a what-if hourly rate.

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Remediation FPA + capacity      [sev | framework | team capacity]  │
├──────────┬──────────┬──────────┬──────────┬────────────────────────────────┤
│ Open     │ FPA      │ Estimated│ Weeks to │ HourlyRateUSD what-if (slider) │
│ Backlog  │ Hours    │ Cost USD │ Clear    │                                 │
│  (KPI)   │  (KPI)   │  (KPI)   │  (KPI)   │                                 │
├──────────┴──────────┴──────────┴──────────┴────────────────────────────────┤
│ FPA hours by framework (clustered bar) │ FPA hours by business unit (bar) │
├────────────────────────────────────────┼──────────────────────────────────┤
│ Velocity: hours closed last 7D / 30D  │ Burndown vs ideal (line + ref)    │
└────────────────────────────────────────┴──────────────────────────────────┘
```

## What-if parameters to create

In Power BI Desktop: **Modeling → New parameter → Numeric range**:

| Name | Min | Max | Increment | Default |
| --- | ---:| ---:| ---:| ---:|
| `HourlyRateUSD` | 25 | 250 | 5 | 75 |
| `TeamCapacityHrsPerWeek` | 20 | 600 | 20 | 120 |

Drag both onto the page as slicers — the cost + weeks-to-clear cards
react in real time.

## Measures used

- `Open Violations`
- `FPA Hours Total`, `FPA Hours Critical`, `FPA Hours High`
- `FPA Estimated Cost USD`, `FPA Estimated Cost USD Card`
- `FPA Weeks To Clear`, `FPA Weeks To Clear Card`
- `FPA Hours By Framework`, `FPA Hours By Business Unit`
- `FPA Hours Closed 7D`, `FPA Hours Closed 30D`

## Burndown setup

1. Line chart, x = `dim_date[date]` (last 90 days), y = cumulative open
   `FPA Hours Total` evaluated at each date (use
   `CALCULATE([FPA Hours Total], FILTER(ALL(dim_date), dim_date[date] <= MAX(dim_date[date])))`).
2. Add a constant reference line at the target backlog by month end.
