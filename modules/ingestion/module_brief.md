# Ingestion Module

## Purpose

Read external datasets into the Opsight pipeline.

## Inputs

Dataset file path

## Outputs

Loaded dataset in a dataframe-like structure for downstream transformation.

## Responsibilities

- detect source format
- load source data
- perform basic input record validation

The ingestion module is responsible only for reading and validating source data before transformation.