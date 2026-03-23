import React from "react";
import { useState } from "react";
import { triggerPipeline } from "../api/client";
import { resolveBaseUrl } from "../config/env";

const isDev = import.meta.env.DEV;

export default function UploadTab({ onPipelineComplete }) {
  const [targetEnvironment, setTargetEnvironment] = useState(isDev ? "local" : "cloud");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [result, setResult] = useState(null);

  async function handleTrigger() {
    setLoading(true);
    setError("");
    setSuccessMessage("");
    setResult(null);

    const requestBaseUrl = resolveBaseUrl(targetEnvironment);

    const response = await triggerPipeline({}, {
      baseUrl: requestBaseUrl,
    });

    setLoading(false);
    if (!response.ok) {
      if (response.status === 0 && targetEnvironment === "local") {
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
      <p>Run the pipeline using the default dataset.</p>

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
              border: "1px solid #ccc",
              fontWeight: targetEnvironment === "local" ? 700 : 400,
              background: targetEnvironment === "local" ? "#e8f0fe" : "transparent",
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
              border: "1px solid #ccc",
              fontWeight: targetEnvironment === "cloud" ? 700 : 400,
              background: targetEnvironment === "cloud" ? "#e8f0fe" : "transparent",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Cloud
          </button>
        </div>

        <p style={{ marginBottom: "1rem", opacity: 0.85 }}>
          Target: <strong>{targetEnvironment === "local" ? "Local API (this computer)" : "Deployed API (cloud)"}</strong>
        </p>

        <button
          type="button"
          onClick={handleTrigger}
          disabled={loading}
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
          <strong>Response</strong>
          <pre style={{ marginTop: "0.75rem", whiteSpace: "pre-wrap" }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
