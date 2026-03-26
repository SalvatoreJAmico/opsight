import React, { useEffect, useState, useCallback } from "react";
import { getHealth, getSessionState } from "./api/client";
import GlobalStatusBar from "./components/GlobalStatusBar";
import DatasetTab from "./tabs/UploadTab";
import MetricsTab from "./tabs/MetricsTab";
import ChartsTab from "./tabs/ChartsTab";
import MlTab from "./tabs/MlTab";
import PredictionTab from "./tabs/PredictionTab";

const RESET_SESSION_STATE = {
  pipeline_status: "not_run",
  anomaly_status: "idle",
  prediction_status: "idle",
};

function buildResetSessionState(datasetId) {
  return {
    active_dataset: datasetId || null,
    ...RESET_SESSION_STATE,
  };
}

const tabs = [
  { id: "dataset", label: "Dataset" },
  { id: "metrics", label: "Metrics" },
  { id: "charts", label: "Charts" },
  { id: "ml", label: "ML" },
  { id: "prediction", label: "Prediction" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("dataset");
  const [healthStatus, setHealthStatus] = useState("Checking API...");
  const [healthError, setHealthError] = useState("");
  const [apiVersion, setApiVersion] = useState("");
  const [pipelineResult, setPipelineResult] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [pendingDatasetId, setPendingDatasetId] = useState(null);

  const activeDatasetIdentity = pendingDatasetId ?? sessionState?.active_dataset ?? null;

  const refreshSessionState = useCallback(async () => {
    const result = await getSessionState();
    if (result.ok) {
      if (pendingDatasetId && result.data?.active_dataset !== pendingDatasetId) {
        setSessionState(buildResetSessionState(pendingDatasetId));
        return;
      }

      if (pendingDatasetId && result.data?.active_dataset === pendingDatasetId) {
        setPendingDatasetId(null);
      }

      setSessionState(result.data);
    }
  }, [pendingDatasetId]);

  const handleDatasetChange = useCallback((datasetId) => {
    setPendingDatasetId(datasetId || null);
    setSessionState(buildResetSessionState(datasetId));
  }, []);

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

  useEffect(() => {
    refreshSessionState();
    const intervalId = setInterval(refreshSessionState, 8000);
    return () => clearInterval(intervalId);
  }, [refreshSessionState]);

  useEffect(() => {
    setPipelineResult(null);
  }, [activeDatasetIdentity]);

  const renderPanel = () => {
    switch (activeTab) {
      case "dataset":
        return (
          <DatasetTab
            onPipelineComplete={setPipelineResult}
            onAction={refreshSessionState}
            onDatasetChange={handleDatasetChange}
          />
        );
      case "metrics":
        return <MetricsTab pipelineResult={pipelineResult} />;
      case "charts":
        return <ChartsTab />;
      case "ml":
        return <MlTab onAction={refreshSessionState} />;
      case "prediction":
        return <PredictionTab onAction={refreshSessionState} />;
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

      <GlobalStatusBar sessionState={sessionState} />

      <nav
        style={{
          display: "flex",
          gap: "0.75rem",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
        }}
      >
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
