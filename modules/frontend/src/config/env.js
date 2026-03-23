const AZURE_URL =
  "https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io";

// Per-target URL resolution.
// In dev Vite proxies /api-local and /api-cloud to the real backends.
// In production (built/deployed) real URLs are required; set VITE_LOCAL_API_URL
// and VITE_CLOUD_API_URL at build time to override the defaults.
const LOCAL_API_URL = import.meta.env.DEV
  ? "/api-local"
  : (import.meta.env.VITE_LOCAL_API_URL?.trim() || "http://127.0.0.1:8000");

const CLOUD_API_URL = import.meta.env.DEV
  ? "/api-cloud"
  : (import.meta.env.VITE_CLOUD_API_URL?.trim() || AZURE_URL);

/**
 * Resolves the base URL for API requests given a logical target name.
 * Works consistently in local dev (via Vite proxy) and in deployed builds
 * (via real URLs from env vars or built-in defaults).
 *
 * @param {"local"|"cloud"} target
 * @returns {string}
 */
export function resolveBaseUrl(target) {
  return target === "local" ? LOCAL_API_URL : CLOUD_API_URL;
}

// Single-target fallback used by components that don't expose a selector.
const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

const fallbackBaseUrl = import.meta.env.DEV ? "/api-local" : AZURE_URL;

export const API_BASE_URL = (configuredBaseUrl || fallbackBaseUrl).replace(/\/+$/, "");