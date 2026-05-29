# Deployment guide

## 1. Build the .pbix in Power BI Desktop

See [`pbix_build_guide.md`](../pbix_build_guide.md). Save as
`AI-Agent-Governance.pbix` in the repo root.

## 2. Publish to a workspace

Choose a **Premium per User (PPU)** or **Premium capacity** workspace
if you want incremental refresh, large model storage, or paginated
reports.

1. **File → Publish** in Power BI Desktop.
2. Pick the workspace (`AI Governance` is a good name).
3. Wait for publish to complete; click "Open in Power BI" to verify.

## 3. Configure data source credentials

1. Workspace → Dataset → **Settings → Data source credentials**.
2. For `Folder` (CSV): point at the OneDrive / SharePoint mount.
3. For `Web` (REST API): set the API key parameter and authentication
   kind.

## 4. Set up scheduled refresh

1. Dataset → **Settings → Scheduled refresh** → On.
2. Pick the cadence from [`refresh_strategy.md`](refresh_strategy.md).
3. Tick "Send refresh failure notifications to me".

## 5. Apply RLS

See [`rls_setup.md`](rls_setup.md). Add members to roles.

## 6. Create an app

Workspace → **Create app**. Add the leadership audience to the **Built-in
audience** group. Optional second audience for security ops with more
detailed pages exposed.

## 7. Embed (optional)

Power BI embedded into Teams: **Add tab → Power BI** in the team's
channel. For a customer-facing app, use **Power BI Embedded** with
service principal auth — the dataset's RLS still applies via the
embed token's `role` parameter.

## Cost notes

- PPU is ~$20/user/month — fine for small leadership audiences.
- Premium capacity (P1/P2) is right for tenant-wide rollouts; check
  the **Premium Gen2 capacity metrics** app to confirm headroom.
- Direct Query mode on `fact_runtime_event` saves storage but adds
  load on the source — measure before flipping.
