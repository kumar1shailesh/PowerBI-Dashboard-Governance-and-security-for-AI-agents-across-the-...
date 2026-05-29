# Refresh strategy

How often to refresh, what fails first, how to make scheduled refresh
robust in Power BI Service.

## Cadence

| Table | Recommended cadence | Reasoning |
| --- | --- | --- |
| `dim_agent` | hourly | agent inventory changes when new bots are deployed |
| `dim_framework` / `dim_control` | weekly | regulatory references rarely change |
| `dim_severity`, `dim_status` | static | no refresh required |
| `dim_date` | yearly | extend end date once a year |
| `fact_violation` | every 15 min | this is the operational signal |
| `fact_runtime_event` | every 5 min (Direct Query if volume is high) | live defence posture |
| `fact_token_consumption` | hourly | cost telemetry is daily anyway |
| `fact_design_finding` | hourly | pipeline-driven |

## Incremental refresh

The big two — `fact_token_consumption` and `fact_runtime_event` — benefit
from incremental refresh:

1. In Power Query, parameterise the date filter with `RangeStart` and
   `RangeEnd` (built-in names — Power BI recognises them).
2. Right-click the table → **Incremental refresh** policy → keep
   18 months of historical, refresh the last 7 days, detect data changes
   on `event_ts` / `date`.
3. First publish to Service triggers the historical partition build.

## Gateway

For on-prem REST APIs, install the **On-premises data gateway (standard
mode)**, register it under the workspace, and assign credentials.

For SaaS APIs, use the **VNet gateway** (preview) or dataset-level
"Authentication kind: Web API → Key" — depends on tenant policy.

## Refresh failure handling

- Email notification on failure: **Dataset Settings → Scheduled refresh
  → Send refresh failure notifications to** the team distribution
  list.
- Power Automate flow: poll the Admin REST API
  (`GET /admin/refreshes`) and alert on consecutive failures.

## Query folding hygiene

- Keep types narrow (Int64, Date, not Text) so the engine folds
  filters back to the source.
- Avoid `Table.AddColumn(..., each ...)` over big tables — write the
  calculation upstream where possible.
- View **Query Diagnostics** (Transform Data → Diagnose) on each fact
  table during dev — fix any "View native query" greyed-out warnings
  before production publish.
