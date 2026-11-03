# Dataset-aware charts

Chart choices and summaries now follow the columns of the currently persisted canonical dataset rather than requiring the Superstore Sales schema.

- Numeric target choices contain finite numeric measurements. Boolean, identifier and all-null fields are not suggested as numeric targets.
- Northwind Orders can chart `freight` without relabeling it as Sales. Canonical timestamps use `Timestamp` outside the legacy Sales view.
- Category counts work without a numeric measurement. Distribution and relationship charts require a usable numeric target; time-line charts additionally require a date/time comparison. Invalid selections and pairs with no overlapping values return explanatory 422 responses.
- Partially invalid date fields retain valid dates and report invalid entries as missing. Categorical columns named Sales do not trigger numeric aggregation.
- Chart overview and image requests reject running/failed ingestion and a selected dataset that has not completed processing, preventing a failed switch from relabeling older persisted records.
- Missing-value summaries cover all analysis fields, including SQL shipping columns.
- Dataset changes clear saved variable choices. The UI validates restored choices against the current schema and discards stale chart responses.
- Categorical scatter comparisons retain the existing explicit encoded-axis labeling; encoding is not evidence of a meaningful numerical relationship.

## Verification limits

The regression suite uses synthetic Northwind-shaped records and equivalent CSV, JSON, Parquet and Excel round trips. SQL query transport is mocked; these tests do not verify a live SQL connection or arbitrary customer data. The existing canonical adapter still selects one ID and one timestamp column and does not retain additional ID/date columns. Unsupported, empty, all-null and non-overlapping inputs do not produce invented charts.

This is a chart-only readiness guard, not a persistent dataset-isolation redesign. Session state remains process-local and ML endpoints are outside this fix.

No live deployment is included in this change.
