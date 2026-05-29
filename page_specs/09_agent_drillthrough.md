# Page 9 — Agent Drill-Through

One agent, every signal. Mark this page as a drill-through target
(Format pane → Drill through → cross-report off → drill through fields
= `dim_agent[agent_id]`).

## Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TITLE: <agent name>            ⟵ back arrow      criticality | platform   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Agent metadata card (multi-row):                                           │
│  owner | business_unit | environment | deployed_date | data_classification │
│  tools_count | uses_rag | uses_internet                                     │
├──────────────────────────────────┬──────────────────────────────────────────┤
│ Risk score gauge (0-100)         │ Open violations table (this agent only) │
├──────────────────────────────────┼──────────────────────────────────────────┤
│ Token cost trend 90D (line)      │ Runtime events 30D (stacked area)       │
├──────────────────────────────────┼──────────────────────────────────────────┤
│ Compliance per framework (bar)   │ Design-time findings (table)            │
└──────────────────────────────────┴──────────────────────────────────────────┘
```

## Drill-through setup

1. On the page, expand the Visualizations pane → **Drill through**.
2. Add `dim_agent[agent_id]` to "Drill through fields here".
3. Toggle "Keep all filters" on.
4. On any other page, right-click an agent row → Drill through → "Agent
   Drill-Through".

## Measures used

Everything in this file is the same as the portfolio pages, but
filtered to one agent via the drill-through filter — Power BI applies it
automatically.

## Back button

Power BI adds a back arrow automatically. Style it via the theme JSON's
button section to match the page header.
