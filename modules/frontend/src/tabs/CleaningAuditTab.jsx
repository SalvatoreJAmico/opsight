import React, { useEffect, useMemo, useState } from "react";
import { getCleaningAudit } from "../api/client";
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

function toRows(beforeValues = {}, afterValues = {}) {
  const fields = Array.from(new Set([...Object.keys(beforeValues), ...Object.keys(afterValues)])).sort();
  return fields.map((field) => ({
    field,
    before: beforeValues[field] ?? 0,
    after: afterValues[field] ?? 0,
  }));
}

export default function CleaningAuditTab({ activeDatasetId = null }) {
  const isDev = import.meta.env.DEV;
  const [target, setTarget] = useState(isDev ? "local" : "cloud");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [audit, setAudit] = useState(null);

  useEffect(() => {
    if (!activeDatasetId) {
      setAudit(null);
      setError("");
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError("");

    const baseUrl = resolveBaseUrl(target);
    getCleaningAudit({ baseUrl }).then((result) => {
      if (cancelled) return;
      setLoading(false);
      if (result.ok) {
        setAudit(result.data);
      } else {
        setError(result.error || "Failed to load cleaning audit.");
        setAudit(null);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [activeDatasetId, target]);

  const missingRows = useMemo(() => {
    return toRows(audit?.missing_by_column?.before || {}, audit?.missing_by_column?.after || {});
  }, [audit]);

  const handleExport = () => {
    if (!audit) {
      return;
    }

    const datasetName = audit?.source?.dataset_id || activeDatasetId || "dataset";
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `${datasetName}-cleaning-audit-${timestamp}.json`;
    downloadJson(filename, audit);
  };

  return (
    <div>
      <h2>Cleaning Audit</h2>
      {!activeDatasetId ? (
        <p>No dataset loaded. Run a dataset to view the cleaning audit.</p>
      ) : loading ? (
        <p>Loading cleaning audit...</p>
      ) : error ? (
        <p style={{ color: "#c00" }}>{error}</p>
      ) : audit ? (
        <>
          <div style={{ marginBottom: "1rem" }}>
            <button
              type="button"
              onClick={handleExport}
              style={{
                padding: "0.45rem 0.8rem",
                borderRadius: "6px",
                border: "1px solid #ccc",
                cursor: "pointer",
                fontSize: "0.85rem",
                fontWeight: 600,
              }}
            >
              Export Audit (JSON)
            </button>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
              marginBottom: "1.25rem",
            }}
          >
            <div style={{ border: "1px solid #ccc", borderRadius: "10px", padding: "1rem" }}>
              <strong>Rows Before</strong>
              <p>{audit.row_counts?.before ?? 0}</p>
            </div>
            <div style={{ border: "1px solid #ccc", borderRadius: "10px", padding: "1rem" }}>
              <strong>Rows After</strong>
              <p>{audit.row_counts?.after ?? 0}</p>
            </div>
            <div style={{ border: "1px solid #ccc", borderRadius: "10px", padding: "1rem" }}>
              <strong>Duplicates Before</strong>
              <p>{audit.duplicates?.before ?? 0}</p>
            </div>
            <div style={{ border: "1px solid #ccc", borderRadius: "10px", padding: "1rem" }}>
              <strong>Duplicates After</strong>
              <p>{audit.duplicates?.after ?? 0}</p>
            </div>
          </div>

          <h3>Missing Values By Column</h3>
          {missingRows.length ? (
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1.25rem" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Column</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Before</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>After</th>
                </tr>
              </thead>
              <tbody>
                {missingRows.map((row) => (
                  <tr key={row.field}>
                    <td style={{ borderBottom: "1px solid #f0f0f0", padding: "0.5rem" }}>{row.field}</td>
                    <td style={{ borderBottom: "1px solid #f0f0f0", padding: "0.5rem" }}>{row.before}</td>
                    <td style={{ borderBottom: "1px solid #f0f0f0", padding: "0.5rem" }}>{row.after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No missing value columns were found.</p>
          )}

          <h3>Invalid Rows Removed</h3>
          <p>Total Removed: {audit.invalid_rows_removed?.count ?? 0}</p>
          {Object.entries(audit.invalid_rows_removed?.reason_counts || {}).length ? (
            <ul>
              {Object.entries(audit.invalid_rows_removed.reason_counts).map(([reason, count]) => (
                <li key={reason}>
                  {reason}: {count}
                </li>
              ))}
            </ul>
          ) : (
            <p>No invalid rows were removed.</p>
          )}
        </>
      ) : null}

      {isDev && (
        <div style={{ marginTop: "1.25rem" }}>
          <div style={{ fontWeight: 600, marginBottom: "0.6rem", fontSize: "0.9rem", textAlign: "center" }}>
            Dev - API Target:
          </div>
          <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem" }}>
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
        </div>
      )}
    </div>
  );
}
