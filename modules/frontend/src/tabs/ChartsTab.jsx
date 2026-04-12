import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  getHistogram,
  getBarCategory,
  getBoxplot,
  getScatter,
  getGroupedComparison,
  getGroupedBoxplot,
  getTimeLine,
  getChartOverview,
  getVariableSelection,
  saveVariableSelection,
  resolveApiAssetUrl,
} from "../api/client";
import { chartCatalog } from "../catalog/chartCatalog";
import { resolveBaseUrl } from "../config/env";

const DEFAULT_TARGET_VARIABLE = "Sales";
const FALLBACK_TARGET_OPTIONS = [DEFAULT_TARGET_VARIABLE];
const FALLBACK_COMPARE_OPTIONS = ["Profit", "Quantity", "Discount", "Category", "Order Date"];
const CHART_COLOR_OPTIONS = [
  { label: "Blue", value: "#2563eb" },
  { label: "Green", value: "#16a34a" },
  { label: "Red", value: "#dc2626" },
  { label: "Orange", value: "#ea580c" },
  { label: "Purple", value: "#7c3aed" },
  { label: "Gray", value: "#6b7280" },
];
const DEFAULT_CHART_ENHANCEMENTS = {
  title: "",
  subtitle: "",
  xLabel: "",
  yLabel: "",
  showLegend: false,
  showGrid: true,
  color: "#2563eb",
  annotation: "",
  xMin: "",
  xMax: "",
  yMin: "",
  yMax: "",
  logScaleX: false,
  logScaleY: false,
  clipMode: "none",
  clipPercentile: "95",
  clipMax: "",
  zoomPreset: "full_range",
};
const summaryCardStyle = {
  border: "1px solid #374151",
  borderRadius: "12px",
  padding: "1rem",
  background: "#111827",
  color: "#f9fafb",
  textAlign: "center",
  minHeight: "100%",
  width: "100%",
  boxSizing: "border-box",
  boxShadow: "0 8px 20px rgba(0, 0, 0, 0.18)",
};
const summaryCardTitleStyle = {
  marginTop: 0,
  marginBottom: "0.75rem",
  fontSize: "0.95rem",
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#e5e7eb",
};
const summaryMetricStyle = {
  margin: "0.3rem 0",
  color: "#d1d5db",
};
const summaryDividerStyle = {
  border: 0,
  borderTop: "1px solid #374151",
  margin: "0.8rem 0",
};

function normalizeFieldName(fieldName) {
  return String(fieldName || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\s+/g, " ");
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(objectUrl);
}

export default function ChartsTab({ activeDatasetId = null }) {
  const isDev = import.meta.env.DEV;
  const [target, setTarget] = useState(isDev ? "local" : "cloud");
  const [activeChart, setActiveChart] = useState("");
  const [chartImages, setChartImages] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState("");
  const [targetVariable, setTargetVariable] = useState(DEFAULT_TARGET_VARIABLE);
  const [compareVariables, setCompareVariables] = useState([FALLBACK_COMPARE_OPTIONS[0]]);
  const [chartEnhancements, setChartEnhancements] = useState(DEFAULT_CHART_ENHANCEMENTS);
  const [chartMetadata, setChartMetadata] = useState({});
  const [relationshipRuns, setRelationshipRuns] = useState([]);
  const [relationshipLoading, setRelationshipLoading] = useState(false);
  const [relationshipError, setRelationshipError] = useState("");
  const [axisSlider, setAxisSlider] = useState({
    xMin: 0,
    xMax: 0,
    yMin: 0,
    yMax: 0,
    xTouched: false,
    yTouched: false,
  });
  const [dragSelection, setDragSelection] = useState(null);
  const dragStartRef = useRef(null);
  const chartContainerRef = useRef(null);
  const selectionLoadedRef = useRef(false);

  useEffect(() => {
    if (!activeDatasetId) {
      setOverview(null);
      setOverviewError("");
      selectionLoadedRef.current = false;
      return;
    }

    let cancelled = false;
    setOverviewLoading(true);
    setOverviewError("");

    const baseUrl = resolveBaseUrl(target);
    getChartOverview({ baseUrl }).then((result) => {
      if (cancelled) return;
      setOverviewLoading(false);
      if (result.ok) {
        setOverview(result.data);
      } else {
        setOverviewError(result.error || "Failed to load dataset overview.");
      }
    });

    return () => {
      cancelled = true;
    };
  }, [activeDatasetId, target]);

  useEffect(() => {
    if (!activeDatasetId) return;

    let cancelled = false;
    const baseUrl = resolveBaseUrl(target);

    getVariableSelection({ baseUrl }).then((result) => {
      if (cancelled) return;
      if (result.ok && result.data?.target) {
        setTargetVariable(result.data.target);
        setCompareVariables(
          Array.isArray(result.data.compare) && result.data.compare.length > 0
            ? result.data.compare
            : [FALLBACK_COMPARE_OPTIONS[0]],
        );
        selectionLoadedRef.current = true;
      }
    });

    return () => {
      cancelled = true;
    };
  }, [activeDatasetId, target]);

  useEffect(() => {
    if (selectionLoadedRef.current) return;
    const nextTarget = overview?.assignment_analysis?.target_variable || DEFAULT_TARGET_VARIABLE;
    const nextCompareOptions = overview?.assignment_analysis?.compare_options || FALLBACK_COMPARE_OPTIONS;

    if (targetVariable !== nextTarget) {
      setTargetVariable(nextTarget);
    }

    if (!nextCompareOptions.includes(compareVariables[0])) {
      setCompareVariables([nextCompareOptions[0] || FALLBACK_COMPARE_OPTIONS[0]]);
    }
  }, [overview, targetVariable, compareVariables]);

  const targetOptions = overview?.assignment_analysis?.target_options || FALLBACK_TARGET_OPTIONS;
  const compareOptions = overview?.assignment_analysis?.compare_options || FALLBACK_COMPARE_OPTIONS;
  const compareVariable = compareVariables[0] ?? FALLBACK_COMPARE_OPTIONS[0];
  const axisContext = useMemo(
    () => getAxisContext(activeChart, overview, targetVariable, compareVariable),
    [activeChart, overview, targetVariable, compareVariable],
  );

  const buildEnhancementPayload = () => ({
    title: chartEnhancements.title,
    subtitle: chartEnhancements.subtitle,
    xLabel: chartEnhancements.xLabel,
    yLabel: chartEnhancements.yLabel,
    showLegend: chartEnhancements.showLegend,
    showGrid: chartEnhancements.showGrid,
    color: chartEnhancements.color,
    annotation: chartEnhancements.annotation,
    xMin: chartEnhancements.xMin,
    xMax: chartEnhancements.xMax,
    yMin: chartEnhancements.yMin,
    yMax: chartEnhancements.yMax,
    logScaleX: chartEnhancements.logScaleX,
    logScaleY: chartEnhancements.logScaleY,
    clipMode: chartEnhancements.clipMode,
    clipPercentile: chartEnhancements.clipPercentile,
    clipMax: chartEnhancements.clipMax,
    zoomPreset: chartEnhancements.zoomPreset,
  });

  useEffect(() => {
    const hasX = axisContext.x && Number.isFinite(axisContext.x.min) && Number.isFinite(axisContext.x.max);
    const hasY = axisContext.y && Number.isFinite(axisContext.y.min) && Number.isFinite(axisContext.y.max);

    setAxisSlider((prev) => ({
      xMin: hasX ? axisContext.x.min : 0,
      xMax: hasX ? axisContext.x.max : 0,
      yMin: hasY ? axisContext.y.min : 0,
      yMax: hasY ? axisContext.y.max : 0,
      xTouched: false,
      yTouched: false,
    }));

    setChartEnhancements((prev) => ({
      ...prev,
      xMin: "",
      xMax: "",
      yMin: "",
      yMax: "",
    }));
  }, [axisContext.x?.min, axisContext.x?.max, axisContext.y?.min, axisContext.y?.max]);

  const applyAxisFromSlider = async (axis) => {
    let nextEnhancements = chartEnhancements;
    if (axis === "x") {
      nextEnhancements = {
        ...chartEnhancements,
        xMin: String(axisSlider.xMin),
        xMax: String(axisSlider.xMax),
      };
    } else {
      nextEnhancements = {
        ...chartEnhancements,
        yMin: String(axisSlider.yMin),
        yMax: String(axisSlider.yMax),
      };
    }

    setChartEnhancements(nextEnhancements);
    if (activeChart) {
      await handleChartSelect(activeChart, nextEnhancements);
    }
  };

  const handleTargetChange = (newTarget) => {
    setTargetVariable(newTarget);
    const baseUrl = resolveBaseUrl(target);
    saveVariableSelection({ baseUrl, target: newTarget, compare: compareVariables });
  };

  const handleCompareChange = (newCompareArr) => {
    setCompareVariables(newCompareArr);
    const baseUrl = resolveBaseUrl(target);
    saveVariableSelection({ baseUrl, target: targetVariable, compare: newCompareArr });
  };
  const missingValueEntries = Object.entries(overview?.missing_by_column || {}).filter(([, missing]) =>
    Number(missing) > 0,
  );
  const selectedVariables = Array.from(
    new Set(
      [targetVariable, ...compareVariables]
        .filter(Boolean)
        .map((fieldName) => normalizeFieldName(fieldName)),
    ),
  );
  const filteredNumericSummary = (overview?.numeric_summary || []).filter((item) =>
    selectedVariables.includes(normalizeFieldName(item.field)),
  );
  const dateFieldNames = new Set(
    (overview?.date_summary || []).map((item) => normalizeFieldName(item.field)),
  );
  const filteredDateSummary = (overview?.date_summary || []).filter((item) =>
    selectedVariables.includes(normalizeFieldName(item.field)),
  );
  const filteredCategoricalSummary = (overview?.categorical_summary || []).filter((item) =>
    selectedVariables.includes(normalizeFieldName(item.field)) &&
    !dateFieldNames.has(normalizeFieldName(item.field)),
  );

  const renderSummaryCardsForVariable = (normalizedFieldName) => (
    <>
      {filteredNumericSummary
        .filter((item) => normalizeFieldName(item.field) === normalizedFieldName)
        .map((item) => (
          <div
            key={`numeric-${item.field}`}
            data-testid={`numeric-summary-card-${normalizeFieldName(item.field).replace(/\s+/g, "-")}`}
            style={summaryCardStyle}
          >
            <p style={summaryCardTitleStyle}>{item.field}</p>
            <p style={summaryMetricStyle}>Count: {item.count}</p>
            <p style={summaryMetricStyle}>Missing: {item.missing}</p>
            <hr style={summaryDividerStyle} />
            <p style={summaryMetricStyle}>Min: {item.min ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Max: {item.max ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Mean: {item.mean ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Median: {item.median ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Std Dev: {item.std ?? "N/A"}</p>
          </div>
        ))}

      {filteredDateSummary
        .filter((item) => normalizeFieldName(item.field) === normalizedFieldName)
        .map((item) => (
          <div
            key={`date-${item.field}`}
            data-testid={`date-summary-card-${normalizeFieldName(item.field).replace(/\s+/g, "-")}`}
            style={summaryCardStyle}
          >
            <p style={summaryCardTitleStyle}>{item.field}</p>
            <p style={summaryMetricStyle}>Count: {item.count}</p>
            <p style={summaryMetricStyle}>Missing: {item.missing}</p>
            <hr style={summaryDividerStyle} />
            <p style={summaryMetricStyle}>Min Date: {item.min_date ?? "N/A"}</p>
            <p style={summaryMetricStyle}>Max Date: {item.max_date ?? "N/A"}</p>
          </div>
        ))}

      {filteredCategoricalSummary
        .filter((item) => normalizeFieldName(item.field) === normalizedFieldName)
        .map((item) => (
          <div
            key={`categorical-${item.field}`}
            data-testid={`categorical-summary-card-${normalizeFieldName(item.field).replace(/\s+/g, "-")}`}
            style={summaryCardStyle}
          >
            <p style={summaryCardTitleStyle}>{item.field}</p>
            <p style={summaryMetricStyle}>Unique: {item.unique}</p>
            <p style={summaryMetricStyle}>Missing: {item.missing}</p>
            <hr style={summaryDividerStyle} />
            {item.top_values?.length ? (
              <div>
                {item.top_values.map((entry, index) => (
                  <p
                    key={`cat-${item.field}-${entry.value}-${index}`}
                    style={summaryMetricStyle}
                  >
                    {entry.value}: {entry.count}
                  </p>
                ))}
              </div>
            ) : null}
          </div>
        ))}
    </>
  );

  const loadChartById = async (chartId, enhancementOverride = null) => {
    const baseUrl = resolveBaseUrl(target);
    const enhancements = enhancementOverride || buildEnhancementPayload();
    switch (chartId) {
      case "histogram":
        return getHistogram({ baseUrl, targetVariable, enhancements });
      case "bar-category":
        return getBarCategory({ baseUrl, targetVariable, compareVariable, enhancements });
      case "boxplot":
        return getBoxplot({ baseUrl, targetVariable, enhancements });
      case "scatter":
        return getScatter({ baseUrl, targetVariable, compareVariable, enhancements });
      case "grouped-comparison":
        return getGroupedComparison({ baseUrl, targetVariable, compareVariable, enhancements });
      case "grouped-boxplot":
        return getGroupedBoxplot({ baseUrl, targetVariable, compareVariable, enhancements });
      case "time-line":
        return getTimeLine({ baseUrl, targetVariable, compareVariable, enhancements });
      default:
        return { ok: false, error: "Unsupported chart selection." };
    }
  };

  const handleExportSummary = () => {
    if (!overview) {
      return;
    }

    const datasetName = overview.source_metadata?.dataset_id || activeDatasetId || "dataset";
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `${datasetName}-summary-${timestamp}.json`;

    downloadJson(filename, {
      source: overview.source,
      source_metadata: overview.source_metadata,
      shape: overview.shape,
      fields: overview.fields,
      selected_variables: {
        target: targetVariable,
        compare: compareVariables,
      },
      assignment_analysis: overview.assignment_analysis,
      relationship_chart_list: relationshipRuns.map((entry) => ({
        chart_id: entry.chartId,
        chart_title: entry.chartTitle,
        target_variable: entry.targetVariable,
        compare_variable: entry.compareVariable,
        enhancement_metadata: entry.enhancementMetadata,
        image: entry.image,
        generated_at: entry.generatedAt,
      })),
      chart_enhancement_controls: {
        ...chartEnhancements,
      },
      chart_metadata: chartMetadata,
      missing_by_column: overview.missing_by_column,
      numeric_summary: overview.numeric_summary,
      date_summary: overview.date_summary,
      categorical_summary: overview.categorical_summary,
    });
  };

  const handleChartSelect = async (chartId, enhancementOverride = null) => {
    setError("");
    setDragSelection(null);
    setActiveChart(chartId);
    setLoading(true);
    setChartImages({});
    setChartMetadata({});

    const response = await loadChartById(chartId, enhancementOverride);

    setLoading(false);

    if (!response.ok) {
      setActiveChart("");
      setError(response.error || "Chart request failed.");
      return;
    }

    const resolvedImageUrl = resolveApiAssetUrl(
      response.data?.image,
      resolveBaseUrl(target)
    );

    if (!resolvedImageUrl) {
      setActiveChart("");
      setError("Chart response did not include an image path.");
      return;
    }

    const cacheBustedImageUrl = `${resolvedImageUrl}${resolvedImageUrl.includes("?") ? "&" : "?"}t=${Date.now()}`;

    setChartImages((prev) => ({
      ...prev,
      [chartId]: cacheBustedImageUrl,
    }));

    setChartMetadata((prev) => ({
      ...prev,
      [chartId]: response.data?.chart_metadata || { enhancements: enhancementOverride || buildEnhancementPayload() },
    }));
  };

  const handleResetZoom = async () => {
    if (!activeChart) {
      return;
    }

    const nextEnhancements = {
      ...chartEnhancements,
      xMin: "",
      xMax: "",
      yMin: "",
      yMax: "",
      zoomPreset: "full_range",
    };
    setChartEnhancements(nextEnhancements);
    await handleChartSelect(activeChart, nextEnhancements);
  };

  const handleResetChart = async () => {
    if (!activeChart) {
      return;
    }

    const nextEnhancements = {
      ...DEFAULT_CHART_ENHANCEMENTS,
      color: chartEnhancements.color,
    };
    setChartEnhancements(nextEnhancements);
    await handleChartSelect(activeChart, nextEnhancements);
  };

  const handleRunRelationshipAnalysis = async () => {
    setRelationshipError("");
    setRelationshipLoading(true);

    const relationshipChartIds = ["scatter", "grouped-boxplot"];
    const runEntries = [];

    for (const compareVariableCandidate of compareVariables) {
      const chartIdsForVariable = [...relationshipChartIds];
      if (normalizeFieldName(compareVariableCandidate) === "order date") {
        chartIdsForVariable.push("time-line");
      }

      for (const chartId of chartIdsForVariable) {
        const baseUrl = resolveBaseUrl(target);
        let response;
        if (chartId === "scatter") {
          response = await getScatter({
            baseUrl,
            targetVariable,
            compareVariable: compareVariableCandidate,
            enhancements: buildEnhancementPayload(),
          });
        } else if (chartId === "grouped-boxplot") {
          response = await getGroupedBoxplot({
            baseUrl,
            targetVariable,
            compareVariable: compareVariableCandidate,
            enhancements: buildEnhancementPayload(),
          });
        } else {
          response = await getTimeLine({
            baseUrl,
            targetVariable,
            compareVariable: compareVariableCandidate,
            enhancements: buildEnhancementPayload(),
          });
        }

        if (!response.ok) {
          setRelationshipLoading(false);
          setRelationshipError(response.error || "Relationship analysis request failed.");
          return;
        }

        const resolvedImageUrl = resolveApiAssetUrl(
          response.data?.image,
          baseUrl,
        );

        if (!resolvedImageUrl) {
          setRelationshipLoading(false);
          setRelationshipError("Relationship analysis response did not include an image path.");
          return;
        }

        const chartMeta = chartCatalog.find((chart) => chart.id === chartId);
        runEntries.push({
          chartId,
          chartTitle: chartMeta?.title || chartId,
          targetVariable,
          compareVariable: compareVariableCandidate,
          enhancementMetadata: response.data?.chart_metadata?.enhancements || buildEnhancementPayload(),
          image: `${resolvedImageUrl}${resolvedImageUrl.includes("?") ? "&" : "?"}t=${Date.now()}`,
          generatedAt: new Date().toISOString(),
        });
      }
    }

    setRelationshipRuns(runEntries);
    setRelationshipLoading(false);
  };


const getChartExplainability = (chartId) => {
  switch (chartId) {
    case "histogram":
      return {
        what: "This chart shows how many records fall into each value range.",
        time: "Time is not used. Values are compared across the full dataset.",
        comparison: "It compares frequencies of value ranges.",
        where: "The chart image above is the result.",
      };

    case "bar-category":
      return {
        what: "This chart shows how records are distributed by group.",
        time: "Time is not used. Groups are compared across the full dataset.",
        comparison: "It compares record counts between groups.",
        where: "The chart image above is the result.",
      };

    case "boxplot":
      return {
        what: "This chart summarizes typical values and possible outliers.",
        time: "Time is not used. Values are compared across the full dataset.",
        comparison: "It compares median, spread, and outliers in the value field.",
        where: "The chart image above is the result.",
      };

    case "scatter":
      return {
        what: "This chart shows how one value field moves relative to another.",
        time: "Time is not used. Pairs of values are compared across the full dataset.",
        comparison: "It compares value-to-value pairs to show correlation patterns.",
        where: "The chart image above is the result.",
      };

    case "grouped-comparison":
      return {
        what: "This chart shows average values for each group.",
        time: "Time is not used. Groups are compared across the full dataset.",
        comparison: "It compares group-level average values.",
        where: "The chart image above is the result.",
      };

    case "grouped-boxplot":
      return {
        what: "This chart compares quartiles, spread, and outliers across groups.",
        time: "Time is not used. Group distributions are compared across the full dataset.",
        comparison: "It compares per-group distribution shapes for the selected metric.",
        where: "The chart image above is the result.",
      };

    case "time-line":
      return {
        what: "This chart shows the trend of the selected metric over time.",
        time: "Time is central. Values are aggregated across date intervals.",
        comparison: "It compares how the metric changes across time points.",
        where: "The chart image above is the result.",
      };

    default:
      return {
        what: "No explanation is available for this chart yet.",
        time: "",
        comparison: "",
        where: "",
      };
  }
};

const getChartContextEntries = (chartId, targetVariable, compareVariable) => {
  switch (chartId) {
    case "histogram":
    case "boxplot":
      return [["target_variable", targetVariable]];
    case "bar-category":
      return [["compare_variable", compareVariable]];
    case "scatter":
    case "grouped-comparison":
    case "grouped-boxplot":
    case "time-line":
      return [
        ["target_variable", targetVariable],
        ["compare_variable", compareVariable],
      ];
    default:
      return [];
  }
};

const getRangeFromEnhancement = (minText, maxText, fallback) => {
  const min = Number(minText);
  const max = Number(maxText);
  if (Number.isFinite(min) && Number.isFinite(max) && min < max) {
    return { min, max };
  }
  return fallback;
};

const supportsDragZoom = ["histogram", "boxplot", "scatter"].includes(activeChart);

const getEffectiveAxisRange = () => {
  const xFallback = axisContext.x ? { min: axisContext.x.min, max: axisContext.x.max } : null;
  const yFallback = axisContext.y ? { min: axisContext.y.min, max: axisContext.y.max } : null;

  return {
    x: xFallback
      ? getRangeFromEnhancement(chartEnhancements.xMin, chartEnhancements.xMax, xFallback)
      : null,
    y: yFallback
      ? getRangeFromEnhancement(chartEnhancements.yMin, chartEnhancements.yMax, yFallback)
      : null,
  };
};

const handleChartMouseDown = (event) => {
  if (!supportsDragZoom || !chartContainerRef.current) {
    return;
  }

  const rect = chartContainerRef.current.getBoundingClientRect();
  dragStartRef.current = {
    x: Math.max(0, Math.min(rect.width, event.clientX - rect.left)),
    y: Math.max(0, Math.min(rect.height, event.clientY - rect.top)),
    width: rect.width,
    height: rect.height,
  };
  setDragSelection({ left: dragStartRef.current.x, top: dragStartRef.current.y, width: 0, height: 0 });
};

const handleChartMouseMove = (event) => {
  if (!dragStartRef.current || !chartContainerRef.current) {
    return;
  }

  const rect = chartContainerRef.current.getBoundingClientRect();
  const currentX = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
  const currentY = Math.max(0, Math.min(rect.height, event.clientY - rect.top));
  const left = Math.min(dragStartRef.current.x, currentX);
  const top = Math.min(dragStartRef.current.y, currentY);
  const width = Math.abs(currentX - dragStartRef.current.x);
  const height = Math.abs(currentY - dragStartRef.current.y);
  setDragSelection({ left, top, width, height });
};

const handleChartMouseUp = async () => {
  if (!dragStartRef.current || !dragSelection) {
    dragStartRef.current = null;
    setDragSelection(null);
    return;
  }

  const selectionTooSmall = dragSelection.width < 8 || dragSelection.height < 8;
  const axisRange = getEffectiveAxisRange();
  dragStartRef.current = null;

  if (selectionTooSmall) {
    setDragSelection(null);
    return;
  }

  const start = dragSelection;
  const width = chartContainerRef.current?.clientWidth || 1;
  const height = chartContainerRef.current?.clientHeight || 1;

  const x1Pct = start.left / width;
  const x2Pct = (start.left + start.width) / width;
  const yTopPct = start.top / height;
  const yBottomPct = (start.top + start.height) / height;

  const nextEnhancements = { ...chartEnhancements };
  if (axisRange.x) {
    const newXMin = axisRange.x.min + (axisRange.x.max - axisRange.x.min) * x1Pct;
    const newXMax = axisRange.x.min + (axisRange.x.max - axisRange.x.min) * x2Pct;
    nextEnhancements.xMin = String(Number(newXMin.toFixed(4)));
    nextEnhancements.xMax = String(Number(newXMax.toFixed(4)));
  }
  if (axisRange.y) {
    const newYMax = axisRange.y.max - (axisRange.y.max - axisRange.y.min) * yTopPct;
    const newYMin = axisRange.y.max - (axisRange.y.max - axisRange.y.min) * yBottomPct;
    nextEnhancements.yMin = String(Number(newYMin.toFixed(4)));
    nextEnhancements.yMax = String(Number(newYMax.toFixed(4)));
  }

  setChartEnhancements(nextEnhancements);
  setDragSelection(null);
  await handleChartSelect(activeChart, nextEnhancements);
};






  return (
    <div>
      <h2>Charts</h2>

      <h3>Dataset Overview</h3>
      {!activeDatasetId ? (
        <p style={{ opacity: 0.7 }}>
          No dataset loaded — select and run a dataset to view charts.
        </p>
      ) : overviewLoading ? (
        <p>Loading dataset overview...</p>
      ) : overviewError ? (
        <p style={{ color: "#c00" }}>{overviewError}</p>
      ) : overview ? (
        <>
          {activeDatasetId && overview.source && overview.source !== activeDatasetId && (
            <p style={{ color: "#b8860b", fontWeight: 600, marginBottom: "0.5rem" }}>
              Note: charts show data from &ldquo;{overview.source}&rdquo;. Run the selected dataset to update.
            </p>
          )}
          <button
            type="button"
            onClick={handleExportSummary}
            style={{
              marginTop: "0.5rem",
              marginBottom: "0.5rem",
              padding: "0.45rem 0.8rem",
              borderRadius: "6px",
              border: "1px solid #ccc",
              cursor: "pointer",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            Export Summary (JSON)
          </button>

          <div className="summary-full">
            <div style={summaryCardStyle}>
              <p style={summaryCardTitleStyle}>Dataset Summary</p>
              <p style={summaryMetricStyle}>Source: {overview.source}</p>
              {overview.source_metadata?.source_location ? (
                <p style={summaryMetricStyle}>Source Location: {overview.source_metadata.source_location}</p>
              ) : null}
              {overview.source_metadata?.source_url ? (
                <p style={summaryMetricStyle}>Source URL: {overview.source_metadata.source_url}</p>
              ) : null}
              <hr style={summaryDividerStyle} />
              <p style={summaryMetricStyle}>Rows: {overview.rows}</p>
              {overview.shape ? (
                <p style={summaryMetricStyle}>Columns: {overview.shape.columns}</p>
              ) : null}
              {overview.variables != null && <p style={summaryMetricStyle}>Analysis Variables: {overview.variables}</p>}
              {overview.fields && <p style={summaryMetricStyle}>Analysis Fields: {overview.fields.join(", ")}</p>}
              {overview.shape ? (
                <p style={summaryMetricStyle}>Shape: {overview.shape.rows} x {overview.shape.columns}</p>
              ) : null}
              <hr style={summaryDividerStyle} />
              {overview.min != null && <p style={summaryMetricStyle}>Min: {overview.min}</p>}
              {overview.max != null && <p style={summaryMetricStyle}>Max: {overview.max}</p>}
              {overview.mean != null && <p style={summaryMetricStyle}>Mean: {overview.mean}</p>}
              {overview.count != null && <p style={summaryMetricStyle}>Count: {overview.count}</p>}
              <hr style={summaryDividerStyle} />
              {missingValueEntries.length ? (
                <div>
                  <p style={{ ...summaryMetricStyle, fontWeight: 600 }}>Missing Values:</p>
                  {missingValueEntries.map(([field, missing]) => (
                    <p key={`missing-${field}`} style={summaryMetricStyle}>
                      {field}: {missing}
                    </p>
                  ))}
                </div>
              ) : (
                <p style={summaryMetricStyle}>Missing Values: None detected</p>
              )}
            </div>
          </div>

          <h3>Analysis Variables</h3>
          <div className="summary-grid">
            <div className="summary-variable-column">
              <label
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                  fontWeight: 600,
                  alignItems: "center",
                  marginBottom: "1rem",
                }}
              >
                <span>Target Variable</span>
                <select
                  value={targetVariable}
                  onChange={(event) => handleTargetChange(event.target.value)}
                  disabled={!activeDatasetId || overviewLoading}
                  style={{ minWidth: "12rem", padding: "0.45rem" }}
                >
                  {targetOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <div className="summary-variable-cards">
                {renderSummaryCardsForVariable(normalizeFieldName(targetVariable))}
              </div>
            </div>

            <div className="summary-variable-column">
              <label
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                  fontWeight: 600,
                  alignItems: "center",
                  marginBottom: "1rem",
                }}
              >
                <span>Compare Variable</span>
                <select
                  multiple
                  aria-label="Compare Variable"
                  value={compareVariables}
                  onChange={(event) => {
                    const selected = Array.from(event.target.selectedOptions || []).map((o) => o.value);
                    const result = selected.length > 0 ? selected : [event.target.value].filter(Boolean);
                    if (result.length > 0) handleCompareChange(result);
                  }}
                  disabled={!activeDatasetId || overviewLoading || compareOptions.length === 0}
                  style={{ minWidth: "12rem", padding: "0.45rem", minHeight: "6rem" }}
                >
                  {compareOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <span style={{ fontSize: "0.78rem", opacity: 0.65 }}>Hold Ctrl / Cmd to select multiple</span>
              </label>
              <div className="summary-variable-cards">
                {compareVariables.map((cv) => (
                  <React.Fragment key={`summary-${normalizeFieldName(cv)}`}>
                    {renderSummaryCardsForVariable(normalizeFieldName(cv))}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : null}

      <p style={{ marginBottom: "1rem", opacity: 0.85 }}>
        Each chart includes guidance on what it shows, when to use it, and whether it is recommended for the current dataset.
      </p>

      <h3>Advanced Graph Enhancement Controls</h3>
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: "10px",
          padding: "0.9rem",
          marginBottom: "1rem",
          background: "#fafafa",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.65rem",
        }}
      >
        <div style={{ gridColumn: "1 / -1", fontWeight: 700, marginBottom: "0.15rem" }}>Visual Styling</div>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Title
          <input
            aria-label="Chart Title"
            value={chartEnhancements.title}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, title: event.target.value }))}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Subtitle
          <input
            aria-label="Chart Subtitle"
            value={chartEnhancements.subtitle}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, subtitle: event.target.value }))}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          X Axis Label
          <input
            aria-label="X Axis Label"
            value={chartEnhancements.xLabel}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, xLabel: event.target.value }))}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Y Axis Label
          <input
            aria-label="Y Axis Label"
            value={chartEnhancements.yLabel}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, yLabel: event.target.value }))}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Color Theme
          <select
            aria-label="Color Theme"
            value={chartEnhancements.color}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, color: event.target.value }))}
          >
            {CHART_COLOR_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Annotation
          <input
            aria-label="Annotation"
            value={chartEnhancements.annotation}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, annotation: event.target.value }))}
          />
        </label>
        <div style={{ gridColumn: "1 / -1", fontWeight: 700, marginTop: "0.15rem", marginBottom: "0.15rem" }}>Scaling</div>
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <input
            type="checkbox"
            checked={chartEnhancements.showLegend}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, showLegend: event.target.checked }))}
          />
          Show Legend
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <input
            type="checkbox"
            checked={chartEnhancements.showGrid}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, showGrid: event.target.checked }))}
          />
          Show Gridlines
        </label>
        <div style={{ gridColumn: "1 / -1", fontWeight: 700, marginTop: "0.15rem", marginBottom: "0.15rem" }}>Axis Control</div>
        {axisContext.x ? (
          <div style={{ gridColumn: "1 / -1", padding: "0.5rem", border: "1px solid #e5e7eb", borderRadius: "8px", background: "#fff" }}>
            <p style={{ marginBottom: "0.45rem", fontWeight: 600 }}>
              X-axis range ({axisContext.x.label}): {Number(axisSlider.xMin).toFixed(2)} - {Number(axisSlider.xMax).toFixed(2)}
            </p>
            <input
              aria-label="X-axis Min Slider"
              type="range"
              min={axisContext.x.min}
              max={axisContext.x.max}
              step={(axisContext.x.max - axisContext.x.min) / 200 || 1}
              value={axisSlider.xMin}
              onChange={(event) => {
                const value = Number(event.target.value);
                setAxisSlider((prev) => ({
                  ...prev,
                  xMin: Math.min(value, prev.xMax - 0.0001),
                  xTouched: true,
                }));
              }}
              style={{ width: "100%" }}
            />
            <input
              aria-label="X-axis Max Slider"
              type="range"
              min={axisContext.x.min}
              max={axisContext.x.max}
              step={(axisContext.x.max - axisContext.x.min) / 200 || 1}
              value={axisSlider.xMax}
              onChange={(event) => {
                const value = Number(event.target.value);
                setAxisSlider((prev) => ({
                  ...prev,
                  xMax: Math.max(value, prev.xMin + 0.0001),
                  xTouched: true,
                }));
              }}
              style={{ width: "100%" }}
            />
            <button
              type="button"
              onClick={() => applyAxisFromSlider("x")}
              style={{ marginTop: "0.45rem", padding: "0.35rem 0.7rem", borderRadius: "6px", border: "1px solid #ccc", cursor: "pointer" }}
            >
              Apply X-axis Range
            </button>
          </div>
        ) : null}
        {axisContext.y ? (
          <div style={{ gridColumn: "1 / -1", padding: "0.5rem", border: "1px solid #e5e7eb", borderRadius: "8px", background: "#fff" }}>
            <p style={{ marginBottom: "0.45rem", fontWeight: 600 }}>
              Y-axis range ({axisContext.y.label}): {Number(axisSlider.yMin).toFixed(2)} - {Number(axisSlider.yMax).toFixed(2)}
            </p>
            <input
              aria-label="Y-axis Min Slider"
              type="range"
              min={axisContext.y.min}
              max={axisContext.y.max}
              step={(axisContext.y.max - axisContext.y.min) / 200 || 1}
              value={axisSlider.yMin}
              onChange={(event) => {
                const value = Number(event.target.value);
                setAxisSlider((prev) => ({
                  ...prev,
                  yMin: Math.min(value, prev.yMax - 0.0001),
                  yTouched: true,
                }));
              }}
              style={{ width: "100%" }}
            />
            <input
              aria-label="Y-axis Max Slider"
              type="range"
              min={axisContext.y.min}
              max={axisContext.y.max}
              step={(axisContext.y.max - axisContext.y.min) / 200 || 1}
              value={axisSlider.yMax}
              onChange={(event) => {
                const value = Number(event.target.value);
                setAxisSlider((prev) => ({
                  ...prev,
                  yMax: Math.max(value, prev.yMin + 0.0001),
                  yTouched: true,
                }));
              }}
              style={{ width: "100%" }}
            />
            <button
              type="button"
              onClick={() => applyAxisFromSlider("y")}
              style={{ marginTop: "0.45rem", padding: "0.35rem 0.7rem", borderRadius: "6px", border: "1px solid #ccc", cursor: "pointer" }}
            >
              Apply Y-axis Range
            </button>
          </div>
        ) : null}
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <input
            type="checkbox"
            checked={chartEnhancements.logScaleX}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, logScaleX: event.target.checked }))}
          />
          Use Log Scale (X-axis)
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <input
            type="checkbox"
            checked={chartEnhancements.logScaleY}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, logScaleY: event.target.checked }))}
          />
          Use Log Scale (Y-axis)
        </label>
        <div style={{ gridColumn: "1 / -1", fontWeight: 700, marginTop: "0.15rem", marginBottom: "0.15rem" }}>Data Control</div>
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Clip extreme values
          <select
            aria-label="Clip extreme values"
            value={chartEnhancements.clipMode}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, clipMode: event.target.value }))}
          >
            <option value="none">None</option>
            <option value="percentile">Percentile-based</option>
            <option value="manual">Manual threshold</option>
          </select>
        </label>
        {chartEnhancements.clipMode === "percentile" ? (
          <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
            Clip Percentile
            <select
              aria-label="Clip Percentile"
              value={chartEnhancements.clipPercentile}
              onChange={(event) => setChartEnhancements((prev) => ({ ...prev, clipPercentile: event.target.value }))}
            >
              <option value="95">95th percentile</option>
              <option value="99">99th percentile</option>
            </select>
          </label>
        ) : null}
        {chartEnhancements.clipMode === "manual" ? (
          <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
            Manual Clip Max
            <input
              aria-label="Manual Clip Max"
              type="number"
              value={chartEnhancements.clipMax}
              onChange={(event) => setChartEnhancements((prev) => ({ ...prev, clipMax: event.target.value }))}
              placeholder="e.g. 5000"
            />
          </label>
        ) : null}
        <label style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          Zoom Preset
          <select
            aria-label="Zoom Preset"
            value={chartEnhancements.zoomPreset}
            onChange={(event) => setChartEnhancements((prev) => ({ ...prev, zoomPreset: event.target.value }))}
          >
            <option value="full_range">Full Range</option>
            <option value="focus_low_range">Focus Low Range</option>
            <option value="iqr">Interquartile Range (IQR)</option>
          </select>
        </label>
        <div style={{ gridColumn: "1 / -1", fontWeight: 700, marginTop: "0.15rem", marginBottom: "0.15rem" }}>Interaction</div>
        <button
          type="button"
          onClick={handleResetZoom}
          disabled={!activeChart}
          style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid #ccc", cursor: "pointer" }}
        >
          Reset Zoom
        </button>
        <button
          type="button"
          onClick={handleResetChart}
          disabled={!activeChart}
          style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid #ccc", cursor: "pointer" }}
        >
          Reset Chart
        </button>
      </div>

      <h3>Relationship Analysis Mode</h3>
      <p style={{ marginBottom: "0.5rem", opacity: 0.85 }}>
        Run scatter, grouped box plot, and time-based line charts in sequence for each selected compare variable.
      </p>
      <button
        type="button"
        onClick={handleRunRelationshipAnalysis}
        disabled={!activeDatasetId || overviewLoading || relationshipLoading || compareVariables.length === 0}
        style={{
          marginBottom: "0.75rem",
          padding: "0.45rem 0.85rem",
          borderRadius: "6px",
          border: "1px solid #ccc",
          cursor: "pointer",
          fontWeight: 600,
        }}
      >
        {relationshipLoading ? "Running Relationship Analysis..." : "Run Guided Relationship Analysis"}
      </button>
      {relationshipError ? <p style={{ color: "#c00" }}>{relationshipError}</p> : null}
      {relationshipRuns.length > 0 ? (
        <div style={{ marginBottom: "1rem" }}>
          <p style={{ fontWeight: 600, marginBottom: "0.5rem" }}>
            Relationship charts generated: {relationshipRuns.length}
          </p>
          {relationshipRuns.map((entry, index) => (
            <div
              key={`${entry.chartId}-${entry.compareVariable}-${index}`}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "0.75rem",
                marginBottom: "0.75rem",
                background: "#fafafa",
              }}
            >
              <p style={{ margin: 0, fontWeight: 700 }}>{entry.chartTitle}</p>
              <p style={{ margin: "0.35rem 0" }}>
                <strong>target variable:</strong> {entry.targetVariable} | <strong>compare variable:</strong> {entry.compareVariable}
              </p>
              <p style={{ margin: "0.35rem 0" }}>
                <strong>Enhancements Applied:</strong>
              </p>
              <ul style={{ marginTop: 0, marginBottom: "0.5rem", textAlign: "left" }}>
                {toHumanEnhancements(entry.enhancementMetadata).map(([label, value]) => (
                  <li key={`${entry.chartId}-${entry.compareVariable}-${label}`}>
                    {label}: {value}
                  </li>
                ))}
              </ul>
              <div className="chart-container" style={{ marginTop: "0.4rem" }}>
                <img
                  src={entry.image}
                  alt={`${entry.chartTitle} relationship visualization`}
                  style={{ width: "100%", height: "100%", objectFit: "contain", border: "1px solid #ccc", borderRadius: "8px" }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : null}

      <div style={{ marginBottom: "1.25rem" }}>
        {isDev && (
          <>
            <div style={{ fontWeight: 600, marginBottom: "0.75rem", fontSize: "0.9rem", textAlign: "center" }}>Dev — API Target:</div>
            <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <button
                type="button"
                onClick={() => setTarget("local")}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  fontWeight: target === "local" ? 700 : 400,
                  background: target === "local" ? "#e8f0fe" : "transparent",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Local
              </button>
              <button
                type="button"
                onClick={() => setTarget("cloud")}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  fontWeight: target === "cloud" ? 700 : 400,
                  background: target === "cloud" ? "#e8f0fe" : "transparent",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Cloud
              </button>
            </div>
            <p style={{ marginTop: "0.25rem", opacity: 0.85, fontSize: "0.9rem" }}>
              Target: <strong>{target === "local" ? "Local API (this computer)" : "Deployed API (cloud)"}</strong>
            </p>
          </>
        )}
      </div>

      <h3>Available Charts</h3>
      {chartCatalog.map((chart) => (
        <div key={chart.id} style={{ marginBottom: "1rem" }}>
          <label
            style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 600 }}
          >
            <input
              type="radio"
              name="chart-selection"
              checked={activeChart === chart.id}
              onChange={() => handleChartSelect(chart.id)}
            />
            {chart.title}
          </label>

          <p><strong>Why this chart:</strong> {chart.purpose}</p>
          <p><em>{chart.whenToUse}</em></p>
          <p>
            Recommended for current dataset:{" "}
            <strong>{chart.recommended ? "Yes" : "No"}</strong>
          </p>
          <p style={{ opacity: 0.8 }}>{chart.recommendationReason}</p>

          {loading && activeChart === chart.id ? (
            <p style={{ marginTop: "0.75rem" }}>Loading chart...</p>
          ) : null}

         {activeChart === chart.id && chartImages[chart.id] ? (
  <div style={{ marginTop: "0.75rem" }}>
    <div
      ref={chartContainerRef}
      className="chart-container"
      onMouseDown={handleChartMouseDown}
      onMouseMove={handleChartMouseMove}
      onMouseUp={handleChartMouseUp}
      onMouseLeave={handleChartMouseUp}
      style={{ cursor: supportsDragZoom ? "crosshair" : "default" }}
    >
      <img
        src={chartImages[chart.id]}
        alt={`${chart.title} visualization`}
        style={{ width: "100%", height: "100%", objectFit: "contain", border: "1px solid #ccc", borderRadius: "8px" }}
      />
      {dragSelection ? (
        <div
          style={{
            position: "absolute",
            left: `${dragSelection.left}px`,
            top: `${dragSelection.top}px`,
            width: `${dragSelection.width}px`,
            height: `${dragSelection.height}px`,
            border: "2px dashed #2563eb",
            background: "rgba(37, 99, 235, 0.15)",
            pointerEvents: "none",
          }}
        />
      ) : null}
    </div>

    {getChartContextEntries(chart.id, targetVariable, compareVariable).length > 0 ? (
      <div
        style={{
          marginTop: "0.75rem",
          padding: "0.75rem",
          border: "1px solid #ddd",
          borderRadius: "8px",
          background: "#fafafa",
        }}
      >
        <strong>Fields used</strong>
        {getChartContextEntries(chart.id, targetVariable, compareVariable).map(([role, field]) => (
          <p key={`${chart.id}-${role}`} style={{ marginTop: "0.35rem" }}>
            <strong>{role.replace(/_/g, " ")}:</strong> {field}
          </p>
        ))}
      </div>
    ) : null}

    <div
      style={{
        marginTop: "0.75rem",
        padding: "0.75rem",
        border: "1px solid #ddd",
        borderRadius: "8px",
        background: "#fafafa",
      }}
    >
      <strong>How to read this chart</strong>
              {chartMetadata[chart.id]?.enhancements ? (
                <div style={{ marginTop: "0.5rem", marginBottom: "0.35rem", textAlign: "left" }}>
                  <strong>Enhancements Applied:</strong>
                  <ul style={{ marginTop: "0.3rem", marginBottom: "0.4rem" }}>
                    {toHumanEnhancements(chartMetadata[chart.id].enhancements).map(([label, value]) => (
                      <li key={`${chart.id}-${label}`}>{label}: {value}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
      <p style={{ marginTop: "0.5rem", marginBottom: "0.35rem" }}>
        <strong>What this output shows:</strong> {getChartExplainability(chart.id).what}
      </p>
      <p style={{ marginTop: 0, marginBottom: "0.35rem" }}>
        <strong>Time usage:</strong> {getChartExplainability(chart.id).time}
      </p>
      <p style={{ marginTop: 0, marginBottom: "0.35rem" }}>
        <strong>Comparison:</strong> {getChartExplainability(chart.id).comparison}
      </p>
      <p style={{ marginTop: 0 }}>
        <strong>Where to find it:</strong> {getChartExplainability(chart.id).where}
      </p>
    </div>
  </div>
) : null}
        </div>
      ))}

      {error ? (
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            border: "1px solid #d88",
            borderRadius: "10px",
          }}
        >
          <strong>Error</strong>
          <p style={{ marginTop: "0.5rem" }}>{error}</p>
        </div>
      ) : null}
    </div>
  );
}

function parseNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getNumericStats(overview, label) {
  const normalized = normalizeFieldName(label);
  const match = (overview?.numeric_summary || []).find(
    (item) => normalizeFieldName(item.field) === normalized,
  );
  if (!match) {
    return null;
  }

  const min = parseNumber(match.min);
  const max = parseNumber(match.max);
  if (min == null || max == null || min === max) {
    return null;
  }

  return { min, max, label };
}

function getAxisContext(activeChart, overview, targetVariable, compareVariable) {
  const targetStats = getNumericStats(overview, targetVariable);
  const compareStats = getNumericStats(overview, compareVariable);

  switch (activeChart) {
    case "histogram":
      return { x: targetStats, y: null };
    case "boxplot":
      return { x: null, y: targetStats };
    case "scatter":
      return { x: targetStats, y: compareStats };
    default:
      return { x: null, y: null };
  }
}

function toHumanEnhancements(enhancements = {}) {
  const lines = [];
  const title = enhancements.title || enhancements.chart_title || null;
  const xLabel = enhancements.x_label || enhancements.xLabel || null;
  const yLabel = enhancements.y_label || enhancements.yLabel || null;
  const showGrid = enhancements.show_grid ?? enhancements.showGrid;
  const showLegend = enhancements.show_legend ?? enhancements.showLegend;
  const logScaleX = enhancements.log_scale_x ?? enhancements.logScaleX;
  const logScaleY = enhancements.log_scale_y ?? enhancements.logScaleY;
  const clipMode = enhancements.clip_mode ?? enhancements.clipMode;
  const zoomPreset = enhancements.zoom_preset ?? enhancements.zoomPreset;

  lines.push(["Title", title || "Not set"]);
  lines.push(["X-axis Label", xLabel || "Not set"]);
  lines.push(["Y-axis Label", yLabel || "Not set"]);
  lines.push(["Gridlines", showGrid ? "Enabled" : "Disabled"]);
  lines.push(["Legend", showLegend ? "Enabled" : "Disabled"]);
  lines.push(["Log Scale (X)", logScaleX ? "On" : "Off"]);
  lines.push(["Log Scale (Y)", logScaleY ? "On" : "Off"]);
  lines.push(["Clipping", clipMode || "None"]);
  lines.push(["Zoom", (zoomPreset || "full_range").replace(/_/g, " ")]);

  return lines;
}