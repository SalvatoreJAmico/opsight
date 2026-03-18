import { useState } from "react";

const tabs = [
  { id: "upload", label: "Upload" },
  { id: "metrics", label: "Metrics" },
  { id: "charts", label: "Charts" },
  { id: "ml", label: "ML" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("upload");

  const renderPanel = () => {
    switch (activeTab) {
      case "upload":
        return (
          <>
            <h2>Upload</h2>
            <p>Upload workflow will appear here.</p>
            <p>Dataset upload and sample dataset selection will be added in PS-119.</p>
          </>
        );
      case "metrics":
        return (
          <>
            <h2>Metrics</h2>
            <p>Summary metrics and KPI views will appear here.</p>
            <p>Connected metrics UI will be added in PS-120.</p>
          </>
        );
      case "charts":
        return (
          <>
            <h2>Charts</h2>
            <p>Dataset visualizations will appear here.</p>
            <p>Chart rendering will be added in PS-114.</p>
          </>
        );
      case "ml":
        return (
          <>
            <h2>ML</h2>
            <p>Anomaly detection outputs will appear here.</p>
            <p>ML result views will be added in PS-115.</p>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "2rem" }}>
      <header style={{ marginBottom: "1.5rem" }}>
        <h1>Opsight</h1>
        <p>Operational analytics, visualization, and anomaly detection demo UI.</p>
      </header>

      <nav style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "0.75rem 1rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
              cursor: "pointer",
              fontWeight: activeTab === tab.id ? "700" : "400",
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main
        style={{
          border: "1px solid #ddd",
          borderRadius: "12px",
          padding: "1.5rem",
          minHeight: "280px",
        }}
      >
        {renderPanel()}
      </main>
    </div>
  );
}
