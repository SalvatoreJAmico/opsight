import React from "react";
import { useState } from "react";
import { startSqlServer, triggerPipeline } from "../api/client";
import { resolveBaseUrl } from "../config/env";
import { DATASETS } from "../config/datasets";
const isDev = import.meta.env.DEV;
const SQL_START_MAX_WAIT_MS = 240000;
const SQL_START_POLL_MS = 3000;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

function getSourceMetadata(activeDatasetConfig, result) {
  const sourceName = result?.dataset_source_name || activeDatasetConfig?.sourceName || "Unknown source";
  const sourceUrl = result?.dataset_source_url || activeDatasetConfig?.sourceUrl || null;
  const sourceLocation = result?.dataset_source_location || activeDatasetConfig?.location || null;

  return {
    sourceName,
    sourceUrl,
    sourceLocation,
  };
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
  const [sqlStartupProgress, setSqlStartupProgress] = useState(0);
  const activeDatasetConfig = DATASETS.find((d) => d.id === activeDataset) || null;
  const isSalesSqlDataset = activeDataset === "sales_sql";
  const datasetSummaryLabel = activeDatasetConfig?.label || result?.dataset_id || "Unknown dataset";
  const sourceMetadata = getSourceMetadata(activeDatasetConfig, result);
  const isRunDisabled = loading || !activeDataset || (isSalesSqlDataset && sqlReadiness !== "ready");
  const isSqlStartInFlight = sqlReadiness === "starting";

  function isSqlReadyResponse(response) {
    return response?.data?.ready === true || response?.data?.status === "ready";
  }

  function isSqlTransientStartupResponse(response) {
    if (!response?.ok || isSqlReadyResponse(response)) {
      return false;
    }

    const status = response?.data?.status;
    const message = (response?.data?.message || "").toLowerCase();

    return (
      status === "starting" ||
      message.includes("still starting") ||
      message.includes("startup was triggered") ||
      message.includes("still unreachable")
    );
  }

  async function handleStartSqlServer() {
    if (isSqlStartInFlight) {
      return;
    }

    setSqlReadiness("starting");
    setSqlStartupError("");
    setSqlStartupMessage("Starting SQL Server. This can take up to a few minutes.");
    setSqlStartupProgress(3);

    try {
      const requestBaseUrl = resolveBaseUrl(targetEnvironment);
      const startedAt = Date.now();

      while (Date.now() - startedAt < SQL_START_MAX_WAIT_MS) {
        const elapsed = Date.now() - startedAt;
        const progress = Math.min(95, Math.max(3, Math.round((elapsed / SQL_START_MAX_WAIT_MS) * 95)));
        setSqlStartupProgress(progress);

        const response = await startSqlServer({
          baseUrl: requestBaseUrl,
          target: targetEnvironment,
        });

        if (!response.ok) {
          setSqlReadiness("failed");
          setSqlStartupProgress(0);
          setSqlStartupError(formatSqlUserMessage(response.error, targetEnvironment === "cloud"));
          return;
        }

        if (isSqlReadyResponse(response)) {
          setSqlReadiness("ready");
          setSqlStartupProgress(100);
          setSqlStartupMessage(response.data?.message || "SQL Server is ready");
          return;
        }

        if (!isSqlTransientStartupResponse(response)) {
          setSqlReadiness("failed");
          setSqlStartupProgress(0);
          setSqlStartupError(formatSqlUserMessage(response.data?.message, targetEnvironment === "cloud"));
          return;
        }

        setSqlStartupMessage(response.data?.message || "SQL Server is still starting...");
        await sleep(SQL_START_POLL_MS);
      }

      setSqlReadiness("failed");
      setSqlStartupProgress(0);
      setSqlStartupError("SQL Server is taking longer than expected. Please try again.");
    } catch (error) {
      setSqlReadiness("failed");
      setSqlStartupProgress(0);
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
                disabled={loading || isSqlStartInFlight}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: targetEnvironment === "local" ? "1px solid #a78bfa" : "1px solid #4b5563",
                  fontWeight: targetEnvironment === "local" ? 700 : 400,
                  background: targetEnvironment === "local" ? "#e9d5ff" : "#1f2937",
                  color: targetEnvironment === "local" ? "#111827" : "#f3f4f6",
                  cursor: loading || isSqlStartInFlight ? "not-allowed" : "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Local
              </button>
              <button
                type="button"
                onClick={() => setTargetEnvironment("cloud")}
                disabled={loading || isSqlStartInFlight}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: targetEnvironment === "cloud" ? "1px solid #a78bfa" : "1px solid #4b5563",
                  fontWeight: targetEnvironment === "cloud" ? 700 : 400,
                  background: targetEnvironment === "cloud" ? "#e9d5ff" : "#1f2937",
                  color: targetEnvironment === "cloud" ? "#111827" : "#f3f4f6",
                  cursor: loading || isSqlStartInFlight ? "not-allowed" : "pointer",
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
          disabled={isSqlStartInFlight}
          onChange={(e) => {
            const nextDataset = e.target.value || null;
            const hasChanged = nextDataset !== activeDataset;

            if (!hasChanged) {
              return;
            }

            setActiveDataset(nextDataset);
            setError("");
            setSuccessMessage("");
            setResult(null);
            setSqlReadiness("idle");
            setSqlStartupMessage("");
            setSqlStartupError("");
            setSqlStartupProgress(0);

            onDatasetChange?.(nextDataset);
          }}
        >
          <option value="">Select dataset</option>
          {DATASETS.map((ds) => (
            <option key={ds.id} value={ds.id}>
              {ds.label}
            </option>
          ))}
        </select>

        {activeDataset ? (
          <div
            style={{
              marginBottom: "1rem",
              padding: "0.75rem",
              border: "1px solid #374151",
              borderRadius: "8px",
              background: "#0b1220",
              textAlign: "left",
            }}
          >
            <p style={{ margin: 0, color: "#f9fafb" }}>
              <strong>Loaded:</strong> {activeDatasetConfig?.label}
            </p>
            <p style={{ marginTop: "0.35rem", marginBottom: 0, color: "#d1d5db" }}>
              <strong>Source Name:</strong> {sourceMetadata.sourceName}
            </p>
            {sourceMetadata.sourceLocation ? (
              <p style={{ marginTop: "0.35rem", marginBottom: 0, color: "#d1d5db" }}>
                <strong>Source Location:</strong> {sourceMetadata.sourceLocation}
              </p>
            ) : null}
            {sourceMetadata.sourceUrl ? (
              <p style={{ marginTop: "0.35rem", marginBottom: 0, color: "#d1d5db" }}>
                <strong>Source URL:</strong>{" "}
                <span>{sourceMetadata.sourceUrl}</span>
              </p>
            ) : null}
          </div>
        ) : null}

        {isSalesSqlDataset ? (
          <div style={{ marginBottom: "1rem" }}>
            <button
              type="button"
              onClick={handleStartSqlServer}
              disabled={isSqlStartInFlight}
              style={{
                display: "block",
                margin: "0 auto",
                padding: "0.75rem 1.5rem",
                borderRadius: "8px",
                border: "1px solid #ccc",
                cursor: isSqlStartInFlight ? "not-allowed" : "pointer",
                fontWeight: 600,
                fontSize: "1rem",
              }}
            >
              {isSqlStartInFlight ? "Starting SQL Server..." : "Start SQL Server"}
            </button>
            {isSqlStartInFlight ? (
              <div style={{ marginTop: "0.6rem" }}>
                <div
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={sqlStartupProgress}
                  style={{
                    width: "100%",
                    maxWidth: "420px",
                    height: "10px",
                    margin: "0 auto",
                    borderRadius: "999px",
                    background: "#374151",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${sqlStartupProgress}%`,
                      height: "100%",
                      background: "#60a5fa",
                      transition: "width 300ms ease",
                    }}
                  />
                </div>
                <p style={{ marginTop: "0.4rem", color: "#93c5fd", fontSize: "0.85rem" }}>
                  SQL startup in progress: {sqlStartupProgress}%
                </p>
              </div>
            ) : null}
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
              {result.dataset_source_name ? (
                <p style={{ marginTop: 0, marginBottom: "0.25rem", color: "#d1d5db" }}>
                  Source Name: {result.dataset_source_name}
                </p>
              ) : null}
              {result.dataset_source_location ? (
                <p style={{ marginTop: 0, marginBottom: "0.25rem", color: "#d1d5db" }}>
                  Source Location: {result.dataset_source_location}
                </p>
              ) : null}
              {result.dataset_source_url ? (
                <p style={{ marginTop: 0, marginBottom: "0.25rem", color: "#d1d5db" }}>
                  Source URL:{" "}
                  <span>{result.dataset_source_url}</span>
                </p>
              ) : null}
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
