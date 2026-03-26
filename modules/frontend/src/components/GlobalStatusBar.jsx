const STATUS_COLORS = {
  // pipeline statuses
  completed: "#6ee7b7",
  running: "#fbbf24",
  failed: "#f87171",
  not_run: "#9ca3af",
  // model statuses
  idle: "#9ca3af",
  // dataset pseudo-statuses
  loaded: "#6ee7b7",
  none: "#9ca3af",
};

function StatusPill({ label, value }) {
  const displayValue = value ?? "unknown";
  const color = STATUS_COLORS[displayValue] ?? "#9ca3af";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: "0.3rem 0.75rem",
        borderRadius: "999px",
        border: "1px solid #2e303a",
        background: "#111827",
      }}
    >
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          background: color,
          flexShrink: 0,
        }}
      />
      <span style={{ fontSize: "0.78rem", color: "#9ca3af" }}>{label}:</span>
      <span style={{ fontSize: "0.78rem", color: color, fontWeight: 600 }}>
        {displayValue}
      </span>
    </div>
  );
}

export default function GlobalStatusBar({ sessionState }) {
  const s = sessionState || {};
  const datasetValue = s.active_dataset != null ? "loaded" : "none";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.6rem",
        flexWrap: "wrap",
        padding: "0.55rem 1rem",
        border: "1px solid #2e303a",
        borderRadius: "10px",
        marginBottom: "1.25rem",
        background: "#0d0e14",
      }}
    >
      <span
        style={{
          fontSize: "0.7rem",
          color: "#4b5563",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          marginRight: "0.25rem",
          flexShrink: 0,
        }}
      >
        Status
      </span>
      <StatusPill label="Dataset" value={datasetValue} />
      <StatusPill label="Pipeline" value={s.pipeline_status} />
      <StatusPill label="Anomaly" value={s.anomaly_status} />
      <StatusPill label="Prediction" value={s.prediction_status} />
    </div>
  );
}
