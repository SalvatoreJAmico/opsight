# Adapter Module

## Purpose
The adapter module converts loaded input datasets into the Opsight canonical schema.
It standardizes records so the rest of the pipeline can process them consistently.

## Responsibilities
- Normalize column names and roles
- Map records to the canonical schema
- Output standardized records for downstream modules

## Input Data Sources
The adapter may receive data from multiple formats:

- CSV
- TSV
- JSON
- Excel
- Parquet
- SQL sources

These sources are detected and loaded by ingestion before adapter transformation.

## Output Canonical Schema
Each record is transformed into the Opsight canonical structure:


entity_id
timestamp
features
metadata


Example:


{
entity_id: 101,
timestamp: "2026-03-13",
features: {
amount: 45.00,
region: "west"
},
metadata: {}
}


## Role in the Opsight Pipeline
The adapter sits between ingestion and downstream processing.

Pipeline flow:


Ingestion (read)
↓
Adapter (transform)
↓
Canonical Records
↓
Feature / analytics modules


The adapter ensures all downstream components receive data in a consistent format regardless of the original source.