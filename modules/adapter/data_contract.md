# Adapter Data Contract

## Overview
The adapter module receives loaded datasets and converts them into the Opsight canonical schema.
This contract defines the expected input structure and the output format produced by the adapter.

---

## Input Contract

The adapter receives a loaded dataset and produces a normalized internal representation before canonical mapping.

Structure:


record = {
"entity_id_cols": [str],
"timestamp_cols": [str],
"feature_cols": [str],
"data": pandas.DataFrame
}


### Field Descriptions

**entity_id_cols**  
List of columns representing entity identifiers.

Example:

["customer_id"]


**timestamp_cols**  
List of columns representing timestamps or event times.

Example:

["created_at"]


**feature_cols**  
Columns representing measurable attributes or features of the record.

Example:

["amount", "region", "product"]


**data**  
A pandas DataFrame containing the dataset rows.

Example:


customer_id | created_at | amount | region
101 | 2026-03-12 | 45.00 | west
102 | 2026-03-13 | 51.00 | east


---

## Output Contract

The adapter returns a list of canonical records.

Structure:


[
{
"entity_id": Any,
"timestamp": Any,
"features": dict,
"metadata": dict
}
]


### Field Descriptions

**entity_id**  
The identifier for the entity associated with the record.

Example:

101


**timestamp**  
The time associated with the event or record.

Example:

"2026-03-12"


**features**  
Dictionary containing feature values extracted from the dataset.

Example:


{
"amount": 45.00,
"region": "west"
}


**metadata**  
Optional information describing the record source or processing details.

Example:


{
"source": "orders.csv"
}


---

## Contract Guarantees

The adapter guarantees:

- All output records follow the canonical schema.
- Entity identifiers and timestamps are extracted from normalized columns.
- Feature values are preserved from the source dataset.
- Metadata fields may be extended in future versions.

---

## Pipeline Context


Raw Source
↓
Ingestion (detect and load)
↓
Adapter (normalize and map)
↓
Canonical Records


The adapter ensures downstream modules always receive standardized records regardless of the original data source.