# Persistence Module

## Purpose

Store validated canonical records and establish the persistence boundary for the Opsight pipeline.

## Responsibilities

- accept validated canonical records
- define the storage entry point for Phase 3
- provide a stable place for future file, database, or service-backed storage implementations

## Current Status

This module is a scaffold. The storage interface exists, but backend-specific persistence behavior has not been implemented yet.