import React from "react";

export default function ModelCard({ model, checked, onToggle, disabled = false, loading = false, error = "", result = null }) {
  const formatRoleLabel = (role) => role.replace(/_/g, " ");
  const datasetContextEntries = Object.entries(result?.datasetContext || {}).filter(([, value]) => Boolean(value));
  const explanation = result?.explanation || null;

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: "10px",
        padding: "1rem",
        marginBottom: "1rem",
      }}
    >
      <label style={{ fontWeight: 600 }}>
        <input
          type="checkbox"
          checked={checked}
          onChange={onToggle}
          disabled={disabled}
          style={{ marginRight: "0.5rem" }}
        />
        {model.name}
      </label>

      {checked && (
        <div style={{ marginTop: "0.75rem" }}>
          <p><strong>In plain English:</strong> {model.education}</p>
          <p><strong>Best when:</strong> {model.recommendation}</p>

          <div
            style={{
              marginTop: "0.75rem",
              padding: "0.75rem",
              background: "#f9f9f9",
              borderRadius: "6px",
            }}
          >
            <strong>Results:</strong>
            {loading && <p style={{ marginTop: "0.5rem", margin: "0.5rem 0 0 0" }}>Loading...</p>}
            {error && <p style={{ marginTop: "0.5rem", color: "#d32f2f", margin: "0.5rem 0 0 0" }}>{error}</p>}
            {!loading && !error && result && (
              <div style={{ marginTop: "0.5rem" }}>
                <p style={{ margin: "0 0 0.35rem 0" }}>
                  <strong>Status:</strong> {result.status}
                </p>
                <p style={{ margin: "0 0 0.35rem 0" }}>
                  <strong>What this output shows:</strong> {result.summary}
                </p>
                <p style={{ margin: 0 }}>
                  <strong>What it means:</strong> {result.notes}
                </p>
                {explanation ? (
                  <div
                    style={{
                      marginTop: "0.65rem",
                      padding: "0.6rem",
                      border: "1px solid #ddd",
                      borderRadius: "6px",
                      background: "#fff",
                    }}
                  >
                    <strong>How to read this result</strong>
                    {explanation.what ? (
                      <p style={{ margin: "0.35rem 0 0 0" }}><strong>Output:</strong> {explanation.what}</p>
                    ) : null}
                    {explanation.time ? (
                      <p style={{ margin: "0.35rem 0 0 0" }}><strong>Time usage:</strong> {explanation.time}</p>
                    ) : null}
                    {explanation.comparison ? (
                      <p style={{ margin: "0.35rem 0 0 0" }}><strong>Comparison:</strong> {explanation.comparison}</p>
                    ) : null}
                    {explanation.where ? (
                      <p style={{ margin: "0.35rem 0 0 0" }}><strong>Where to find it:</strong> {explanation.where}</p>
                    ) : null}
                  </div>
                ) : null}
                {datasetContextEntries.length > 0 ? (
                  <div
                    style={{
                      marginTop: "0.65rem",
                      padding: "0.6rem",
                      border: "1px solid #ddd",
                      borderRadius: "6px",
                      background: "#fff",
                    }}
                  >
                    <strong>Fields used</strong>
                    {datasetContextEntries.map(([role, field]) => (
                      <p key={role} style={{ margin: "0.35rem 0 0 0" }}>
                        <strong>{formatRoleLabel(role)}:</strong> {field}
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}