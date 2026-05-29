# AI Agent Governance — Leadership Dashboard (Power BI)

Plug-and-play Power BI leadership dashboard for governing **Microsoft
Copilot**, **Anthropic Claude**, and any other agentic AI workloads in
your portfolio. Covers design-time and runtime security, compliance
posture across OWASP LLM Top 10 / MITRE ATLAS / NIST AI RMF / EU AI Act
/ ISO 42001, token consumption + cost, and **Function-Point Analysis**
for remediation effort estimation.

## Three delivery paths

**Easiest — open the HTML dashboard.** This repo ships
**[`dashboard.html`](dashboard.html)** at the root — a single
self-contained file (58 KB). Double-click to open in any browser. Nine
tabbed pages, 16 interactive Plotly.js charts, all the same KPIs as the
Power BI version, computed from the same CSVs. No Power BI Desktop, no
server, no install.

**Fast path — open the bundled `.pbit` template.** This repo also ships
**[`AI-Agent-Governance.pbit`](AI-Agent-Governance.pbit)** at the root.
The template contains all 10 tables, 13 relationships, 74 DAX measures,
and one starter page. Open it in Power BI Desktop; when prompted for
the `DataFolder` parameter, paste the absolute path to the repo's
`data/` folder. The model materialises and you have a working skeleton
— then build out the remaining 8 pages using the page specs.

> The PBIT is generated from text by `scripts/build_pbit.py`. The
> format is finicky; see [`docs/pbit_caveats.md`](docs/pbit_caveats.md).
> If Power BI Desktop refuses the file, the manual build below is the
> reliable fallback.

**Reliable path — hand-build the PBIX in 30 minutes.** Every text
artifact needed to build a PBIX from scratch is in this repo: synthetic
data, DAX measures, Power Query M, theme JSON, and page-by-page layout
specs. Follow [`pbix_build_guide.md`](pbix_build_guide.md).

## What's inside

```
powerbi-agent-governance/
├── README.md                        # you are here
├── pbix_build_guide.md              # 30-minute step-by-step
├── data/                            # 10 CSVs — load via connect_csv.pq
│   ├── dim_agent.csv                # 60 synthetic agents (Copilot + Claude + others)
│   ├── dim_framework.csv            # OWASP / ATLAS / NIST / EU AI Act / ISO 42001
│   ├── dim_control.csv              # 36 controls across all 5 frameworks
│   ├── dim_severity.csv / dim_status.csv / dim_date.csv
│   ├── fact_violation.csv           # 700 rows
│   ├── fact_token_consumption.csv   # 10,800 rows (180 days × 60 agents)
│   ├── fact_runtime_event.csv       # 14,677 rows
│   ├── fact_design_finding.csv      # 200 rows
│   └── frameworks/                  # human-readable framework references
├── dax/                             # 6 .dax files — paste into Tabular Editor
│   ├── 01_risk_measures.dax         # composite Risk Score (0-100) + bucket
│   ├── 02_violation_measures.dax    # MTTR, SLA breach, aging buckets
│   ├── 03_token_measures.dax        # cost MoM%, anomaly flag, top consumers
│   ├── 04_compliance_measures.dax   # Compliance % per framework + heatmap
│   ├── 05_fpa_measures.dax          # Function-Point Analysis remediation effort + cost
│   └── 06_runtime_measures.dax      # block rate, attack-class counters
├── power_query/                     # M scripts
│   ├── connect_csv.pq               # default — load CSVs from a folder param
│   ├── connect_rest_api.pq          # production — pull from your governance REST API
│   └── date_dimension.pq            # standalone date table
├── themes/governance_theme.json     # real Power BI theme
├── page_specs/                      # 9 dashboard pages — layout + measures + slicers
├── docs/                            # data model ERD, refresh, RLS, deployment
└── scripts/                         # Python data generator
```

## Dashboard pages

1. **Executive Summary** — KPIs, top-10 risky agents, compliance per framework, cost trend.
2. **Agent Risk Heat Map** — matrix of agents × risk drivers, color scale 0-100.
3. **Framework Compliance** — coverage heat map across OWASP LLM Top 10, MITRE ATLAS, NIST AI RMF, EU AI Act, ISO 42001.
4. **Violations & Remediation** — open backlog, MTTR, SLA breach, aging buckets.
5. **Token Consumption & Cost** — per-agent cost, MoM growth, anomaly detection.
6. **Runtime Events** — attack timeline, block rate, per-class counters.
7. **Design-Time Findings** — code/config review issues before deploy.
8. **FPA Effort & Capacity Planning** — function-point estimation of remediation effort, weeks-to-clear with what-if hourly rate.
9. **Agent Drill-Through** — single-agent deep dive.

## Frameworks covered

| Framework | Controls included | Source |
| --- | --- | --- |
| **OWASP LLM Top 10 (2025)** | LLM01-LLM10 | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |
| **MITRE ATLAS** | 10 attack techniques | https://atlas.mitre.org/ |
| **NIST AI RMF 1.0** | Govern / Map / Measure / Manage controls | https://www.nist.gov/itl/ai-risk-management-framework |
| **EU AI Act** | Articles 9, 10, 13, 14, 15, 50 | https://artificialintelligenceact.eu/ |
| **ISO/IEC 42001:2023** | Clauses 8.2, 8.3, 8.4, 9.4 | https://www.iso.org/standard/81230.html |

## Function-Point Analysis (FPA) for remediation

Every open violation carries an `fpa_complexity` of `S` / `M` / `L` /
`XL`, mapped to function-point hours:

| Complexity | Hours |
| --- | ---: |
| S | 2 |
| M | 6 |
| L | 16 |
| XL | 40 |

Combined with a what-if `HourlyRateUSD` (default $75) and
`TeamCapacityHrsPerWeek` (default 120), the **FPA Effort & Capacity
Planning** page answers:

- Total estimated remediation cost (USD)
- Estimated weeks to clear the backlog at current team capacity
- Hours-by-framework / hours-by-business-unit splits
- Closed-hours velocity over last 7 / 30 days

DAX is in [`dax/05_fpa_measures.dax`](dax/05_fpa_measures.dax).

## Quickstart

```powershell
# 1. Generate data
git clone https://github.com/kumar1shailesh/PowerBI-Dashboard-Governance-and-security-for-AI-agents-across-the-....git
cd PowerBI-Dashboard-Governance-and-security-for-AI-agents-across-the-...
pip install -r scripts/requirements.txt
python scripts/generate_synthetic_data.py

# 2. Build the PBIX
# Open Power BI Desktop, follow pbix_build_guide.md (30 minutes).

# 3. Publish + schedule refresh
# Follow docs/deployment.md.
```

## Configurable data sources

The CSV connector is the demo path. To switch to a live source:

| Source kind | What to do |
| --- | --- |
| **CSV (default)** | Point the `DataFolder` parameter at your data drop. |
| **REST API** | Use [`power_query/connect_rest_api.pq`](power_query/connect_rest_api.pq); set `BaseUrl` + `ApiKey` parameters. |
| **Azure SQL / Synapse** | Replace the CSV queries with `Sql.Database(...)` and the same column names — the model and DAX are unchanged. |
| **Microsoft Defender for Cloud Apps** | Stream alerts via the Activity Log API into `fact_runtime_event`. |
| **Purview Compliance Manager** | Pull control assessments into `fact_violation`. |

## Open-source friendly

- Synthetic data generator is open source (MIT licence).
- Reference framework CSVs are derived from publicly available sources.
- Theme + DAX + M code are all plain text — diff-friendly in Git.

## Docs

- [`pbix_build_guide.md`](pbix_build_guide.md) — 30-minute walkthrough.
- [`docs/data_model.md`](docs/data_model.md) — star-schema ERD + relationships.
- [`docs/refresh_strategy.md`](docs/refresh_strategy.md) — cadence, incremental refresh, gateway.
- [`docs/rls_setup.md`](docs/rls_setup.md) — three personas with DAX filters.
- [`docs/deployment.md`](docs/deployment.md) — publish, schedule, RLS, embed.

## License

MIT
