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
  const { timeoutMs = 0, ...fetchOptions } = options;
  const controller = timeoutMs > 0 ? new AbortController() : null;
  let timeoutId = null;

  try {
    if (controller) {
      timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    }

    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(fetchOptions.headers || {}),
      },
      ...fetchOptions,
      signal: controller?.signal,
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
    if (error?.name === "AbortError") {
      return {
        ok: false,
        status: 0,
        error: "Request timed out",
        data: null,
      };
    }

    return {
      ok: false,
      status: 0,
      error: error?.message || "Network error",
      data: null,
    };
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

function buildChartPath(path, params = {}) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== "") {
      query.set(key, value);
    }
  });

  const queryString = query.toString();
  return queryString ? `${path}?${queryString}` : path;
}

function withEnhancementParams(params = {}, enhancements = {}) {
  return {
    ...params,
    chart_title: enhancements.title,
    chart_subtitle: enhancements.subtitle,
    x_label: enhancements.xLabel,
    y_label: enhancements.yLabel,
    show_legend: enhancements.showLegend,
    show_grid: enhancements.showGrid,
    color_theme: enhancements.color,
    annotation: enhancements.annotation,
    x_min: enhancements.xMin,
    x_max: enhancements.xMax,
    y_min: enhancements.yMin,
    y_max: enhancements.yMax,
    log_scale_x: enhancements.logScaleX,
    log_scale_y: enhancements.logScaleY,
    clip_mode: enhancements.clipMode,
    clip_percentile: enhancements.clipPercentile,
    clip_max: enhancements.clipMax,
    zoom_preset: enhancements.zoomPreset,
  };
}

export async function getHistogram({ baseUrl, targetVariable, enhancements } = {}) {
  return request(
    buildChartPath("/charts/histogram", withEnhancementParams({ target_variable: targetVariable }, enhancements)),
    { method: "GET" },
    baseUrl,
  );
}

export async function getBarCategory({ baseUrl, targetVariable, compareVariable, enhancements } = {}) {
  return request(
    buildChartPath(
      "/charts/bar-category",
      withEnhancementParams(
        {
          target_variable: targetVariable,
          compare_variable: compareVariable,
        },
        enhancements,
      ),
    ),
    { method: "GET" },
    baseUrl,
  );
}

export async function getBoxplot({ baseUrl, targetVariable, enhancements } = {}) {
  return request(
    buildChartPath("/charts/boxplot", withEnhancementParams({ target_variable: targetVariable }, enhancements)),
    { method: "GET" },
    baseUrl,
  );
}

export async function getScatter({ baseUrl, targetVariable, compareVariable, enhancements } = {}) {
  return request(
    buildChartPath(
      "/charts/scatter",
      withEnhancementParams(
        {
          target_variable: targetVariable,
          compare_variable: compareVariable,
        },
        enhancements,
      ),
    ),
    { method: "GET" },
    baseUrl,
  );
}

export async function getGroupedComparison({ baseUrl, targetVariable, compareVariable, enhancements } = {}) {
  return request(
    buildChartPath(
      "/charts/grouped-comparison",
      withEnhancementParams(
        {
          target_variable: targetVariable,
          compare_variable: compareVariable,
        },
        enhancements,
      ),
    ),
    { method: "GET" },
    baseUrl,
  );
}

export async function getGroupedBoxplot({ baseUrl, targetVariable, compareVariable, enhancements } = {}) {
  return request(
    buildChartPath(
      "/charts/grouped-boxplot",
      withEnhancementParams(
        {
          target_variable: targetVariable,
          compare_variable: compareVariable,
        },
        enhancements,
      ),
    ),
    { method: "GET" },
    baseUrl,
  );
}

export async function getTimeLine({ baseUrl, targetVariable, compareVariable, enhancements } = {}) {
  return request(
    buildChartPath(
      "/charts/time-line",
      withEnhancementParams(
        {
          target_variable: targetVariable,
          compare_variable: compareVariable,
        },
        enhancements,
      ),
    ),
    { method: "GET" },
    baseUrl,
  );
}
export async function getChartOverview({ baseUrl } = {}) {
  return request(ENDPOINTS.CHARTS_OVERVIEW, { method: "GET" }, baseUrl);
}

export async function getCleaningAudit({ baseUrl } = {}) {
  return request(ENDPOINTS.CLEANING_AUDIT, { method: "GET" }, baseUrl);
}

export async function getVariableSelection({ baseUrl } = {}) {
  return request(ENDPOINTS.VARIABLE_SELECTION, { method: "GET" }, baseUrl);
}

export async function saveVariableSelection({ baseUrl, target, compare } = {}) {
  return request(
    ENDPOINTS.VARIABLE_SELECTION,
    { method: "POST", body: JSON.stringify({ target: target ?? null, compare: compare ?? [] }) },
    baseUrl,
  );
}

export async function getHealth() {
  return request(ENDPOINTS.HEALTH, {
    method: "GET",
  });
}

export async function getSessionState() {
  return request(ENDPOINTS.SESSION_STATE, {
    method: "GET",
  });
}

export async function resetSession() {
  return request(ENDPOINTS.SESSION_RESET, {
    method: "POST",
  });
}

export async function startSqlServer(config = {}) {
  return request(ENDPOINTS.SQL_START, {
    method: "POST",
    body: JSON.stringify({
      target: config.target || "local",
    }),
    timeoutMs: config.timeoutMs || 180000,
  }, config.baseUrl);
}

export async function triggerPipeline(payload, config = {}) {
  return request(ENDPOINTS.PIPELINE_TRIGGER, {
    method: "POST",
    body: JSON.stringify(payload),
  }, config.baseUrl);
}

export async function runZscoreAnomaly(config = {}) {
  return request(ENDPOINTS.ANOMALY_DETECTION_ZSCORE, { method: "GET" }, config.baseUrl);
}

export async function runIsolationForestAnomaly(config = {}) {
  return request(ENDPOINTS.ANOMALY_DETECTION_ISOLATION_FOREST, { method: "GET" }, config.baseUrl);
}

export async function runKmeansAnomaly(config = {}) {
  return request(ENDPOINTS.ANOMALY_DETECTION_KMEANS, { method: "GET" }, config.baseUrl);
}

export async function runRegressionPrediction(stepsAhead = 5, config = {}) {
  const path = `${ENDPOINTS.PREDICTION_REGRESSION}?steps_ahead=${encodeURIComponent(stepsAhead)}`;
  return request(path, { method: "GET" }, config.baseUrl);
}

export async function runMovingAveragePrediction(stepsAhead = 5, config = {}) {
  const path = `${ENDPOINTS.PREDICTION_MOVING_AVERAGE}?steps_ahead=${encodeURIComponent(stepsAhead)}`;
  return request(path, { method: "GET" }, config.baseUrl);
}

// Backward-compatible alias for older callers.
export async function runPipeline(payload) {
  return triggerPipeline(payload);
}
