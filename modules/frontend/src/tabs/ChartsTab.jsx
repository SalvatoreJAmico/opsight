import React, { useEffect, useState } from "react";
import {
  getHistogram,
  getBarCategory,
  getBoxplot,
  getScatter,
  getGroupedComparison,
  getChartOverview,
  resolveApiAssetUrl,
} from "../api/client";
import { chartCatalog } from "../catalog/chartCatalog";
import { resolveBaseUrl } from "../config/env";

const DEFAULT_TARGET_VARIABLE = "Sales";
const FALLBACK_TARGET_OPTIONS = [DEFAULT_TARGET_VARIABLE];
const FALLBACK_COMPARE_OPTIONS = ["Profit", "Quantity", "Discount", "Category", "Order Date"];
const summaryCardStyle = {
  border: "1px solid #374151",
  borderRadius: "12px",
  padding: "1rem",
  background: "#111827",
  color: "#f9fafb",
  textAlign: "center",
  minHeight: "100%",
  width: "100%",
  boxSizing: "border-box",
  boxShadow: "0 8px 20px rgba(0, 0, 0, 0.18)",
};
const summaryCardTitleStyle = {
  marginTop: 0,
  marginBottom: "0.75rem",
  fontSize: "0.95rem",
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#e5e7eb",
};
const summaryMetricStyle = {
  margin: "0.3rem 0",
  color: "#d1d5db",
};
const summaryDividerStyle = {
  border: 0,
  borderTop: "1px solid #374151",
  margin: "0.8rem 0",
};

function normalizeFieldName(fieldName) {
  return String(fieldName || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\s+/g, " ");
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(objectUrl);
}

export default function ChartsTab({ activeDatasetId = null }) {
  const isDev = import.meta.env.DEV;
  const [target, setTarget] = useState(isDev ? "local" : "cloud");
  const [activeChart, setActiveChart] = useState("");
  const [chartImages, setChartImages] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState("");
  const [targetVariable, setTargetVariable] = useState(DEFAULT_TARGET_VARIABLE);
  const [compareVariable, setCompareVariable] = useState(FALLBACK_COMPARE_OPTIONS[0]);

  useEffect(() => {
    if (!activeDatasetId) {
      setOverview(null);
      setOverviewError("");
      return;
    }

    let cancelled = false;
    setOverviewLoading(true);
    setOverviewError("");

    const baseUrl = resolveBaseUrl(target);
    getChartOverview({ baseUrl }).then((result) => {
      if (cancelled) return;
      setOverviewLoading(false);
      if (result.ok) {
        setOverview(result.data);
      } else {
        setOverviewError(result.error || "Failed to load dataset overview.");
      }
    });

    return () => {
      cancelled = true;
    };
  }, [activeDatasetId, target]);

  useEffect(() => {
    const nextTarget = overview?.assignment_analysis?.target_variable || DEFAULT_TARGET_VARIABLE;
    const nextCompareOptions = overview?.assignment_analysis?.compare_options || FALLBACK_COMPARE_OPTIONS;

    if (targetVariable !== nextTarget) {
      setTargetVariable(nextTarget);
    }

    if (!nextCompareOptions.includes(compareVariable)) {
      setCompareVariable(nextCompareOptions[0] || FALLBACK_COMPARE_OPTIONS[0]);
    }
  }, [overview, targetVariable, compareVariable]);

  const targetOptions = overview?.assignment_analysis?.target_options || FALLBACK_TARGET_OPTIONS;
  const compareOptions = overview?.assignment_analysis?.compare_options || FALLBACK_COMPARE_OPTIONS;
  const missingValueEntries = Object.entries(overview?.missing_by_column || {}).filter(([, missing]) =>
    Number(missing) > 0,
  );
  const selectedVariables = Array.from(
    new Set(
      [targetVariable, compareVariable]
        .filter(Boolean)
        .map((fieldName) => normalizeFieldName(fieldName)),
    ),
  );
  const filteredNumericSummary = (overview?.numeric_summary || []).filter((item) =>
    selectedVariables.includes(normalizeFieldName(item.field)),
  );
  const dateFieldNames = new Set(
    (overview?.date_summary || []).map((item) => normalizeFieldName(item.field)),
  );
  const filteredDateSummary = (overview?.date_summary || []).filter((item) =>
    selectedVariables.includes(normalizeFieldName(item.field)),
  );
  const filteredCategoricalSummary = (overview?.categorical_summary || []).filter((item) =>
    selectedVariables.includes(normalizeFieldName(item.field)) &&
    !dateFieldNames.has(normalizeFieldName(item.field)),
  );

  const renderSummaryCardsForVariable = (normalizedFieldName) => (
    <>
      {filteredNumericSummary
        .filter((item) => normalizeFieldName(item.field) === normalizedFieldName)
        .map((item) => (
          <div
            key={`numeric-${item.field}`}
            data-testid={`numeric-summary-card-${normalizeFieldName(item.field).replace(/\s+/g, "-")}`}
            style={summaryCardStyle}
          >
            <p style={summaryCardTitleStyle}>{item.field}</p>
            <p style={summaryMetricStyle}>Count: {item.count}</p>
            <p style={summaryMetricStyle}>Missing: {item.missing}</p>
            <hr style={summaryDividerStyle} />
            <p style={summaryMetricStyle}>Min: {item.min ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Max: {item.max ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Mean: {item.mean ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Median: {item.median ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Std Dev: {item.std ?? "N/A"}</p>
          </div>
        ))}

      {filteredDateSummary
        .filter((item) => normalizeFieldName(item.field) === normalizedFieldName)
        .map((item) => (
          <div
            key={`date-${item.field}`}
            data-testid={`date-summary-card-${normalizeFieldName(item.field).replace(/\s+/g, "-")}`}
            style={summaryCardStyle}
          >
            <p style={summaryCardTitleStyle}>{item.field}</p>
            <p style={summaryMetricStyle}>Count: {item.count}</p>
            <p style={summaryMetricStyle}>Missing: {item.missing}</p>
            <hr style={summaryDividerStyle} />
            <p style={summaryMetricStyle}>Min Date: {item.min_date ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Max Date: {item.max_date ?? "N/A"}</p>
          </div>
        ))}

      {filteredCategoricalSummary
        .filter((item) => normalizeFieldName(item.field) === normalizedFieldName)
        .map((item) => (
          <div
            key={`categorical-${item.field}`}
            data-testid={`categorical-summary-card-${normalizeFieldName(item.field).replace(/\s+/g, "-")}`}
            style={summaryCardStyle}
          >
            <p style={summaryCardTitleStyle}>{item.field}</p>
            <p style={summaryMetricStyle}>Unique: {item.unique}</p>
            <p style={summaryMetricStyle}>Missing: {item.missing}</p>
            <hr style={summaryDividerStyle} />
            {item.top_values?.length ? (
              <div>
                {item.top_values.map((entry, index) => (
                  <p
                    key={`cat-${item.field}-${entry.value}-${index}`}
                    style={summaryMetricStyle}
                  >
                    {entry.value}: {entry.count}
                  </p>
                ))}
              </div>
            ) : null}
          </div>
        ))}
    </>
  );

  const loadChartById = async (chartId) => {
    const baseUrl = resolveBaseUrl(target);
    switch (chartId) {
      case "histogram":
        return getHistogram({ baseUrl, targetVariable });
      case "bar-category":
        return getBarCategory({ baseUrl, targetVariable, compareVariable });
      case "boxplot":
        return getBoxplot({ baseUrl, targetVariable });
      case "scatter":
        return getScatter({ baseUrl, targetVariable, compareVariable });
      case "grouped-comparison":
        return getGroupedComparison({ baseUrl, targetVariable, compareVariable });
      default:
        return { ok: false, error: "Unsupported chart selection." };
    }
  };

  const handleExportSummary = () => {
    if (!overview) {
      return;
    }

    const datasetName = overview.source_metadata?.dataset_id || activeDatasetId || "dataset";
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `${datasetName}-summary-${timestamp}.json`;

    downloadJson(filename, {
      source: overview.source,
      source_metadata: overview.source_metadata,
      shape: overview.shape,
      fields: overview.fields,
      assignment_analysis: overview.assignment_analysis,
      missing_by_column: overview.missing_by_column,
      numeric_summary: overview.numeric_summary,
      date_summary: overview.date_summary,
      categorical_summary: overview.categorical_summary,
    });
  };

  const handleChartSelect = async (chartId) => {
    setError("");
    setActiveChart(chartId);
    setLoading(true);

    const response = await loadChartById(chartId);

    setLoading(false);

    if (!response.ok) {
      setActiveChart("");
      setError(response.error || "Chart request failed.");
      return;
    }

    const resolvedImageUrl = resolveApiAssetUrl(
      response.data?.image,
      resolveBaseUrl(target)
    );

    if (!resolvedImageUrl) {
      setActiveChart("");
      setError("Chart response did not include an image path.");
      return;
    }

    const cacheBustedImageUrl = `${resolvedImageUrl}${resolvedImageUrl.includes("?") ? "&" : "?"}t=${Date.now()}`;

    setChartImages((prev) => ({
      ...prev,
      [chartId]: cacheBustedImageUrl,
    }));
  };


const getChartExplainability = (chartId) => {
  switch (chartId) {
    case "histogram":
      return {
        what: "This chart shows how many records fall into each value range.",
        time: "Time is not used. Values are compared across the full dataset.",
        comparison: "It compares frequencies of value ranges.",
        where: "The chart image above is the result.",
      };

    case "bar-category":
      return {
        what: "This chart shows how records are distributed by group.",
        time: "Time is not used. Groups are compared across the full dataset.",
        comparison: "It compares record counts between groups.",
        where: "The chart image above is the result.",
      };

    case "boxplot":
      return {
        what: "This chart summarizes typical values and possible outliers.",
        time: "Time is not used. Values are compared across the full dataset.",
        comparison: "It compares median, spread, and outliers in the value field.",
        where: "The chart image above is the result.",
      };

    case "scatter":
      return {
        what: "This chart shows how one value field moves relative to another.",
        time: "Time is not used. Pairs of values are compared across the full dataset.",
        comparison: "It compares value-to-value pairs to show correlation patterns.",
        where: "The chart image above is the result.",
      };

    case "grouped-comparison":
      return {
        what: "This chart shows average values for each group.",
        time: "Time is not used. Groups are compared across the full dataset.",
        comparison: "It compares group-level average values.",
        where: "The chart image above is the result.",
      };

    default:
      return {
        what: "No explanation is available for this chart yet.",
        time: "",
        comparison: "",
        where: "",
      };
  }
};

const getChartContextEntries = (chartId, targetVariable, compareVariable) => {
  switch (chartId) {
    case "histogram":
    case "boxplot":
      return [["target_variable", targetVariable]];
    case "bar-category":
      return [["compare_variable", compareVariable]];
    case "scatter":
    case "grouped-comparison":
      return [
        ["target_variable", targetVariable],
        ["compare_variable", compareVariable],
      ];
    default:
      return [];
  }
};






  return (
    <div>
      <h2>Charts</h2>

      <h3>Dataset Overview</h3>
      {!activeDatasetId ? (
        <p style={{ opacity: 0.7 }}>
          No dataset loaded — select and run a dataset to view charts.
        </p>
      ) : overviewLoading ? (
        <p>Loading dataset overview...</p>
      ) : overviewError ? (
        <p style={{ color: "#c00" }}>{overviewError}</p>
      ) : overview ? (
        <>
          {activeDatasetId && overview.source && overview.source !== activeDatasetId && (
            <p style={{ color: "#b8860b", fontWeight: 600, marginBottom: "0.5rem" }}>
              Note: charts show data from &ldquo;{overview.source}&rdquo;. Run the selected dataset to update.
            </p>
          )}
          <button
            type="button"
            onClick={handleExportSummary}
            style={{
              marginTop: "0.5rem",
              marginBottom: "0.5rem",
              padding: "0.45rem 0.8rem",
              borderRadius: "6px",
              border: "1px solid #ccc",
              cursor: "pointer",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            Export Summary (JSON)
          </button>

          <div className="summary-full">
            <div style={summaryCardStyle}>
              <p style={summaryCardTitleStyle}>Dataset Summary</p>
              <p style={summaryMetricStyle}>Source: {overview.source}</p>
              {overview.source_metadata?.source_location ? (
                <p style={summaryMetricStyle}>Source Location: {overview.source_metadata.source_location}</p>
              ) : null}
              {overview.source_metadata?.source_url ? (
                <p style={summaryMetricStyle}>Source URL: {overview.source_metadata.source_url}</p>
              ) : null}
              <hr style={summaryDividerStyle} />
              <p style={summaryMetricStyle}>Rows: {overview.rows}</p>
              {overview.shape ? (
                <p style={summaryMetricStyle}>Columns: {overview.shape.columns}</p>
              ) : null}
              {overview.variables != null && <p style={summaryMetricStyle}>Analysis Variables: {overview.variables}</p>}
              {overview.fields && <p style={summaryMetricStyle}>Analysis Fields: {overview.fields.join(", ")}</p>}
              {overview.shape ? (
                <p style={summaryMetricStyle}>Shape: {overview.shape.rows} x {overview.shape.columns}</p>
              ) : null}
              <hr style={summaryDividerStyle} />
              {overview.min != null && <p style={summaryMetricStyle}>Min: {overview.min}</p>}
              {overview.max != null && <p style={summaryMetricStyle}>Max: {overview.max}</p>}
              {overview.mean != null && <p style={summaryMetricStyle}>Mean: {overview.mean}</p>}
              {overview.count != null && <p style={summaryMetricStyle}>Count: {overview.count}</p>}
              <hr style={summaryDividerStyle} />
              {missingValueEntries.length ? (
                <div>
                  <p style={{ ...summaryMetricStyle, fontWeight: 600 }}>Missing Values:</p>
                  {missingValueEntries.map(([field, missing]) => (
                    <p key={`missing-${field}`} style={summaryMetricStyle}>
                      {field}: {missing}
                    </p>
                  ))}
                </div>
              ) : (
                <p style={summaryMetricStyle}>Missing Values: None detected</p>
              )}
            </div>
          </div>

          <h3>Analysis Variables</h3>
          <div className="summary-grid">
            <div className="summary-variable-column">
              <label
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                  fontWeight: 600,
                  alignItems: "center",
                  marginBottom: "1rem",
                }}
              >
                <span>Target Variable</span>
                <select
                  value={targetVariable}
                  onChange={(event) => setTargetVariable(event.target.value)}
                  disabled={!activeDatasetId || overviewLoading}
                  style={{ minWidth: "12rem", padding: "0.45rem" }}
                >
                  {targetOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <div className="summary-variable-cards">
                {renderSummaryCardsForVariable(normalizeFieldName(targetVariable))}
              </div>
            </div>

            <div className="summary-variable-column">
              <label
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                  fontWeight: 600,
                  alignItems: "center",
                  marginBottom: "1rem",
                }}
              >
                <span>Compare Variable</span>
                <select
                  value={compareVariable}
                  onChange={(event) => setCompareVariable(event.target.value)}
                  disabled={!activeDatasetId || overviewLoading || compareOptions.length === 0}
                  style={{ minWidth: "12rem", padding: "0.45rem" }}
                >
                  {compareOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <div className="summary-variable-cards">
                {renderSummaryCardsForVariable(normalizeFieldName(compareVariable))}
              </div>
            </div>
          </div>
        </>
      ) : null}

      <p style={{ marginBottom: "1rem", opacity: 0.85 }}>
        Each chart includes guidance on what it shows, when to use it, and whether it is recommended for the current dataset.
      </p>

      <div style={{ marginBottom: "1.25rem" }}>
        {isDev && (
          <>
            <div style={{ fontWeight: 600, marginBottom: "0.75rem", fontSize: "0.9rem", textAlign: "center" }}>Dev — API Target:</div>
            <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <button
                type="button"
                onClick={() => setTarget("local")}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  fontWeight: target === "local" ? 700 : 400,
                  background: target === "local" ? "#e8f0fe" : "transparent",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Local
              </button>
              <button
                type="button"
                onClick={() => setTarget("cloud")}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  fontWeight: target === "cloud" ? 700 : 400,
                  background: target === "cloud" ? "#e8f0fe" : "transparent",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Cloud
              </button>
            </div>
            <p style={{ marginTop: "0.25rem", opacity: 0.85, fontSize: "0.9rem" }}>
              Target: <strong>{target === "local" ? "Local API (this computer)" : "Deployed API (cloud)"}</strong>
            </p>
          </>
        )}
      </div>

      <h3>Available Charts</h3>
      {chartCatalog.map((chart) => (
        <div key={chart.id} style={{ marginBottom: "1rem" }}>
          <label
            style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 600 }}
          >
            <input
              type="radio"
              name="chart-selection"
              checked={activeChart === chart.id}
              onChange={() => handleChartSelect(chart.id)}
            />
            {chart.title}
          </label>

          <p><strong>Why this chart:</strong> {chart.purpose}</p>
          <p><em>{chart.whenToUse}</em></p>
          <p>
            Recommended for current dataset:{" "}
            <strong>{chart.recommended ? "Yes" : "No"}</strong>
          </p>
          <p style={{ opacity: 0.8 }}>{chart.recommendationReason}</p>

          {loading && activeChart === chart.id ? (
            <p style={{ marginTop: "0.75rem" }}>Loading chart...</p>
          ) : null}

         {activeChart === chart.id && chartImages[chart.id] ? (
  <div style={{ marginTop: "0.75rem" }}>
    <img
      src={chartImages[chart.id]}
      alt={`${chart.title} visualization`}
      style={{ maxWidth: "100%", border: "1px solid #ccc", borderRadius: "8px" }}
    />

    {getChartContextEntries(chart.id, targetVariable, compareVariable).length > 0 ? (
      <div
        style={{
          marginTop: "0.75rem",
          padding: "0.75rem",
          border: "1px solid #ddd",
          borderRadius: "8px",
          background: "#fafafa",
        }}
      >
        <strong>Fields used</strong>
        {getChartContextEntries(chart.id, targetVariable, compareVariable).map(([role, field]) => (
          <p key={`${chart.id}-${role}`} style={{ marginTop: "0.35rem" }}>
            <strong>{role.replace(/_/g, " ")}:</strong> {field}
          </p>
        ))}
      </div>
    ) : null}

    <div
      style={{
        marginTop: "0.75rem",
        padding: "0.75rem",
        border: "1px solid #ddd",
        borderRadius: "8px",
        background: "#fafafa",
      }}
    >
      <strong>How to read this chart</strong>
      <p style={{ marginTop: "0.5rem", marginBottom: "0.35rem" }}>
        <strong>What this output shows:</strong> {getChartExplainability(chart.id).what}
      </p>
      <p style={{ marginTop: 0, marginBottom: "0.35rem" }}>
        <strong>Time usage:</strong> {getChartExplainability(chart.id).time}
      </p>
      <p style={{ marginTop: 0, marginBottom: "0.35rem" }}>
        <strong>Comparison:</strong> {getChartExplainability(chart.id).comparison}
      </p>
      <p style={{ marginTop: 0 }}>
        <strong>Where to find it:</strong> {getChartExplainability(chart.id).where}
      </p>
    </div>
  </div>
) : null}
        </div>
      ))}

      {error ? (
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            border: "1px solid #d88",
            borderRadius: "10px",
          }}
        >
          <strong>Error</strong>
          <p style={{ marginTop: "0.5rem" }}>{error}</p>
        </div>
      ) : null}
    </div>
  );
}