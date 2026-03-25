export const DATASETS = [
  {
    id: "sales_csv",
    label: "Sales CSV",
    sourceType: "blob",
    format: "csv",
    location: "opsight-raw/csv/Sample - Superstore.csv",
  },
  {
    id: "transactions_json",
    label: "Transactions JSON",
    sourceType: "blob",
    format: "json",
    location: "opsight-raw/json/mock-transactions.json",
  },
  {
    id: "userdata_parquet",
    label: "User Data Parquet",
    sourceType: "blob",
    format: "parquet",
    location: "opsight-raw/parquet/userdata1.parquet",
  },
  {
    id: "employee_xlsx",
    label: "Employee XLSX",
    sourceType: "blob",
    format: "xlsx",
    location: "opsight-raw/xlsx/Employee-Management-Sample-Data.xlsx",
  },
  {
  id: "sales_sql",
  label: "Sales SQL",
  sourceType: "sql",
  format: "sql",
  location: "Northwind",
  schema: "sales",
  table: "orders"
}
];