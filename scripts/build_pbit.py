"""Assemble a `.pbit` (Power BI template) from the repo's text artifacts.

A PBIT is a ZIP with a documented internal layout. This script:
  1. reads the CSV headers in `data/` to derive column types
  2. reads `dax/*.dax` to collect every measure
  3. builds DataModelSchema (TMSL JSON) with all tables + relationships +
     measures + a `DataFolder` query parameter
  4. builds a minimal Report/Layout JSON with one page (Executive Summary)
     containing the key KPI cards bound to those measures
  5. writes the PBIT manifest files
  6. ZIPs everything into `AI-Agent-Governance.pbit` at the repo root

Run:
    python scripts/build_pbit.py

Open the resulting .pbit in Power BI Desktop. Desktop will prompt for the
`DataFolder` parameter (point it at the absolute path of `data/` on your
machine), then materialise the data model and render the page. Add the
other 8 pages by following `page_specs/02-09`.

CAVEAT: the PBIT internal format is finicky. If Power BI Desktop rejects
the file, fall back to `pbix_build_guide.md` (a 30-minute manual build).
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DAX_DIR = ROOT / "dax"
PBIT_DIR = ROOT / "pbit_build"
OUTPUT = ROOT / "AI-Agent-Governance.pbit"

# ─── compatibility / model knobs ─────────────────────────────────────────────
MODEL_NAME = "AI Agent Governance"
COMPAT_LEVEL = 1567
DEFAULT_CULTURE = "en-US"


# ─── column type inference ───────────────────────────────────────────────────
def infer_types(csv_path: Path) -> list[dict]:
    """Sample the first 200 rows of a CSV and infer each column's data type."""
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for i, row in enumerate(reader):
            if i >= 200:
                break
            rows.append(row)
        if not rows:
            cols = reader.fieldnames or []
            return [{"name": c, "dataType": "string", "sourceColumn": c} for c in cols]

    cols: list[dict] = []
    for col in rows[0].keys():
        values = [r[col] for r in rows if r.get(col) not in (None, "")]
        dt = _guess_type(values)
        cols.append({"name": col, "dataType": dt, "sourceColumn": col})
    return cols


def _guess_type(values: list[str]) -> str:
    if not values:
        return "string"
    sample = values[:50]
    if all(_is_int(v) for v in sample):
        return "int64"
    if all(_is_num(v) for v in sample):
        return "double"
    if all(_is_date(v) for v in sample):
        return "dateTime"
    if all(_is_bool(v) for v in sample):
        return "boolean"
    return "string"


def _is_int(v: str) -> bool:
    try:
        int(v)
        return True
    except (TypeError, ValueError):
        return False


def _is_num(v: str) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _is_date(v: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(:\d{2})?)?$", v))


def _is_bool(v: str) -> bool:
    return v.strip().lower() in {"true", "false", "0", "1", "yes", "no"}


# ─── M expression per table ──────────────────────────────────────────────────
def build_m_query(table_name: str, csv_filename: str, columns: list[dict]) -> str:
    """One M query per table — uses the DataFolder parameter so the
    operator can repoint without editing the model."""
    typecast = ", ".join(
        f'{{"{c["name"]}", {_m_type(c["dataType"])}}}'
        for c in columns
    )
    return (
        f"let\n"
        f"    Source = Csv.Document(File.Contents(DataFolder & \"\\\\{csv_filename}\"),"
        f" [Delimiter=\",\", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n"
        f"    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n"
        f"    Typed = Table.TransformColumnTypes(Promoted, {{{typecast}}})\n"
        f"in\n"
        f"    Typed"
    )


def _m_type(t: str) -> str:
    return {
        "string": "type text",
        "int64": "Int64.Type",
        "double": "type number",
        "dateTime": "type date",
        "boolean": "type logical",
    }.get(t, "type text")


# ─── DAX measure parsing ─────────────────────────────────────────────────────
_MEASURE_RE = re.compile(
    r"^([A-Za-z][\w \-/%&]*?)\s*=\s*$",
    re.MULTILINE,
)


def parse_measures(dax_dir: Path) -> list[dict]:
    """Read every .dax file and extract (name, expression) pairs."""
    measures: list[dict] = []
    for path in sorted(dax_dir.glob("*.dax")):
        text = path.read_text(encoding="utf-8")
        # Strip line comments (// ...) and block comments for cleaner extraction.
        text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
        # Split into "Name = ..." blocks. Naive but works for our consistent file shape.
        blocks = re.split(r"\n(?=[A-Za-z][\w \-/%&]+\s*=\s*\n)", text)
        for block in blocks:
            block = block.strip()
            if not block or "=" not in block:
                continue
            head, _, expr = block.partition("=")
            name = head.strip()
            expr = expr.strip()
            # Skip lines that aren't really measures (e.g. parameter table refs).
            if not name or not expr or "\n" in name or len(name) > 80:
                continue
            measures.append({"name": name, "expression": expr,
                              "formatString": _format_for(name)})
    return measures


def _format_for(name: str) -> str:
    lower = name.lower()
    if "%" in lower or "rate" in lower or "share" in lower:
        return "0.0%"
    if "cost" in lower or "usd" in lower:
        return "\"$\"#,##0.00"
    if "days" in lower or "weeks" in lower:
        return "0.00"
    if "score" in lower:
        return "0.0"
    return "#,##0"


# ─── TMSL data model assembly ────────────────────────────────────────────────
def build_data_model() -> dict:
    tables: list[dict] = []
    for csv_path in sorted(DATA.glob("*.csv")):
        name = csv_path.stem
        columns = infer_types(csv_path)
        partition = {
            "name": "Partition",
            "mode": "import",
            "source": {
                "type": "m",
                "expression": build_m_query(name, csv_path.name, columns),
            },
        }
        # All measures attach to a single _Measures table to keep the field list clean
        tables.append({
            "name": name,
            "lineageTag": f"lt-{name}",
            "columns": columns,
            "partitions": [partition],
        })

    # Measure-host table (hidden, empty)
    measures = parse_measures(DAX_DIR)
    measure_table = {
        "name": "_Measures",
        "lineageTag": "lt-_Measures",
        "isHidden": False,
        "columns": [
            {"name": "Placeholder", "dataType": "string", "sourceColumn": "Placeholder", "isHidden": True}
        ],
        "partitions": [{
            "name": "Partition",
            "mode": "import",
            "source": {
                "type": "m",
                "expression": "let Source = Table.FromRows({{\"\"}}, {\"Placeholder\"}) in Source",
            },
        }],
        "measures": [
            {"name": m["name"], "expression": m["expression"], "formatString": m["formatString"]}
            for m in measures
        ],
    }
    tables.append(measure_table)

    relationships = build_relationships()

    return {
        "compatibilityLevel": COMPAT_LEVEL,
        "model": {
            "culture": DEFAULT_CULTURE,
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True,
            },
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": relationships,
            "annotations": [
                {"name": "PBI_QueryOrder", "value": json.dumps([t["name"] for t in tables])},
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
            ],
            "expressions": [{
                "name": "DataFolder",
                "kind": "m",
                "expression": (
                    "\"\" meta [IsParameterQuery=true, "
                    "Type=\"Text\", IsParameterQueryRequired=true]"
                ),
                "lineageTag": "lt-DataFolder",
            }],
        },
        "id": "Model",
        "name": "Model",
    }


def build_relationships() -> list[dict]:
    """Star-schema relationships — see docs/data_model.md for the ERD."""
    rels = [
        ("fact_violation", "agent_id", "dim_agent", "agent_id"),
        ("fact_violation", "control_id", "dim_control", "control_id"),
        ("fact_violation", "detected_date", "dim_date", "date"),
        ("fact_violation", "severity", "dim_severity", "severity"),
        ("fact_violation", "status", "dim_status", "status"),
        ("fact_token_consumption", "agent_id", "dim_agent", "agent_id"),
        ("fact_token_consumption", "date", "dim_date", "date"),
        ("fact_runtime_event", "agent_id", "dim_agent", "agent_id"),
        ("fact_runtime_event", "severity", "dim_severity", "severity"),
        ("fact_design_finding", "agent_id", "dim_agent", "agent_id"),
        ("fact_design_finding", "severity", "dim_severity", "severity"),
        ("fact_design_finding", "status", "dim_status", "status"),
        ("dim_control", "framework_id", "dim_framework", "framework_id"),
    ]
    out = []
    for i, (ft, fc, tt, tc) in enumerate(rels, start=1):
        out.append({
            "name": f"rel{i}",
            "fromTable": ft,
            "fromColumn": fc,
            "toTable": tt,
            "toColumn": tc,
        })
    return out


# ─── Report layout (single page, KPI cards) ──────────────────────────────────
def build_report_layout() -> dict:
    """Minimal layout: one section with title + 4 KPI cards. The user
    expands to all 9 pages following the page_specs/."""
    cards = [
        {"x": 40,  "title": "Total Agents",     "measure": None,
         "field":  ("dim_agent", "agent_id", "Count (Distinct)")},
        {"x": 350, "title": "Open Violations",  "measure": "Open Violations"},
        {"x": 660, "title": "SLA Breaches",     "measure": "SLA Breach Count"},
        {"x": 970, "title": "Critical Agents",  "measure": "Critical Agents Count"},
    ]
    containers = [
        # Page header
        _text_container(
            x=40, y=20, w=1200, h=40,
            text="AI Agent Governance — Executive Summary",
            size=28, color="#1F4E79", bold=True,
        ),
    ]
    for i, card in enumerate(cards):
        containers.append(_card_container(
            x=card["x"], y=80, w=270, h=130,
            title=card["title"],
            measure=card.get("measure"),
            field=card.get("field"),
            index=i,
        ))

    # Note box explaining this is a starter page
    containers.append(_text_container(
        x=40, y=240, w=1200, h=80,
        text=("This is the starter Executive Summary page. Add the remaining "
              "eight pages by following page_specs/02-09 in the repo."),
        size=11, color="#5B5B5B",
    ))

    section = {
        "name": "ReportSection_ExecutiveSummary",
        "displayName": "Executive Summary",
        "displayOption": 1,
        "width": 1280,
        "height": 720,
        "config": "{}",
        "visualContainers": containers,
    }

    return {
        "id": 0,
        "resourcePackages": [],
        "config": json.dumps({
            "version": "5.43",
            "themeCollection": {"baseTheme": {"name": "CY24SU10"}},
            "activeSectionIndex": 0,
            "settings": {"useStylableVisualContainerHeader": True},
        }),
        "layoutOptimization": 0,
        "publicCustomVisuals": [],
        "sections": [section],
    }


def _text_container(x: int, y: int, w: int, h: int, text: str,
                    size: int = 12, color: str = "#222222",
                    bold: bool = False) -> dict:
    style = (
        f"<p><span style=\"font-size:{size}px;color:{color};"
        f"{'font-weight:bold;' if bold else ''}\">{text}</span></p>"
    )
    cfg = {
        "name": f"tb-{abs(hash(text)) % 1_000_000}",
        "layouts": [{"id": 0, "position": {"x": x, "y": y,
                                            "width": w, "height": h, "z": 1}}],
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {
                "general": [{"properties": {
                    "paragraphs": [{"textRuns": [
                        {"value": text, "textStyle": {
                            "fontSize": f"{size}pt",
                            "color": {"solid": {"color": color}},
                            "fontWeight": "bold" if bold else "normal",
                        }}
                    ]}]
                }}]
            },
        },
    }
    return {"x": x, "y": y, "z": 0, "width": w, "height": h,
            "config": json.dumps(cfg)}


def _card_container(x: int, y: int, w: int, h: int, title: str,
                    measure: str | None, field: tuple | None,
                    index: int) -> dict:
    if measure:
        projections = {"Values": [{"queryRef": f"_Measures.{measure}"}]}
        select = [{"Measure": {"Expression": {"SourceRef": {"Source": "m"}},
                                "Property": measure}, "Name": f"_Measures.{measure}"}]
        from_clause = [{"Name": "m", "Entity": "_Measures", "Type": 0}]
    else:
        table, col, _ = field
        projections = {"Values": [{"queryRef": f"{table}.{col}"}]}
        select = [{"Aggregation": {"Expression": {"Column": {
            "Expression": {"SourceRef": {"Source": "t"}}, "Property": col
        }}, "Function": 5}, "Name": f"CountDistinct({table}.{col})"}]
        from_clause = [{"Name": "t", "Entity": table, "Type": 0}]

    cfg = {
        "name": f"card-{index}",
        "layouts": [{"id": 0, "position": {"x": x, "y": y,
                                            "width": w, "height": h, "z": index + 1}}],
        "singleVisual": {
            "visualType": "card",
            "projections": projections,
            "prototypeQuery": {
                "Version": 2,
                "From": from_clause,
                "Select": select,
            },
            "drillFilterOtherVisuals": True,
            "objects": {
                "general": [{"properties": {
                    "altText": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                }}],
                "categoryLabels": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": "#5B5B5B"}},
                }}],
                "labels": [{"properties": {
                    "color": {"solid": {"color": "#1F4E79"}},
                    "fontSize": {"expr": {"Literal": {"Value": "32D"}}},
                }}],
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": "#1F4E79"}},
                }}],
            },
        },
    }
    return {"x": x, "y": y, "z": index, "width": w, "height": h,
            "config": json.dumps(cfg)}


# ─── Connections file ────────────────────────────────────────────────────────
def build_connections() -> dict:
    return {
        "Version": 1,
        "Connections": [{
            "Name": "EntityDataSource",
            "ConnectionString": (
                f"Data Source=$Embedded$;Provider=MSOLAP;"
                f"Initial Catalog={MODEL_NAME};"
                "Persist Security Info=True;Impersonation Level=Impersonate"
            ),
            "ConnectionType": "analysisServicesDatabaseLive",
        }],
    }


# ─── PBIT assembly ───────────────────────────────────────────────────────────
def write_pbit() -> None:
    PBIT_DIR.mkdir(parents=True, exist_ok=True)
    for sub in ("Report", "Metadata", "SecurityBindings"):
        (PBIT_DIR / sub).mkdir(parents=True, exist_ok=True)

    # ── Static files
    (PBIT_DIR / "Version").write_text("3.0", encoding="utf-16-le")
    (PBIT_DIR / "Settings").write_text("{}", encoding="utf-8")
    (PBIT_DIR / "Metadata" / "Version").write_text(
        json.dumps({"Version": "3.0", "AutoExtendedTypes": "True"}),
        encoding="utf-8",
    )
    (PBIT_DIR / "SecurityBindings" / "Version").write_text("3.0", encoding="utf-16-le")

    # ── DataModelSchema (TMSL JSON, utf-16-le without BOM is what PBI Desktop writes)
    schema = build_data_model()
    (PBIT_DIR / "DataModelSchema").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-16-le",
    )

    # ── Report/Layout
    layout = build_report_layout()
    (PBIT_DIR / "Report" / "Layout").write_text(
        json.dumps(layout, ensure_ascii=False),
        encoding="utf-16-le",
    )

    # ── Connections
    conn = build_connections()
    (PBIT_DIR / "Connections").write_text(
        json.dumps(conn, ensure_ascii=False),
        encoding="utf-8",
    )

    # ── [Content_Types].xml
    ct = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="json" ContentType="" />\n'
        '  <Default Extension="xml" ContentType="application/xml" />\n'
        '  <Override PartName="/Version" ContentType="" />\n'
        '  <Override PartName="/Settings" ContentType="" />\n'
        '  <Override PartName="/Metadata/Version" ContentType="" />\n'
        '  <Override PartName="/DataModelSchema" ContentType="" />\n'
        '  <Override PartName="/Connections" ContentType="" />\n'
        '  <Override PartName="/Report/Layout" ContentType="" />\n'
        '  <Override PartName="/SecurityBindings/Version" ContentType="" />\n'
        '</Types>\n'
    )
    (PBIT_DIR / "[Content_Types].xml").write_text(ct, encoding="utf-8")

    # ── ZIP into .pbit
    if OUTPUT.exists():
        OUTPUT.unlink()
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PBIT_DIR.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(PBIT_DIR).as_posix()
            zf.write(path, arcname=rel)

    size_kb = OUTPUT.stat().st_size // 1024
    measures = parse_measures(DAX_DIR)
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({size_kb} KB)")
    print(f"  tables:         {len(list(DATA.glob('*.csv')))}")
    print(f"  relationships:  {len(build_relationships())}")
    print(f"  DAX measures:   {len(measures)}")
    print()
    print("Next step: open the .pbit in Power BI Desktop. When prompted, set")
    print("`DataFolder` to the absolute path of the `data/` directory on your machine.")


if __name__ == "__main__":
    write_pbit()
