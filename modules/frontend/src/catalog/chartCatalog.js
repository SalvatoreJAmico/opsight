export const chartCatalog = [
  {
    id: "histogram",
    title: "Histogram",
    purpose: "Shows the distribution of a numeric variable.",
    whenToUse:
      "Use when you want to understand spread, frequency, and concentration of values.",
    recommended: true,
    recommendationReason:
      "Recommended because metric_value is numeric and suitable for distribution analysis.",
    endpoint: "/charts/histogram",
  },
  {
    id: "bar-category",
    title: "Category Bar Chart",
    purpose: "Compares counts across categories.",
    whenToUse: "Use when you want to compare frequency across discrete groups.",
    recommended: true,
    recommendationReason:
      "Recommended because category is available as a grouping field.",
    endpoint: "/charts/bar-category",
  },
  {
    id: "boxplot",
    title: "Box Plot",
    purpose: "Summarizes distribution and highlights potential outliers using quartiles.",
    whenToUse:
      "Use when you want a compact summary of spread and detection of unusual values.",
    recommended: true,
    recommendationReason:
      "Recommended because metric_value is numeric and suitable for distribution summary.",
    endpoint: "/charts/boxplot",
  },
  {
    id: "scatter",
    title: "Scatter Plot",
    purpose: "Shows the relationship between two numeric variables.",
    whenToUse:
      "Use when you want to inspect correlation or patterns between variables.",
    recommended: true,
    recommendationReason:
      "Recommended because metric_value and secondary_metric are both available for relationship analysis.",
    endpoint: "/charts/scatter",
  },
  {
    id: "grouped-comparison",
    title: "Grouped Comparison",
    purpose: "Compares average metric values across categories.",
    whenToUse: "Use when you want to compare aggregated values between groups.",
    recommended: true,
    recommendationReason:
      "Recommended because category and metric_value support grouped mean comparison.",
    endpoint: "/charts/grouped-comparison",
  },
  {
    id: "grouped-boxplot",
    title: "Grouped Box Plot",
    purpose: "Compares distribution spread for a metric across groups.",
    whenToUse: "Use when you want quartile and outlier comparisons by category.",
    recommended: true,
    recommendationReason:
      "Recommended because grouped box plots are useful for relationship analysis between a metric and group field.",
    endpoint: "/charts/grouped-boxplot",
  },
  {
    id: "time-line",
    title: "Time-based Line Chart",
    purpose: "Shows trend movement of a metric over time.",
    whenToUse: "Use when a valid date field is available and you need temporal pattern analysis.",
    recommended: true,
    recommendationReason:
      "Recommended when Order Date is available for assignment-aligned time-based relationship analysis.",
    endpoint: "/charts/time-line",
  },
];