import React from "react";
import { useState } from "react";
import { triggerPipeline } from "../api/client";
import { resolveBaseUrl } from "../config/env";
import { DATASETS } from "../config/datasets";
const isDev = import.meta.env.DEV;

function getDatasetSourceLabel(sourceType) {
  if (sourceType === "blob") {
    return "Blob Storage";
  }
  if (sourceType === "sql") {
    return "SQL";
  }
  return sourceType || "Unknown";
}

function getFilename(path) {
  if (!path) {
    return "";
  }
  const segments = path.split("/");
  return segments[segments.length - 1] || path;
}

export default function DatasetTab({ onPipelineComplete }) {
  const [targetEnvironment, setTargetEnvironment] = useState(isDev ? "local" : "cloud");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [result, setResult] = useState(null);
  const [activeDataset, setActiveDataset] = useState(null);
  const activeDatasetConfig = DATASETS.find((d) => d.id === activeDataset) || null;
  const datasetSummaryLabel = activeDatasetConfig?.label || result?.dataset_id || "Unknown dataset";


  async function handleTrigger() {
    if (!activeDataset) {
      setError("Select a dataset before running.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccessMessage("");
    setResult(null);

    const requestBaseUrl = resolveBaseUrl(targetEnvironment);

    const response = await triggerPipeline({
      target: targetEnvironment,
      dataset_id: activeDataset,
    },
    
    {
      baseUrl: requestBaseUrl,
    });

    setLoading(false);
    if (!response.ok) {
      if (response.status === 0 && targetEnvironment === "local") {
        setError("Local API is unavailable. Start the API on http://127.0.0.1:8000 and try again.");
      } else if (response.status === 501 && activeDatasetConfig?.sourceType === "sql") {
        setError("SQL dataset execution is not wired yet.");
      } else {
        setError(response.error || "Pipeline trigger failed.");
      }
      return;
    }

    const destinationLabel =
      targetEnvironment === "local" ? "local API" : "deployed API";
    const datasetLabelSuffix = activeDatasetConfig ? ` for ${activeDatasetConfig.label}` : "";
    setSuccessMessage(`Dataset run triggered successfully on ${destinationLabel}${datasetLabelSuffix}.`);
    setResult(response.data);
    if (onPipelineComplete) {
      onPipelineComplete(response.data);
    }
  }

  return (
    <div>
      <h2>Dataset</h2>
      <p>Run analysis on the selected dataset.</p>

      <div style={{ marginTop: "1.5rem", maxWidth: "560px" }}>
        <div style={{ marginBottom: "1rem" }}>
          <span style={{ fontWeight: 600, marginRight: "0.75rem" }}>API Target:</span>
          <button
            type="button"
            onClick={() => setTargetEnvironment("local")}
            disabled={loading}
            style={{
              marginRight: "0.5rem",
              padding: "0.4rem 0.9rem",
              borderRadius: "6px",
              border: targetEnvironment === "local" ? "1px solid #a78bfa" : "1px solid #4b5563",
              fontWeight: targetEnvironment === "local" ? 700 : 400,
              background: targetEnvironment === "local" ? "#e9d5ff" : "#1f2937",
              color: targetEnvironment === "local" ? "#111827" : "#f3f4f6",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Local
          </button>
          <button
            type="button"
            onClick={() => setTargetEnvironment("cloud")}
            disabled={loading}
            style={{
              padding: "0.4rem 0.9rem",
              borderRadius: "6px",
              border: targetEnvironment === "cloud" ? "1px solid #a78bfa" : "1px solid #4b5563",
              fontWeight: targetEnvironment === "cloud" ? 700 : 400,
              background: targetEnvironment === "cloud" ? "#e9d5ff" : "#1f2937",
              color: targetEnvironment === "cloud" ? "#111827" : "#f3f4f6",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Cloud
          </button>
        </div>

        <p style={{ marginBottom: "1rem", color: "#d1d5db" }}>
          Target: <strong>{targetEnvironment === "local" ? "Local API (this computer)" : "Deployed API (cloud)"}</strong>
        </p>

        <label htmlFor="dataset-select" style={{ display: "block", marginBottom: "0.4rem", fontWeight: 600 }}>
          Dataset
        </label>
        <select
          id="dataset-select"
          style={{
            width: "100%",
            marginBottom: "0.75rem",
            padding: "0.55rem 0.7rem",
            borderRadius: "8px",
            border: "1px solid #4b5563",
            background: "#111827",
            color: "#f9fafb",
          }}
          value={activeDataset || ""}
          onChange={(e) => {
            setActiveDataset(e.target.value);
            setError("");
            setSuccessMessage("");
            setResult(null);
          }}
        >
          <option value="">Select dataset</option>
          {DATASETS.map((ds) => (
            <option key={ds.id} value={ds.id}>
              {ds.label}
            </option>
          ))}
        </select>

        {activeDataset && (
          <p style={{ marginBottom: "1rem" }}>Loaded: {activeDatasetConfig?.label}</p>
        )}

        <button
          type="button"
          onClick={handleTrigger}
          disabled={loading || !activeDataset}
          style={{
            padding: "0.75rem 1.5rem",
            borderRadius: "8px",
            border: "1px solid #ccc",
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: "1rem",
          }}
        >
          {loading ? "Running..." : "Run"}
        </button>
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

      {successMessage ? (
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            border: "1px solid #8bbf8b",
            borderRadius: "10px",
          }}
        >
          <strong>Success</strong>
          <p style={{ marginTop: "0.5rem" }}>{successMessage}</p>
        </div>
      ) : null}

      {result ? (
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            border: "1px solid #ccc",
            borderRadius: "10px",
          }}
        >
          {result.dataset_id ? (
            <div
              style={{
                marginBottom: "0.9rem",
                padding: "0.75rem",
                border: "1px solid #ddd",
                borderRadius: "8px",
                background: "#111827",
              }}
            >
              <strong>Dataset Execution</strong>
              <p style={{ marginTop: "0.45rem", marginBottom: "0.25rem", color: "#f3f4f6" }}>
                Dataset: {datasetSummaryLabel}
              </p>
              <p style={{ marginTop: 0, marginBottom: "0.25rem", color: "#d1d5db" }}>
                Source: {getDatasetSourceLabel(result.dataset_source_type)}
              </p>
              {result.dataset_source_type === "blob" && result.dataset_path ? (
                <p style={{ marginTop: 0, color: "#d1d5db" }}>File: {getFilename(result.dataset_path)}</p>
              ) : null}
            </div>
          ) : null}
          <strong>Response</strong>
          <pre style={{ marginTop: "0.75rem", whiteSpace: "pre-wrap" }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
