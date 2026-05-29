# Page 4 — Violations & Remediation

Ops-team view. Where are the open violations, how old, who owns them?

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: Violations & remediation                [date | sev | status]      │
├────────────┬─────────────┬───────────────┬───────────────┬─────────────────┤
│ Open       │ MTTR        │ MTTR Critical │ SLA breach %  │ Closed 30D      │
│ (KPI)      │ (KPI days)  │ (KPI days)    │ (KPI %)       │ (KPI)           │
├────────────┴─────────────┴───────────────┴───────────────┴─────────────────┤
│  Aging buckets (column chart):     │  Status distribution (donut)         │
│  0-7d / 8-30d / 31-90d / 91d+      │                                       │
├────────────────────────────────────┼───────────────────────────────────────┤
│  Open violations table (paged):                                            │
│  violation_id | agent | control | severity | detected_date | due_date     │
│  status | days_overdue                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Measures used

- `Open Violations`
- `MTTR Days`
- `MTTR Critical Days`
- `MTTR High Days`
- `SLA Breach Count` / `SLA Breach %`
- `Open Violations 0-7d` / `8-30d` / `31-90d` / `91d+`
- `Remediated Violations` filtered to last 30 days

## Conditional formatting

- `days_overdue` column: > 0 → red, ≤ 0 → grey.
- Severity column: cell background from `dim_severity[color_hex]`.

## Slicers

- Date range
- Severity (multi-select)
- Status (multi-select)
- Business unit
- Platform
