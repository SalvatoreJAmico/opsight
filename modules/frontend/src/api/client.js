import { API_BASE_URL } from "../config/env";
import { ENDPOINTS } from "./endpoints";


function normalizeBaseUrl(baseUrlOverride = null) {
  return (baseUrlOverride || API_BASE_URL).replace(/\/+$/, "");
}


export function resolveApiAssetUrl(assetPath, baseUrlOverride = null) {
  if (!assetPath) {
    return "";
  }

  if (/^https?:\/\//i.test(assetPath)) {
    return assetPath;
  }

  const requestBaseUrl = normalizeBaseUrl(baseUrlOverride);
  const normalizedAssetPath = assetPath.startsWith("/") ? assetPath : `/${assetPath}`;

  return `${requestBaseUrl}${normalizedAssetPath}`;
}

async function request(path, options = {}, baseUrlOverride = null) {
  const requestBaseUrl = normalizeBaseUrl(baseUrlOverride);
  const url = `${requestBaseUrl}${path}`;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        error:
          typeof data === "string"
            ? data
            : data?.detail || data?.message || "Request failed",
        data: null,
      };
    }

    return {
      ok: true,
      status: response.status,
      error: null,
      data,
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      error: error?.message || "Network error",
      data: null,
    };
  }
}
export async function getHistogram({ baseUrl } = {}) {
  return request("/charts/histogram", { method: "GET" }, baseUrl);
}

export async function getBarCategory({ baseUrl } = {}) {
  return request("/charts/bar-category", { method: "GET" }, baseUrl);
}

export async function getBoxplot({ baseUrl } = {}) {
  return request("/charts/boxplot", { method: "GET" }, baseUrl);
}

export async function getScatter({ baseUrl } = {}) {
  return request("/charts/scatter", { method: "GET" }, baseUrl);
}

export async function getGroupedComparison({ baseUrl } = {}) {
  return request("/charts/grouped-comparison", { method: "GET" }, baseUrl);
}
export async function getHealth() {
  return request(ENDPOINTS.HEALTH, {
    method: "GET",
  });
}

export async function triggerPipeline(payload, config = {}) {
  return request(ENDPOINTS.PIPELINE_TRIGGER, {
    method: "POST",
    body: JSON.stringify(payload),
  }, config.baseUrl);
}

// Backward-compatible alias for older callers.
export async function runPipeline(payload) {
  return triggerPipeline(payload);
}