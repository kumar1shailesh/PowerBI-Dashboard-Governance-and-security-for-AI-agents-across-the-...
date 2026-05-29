// date_dimension.pq
//
// M-based date table. Replaces dim_date.csv if you want a self-contained
// model (no separate CSV to manage).
//
// Mark this table as a Date Table via:
//   Modeling → Mark as date table → Date column = "date"

let
    StartDate = #date(2025, 1, 1),
    EndDate   = #date(2026, 12, 31),
    NumDays   = Duration.Days(EndDate - StartDate) + 1,
    Dates     = List.Dates(StartDate, NumDays, #duration(1, 0, 0, 0)),
    AsTable   = Table.FromList(
        Dates,
        Splitter.SplitByNothing(),
        {"date"}, null, ExtraValues.Error
    ),
    Typed     = Table.TransformColumnTypes(AsTable, {{"date", type date}}),
    Added = Table.AddColumn(
        Table.AddColumn(
            Table.AddColumn(
                Table.AddColumn(
                    Table.AddColumn(
                        Table.AddColumn(
                            Table.AddColumn(
                                Table.AddColumn(Typed, "year",
                                    each Date.Year([date]), Int64.Type),
                                "month", each Date.Month([date]), Int64.Type),
                            "day", each Date.Day([date]), Int64.Type),
                        "quarter", each Date.QuarterOfYear([date]), Int64.Type),
                    "weekday_num", each Date.DayOfWeek([date], Day.Monday) + 1, Int64.Type),
                "weekday_name", each Date.DayOfWeekName([date]), type text),
            "month_name", each Date.MonthName([date]), type text),
        "iso_week", each
            Text.From(Date.Year([date])) & "-W" &
            Text.PadStart(Text.From(Date.WeekOfYear([date])), 2, "0"),
            type text
    )
in
    Added
