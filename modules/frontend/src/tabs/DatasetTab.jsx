import React from "react";
import { useState } from "react";
import { startSqlServer, triggerPipeline } from "../api/client";
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

function formatSqlUserMessage(message, isCloudTarget) {
  const text = (message || "").toLowerCase();

  if (isCloudTarget) {
    if (text.includes("cannot start a database server")) {
      return "Connection check failed in cloud mode. The app cannot start a database server in cloud mode, so please contact support if this continues.";
    }
    if (text.includes("could not reach") || text.includes("timeout")) {
      return "We could not reach the database from the cloud app right now. Please try again, and contact support if it keeps failing.";
    }
  }

  if (text.includes("sign-in failed") || text.includes("login")) {
    return "Database access failed. Please contact support to verify database credentials and permissions.";
  }

  return message || "Database connection failed. Please try again.";
}

export default function DatasetTab({ onPipelineComplete, onAction, onDatasetChange }) {
  const [targetEnvironment, setTargetEnvironment] = useState(isDev ? "local" : "cloud");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [result, setResult] = useState(null);
  const [activeDataset, setActiveDataset] = useState(null);
  const [sqlReadiness, setSqlReadiness] = useState("idle");
  const [sqlStartupMessage, setSqlStartupMessage] = useState("");
  const [sqlStartupError, setSqlStartupError] = useState("");
  const activeDatasetConfig = DATASETS.find((d) => d.id === activeDataset) || null;
  const isSalesSqlDataset = activeDataset === "sales_sql";
  const datasetSummaryLabel = activeDatasetConfig?.label || result?.dataset_id || "Unknown dataset";
  const isRunDisabled = loading || !activeDataset || (isSalesSqlDataset && sqlReadiness !== "ready");

  async function handleStartSqlServer() {
    setSqlReadiness("starting");
    setSqlStartupError("");
    setSqlStartupMessage("");

    try {
      const requestBaseUrl = resolveBaseUrl(targetEnvironment);
      const response = await startSqlServer({
        baseUrl: requestBaseUrl,
        target: targetEnvironment,
      });
      const isSqlReady = response.data?.ready === true || response.data?.status === "ready";

      if (!response.ok) {
        setSqlReadiness("failed");
        setSqlStartupError(formatSqlUserMessage(response.error, targetEnvironment === "cloud"));
        return;
      }

      if (!isSqlReady) {
        setSqlReadiness("failed");
        setSqlStartupError(formatSqlUserMessage(response.data?.message, targetEnvironment === "cloud"));
        return;
      }

      setSqlReadiness("ready");
      setSqlStartupMessage(response.data?.message || "SQL Server is ready");
    } catch (error) {
      setSqlReadiness("failed");
      setSqlStartupError(formatSqlUserMessage(error?.message, targetEnvironment === "cloud"));
    }
  }

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

    const response = await triggerPipeline(
      {
        target: targetEnvironment,
        dataset_id: activeDataset,
      },
      {
        baseUrl: requestBaseUrl,
      },
    );

    setLoading(false);
    if (!response.ok) {
      if (response.status === 0 && targetEnvironment === "local") {
        setError("Local API is unavailable. Start the API on http://127.0.0.1:8000 and try again.");
      } else if (isSalesSqlDataset) {
        setError(
          response.error ||
            "SQL dataset run failed. Ensure SQL Server is reachable, then click Start SQL Server before running.",
        );
      } else {
        setError(response.error || "Pipeline trigger failed.");
      }
      onAction?.();
      return;
    }

    const destinationLabel = targetEnvironment === "local" ? "local API" : "deployed API";
    const datasetLabelSuffix = activeDatasetConfig ? ` for ${activeDatasetConfig.label}` : "";
    setSuccessMessage(`Dataset run triggered successfully on ${destinationLabel}${datasetLabelSuffix}.`);
    setResult(response.data);
    if (onPipelineComplete) {
      onPipelineComplete(response.data);
    }
    onAction?.();
  }

  return (
    <div>
      <h2>Dataset</h2>
      <p>Run analysis on the selected dataset.</p>

      <div
        style={{
          marginTop: "1.5rem",
          maxWidth: "560px",
          marginLeft: "auto",
          marginRight: "auto",
          textAlign: "center",
        }}
      >
        {isDev && (
          <div style={{ marginBottom: "1rem", textAlign: "center" }}>
            <div style={{ fontWeight: 600, marginBottom: "0.5rem", fontSize: "0.9rem" }}>Dev — API Target:</div>
            <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem" }}>
              <button
                type="button"
                onClick={() => setTargetEnvironment("local")}
                disabled={loading}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: targetEnvironment === "local" ? "1px solid #a78bfa" : "1px solid #4b5563",
                  fontWeight: targetEnvironment === "local" ? 700 : 400,
                  background: targetEnvironment === "local" ? "#e9d5ff" : "#1f2937",
                  color: targetEnvironment === "local" ? "#111827" : "#f3f4f6",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontSize: "0.9rem",
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
                  fontSize: "0.9rem",
                }}
              >
                Cloud
              </button>
            </div>
          </div>
        )}

        <label htmlFor="dataset-select" style={{ display: "block", marginBottom: "0.4rem", fontWeight: 600 }}>
          Dataset
        </label>
        <select
          id="dataset-select"
          style={{
            width: "100%",
            margin: "0 auto 0.75rem auto",
            display: "block",
            padding: "0.55rem 0.7rem",
            borderRadius: "8px",
            border: "1px solid #4b5563",
            background: "#111827",
            color: "#f9fafb",
          }}
          value={activeDataset || ""}
          onChange={(e) => {
            const nextDataset = e.target.value || null;
            const hasChanged = nextDataset !== activeDataset;

            setActiveDataset(nextDataset);
            setError("");
            setSuccessMessage("");
            setResult(null);
            setSqlReadiness("idle");
            setSqlStartupMessage("");
            setSqlStartupError("");

            if (hasChanged) {
              onDatasetChange?.(nextDataset);
            }
          }}
        >
          <option value="">Select dataset</option>
          {DATASETS.map((ds) => (
            <option key={ds.id} value={ds.id}>
              {ds.label}
            </option>
          ))}
        </select>

        {activeDataset && <p style={{ marginBottom: "1rem" }}>Loaded: {activeDatasetConfig?.label}</p>}

        {isSalesSqlDataset ? (
          <div style={{ marginBottom: "1rem" }}>
            <button
              type="button"
              onClick={handleStartSqlServer}
              disabled={sqlReadiness === "starting"}
              style={{
                display: "block",
                margin: "0 auto",
                padding: "0.75rem 1.5rem",
                borderRadius: "8px",
                border: "1px solid #ccc",
                cursor: sqlReadiness === "starting" ? "not-allowed" : "pointer",
                fontWeight: 600,
                fontSize: "1rem",
              }}
            >
              {sqlReadiness === "starting" ? "Starting SQL Server..." : "Start SQL Server"}
            </button>
            {sqlStartupMessage ? <p style={{ marginTop: "0.6rem", color: "#86efac" }}>{sqlStartupMessage}</p> : null}
            {sqlStartupError ? <p style={{ marginTop: "0.6rem", color: "#fca5a5" }}>{sqlStartupError}</p> : null}
          </div>
        ) : null}

        <button
          type="button"
          onClick={handleTrigger}
          disabled={isRunDisabled}
          style={{
            display: "block",
            margin: "0 auto",
            padding: "0.75rem 1.5rem",
            borderRadius: "8px",
            border: "1px solid #ccc",
            cursor: isRunDisabled ? "not-allowed" : "pointer",
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
          {isDev ? (
            <>
              <strong>Response (Dev)</strong>
              <pre style={{ marginTop: "0.75rem", whiteSpace: "pre-wrap", fontSize: "0.85rem", maxHeight: "300px", overflowY: "auto" }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
