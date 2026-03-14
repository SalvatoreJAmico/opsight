# Ingestion Data Contract

## Purpose

The ingestion module is responsible for reading source data only.
It detects source formats, loads datasets, and performs basic required-field checks before handoff to adapter transformation.

## Raw Input Record

Raw records represent operational events received from external datasets or external systems.

## Expected Fields

<table style="table-layout: fixed; width: 760px;">
	<colgroup>
		<col style="width: 160px;" />
		<col style="width: 140px;" />
		<col style="width: 120px;" />
		<col style="width: 340px;" />
	</colgroup>
	<thead>
		<tr>
			<th>Field</th>
			<th>Type</th>
			<th>Required</th>
			<th>Description</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>timestamp</td>
			<td>datetime</td>
			<td>yes</td>
			<td>Time the event occurred</td>
		</tr>
		<tr>
			<td>source</td>
			<td>string</td>
			<td>yes</td>
			<td>System or dataset source</td>
		</tr>
		<tr>
			<td>event_type</td>
			<td>string</td>
			<td>yes</td>
			<td>Type of operational event</td>
		</tr>
		<tr>
			<td>severity</td>
			<td>string</td>
			<td>optional</td>
			<td>Event severity level</td>
		</tr>
		<tr>
			<td>message</td>
			<td>string</td>
			<td>optional</td>
			<td>Event description</td>
		</tr>
		<tr>
			<td>asset_id</td>
			<td>string</td>
			<td>optional</td>
			<td>Associated infrastructure asset</td>
		</tr>
	</tbody>
</table>

### Example Raw Record

```json
{
	"timestamp": "2026-03-10T12:01:22Z",
	"source": "sensor_gateway",
	"event_type": "temperature_alert",
	"severity": "warning",
	"message": "Temperature exceeded threshold",
	"asset_id": "rack-22"
}
```

## Source Format Detection

The ingestion module detects source format with `detect_format(source_path)`.
Supported formats:

- csv
- tsv
- json
- parquet
- excel
- sql
- text

## Loaded Output Structure

The ingestion module loads the source with `load_source(source_path, source_format)` and returns a dataframe-like dataset (pandas DataFrame).

## Validation Rules

The ingestion module performs basic record validation before transformation.

- `timestamp` must be a valid datetime.
- `source` must be present.
- `event_type` must be present.
- Records missing required fields are rejected.
- Optional fields may be absent or null.

## Error Handling

If a record fails validation:

- The record is skipped.
- The error is logged.
- Ingestion continues for remaining records.

This prevents ingestion pipelines from stopping due to malformed data.

## Handoff Boundary

The ingestion module does not normalize or map canonical records.
Transformation to canonical schema is handled by the adapter module.