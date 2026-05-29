# PBIX build guide — 30-minute walkthrough

This repo ships everything that goes **into** a Power BI file. The
binary `.pbix` itself has to be authored in Power BI Desktop because
PBIX is Microsoft's container format. Follow the steps below once and
save the result as `AI-Agent-Governance.pbix` in the repo root (it's
gitignored by default — uncomment if you want to commit binaries).

## Prereqs

- Power BI Desktop (free) — January 2025 or later.
- Python 3.10+ (only for regenerating the synthetic data).
- Optional: **Tabular Editor** (free, https://tabulareditor.com) — makes
  bulk DAX paste-in 10× faster.

## Step 1 — Generate / refresh data

```powershell
cd "C:\path\to\repo"
pip install -r scripts\requirements.txt
python scripts\generate_synthetic_data.py
```

You'll get CSVs in `data/` and `data/frameworks/`.

## Step 2 — Apply the theme

1. Open Power BI Desktop → **View → Themes → Browse for themes**.
2. Pick [`themes/governance_theme.json`](themes/governance_theme.json).
3. The page background turns light grey and the accent colour becomes
   the dark blue palette.

## Step 3 — Load the data

1. **Home → Get data → Folder**, pick the `data/` directory.
2. **Transform Data**. In the **Advanced Editor** for the auto-generated
   query, paste the contents of
   [`power_query/connect_csv.pq`](power_query/connect_csv.pq).
3. Create a parameter `DataFolder` pointing at the absolute path of
   `data/` on your machine. **Manage Parameters → New**.
4. Expand the `Promoted` column. Each table appears.
5. Right-click the master query → **Reference** for each table you
   need; rename the new queries to `dim_agent`, `fact_violation`, etc.
6. Close & Apply.

## Step 4 — Define the data model

In the **Model view**, create relationships exactly per
[`docs/data_model.md`](docs/data_model.md):

- `fact_violation[agent_id]` → `dim_agent[agent_id]`
- `fact_violation[control_id]` → `dim_control[control_id]`
- `fact_violation[detected_date]` → `dim_date[date]`
- `fact_violation[severity]` → `dim_severity[severity]`
- `fact_violation[status]` → `dim_status[status]`
- `fact_token_consumption[agent_id]` → `dim_agent[agent_id]`
- `fact_token_consumption[date]` → `dim_date[date]`
- `fact_runtime_event[agent_id]` → `dim_agent[agent_id]`
- `fact_design_finding[agent_id]` → `dim_agent[agent_id]`
- `dim_control[framework_id]` → `dim_framework[framework_id]`

Mark `dim_date` as a date table: **Modeling → Mark as date table** →
date column = `date`.

## Step 5 — What-if parameters

**Modeling → New parameter → Numeric range**, twice:

| Name | Min | Max | Increment | Default |
| ---: | ---:| ---:| ---:| ---:|
| `HourlyRateUSD` | 25 | 250 | 5 | 75 |
| `TeamCapacityHrsPerWeek` | 20 | 600 | 20 | 120 |

## Step 6 — Paste in the DAX measures

The fast path: install **Tabular Editor 2** (free), then
**External Tools → Tabular Editor** → paste each `.dax` file's content
into a new script and run.

The manual path: for each measure in `dax/01_risk_measures.dax` through
`dax/06_runtime_measures.dax`, **Home → New measure** in Power BI
Desktop, paste, give it the same name as the file header.

Create a `_Measures` table (Home → Enter Data → leave empty, name it
`_Measures`) and drag every measure onto it so the field list stays
clean.

## Step 7 — Build the pages

For each page-spec file under [`page_specs/`](page_specs/):

1. **Insert → New page** in Power BI Desktop.
2. Rename the page tab to match the spec title.
3. Drop in the visuals from the layout diagram (cards, matrices,
   charts).
4. Bind each visual to the measure named in the spec.
5. Apply conditional formatting where called out (color-from-field).
6. Add the slicers listed in the spec.

Order:
1. Executive Summary (cover)
2. Agent Risk Heat Map
3. Framework Compliance
4. Violations & Remediation
5. Token Consumption & Cost
6. Runtime Events
7. Design-Time Findings
8. FPA Effort & Capacity
9. Agent Drill-Through (mark page as drill-through target)

## Step 8 — Save and publish

`File → Save As → AI-Agent-Governance.pbix`. Then follow
[`docs/deployment.md`](docs/deployment.md) to push to Service.

## Estimated time

| Phase | Time |
| --- | --- |
| Data load + model + relationships | 8 min |
| Theme + parameters | 2 min |
| Paste DAX (Tabular Editor) | 5 min |
| Build all 9 pages | 15 min |
| **Total** | **30 min** |
