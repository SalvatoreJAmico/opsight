export default function ModelCard({ model, checked, onToggle, result }) {
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
          style={{ marginRight: "0.5rem" }}
        />
        {model.name}
      </label>

      {checked && (
        <div style={{ marginTop: "0.75rem" }}>
          <p><strong>Education:</strong> {model.education}</p>
          <p><strong>Recommendation:</strong> {model.recommendation}</p>

          <div
            style={{
              marginTop: "0.75rem",
              padding: "0.75rem",
              background: "#f9f9f9",
              borderRadius: "6px",
            }}
          >
            <strong>Results:</strong>
            <div style={{ marginTop: "0.5rem" }}>
              <p style={{ margin: "0 0 0.35rem 0" }}>
                <strong>Status:</strong> {result.status}
              </p>
              <p style={{ margin: "0 0 0.35rem 0" }}>
                <strong>Summary:</strong> {result.summary}
              </p>
              <p style={{ margin: 0 }}>
                <strong>Notes:</strong> {result.notes}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}