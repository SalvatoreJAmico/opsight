# Opsight

## 🚀 Live Demo

Frontend

👉 https://agreeable-cliff-08bf3bd0f.2.azurestaticapps.net

API Docs (Swagger)

👉 https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io/docs

Health Check

👉 https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io/health

Opsight is a deployed full-stack ML system running on Azure.  
It ingests real data from Blob Storage, processes it through a pipeline, and provides analytics, anomaly detection, and predictions through a live web interface.

---

## What Is Opsight?

Opsight is an end-to-end operational analytics project that takes raw business-style datasets and turns them into usable analysis outputs.

It combines:

- a modular Python data pipeline  
- a FastAPI backend  
- a React frontend  
- analytics, anomaly detection, and chart visualization  

In one flow, a user can load a dataset, run processing, review quality metrics, inspect charts, and run anomaly or prediction models.

---

## Problem It Solves

Many teams receive data that is inconsistent across files and systems. Before any useful analysis, that data must be standardized and validated.

Opsight demonstrates a practical solution:

- ingest heterogeneous tabular data  
- normalize records into one canonical structure  
- validate records before storage  
- expose analysis results through API endpoints and UI views  

---

## How It Works

### Pipeline Path

- **Ingestion:** load source data (CSV, JSON, Parquet, XLSX, and common URL sources)  
- **Normalization:** map source rows to canonical records  
- **Validation:** apply record checks and quality rules  
- **Storage:** persist valid records (JSON or Parquet)  
- **Analytics Surface:** serve metrics, charts, anomaly detection, and prediction through FastAPI + React  

### System Flow
