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
    recommended: false,
    recommendationReason:
      "Not currently recommended because the dataset only contains one numeric variable.",
    endpoint: "/charts/scatter",
  },
  {
    id: "line-trend",
    title: "Line / Trend Chart",
    purpose: "Shows change over time or ordered progression.",
    whenToUse: "Use when the dataset includes a time field or meaningful sequence.",
    recommended: false,
    recommendationReason:
      "Not currently recommended because the dataset does not include a time or sequence field.",
    endpoint: "/charts/line-trend",
  },
];