import { useEffect, useState } from "react";
import { getHealth } from "./api/client";
import UploadTab from "./tabs/UploadTab";
import MetricsTab from "./tabs/MetricsTab";
import ChartsTab from "./tabs/ChartsTab";

const tabs = [
  { id: "upload", label: "Upload" },
  { id: "metrics", label: "Metrics" },
  { id: "charts", label: "Charts" },
  { id: "ml", label: "ML" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("upload");
  const [healthStatus, setHealthStatus] = useState("Checking API...");
  const [healthError, setHealthError] = useState("");
  const [apiVersion, setApiVersion] = useState("");
  const [pipelineResult, setPipelineResult] = useState(null);

  useEffect(() => {
    async function checkApi() {
      const result = await getHealth();

      if (result.ok) {
        setHealthStatus("API connected");
        setApiVersion(result.data?.version || "");
        setHealthError("");
      } else {
        setHealthStatus("API unavailable");
        setHealthError(result.error || "Unable to reach API");
      }
    }

    checkApi();
  }, []);

  const renderPanel = () => {
    switch (activeTab) {
      case "upload":
        return <UploadTab onPipelineComplete={setPipelineResult} />;
      case "metrics":
        return <MetricsTab pipelineResult={pipelineResult} />;
      case "charts":
         return <ChartsTab />;
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

        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            border: "1px solid #ddd",
            borderRadius: "10px",
          }}
        >
          <strong>{healthStatus}</strong>
          {apiVersion ? <span> — version {apiVersion}</span> : null}
          {healthError ? (
            <p style={{ marginTop: "0.5rem" }}>{healthError}</p>
          ) : null}
        </div>
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