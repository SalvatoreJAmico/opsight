# Opsight API Documentation

## Overview

The Opsight API is a FastAPI-based backend service that provides endpoints for:
- **Data Ingestion**: Trigger pipelines to ingest data from various sources (CSV, JSON, Parquet, XLSX, SQL)
- **Data Retrieval**: Fetch persisted records and entity-specific data
- **Machine Learning**: Execute anomaly detection and predictive models
- **Visualization**: Generate charts and statistical summaries
- **System Status**: Monitor pipeline execution and session state

**Base URL**: `http://localhost:8000` (default)  
**Version**: See `/health` endpoint  
**API Type**: RESTful HTTP

---

## API Endpoints

### Health & System

#### `GET /health`
Returns the health status and version of the API.

**Response Status**: `200 OK`

**Example Response**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### Session Management

#### `GET /session/state`
Retrieves the current session state, including the active dataset and pipeline/model status.

**Response Status**: `200 OK`

**Example Response**:
```json
{
  "active_dataset": "sales_csv",
  "pipeline_status": "idle",
  "anomaly_status": "idle",
  "prediction_status": "idle"
}
```

#### `POST /session/reset`
Resets the session state and clears all persisted records. All ML model results and visualization data are cleared.

**Response Status**: `200 OK`

**Example Response**:
```json
{
  "status": "reset",
  "session": {
    "active_dataset": null,
    "pipeline_status": "idle",
    "anomaly_status": "idle",
    "prediction_status": "idle"
  }
}
```

---

### Data Ingestion & Pipeline

#### `POST /pipeline/trigger`
Triggers the ingestion and processing pipeline for a selected dataset. Supports multiple source types (CSV, JSON, Parquet, XLSX blob storage and SQL databases).

**Request Body**:
```json
{
  "target": "local",
  "dataset_id": "sales_csv"
}
```

**Parameters**:
- `target` (required): Deployment target - `"local"` or `"cloud"` (string)
- `dataset_id` (required): Dataset identifier from the dataset catalog (string)

**Available Datasets**:
- `sales_csv`: CSV file from blob storage
- `transactions_json`: JSON file from blob storage  
- `userdata_parquet`: Parquet file from blob storage
- `employee_xlsx`: Excel file from blob storage
- `sales_sql`: SQL database table (Northwind.dbo.Orders)

**Response Status**: 
- `200 OK` - Pipeline executed successfully
- `400 Bad Request` - Invalid target or dataset_id
- `500 Internal Server Error` - Pipeline execution failed

**Example Response (Success)**:
```json
{
  "status": "processed",
  "source_path": "/path/to/data/Sample - Superstore.csv",
  "records_ingested": 9994,
  "records_valid": 9500,
  "records_invalid": 494,
  "records_persisted": 9500,
  "dataset_id": "sales_csv",
  "dataset_source_type": "blob",
  "dataset_path": "opsight-raw/csv/Sample - Superstore.csv"
}
```

**Example Response (Failure)**:
```json
{
  "detail": "Pipeline failure at stage: ingestion. CSV parsing error on row 423"
}
```

#### `POST /data`
Legacy endpoint for custom data ingestion. Requires upload access code verification.

**Request Body**:
```json
{
  "source_path": "/path/to/data.csv"
}
```

**Response Status**:
- `200 OK` - Data ingested successfully
- `403 Forbidden` - Invalid or missing access code
- `422 Unprocessable Entity` - Missing source_path
- `500 Internal Server Error` - Pipeline failure

**Note**: This endpoint validates the upload access code via header. See `access_control.py` for authentication details.

---

### Pipeline Status

#### `GET /pipeline/status`
Retrieves the results and metadata from the most recent pipeline execution.

**Response Status**: `200 OK`

**Example Response**:
```json
{
  "status": "SUCCESS",
  "timestamp": "2025-03-26T10:30:45",
  "pipeline": "Main Data Pipeline",
  "stage": "complete",
  "records_ingested": 9994,
  "records_valid": 9500,
  "records_invalid": 494,
  "records_persisted": 9500,
  "validation_rules_passed": 8900,
  "validation_rules_failed": 600,
  "runtime_seconds": 23.45
}
```

**Response when no runs recorded**:
```json
{
  "status": "no runs recorded"
}
```

---

### Data & Entities

#### `GET /entity/{entity_id}`
Retrieves all records for a specific entity from the persisted dataset.

**Path Parameters**:
- `entity_id` (required): The unique identifier of the entity (string)

**Response Status**:
- `200 OK` - Entity found with records
- `404 Not Found` - Entity not found in dataset

**Example Request**:
```
GET /entity/customer_12345
```

**Example Response (Success)**:
```json
{
  "entity_id": "customer_12345",
  "records": [
    {
      "entity_id": "customer_12345",
      "timestamp": "2025-01-15",
      "features": {
        "sales": 1500.50,
        "quantity": 5,
        "region": "West"
      }
    },
    {
      "entity_id": "customer_12345",
      "timestamp": "2025-02-20",
      "features": {
        "sales": 2100.00,
        "quantity": 7,
        "region": "West"
      }
    }
  ]
}
```

**Example Response (Not Found)**:
```json
{
  "detail": "Entity not found"
}
```

---

### Charts & Visualization

#### `GET /charts/overview`
Returns a statistical summary and metadata about the currently loaded dataset. Includes min/max/mean values and field information.

**Response Status**: 
- `200 OK` - Dataset loaded with summary statistics
- `422 Unprocessable Entity` - No dataset loaded

**Example Response**:
```json
{
  "source": "sales_csv",
  "rows": 9500,
  "variables": 21,
  "fields": ["order_id", "customer_id", "order_date", "sales", "quantity", "region", "category"],
  "min": 5.25,
  "max": 12000.00,
  "mean": 456.78,
  "count": 8900
}
```

#### `GET /charts/histogram`
Generates a histogram visualization for the primary numeric feature in the dataset.

**Response Status**:
- `200 OK` - Chart generated successfully
- `422 Unprocessable Entity` - No dataset loaded
- `500 Internal Server Error` - Chart generation failed

**Example Response**:
```json
{
  "image": "/static/plots/histogram_2025-03-26_10-30-45.png"
}
```

#### `GET /charts/bar-category`
Generates a bar chart grouped by categories for the primary string feature in the dataset.

**Response Status**:
- `200 OK` - Chart generated successfully
- `422 Unprocessable Entity` - No dataset loaded
- `500 Internal Server Error` - Chart generation failed

**Example Response**:
```json
{
  "image": "/static/plots/bar_category_2025-03-26_10-30-45.png"
}
```

#### `GET /charts/boxplot`
Generates a boxplot visualization of the primary numeric feature distribution.

**Response Status**:
- `200 OK` - Chart generated successfully
- `422 Unprocessable Entity` - No dataset loaded
- `500 Internal Server Error` - Chart generation failed

**Example Response**:
```json
{
  "image": "/static/plots/boxplot_2025-03-26_10-30-45.png"
}
```

#### `GET /charts/scatter`
Generates a scatter plot comparing the primary and secondary numeric features.

**Response Status**:
- `200 OK` - Chart generated successfully
- `422 Unprocessable Entity` - No dataset loaded
- `500 Internal Server Error` - Chart generation failed

**Example Response**:
```json
{
  "image": "/static/plots/scatter_2025-03-26_10-30-45.png"
}
```

#### `GET /charts/grouped-comparison`
Generates a grouped comparison chart combining numeric features with categorical grouping.

**Response Status**:
- `200 OK` - Chart generated successfully
- `422 Unprocessable Entity` - No dataset loaded
- `500 Internal Server Error` - Chart generation failed

**Example Response**:
```json
{
  "image": "/static/plots/grouped_comparison_2025-03-26_10-30-45.png"
}
```

---

### Machine Learning - Anomaly Detection

These endpoints execute anomaly detection models on the persisted dataset. All require a dataset to be loaded first via `/pipeline/trigger`.

#### `GET /ml/anomaly/zscore`
Detects anomalies using Z-Score method. Identifies points that deviate significantly from the mean (threshold: 1.5 standard deviations).

**Response Status**:
- `200 OK` - Model executed successfully
- `422 Unprocessable Entity` - No dataset loaded

**Example Response**:
```json
{
  "result": [
    {
      "entity_id": "customer_001",
      "timestamp": "2025-01-15",
      "value": 5000.00,
      "is_anomaly": true,
      "zscore": 2.34
    },
    {
      "entity_id": "customer_002",
      "timestamp": "2025-01-15",
      "value": 450.00,
      "is_anomaly": false,
      "zscore": 0.45
    }
  ],
  "summary": {
    "total_records": 9500,
    "anomaly_count": 234,
    "anomaly_percentage": 2.47
  }
}
```

#### `GET /ml/anomaly/isolation-forest`
Detects anomalies using Isolation Forest algorithm. Identifies outliers by isolating them in the feature space (contamination threshold: 0.1).

**Response Status**:
- `200 OK` - Model executed successfully
- `422 Unprocessable Entity` - No dataset loaded

**Example Response**:
```json
{
  "result": [
    {
      "entity_id": "customer_001",
      "timestamp": "2025-01-15",
      "value": 5000.00,
      "is_anomaly": true,
      "anomaly_score": -0.85
    },
    {
      "entity_id": "customer_002",
      "timestamp": "2025-01-15",
      "value": 450.00,
      "is_anomaly": false,
      "anomaly_score": 0.15
    }
  ],
  "summary": {
    "total_records": 9500,
    "anomaly_count": 950,
    "anomaly_percentage": 10.0
  }
}
```

#### `GET /ml/anomaly/kmeans`
Detects anomalies using K-Means clustering. Identifies points as anomalies based on distance from cluster centroids (clusters: 3).

**Response Status**:
- `200 OK` - Model executed successfully
- `422 Unprocessable Entity` - No dataset loaded

**Example Response**:
```json
{
  "status": "completed",
  "anomalies": 312,
  "total": 9500,
  "summary": {
    "total_records": 9500,
    "anomaly_count": 312,
    "anomaly_percentage": 3.29,
    "notes": "K-Means clustering using distance from centroid."
  },
  "result": [
    {
      "entity_id": "customer_001",
      "timestamp": "2025-01-15",
      "value": 5000.00,
      "is_anomaly": true,
      "distance_to_centroid": 2.45,
      "cluster": 1
    }
  ]
}
```

---

### Machine Learning - Predictive Models

These endpoints execute predictive models on the persisted dataset. All require a dataset to be loaded first via `/pipeline/trigger`.

#### `GET /ml/prediction/regression`
Predicts future values using Linear Regression model.

**Query Parameters**:
- `steps_ahead` (optional, default: 5): Number of future time steps to predict (integer)

**Response Status**:
- `200 OK` - Model executed successfully
- `422 Unprocessable Entity` - No dataset loaded

**Example Request**:
```
GET /ml/prediction/regression?steps_ahead=10
```

**Example Response**:
```json
{
  "result": [
    {
      "entity_id": "customer_001",
      "timestamp": "2025-03-27",
      "value": 4850.25,
      "is_prediction": true,
      "confidence": 0.87
    },
    {
      "entity_id": "customer_001",
      "timestamp": "2025-03-28",
      "value": 4920.50,
      "is_prediction": true,
      "confidence": 0.85
    }
  ]
}
```

#### `GET /ml/prediction/moving-average`
Predicts future values using Moving Average model with a window size of 2.

**Query Parameters**:
- `steps_ahead` (optional, default: 5): Number of future time steps to predict (integer)

**Response Status**:
- `200 OK` - Model executed successfully
- `422 Unprocessable Entity` - No dataset loaded

**Example Request**:
```
GET /ml/prediction/moving-average?steps_ahead=10
```

**Example Response**:
```json
{
  "result": [
    {
      "entity_id": "customer_001",
      "timestamp": "2025-03-27",
      "value": 4750.00,
      "is_prediction": true
    },
    {
      "entity_id": "customer_001",
      "timestamp": "2025-03-28",
      "value": 4800.00,
      "is_prediction": true
    }
  ]
}
```

---

## Common Response Patterns

### Success Response (200 OK)
All successful endpoints return a JSON object with endpoint-specific fields.

### Error Responses

**400 Bad Request**:
```json
{
  "detail": "Invalid request parameter"
}
```

**403 Forbidden** (access control):
```json
{
  "detail": "Invalid or missing access code"
}
```

**404 Not Found**:
```json
{
  "detail": "Entity not found"
}
```

**422 Unprocessable Entity**:
```json
{
  "detail": "No dataset loaded. Select and run a dataset to view charts."
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Pipeline failure: [detailed error message]"
}
```

---

## Data Flow & Dependencies

```
1. Load Dataset
   POST /pipeline/trigger → records persisted to local storage

2. Check Dataset Info
   GET /charts/overview → metadata about loaded dataset

3. View Data by Entity
   GET /entity/{entity_id} → fetch entity records

4. Generate Visualizations
   GET /charts/* → generate PNG charts from persisted records

5. Run ML Models
   GET /ml/anomaly/* → execute anomaly detection
   GET /ml/prediction/* → execute prediction models

6. Monitor Progress
   GET /session/state → check pipeline and model status
   GET /pipeline/status → last execution results
```

**Important**: All chart and ML endpoints require a dataset to be loaded first. Using these endpoints without loading data will return a 422 status with a message to select and run a dataset.

---

## Rate Limiting & Performance Notes

- **No explicit rate limiting** is currently implemented
- **Pipeline execution** may take 10-30 seconds depending on dataset size
- **ML model execution** typically completes in 5-15 seconds
- **Chart generation** completes in 1-5 seconds
- Request logging is enabled; check logs for timing details

---

## Authentication & Access Control

- The `/data` endpoint requires an `upload_access_code` parameter for security
- See `modules/api/access_control.py` for implementation details
- Other endpoints do not currently require authentication
- All endpoints validate the request format using Pydantic models

---

## Logging

All requests are logged with:
- HTTP method and path
- Response status code
- Request runtime in milliseconds
- Errors and exceptions with full stack traces

Check `logs/` directory for application logs (when running with file logging enabled).

---

## Future Considerations

- SQL datasets require `SQL_CONNECTION_STRING` to be configured in environment variables.
- Consider adding request validation/rate limiting for production deployments  
- API documentation is versioned alongside schema changes
