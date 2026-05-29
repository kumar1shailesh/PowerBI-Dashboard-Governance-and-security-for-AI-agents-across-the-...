# Power Query M scripts

| File | What it does |
| --- | --- |
| `connect_csv.pq` | Single parameterised query that loads every CSV under `/data/` |
| `connect_rest_api.pq` | Drop-in replacement for the CSV connector — pulls from a governance REST API |
| `date_dimension.pq` | M-based date table if you'd rather not load `dim_date.csv` |
| `rest_api_template.pq` | Shape-preserving template for any custom REST source |

## How to use

1. Open the `.pq` file in a text editor.
2. In Power BI Desktop: **Home → Transform Data → Home → Advanced Editor**.
3. Replace the auto-generated M with the contents of the file.
4. Apply.

For the REST connector, set the `BaseUrl` and `ApiKey` parameters in
**Transform Data → Manage Parameters** before the query runs.
