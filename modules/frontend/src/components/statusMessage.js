export function resolveStatusMessage(sessionState) {
  const s = sessionState || {};

  if (s.pipeline_status === "failed") {
    return { text: "Pipeline failed \u2014 check the logs", type: "failed" };
  }
  if (s.pipeline_status === "running") {
    return { text: "Pipeline is running...", type: "running" };
  }
  if (s.anomaly_status === "running") {
    return { text: "Anomaly detection running...", type: "running" };
  }
  if (s.prediction_status === "running") {
    return { text: "Prediction model running...", type: "running" };
  }
  if (s.pipeline_status === "completed") {
    return { text: "Pipeline completed successfully", type: "completed" };
  }
  if (s.anomaly_status === "completed") {
    return { text: "Anomaly detection complete", type: "completed" };
  }
  if (s.prediction_status === "completed") {
    return { text: "Prediction complete", type: "completed" };
  }
  if (s.active_dataset == null) {
    return { text: "No dataset loaded \u2014 select a dataset to get started", type: "default" };
  }
  return { text: `Dataset loaded: ${s.active_dataset}`, type: "default" };
}
