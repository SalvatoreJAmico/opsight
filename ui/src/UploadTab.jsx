import { useState } from "react";
import { triggerPipeline } from "./api/client";

const SAMPLE_SOURCE_PATH = "csv/opsight_sample_sales.csv";

export default function UploadTab() {
  const [accessCode, setAccessCode] = useState("demo-code");
  const [sourcePath, setSourcePath] = useState(SAMPLE_SOURCE_PATH);
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

    const response = await triggerPipeline({
      access_code: trimmedAccessCode,
      source_path: trimmedSourcePath,
    });

    setLoading(false);

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        setError("Invalid or missing access code.");
      } else if (response.status === 400) {
        setError(response.error || "Invalid request.");
      } else {
        setError(response.error || "Pipeline trigger failed.");
      }
      return;
    }

    setSuccessMessage("Pipeline triggered successfully.");
    setResult(response.data);
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
            placeholder="csv/opsight_sample_sales.csv"
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
            }}
          />
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
            onClick={() => setSourcePath(SAMPLE_SOURCE_PATH)}
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
            Use Sample Dataset
          </button>
        </div>
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
