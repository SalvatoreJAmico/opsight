export default function MetricsTab({ pipelineResult }) {
  if (!pipelineResult) {
    return (
      <div>
        <h2>Pipeline Metrics</h2>
        <p>No data yet. Run the pipeline from the Upload tab.</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Pipeline Metrics</h2>

      <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        <MetricCard label="Ingested" value={pipelineResult.records_ingested} />
        <MetricCard label="Valid" value={pipelineResult.records_valid} />
        <MetricCard label="Invalid" value={pipelineResult.records_invalid} />
        <MetricCard label="Persisted" value={pipelineResult.records_persisted} />
      </div>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div
      style={{
        border: "1px solid #ccc",
        borderRadius: "10px",
        padding: "1rem",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "0.9rem", opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{value ?? 0}</div>
    </div>
  );
}