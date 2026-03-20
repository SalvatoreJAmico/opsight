export default function MlTab() {
  return (
    <div>
      <h2>ML</h2>
      <p>Operational anomaly detection views for Opsight.</p>

      <h3>Algorithm</h3>
      <p>
        Isolation Forest is planned as the primary anomaly detection algorithm.
        It works by isolating unusual observations that require fewer random splits
        than normal data points.
      </p>

      <h3>Model Control</h3>
      <button
        type="button"
        disabled
        style={{
          padding: "0.75rem 1rem",
          borderRadius: "8px",
          border: "1px solid #ccc",
          cursor: "not-allowed",
          fontWeight: 600,
        }}
      >
        Run Model
      </button>
      <p style={{ marginTop: "0.5rem", opacity: 0.8 }}>
        Model execution will be added in a later ML phase.
      </p>

      <h3>Results</h3>
      <p>No anomaly detection results yet.</p>

      <h3>Evaluation Metrics</h3>
      <p>Precision, recall, F1-score, and ROC-AUC will appear here in a later phase.</p>
    </div>
  );
}