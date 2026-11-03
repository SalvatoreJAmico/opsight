import React, { useEffect, useState, useCallback, useRef } from "react";
import { getHealth, getSessionState, resetSession } from "./api/client";
import GlobalStatusBar from "./components/GlobalStatusBar";
import DatasetTab from "./tabs/DatasetTab";
import MetricsTab from "./tabs/MetricsTab";
import ChartsTab from "./tabs/ChartsTab";
import CleaningAuditTab from "./tabs/CleaningAuditTab";
import AnomalyDetectionTab from "./tabs/AnomalyDetectionTab";
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
  { id: "cleaning-audit", label: "Cleaning Audit" },
  { id: "anomaly-detection", label: "Anomaly Detection" },
  { id: "prediction", label: "Prediction" },
];

export default function App() {
  const isDev = import.meta.env.DEV;
  const [activeTab, setActiveTab] = useState("dataset");
  const [uiResetVersion, setUiResetVersion] = useState(0);
  const [resettingSession, setResettingSession] = useState(false);
  const [healthStatus, setHealthStatus] = useState("Checking API...");
  const [healthError, setHealthError] = useState("");
  const [apiVersion, setApiVersion] = useState("");
  const [pipelineResult, setPipelineResult] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [pendingDatasetId, setPendingDatasetId] = useState(null);

  const selectionVersion = useRef(0);
  const pendingDataset = useRef(null);
  const runInFlight = useRef(false);

  const activeDatasetIdentity = pendingDatasetId ?? sessionState?.active_dataset ?? null;
  const pipelineCompleted = pendingDatasetId == null && sessionState?.pipeline_status === "completed";

  const applySessionState = useCallback((result, version) => {
    if (!result.ok || version !== selectionVersion.current || runInFlight.current || pendingDataset.current !== null) return;
    setSessionState(result.data);
  }, []);

  const refreshSessionState = useCallback(async () => {
    const version = selectionVersion.current;
    const result = await getSessionState();
    applySessionState(result, version);
  }, [applySessionState]);

  const handleDatasetChange = useCallback((datasetId) => {
    selectionVersion.current += 1;
    runInFlight.current = false;
    pendingDataset.current = datasetId ?? "";
    setPendingDatasetId(datasetId || null);
    setPipelineResult(null);
    setSessionState(buildResetSessionState(datasetId));
  }, []);

  const handlePipelineStart = useCallback((datasetId) => {
    selectionVersion.current += 1;
    runInFlight.current = true;
    setPipelineResult(null);
    setSessionState({ ...buildResetSessionState(datasetId), pipeline_status: "running" });
    return selectionVersion.current;
  }, []);

  const handlePipelineComplete = (result, version) => {
    if (version != null && version !== selectionVersion.current) return;
    pendingDataset.current = null;
    setPendingDatasetId(null);
    setPipelineResult({ datasetId: activeDatasetIdentity, data: result });
    setSessionState((previous) => ({ ...previous, pipeline_status: "completed" }));
  };

  const handlePipelineAction = (version) => {
    if (version != null && version !== selectionVersion.current) return;
    if (runInFlight.current) {
      runInFlight.current = false;
      pendingDataset.current = null;
      setPendingDatasetId(null);
    }
    refreshSessionState();
  };

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
    let cancelled = false;
    const poll = async () => {
      const version = selectionVersion.current;
      const result = await getSessionState();
      if (!cancelled) applySessionState(result, version);
    };
    poll();
    const intervalId = setInterval(poll, 8000);
    return () => { cancelled = true; clearInterval(intervalId); };
  }, [applySessionState]);

  const handleSessionReset = useCallback(async () => {
    setResettingSession(true);
    setHealthError("");

    const response = await resetSession();
    if (!response.ok) {
      setHealthError(response.error || "Session reset failed.");
      setResettingSession(false);
      return;
    }

    selectionVersion.current += 1;
    pendingDataset.current = null;
    runInFlight.current = false;
    setPendingDatasetId(null);
    setPipelineResult(null);
    setSessionState(response.data?.session || buildResetSessionState(null));
    setActiveTab("dataset");
    setUiResetVersion((prev) => prev + 1);
    await refreshSessionState();
    setResettingSession(false);
  }, [refreshSessionState]);

  const panelKey = `${activeTab}-${uiResetVersion}`;
  const analysisKey = `${panelKey}-${activeDatasetIdentity}-${sessionState?.pipeline_status}-${sessionState?.pipeline_run_id || ""}-${sessionState?.selected_variables?.target || ""}`;
  const currentMetrics = pipelineCompleted
    ? sessionState?.pipeline_summary || (pipelineResult?.datasetId === activeDatasetIdentity ? pipelineResult.data : null)
    : null;

  const renderPanel = () => {
    switch (activeTab) {
      case "dataset":
        return (
          <DatasetTab
            key={panelKey}
            onPipelineComplete={handlePipelineComplete}
            onPipelineStart={handlePipelineStart}
            onAction={handlePipelineAction}
            onDatasetChange={handleDatasetChange}
          />
        );
      case "metrics":
        return <MetricsTab key={panelKey} pipelineResult={currentMetrics} />;
      case "charts":
        return <ChartsTab key={analysisKey} activeDatasetId={pipelineCompleted ? activeDatasetIdentity : null} />;
      case "cleaning-audit":
        return <CleaningAuditTab key={analysisKey} activeDatasetId={pipelineCompleted ? activeDatasetIdentity : null} />;
      case "anomaly-detection":
        return <AnomalyDetectionTab key={analysisKey} onAction={refreshSessionState} pipelineCompleted={pipelineCompleted} />;
      case "prediction":
        return <PredictionTab key={analysisKey} onAction={refreshSessionState} pipelineCompleted={pipelineCompleted} />;
      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "2rem" }}>
      <header style={{ marginBottom: "1.5rem" }}>
        <h1>Opsight</h1>
        <p>A working demo for operational analytics, visualization, and anomaly detection.</p>
        <p>
          Tested with selected CSV, SQL, JSON, Parquet, and XLSX datasets.
          {" "}Long-term goal: support every dataset.
        </p>

        {isDev ? (
          <>
            <div
              style={{
                marginTop: "1rem",
                padding: "0.75rem 1rem",
                 border: "1px solid #444",
                borderRadius: "10px",
                 background: "#1a1a1a",
                fontSize: "0.9rem",
                             textAlign: "center",
                             color: "#e0e0e0",
              }}
            >
              <strong>{healthStatus}</strong>
              {apiVersion ? <span> — version {apiVersion}</span> : null}
              {healthError ? (
                 <p style={{ marginTop: "0.5rem", color: "#ff6b6b" }}>{healthError}</p>
              ) : null}
            </div>
             <div style={{ marginTop: "0.75rem", textAlign: "center" }}>
              <button
                type="button"
                onClick={handleSessionReset}
                disabled={resettingSession}
                style={{
                  padding: "0.65rem 1rem",
                  borderRadius: "8px",
                   border: "1px solid #555",
                  cursor: resettingSession ? "not-allowed" : "pointer",
                  fontWeight: 600,
                   background: "#333",
                   color: "#e0e0e0",
                  fontSize: "0.9rem",
                }}
              >
                {resettingSession ? "Resetting..." : "Reset Session"}
              </button>
            </div>
          </>
        ) : (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.75rem 1rem",
              borderRadius: "10px",
              fontSize: "0.9rem",
               color: "#999",
            }}
          >
            {healthError ? (
               <p style={{ color: "#ff6b6b", marginBottom: 0 }}>{healthError}</p>
            ) : (
              <p style={{ marginBottom: 0, opacity: 0.7 }}>{healthStatus}</p>
            )}
          </div>
        )}
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
