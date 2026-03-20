const SAMPLE_DATA = [
  { entity_id: "A", metric_value: 10, category: "X" },
  { entity_id: "B", metric_value: 20, category: "Y" },
  { entity_id: "C", metric_value: 15, category: "X" },
  { entity_id: "D", metric_value: 30, category: "Z" },
];

export default function ChartsTab() {

    const data = SAMPLE_DATA;
    const values = data.map((d) => d.metric_value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const mean = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);



    return (
        <div>
            <h2>Charts</h2>
            <h3>Dataset Overview</h3>
            <p>Source: Sample Dataset</p>
            <p>Rows: {data.length}</p>
            <p>Variables: {Object.keys(data[0]).length}</p>
            <p>Fields: {Object.keys(data[0]).join(", ")}</p>
            {/* overview */}
            {/* summary stats */}
            {/* cleaning results */}
            {/* controls */}
            {/* charts */}
            {/* observations */}
        </div>
    );
}