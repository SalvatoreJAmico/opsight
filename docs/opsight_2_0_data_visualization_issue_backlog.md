# Opsight 2.0 Data Visualization Issue Backlog

This backlog maps the CSC 562 data visualization assignment requirements to concrete Opsight UI and export features.

## Suggested Copilot batch prompt

Use this prompt in GitHub Copilot Chat inside the Opsight repository:

```text
Create GitHub issues for the Opsight 2.0 data visualization backlog described in docs/opsight_2_0_data_visualization_issue_backlog.md.

Rules:
- Create one issue per section under "Issues"
- Preserve the exact issue title
- Use the Description and Acceptance Criteria exactly as written unless small formatting cleanup is needed
- Add label: enhancement
- Add label: data-visualization
- Add label: opsight-2.0
- Order the issues by Priority, highest first
- Do not merge issues together
- After creating them, return the full issue list with issue numbers
```

---

## Issues

### 1. Expose Dataset Source Metadata
**Priority:** P0

**Description:**
Display explicit dataset source information after dataset load, including the external source name, the source location used by Opsight, and a clickable source URL when available. Surface this metadata in both the Dataset and Charts views so the user can tie every chart back to the source dataset.

**Acceptance Criteria:**
- Source name is visible after dataset load
- Clickable external URL is visible when available
- Opsight source location is visible, such as predefined dataset or blob path
- Source metadata persists in session state
- Source metadata appears in exported summary/report evidence

---

### 2. Add Complete Dataset Summary View
**Priority:** P0

**Description:**
Provide a full summary view for numeric and categorical variables so Opsight can satisfy the assignment’s overall-summary requirement directly in the UI.

**Acceptance Criteria:**
- Numeric statistics are visible for selected dataset fields, including count, min, max, mean, median, and standard deviation
- Missing-value counts per column are visible
- Categorical frequency tables are visible for major categorical fields
- Dataset shape is visible as rows x columns
- Summary output can be exported for report evidence

---

### 3. Add Data Cleaning Before/After Audit View
**Priority:** P0

**Description:**
Show an explicit before/after cleaning audit generated from the Opsight validation and cleaning pipeline so users can prove what changed.

**Acceptance Criteria:**
- Before and after row counts are displayed
- Missing values by column are displayed before and after cleaning
- Duplicate counts are displayed before and after cleaning
- Invalid rows removed are displayed with reason counts
- Cleaning audit is exportable for report evidence

---

### 4. Add Guided Variable Selection
**Priority:** P0

**Description:**
Add a guided workflow that allows the user to choose one primary variable and one or more companion variables for chart generation and report alignment.

**Acceptance Criteria:**
- User can select a target or focus variable
- User can select one or more comparison variables
- Selection is saved in session state
- Selected variables are shown in chart generation context
- Selected variables appear in exported report evidence

---

### 5. Add Guided Relationship Analysis
**Priority:** P0

**Description:**
Create a dedicated relationship-analysis mode for comparing the selected focus variable against other variables using assignment-relevant charts.

**Acceptance Criteria:**
- User picks one main variable and multiple related variables
- Relationship charts can be generated in sequence
- Supported chart types include at least scatter plot, grouped box plot, and time-based line chart where applicable
- Each chart clearly shows the variables being compared
- Relationship chart list appears in exported report evidence

---

### 6. Add Advanced Graph Enhancement Controls
**Priority:** P1

**Description:**
Add controls for assignment-required chart enhancements so the user can visibly apply readability and storytelling improvements inside Opsight.

**Acceptance Criteria:**
- At least four enhancement options are available per chart
- Supported enhancements include title, subtitle, axis labels, legend, gridlines, color/styling, and annotations/text callouts
- Applied enhancements are visible on rendered charts
- Applied enhancements are recorded in chart metadata
- Enhancement metadata appears in exported report evidence

---

### 7. Track Two Distinct Distribution Graphs
**Priority:** P1

**Description:**
Track whether the user has generated at least two different distribution chart types for the selected variables so Opsight can support the assignment’s distribution requirement.

**Acceptance Criteria:**
- Opsight tracks generated distribution chart types by variable
- UI shows whether at least two distinct distribution chart types have been created
- Supported distribution charts include at least histogram, box plot, bar chart, or density-style equivalent
- Chosen chart types and variables are listed for report evidence export

---

### 8. Add Observations and Insights Capture Tab
**Priority:** P1

**Description:**
Provide a structured place for the user to record findings tied to specific charts and summarize final observations for the assignment.

**Acceptance Criteria:**
- Notes can be attached to individual charts
- A final observations area exists for overall findings
- Timestamp and variable references are stored with notes
- Notes are exportable for report evidence

---

### 9. Add Assignment Evidence Export
**Priority:** P1

**Description:**
Export assignment-ready evidence from the UI so the user can generate a single file or package containing the artifacts needed for the final report.

**Acceptance Criteria:**
- Export includes dataset source metadata
- Export includes dataset summary output
- Export includes data cleaning audit output
- Export includes selected variables
- Export includes generated chart list
- Export includes applied graph enhancements
- Export includes observations/insights notes
- Export supports at least one structured format such as Markdown or JSON, with PDF optional

---

### 10. Add Variable Definitions Panel
**Priority:** P2

**Description:**
Show a variable definitions panel that explains the meaning of fields used in analysis, with initial support focused on the Superstore dataset.

**Acceptance Criteria:**
- Variable table includes column name and data type
- Variable meaning/description is shown for supported fields
- Panel is accessible from the Dataset tab
- Superstore fields are supported initially

---

### 11. Add Assignment Progress Tracker
**Priority:** P2

**Description:**
Show assignment completion status across required deliverables so the user can see what Opsight already satisfies and what still needs action.

**Acceptance Criteria:**
- UI displays each assignment section with status such as complete, partial, or missing
- Status updates as the user generates summaries, audits, charts, and notes
- Progress view is accessible from the main UI
- Progress state persists during the session
