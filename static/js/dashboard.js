/**
 * dashboard.js
 * GEOID — Global Economy Intelligence Dashboard
 *
 * Responsibilities:
 *   Boot splash animation
 *   UTC clock
 *   Refresh countdown arc
 *   API polling every 5 s (GET /api/economy)
 *   KPI summary strip
 *   Racing bar chart (animated reorder)
 *   GDP comparison bar chart
 *   Economic Power Index horizontal bar chart
 *   GDP Trajectory line chart (multi-year)
 *   AI Ensemble Forecast bar chart + error bars
 *   Confidence Interval horizontal stacked bar chart
 *   AI Prediction Matrix cards
 *   War Risk Matrix cards
 *   Sector Breakdown doughnut chart
 *   Intelligence news feed
 *   Ticker tape
 */
"use strict";

/* ─────────────────────────────── Constants ──────────────────────── */

const API_URL    = "/api/economy";
const REFRESH_MS = 5000;

/** Tab options for sector panel */
const SECTOR_TABS = ["US","CN","JP","DE","IN","GB","FR","BR","KR","RU","SA","AU"];

/** Per-country brand colours */
const CC = {
  US:"#3b82f6", CN:"#ef4444", JP:"#f59e0b", DE:"#22c55e", IN:"#f97316",
  GB:"#8b5cf6", FR:"#06b6d4", BR:"#84cc16", IT:"#ec4899", CA:"#38bdf8",
  KR:"#fbbf24", AU:"#34d399", MX:"#fb923c", ID:"#c084fc", TR:"#f43f5e",
  SA:"#fde047", AR:"#2dd4bf", ZA:"#a3e635", RU:"#ff7c5c",
};

/** Fallback country names (used before API response arrives) */
const CN_FB = {
  US:"United States", CN:"China",       JP:"Japan",        DE:"Germany",
  IN:"India",         GB:"United Kingdom", FR:"France",    BR:"Brazil",
  IT:"Italy",         CA:"Canada",      KR:"South Korea",  AU:"Australia",
  MX:"Mexico",        ID:"Indonesia",   TR:"Turkey",       SA:"Saudi Arabia",
  AR:"Argentina",     ZA:"South Africa",RU:"Russia",
};

/* ─────────────────────────────── State ──────────────────────────── */

const S = {
  data:         null,
  charts:       {},
  activeSector: "US",
  arcTimer:     null,
  arcStart:     null,
};

/* ─────────────────────────────── Boot ───────────────────────────── */

const BOOT = [
  { t: "Initialising GEOID v4.1.2 …",               d: 0,    c: "" },
  { t: "[ OK ] Kernel modules loaded",               d: 280,  c: "ok" },
  { t: "[ OK ] Network interface UP",                d: 520,  c: "ok" },
  { t: "[ OK ] Connecting to World Bank API …",      d: 760,  c: "ok" },
  { t: "[ !! ] API cache fallback engaged",           d: 1000, c: "warn" },
  { t: "[ OK ] Geopolitical risk engine ready",      d: 1240, c: "ok" },
  { t: "[ OK ] ML forecast model initialised",       d: 1460, c: "ok" },
  { t: "[ OK ] Chart renderers primed",              d: 1680, c: "ok" },
  { t: "[ OK ] Intelligence feed connected",         d: 1880, c: "ok" },
  { t: "SYSTEM READY — LIVE MONITORING ACTIVE",      d: 2120, c: "ok" },
];

function runBoot() {
  const logEl  = document.getElementById("boot-lines");
  const barEl  = document.getElementById("boot-bar");
  const statEl = document.getElementById("boot-status");
  const splash = document.getElementById("boot-overlay");
  const n      = BOOT.length;

  BOOT.forEach((step, i) => {
    setTimeout(() => {
      const el       = document.createElement("div");
      el.className   = "splash-log-line" + (step.c ? " " + step.c : "");
      el.textContent = "> " + step.t;
      logEl.appendChild(el);
      barEl.style.width = ((i + 1) / n * 100) + "%";
      statEl.textContent = step.t;
    }, step.d);
  });

  setTimeout(() => {
    splash.classList.add("fade-out");
    setTimeout(() => { splash.style.display = "none"; }, 1000);
  }, BOOT[n - 1].d + 500);
}

/* ─────────────────────────────── Clock ──────────────────────────── */

function startClock() {
  const el = document.getElementById("clock-utc");
  const tick = () => {
    const d = new Date();
    el.textContent = [d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds()]
      .map(n => String(n).padStart(2, "0")).join(":");
  };
  tick();
  setInterval(tick, 1000);
}

/* ─────────────────────────────── Refresh arc ────────────────────── */

const ARC_CIRC = 75.4;   // 2π × 12

function startArc() {
  S.arcStart = Date.now();
  if (S.arcTimer) clearInterval(S.arcTimer);
  S.arcTimer = setInterval(() => {
    const arc  = document.getElementById("arc-progress");
    const cntd = document.getElementById("refresh-countdown");
    const pct  = Math.min(1, (Date.now() - S.arcStart) / REFRESH_MS);
    arc.style.strokeDashoffset = ARC_CIRC * (1 - pct);
    cntd.textContent = Math.max(0, Math.ceil((REFRESH_MS - (Date.now() - S.arcStart)) / 1000));
  }, 80);
}

/* ─────────────────────────────── API polling ────────────────────── */

async function fetchData() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error("HTTP " + res.status);
    S.data = await res.json();
    renderAll();
  } catch (e) {
    console.warn("[GEOID] Fetch error:", e.message);
  } finally {
    startArc();
  }
}

function startPolling() {
  fetchData();
  setInterval(fetchData, REFRESH_MS);
}

/* ─────────────────────────────── Render orchestrator ────────────── */

function renderAll() {
  const d = S.data;
  if (!d) return;
  renderKPI(d);
  renderRacing(d);
  renderGDPChart(d);
  renderEPIChart(d);
  renderForecastChart(d);
  renderAIForecastChart(d);
  renderCIChart(d);
  renderAICards(d);
  renderAIForecastMeta(d);
  renderWarRisk(d);
  renderSectors(d);
  renderNewsFeed(d);
  renderTicker(d);
}

/* ─────────────────────────────── Helpers ────────────────────────── */

/** Resolve country display name */
const cName = (code, d) => d?.country_names?.[code] || CN_FB[code] || code;

/** Locale-format a number */
const fmt = (n, dp = 0) =>
  Number(n).toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp });

/** Update an element's text and flash it */
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el && el.textContent !== String(val)) {
    el.textContent = val;
    el.classList.remove("flash");
    void el.offsetWidth;   // force reflow
    el.classList.add("flash");
  }
}

/** Shared Chart.js tooltip config */
const tooltipCfg = () => ({
  backgroundColor: "rgba(6,11,20,0.95)",
  borderColor:     "rgba(255,255,255,0.08)",
  borderWidth:     1,
  titleColor:      "#e8f0f8",
  bodyColor:       "#94a8c0",
  titleFont:       { family: "'DM Mono'", size: 11 },
  bodyFont:        { family: "'DM Mono'", size: 10 },
  padding:         12,
  cornerRadius:    8,
});

/** Shared Chart.js scale config */
const scaleCfg = (extra = {}) => ({
  ticks:  { color: "#2a3d54", font: { family: "'DM Mono'", size: 9 }, ...extra },
  grid:   { color: "rgba(255,255,255,0.04)" },
  border: { color: "rgba(255,255,255,0.06)" },
});

/* ─────────────────────────────── KPI strip ──────────────────────── */

function renderKPI(d) {
  /* Total GDP */
  setEl("val-total-gdp", "$" + fmt(d.total_g20_gdp) + "B");

  /* Dominant economy */
  const sorted = Object.entries(d.gdp || {}).sort((a, b) => b[1] - a[1]);
  const [topCode, topVal] = sorted[0] || ["—", 0];
  setEl("val-top-economy", cName(topCode, d));
  setEl("sub-top-economy", "$" + fmt(topVal) + "B GDP");

  /* Highest EPI */
  const epiSrt = Object.entries(d.power_index || {}).sort((a, b) => b[1].score - a[1].score);
  const [topEPI, epiData] = epiSrt[0] || ["—", { score: 0 }];
  setEl("val-top-epi", cName(topEPI, d));
  setEl("sub-top-epi", "EPI " + fmt(epiData.score, 1));

  /* Top war risk */
  const riskSrt = Object.entries(d.war_risk || {}).sort((a, b) => b[1].risk_score - a[1].risk_score);
  const [topRisk, riskData] = riskSrt[0] || ["—", { risk_score: 0, level: "—" }];
  setEl("val-top-risk", cName(topRisk, d));
  setEl("sub-top-risk", riskData.risk_score.toFixed(1) + "/100 — " + riskData.level);

  /* AI avg growth */
  const growths = Object.values(d.ai_forecast || {}).map(f => f.next_year_growth || 0);
  const avg     = growths.reduce((a, b) => a + b, 0) / (growths.length || 1);
  setEl("val-avg-growth", (avg >= 0 ? "+" : "") + avg.toFixed(2) + "%");

  /* High-risk count */
  const high = Object.values(d.war_risk || {}).filter(r => ["CRITICAL", "HIGH"].includes(r.level)).length;
  setEl("val-conflicts", high);
}

/* ─────────────────────────────── Racing bar ─────────────────────── */

function renderRacing(d) {
  const wrap   = document.getElementById("race-container");
  const sorted = Object.entries(d.gdp || {}).sort((a, b) => b[1] - a[1]).slice(0, 15);
  const maxVal = sorted[0]?.[1] || 1;
  const ROW_H  = 28;

  wrap.style.height   = sorted.length * ROW_H + 20 + "px";
  wrap.style.position = "relative";

  sorted.forEach(([code, val], rank) => {
    let row = document.getElementById("rr-" + code);
    if (!row) {
      row           = document.createElement("div");
      row.id        = "rr-" + code;
      row.className = "race-row";
      row.innerHTML = `
        <span class="race-rank"  id="rrk-${code}">${rank + 1}</span>
        <span class="race-code">${code}</span>
        <div class="race-track">
          <div class="race-fill" id="rrf-${code}"
               style="background:${CC[code] || "#888"};width:0%"></div>
        </div>
        <span class="race-val"   id="rrv-${code}">$${fmt(val)}B</span>`;
      wrap.appendChild(row);
    }

    row.style.top = rank * ROW_H + 10 + "px";

    const rkEl = document.getElementById("rrk-" + code);
    if (rkEl) {
      rkEl.textContent = rank + 1;
      rkEl.className   = "race-rank" + (rank === 0 ? " race-rank-gold" : "");
    }
    const fEl = document.getElementById("rrf-" + code);
    if (fEl) fEl.style.width = (val / maxVal * 100).toFixed(1) + "%";
    const vEl = document.getElementById("rrv-" + code);
    if (vEl) vEl.textContent = "$" + fmt(val) + "B";
  });
}

/* ─────────────────────────────── GDP bar chart ──────────────────── */

function renderGDPChart(d) {
  const sorted = Object.entries(d.gdp || {}).sort((a, b) => b[1] - a[1]);
  const labels = sorted.map(([k]) => k);
  const vals   = sorted.map(([, v]) => v);
  const colors = labels.map(k => CC[k] || "#888");

  if (S.charts.gdp) {
    const ch = S.charts.gdp;
    ch.data.labels                              = labels;
    ch.data.datasets[0].data                   = vals;
    ch.data.datasets[0].backgroundColor        = colors.map(c => c + "28");
    ch.data.datasets[0].borderColor            = colors;
    ch.update("active");
    return;
  }

  const ctx = document.getElementById("chart-gdp").getContext("2d");
  S.charts.gdp = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label:           "GDP (B USD)",
        data:            vals,
        backgroundColor: colors.map(c => c + "28"),
        borderColor:     colors,
        borderWidth:     1.5,
        borderRadius:    4,
        borderSkipped:   false,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 800, easing: "easeInOutQuart" },
      plugins: {
        legend:  { display: false },
        tooltip: {
          ...tooltipCfg(),
          callbacks: {
            title: i => cName(i[0].label, d),
            label: i => ` GDP: $${fmt(i.parsed.y)}B`,
          },
        },
      },
      scales: {
        x: { ...scaleCfg({ maxRotation: 0 }) },
        y: {
          ...scaleCfg(),
          ticks: {
            ...scaleCfg().ticks,
            callback: v => "$" + (v / 1000).toFixed(0) + "T",
          },
        },
      },
    },
  });
}

/* ─────────────────────────────── EPI chart ──────────────────────── */

function renderEPIChart(d) {
  const sorted = Object.entries(d.power_index || {}).sort((a, b) => b[1].score - a[1].score);
  const labels = sorted.map(([k]) => k);
  const vals   = sorted.map(([, v]) => v.score);
  const colors = labels.map(k => CC[k] || "#888");

  if (S.charts.epi) {
    const ch = S.charts.epi;
    ch.data.labels                              = labels;
    ch.data.datasets[0].data                   = vals;
    ch.data.datasets[0].backgroundColor        = colors.map(c => c + "28");
    ch.data.datasets[0].borderColor            = colors;
    ch.update("active");
    return;
  }

  const ctx = document.getElementById("chart-epi").getContext("2d");
  S.charts.epi = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label:           "EPI Score",
        data:            vals,
        backgroundColor: colors.map(c => c + "28"),
        borderColor:     colors,
        borderWidth:     1.5,
        borderRadius:    4,
        borderSkipped:   false,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      indexAxis:           "y",
      animation:           { duration: 700 },
      plugins: {
        legend:  { display: false },
        tooltip: {
          ...tooltipCfg(),
          callbacks: {
            title: i => cName(i[0].label, d),
            label: i => ` EPI: ${i.parsed.x.toFixed(1)} — ${d.power_index[i.label]?.tier || ""}`,
          },
        },
      },
      scales: {
        x: { ...scaleCfg(), max: 105 },
        y: { ...scaleCfg({ color: "#4d6480" }) },
      },
    },
  });
}

/* ─────────────────────────────── Forecast line chart ────────────── */

function renderForecastChart(d) {
  const fc   = d.gdp_forecast;
  if (!fc) return;

  const top8   = Object.entries(d.gdp || {}).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k]) => k);
  const years  = Object.keys(fc[top8[0]]?.forecast || {}).sort();
  const labels = ["Current", ...years];

  const datasets = top8.map(code => {
    const f = fc[code];
    if (!f) return null;
    const color = CC[code] || "#888";
    return {
      label:               code,
      data:                [f.current_gdp, ...years.map(yr => f.forecast[yr] || null)],
      borderColor:         color,
      backgroundColor:     color + "18",
      fill:                false,
      tension:             0.4,
      pointRadius:         3,
      pointHoverRadius:    6,
      pointBackgroundColor: color,
      borderWidth:         2,
    };
  }).filter(Boolean);

  if (S.charts.forecast) {
    S.charts.forecast.data.datasets = datasets;
    S.charts.forecast.data.labels   = labels;
    S.charts.forecast.update("active");
    return;
  }

  const ctx = document.getElementById("chart-forecast").getContext("2d");
  S.charts.forecast = new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 900 },
      interaction:         { mode: "index", intersect: false },
      plugins: {
        legend: {
          display:  true,
          position: "bottom",
          labels:   { color: "#4d6480", font: { family: "'DM Mono'", size: 9 }, boxWidth: 10, padding: 10, usePointStyle: true },
        },
        tooltip: {
          ...tooltipCfg(),
          callbacks: { label: i => ` ${i.dataset.label}: $${fmt(i.parsed.y)}B` },
        },
      },
      scales: {
        x: { ...scaleCfg() },
        y: { ...scaleCfg(), ticks: { ...scaleCfg().ticks, callback: v => "$" + (v / 1000).toFixed(0) + "T" } },
      },
    },
  });
}

/* ─────────────────────────────── AI Forecast bar chart ──────────── */

function renderAIForecastChart(d) {
  if (!d.ai_forecast) return;

  const sorted  = Object.entries(d.ai_forecast).sort((a, b) => b[1].next_year_gdp - a[1].next_year_gdp);
  const labels  = sorted.map(([k]) => k);
  const current = sorted.map(([k]) => d.gdp?.[k] || 0);
  const pred    = sorted.map(([, v]) => v.next_year_gdp);
  const ciLow   = sorted.map(([, v]) => v.confidence_interval[0]);
  const ciHigh  = sorted.map(([, v]) => v.confidence_interval[1]);
  const colors  = labels.map(k => CC[k] || "#888");

  /* Custom plugin: draw error bars after datasets */
  const errorBarPlugin = {
    id: "geoid-error-bars",
    afterDatasetsDraw(chart) {
      const ctx  = chart.ctx;
      const meta = chart.getDatasetMeta(1);
      if (!meta.visible) return;
      ctx.save();
      ctx.strokeStyle = "rgba(167,139,250,0.5)";
      ctx.lineWidth   = 1.5;
      meta.data.forEach((bar, i) => {
        const x  = bar.x;
        const yL = chart.scales.y.getPixelForValue(ciLow[i]);
        const yH = chart.scales.y.getPixelForValue(ciHigh[i]);
        const hw = 4;
        ctx.beginPath();
        ctx.moveTo(x, yH); ctx.lineTo(x, yL);
        ctx.moveTo(x - hw, yH); ctx.lineTo(x + hw, yH);
        ctx.moveTo(x - hw, yL); ctx.lineTo(x + hw, yL);
        ctx.stroke();
      });
      ctx.restore();
    },
  };

  if (S.charts.aiFC) {
    const ch = S.charts.aiFC;
    ch.data.labels                              = labels;
    ch.data.datasets[0].data                   = current;
    ch.data.datasets[0].backgroundColor        = colors.map(c => c + "20");
    ch.data.datasets[0].borderColor            = colors.map(c => c + "88");
    ch.data.datasets[1].data                   = pred;
    ch.data.datasets[1].backgroundColor        = colors.map(c => c + "44");
    ch.data.datasets[1].borderColor            = colors;
    ch.update("active");
    return;
  }

  const ctx = document.getElementById("chart-ai-forecast")?.getContext("2d");
  if (!ctx) return;

  S.charts.aiFC = new Chart(ctx, {
    type:    "bar",
    plugins: [errorBarPlugin],
    data: {
      labels,
      datasets: [
        {
          label:              "Current GDP 2024",
          data:               current,
          backgroundColor:    colors.map(c => c + "20"),
          borderColor:        colors.map(c => c + "88"),
          borderWidth:        1,
          borderRadius:       3,
          barPercentage:      0.4,
          categoryPercentage: 0.85,
        },
        {
          label:              "AI Predicted GDP 2025",
          data:               pred,
          backgroundColor:    colors.map(c => c + "44"),
          borderColor:        colors,
          borderWidth:        1.5,
          borderRadius:       3,
          barPercentage:      0.4,
          categoryPercentage: 0.85,
        },
      ],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 900 },
      plugins: {
        legend: {
          display:  true,
          position: "top",
          align:    "end",
          labels:   { color: "#4d6480", font: { family: "'DM Mono'", size: 9 }, boxWidth: 10, padding: 8, usePointStyle: true },
        },
        tooltip: {
          ...tooltipCfg(),
          callbacks: {
            title: i => cName(i[0].label, d),
            label: (item) => {
              const code = labels[item.dataIndex];
              const af   = d.ai_forecast[code];
              if (item.datasetIndex === 1 && af) {
                const ci = af.confidence_interval;
                return [
                  ` Predicted: $${fmt(af.next_year_gdp)}B`,
                  ` Growth: ${af.next_year_growth >= 0 ? "+" : ""}${af.next_year_growth.toFixed(2)}%`,
                  ` Signal: ${af.signal}`,
                  ` CI: [$${fmt(ci[0])}B – $${fmt(ci[1])}B]`,
                  ` Confidence: ${af.confidence_score}%`,
                ];
              }
              return ` Current: $${fmt(item.parsed.y)}B`;
            },
          },
        },
      },
      scales: {
        x: { ...scaleCfg({ maxRotation: 0 }) },
        y: { ...scaleCfg(), ticks: { ...scaleCfg().ticks, callback: v => "$" + (v / 1000).toFixed(0) + "T" } },
      },
    },
  });
}

/* ─────────────────────────────── CI horizontal chart ────────────── */

function renderCIChart(d) {
  if (!d.ai_forecast) return;

  const top10 = Object.entries(d.ai_forecast)
    .sort((a, b) => b[1].next_year_gdp - a[1].next_year_gdp)
    .slice(0, 10);

  const labels = top10.map(([k]) => k);
  const lows   = top10.map(([, v]) => v.confidence_interval[0]);
  const highs  = top10.map(([, v]) => v.confidence_interval[1]);
  const spread = top10.map(([, v]) => v.confidence_interval[1] - v.confidence_interval[0]);
  const preds  = top10.map(([, v]) => v.next_year_gdp);
  const colors = labels.map(k => CC[k] || "#888");

  if (S.charts.ci) {
    const ch = S.charts.ci;
    ch.data.labels                              = labels;
    ch.data.datasets[0].data                   = lows;
    ch.data.datasets[1].data                   = spread;
    ch.data.datasets[1].backgroundColor        = colors.map(c => c + "44");
    ch.data.datasets[1].borderColor            = colors;
    ch.update("active");
    return;
  }

  const ctx = document.getElementById("chart-ci")?.getContext("2d");
  if (!ctx) return;

  S.charts.ci = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label:           "CI Base",
          data:            lows,
          backgroundColor: "transparent",
          borderColor:     "transparent",
          borderWidth:     0,
          stack:           "ci",
        },
        {
          label:           "90% Confidence Interval",
          data:            spread,
          backgroundColor: colors.map(c => c + "44"),
          borderColor:     colors,
          borderWidth:     1,
          borderRadius:    3,
          stack:           "ci",
        },
      ],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      indexAxis:           "y",
      animation:           { duration: 700 },
      plugins: {
        legend:  { display: false },
        tooltip: {
          ...tooltipCfg(),
          filter: item => item.datasetIndex === 1,
          callbacks: {
            title: i => cName(i[0].label, d) + " — 90% CI",
            label: (_, i) => [
              ` Lower:     $${fmt(lows[i])}B`,
              ` Upper:     $${fmt(highs[i])}B`,
              ` Predicted: $${fmt(preds[i])}B`,
            ],
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          ...scaleCfg(),
          ticks: { ...scaleCfg().ticks, callback: v => "$" + (v / 1000).toFixed(0) + "T" },
        },
        y: { stacked: true, ...scaleCfg({ color: "#4d6480" }) },
      },
    },
  });
}

/* ─────────────────────────────── AI prediction cards ────────────── */

function renderAICards(d) {
  if (!d.ai_forecast) return;
  const grid = document.getElementById("ai-cards-grid");
  if (!grid) return;

  const sorted = Object.entries(d.ai_forecast)
    .sort((a, b) => b[1].next_year_growth - a[1].next_year_growth);

  const maxPred  = Math.max(...sorted.map(([, v]) => v.next_year_gdp));
  const mkColors = {
    poly_regression:       "#3b82f6",
    exponential_smoothing: "#f59e0b",
    ridge_features:        "#a78bfa",
  };
  const mkShort  = {
    poly_regression:       "POLY",
    exponential_smoothing: "HOLT",
    ridge_features:        "RDG",
  };

  grid.innerHTML = sorted.map(([code, af]) => {
    const g   = af.next_year_growth;
    const gcl = g > 1 ? "pos" : g < -1 ? "neg" : "neu";
    const ci  = af.confidence_interval;
    const mb  = af.model_breakdown || {};

    const bars = Object.keys(mkColors).map(k => `
      <div class="aic-model-row">
        <span class="aic-model-label">${mkShort[k]}</span>
        <div class="aic-model-bar-track">
          <div class="aic-model-bar-fill"
               style="width:${((mb[k] || af.next_year_gdp) / maxPred * 100).toFixed(1)}%;background:${mkColors[k]}66"></div>
        </div>
        <span class="aic-model-val">$${fmt(mb[k] || 0)}B</span>
      </div>`).join("");

    return `
      <div class="ai-card signal-${af.signal}" title="${af.model_version}">
        <div class="aic-header">
          <span class="aic-code">${code}</span>
          <span class="aic-signal ${af.signal}">${af.signal.substring(0, 3)}</span>
        </div>
        <div class="aic-name">${cName(code, d).substring(0, 15)}</div>
        <div class="aic-predicted">$${fmt(af.next_year_gdp)}B</div>
        <div class="aic-growth ${gcl}">${g >= 0 ? "+" : ""}${g.toFixed(2)}% YoY</div>
        <div class="aic-conf-wrap">
          <div class="aic-conf-track">
            <div class="aic-conf-fill" style="width:${af.confidence_score}%"></div>
          </div>
          <span class="aic-conf-pct">${af.confidence_score.toFixed(0)}%</span>
        </div>
        <div class="aic-ci">CI: $${fmt(ci[0])}–$${fmt(ci[1])}B</div>
        <div class="aic-models">${bars}</div>
      </div>`;
  }).join("");
}

/* ─────────────────────────────── AI meta bar ────────────────────── */

function renderAIForecastMeta(d) {
  const s = d.ai_forecast_summary;
  if (!s) return;
  const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  set("ai-model-ver",       "v " + (s.model_version || "—").replace("GEOID-ML-", ""));
  set("ai-world-growth",    "G20: " + (s.avg_world_growth_pct >= 0 ? "+" : "") + (s.avg_world_growth_pct || 0).toFixed(2) + "%");
  set("ai-expansion-count", "Expanding: " + (s.expansion_count || 0) + "/" + Object.keys(d.ai_forecast || {}).length);
  set("ai-fastest",         "↑ Fastest: " + (s.fastest_growing || "—"));
}

/* ─────────────────────────────── War risk cards ─────────────────── */

function renderWarRisk(d) {
  const grid   = document.getElementById("war-grid");
  const sorted = Object.entries(d.war_risk || {}).sort((a, b) => b[1].risk_score - a[1].risk_score);
  grid.innerHTML = sorted.map(([code, r]) => `
    <div class="war-card wl-${r.level}" title="${(r.active_conflicts || []).join(", ") || "No active conflicts"}">
      <div class="wc-top">
        <span class="wc-code">${code}</span>
        <span class="wc-trend">${r.trend}</span>
      </div>
      <div class="wc-name">${cName(code, d)}</div>
      <div class="wc-bar-bg">
        <div class="wc-bar-fill" style="width:${r.risk_score}%"></div>
      </div>
      <div class="wc-bottom">
        <span class="wc-score">${r.risk_score.toFixed(0)}</span>
        <span class="wc-level">${r.level}</span>
      </div>
    </div>`).join("");
}

/* ─────────────────────────────── Sector panel ───────────────────── */

const SECTOR_PAL = [
  "#3b82f6","#f59e0b","#ef4444","#22c55e","#a78bfa",
  "#f97316","#38bdf8","#ec4899","#fbbf24","#34d399",
];

function renderSectors(d) {
  const tabs = document.getElementById("sector-tabs");

  if (!tabs.children.length) {
    SECTOR_TABS.forEach(code => {
      const btn       = document.createElement("button");
      btn.className   = "sector-tab" + (code === S.activeSector ? " active" : "");
      btn.textContent = code;
      btn.dataset.code = code;
      btn.addEventListener("click", () => {
        S.activeSector = code;
        tabs.querySelectorAll(".sector-tab").forEach(t =>
          t.classList.toggle("active", t.dataset.code === code));
        updateSector(d);
      });
      tabs.appendChild(btn);
    });
  }
  updateSector(d);
}

function updateSector(d) {
  const code    = S.activeSector;
  const sectors = d.sector_importance?.[code];
  if (!sectors) return;

  const labels = Object.keys(sectors);
  const vals   = Object.values(sectors);
  const colors = labels.map((_, i) => SECTOR_PAL[i % SECTOR_PAL.length]);

  /* Legend */
  document.getElementById("sector-legend").innerHTML = labels.map((l, i) => `
    <div class="legend-item">
      <div class="legend-dot" style="background:${colors[i]}"></div>
      <span>${l}: ${vals[i]}%</span>
    </div>`).join("");

  if (S.charts.sector) {
    S.charts.sector.data.labels                       = labels;
    S.charts.sector.data.datasets[0].data            = vals;
    S.charts.sector.data.datasets[0].backgroundColor = colors.map(c => c + "bb");
    S.charts.sector.data.datasets[0].borderColor     = colors;
    S.charts.sector.update();
    return;
  }

  const ctx = document.getElementById("chart-sector").getContext("2d");
  S.charts.sector = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data:            vals,
        backgroundColor: colors.map(c => c + "bb"),
        borderColor:     colors,
        borderWidth:     1.5,
        hoverOffset:     8,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      cutout:              "60%",
      animation:           { duration: 600 },
      plugins: {
        legend:  { display: false },
        tooltip: {
          ...tooltipCfg(),
          callbacks: { label: i => ` ${i.label}: ${i.parsed}%` },
        },
      },
    },
  });
}

/* ─────────────────────────────── News feed ──────────────────────── */

function renderNewsFeed(d) {
  const feed = document.getElementById("news-feed");
  if (!d.war_news?.length) return;
  feed.innerHTML = d.war_news.map(n => `
    <div class="news-item sev-${n.severity}">
      <div class="news-top">
        <span class="news-country">${n.country}</span>
        <div class="news-badges">
          <span class="news-sev ${n.severity}">${n.severity}</span>
          <span class="news-cat">${n.category || "INTEL"}</span>
        </div>
      </div>
      <div class="news-title">${n.title}</div>
      <div class="news-time">${n.age || "—"}</div>
    </div>`).join("");
}

/* ─────────────────────────────── Ticker ─────────────────────────── */

function renderTicker(d) {
  const el     = document.getElementById("ticker-content");
  const sorted = Object.entries(d.war_risk || {}).sort((a, b) => b[1].risk_score - a[1].risk_score);
  const html   = sorted.map(([code, r]) => `
    <span class="ticker-item">
      <span class="ti-code">${code}</span>
      <span>${cName(code, d).substring(0, 10)}</span>
      <span class="ti-sev ${r.level}">${r.level}</span>
      <span>${r.risk_score.toFixed(1)}/100</span>
      <span>${r.trend}</span>
    </span>`).join("");
  /* Double content for seamless CSS loop */
  el.innerHTML = html + html;
}

/* ─────────────────────────────── Entry point ────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  startClock();
  runBoot();
  /* Delay data load until boot animation is mostly done */
  setTimeout(startPolling, BOOT[BOOT.length - 1].d + 600);
});
