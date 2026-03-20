import { useState } from "react";
import {
  getHistogram,
  getBarCategory,
  getBoxplot,
  getScatter,
  getGroupedComparison,
  resolveApiAssetUrl,
} from "../api/client";
import { chartCatalog } from "../catalog/chartCatalog";

const SAMPLE_DATA = [
  { entity_id: "A", metric_value: 10, secondary_metric: 8, category: "X" },
  { entity_id: "B", metric_value: 20, secondary_metric: 18, category: "Y" },
  { entity_id: "C", metric_value: 15, secondary_metric: 12, category: "X" },
  { entity_id: "D", metric_value: 30, secondary_metric: 25, category: "Z" },
];

const LOCAL_PROXY_BASE_URL = "/api-local";

export default function ChartsTab() {
  const data = SAMPLE_DATA;
  const values = data.map((d) => d.metric_value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const mean = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);

  const [activeChart, setActiveChart] = useState("");
  const [chartImages, setChartImages] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadChartById = async (chartId) => {
    switch (chartId) {
      case "histogram":
        return getHistogram({ baseUrl: LOCAL_PROXY_BASE_URL });
      case "bar-category":
        return getBarCategory({ baseUrl: LOCAL_PROXY_BASE_URL });
      case "boxplot":
        return getBoxplot({ baseUrl: LOCAL_PROXY_BASE_URL });
      case "scatter":
        return getScatter({ baseUrl: LOCAL_PROXY_BASE_URL });
      case "grouped-comparison":
        return getGroupedComparison({ baseUrl: LOCAL_PROXY_BASE_URL });
      default:
        return { ok: false, error: "Unsupported chart selection." };
    }
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
      LOCAL_PROXY_BASE_URL
    );

    if (!resolvedImageUrl) {
      setActiveChart("");
      setError("Chart response did not include an image path.");
      return;
    }

    setChartImages((prev) => ({
      ...prev,
      [chartId]: resolvedImageUrl,
    }));
  };


const getObservationText = (chartId) => {
  switch (chartId) {
    case "histogram":
      return "The distribution of metric_value shows how values are spread across the dataset. Most values appear within a moderate range, with no extreme clustering or gaps.";

    case "bar-category":
      return "The bar chart shows how records are distributed across categories. Some categories may have higher counts, indicating concentration in specific groups.";

    case "boxplot":
      return "The box plot highlights the spread and potential outliers in metric_value. The median and quartiles indicate the central tendency and variability of the dataset.";

    case "scatter":
      return "The scatter plot shows the relationship between metric_value and secondary_metric. Patterns or clustering may indicate correlation between the two variables.";

    case "grouped-comparison":
      return "The grouped comparison chart shows average metric_value across categories. Differences between bars indicate how categories compare in terms of average performance.";

    default:
      return "No observations available for this chart.";
  }
};






  return (
    <div>
      <h2>Charts</h2>

      <h3>Dataset Overview</h3>
      <p>Source: Sample Dataset</p>
      <p>Rows: {data.length}</p>
      <p>Variables: {Object.keys(data[0]).length}</p>
      <p>Fields: {Object.keys(data[0]).join(", ")}</p>

      <h3>Summary Statistics</h3>
      <p>Min: {min}</p>
      <p>Max: {max}</p>
      <p>Mean: {mean}</p>
      <p>Count: {values.length}</p>

      <p style={{ marginBottom: "1rem", opacity: 0.85 }}>
        Each chart includes guidance on what it shows, when to use it, and whether it is recommended for the current dataset.
      </p>

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

    <div
      style={{
        marginTop: "0.75rem",
        padding: "0.75rem",
        border: "1px solid #ddd",
        borderRadius: "8px",
        background: "#fafafa",
      }}
    >
      <strong>Observations</strong>
      <p style={{ marginTop: "0.5rem" }}>
        {getObservationText(chart.id)}
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