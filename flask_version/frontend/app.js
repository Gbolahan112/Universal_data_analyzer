const fileInput = document.getElementById("fileInput");
const loadBtn = document.getElementById("loadBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const genderFilter = document.getElementById("genderFilter");
const ageFilter = document.getElementById("ageFilter");
const campaignFilter = document.getElementById("campaignFilter");
const statusBox = document.getElementById("status");
const dashboard = document.getElementById("dashboard");
const authStatus = document.getElementById("authStatus");
const reportsList = document.getElementById("reportsList");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const registerBtn = document.getElementById("registerBtn");
const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");

let selectedFile = null;
let latestReportId = null;

registerBtn.addEventListener("click", async () => {
  await authRequest("/register");
});

loginBtn.addEventListener("click", async () => {
  await authRequest("/login");
});

logoutBtn.addEventListener("click", async () => {
  const response = await fetch("/logout", { method: "POST" });
  const data = await response.json();
  authStatus.textContent = data.message;
  reportsList.innerHTML = "Log in to load saved reports.";
});

loadBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    statusBox.textContent = "Choose a dataset first.";
    return;
  }

  selectedFile = file;
  const formData = new FormData();
  formData.append("file", file);

  statusBox.textContent = "Loading dataset...";
  dashboard.innerHTML = "";

  try {
    const response = await fetch("/upload", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) {
      statusBox.textContent = `Error: ${data.error || "Load failed"}`;
      return;
    }

    populateFilter(genderFilter, data.filters.gender, "All Genders");
    populateFilter(ageFilter, data.filters.age, "All Ages");
    populateFilter(campaignFilter, data.filters.campaign_id, "All Campaigns");

    statusBox.textContent = `Dataset loaded. ${data.rows.toLocaleString()} rows found.`;
    renderInitialPreview(data);
  } catch (error) {
    statusBox.textContent = `Request failed: ${error.message}`;
  }
});

analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) {
    statusBox.textContent = "Load a dataset first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("gender", genderFilter.value);
  formData.append("age", ageFilter.value);
  formData.append("campaign_id", campaignFilter.value);

  statusBox.textContent = "Running analysis...";
  dashboard.innerHTML = "";

  try {
    const response = await fetch("/analyze", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) {
      statusBox.textContent = `Error: ${data.error || "Analysis failed"}`;
      return;
    }

    latestReportId = data.report_id;
    statusBox.textContent = "Analysis complete and report saved.";
    renderDashboard(data);
    loadReports();
  } catch (error) {
    statusBox.textContent = `Request failed: ${error.message}`;
  }
});

async function authRequest(url) {
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  if (!username || !password) {
    authStatus.textContent = "Enter username and password.";
    return;
  }

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();
  authStatus.textContent = data.message || data.error || "Done.";

  if (response.ok) {
    loadReports();
  }
}

async function loadReports() {
  const response = await fetch("/reports");
  if (!response.ok) {
    reportsList.innerHTML = "Log in to load saved reports.";
    return;
  }

  const reports = await response.json();
  if (!reports.length) {
    reportsList.innerHTML = "No saved reports yet.";
    return;
  }

  reportsList.innerHTML = reports.map(report => `
    <div class="report-item">
      <div>
        <strong>${report.report_name}</strong><br>
        <span class="muted">${report.created_at}</span>
      </div>
      <div>
        <button class="secondary" onclick="viewReport(${report.id})">Open</button>
        <button onclick="window.open('/reports/${report.id}/pdf', '_blank')">PDF</button>
        <button onclick="window.open('/reports/${report.id}/xlsx', '_blank')">Excel</button>
      </div>
    </div>
  `).join("");
}

async function viewReport(reportId) {
  const response = await fetch(`/reports/${reportId}`);
  const data = await response.json();

  if (!response.ok) {
    authStatus.textContent = data.error || "Could not load report.";
    return;
  }

  latestReportId = data.id;
  renderDashboard({ ...data.results, report_id: data.id });
}

window.viewReport = viewReport;

function populateFilter(selectElement, items, defaultLabel) {
  selectElement.innerHTML = `<option value="All">${defaultLabel}</option>`;
  items.forEach(item => {
    selectElement.innerHTML += `<option value="${item}">${item}</option>`;
  });
}

function renderInitialPreview(data) {
  dashboard.innerHTML = `
    <div class="card">
      <h2>Dataset Overview</h2>
      <p><span class="pill">Rows ${formatNumber(data.rows)}</span><span class="pill">Columns ${formatNumber(data.columns)}</span></p>
      <p class="muted">${data.column_names.join(", ")}</p>
    </div>
    <div class="table-box">
      <h2>Preview</h2>
      <div class="table-wrap">${buildTable(data.preview)}</div>
    </div>
  `;
}

function renderDashboard(data) {
  dashboard.innerHTML = `
    <div class="card">
      <div class="row" style="justify-content:space-between;">
        <h2>Analysis Dashboard</h2>
        ${data.report_id ? `
          <div class="row">
            <button onclick="window.open('/reports/${data.report_id}/pdf', '_blank')">Export PDF</button>
            <button class="secondary" onclick="window.open('/reports/${data.report_id}/xlsx', '_blank')">Export Excel</button>
          </div>
        ` : ""}
      </div>
      <div class="kpi-grid">
        ${kpiCard("Rows", formatNumber(data.rows))}
        ${kpiCard("Columns", formatNumber(data.columns))}
        ${kpiCard("Impressions", formatNumber(data.kpis.total_impressions))}
        ${kpiCard("Clicks", formatNumber(data.kpis.total_clicks))}
        ${kpiCard("Spend", formatCurrency(data.kpis.total_spent))}
        ${kpiCard("Approved Conversions", formatNumber(data.kpis.total_approved_conversions))}
        ${kpiCard("Avg CTR", formatDecimal(data.kpis.average_ctr))}
        ${kpiCard("Avg Conversion", formatDecimal(data.kpis.average_conversion_rate))}
        ${kpiCard("Avg ROI", formatDecimal(data.kpis.average_roi))}
      </div>
    </div>

    <div class="summary-grid">
      <div class="card">
        <h2>Insights</h2>
        <ul>${data.insights.map(item => `<li>${item}</li>`).join("")}</ul>
      </div>
      <div class="card">
        <h2>Highlights</h2>
        <p><strong>Best Age Group:</strong> ${data.best_age_group ? `${data.best_age_group.age} (${formatDecimal(data.best_age_group.average_roi)})` : "N/A"}</p>
        <p><strong>Best Gender:</strong> ${data.best_gender ? `${data.best_gender.gender} (${formatNumber(data.best_gender.approved_conversions)})` : "N/A"}</p>
        <p><strong>Saved Report ID:</strong> ${data.report_id || latestReportId || "N/A"}</p>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-box">
        <h2>Spend by Gender</h2>
        <div id="spendByGenderChart" style="height:360px;"></div>
      </div>
      <div class="chart-box">
        <h2>Clicks by Age</h2>
        <div id="clicksByAgeChart" style="height:360px;"></div>
      </div>
    </div>

    <div class="chart-box">
      <h2>Trend and Forecast</h2>
      <div id="trendChart" style="height:420px;"></div>
    </div>

    <div class="summary-grid">
      <div class="table-box">
        <h2>Top Ads by Clicks</h2>
        <div class="table-wrap">${buildTable(data.top_ads_by_clicks)}</div>
      </div>
      <div class="table-box">
        <h2>Top Ads by ROI</h2>
        <div class="table-wrap">${buildTable(data.top_ads_by_roi)}</div>
      </div>
    </div>

    <div class="table-box">
      <h2>Top Campaigns</h2>
      <div class="table-wrap">${buildTable(data.top_campaigns)}</div>
    </div>

    <div class="table-box">
      <h2>Anomaly Detection</h2>
      <div class="table-wrap">${buildTable(data.anomalies)}</div>
    </div>

    <div class="table-box">
      <h2>Forecasted Clicks</h2>
      <div class="table-wrap">${buildTable(data.predictions)}</div>
    </div>

    <div class="table-box">
      <h2>Filtered Preview</h2>
      <div class="table-wrap">${buildTable(data.preview)}</div>
    </div>
  `;

  renderSpendByGender(data.charts.spend_by_gender);
  renderClicksByAge(data.charts.clicks_by_age);
  renderTrendChart(data.charts.trend_data, data.predictions);
}

function renderSpendByGender(rows) {
  if (!rows || !rows.length) return;
  Plotly.newPlot("spendByGenderChart", [{
    x: rows.map(r => r.gender),
    y: rows.map(r => r.spent),
    type: "bar",
    marker: { color: "#0f62fe" }
  }], { margin: { t: 20 } }, { responsive: true });
}

function renderClicksByAge(rows) {
  if (!rows || !rows.length) return;
  Plotly.newPlot("clicksByAgeChart", [{
    x: rows.map(r => r.age),
    y: rows.map(r => r.clicks),
    type: "bar",
    marker: { color: "#14b8a6" }
  }], { margin: { t: 20 } }, { responsive: true });
}

function renderTrendChart(rows, predictions) {
  if ((!rows || !rows.length) && (!predictions || !predictions.length)) return;

  const traces = [];
  if (rows && rows.length) {
    traces.push({
      x: rows.map(r => r.date),
      y: rows.map(r => r.clicks || 0),
      mode: "lines+markers",
      name: "Actual Clicks",
      line: { color: "#0f62fe" }
    });
    traces.push({
      x: rows.map(r => r.date),
      y: rows.map(r => r.spent || 0),
      mode: "lines+markers",
      name: "Spend",
      yaxis: "y2",
      line: { color: "#f59e0b" }
    });
  }

  if (predictions && predictions.length) {
    traces.push({
      x: predictions.map(r => r.date),
      y: predictions.map(r => r.predicted_clicks),
      mode: "lines+markers",
      name: "Predicted Clicks",
      line: { dash: "dash", color: "#dc2626" }
    });
  }

  Plotly.newPlot("trendChart", traces, {
    margin: { t: 20 },
    yaxis: { title: "Clicks" },
    yaxis2: { title: "Spend", overlaying: "y", side: "right" }
  }, { responsive: true });
}

function kpiCard(label, value) {
  return `<div class="kpi"><h3>${label}</h3><p>${value}</p></div>`;
}

function buildTable(rows) {
  if (!rows || !rows.length) return "<p class='muted'>No data available.</p>";
  const headers = Object.keys(rows[0]);
  return `
    <table>
      <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
      <tbody>
        ${rows.map(row => `<tr>${headers.map(h => `<td>${formatCell(row[h])}</td>`).join("")}</tr>`).join("")}
      </tbody>
    </table>
  `;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

function formatCurrency(value) {
  return `$${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDecimal(value) {
  return Number(value || 0).toFixed(4);
}

function formatCell(value) {
  if (value === null || value === undefined || value === "") return "";
  if (!isNaN(value) && value !== "") return Number(value).toLocaleString();
  return value;
}

loadReports();

