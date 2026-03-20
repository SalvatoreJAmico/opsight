import React from "react";
import { useState } from "react";
import { triggerPipeline } from "../api/client";

const isDev = import.meta.env.DEV;
const BLOB_SAMPLE_SOURCE_PATH = "opsight-raw/csv/opsight_sample_sales.csv";
const LOCAL_SAMPLE_SOURCE_PATH = "data/opsight_sample_sales.csv";
const CLOUD_PROXY_BASE_URL = "/api-cloud";
const LOCAL_PROXY_BASE_URL = "/api-local";

export default function UploadTab({ onPipelineComplete }) {
  const [accessCode, setAccessCode] = useState("demo-code");
  const [sourcePath, setSourcePath] = useState(BLOB_SAMPLE_SOURCE_PATH);
  const [targetEnvironment, setTargetEnvironment] = useState("cloud");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [result, setResult] = useState(null);

  async function handleTrigger() {
    const trimmedAccessCode = accessCode.trim();
    const trimmedSourcePath = sourcePath.trim();

    if (!trimmedAccessCode) {
      setError("Access code is required.");
      setSuccessMessage("");
      setResult(null);
      return;
    }

    if (!trimmedSourcePath) {
      setError("Source path is required.");
      setSuccessMessage("");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");
    setSuccessMessage("");
    setResult(null);

    const requestBaseUrl =
      targetEnvironment === "local"
        ? LOCAL_PROXY_BASE_URL
        : CLOUD_PROXY_BASE_URL;

    const response = await triggerPipeline({
      access_code: trimmedAccessCode,
      source_path: trimmedSourcePath,
    }, {
      baseUrl: requestBaseUrl,
    });

    setLoading(false); 
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        setError("Invalid or missing access code.");
      } else if (response.status === 400) {
        setError(response.error || "Invalid request.");
      } else if (response.status === 0 && targetEnvironment === "local") {
        setError("Local API is unavailable. Start the API on http://127.0.0.1:8000 and try again.");
      } else {
        setError(response.error || "Pipeline trigger failed.");
      }
      return;
    }

    const destinationLabel =
      targetEnvironment === "local" ? "local API" : "deployed API";
    setSuccessMessage(`Pipeline triggered successfully on ${destinationLabel}.`);
    setResult(response.data);
    if (onPipelineComplete) {
      onPipelineComplete(response.data);
    }
  }

  return (
    <div>
      <h2>Upload</h2>
      <p>Trigger the protected pipeline using an access code and source path.</p>

      <div style={{ display: "grid", gap: "1rem", maxWidth: "560px", marginTop: "1.25rem" }}>
        <div>
          <label htmlFor="access-code" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 600 }}>
            Access Code
          </label>
          <input
            id="access-code"
            type="password"
            value={accessCode}
            onChange={(event) => setAccessCode(event.target.value)}
            placeholder="Enter upload access code"
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
            }}
          />
        </div>

        <div>
          <label htmlFor="source-path" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 600 }}>
            Source Path
          </label>
          <input
            id="source-path"
            type="text"
            value={sourcePath}
            onChange={(event) => setSourcePath(event.target.value)}
            placeholder="opsight-raw/csv/opsight_sample_sales.csv"
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
            }}
          />
          <p style={{ marginTop: "0.5rem", opacity: 0.85 }}>
            Use <strong>container/path</strong> format for Blob paths.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={handleTrigger}
            disabled={loading}
            style={{
              width: "fit-content",
              padding: "0.75rem 1rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading ? "Running..." : "Run Pipeline"}
          </button>

          <button
            type="button"
            onClick={() => {
              setSourcePath(BLOB_SAMPLE_SOURCE_PATH);
              setTargetEnvironment("cloud");
            }}
            disabled={loading}
            style={{
              width: "fit-content",
              padding: "0.75rem 1rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            Use Blob Sample
          </button>

          {isDev && (
            <button
              type="button"
              onClick={() => {
                setSourcePath(LOCAL_SAMPLE_SOURCE_PATH);
                setTargetEnvironment("local");
              }}
              disabled={loading}
              style={{
                width: "fit-content",
                padding: "0.75rem 1rem",
                borderRadius: "8px",
                border: "1px solid #ccc",
                cursor: loading ? "not-allowed" : "pointer",
                fontWeight: 600,
              }}
            >
              Use Local Sample
            </button>
          )}
        </div>

        <p style={{ marginTop: "0.25rem", opacity: 0.85 }}>
          Target: <strong>{targetEnvironment === "local" ? "Local API (this computer)" : "Deployed API (cloud)"}</strong>
        </p>
      </div>

      {loading ? <p style={{ marginTop: "1rem" }}>Submitting pipeline request...</p> : null}

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
          <strong>Response</strong>
          <pre style={{ marginTop: "0.75rem", whiteSpace: "pre-wrap" }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
