// connect_csv.pq
//
// Load every CSV from a configurable data folder. The DataFolder parameter
// makes it easy to point the dashboard at a different drop location —
// e.g. a OneDrive sync, a SharePoint mount, or an on-prem file share.
//
// Usage:
//   1. Transform Data → Manage Parameters → New Parameter
//        Name:  DataFolder
//        Type:  Text
//        Current Value: C:\path\to\repo\data
//   2. Paste this into Advanced Editor for the load query.

let
    Source = Folder.Files(DataFolder),
    OnlyCsv = Table.SelectRows(
        Source,
        each [Extension] = ".csv"
    ),
    AddedName = Table.AddColumn(
        OnlyCsv, "TableName",
        each Text.BeforeDelimiter([Name], ".")
    ),
    Loaded = Table.AddColumn(
        AddedName, "Data",
        each Csv.Document(
            File.Contents([Folder Path] & [Name]),
            [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
        )
    ),
    Promoted = Table.AddColumn(
        Loaded, "Promoted",
        each Table.PromoteHeaders([Data], [PromoteAllScalars = true])
    ),
    Final = Table.SelectColumns(Promoted, {"TableName", "Promoted"})
in
    Final

// After loading, click the expand icon on the "Promoted" column to
// materialise each table. Right-click the Final query and "Reference"
// it into one query per table — that gives you clean, individually
// refreshable artefacts in the model.
