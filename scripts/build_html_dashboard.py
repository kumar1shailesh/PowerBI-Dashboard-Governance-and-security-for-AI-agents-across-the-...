"""Generate a self-contained HTML dashboard from the same CSVs the PBIT uses.

Output: `dashboard.html` at the repo root. Double-click to open in any
browser — no server, no Power BI required. Uses Plotly.js via CDN.

Aggregations are computed server-side here (in Python) and embedded as
JSON so the page renders instantly without a JS-side number-crunch.

Run:
    python scripts/build_html_dashboard.py
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "dashboard.html"

TODAY = date(2026, 5, 30)               # locked to the synthetic data's "now"

THEME = {
    "primary":    "#1F4E79",
    "primary2":   "#2E75B6",
    "primary3":   "#5B9BD5",
    "critical":   "#C00000",
    "high":       "#E97132",
    "medium":     "#FFC000",
    "low":        "#2E75B6",
    "info":       "#7F7F7F",
    "compliant":  "#548235",
    "bg":         "#F4F6F9",
    "card_bg":    "#FFFFFF",
    "ink":        "#1F1F1F",
    "muted":      "#5B5B5B",
}
SEV_COLOR = {"Critical": THEME["critical"], "High": THEME["high"],
             "Medium": THEME["medium"], "Low": THEME["low"], "Info": THEME["info"]}
SEV_RANK = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Info": 0}
SEV_SLA = {"Critical": 3, "High": 7, "Medium": 30, "Low": 90, "Info": 365}


# ─────────────────────────────── load CSVs ──────────────────────────────────
def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def to_date(s: str) -> date | None:
    if not s:
        return None
    return date.fromisoformat(s[:10]) if s else None


def to_int(s: str, default: int = 0) -> int:
    try:
        return int(float(s)) if s not in (None, "") else default
    except (TypeError, ValueError):
        return default


def to_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s) if s not in (None, "") else default
    except (TypeError, ValueError):
        return default


def to_bool(s: str) -> bool:
    return str(s or "").lower() in {"true", "1", "yes"}


def main() -> None:
    agents = load(DATA / "dim_agent.csv")
    frameworks = load(DATA / "dim_framework.csv")
    controls = load(DATA / "dim_control.csv")
    violations = load(DATA / "fact_violation.csv")
    tokens = load(DATA / "fact_token_consumption.csv")
    runtime = load(DATA / "fact_runtime_event.csv")
    findings = load(DATA / "fact_design_finding.csv")

    print(f"loaded: agents={len(agents)} controls={len(controls)} "
          f"violations={len(violations)} tokens={len(tokens)} "
          f"runtime={len(runtime)} findings={len(findings)}")

    # ── PAGE 1 — Executive Summary ──────────────────────────────────────────
    open_v = [v for v in violations if v["status"] in ("open", "in_progress")]
    open_crit_high = [v for v in open_v if v["severity"] in ("Critical", "High")]
    sla_breaches = [v for v in open_v
                    if to_date(v["remediation_due_date"]) and to_date(v["remediation_due_date"]) < TODAY]

    cost_mtd = sum(to_float(t["cost_usd"]) for t in tokens
                   if to_date(t["date"]) and to_date(t["date"]) >= date(TODAY.year, TODAY.month, 1))
    cost_ytd = sum(to_float(t["cost_usd"]) for t in tokens
                   if to_date(t["date"]) and to_date(t["date"]) >= date(TODAY.year, 1, 1))

    runtime_30d = [r for r in runtime
                   if to_date(r["event_ts"][:10]) and to_date(r["event_ts"][:10]) >= TODAY - timedelta(days=30)]
    blocked = sum(1 for r in runtime_30d if to_bool(r["blocked"]))
    block_rate = blocked / len(runtime_30d) if runtime_30d else 0.0

    # Per-agent risk score (composite, 0-100). Same recipe as the DAX.
    agent_risk = []
    runtime_by_agent = defaultdict(int)
    for r in runtime_30d:
        if r["event_type"] in ("prompt_injection_attempt", "jailbreak_attempt",
                                "tool_misuse_blocked", "system_prompt_disclosed"):
            runtime_by_agent[r["agent_id"]] += 1
    open_v_by_agent_sev = defaultdict(lambda: {"crit_high": 0, "sla": 0})
    for v in open_v:
        a = v["agent_id"]
        if v["severity"] in ("Critical", "High"):
            open_v_by_agent_sev[a]["crit_high"] += 1
        due = to_date(v["remediation_due_date"])
        if due and due < TODAY:
            open_v_by_agent_sev[a]["sla"] += 1
    excessive_by_agent = defaultdict(int)
    for f in findings:
        if f["status"] in ("open", "in_progress") and (
            "wildcard" in f["title"] or "human-in-the-loop" in f["title"]
        ):
            excessive_by_agent[f["agent_id"]] += 1

    crit_mult = {"Critical": 1.0, "High": 0.7, "Medium": 0.4, "Low": 0.2}
    for a in agents:
        aid = a["agent_id"]
        ocrh = min(open_v_by_agent_sev[aid]["crit_high"], 10) / 10
        sla = min(open_v_by_agent_sev[aid]["sla"], 5) / 5
        atk = min(runtime_by_agent[aid], 200) / 200
        cm = crit_mult.get(a["criticality"], 0.4)
        ex = min(excessive_by_agent[aid], 5) / 5
        tools_ind = 1 if to_int(a["tools_count"]) > 6 else 0
        score = 100 * (0.35 * ocrh + 0.25 * sla + 0.15 * atk
                       + 0.15 * cm + 0.05 * ex + 0.05 * tools_ind)
        agent_risk.append({
            "agent_id": aid, "name": a["name"], "platform": a["platform"],
            "business_unit": a["business_unit"], "criticality": a["criticality"],
            "score": round(score, 1),
            "open_ch": open_v_by_agent_sev[aid]["crit_high"],
            "sla": open_v_by_agent_sev[aid]["sla"],
            "attempts": runtime_by_agent[aid],
            "excessive": excessive_by_agent[aid],
            "tools_count": to_int(a["tools_count"]),
        })
    agent_risk.sort(key=lambda x: x["score"], reverse=True)
    risk_critical_agents = sum(1 for x in agent_risk if x["score"] >= 75)

    # ── Compliance % per framework ─────────────────────────────────────────
    open_v_pairs = {(v["agent_id"], v["control_id"]) for v in open_v}
    fw_compliance = []
    for fw in frameworks:
        fw_id = fw["framework_id"]
        fw_controls = [c["control_id"] for c in controls if c["framework_id"] == fw_id]
        total = len(agents) * len(fw_controls)
        bad = sum(1 for (a, c) in open_v_pairs if c in fw_controls)
        comp = (total - bad) / total if total else 0
        fw_compliance.append({"framework_id": fw_id, "name": fw["name"],
                              "compliance": round(comp * 100, 1)})

    # ── Severity distribution of open violations ───────────────────────────
    sev_counts = Counter(v["severity"] for v in open_v)
    open_by_sev = [{"severity": s, "count": sev_counts.get(s, 0),
                    "color": SEV_COLOR[s]}
                   for s in ("Critical", "High", "Medium", "Low", "Info")]

    # ── Daily cost trend (last 90 days) ────────────────────────────────────
    cost_by_day = defaultdict(float)
    for t in tokens:
        d = to_date(t["date"])
        if d and d >= TODAY - timedelta(days=90):
            cost_by_day[d.isoformat()] += to_float(t["cost_usd"])
    cost_series = sorted(cost_by_day.items())

    # ── PAGE 4 — Aging buckets + MTTR ──────────────────────────────────────
    aging = {"0-7d": 0, "8-30d": 0, "31-90d": 0, "91d+": 0}
    for v in open_v:
        d = to_date(v["detected_date"])
        if not d:
            continue
        days = (TODAY - d).days
        if days <= 7: aging["0-7d"] += 1
        elif days <= 30: aging["8-30d"] += 1
        elif days <= 90: aging["31-90d"] += 1
        else: aging["91d+"] += 1

    rem = [v for v in violations if v["status"] == "remediated"
           and v["remediation_completed_date"] and v["detected_date"]]
    def days_between(a, b):
        return (to_date(b) - to_date(a)).days if (to_date(a) and to_date(b)) else None
    mttr_all = [days_between(v["detected_date"], v["remediation_completed_date"]) for v in rem]
    mttr_all = [d for d in mttr_all if d is not None]
    mttr_crit = [days_between(v["detected_date"], v["remediation_completed_date"]) for v in rem if v["severity"] == "Critical"]
    mttr_crit = [d for d in mttr_crit if d is not None]
    mttr = round(statistics.mean(mttr_all), 1) if mttr_all else None
    mttr_critical = round(statistics.mean(mttr_crit), 1) if mttr_crit else None

    status_counts = Counter(v["status"] for v in violations)

    # Pageable list of open violations (top 50 by severity then age)
    agent_name_by_id = {a["agent_id"]: a["name"] for a in agents}
    control_title_by_id = {c["control_id"]: c["title"] for c in controls}
    open_list = []
    for v in open_v:
        d = to_date(v["detected_date"])
        due = to_date(v["remediation_due_date"])
        overdue = (TODAY - due).days if (due and due < TODAY) else 0
        open_list.append({
            "violation_id": v["violation_id"],
            "agent": agent_name_by_id.get(v["agent_id"], v["agent_id"]),
            "control": control_title_by_id.get(v["control_id"], v["control_id"]),
            "severity": v["severity"],
            "detected_date": v["detected_date"],
            "due_date": v["remediation_due_date"],
            "status": v["status"],
            "days_overdue": overdue,
        })
    open_list.sort(key=lambda x: (-SEV_RANK[x["severity"]], -x["days_overdue"]))
    open_list = open_list[:50]

    # ── PAGE 5 — Token consumption ─────────────────────────────────────────
    cost_by_agent = defaultdict(float)
    cost_by_model = defaultdict(float)
    for t in tokens:
        cost_by_agent[t["agent_id"]] += to_float(t["cost_usd"])
        cost_by_model[t["model"]] += to_float(t["cost_usd"])
    top_agents_cost = sorted(
        [(agent_name_by_id.get(a, a), c) for a, c in cost_by_agent.items()],
        key=lambda x: x[1], reverse=True
    )[:15]
    by_model = sorted(cost_by_model.items(), key=lambda x: x[1], reverse=True)

    # ── PAGE 6 — Runtime events ────────────────────────────────────────────
    events_by_type = Counter(r["event_type"] for r in runtime_30d)
    events_by_day = defaultdict(int)
    for r in runtime_30d:
        d = to_date(r["event_ts"][:10])
        if d:
            events_by_day[d.isoformat()] += 1
    runtime_series = sorted(events_by_day.items())

    # ── PAGE 7 — Design-time findings ──────────────────────────────────────
    open_design = [f for f in findings if f["status"] in ("open", "in_progress")]
    design_sev_counts = Counter(f["severity"] for f in open_design)
    design_titles = Counter(f["title"] for f in open_design)

    # ── PAGE 8 — FPA ───────────────────────────────────────────────────────
    fpa_hours_map = {"S": 2, "M": 6, "L": 16, "XL": 40}
    fpa_total = sum(fpa_hours_map.get(v["fpa_complexity"], 4) for v in open_v)
    fpa_critical = sum(fpa_hours_map.get(v["fpa_complexity"], 4)
                       for v in open_v if v["severity"] == "Critical")

    # FPA hours by framework
    ctrl_to_fw = {c["control_id"]: c["framework_id"] for c in controls}
    fw_name = {f["framework_id"]: f["name"] for f in frameworks}
    fpa_by_fw = defaultdict(int)
    for v in open_v:
        fw = ctrl_to_fw.get(v["control_id"])
        if fw:
            fpa_by_fw[fw_name[fw]] += fpa_hours_map.get(v["fpa_complexity"], 4)
    fpa_by_fw_list = sorted(fpa_by_fw.items(), key=lambda x: x[1], reverse=True)

    # FPA by BU
    agent_bu = {a["agent_id"]: a["business_unit"] for a in agents}
    fpa_by_bu = defaultdict(int)
    for v in open_v:
        bu = agent_bu.get(v["agent_id"])
        if bu:
            fpa_by_bu[bu] += fpa_hours_map.get(v["fpa_complexity"], 4)
    fpa_by_bu_list = sorted(fpa_by_bu.items(), key=lambda x: x[1], reverse=True)

    # ── Bundle into a single JS payload ────────────────────────────────────
    payload = {
        "summary": {
            "total_agents": len(agents),
            "critical_agents": risk_critical_agents,
            "open_violations": len(open_v),
            "sla_breaches": len(sla_breaches),
            "cost_mtd": round(cost_mtd, 2),
            "cost_ytd": round(cost_ytd, 2),
            "block_rate": round(block_rate * 100, 1),
            "open_critical_high": len(open_crit_high),
            "mttr": mttr,
            "mttr_critical": mttr_critical,
            "fpa_hours": fpa_total,
            "fpa_critical": fpa_critical,
            "today": TODAY.isoformat(),
        },
        "agents":            agent_risk,
        "fw_compliance":     fw_compliance,
        "open_by_sev":       open_by_sev,
        "cost_series":       cost_series,
        "aging":             aging,
        "status_counts":     status_counts,
        "open_list":         open_list,
        "top_agents_cost":   [{"agent": a, "cost": round(c, 2)} for a, c in top_agents_cost],
        "by_model":          [{"model": m, "cost": round(c, 2)} for m, c in by_model],
        "events_by_type":    events_by_type,
        "runtime_series":    runtime_series,
        "design_sev_counts": design_sev_counts,
        "design_titles":     design_titles.most_common(10),
        "fpa_by_fw":         fpa_by_fw_list,
        "fpa_by_bu":         fpa_by_bu_list,
        "theme":             THEME,
        "sev_color":         SEV_COLOR,
    }

    html = render(payload)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUTPUT.name} ({OUTPUT.stat().st_size // 1024} KB)")


def render(payload: dict) -> str:
    """Build the final HTML. Plotly.js loaded from CDN, all logic inline."""
    data_json = json.dumps(payload, default=str)
    return _TEMPLATE.replace("__DATA_JSON__", data_json)


# ─────────────────────────────── template ───────────────────────────────────
_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Agent Governance — Leadership Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      --primary: #1F4E79;
      --primary2: #2E75B6;
      --bg: #F4F6F9;
      --card-bg: #FFFFFF;
      --ink: #1F1F1F;
      --muted: #5B5B5B;
      --critical: #C00000;
      --high: #E97132;
      --medium: #FFC000;
      --low: #2E75B6;
      --info: #7F7F7F;
      --compliant: #548235;
      --border: #E2E5EA;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Segoe UI", system-ui, sans-serif;
           background: var(--bg); color: var(--ink); }
    header { background: var(--primary); color: #fff; padding: 16px 28px;
             display: flex; align-items: center; gap: 16px;
             box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    header h1 { margin: 0; font-size: 18px; font-weight: 600; flex: 1; }
    header .meta { font-size: 12px; opacity: 0.85; }
    nav { background: #fff; padding: 0 16px; border-bottom: 1px solid var(--border);
          display: flex; flex-wrap: wrap; gap: 4px; position: sticky; top: 0;
          z-index: 10; box-shadow: 0 1px 0 rgba(0,0,0,0.04); }
    nav button { background: transparent; border: 0; padding: 12px 14px;
                 font-family: inherit; font-size: 13px; color: var(--muted);
                 cursor: pointer; border-bottom: 3px solid transparent;
                 transition: all 0.15s ease; }
    nav button:hover { color: var(--primary); }
    nav button.active { color: var(--primary); border-bottom-color: var(--primary);
                        font-weight: 600; }
    main { padding: 20px 24px 60px; max-width: 1600px; margin: 0 auto; }
    .page { display: none; }
    .page.active { display: block; }
    .page h2 { margin: 0 0 16px; color: var(--primary); font-weight: 600; font-size: 22px; }
    .page .subtitle { color: var(--muted); margin-bottom: 20px; font-size: 13px; }
    .grid { display: grid; gap: 16px; }
    .grid-5 { grid-template-columns: repeat(5, 1fr); }
    .grid-4 { grid-template-columns: repeat(4, 1fr); }
    .grid-2 { grid-template-columns: 1fr 1fr; }
    @media (max-width: 1100px) {
      .grid-5, .grid-4 { grid-template-columns: repeat(2, 1fr); }
      .grid-2 { grid-template-columns: 1fr; }
    }
    .card { background: var(--card-bg); border: 1px solid var(--border);
            border-radius: 8px; padding: 16px; }
    .card h3 { margin: 0 0 4px; font-size: 12px; color: var(--muted);
               font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .card .num { font-size: 32px; font-weight: 600; color: var(--primary);
                 line-height: 1.2; }
    .card .num.alert { color: var(--critical); }
    .card .sub { font-size: 11px; color: var(--muted); margin-top: 4px; }
    .chart { background: var(--card-bg); border: 1px solid var(--border);
             border-radius: 8px; padding: 12px; min-height: 320px; }
    .chart h3 { margin: 0 0 8px; font-size: 14px; color: var(--primary);
                font-weight: 600; }
    table.data { width: 100%; border-collapse: collapse; font-size: 12px; }
    table.data th { background: var(--bg); padding: 8px;
                    text-align: left; font-weight: 600; color: var(--muted);
                    border-bottom: 2px solid var(--border); }
    table.data td { padding: 6px 8px; border-bottom: 1px solid var(--border); }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 10px;
            font-size: 11px; font-weight: 600; color: #fff; }
    .pill.Critical { background: var(--critical); }
    .pill.High     { background: var(--high); color: #fff; }
    .pill.Medium   { background: var(--medium); color: #1F1F1F; }
    .pill.Low      { background: var(--low); }
    .pill.Info     { background: var(--info); }
    .footnote { color: var(--muted); font-size: 11px; margin-top: 28px;
                text-align: center; }
    .footnote a { color: var(--primary); }
    .heatmap-cell { width: 22px; height: 22px; display: inline-block;
                    margin: 1px; border-radius: 2px; vertical-align: middle; }
  </style>
</head>
<body>

<header>
  <div>
    <h1>AI Agent Governance — Leadership Dashboard</h1>
    <div class="meta">Synthetic demo data · same model as the Power BI PBIT</div>
  </div>
</header>

<nav id="nav">
  <button data-page="executive">Executive Summary</button>
  <button data-page="risk">Agent Risk</button>
  <button data-page="framework">Framework Compliance</button>
  <button data-page="violations">Violations &amp; Remediation</button>
  <button data-page="tokens">Token Consumption</button>
  <button data-page="runtime">Runtime Events</button>
  <button data-page="design">Design-Time Findings</button>
  <button data-page="fpa">FPA Capacity</button>
  <button data-page="drill">Agent Drill-Through</button>
</nav>

<main>

<!-- PAGE 1 — EXECUTIVE SUMMARY -->
<section id="executive" class="page active">
  <h2>Executive Summary</h2>
  <p class="subtitle">Board-level view across the agent portfolio.</p>
  <div class="grid grid-5">
    <div class="card"><h3>Total Agents</h3><div class="num" id="kpi-total"></div></div>
    <div class="card"><h3>Critical Risk Agents</h3><div class="num alert" id="kpi-critical"></div></div>
    <div class="card"><h3>Open Violations</h3><div class="num" id="kpi-open"></div></div>
    <div class="card"><h3>SLA Breaches</h3><div class="num alert" id="kpi-sla"></div></div>
    <div class="card"><h3>Cost MTD (USD)</h3><div class="num" id="kpi-cost"></div></div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="chart"><h3>Compliance % by framework</h3><div id="chart-compliance"></div></div>
    <div class="chart"><h3>Top 10 risky agents</h3><div id="chart-top-risky"></div></div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="chart"><h3>Open violations by severity</h3><div id="chart-open-sev"></div></div>
    <div class="chart"><h3>Token cost (last 90 days)</h3><div id="chart-cost-trend"></div></div>
  </div>
</section>

<!-- PAGE 2 — AGENT RISK -->
<section id="risk" class="page">
  <h2>Agent Risk Heatmap</h2>
  <p class="subtitle">One row per agent. Higher score = higher risk. Sort by clicking column headers in Power BI.</p>
  <div class="chart" style="padding:0">
    <table class="data" id="risk-table"></table>
  </div>
</section>

<!-- PAGE 3 — FRAMEWORK COMPLIANCE -->
<section id="framework" class="page">
  <h2>Framework Compliance</h2>
  <p class="subtitle">Coverage across OWASP LLM Top 10 · MITRE ATLAS · NIST AI RMF · EU AI Act · ISO 42001.</p>
  <div class="grid grid-5" id="fw-gauges"></div>
  <div class="chart" style="margin-top:16px">
    <h3>Compliance gauge per framework</h3>
    <div id="chart-fw-bars"></div>
  </div>
</section>

<!-- PAGE 4 — VIOLATIONS & REMEDIATION -->
<section id="violations" class="page">
  <h2>Violations &amp; Remediation</h2>
  <p class="subtitle">Operational backlog · age distribution · status mix.</p>
  <div class="grid grid-5">
    <div class="card"><h3>Open</h3><div class="num" id="kpi-open2"></div></div>
    <div class="card"><h3>MTTR (days)</h3><div class="num" id="kpi-mttr"></div></div>
    <div class="card"><h3>MTTR Critical (days)</h3><div class="num alert" id="kpi-mttr-crit"></div></div>
    <div class="card"><h3>SLA breach %</h3><div class="num alert" id="kpi-sla-pct"></div></div>
    <div class="card"><h3>Block rate %</h3><div class="num" id="kpi-block"></div></div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="chart"><h3>Aging buckets</h3><div id="chart-aging"></div></div>
    <div class="chart"><h3>Status distribution (all violations)</h3><div id="chart-status"></div></div>
  </div>
  <div class="chart" style="margin-top:16px">
    <h3>Open violations — top 50 by severity × overdue</h3>
    <div style="max-height:380px; overflow:auto">
      <table class="data" id="violations-table"></table>
    </div>
  </div>
</section>

<!-- PAGE 5 — TOKEN CONSUMPTION -->
<section id="tokens" class="page">
  <h2>Token Consumption &amp; Cost</h2>
  <p class="subtitle">Per-agent + per-model cost telemetry.</p>
  <div class="grid grid-4">
    <div class="card"><h3>Cost MTD</h3><div class="num" id="kpi-cost-mtd"></div></div>
    <div class="card"><h3>Cost YTD</h3><div class="num" id="kpi-cost-ytd"></div></div>
    <div class="card"><h3>Daily cost trend</h3><div class="num" id="kpi-cost-trend"></div></div>
    <div class="card"><h3>Top consumer</h3><div class="num" id="kpi-top-consumer" style="font-size:18px"></div></div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="chart"><h3>Daily cost (last 90 days)</h3><div id="chart-cost-daily"></div></div>
    <div class="chart"><h3>Cost by model</h3><div id="chart-cost-model"></div></div>
  </div>
  <div class="chart" style="margin-top:16px">
    <h3>Top 15 agents by cost</h3>
    <div id="chart-cost-agents"></div>
  </div>
</section>

<!-- PAGE 6 — RUNTIME EVENTS -->
<section id="runtime" class="page">
  <h2>Runtime Events</h2>
  <p class="subtitle">Live-defence posture. Last 30 days.</p>
  <div class="grid grid-4">
    <div class="card"><h3>Events 30D</h3><div class="num" id="kpi-runtime-total"></div></div>
    <div class="card"><h3>Blocked 30D</h3><div class="num" id="kpi-runtime-blocked"></div></div>
    <div class="card"><h3>Block rate</h3><div class="num" id="kpi-runtime-block-rate"></div></div>
    <div class="card"><h3>Prompt injection attempts</h3><div class="num alert" id="kpi-pi"></div></div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="chart"><h3>Events over time</h3><div id="chart-runtime-trend"></div></div>
    <div class="chart"><h3>Events by type</h3><div id="chart-runtime-type"></div></div>
  </div>
</section>

<!-- PAGE 7 — DESIGN-TIME FINDINGS -->
<section id="design" class="page">
  <h2>Design-Time Findings</h2>
  <p class="subtitle">Code- and config-level issues caught during agent review.</p>
  <div class="grid grid-2">
    <div class="chart"><h3>Open by severity</h3><div id="chart-design-sev"></div></div>
    <div class="chart"><h3>Top 10 finding titles</h3><div id="chart-design-titles"></div></div>
  </div>
</section>

<!-- PAGE 8 — FPA CAPACITY -->
<section id="fpa" class="page">
  <h2>FPA Effort &amp; Capacity Planning</h2>
  <p class="subtitle">Function-Point Analysis · what-if hourly rate &amp; team capacity.</p>
  <div class="grid grid-5">
    <div class="card"><h3>Open backlog</h3><div class="num" id="kpi-fpa-open"></div></div>
    <div class="card"><h3>FPA hours total</h3><div class="num" id="kpi-fpa-hours"></div></div>
    <div class="card"><h3>FPA hours Critical</h3><div class="num alert" id="kpi-fpa-crit"></div></div>
    <div class="card"><h3>Est. cost @ <input id="rate" type="number" value="75" min="25" max="250" step="5" style="width:48px;font:inherit"/> /h</h3><div class="num" id="kpi-fpa-cost"></div></div>
    <div class="card"><h3>Weeks @ <input id="cap" type="number" value="120" min="20" max="600" step="20" style="width:64px;font:inherit"/> h/wk</h3><div class="num" id="kpi-fpa-weeks"></div></div>
  </div>
  <div class="grid grid-2" style="margin-top:16px">
    <div class="chart"><h3>FPA hours by framework</h3><div id="chart-fpa-fw"></div></div>
    <div class="chart"><h3>FPA hours by business unit</h3><div id="chart-fpa-bu"></div></div>
  </div>
</section>

<!-- PAGE 9 — DRILL-THROUGH -->
<section id="drill" class="page">
  <h2>Agent Drill-Through</h2>
  <p class="subtitle">Pick an agent to inspect.</p>
  <select id="drill-select" style="margin-bottom:16px; padding:6px 10px; font:inherit"></select>
  <div id="drill-content"></div>
</section>

<div class="footnote">
  Generated from synthetic data with the same model as
  <code>AI-Agent-Governance.pbit</code>. Source CSVs + DAX + page specs at
  <a href="https://github.com/kumar1shailesh/PowerBI-Dashboard-Governance-and-security-for-AI-agents-across-the-...">github.com/kumar1shailesh/PowerBI-Dashboard-Governance-...</a>
</div>

</main>

<script>
const PAYLOAD = __DATA_JSON__;
const T = PAYLOAD.theme;
const SC = PAYLOAD.sev_color;

const fmtUSD = n => "$" + (n || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
const fmtUSD0 = n => "$" + (n || 0).toLocaleString(undefined, {maximumFractionDigits: 0});
const fmtInt = n => (n || 0).toLocaleString();

// ─── tabs ─────────────────────────────────────────────────────────────────
document.querySelectorAll("#nav button").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll("#nav button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.page).classList.add("active");
    setTimeout(() => window.dispatchEvent(new Event("resize")), 50);
  };
});
document.querySelector("#nav button").classList.add("active");

const baseLayout = {
  paper_bgcolor: T.card_bg,
  plot_bgcolor: T.card_bg,
  font: { family: "Segoe UI, system-ui, sans-serif", color: T.ink, size: 11 },
  margin: { l: 60, r: 16, t: 28, b: 50 },
};

// ─── PAGE 1 — Executive Summary ───────────────────────────────────────────
const s = PAYLOAD.summary;
document.getElementById("kpi-total").textContent    = fmtInt(s.total_agents);
document.getElementById("kpi-critical").textContent = fmtInt(s.critical_agents);
document.getElementById("kpi-open").textContent     = fmtInt(s.open_violations);
document.getElementById("kpi-sla").textContent      = fmtInt(s.sla_breaches);
document.getElementById("kpi-cost").textContent     = fmtUSD0(s.cost_mtd);

Plotly.newPlot("chart-compliance", [{
  type: "bar", orientation: "h",
  x: PAYLOAD.fw_compliance.map(f => f.compliance),
  y: PAYLOAD.fw_compliance.map(f => f.name),
  marker: { color: PAYLOAD.fw_compliance.map(f => f.compliance >= 90 ? T.compliant : f.compliance >= 70 ? T.medium : T.critical) },
  text: PAYLOAD.fw_compliance.map(f => f.compliance + "%"),
  textposition: "auto",
}], {...baseLayout, xaxis: {range: [0, 100], title: "compliance %"}, margin: {...baseLayout.margin, l: 180}}, {displayModeBar: false, responsive: true});

const top10 = PAYLOAD.agents.slice(0, 10);
Plotly.newPlot("chart-top-risky", [{
  type: "bar", orientation: "h",
  x: top10.map(a => a.score).reverse(),
  y: top10.map(a => a.name).reverse(),
  marker: { color: top10.map(a => a.score >= 75 ? T.critical : a.score >= 50 ? T.high : T.medium).reverse() },
  text: top10.map(a => a.score.toFixed(1)).reverse(),
  textposition: "auto",
}], {...baseLayout, xaxis: { title: "risk score (0-100)"}, margin: {...baseLayout.margin, l: 160}}, {displayModeBar: false, responsive: true});

Plotly.newPlot("chart-open-sev", [{
  type: "pie", hole: 0.5,
  labels: PAYLOAD.open_by_sev.map(x => x.severity),
  values: PAYLOAD.open_by_sev.map(x => x.count),
  marker: { colors: PAYLOAD.open_by_sev.map(x => x.color) },
  textinfo: "label+value",
}], baseLayout, {displayModeBar: false, responsive: true});

Plotly.newPlot("chart-cost-trend", [{
  type: "scatter", mode: "lines",
  x: PAYLOAD.cost_series.map(d => d[0]),
  y: PAYLOAD.cost_series.map(d => d[1]),
  line: { color: T.primary, width: 2 }, fill: "tozeroy", fillcolor: T.primary3 + "33",
}], {...baseLayout, yaxis: {title: "USD/day"}}, {displayModeBar: false, responsive: true});

// ─── PAGE 2 — Risk table ───────────────────────────────────────────────────
const riskHead = ["#", "Agent", "Platform", "BU", "Criticality", "Score", "C/H Open", "SLA", "Attempts 30D"];
const riskRows = PAYLOAD.agents.map((a, i) => `
  <tr>
    <td>${i+1}</td>
    <td>${a.name}</td>
    <td>${a.platform}</td>
    <td>${a.business_unit}</td>
    <td>${a.criticality}</td>
    <td><span class="pill ${a.score >= 75 ? 'Critical' : a.score >= 50 ? 'High' : a.score >= 25 ? 'Medium' : 'Low'}">${a.score.toFixed(1)}</span></td>
    <td>${a.open_ch}</td>
    <td>${a.sla}</td>
    <td>${a.attempts}</td>
  </tr>`).join("");
document.getElementById("risk-table").innerHTML =
  `<thead><tr>${riskHead.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${riskRows}</tbody>`;

// ─── PAGE 3 — Framework compliance ─────────────────────────────────────────
const fwHtml = PAYLOAD.fw_compliance.map(f =>
  `<div class="card" style="text-align:center">
     <h3>${f.name.replace(/\\\(.*\\\)/, "").trim()}</h3>
     <div class="num" style="color: ${f.compliance >= 90 ? T.compliant : f.compliance >= 70 ? T.medium : T.critical}">${f.compliance}%</div>
   </div>`).join("");
document.getElementById("fw-gauges").innerHTML = fwHtml;

Plotly.newPlot("chart-fw-bars", [{
  type: "bar",
  x: PAYLOAD.fw_compliance.map(f => f.name),
  y: PAYLOAD.fw_compliance.map(f => f.compliance),
  marker: { color: PAYLOAD.fw_compliance.map(f => f.compliance >= 90 ? T.compliant : f.compliance >= 70 ? T.medium : T.critical) },
  text: PAYLOAD.fw_compliance.map(f => f.compliance + "%"),
  textposition: "auto",
}], {...baseLayout, yaxis: { title: "compliance %", range: [0, 100] }}, {displayModeBar: false, responsive: true});

// ─── PAGE 4 — Violations & Remediation ─────────────────────────────────────
document.getElementById("kpi-open2").textContent      = fmtInt(s.open_violations);
document.getElementById("kpi-mttr").textContent       = s.mttr ?? "—";
document.getElementById("kpi-mttr-crit").textContent  = s.mttr_critical ?? "—";
document.getElementById("kpi-sla-pct").textContent    = s.open_violations ? Math.round(s.sla_breaches / s.open_violations * 100) + "%" : "0%";
document.getElementById("kpi-block").textContent      = s.block_rate + "%";

Plotly.newPlot("chart-aging", [{
  type: "bar",
  x: Object.keys(PAYLOAD.aging),
  y: Object.values(PAYLOAD.aging),
  marker: { color: [T.compliant, T.medium, T.high, T.critical] },
  text: Object.values(PAYLOAD.aging),
  textposition: "auto",
}], {...baseLayout, yaxis: { title: "open violations" }}, {displayModeBar: false, responsive: true});

const statusLabels = Object.keys(PAYLOAD.status_counts);
Plotly.newPlot("chart-status", [{
  type: "pie", hole: 0.5,
  labels: statusLabels,
  values: statusLabels.map(k => PAYLOAD.status_counts[k]),
  marker: { colors: [T.critical, T.high, T.compliant, "#7030A0", T.info] },
}], baseLayout, {displayModeBar: false, responsive: true});

const vHead = ["ID", "Agent", "Control", "Sev", "Detected", "Due", "Status", "Overdue (days)"];
const vRows = PAYLOAD.open_list.map(v => `
  <tr>
    <td>${v.violation_id}</td><td>${v.agent}</td><td>${v.control}</td>
    <td><span class="pill ${v.severity}">${v.severity}</span></td>
    <td>${v.detected_date}</td><td>${v.due_date}</td>
    <td>${v.status}</td>
    <td style="color:${v.days_overdue > 0 ? T.critical : T.muted}">${v.days_overdue}</td>
  </tr>`).join("");
document.getElementById("violations-table").innerHTML =
  `<thead><tr>${vHead.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${vRows}</tbody>`;

// ─── PAGE 5 — Token consumption ────────────────────────────────────────────
document.getElementById("kpi-cost-mtd").textContent = fmtUSD0(s.cost_mtd);
document.getElementById("kpi-cost-ytd").textContent = fmtUSD0(s.cost_ytd);
const last = PAYLOAD.cost_series.length ? PAYLOAD.cost_series[PAYLOAD.cost_series.length - 1][1] : 0;
document.getElementById("kpi-cost-trend").textContent = fmtUSD0(last);
document.getElementById("kpi-top-consumer").textContent = PAYLOAD.top_agents_cost[0] ? PAYLOAD.top_agents_cost[0].agent : "—";

Plotly.newPlot("chart-cost-daily", [{
  type: "scatter", mode: "lines",
  x: PAYLOAD.cost_series.map(d => d[0]),
  y: PAYLOAD.cost_series.map(d => d[1]),
  line: { color: T.primary, width: 2 }, fill: "tozeroy", fillcolor: T.primary3 + "33",
}], {...baseLayout, yaxis: { title: "USD/day" }}, {displayModeBar: false, responsive: true});

Plotly.newPlot("chart-cost-model", [{
  type: "pie", hole: 0.4,
  labels: PAYLOAD.by_model.map(m => m.model),
  values: PAYLOAD.by_model.map(m => m.cost),
}], baseLayout, {displayModeBar: false, responsive: true});

Plotly.newPlot("chart-cost-agents", [{
  type: "bar", orientation: "h",
  x: PAYLOAD.top_agents_cost.map(a => a.cost).reverse(),
  y: PAYLOAD.top_agents_cost.map(a => a.agent).reverse(),
  marker: { color: T.primary2 },
  text: PAYLOAD.top_agents_cost.map(a => fmtUSD0(a.cost)).reverse(),
  textposition: "auto",
}], {...baseLayout, xaxis: { title: "USD" }, margin: {...baseLayout.margin, l: 180}}, {displayModeBar: false, responsive: true});

// ─── PAGE 6 — Runtime events ───────────────────────────────────────────────
const totalRuntime = Object.values(PAYLOAD.events_by_type).reduce((a,b) => a+b, 0);
const piAttempts = PAYLOAD.events_by_type.prompt_injection_attempt || 0;
const blocked30 = Math.round(totalRuntime * s.block_rate / 100);
document.getElementById("kpi-runtime-total").textContent       = fmtInt(totalRuntime);
document.getElementById("kpi-runtime-blocked").textContent     = fmtInt(blocked30);
document.getElementById("kpi-runtime-block-rate").textContent  = s.block_rate + "%";
document.getElementById("kpi-pi").textContent                  = fmtInt(piAttempts);

Plotly.newPlot("chart-runtime-trend", [{
  type: "scatter", mode: "lines",
  x: PAYLOAD.runtime_series.map(d => d[0]),
  y: PAYLOAD.runtime_series.map(d => d[1]),
  line: { color: T.primary, width: 2 }, fill: "tozeroy", fillcolor: T.primary3 + "33",
}], {...baseLayout, yaxis: { title: "events/day" }}, {displayModeBar: false, responsive: true});

const rt = Object.entries(PAYLOAD.events_by_type).sort((a, b) => b[1] - a[1]);
Plotly.newPlot("chart-runtime-type", [{
  type: "bar", orientation: "h",
  x: rt.map(e => e[1]).reverse(),
  y: rt.map(e => e[0]).reverse(),
  marker: { color: T.primary2 },
}], {...baseLayout, margin: {...baseLayout.margin, l: 200} }, {displayModeBar: false, responsive: true});

// ─── PAGE 7 — Design-time findings ─────────────────────────────────────────
const designSev = Object.entries(PAYLOAD.design_sev_counts);
Plotly.newPlot("chart-design-sev", [{
  type: "pie", hole: 0.5,
  labels: designSev.map(e => e[0]),
  values: designSev.map(e => e[1]),
  marker: { colors: designSev.map(e => SC[e[0]] || T.muted) },
}], baseLayout, {displayModeBar: false, responsive: true});

Plotly.newPlot("chart-design-titles", [{
  type: "bar", orientation: "h",
  x: PAYLOAD.design_titles.map(t => t[1]).reverse(),
  y: PAYLOAD.design_titles.map(t => t[0]).reverse(),
  marker: { color: T.primary2 },
  text: PAYLOAD.design_titles.map(t => t[1]).reverse(),
  textposition: "auto",
}], {...baseLayout, margin: {...baseLayout.margin, l: 260}}, {displayModeBar: false, responsive: true});

// ─── PAGE 8 — FPA capacity (interactive) ───────────────────────────────────
function updateFpa() {
  const rate = +document.getElementById("rate").value || 75;
  const cap = +document.getElementById("cap").value || 120;
  document.getElementById("kpi-fpa-open").textContent  = fmtInt(s.open_violations);
  document.getElementById("kpi-fpa-hours").textContent = fmtInt(s.fpa_hours);
  document.getElementById("kpi-fpa-crit").textContent  = fmtInt(s.fpa_critical);
  document.getElementById("kpi-fpa-cost").textContent  = fmtUSD0(s.fpa_hours * rate);
  document.getElementById("kpi-fpa-weeks").textContent = (s.fpa_hours / cap).toFixed(1) + " wks";
}
document.getElementById("rate").oninput = updateFpa;
document.getElementById("cap").oninput  = updateFpa;
updateFpa();

Plotly.newPlot("chart-fpa-fw", [{
  type: "bar",
  x: PAYLOAD.fpa_by_fw.map(e => e[0]),
  y: PAYLOAD.fpa_by_fw.map(e => e[1]),
  marker: { color: T.primary2 },
  text: PAYLOAD.fpa_by_fw.map(e => e[1]),
  textposition: "auto",
}], {...baseLayout, yaxis: { title: "hours" }}, {displayModeBar: false, responsive: true});

Plotly.newPlot("chart-fpa-bu", [{
  type: "bar",
  x: PAYLOAD.fpa_by_bu.map(e => e[0]),
  y: PAYLOAD.fpa_by_bu.map(e => e[1]),
  marker: { color: T.primary3 },
  text: PAYLOAD.fpa_by_bu.map(e => e[1]),
  textposition: "auto",
}], {...baseLayout, yaxis: { title: "hours" }}, {displayModeBar: false, responsive: true});

// ─── PAGE 9 — Drill-through ────────────────────────────────────────────────
const sel = document.getElementById("drill-select");
PAYLOAD.agents.forEach(a => {
  const opt = document.createElement("option");
  opt.value = a.agent_id; opt.textContent = a.name + " — " + a.platform;
  sel.appendChild(opt);
});
function renderDrill() {
  const a = PAYLOAD.agents.find(x => x.agent_id === sel.value);
  if (!a) return;
  document.getElementById("drill-content").innerHTML = `
    <div class="grid grid-4">
      <div class="card"><h3>Risk score</h3><div class="num" style="color: ${a.score >= 75 ? T.critical : a.score >= 50 ? T.high : T.compliant}">${a.score.toFixed(1)}</div></div>
      <div class="card"><h3>C/H violations</h3><div class="num">${a.open_ch}</div></div>
      <div class="card"><h3>SLA breaches</h3><div class="num">${a.sla}</div></div>
      <div class="card"><h3>Attempts 30D</h3><div class="num">${a.attempts}</div></div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>Metadata</h3>
      <table class="data">
        <tr><th>Agent ID</th><td>${a.agent_id}</td><th>Platform</th><td>${a.platform}</td></tr>
        <tr><th>Business unit</th><td>${a.business_unit}</td><th>Criticality</th><td>${a.criticality}</td></tr>
        <tr><th>Tools count</th><td>${a.tools_count}</td><th>Excessive-agency findings</th><td>${a.excessive}</td></tr>
      </table>
    </div>`;
}
sel.onchange = renderDrill;
sel.value = PAYLOAD.agents[0].agent_id;
renderDrill();
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
