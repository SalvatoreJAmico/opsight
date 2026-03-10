# Ingestion Data Contract

## Purpose

The ingestion module imports external datasets into the Opsight system and converts them into a normalized internal event format.
This document defines the expected input schema, normalized output schema, validation rules, and error handling behavior.

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

## Normalized Output Record

The ingestion module converts raw records into a normalized internal structure used by Opsight.

## Normalized Fields

<table style="table-layout: fixed; width: 620px;">
	<colgroup>
		<col style="width: 180px;" />
		<col style="width: 140px;" />
		<col style="width: 300px;" />
	</colgroup>
	<thead>
		<tr>
			<th>Field</th>
			<th>Type</th>
			<th>Description</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>event_time</td>
			<td>datetime</td>
			<td>Normalized timestamp</td>
		</tr>
		<tr>
			<td>source_system</td>
			<td>string</td>
			<td>Data source</td>
		</tr>
		<tr>
			<td>type</td>
			<td>string</td>
			<td>Event classification</td>
		</tr>
		<tr>
			<td>severity</td>
			<td>string</td>
			<td>Normalized severity</td>
		</tr>
		<tr>
			<td>description</td>
			<td>string</td>
			<td>Event message</td>
		</tr>
		<tr>
			<td>asset</td>
			<td>string</td>
			<td>Infrastructure asset identifier</td>
		</tr>
	</tbody>
</table>

### Example Normalized Record

```json
{
	"event_time": "2026-03-10T12:01:22Z",
	"source_system": "sensor_gateway",
	"type": "temperature_alert",
	"severity": "warning",
	"description": "Temperature exceeded threshold",
	"asset": "rack-22"
}
```

## Validation Rules

The ingestion module validates records before normalization.

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