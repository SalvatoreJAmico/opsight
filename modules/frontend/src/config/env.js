const DEV_DEFAULT_API_BASE_URL = "/api-local";
const PROD_DEFAULT_API_BASE_URL =
  "https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io";

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

const fallbackBaseUrl = import.meta.env.DEV
  ? DEV_DEFAULT_API_BASE_URL
  : PROD_DEFAULT_API_BASE_URL;

export const API_BASE_URL = (configuredBaseUrl || fallbackBaseUrl).replace(/\/+$/, "");