# Functional hardening (November 2026)

The schema-aware chart changes are reconciled with the current main branch. Existing axis scaling, clipping, zoom presets, visualization styling, and the Isolation Forest top-10 anomaly sample remain available.

## Correctness changes

- Charts and ML reject a selected dataset whose pipeline has not completed successfully, rather than analyzing the previous stored dataset.
- ML uses the chosen numeric target consistently. If a dataset has several numeric fields and no established Sales default, choose the measurement in Charts. Results identify the actual field and disclose excluded missing/non-finite rows.
- Forecasts sort valid timestamps chronologically. They forecast the next record steps, not a calendar schedule or business outcome. Linear regression requires at least two usable observations; invalid timestamps, empty numeric data and invalid forecast horizons produce validation errors.
- Completed-run metrics survive page reloads while the API process is running. New runs clear old model results and metrics; late responses from a prior selection cannot overwrite the new selection.
- The duplicate Threshold option was removed because it called the Z-Score model rather than a separate threshold algorithm.
- Chart Apply Changes tracks text, grid and legend edits as well as numeric controls. Reset Zoom restores both the request bounds and displayed sliders. Invalid chart colors produce a controlled validation error.

## Verification and limits

Automated regression tests use synthetic local records and mocked external ingestion. They cover chart schema variations, supported file formats, missing values, stale dataset state, selected fields, forecast ordering, model edge cases, frontend flows, production bundle generation and lint.

The demo still has one shared, process-local session and active persisted dataset. It is not a per-user isolated service. Session summaries are not durable across API restarts. Local tests do not establish production SQL/Blob availability, model predictive accuracy, load capacity or security assurance. Live verification must be reported separately for the exact deployed revision.
