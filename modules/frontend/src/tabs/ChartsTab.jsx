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

  const loadChartById = async (chartId) => {
    const baseUrl = resolveBaseUrl(target);
    switch (chartId) {
      case "histogram":
        return getHistogram({ baseUrl });
      case "bar-category":
        return getBarCategory({ baseUrl });
      case "boxplot":
        return getBoxplot({ baseUrl });
      case "scatter":
        return getScatter({ baseUrl });
      case "grouped-comparison":
        return getGroupedComparison({ baseUrl });
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
      missing_by_column: overview.missing_by_column,
      numeric_summary: overview.numeric_summary,
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

const getChartContextEntries = (overview, chartId) => {
  const context = overview?.chart_context?.[chartId] || {};
  return Object.entries(context).filter(([, value]) => Boolean(value));
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
          <p>Source: {overview.source}</p>
          {overview.source_metadata?.source_location ? (
            <p>Source Location: {overview.source_metadata.source_location}</p>
          ) : null}
          {overview.source_metadata?.source_url ? (
            <p>
              Source URL:{" "}
              <a href={overview.source_metadata.source_url} target="_blank" rel="noreferrer">
                {overview.source_metadata.source_url}
              </a>
            </p>
          ) : null}
          <p>Rows: {overview.rows}</p>
          {overview.variables != null && <p>Variables: {overview.variables}</p>}
          {overview.fields && <p>Fields: {overview.fields.join(", ")}</p>}

          {overview.shape ? (
            <p>
              Shape: {overview.shape.rows} x {overview.shape.columns}
            </p>
          ) : null}

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

          <h3>Summary Statistics</h3>
          {overview.min != null && <p>Min: {overview.min}</p>}
          {overview.max != null && <p>Max: {overview.max}</p>}
          {overview.mean != null && <p>Mean: {overview.mean}</p>}
          {overview.count != null && <p>Count: {overview.count}</p>}

          <h3>Missing Values By Column</h3>
          {overview.missing_by_column ? (
            <div>
              {Object.entries(overview.missing_by_column).map(([field, missing]) => (
                <p key={`missing-${field}`}>
                  {field}: {missing}
                </p>
              ))}
            </div>
          ) : (
            <p>No missing-value summary available.</p>
          )}

          <h3>Numeric Field Summary</h3>
          {overview.numeric_summary?.length ? (
            <div>
              {overview.numeric_summary.map((item) => (
                <div
                  key={`numeric-${item.field}`}
                  style={{ marginBottom: "0.65rem", paddingBottom: "0.65rem", borderBottom: "1px solid #eee" }}
                >
                  <p><strong>{item.field}</strong></p>
                  <p>Count: {item.count} | Missing: {item.missing}</p>
                  <p>
                    Min: {item.min ?? "N/A"} | Max: {item.max ?? "N/A"} | Mean: {item.mean ?? "N/A"}
                  </p>
                  <p>
                    Median: {item.median ?? "N/A"} | Std Dev: {item.std ?? "N/A"}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p>No numeric summary available.</p>
          )}

          <h3>Categorical Frequency Summary</h3>
          {overview.categorical_summary?.length ? (
            <div>
              {overview.categorical_summary.map((item) => (
                <div
                  key={`categorical-${item.field}`}
                  style={{ marginBottom: "0.65rem", paddingBottom: "0.65rem", borderBottom: "1px solid #eee" }}
                >
                  <p>
                    <strong>{item.field}</strong> (Unique: {item.unique}, Missing: {item.missing})
                  </p>
                  {item.top_values?.length ? (
                    item.top_values.map((entry, index) => (
                      <p key={`cat-${item.field}-${entry.value}-${index}`}>
                        {entry.value}: {entry.count}
                      </p>
                    ))
                  ) : (
                    <p>No frequency data available.</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p>No categorical summary available.</p>
          )}
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

    {getChartContextEntries(overview, chart.id).length > 0 ? (
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
        {getChartContextEntries(overview, chart.id).map(([role, field]) => (
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