// connect_rest_api.pq
//
// Pull governance data from a REST API instead of CSV. This is the
// production swap-in: your security platform exposes the same row shape
// over HTTPS, and Power BI Service refreshes on a schedule.
//
// The API contract (per table):
//   GET {BaseUrl}/v1/agents
//   GET {BaseUrl}/v1/violations?from=YYYY-MM-DD&to=YYYY-MM-DD
//   GET {BaseUrl}/v1/runtime_events?from=...&to=...
//   GET {BaseUrl}/v1/token_consumption?from=...&to=...
//
// All endpoints return JSON arrays with the same field names as the CSVs.

let
    BaseUrl = "https://governance.example.com",                     // parameter
    ApiKey  = "REPLACE_ME_VIA_PARAMETER",                           // parameter
    Path    = "/v1/violations",                                     // change per table
    From    = Date.ToText(Date.AddDays(DateTime.Date(DateTime.LocalNow()), -180), "yyyy-MM-dd"),
    To      = Date.ToText(DateTime.Date(DateTime.LocalNow()), "yyyy-MM-dd"),

    Headers = [
        #"X-Api-Key" = ApiKey,
        #"Accept"    = "application/json"
    ],
    Query = [
        from = From,
        to   = To
    ],

    Raw = Json.Document(
        Web.Contents(
            BaseUrl,
            [
                RelativePath = Path,
                Query        = Query,
                Headers      = Headers,
                Timeout      = #duration(0, 0, 0, 60)
            ]
        )
    ),

    AsTable = Table.FromList(
        Raw,
        Splitter.SplitByNothing(),
        null, null, ExtraValues.Error
    ),
    Expanded = Table.ExpandRecordColumn(
        AsTable, "Column1",
        {"violation_id", "agent_id", "control_id", "detected_date",
         "severity", "status", "remediation_due_date",
         "remediation_completed_date", "fpa_complexity"}
    ),

    // Light type coercion so downstream measures don't have to coerce.
    Typed = Table.TransformColumnTypes(Expanded, {
        {"violation_id",                type text},
        {"agent_id",                    type text},
        {"control_id",                  type text},
        {"detected_date",               type date},
        {"severity",                    type text},
        {"status",                      type text},
        {"remediation_due_date",        type date},
        {"remediation_completed_date",  type date},
        {"fpa_complexity",              type text}
    })
in
    Typed

// Deployment notes:
//   - In Power BI Service set BaseUrl + ApiKey as data source credentials.
//   - On-prem REST APIs require a Gateway; configure under Datasets →
//     Settings → Gateway connection.
//   - For incremental refresh, parameterise `From` and `To` with the
//     RangeStart / RangeEnd built-in parameters (Modeling → Incremental
//     refresh policy on the table).
