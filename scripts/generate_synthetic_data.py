"""Synthetic data generator for the AI Agent Governance dashboard.

Produces CSVs in ../data/ that the Power BI model loads directly.
Re-running overwrites the existing files — deterministic via SEED.

Run:
    python scripts/generate_synthetic_data.py
"""
from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────── dimensions ─────────────────────────────────
PLATFORMS = ["Microsoft Copilot", "Anthropic Claude", "OpenAI Assistants",
             "LangGraph", "Custom Agent"]
BUSINESS_UNITS = ["Finance", "HR", "Engineering", "Sales", "Marketing",
                  "Customer Support", "Legal", "Risk & Compliance"]
ENVIRONMENTS = ["prod", "uat", "dev"]
CRITICALITY = ["Critical", "High", "Medium", "Low"]
SEVERITY_RANKS = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Info": 0}
SEVERITY_SLA_DAYS = {"Critical": 3, "High": 7, "Medium": 30, "Low": 90, "Info": 365}
SEVERITY_COLORS = {
    "Critical": "#C00000", "High": "#E97132", "Medium": "#FFC000",
    "Low": "#2E75B6", "Info": "#7F7F7F",
}
STATUSES = ["open", "in_progress", "remediated", "accepted_risk", "false_positive"]
STATUS_COLORS = {
    "open": "#C00000", "in_progress": "#E97132", "remediated": "#548235",
    "accepted_risk": "#7030A0", "false_positive": "#7F7F7F",
}

# Framework + control libraries (real, public references)
OWASP_LLM = [
    ("LLM01", "Prompt Injection", "runtime"),
    ("LLM02", "Sensitive Information Disclosure", "runtime"),
    ("LLM03", "Supply Chain", "design"),
    ("LLM04", "Data and Model Poisoning", "design"),
    ("LLM05", "Improper Output Handling", "runtime"),
    ("LLM06", "Excessive Agency", "design"),
    ("LLM07", "System Prompt Leakage", "runtime"),
    ("LLM08", "Vector and Embedding Weaknesses", "design"),
    ("LLM09", "Misinformation", "runtime"),
    ("LLM10", "Unbounded Consumption", "runtime"),
]

MITRE_ATLAS = [
    ("AML.T0051", "LLM Prompt Injection", "runtime"),
    ("AML.T0048", "Erode ML Model Integrity", "runtime"),
    ("AML.T0043", "Craft Adversarial Data", "runtime"),
    ("AML.T0049", "Exploit Public-Facing Application", "runtime"),
    ("AML.T0053", "LLM Plugin Compromise", "design"),
    ("AML.T0054", "LLM Jailbreak", "runtime"),
    ("AML.T0040", "ML Model Inference API Access", "design"),
    ("AML.T0044", "Full ML Model Access", "design"),
    ("AML.T0024", "Exfiltration via ML Inference API", "runtime"),
    ("AML.T0057", "LLM Data Leakage", "runtime"),
]

NIST_AI_RMF = [
    ("GOVERN-1.1", "Governance policies are in place", "design"),
    ("MAP-2.3", "Scientific integrity & TEVV considerations", "design"),
    ("MEASURE-2.7", "AI system security & resilience tested", "runtime"),
    ("MEASURE-2.11", "Privacy risk identified and managed", "runtime"),
    ("MANAGE-1.3", "Responses to AI risks documented", "design"),
    ("MANAGE-4.1", "Post-deployment monitoring planned", "runtime"),
]

EU_AI_ACT = [
    ("ART-9", "Risk management system", "design"),
    ("ART-10", "Data and data governance", "design"),
    ("ART-13", "Transparency to deployers", "design"),
    ("ART-14", "Human oversight", "runtime"),
    ("ART-15", "Accuracy, robustness, cybersecurity", "runtime"),
    ("ART-50", "Transparency obligations for general-purpose AI", "runtime"),
]

ISO_42001 = [
    ("8.2", "AI System Impact Assessment", "design"),
    ("8.3", "AI System Data Management", "design"),
    ("8.4", "AI System Lifecycle Information", "design"),
    ("9.4", "AI System Monitoring & Review", "runtime"),
]

FRAMEWORKS = [
    ("FW-OWASP",  "OWASP LLM Top 10 (2025)",  OWASP_LLM),
    ("FW-ATLAS",  "MITRE ATLAS",              MITRE_ATLAS),
    ("FW-NIST",   "NIST AI RMF 1.0",          NIST_AI_RMF),
    ("FW-EUAI",   "EU AI Act",                EU_AI_ACT),
    ("FW-ISO",    "ISO/IEC 42001:2023",       ISO_42001),
]

# Runtime event types — used by the streaming-style fact table
RUNTIME_EVENT_TYPES = [
    "prompt_injection_attempt", "pii_leak_blocked", "tool_misuse_blocked",
    "rate_limit_hit", "policy_violation", "jailbreak_attempt",
    "system_prompt_disclosed", "hallucination_flagged",
    "embedding_anomaly", "supply_chain_alert",
]


# ─────────────────────────────── data writers ───────────────────────────────
def write_csv(name: str, header: list[str], rows: list[list]) -> Path:
    path = DATA / name
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def gen_agents(n: int = 60) -> list[dict]:
    out = []
    for i in range(1, n + 1):
        platform = random.choice(PLATFORMS)
        bu = random.choice(BUSINESS_UNITS)
        out.append({
            "agent_id": f"AGT-{i:04d}",
            "name": f"{platform.split()[0]}-{bu[:3].upper()}-{i:03d}",
            "platform": platform,
            "business_unit": bu,
            "owner": f"owner{i}@example.com",
            "criticality": random.choices(
                CRITICALITY, weights=[1, 3, 4, 2], k=1
            )[0],
            "environment": random.choices(
                ENVIRONMENTS, weights=[5, 2, 3], k=1
            )[0],
            "deployed_date": (date(2025, 1, 1) +
                              timedelta(days=random.randint(0, 480))).isoformat(),
            "tools_count": random.randint(0, 12),
            "uses_rag": random.choice([True, False]),
            "uses_internet": random.choice([True, False]),
            "data_classification": random.choices(
                ["Public", "Internal", "Confidential", "Restricted"],
                weights=[2, 4, 3, 1], k=1)[0],
        })
    return out


def write_agents(agents: list[dict]) -> None:
    write_csv(
        "dim_agent.csv",
        ["agent_id", "name", "platform", "business_unit", "owner",
         "criticality", "environment", "deployed_date", "tools_count",
         "uses_rag", "uses_internet", "data_classification"],
        [[a[k] for k in (
            "agent_id", "name", "platform", "business_unit", "owner",
            "criticality", "environment", "deployed_date", "tools_count",
            "uses_rag", "uses_internet", "data_classification",
        )] for a in agents],
    )


def write_frameworks() -> tuple[list[dict], list[dict]]:
    fw_rows: list[dict] = []
    ctrl_rows: list[dict] = []
    for fw_id, fw_name, controls in FRAMEWORKS:
        fw_rows.append({
            "framework_id": fw_id, "name": fw_name,
            "url": _fw_url(fw_id), "version": "2024/2025 edition",
        })
        for (code, title, dr) in controls:
            ctrl_rows.append({
                "control_id": f"{fw_id}-{code}",
                "framework_id": fw_id,
                "control_code": code,
                "title": title,
                "design_or_runtime": dr,
            })
    write_csv(
        "dim_framework.csv",
        ["framework_id", "name", "url", "version"],
        [[r[k] for k in ("framework_id", "name", "url", "version")]
         for r in fw_rows],
    )
    write_csv(
        "dim_control.csv",
        ["control_id", "framework_id", "control_code", "title",
         "design_or_runtime"],
        [[r[k] for k in ("control_id", "framework_id", "control_code",
                          "title", "design_or_runtime")]
         for r in ctrl_rows],
    )
    return fw_rows, ctrl_rows


def _fw_url(fw_id: str) -> str:
    return {
        "FW-OWASP": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "FW-ATLAS": "https://atlas.mitre.org/",
        "FW-NIST":  "https://www.nist.gov/itl/ai-risk-management-framework",
        "FW-EUAI":  "https://artificialintelligenceact.eu/",
        "FW-ISO":   "https://www.iso.org/standard/81230.html",
    }.get(fw_id, "")


def write_severity_status() -> None:
    sev_rows = [
        [s, SEVERITY_RANKS[s], SEVERITY_SLA_DAYS[s], SEVERITY_COLORS[s]]
        for s in ("Critical", "High", "Medium", "Low", "Info")
    ]
    write_csv("dim_severity.csv",
              ["severity", "rank", "sla_days", "color_hex"], sev_rows)

    st_rows = [[s, STATUS_COLORS[s]] for s in STATUSES]
    write_csv("dim_status.csv", ["status", "color_hex"], st_rows)


def write_date_dimension(start: date, end: date) -> None:
    rows = []
    d = start
    while d <= end:
        rows.append([
            d.isoformat(), d.year, d.month, d.day,
            (d.month - 1) // 3 + 1, d.isoweekday(),
            d.strftime("%A"), d.strftime("%B"),
            f"{d.year}-W{d.isocalendar().week:02d}",
        ])
        d += timedelta(days=1)
    write_csv("dim_date.csv",
              ["date", "year", "month", "day", "quarter", "weekday_num",
               "weekday_name", "month_name", "iso_week"], rows)


# ─────────────────────────────── facts ──────────────────────────────────────
def gen_violations(agents: list[dict], controls: list[dict],
                   count: int = 700) -> list[list]:
    rows: list[list] = []
    today = date(2026, 5, 30)
    for i in range(count):
        ag = random.choice(agents)
        ctrl = random.choice(controls)
        severity = _bias_severity(ctrl["control_code"], ag["criticality"])
        detected = today - timedelta(days=random.randint(0, 180))
        status = random.choices(
            STATUSES, weights=[35, 20, 30, 5, 10], k=1
        )[0]
        sla = SEVERITY_SLA_DAYS[severity]
        due = detected + timedelta(days=sla)
        completed = None
        if status == "remediated":
            completed = detected + timedelta(days=random.randint(1, sla + 5))
        # FPA complexity: S/M/L/XL with weights per severity
        complexity = _pick_complexity(severity)
        rows.append([
            f"VIO-{i+1:05d}",
            ag["agent_id"],
            ctrl["control_id"],
            detected.isoformat(),
            severity,
            status,
            due.isoformat(),
            completed.isoformat() if completed else "",
            complexity,
        ])
    return rows


def _bias_severity(control_code: str, criticality: str) -> str:
    base = {"Critical": [40, 35, 15, 7, 3],
            "High":     [25, 35, 25, 10, 5],
            "Medium":   [15, 25, 35, 20, 5],
            "Low":      [10, 20, 35, 25, 10]}[criticality]
    # Hot-class controls bias toward higher severity
    hot = ("LLM01", "LLM02", "LLM06", "AML.T0051", "ART-15")
    if control_code in hot:
        base = [v + 10 if i < 2 else v - 5 for i, v in enumerate(base)]
    levels = ["Critical", "High", "Medium", "Low", "Info"]
    return random.choices(levels, weights=[max(v, 1) for v in base], k=1)[0]


def _pick_complexity(severity: str) -> str:
    weights = {
        "Critical": [5, 25, 45, 25],
        "High":     [10, 35, 40, 15],
        "Medium":   [25, 45, 25, 5],
        "Low":      [50, 35, 13, 2],
        "Info":     [70, 25, 5, 0],
    }[severity]
    return random.choices(["S", "M", "L", "XL"],
                          weights=[max(v, 1) for v in weights], k=1)[0]


def write_violations(rows: list[list]) -> None:
    write_csv(
        "fact_violation.csv",
        ["violation_id", "agent_id", "control_id", "detected_date",
         "severity", "status", "remediation_due_date",
         "remediation_completed_date", "fpa_complexity"],
        rows,
    )


def gen_token_consumption(agents: list[dict], days: int = 180) -> list[list]:
    rows: list[list] = []
    today = date(2026, 5, 30)
    for ag in agents:
        # Each agent has a baseline daily volume by criticality + RAG
        base = {"Critical": 80000, "High": 30000,
                "Medium": 8000, "Low": 1500}[ag["criticality"]]
        if ag["uses_rag"]:
            base = int(base * 1.6)
        for i in range(days):
            d = today - timedelta(days=days - 1 - i)
            # Some weekday-only seasonality.
            mult = 0.4 if d.isoweekday() >= 6 else 1.0
            jitter = random.uniform(0.6, 1.4)
            input_tok = int(base * mult * jitter * 0.65)
            output_tok = int(base * mult * jitter * 0.35)
            model = _pick_model(ag["platform"])
            cost = _cost(model, input_tok, output_tok)
            rows.append([
                d.isoformat(), ag["agent_id"], model,
                input_tok, output_tok, round(cost, 4),
                int((input_tok + output_tok) / 1500),  # ~requests
            ])
    return rows


def _pick_model(platform: str) -> str:
    if platform == "Anthropic Claude":
        return random.choice(["claude-sonnet-4-6", "claude-opus-4-7",
                               "claude-haiku-4-5"])
    if platform == "Microsoft Copilot":
        return random.choice(["gpt-4o", "gpt-4.1", "gpt-4o-mini"])
    if platform == "OpenAI Assistants":
        return random.choice(["gpt-4o", "gpt-4o-mini", "o3-mini"])
    return random.choice(["llama-3.1-8b", "mistral-large", "gemini-1.5-pro"])


# Per-million-token blended cost (illustrative — update yearly)
_TARIFF: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-7":   (15.0, 75.0),
    "claude-haiku-4-5":  (0.8, 4.0),
    "gpt-4o":            (2.5, 10.0),
    "gpt-4.1":           (3.0, 12.0),
    "gpt-4o-mini":       (0.15, 0.6),
    "o3-mini":           (1.1, 4.4),
    "llama-3.1-8b":      (0.1, 0.4),
    "mistral-large":     (2.0, 6.0),
    "gemini-1.5-pro":    (3.5, 10.5),
}


def _cost(model: str, in_tok: int, out_tok: int) -> float:
    in_rate, out_rate = _TARIFF.get(model, (1.0, 3.0))
    return (in_tok / 1_000_000) * in_rate + (out_tok / 1_000_000) * out_rate


def write_token_consumption(rows: list[list]) -> None:
    write_csv(
        "fact_token_consumption.csv",
        ["date", "agent_id", "model", "input_tokens", "output_tokens",
         "cost_usd", "requests"],
        rows,
    )


def gen_runtime_events(agents: list[dict], days: int = 60) -> list[list]:
    rows: list[list] = []
    today = date(2026, 5, 30)
    for ag in agents:
        # Higher-criticality agents see more attempted events.
        base = {"Critical": 12, "High": 6, "Medium": 2, "Low": 1}[ag["criticality"]]
        for i in range(days):
            d = today - timedelta(days=days - 1 - i)
            events_today = max(0, int(random.gauss(base, base * 0.5)))
            for _ in range(events_today):
                ts = datetime.combine(d, datetime.min.time()) + timedelta(
                    minutes=random.randint(0, 1440 - 1))
                kind = random.choices(
                    RUNTIME_EVENT_TYPES,
                    weights=[10, 8, 6, 12, 7, 5, 3, 6, 4, 2],
                    k=1)[0]
                blocked = random.choices(
                    [True, False],
                    weights=[80 if kind != "rate_limit_hit" else 50, 20],
                    k=1)[0]
                severity = _kind_to_severity(kind)
                rows.append([
                    ts.isoformat(timespec="seconds"),
                    ag["agent_id"], kind, severity,
                    str(blocked).lower(),
                ])
    return rows


def _kind_to_severity(kind: str) -> str:
    if kind in ("prompt_injection_attempt", "jailbreak_attempt",
                "system_prompt_disclosed", "supply_chain_alert",
                "tool_misuse_blocked"):
        return random.choices(["Critical", "High"], weights=[40, 60])[0]
    if kind in ("pii_leak_blocked", "policy_violation"):
        return random.choices(["High", "Medium"], weights=[55, 45])[0]
    if kind in ("hallucination_flagged", "embedding_anomaly"):
        return random.choices(["Medium", "Low"], weights=[60, 40])[0]
    return "Low"


def write_runtime_events(rows: list[list]) -> None:
    write_csv(
        "fact_runtime_event.csv",
        ["event_ts", "agent_id", "event_type", "severity", "blocked"],
        rows,
    )


def gen_design_findings(agents: list[dict], count: int = 200) -> list[list]:
    """Design-time findings — pulled from a code/config scan rather than from
    runtime. Same shape as a violation but with a fixed `design` type so the
    dashboard can separate the two."""
    rows: list[list] = []
    today = date(2026, 5, 30)
    issues = [
        ("tools wildcard granted",     "Critical"),
        ("missing system prompt hardening", "High"),
        ("RAG corpus missing PII filter",   "High"),
        ("no rate limit configured",        "Medium"),
        ("no human-in-the-loop on sensitive tools", "Critical"),
        ("model card incomplete",           "Low"),
        ("training data lineage missing",   "Medium"),
        ("eval suite < 50 prompts",         "Medium"),
    ]
    for i in range(count):
        ag = random.choice(agents)
        title, sev = random.choice(issues)
        detected = today - timedelta(days=random.randint(0, 90))
        rows.append([
            f"DSN-{i+1:05d}", ag["agent_id"], title, sev,
            random.choices(STATUSES, weights=[40, 15, 35, 5, 5])[0],
            detected.isoformat(),
        ])
    return rows


def write_design_findings(rows: list[list]) -> None:
    write_csv(
        "fact_design_finding.csv",
        ["finding_id", "agent_id", "title", "severity", "status",
         "detected_date"],
        rows,
    )


# ─────────────────────────────── main ───────────────────────────────────────
def main() -> None:
    print(f"writing CSVs to {DATA}/")
    agents = gen_agents(60)
    write_agents(agents)
    _, controls = write_frameworks()
    write_severity_status()
    write_date_dimension(date(2025, 1, 1), date(2026, 12, 31))

    write_violations(gen_violations(agents, controls, count=700))
    write_token_consumption(gen_token_consumption(agents, days=180))
    write_runtime_events(gen_runtime_events(agents, days=60))
    write_design_findings(gen_design_findings(agents, count=200))

    print("done. files written:")
    for p in sorted(DATA.glob("*.csv")):
        rows = sum(1 for _ in p.open(encoding="utf-8")) - 1
        print(f"  {p.name:35s} {rows:6d} rows")


if __name__ == "__main__":
    main()
