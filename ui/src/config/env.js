const DEFAULT_API_BASE_URL =
  "https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;