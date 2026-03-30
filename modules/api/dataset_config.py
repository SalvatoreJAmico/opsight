DATASET_MAP = {
    "sales_csv": {
        "source_type": "blob",
        "format": "csv",
        "path": "opsight-raw/csv/Sample - Superstore.csv",
    },
    "transactions_json": {
        "source_type": "blob",
        "format": "json",
        "path": "opsight-raw/json/mock-transactions.json",
    },
    "userdata_parquet": {
        "source_type": "blob",
        "format": "parquet",
        "path": "opsight-raw/parquet/userdata1.parquet",
    },
    "employee_xlsx": {
        "source_type": "blob",
        "format": "xlsx",
        "path": "opsight-raw/xlsx/Employee-Management-Sample-Data.xlsx",
    },
    "sales_sql": {
        "source_type": "sql",
        "database": "Northwind",
        "schema": "dbo",
        "table": "Orders",
    },
}
