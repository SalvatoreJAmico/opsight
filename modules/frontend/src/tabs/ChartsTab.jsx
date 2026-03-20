import { useState } from "react";
import { getHistogram, resolveApiAssetUrl } from "../api/client";
import { chartCatalog } from "../catalog/chartCatalog";


const SAMPLE_DATA = [
  { entity_id: "A", metric_value: 10, category: "X" },
  { entity_id: "B", metric_value: 20, category: "Y" },
  { entity_id: "C", metric_value: 15, category: "X" },
  { entity_id: "D", metric_value: 30, category: "Z" },
];

const LOCAL_PROXY_BASE_URL = "/api-local";

export default function ChartsTab() {
  const data = SAMPLE_DATA;
  const values = data.map((d) => d.metric_value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const mean = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);

  const [showHistogram, setShowHistogram] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadHistogram = async () => {
    setLoading(true);
    setError("");

    const response = await getHistogram({ baseUrl: LOCAL_PROXY_BASE_URL });

    setLoading(false);

    if (!response.ok) {
      setShowHistogram(false);
      setImageUrl("");
      setError(response.error || "Histogram request failed.");
      return;
    }

    const resolvedImageUrl = resolveApiAssetUrl(response.data?.image, LOCAL_PROXY_BASE_URL);

    if (!resolvedImageUrl) {
      setShowHistogram(false);
      setImageUrl("");
      setError("Histogram response did not include an image path.");
      return;
    }

    setImageUrl(resolvedImageUrl);
    setShowHistogram(true);
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

      <h3>Available Charts</h3>
        {chartCatalog.map((chart) => (
        <div key={chart.id} style={{ marginBottom: "1rem" }}>
            <strong>{chart.title}</strong>
            <p>{chart.purpose}</p>
            <p><em>{chart.whenToUse}</em></p>
            <p>
            Recommended for current dataset:{" "}
            <strong>{chart.recommended ? "Yes" : "No"}</strong>
            </p>
            <p style={{ opacity: 0.8 }}>{chart.recommendationReason}</p>
        </div>
        ))}

        <p style={{ marginBottom: "1rem", opacity: 0.85 }}>
        Each chart includes guidance on what it shows, when to use it, and whether it is recommended for the current dataset.
        </p>

      <h3>Charts</h3>
      <button
        type="button"
        onClick={loadHistogram}
        disabled={loading}
        style={{
          padding: "0.75rem 1rem",
          borderRadius: "8px",
          border: "1px solid #ccc",
          cursor: loading ? "not-allowed" : "pointer",
          fontWeight: 600,
        }}
      >
        {loading ? "Loading..." : "Show Histogram"}
      </button>

      <h3 style={{ marginTop: "1.25rem" }}>Chart Catalog</h3>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "0.75rem",
          marginTop: "0.75rem",
        }}
      >
        {chartCatalog.map((chart) => (
          <div
            key={chart.id}
            style={{
              border: "1px solid #ddd",
              borderRadius: "10px",
              padding: "0.75rem",
              background: chart.recommended ? "#f6fbf6" : "#fafafa",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem" }}>
              <strong>{chart.title}</strong>
              <span
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  color: chart.recommended ? "#1f6f2e" : "#666",
                }}
              >
                {chart.recommended ? "Recommended" : "Optional"}
              </span>
            </div>
            <p style={{ marginTop: "0.5rem" }}>{chart.purpose}</p>
            <p style={{ marginTop: "0.5rem", opacity: 0.9 }}>
              <strong>When to use:</strong> {chart.whenToUse}
            </p>
            <p style={{ marginTop: "0.5rem", opacity: 0.9 }}>
              <strong>Why:</strong> {chart.recommendationReason}
            </p>
            <p style={{ marginTop: "0.5rem", fontFamily: "monospace", fontSize: "0.85rem" }}>
              Endpoint: {chart.endpoint}
            </p>
          </div>
        ))}
      </div>

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

      {showHistogram && imageUrl && (
        <div style={{ marginTop: "1rem" }}>
          <img
            src={imageUrl}
            alt="Histogram of metric values"
            style={{ maxWidth: "100%", border: "1px solid #ccc", borderRadius: "8px" }}
          />
        </div>
      )}
    </div>
  );
}