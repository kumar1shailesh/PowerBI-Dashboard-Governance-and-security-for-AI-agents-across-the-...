# Data model

## ERD (star schema)

```
                ┌──────────────┐
                │  dim_date    │
                └──────┬───────┘
                       │ date
   ┌──────────────┐    │           ┌──────────────────┐
   │  dim_agent   ├────┼──────────┤ fact_violation   │
   └──────┬───────┘    │           └──────┬───────────┘
          │            │                  │ control_id
          │ agent_id   │                  ▼
          │            │           ┌──────────────────┐
          ├────────────┼──────────▶│ dim_control      │
          │            │           └──────┬───────────┘
          │            │                  │ framework_id
          │            │                  ▼
          │            │           ┌──────────────────┐
          │            │           │ dim_framework    │
          │            │           └──────────────────┘
          │            │
          │            │           ┌──────────────────┐
          ├────────────┼──────────▶│ fact_token       │ (date, agent_id, model)
          │            │           │  _consumption    │
          │            │           └──────────────────┘
          │            │
          │            │           ┌──────────────────┐
          ├────────────┼──────────▶│ fact_runtime     │ (event_ts, agent_id)
          │            │           │  _event          │
          │            │           └──────────────────┘
          │            │
          │            │           ┌──────────────────┐
          └────────────┴──────────▶│ fact_design      │ (detected_date, agent_id)
                                   │  _finding        │
                                   └──────────────────┘
                ┌──────────────┐
                │ dim_severity │  ←- referenced by every fact
                └──────────────┘

                ┌──────────────┐
                │  dim_status  │  ←- referenced by fact_violation, fact_design_finding
                └──────────────┘
```

## Tables

### Dimensions

| Table | Grain | Primary key | Notes |
| --- | --- | --- | --- |
| `dim_agent` | one row per AI agent | `agent_id` | platform + business unit slice everything |
| `dim_framework` | one row per regulatory / industry framework | `framework_id` | populated by the generator |
| `dim_control` | one row per control within a framework | `control_id` | bridge to facts via violation |
| `dim_date` | one row per calendar day | `date` | mark as date table |
| `dim_severity` | one row per severity level | `severity` | colour + SLA day count |
| `dim_status` | one row per workflow status | `status` | colour |

### Facts

| Table | Grain | Foreign keys |
| --- | --- | --- |
| `fact_violation` | one row per detected violation | `agent_id`, `control_id`, `detected_date`, `severity`, `status` |
| `fact_token_consumption` | one row per (date, agent, model) | `date`, `agent_id` |
| `fact_runtime_event` | one row per runtime event | `event_ts`, `agent_id`, `severity` |
| `fact_design_finding` | one row per design-time finding | `agent_id`, `severity`, `status`, `detected_date` |

## Relationships

| From | To | Cardinality | Cross-filter |
| --- | --- | --- | --- |
| `fact_violation[agent_id]` | `dim_agent[agent_id]` | many → 1 | single |
| `fact_violation[control_id]` | `dim_control[control_id]` | many → 1 | single |
| `fact_violation[detected_date]` | `dim_date[date]` | many → 1 | single |
| `fact_violation[severity]` | `dim_severity[severity]` | many → 1 | single |
| `fact_violation[status]` | `dim_status[status]` | many → 1 | single |
| `fact_token_consumption[agent_id]` | `dim_agent[agent_id]` | many → 1 | single |
| `fact_token_consumption[date]` | `dim_date[date]` | many → 1 | single |
| `fact_runtime_event[agent_id]` | `dim_agent[agent_id]` | many → 1 | single |
| `fact_runtime_event[severity]` | `dim_severity[severity]` | many → 1 | single |
| `fact_design_finding[agent_id]` | `dim_agent[agent_id]` | many → 1 | single |
| `fact_design_finding[severity]` | `dim_severity[severity]` | many → 1 | single |
| `dim_control[framework_id]` | `dim_framework[framework_id]` | many → 1 | single |

> `fact_runtime_event` does not join to `dim_date` directly because its
> grain is timestamp, not date. If you need date-level slicing on this
> table, add a calculated column `event_date = INT(fact_runtime_event[event_ts])`
> and relate that to `dim_date[date]`.
