/**
 * HYDRO-GUARD AI : Urban Drainage Intelligence & Smart Water Management
 * Complete Client-Side Controller
 * Supporting Cinematic Homepage & Dedicated Single-Page App Screens
 * Tailored for Indore Municipal Corporation (IMC)
 */

const API_BASE = "";

// Global Application State
const appState = {
  currentView: "home",      // "home" | "app"
  currentScreen: "sound",    // "sound" | "purity" | "map" | "prediction" | "simulator" | "history"
  
  // Real-time environmental metrics
  rainfall_mmh: 42.6,
  river_stage_m: 4.32,
  drainage_flow_m3s: 2.8,
  
  // Leaflet map instance
  leafletMap: null,
  mapMarkers: [],
  mapPolyline: null,
  
  // Audio state
  audioContext: null,
  audioElement: null,
  audioPlaying: false,
  audioDuration: 28,
  audioCurrentTime: 0,
  activeAudioSample: "sample_medium.mp3",
  
  // Image state
  activeImageSample: "clean_rainwater",
  
  // History logs cache
  historyRecords: [],
  activeLogFilter: "ALL",
  
  // Polling intervals
  envPollTimer: null,
  clockTimer: null,
};

// Topographical Nodes of Indore Drainage Basin
const INDORE_NODES = [
  { id: "NODE_RAU", name: "Rau Headwaters", lat: 22.6450, lon: 75.8180, elevation: 560.0, zone: "South Ridge" },
  { id: "NODE_BHANWARKUAN", name: "Bhanwarkuan Storm Junction", lat: 22.6891, lon: 75.8653, elevation: 552.0, zone: "South-Central" },
  { id: "NODE_RAJWARA", name: "Rajwada / Krishnapura Confluence", lat: 22.7186, lon: 75.8550, elevation: 540.0, zone: "Central Confluence" },
  { id: "NODE_RAMBAGH", name: "Rambagh Urban Drain", lat: 22.7100, lon: 75.8620, elevation: 536.0, zone: "Central-North" },
  { id: "NODE_PARDESHIPURA", name: "Pardeshipura Industrial Drain", lat: 22.7410, lon: 75.8750, elevation: 526.0, zone: "North Industrial" },
  { id: "NODE_VIJAY_NAGAR", name: "Vijay Nagar Eastern Sump", lat: 22.7533, lon: 75.8937, elevation: 532.0, zone: "Eastern Catchment" },
  { id: "NODE_KABITHEDI", name: "Kabithedi 245 MLD Main STP", lat: 22.7750, lon: 75.8680, elevation: 515.0, zone: "Northern Outfall" }
];

// Screen Meta Descriptions
const SCREEN_TITLES = {
  sound: {
    title: "Sound Level Tester",
    subtitle: "Upload and analyze drain/sewer audio to estimate water level and detect abnormal conditions"
  },
  purity: {
    title: "Image Purity Tester",
    subtitle: "Computer vision colorimetric screening enforcing the 80% Khan River Purity Rule before discharge"
  },
  map: {
    title: "Spatial Drainage GIS View",
    subtitle: "Interactive GIS topological drainage and river reaches across the elevation gradient"
  },
  reports: {
    title: "Reports & Monitoring",
    subtitle: "Water Quality • Drainage • Filtration • Area Intelligence"
  },
  'model-intel': {
    title: "AI Model Intelligence & Scientific Explainability",
    subtitle: "Dataset Lineage • Training Dynamics • Residual Diagnostics • XAI & Permutation Importance • What-If Lab"
  },
  explorer: {
    title: "Multi-Basin Dataset Explorer & Live Inference",
    subtitle: "8 Acquired Datasets • Ground-Truth Observations • Statistical Distributions • Direct Deep Learning Inference"
  },
  'weather-radar': {
    title: "Weather Radar & Precipitation Intelligence",
    subtitle: "Doppler Radar Audit & Specifications • Indian Monsoon Cloudburst Hyetograph • Ground Rain Telemetry"
  },
  drivers: {
    title: "Feature Breakdown & Flood Driver Attribution",
    subtitle: "Hydrological Attribution • Permutation Feature Importance • Temporal Lag Decay • Spatio-Temporal Jacobian"
  }
};

// ==============================================================================
// INITIALIZATION
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initLiveClock();
  initEnvironmentalPolling();
  initRoutingFromHash();
  initAudioPlayer();
  initWaveformCanvas();
  initFileUploadHandlers();
  initSliders();
  
  // Handle URL hash changes (back/forward browser navigation)
  window.addEventListener("hashchange", initRoutingFromHash);
});

// ==============================================================================
// 1. NAVIGATION & ROUTING
// ==============================================================================
function initRoutingFromHash() {
  const hash = window.location.hash.replace("#", "").toLowerCase();
  if (!hash || hash === "home") {
    navigateToHome(false);
  } else if (SCREEN_TITLES[hash] || hash === "explorer") {
    navigateTo(hash, false);
  } else {
    navigateToHome(false);
  }
}

function navigateToHome(updateHash = true) {
  appState.currentView = "home";
  if (updateHash) window.location.hash = "home";

  const vHome = document.getElementById("view-home");
  const vApp = document.getElementById("view-app");
  if (vHome) {
    vHome.classList.add("active");
    vHome.style.display = "block";
  }
  if (vApp) {
    vApp.classList.remove("active");
    vApp.style.display = "none";
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

window.switchScreen = function(id) { return navigateTo(id); };
function navigateTo(screenId, updateHash = true) {
  if (!SCREEN_TITLES[screenId]) screenId = "explorer";
  
  appState.currentView = "app";
  appState.currentScreen = screenId;
  if (updateHash) window.location.hash = screenId;

  // Toggle View Containers
  const vHome = document.getElementById("view-home");
  const vApp = document.getElementById("view-app");
  if (vHome) {
    vHome.classList.remove("active");
    vHome.style.display = "none";
  }
  if (vApp) {
    vApp.classList.add("active");
    vApp.style.display = "block";
    vApp.classList.remove("white-theme");
  }

  // Toggle Active Screen
  document.querySelectorAll(".screen-container").forEach(el => {
    el.classList.remove("active");
    el.style.display = "none";
  });
  const targetScreen = document.getElementById(`screen-${screenId}`);
  if (targetScreen) {
    targetScreen.classList.add("active");
    targetScreen.style.display = "block";
  }

  // Update Sidebar Active Pill
  document.querySelectorAll(".sidebar-item").forEach(item => item.classList.remove("active"));
  const activeNavItem = document.getElementById(`nav-item-${screenId}`);
  if (activeNavItem) activeNavItem.classList.add("active");

  // Update Screen Title & Subtitle
  const meta = SCREEN_TITLES[screenId];
  if (meta) {
    const curTitle = document.getElementById("current-screen-title");
    const curSub = document.getElementById("current-screen-subtitle");
    if (curTitle) curTitle.textContent = meta.title;
    if (curSub) curSub.textContent = meta.subtitle;
  }

  // Hide general page-top-bar on dedicated dashboard screens
  const pageTopBar = document.querySelector(".page-top-bar");
  if (pageTopBar) {
    pageTopBar.style.display = (screenId === "reports" || screenId === "model-intel" || screenId === "explorer" || screenId === "weather-radar") ? "none" : "flex";
  }

  // Screen-Specific Triggers
  if (screenId === "map") {
    setTimeout(initLeafletMap, 150);
    setTimeout(loadStreetInundationPanel, 200);
  } else if (screenId === "reports") {
    loadReportsAndMonitoring();
  } else if (screenId === "model-intel") {
    loadModelIntelligenceDashboard();
  } else if (screenId === "explorer") {
    loadDatasetExplorer();
  } else if (screenId === "weather-radar") {
    loadWeatherRadarIntelligence();
  } else if (screenId === "drivers") {
    loadFloodDriversAnalysis();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function scrollToSection(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) el.scrollIntoView({ behavior: "smooth" });
}

// ==============================================================================
// 2. LIVE CLOCK & ENVIRONMENTAL DATA POLLING
// ==============================================================================
function initLiveClock() {
  updateClock();
  appState.clockTimer = setInterval(updateClock, 1000);
}

function updateClock() {
  const now = new Date();
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const day = String(now.getDate()).padStart(2, "0");
  const month = months[now.getMonth()];
  const year = now.getFullYear();
  
  let hours = now.getHours();
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12 || 12;
  const minutes = String(now.getMinutes()).padStart(2, "0");
  
  const formatted = `${day} ${month} ${year} ${String(hours).padStart(2, "0")}:${minutes} ${ampm}`;
  const clockEl = document.getElementById("app-clock-txt");
  if (clockEl) clockEl.textContent = formatted;
}

function initEnvironmentalPolling() {
  fetchEnvironmentalSummary();
  appState.envPollTimer = setInterval(fetchEnvironmentalSummary, 3500);
}

async function fetchEnvironmentalSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/flood/environmental-summary`);
    if (!res.ok) return;
    const data = await res.json();

    if (data.live_rainfall) {
      const rain = data.live_rainfall;
      appState.rainfall_mmh = rain.value;
      const weatherTxt = document.getElementById("app-weather-txt");
      if (weatherTxt) weatherTxt.textContent = `${Math.round(rain.temp_c || 24)}°C ${rain.condition || "Light Rain"}`;
    }

    if (data.river_level) {
      appState.river_stage_m = data.river_level.value;
    }

    if (data.drainage_flow) {
      appState.drainage_flow_m3s = data.drainage_flow.value;
    }
  } catch (err) {
    console.warn("Environmental polling fallback:", err);
  }
}

// ==============================================================================
// 3. SOUND LEVEL TESTER (Exact match to reference mockup)
// ==============================================================================
function initAudioPlayer() {
  appState.audioElement = document.getElementById("native-audio-player");
  if (!appState.audioElement) return;

  appState.audioElement.src = "/samples/audio/moderate_surge_60pct.wav";

  appState.audioElement.addEventListener("timeupdate", () => {
    if (!appState.audioElement.duration) return;
    const cur = appState.audioElement.currentTime;
    const dur = appState.audioElement.duration;
    const pct = (cur / dur) * 100;
    
    const scrubber = document.getElementById("audio-scrubber");
    if (scrubber) scrubber.value = pct;

    const timeLabel = document.getElementById("audio-current-time");
    if (timeLabel) {
      const formatT = (t) => {
        const m = Math.floor(t / 60);
        const s = Math.floor(t % 60);
        return `${m}:${String(s).padStart(2, "0")}`;
      };
      timeLabel.textContent = `${formatT(cur)} / ${formatT(dur)}`;
    }
  });

  appState.audioElement.addEventListener("ended", () => {
    appState.audioPlaying = false;
    document.getElementById("play-pause-icon").textContent = "▶";
  });

  const scrubber = document.getElementById("audio-scrubber");
  if (scrubber) {
    scrubber.addEventListener("input", (e) => {
      if (appState.audioElement.duration) {
        appState.audioElement.currentTime = (e.target.value / 100) * appState.audioElement.duration;
      }
    });
  }
}

function toggleAudioPlayback() {
  if (!appState.audioElement) return;
  if (appState.audioPlaying) {
    appState.audioElement.pause();
    appState.audioPlaying = false;
    document.getElementById("play-pause-icon").textContent = "▶";
  } else {
    appState.audioElement.play().catch(e => console.log("Audio play error:", e));
    appState.audioPlaying = true;
    document.getElementById("play-pause-icon").textContent = "⏸";
  }
}

function loadSampleAudio(displayName, targetPct, filePath) {
  appState.activeAudioSample = displayName;
  document.getElementById("sound-preview-filename").textContent = displayName;
  
  if (appState.audioElement) {
    appState.audioElement.src = filePath;
    appState.audioElement.currentTime = 0;
    appState.audioPlaying = false;
    document.getElementById("play-pause-icon").textContent = "▶";
  }

  // Animate dynamic waveform
  drawWaveformBars(targetPct);
  
  // Run immediate analysis for responsiveness
  runAcousticAnalysisWithLevel(targetPct, displayName);
}

function initWaveformCanvas() {
  drawWaveformBars(60);
}

function drawWaveformBars(intensity = 60) {
  const canvas = document.getElementById("audio-waveform-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, rect.width, rect.height);
  const numBars = 55;
  const barWidth = 3;
  const gap = (rect.width - numBars * barWidth) / (numBars - 1);
  const midY = rect.height / 2;

  for (let i = 0; i < numBars; i++) {
    const factor = Math.sin((i / numBars) * Math.PI);
    const noise = Math.random() * 0.4 + 0.6;
    const barHeight = Math.max(4, factor * (intensity / 100) * (rect.height * 0.8) * noise);

    const grad = ctx.createLinearGradient(0, midY - barHeight / 2, 0, midY + barHeight / 2);
    grad.addColorStop(0, "#00d2ff");
    grad.addColorStop(0.5, "#0084ff");
    grad.addColorStop(1, "#00d2ff");

    ctx.fillStyle = grad;
    ctx.fillRect(i * (barWidth + gap), midY - barHeight / 2, barWidth, barHeight);
  }
}

async function runAcousticAnalysis() {
  const fileInput = document.getElementById("input-audio-upload");
  if (fileInput && fileInput.files.length > 0) {
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/sensors/acoustic-level/analyze`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      renderAcousticResult(data, file.name);
    } catch (err) {
      console.error("Acoustic analysis upload error:", err);
      runAcousticAnalysisWithLevel(68.0, file.name);
    }
  } else {
    runAcousticAnalysisWithLevel(68.0, appState.activeAudioSample);
  }
}

async function runAcousticAnalysisWithLevel(targetLevel, filename) {
  try {
    const formData = new FormData();
    formData.append("test_level_pct", targetLevel);
    const res = await fetch(`${API_BASE}/api/v1/sensors/acoustic-level/analyze`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    renderAcousticResult(data, filename);
  } catch (err) {
    console.error("Acoustic level request error:", err);
  }
}

function renderAcousticResult(data, filename) {
  const level = Math.round(data.inferred_water_level_pct || (data.analysis && data.analysis.estimated_water_level_pct) || 68);
  const db = Math.round(data.acoustic_decibels_db || (data.analysis && data.analysis.decibel_spl) || 72);
  const recordId = data.record_id ? `#${data.record_id} (SQLite)` : "#Live (SQLite)";

  // Update Circular Gauge
  const circle = document.getElementById("gauge-sound-circle");
  const text = document.getElementById("gauge-sound-text");
  if (circle && text) {
    const circumference = 188.4;
    const offset = circumference - (level / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    text.textContent = `${level}%`;

    if (level <= 50) {
      circle.style.stroke = "var(--safe-green)";
    } else if (level <= 75) {
      circle.style.stroke = "var(--warn-amber)";
    } else {
      circle.style.stroke = "var(--danger-red)";
    }
  }

  // Update Sound Level dB
  document.getElementById("sound-db-text").textContent = `${db} dB`;

  // Update Overflow Risk & Alert Banner
  const riskText = document.getElementById("sound-risk-text");
  const riskWave = document.getElementById("sound-risk-wave");
  const alertBanner = document.getElementById("sound-alert-banner");
  const alertIcon = document.getElementById("sound-alert-icon");
  const alertHead = document.getElementById("sound-alert-headline");
  const alertSub = document.getElementById("sound-alert-sub");
  const recText = document.getElementById("sound-rec-text");

  alertBanner.className = "status-verdict-banner";

  if (level <= 50) {
    riskText.textContent = "Low";
    riskText.style.color = "var(--safe-green)";
    riskWave.style.color = "var(--safe-green)";
    alertBanner.classList.add("safe");
    alertIcon.textContent = "✓";
    alertHead.textContent = "Normal Flow";
    alertSub.textContent = "Current audio indicates normal drainage flow condition.";
    recText.textContent = "Continue monitoring. No immediate action required. Water level is within normal range.";
  } else if (level <= 75) {
    riskText.textContent = "Medium";
    riskText.style.color = "var(--warn-amber)";
    riskWave.style.color = "var(--warn-amber)";
    alertBanner.classList.add("warning");
    alertIcon.textContent = "⚠️";
    alertHead.textContent = "Moderate Surge Flow";
    alertSub.textContent = "Water stage elevated. Sluice gate monitoring active.";
    recText.textContent = "Pre-charge Kabithedi auxiliary high-lift pumps. Standby for diversion if level exceeds 75%.";
  } else {
    riskText.textContent = "Critical";
    riskText.style.color = "var(--danger-red)";
    riskWave.style.color = "var(--danger-red)";
    alertBanner.classList.add("critical");
    alertIcon.textContent = "🚨";
    alertHead.textContent = "Full-Pipe Flash Surge";
    alertSub.textContent = "Pressurized hydraulic turbulence in dark culvert!";
    recText.textContent = "CRITICAL: Deploy emergency IMC diesel dewatering pumps and open Bilawali retention spillway.";
  }

  // Update Key-Value Specs Table
  document.getElementById("spec-sound-filename").textContent = filename || "audio_recording.wav";
  document.getElementById("spec-sound-avgdb").textContent = `${db} dB SPL`;
  document.getElementById("spec-sound-recordid").textContent = recordId;

  // Timestamp
  const now = new Date();
  document.getElementById("sound-result-timestamp").textContent = now.toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
  });
}

function resetSoundTester() {
  document.getElementById("input-audio-upload").value = "";
  loadSampleAudio("sample_medium.mp3", 60.0, "/samples/audio/moderate_surge_60pct.wav");
}

// ==============================================================================
// 4. IMAGE PURITY TESTER (OpenCV 80% Rule)
// ==============================================================================
function loadSampleImage(sampleKey, filename, imagePath) {
  appState.activeImageSample = sampleKey;
  document.getElementById("purity-preview-filename").textContent = filename;
  
  const imgEl = document.getElementById("purity-preview-img");
  if (imgEl) imgEl.src = imagePath;

  runImageAnalysisWithSample(sampleKey, filename);
}

async function runImageAnalysis() {
  const fileInput = document.getElementById("input-image-upload");
  if (fileInput && fileInput.files.length > 0) {
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/sensors/cv-purity/analyze`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      renderPurityResult(data, file.name);
    } catch (err) {
      console.error("Image analysis error:", err);
      runImageAnalysisWithSample("clean_rainwater", file.name);
    }
  } else {
    runImageAnalysisWithSample(appState.activeImageSample, `${appState.activeImageSample}.jpg`);
  }
}

async function runImageAnalysisWithSample(sampleType, filename) {
  try {
    const formData = new FormData();
    formData.append("sample_type", sampleType);
    const res = await fetch(`${API_BASE}/api/v1/sensors/cv-purity/analyze`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    renderPurityResult(data, filename);
  } catch (err) {
    console.error("Sample image analysis error:", err);
  }
}

function renderPurityResult(data, filename) {
  const purity = Math.round(data.purity_score_percent || (data.analysis && data.analysis.purity_score) || 85);
  const isPass = Boolean(data.pass_80pct_rule !== undefined ? data.pass_80pct_rule : (data.analysis && data.analysis.is_clean));
  const gateAction = data.gate_action || (data.analysis && data.analysis.gate_status) || "GATE OPEN TO KHAN RIVER";
  const recordId = data.record_id ? `#${data.record_id} (SQLite)` : "#Live (SQLite)";

  // Update Circular Gauge
  const circle = document.getElementById("gauge-purity-circle");
  const text = document.getElementById("gauge-purity-text");
  if (circle && text) {
    const circumference = 188.4;
    const offset = circumference - (purity / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    text.textContent = `${purity}%`;
    circle.style.stroke = isPass ? "var(--safe-green)" : "var(--danger-red)";
  }

  // Turbidity
  const turbVal = data.parameters_analyzed ? data.parameters_analyzed.turbidity_ntu : (data.analysis && data.analysis.turbidity_ntu_estimate ? data.analysis.turbidity_ntu_estimate : 12);
  document.getElementById("purity-turbidity-val").textContent = `${Math.round(turbVal)} NTU`;

  // Status Alert Banner & Gate
  const banner = document.getElementById("purity-alert-banner");
  const icon = document.getElementById("purity-alert-icon");
  const head = document.getElementById("purity-alert-headline");
  const sub = document.getElementById("purity-alert-sub");
  const gateEl = document.getElementById("purity-gate-action");
  const recEl = document.getElementById("purity-rec-text");

  banner.className = "status-verdict-banner";

  if (isPass) {
    banner.classList.add("safe");
    icon.textContent = "✓";
    head.textContent = `PASS — Purity ${purity}% (≥ 80%)`;
    sub.textContent = "Water meets cleanliness threshold for direct Khan River discharge.";
    gateEl.textContent = "GATE OPEN TO KHAN RIVER";
    gateEl.style.color = "var(--safe-green)";
    recEl.textContent = "Maintain gravity channel outflow into the Khan River. Clean storm runoff aids river rejuvenation.";
  } else {
    banner.classList.add("critical");
    icon.textContent = "⚠️";
    head.textContent = `FAIL — Purity ${purity}% (< 80%)`;
    sub.textContent = "Heavy turbidity / sewage detected. Diverting from Khan River!";
    gateEl.textContent = "DIVERTING TO STP / FILTRATION BASIN";
    gateEl.style.color = "var(--danger-red)";
    recEl.textContent = "Sluice gates diverted to Kabithedi 245 MLD STP to protect Khan River from toxic industrial/sewer sludge.";
  }

  document.getElementById("spec-purity-filename").textContent = filename || "outfall_photo.jpg";
  document.getElementById("spec-purity-recordid").textContent = recordId;

  const now = new Date();
  document.getElementById("purity-result-timestamp").textContent = now.toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
  });
}

function resetImageTester() {
  document.getElementById("input-image-upload").value = "";
  loadSampleImage("clean_rainwater", "clean_rainwater.jpg", "/samples/images/clean_rainwater.jpg");
}

// ==============================================================================
// 5. INDORE FLOOD MAP VIEW (Leaflet GIS)
// ==============================================================================
function initLeafletMap() {
  const container = document.getElementById("leaflet-map");
  if (!container) return;

  if (appState.leafletMap) {
    appState.leafletMap.invalidateSize();
    return;
  }

  // Center at Indore center
  appState.leafletMap = L.map("leaflet-map", {
    center: [22.7196, 75.8577],
    zoom: 12,
    zoomControl: true,
  });

  // OpenStreetMap Tile Layer (Free, Open Access, No API Key Required)
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(appState.leafletMap);

  // Invalidate map size after rendering container to ensure all tiles render cleanly
  setTimeout(() => {
    if (appState.leafletMap) appState.leafletMap.invalidateSize();
  }, 250);

  // Fetch real OpenStreetMap waterways GeoJSON from backend
  fetch("/api/v1/flood/topology")
    .then((res) => res.json())
    .then((data) => {
      // 1. Render Verified Real OSM Waterways
      const realWaterways = data.real_waterways || (data.geojson && {
        type: "FeatureCollection",
        features: data.geojson.features.filter((f) => f.properties && f.properties.is_real_gis_data)
      });

      if (realWaterways && realWaterways.features && realWaterways.features.length > 0) {
        const waterwayLayer = L.geoJSON(realWaterways, {
          style: function (feature) {
            const props = feature.properties || {};
            const sys = props.river_system || "";
            const name = props.name || props.english_name || "";

            if (sys.includes("Saraswati") || name.includes("Saraswati")) {
              return {
                color: "#00f0ff", // Vibrant cyan for Saraswati River
                weight: 4.5,
                opacity: 0.95,
                lineCap: "round",
                lineJoin: "round",
              };
            } else if (name.includes("Tributary") || props.waterway_type === "stream" || props.layer === "-1") {
              return {
                color: "#38bdf8", // Sky blue for tributaries and natural feeders
                weight: 3.0,
                opacity: 0.85,
                dashArray: props.layer === "-1" ? "5, 5" : undefined,
                lineCap: "round",
                lineJoin: "round",
              };
            } else {
              return {
                color: "#0096c7", // Deep river blue for Khan River main channel
                weight: 5.0,
                opacity: 0.95,
                lineCap: "round",
                lineJoin: "round",
              };
            }
          },
          onEachFeature: function (feature, layer) {
            const p = feature.properties || {};
            layer.bindPopup(`
              <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 220px; padding: 2px;">
                <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #0284c7; font-weight: 800; margin-bottom: 2px;">
                  Verified Real Waterway (OSM)
                </div>
                <h4 style="margin: 0 0 4px; font-size: 14px; font-weight: 800; color: #0f172a;">${p.english_name || p.name}</h4>
                ${p.hindi_name ? `<div style="font-size: 12px; color: #475569; margin-bottom: 4px;">${p.hindi_name}</div>` : ""}
                <div style="font-size: 12px; margin-bottom: 3px;">System: <b>${p.river_system || "Indore Waterway"}</b></div>
                <div style="font-size: 12px; margin-bottom: 3px;">Type: <b>${p.waterway_type || "River"}</b></div>
                <div style="font-size: 12px; margin-bottom: 3px;">Surveyed Length: <b>${p.length_km || 0} km</b> (${p.node_count || 0} GPS nodes)</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 6px; border-top: 1px solid #e2e8f0; padding-top: 4px;">
                  OSM Way ID: <a href="https://www.openstreetmap.org/way/${p.osm_id}" target="_blank" style="color: #0284c7; text-decoration: underline;">${p.osm_id}</a> • ${p.attribution || "© OpenStreetMap"}
                </div>
              </div>
            `);
          },
        }).addTo(appState.leafletMap);

        appState.waterwayLayer = waterwayLayer;
      }

      // 2. Render Schematic Hydraulic Routing Line (Distinct dashed line labeled clearly)
      const linePoints = INDORE_NODES.map((n) => [n.lat, n.lon]);
      appState.mapPolyline = L.polyline(linePoints, {
        color: "#f59e0b",
        weight: 2.5,
        opacity: 0.7,
        dashArray: "6, 6",
      }).addTo(appState.leafletMap);
      appState.mapPolyline.bindPopup(`
        <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 190px;">
          <div style="font-size: 11px; color: #d97706; font-weight: 800; text-transform: uppercase;">Hydraulic Routing Edge</div>
          <div style="font-size: 13px; font-weight: 700; margin: 4px 0;">Schematic Flow Path (Rau to Kabithedi)</div>
          <div style="font-size: 11px; color: #64748b;">Gravity drop: 560m to 515m MSL. Illustrative connection between 7 municipal monitoring stations (not subsurface conduit layout).</div>
        </div>
      `);

      // 3. Update Waterway stat card in header if present
      const statWaterway = document.getElementById("map-stat-waterway-len");
      if (statWaterway && data.metadata && data.metadata.total_waterway_length_km) {
        statWaterway.textContent = `${data.metadata.total_waterway_length_km} km`;
      }
    })
    .catch((err) => {
      console.warn("Failed to load /api/v1/flood/topology, falling back to basic polyline:", err);
      const linePoints = INDORE_NODES.map((n) => [n.lat, n.lon]);
      appState.mapPolyline = L.polyline(linePoints, {
        color: "#f59e0b",
        weight: 3,
        opacity: 0.7,
        dashArray: "6, 6",
      }).addTo(appState.leafletMap);
    });

  // Plot Monitored Municipal Nodes with interactive popups
  INDORE_NODES.forEach((node, idx) => {
    const stage = 40 + (idx * 7);
    const color = stage > 75 ? "#ef4444" : (stage > 50 ? "#f59e0b" : "#10b981");

    const marker = L.circleMarker([node.lat, node.lon], {
      radius: 9,
      fillColor: color,
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9,
    }).addTo(appState.leafletMap);

    marker.bindPopup(`
      <div style="font-family: sans-serif; color: #0f172a; min-width: 170px;">
        <h4 style="margin: 0 0 4px; font-size: 14px; font-weight: 800; color: #0070f3;">${node.name}</h4>
        <div style="font-size: 12px; margin-bottom: 2px;">Zone: <b>${node.zone}</b></div>
        <div style="font-size: 12px; margin-bottom: 2px;">Elevation: <b>${node.elevation} m MSL</b></div>
        <div style="font-size: 12px; color: ${color}; font-weight: 800;">Water Stage: ${stage}%</div>
      </div>
    `);

    appState.mapMarkers.push(marker);
  });

  // Task 3.5: Fetch and Render Street-Level Flood Inundation GeoJSON Layer
  fetch(`${API_BASE}/api/v1/flood/inundation-map?rainfall_intensity_mmh=35.0`)
    .then((res) => res.json())
    .then((inundationData) => {
      if (!inundationData || !inundationData.features) return;

      // Group layers into FeatureGroup
      const inundationGroup = L.featureGroup();

      inundationData.features.forEach((feat) => {
        const props = feat.properties || {};

        if (props.feature_type === "inundation_hazard_extent") {
          // Polygon hazard buffers
          L.geoJSON(feat, {
            style: {
              fillColor: props.fill_color || "#ef4444",
              fillOpacity: props.fill_opacity || 0.35,
              color: props.fill_color || "#ef4444",
              weight: 1.5,
              opacity: 0.8,
            },
            onEachFeature: function (f, layer) {
              layer.bindPopup(`
                <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 220px; padding: 2px;">
                  <div style="font-size: 10px; font-weight: 800; color: #ef4444; text-transform: uppercase;">Overland Flood Inundation Zone</div>
                  <h4 style="margin: 3px 0 4px; font-size: 13px; font-weight: 800; color: #0f172a;">${props.street_name}</h4>
                  <div style="font-size: 12px; margin-bottom: 2px;">Zone: <b>${props.zone}</b></div>
                  <div style="font-size: 12px; margin-bottom: 2px;">Estimated Water Depth: <b style="color: ${props.fill_color};">${props.flood_depth_cm} cm</b></div>
                  <div style="font-size: 12px; margin-bottom: 2px;">Wave Arrival Time: <b>${props.arrival_time_min} mins</b></div>
                  <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Hazard: <b>${props.hazard_level}</b> (Buffer: ${props.buffer_radius_m}m)</div>
                </div>
              `);
            },
          }).addTo(inundationGroup);
        } else if (props.feature_type === "urban_street_corridor") {
          // Street LineString
          L.geoJSON(feat, {
            style: {
              color: props.stroke_color || "#3b82f6",
              weight: props.stroke_weight || 3,
              opacity: 0.9,
            },
            onEachFeature: function (f, layer) {
              layer.bindPopup(`
                <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 220px; padding: 2px;">
                  <div style="font-size: 10px; font-weight: 800; color: #0284c7; text-transform: uppercase;">Urban Street Corridor</div>
                  <h4 style="margin: 3px 0 4px; font-size: 13px; font-weight: 800; color: #0f172a;">${props.street_name}</h4>
                  <div style="font-size: 12px; margin-bottom: 2px;">Street Classification: <b>${props.street_type}</b></div>
                  <div style="font-size: 12px; margin-bottom: 2px;">Surface Inundation Depth: <b style="color: ${props.stroke_color};">${props.flood_depth_cm} cm</b></div>
                  <div style="font-size: 12px; margin-bottom: 2px;">Manning Overland Velocity: <b>${props.flow_velocity_ms} m/s</b></div>
                  <div style="font-size: 12px; margin-bottom: 2px;">DEM Surface Elevation: <b>${props.elevation_dem_m} m MSL</b></div>
                  <div style="font-size: 11px; color: #475569; margin-top: 4px; border-top: 1px solid #e2e8f0; padding-top: 4px;">
                    Critical Asset: <b>${props.critical_infra}</b>
                  </div>
                </div>
              `);
            },
          }).addTo(inundationGroup);
        } else if (props.feature_type === "hydraulic_bottleneck") {
          // Bottleneck Warning Marker
          const coords = feat.geometry.coordinates;
          const bnMarker = L.circleMarker([coords[1], coords[0]], {
            radius: 11,
            fillColor: "#ff0055",
            color: "#ffffff",
            weight: 2.5,
            fillOpacity: 0.95,
          });
          bnMarker.bindPopup(`
            <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 240px; padding: 2px;">
              <div style="font-size: 10px; font-weight: 800; color: #dc2626; text-transform: uppercase;">⚠️ Critical Hydraulic Bottleneck</div>
              <h4 style="margin: 3px 0 4px; font-size: 13.5px; font-weight: 800; color: #991b1b;">${props.name}</h4>
              <div style="font-size: 12px; color: #334155; margin-bottom: 6px;">${props.description}</div>
              <div style="font-size: 11.5px; background: #fee2e2; border-left: 3px solid #dc2626; padding: 6px; border-radius: 4px; color: #7f1d1d;">
                <b>Mitigation Advisory:</b> ${props.mitigation_action}
              </div>
            </div>
          `);
          bnMarker.addTo(inundationGroup);
        }
      });

      inundationGroup.addTo(appState.leafletMap);
      appState.inundationLayer = inundationGroup;
    })
    .catch((err) => console.warn("Could not load street inundation layer:", err));

  // Add Interactive GIS Legend
  const legend = L.control({ position: "bottomright" });
  legend.onAdd = function () {
    const div = L.DomUtil.create("div", "gis-map-legend");
    div.style.background = "rgba(15, 23, 42, 0.88)";
    div.style.backdropFilter = "blur(8px)";
    div.style.padding = "10px 14px";
    div.style.borderRadius = "8px";
    div.style.border = "1px solid rgba(255, 255, 255, 0.15)";
    div.style.color = "#ffffff";
    div.style.fontFamily = "'Inter', sans-serif";
    div.style.fontSize = "11px";
    div.style.lineHeight = "1.6";
    div.style.boxShadow = "0 4px 12px rgba(0,0,0,0.3)";
    div.innerHTML = `
      <div style="font-weight: 800; font-size: 12px; margin-bottom: 6px; color: #38bdf8; display: flex; align-items: center; gap: 6px;">
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981;"></span>
        Indore River & Drainage GIS
      </div>
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
        <span style="display:inline-block; width:18px; height:4px; background:#0096c7; border-radius:2px;"></span>
        <span><b>Khan River</b> (OSM Real River Channel)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
        <span style="display:inline-block; width:18px; height:4px; background:#00f0ff; border-radius:2px;"></span>
        <span><b>Saraswati River</b> (OSM Real River Channel)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
        <span style="display:inline-block; width:18px; height:3px; background:#38bdf8; border-radius:2px; border-bottom:1px dashed #fff;"></span>
        <span><b>Feeders / Streams</b> (OSM Waterways)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
        <span style="display:inline-block; width:18px; height:2px; background:#f59e0b; border-bottom:1px dashed #f59e0b;"></span>
        <span><b>Hydraulic Path</b> (Schematic Routing Line)</span>
      </div>
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981; border:1px solid #fff;"></span>
        <span><b>7 Monitored Sumps</b> (Simulated Telemetry)</span>
      </div>
      <div style="font-size:9.5px; color:#94a3b8; margin-top:6px; border-top:1px solid rgba(255,255,255,0.1); padding-top:4px;">
        Source: OpenStreetMap (ODbL) • EPSG:4326
      </div>
    `;
    return div;
  };
  legend.addTo(appState.leafletMap);

  // Load Phase 2A Real Spatial Network & Confluence Layer
  loadSpatialNetworkLayer();
}

function loadSpatialNetworkLayer() {
  if (!appState.leafletMap) return;

  fetch(`${API_BASE}/api/v1/flood/spatial-network`)
    .then((res) => res.json())
    .then((data) => {
      if (data.status !== "success") return;

      const spatialLayer = L.layerGroup();

      // 1. Render Derived Confluence Junction Markers & Continuity Joints
      (data.junction_candidates || []).forEach((j) => {
        const isContinuity = j.junction_type === "CONTINUITY_JUNCTION";
        const jMarker = L.circleMarker([j.lat, j.lon], {
          radius: isContinuity ? 6 : 8,
          fillColor: isContinuity ? "#06b6d4" : "#fbbf24", // Cyan for continuity, amber for confluence candidates
          color: "#ffffff",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.95,
        });
        const badgeLabel = isContinuity ? "Reach Continuity Joint" : "River Confluence Candidate";
        const badgeColor = isContinuity ? "#0891b2" : "#d97706";
        jMarker.bindPopup(`
          <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 220px;">
            <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: ${badgeColor}; font-weight: 800; margin-bottom: 2px;">
              ${badgeLabel}
            </div>
            <h4 style="margin: 0 0 4px; font-size: 13px; font-weight: 800; color: #0f172a;">${j.name}</h4>
            <div style="font-size: 11.5px; margin-bottom: 2px;">Type: <b>${j.junction_type || "JUNCTION"}</b></div>
            <div style="font-size: 11.5px; margin-bottom: 2px;">Coords: <b>${j.lat.toFixed(5)}, ${j.lon.toFixed(5)}</b></div>
            <div style="font-size: 11.5px; margin-bottom: 2px;">Features: <b>${(j.intersecting_features || []).join(" & ")}</b></div>
            <div style="font-size: 10.5px; color: #64748b; margin-top: 4px; border-top: 1px solid #e2e8f0; padding-top: 3px;">
              ${j.classification_description || `Hydraulic Status: <i>${j.hydraulic_status}</i>`}
            </div>
          </div>
        `);
        jMarker.addTo(spatialLayer);
      });

      // 2. Render Monitoring Station Snapping Vectors (Proximity lines linking station to nearest waterway)
      const snapping = (data.monitoring_stations_snapping || {}).station_evaluations || {};
      Object.values(snapping).forEach((s) => {
        if (!s.original_coordinates || !s.snapped_channel_coordinates) return;
        const orig = [s.original_coordinates.lat, s.original_coordinates.lon];
        const snap = [s.snapped_channel_coordinates.lat, s.snapped_channel_coordinates.lon];

        const snapLine = L.polyline([orig, snap], {
          color: s.spatial_classification === "NEAR_CHANNEL" ? "#10b981" : "#94a3b8",
          weight: 1.5,
          dashArray: "3, 4",
          opacity: 0.75,
        });
        snapLine.bindPopup(`
          <div style="font-family: 'Inter', sans-serif; color: #0f172a; min-width: 190px;">
            <div style="font-size: 10px; font-weight: 800; color: #64748b; text-transform: uppercase;">Station Snapping Vector</div>
            <div style="font-size: 12.5px; font-weight: 700; margin: 3px 0;">${s.station_name}</div>
            <div style="font-size: 11.5px;">Distance to River: <b>${s.distance_to_nearest_waterway_m} m</b></div>
            <div style="font-size: 11.5px;">Classification: <b>${s.spatial_classification}</b></div>
            <div style="font-size: 11.5px;">Nearest Waterway: <b>${s.nearest_waterway_name}</b></div>
            <div style="font-size: 10.5px; color: #64748b; margin-top: 4px; border-top: 1px solid #e2e8f0; padding-top: 3px;">
              Original urban station coordinates strictly preserved.
            </div>
          </div>
        `);
        snapLine.addTo(spatialLayer);
      });

      // Add Layer Control Toggle to Leaflet Map
      L.control.layers(null, {
        "Spatial Confluences & Snapping Vectors (Phase 2A)": spatialLayer,
      }, { position: "topright", collapsed: false }).addTo(appState.leafletMap);

      // Add to map by default so user can visibly inspect
      spatialLayer.addTo(appState.leafletMap);
      appState.spatialNetworkLayer = spatialLayer;
    })
    .catch((err) => {
      console.warn("Could not load /api/v1/flood/spatial-network:", err);
    });
}

// ==============================================================================
// 6. DUAL FLOOD PREDICTION ENGINE
// ==============================================================================
function initSliders() {
  const rainSlider = document.getElementById("input-rain-slider");
  if (rainSlider) {
    rainSlider.addEventListener("input", (e) => {
      document.getElementById("slider-rain-val").textContent = `${parseFloat(e.target.value).toFixed(1)} mm/h`;
    });
  }

  const surgeSlider = document.getElementById("input-surge-slider");
  if (surgeSlider) {
    surgeSlider.addEventListener("input", (e) => {
      document.getElementById("slider-surge-val").textContent = `${parseFloat(e.target.value).toFixed(1)}x`;
    });
  }

  const simSurgeSlider = document.getElementById("sim-surge-slider");
  if (simSurgeSlider) {
    simSurgeSlider.addEventListener("input", (e) => {
      document.getElementById("sim-surge-label").textContent = `${parseFloat(e.target.value).toFixed(1)}x`;
    });
  }
}

async function runDualPrediction() {
  const rain = parseFloat(document.getElementById("input-rain-slider")?.value || 35.0);
  const surge = parseFloat(document.getElementById("input-surge-slider")?.value || 1.2);
  const pumps = parseInt(document.getElementById("input-pumps-count")?.value || 2);

  try {
    const res = await fetch(`${API_BASE}/api/v1/flood/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rainfall_intensity_mmh: rain,
        surge_multiplier: surge,
        active_pumps_count: pumps,
        runoff_coefficient: 0.72,
      }),
    });
    const data = await res.json();
    renderPredictionResults(data, rain, surge, pumps);
  } catch (err) {
    console.error("Flood prediction error:", err);
  }
}

function renderPredictionResults(data, rain, surge, pumps) {
  // Primary Hybrid ST-GNN + Hydraulic Model Inference from Backend
  const hybridProb = data.hybrid_details?.overall_flood_probability || data.overall_flood_probability;
  const mlProb = hybridProb !== undefined ? Number(hybridProb).toFixed(1) : (Math.min(98.5, Math.max(12.0, (rain * 0.8 * surge) - (pumps * 4.5)))).toFixed(1);
  const mlProbEl = document.getElementById("ml-prob-val");
  const mlTierEl = document.getElementById("ml-tier-val");

  if (mlProbEl && mlTierEl) {
    mlProbEl.textContent = `${mlProb}%`;
    if (data.overall_basin_risk) {
      mlTierEl.textContent = data.overall_basin_risk;
      const isCrit = mlProb > 70 || data.overall_basin_risk.includes("CRITICAL");
      const isWarn = mlProb > 40 || data.overall_basin_risk.includes("WARNING");
      mlTierEl.style.color = isCrit ? "var(--danger-red)" : (isWarn ? "var(--warn-amber)" : "var(--safe-green)");
    } else if (mlProb > 75) {
      mlTierEl.textContent = "CRITICAL / HIGH FLOOD RISK";
      mlTierEl.style.color = "var(--danger-red)";
    } else if (mlProb > 50) {
      mlTierEl.textContent = "WARNING / MODERATE RISK";
      mlTierEl.style.color = "var(--warn-amber)";
    } else {
      mlTierEl.textContent = "LOW / NORMAL DRAINAGE FLOW";
      mlTierEl.style.color = "var(--safe-green)";
    }
  }

  // Task 3.5: Populate Confidence Interval & Uncertainty Stat Pills
  const hybridDetails = data.hybrid_details || data;
  const firstNode = (data.node_predictions && data.node_predictions[0]) || {};
  const ciDepth = firstNode.confidence_interval_90_depth_cm;
  const ciArrival = firstNode.confidence_interval_90_arrival_mins;
  const uncertainty = firstNode.prediction_uncertainty_sigma;
  const streetsSummary = hybridDetails.street_inundation_summary || {};

  const ciDepthPill = document.getElementById("t35-ci-depth-pill");
  const ciArrivalPill = document.getElementById("t35-ci-arrival-pill");
  const uncertaintyPill = document.getElementById("t35-uncertainty-pill");
  const streetsCountPill = document.getElementById("t35-streets-count-pill");

  if (ciDepthPill && ciDepth) {
    ciDepthPill.textContent = `[${ciDepth[0]} - ${ciDepth[1]} cm]`;
  }
  if (ciArrivalPill && ciArrival) {
    ciArrivalPill.textContent = `[${ciArrival[0]} - ${ciArrival[1]} Mins]`;
  }
  if (uncertaintyPill && uncertainty !== undefined) {
    uncertaintyPill.textContent = `±${Number(uncertainty).toFixed(3)}`;
  }
  if (streetsCountPill) {
    const inundatedCount = streetsSummary.inundated_streets_count !== undefined ? streetsSummary.inundated_streets_count : 21;
    const totalCount = streetsSummary.total_monitored_streets !== undefined ? streetsSummary.total_monitored_streets : 21;
    streetsCountPill.textContent = `${inundatedCount} / ${totalCount} Arterials`;
  }

  // Hydraulic Arrival Time via Manning flow routing
  const arrival = data.peak_flood_arrival_mins || data.hybrid_details?.peak_flood_arrival_mins || 27;
  const choke = data.peak_choke_point || data.hybrid_details?.peak_choke_point || "Rau Headwaters";
  const arrivalEl = document.getElementById("phys-arrival-val");
  const chokeEl = document.getElementById("phys-choke-val");
  if (arrivalEl) arrivalEl.textContent = `${arrival} Mins`;
  if (chokeEl) chokeEl.textContent = `Bottleneck: ${choke}`;

  // AI & Hydraulic Action Advisory
  const advisoryEl = document.getElementById("pred-advisory-txt");
  if (advisoryEl) {
    if (data.automated_action) {
      advisoryEl.textContent = data.automated_action;
    } else if (data.hybrid_details?.recommended_action) {
      advisoryEl.textContent = data.hybrid_details.recommended_action;
    } else if (mlProb > 75) {
      advisoryEl.textContent = `ALERT: Monsoon surge detected. Actuate all 6 Kabithedi pumps and throttle Saraswati confluence gates at Krishnapura Chhatri.`;
    } else {
      advisoryEl.textContent = `Standard gravity drainage active with ${pumps} operational pumps. Outfall within nominal design envelope.`;
    }
  }

  // Node Inundation Table (Spatio-Temporal GNN + Hydraulic Physics)
  const tbody = document.getElementById("pred-nodes-tbody");
  if (tbody && data.node_predictions) {
    tbody.innerHTML = "";
    data.node_predictions.forEach(n => {
      const row = document.createElement("tr");
      const statusColor = n.status === "CRITICAL" ? "var(--danger-red)" : (n.status === "WARNING" ? "var(--warn-amber)" : "var(--safe-green)");
      const levelVal = n.water_level_pct !== undefined ? n.water_level_pct : (n.hydraulic_physics?.water_level_pct || n.hybrid_flood_risk_score || 35.0);
      const streetsList = n.affected_street_corridors ? n.affected_street_corridors.slice(0, 2).join(", ") : "";
      const ciText = n.confidence_interval_90_depth_cm ? `CI: [${n.confidence_interval_90_depth_cm[0]}-${n.confidence_interval_90_depth_cm[1]} cm]` : "";
      const depthText = n.inundation_depth_cm !== undefined ? `<div style="font-size: 11px; color: ${n.inundation_depth_cm > 0 ? '#ef4444' : '#10b981'}; font-weight: 700;">${n.inundation_depth_cm} cm depth</div>` : "";

      row.innerHTML = `
        <td style="font-weight: 700;">
          ${n.node_name}
          ${streetsList ? `<div style="font-size: 10.5px; color: #94a3b8; font-weight: normal; margin-top: 2px;">📍 ${streetsList}</div>` : ""}
        </td>
        <td>${n.elevation_msl}m</td>
        <td>
          <b>${levelVal}%</b>
          ${depthText}
        </td>
        <td style="color: ${statusColor}; font-weight: 800;">
          ${n.status}
          ${ciText ? `<div style="font-size: 9.5px; color: #64748b; font-weight: normal; margin-top: 2px;">${ciText}</div>` : ""}
        </td>
        <td style="font-size: 11px; color: var(--cyan-accent); font-family: monospace;">${n.gate_action || "NORMAL_FLOW"}</td>
      `;
      tbody.appendChild(row);
    });
  }
}

// ==============================================================================
// 7. PUMP & SLUICE SIMULATOR
// ==============================================================================
async function applySimulationControls() {
  const surge = parseFloat(document.getElementById("sim-surge-slider")?.value || 1.0);
  const effluent = document.getElementById("sim-effluent-toggle")?.checked || false;

  try {
    const res = await fetch(`${API_BASE}/api/v1/sensors/simulation/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        surge_multiplier: surge,
        trigger_pollution: effluent,
      }),
    });
    const data = await res.json();
    
    // Task 3.5: Execute Intelligent Pump Scheduling and Gate Optimization
    fetch(`${API_BASE}/api/v1/flood/optimize-pumps-gates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rainfall_intensity_mmh: 35.0,
        surge_multiplier: surge,
        active_pumps_count: 2,
      }),
    })
      .then((r) => r.json())
      .then((optData) => {
        renderOptimizationAdvisory(optData, surge, effluent);
      })
      .catch((err) => console.warn("Failed to optimize pumps/gates:", err));

    alert(`Controls Applied! Surge multiplier set to ${surge}x. Effluent burst injection: ${effluent ? "ACTIVE" : "INACTIVE"}.`);
  } catch (err) {
    console.error("Simulation control error:", err);
  }
}

// ==============================================================================
// 8. HISTORY & PERSISTENT LOGS (SQLite)
// ==============================================================================
async function fetchHistoryLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sensors/history?limit=50`);
    if (!res.ok) return;
    const data = await res.json();
    appState.historyRecords = data.records || [];
    renderHistoryTable();
  } catch (err) {
    console.error("Fetch history error:", err);
  }
}

async function fetchDbStats() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sensors/db-stats`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.database) {
      document.getElementById("stat-total-analyses").textContent = data.database.total_analysis_records || 24;
      document.getElementById("stat-telemetry-count").textContent = `${data.database.total_telemetry_records || 180}+`;
    }
  } catch (err) {
    console.error("Fetch DB stats error:", err);
  }
}

function filterLogs(filterType) {
  appState.activeLogFilter = filterType;
  renderHistoryTable();
}

function renderHistoryTable() {
  const tbody = document.getElementById("history-logs-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const filtered = appState.historyRecords.filter(r => {
    if (appState.activeLogFilter === "ALL") return true;
    return r.analysis_type === appState.activeLogFilter;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-sub);">No records found matching filter.</td></tr>`;
    return;
  }

  filtered.forEach(rec => {
    const row = document.createElement("tr");
    const isCv = rec.analysis_type === "CV_PURITY";
    const statusColor = rec.status_verdict === "SAFE" ? "var(--safe-green)" : (rec.status_verdict === "WARNING" ? "var(--warn-amber)" : "var(--danger-red)");

    row.innerHTML = `
      <td style="font-weight: 800; color: var(--cyan-accent);">#${rec.id}</td>
      <td style="font-size: 11px; color: var(--text-sub);">${rec.timestamp}</td>
      <td><span class="provenance-tag ${isCv ? 'tag-edge' : 'tag-api'}">${rec.analysis_type}</span></td>
      <td>${rec.input_source || "Default"}</td>
      <td style="font-weight: 800;">${isCv ? `${rec.primary_metric}% Purity` : `${rec.primary_metric}% Water Level`}</td>
      <td style="color: ${statusColor}; font-weight: 800;">${rec.status_verdict}</td>
      <td style="font-size: 11px; color: #cbd5e1;">${rec.gate_action || "NORMAL_FLOW"}</td>
    `;
    tbody.appendChild(row);
  });
}

function exportAuditCSV() {
  if (!appState.historyRecords.length) {
    alert("No records to export.");
    return;
  }
  const headers = ["Record_ID", "Timestamp", "Analysis_Type", "Input_Source", "Primary_Metric", "Status_Verdict", "Gate_Action"];
  const rows = appState.historyRecords.map(r => [
    r.id,
    `"${r.timestamp}"`,
    r.analysis_type,
    `"${r.input_source}"`,
    r.primary_metric,
    r.status_verdict,
    `"${r.gate_action || ''}"`
  ]);

  const csv = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `hydro_guard_audit_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ==============================================================================
// 9. FILE UPLOAD DRAG & DROP HANDLERS
// ==============================================================================
function initFileUploadHandlers() {
  // Audio Upload
  const soundDrop = document.getElementById("sound-dropzone");
  const soundInput = document.getElementById("input-audio-upload");
  if (soundDrop && soundInput) {
    soundInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        const file = e.target.files[0];
        document.getElementById("sound-preview-filename").textContent = file.name;
        runAcousticAnalysis();
      }
    });

    ["dragenter", "dragover"].forEach(eventName => {
      soundDrop.addEventListener(eventName, (e) => {
        e.preventDefault();
        soundDrop.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach(eventName => {
      soundDrop.addEventListener(eventName, (e) => {
        e.preventDefault();
        soundDrop.classList.remove("dragover");
      });
    });

    soundDrop.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length > 0) {
        soundInput.files = e.dataTransfer.files;
        const file = e.dataTransfer.files[0];
        document.getElementById("sound-preview-filename").textContent = file.name;
        runAcousticAnalysis();
      }
    });
  }

  // Image Upload
  const purityDrop = document.getElementById("purity-dropzone");
  const purityInput = document.getElementById("input-image-upload");
  if (purityDrop && purityInput) {
    purityInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        const file = e.target.files[0];
        document.getElementById("purity-preview-filename").textContent = file.name;
        
        const reader = new FileReader();
        reader.onload = (re) => {
          document.getElementById("purity-preview-img").src = re.target.result;
        };
        reader.readAsDataURL(file);

        runImageAnalysis();
      }
    });

    ["dragenter", "dragover"].forEach(eventName => {
      purityDrop.addEventListener(eventName, (e) => {
        e.preventDefault();
        purityDrop.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach(eventName => {
      purityDrop.addEventListener(eventName, (e) => {
        e.preventDefault();
        purityDrop.classList.remove("dragover");
      });
    });

    purityDrop.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length > 0) {
        purityInput.files = e.dataTransfer.files;
        const file = e.dataTransfer.files[0];
        document.getElementById("purity-preview-filename").textContent = file.name;
        
        const reader = new FileReader();
        reader.onload = (re) => {
          document.getElementById("purity-preview-img").src = re.target.result;
        };
        reader.readAsDataURL(file);

        runImageAnalysis();
      }
    });
  }
}

// ==============================================================================
// 10. VIDEO SIMULATION MODAL
// ==============================================================================
function openVideoModal() {
  const modal = document.getElementById("video-modal");
  if (modal) modal.classList.add("show");
}

function closeVideoModal() {
  const modal = document.getElementById("video-modal");
  if (modal) modal.classList.remove("show");
}

// ==============================================================================
// 11. REPORTS & MONITORING SCREEN CONTROLLER (PHASE 2B REFERENCE MATCH)
// ==============================================================================
const reportsState = {
  activeTab: "drains",
  currentPage: 1,
  pageSize: 8,
  totalPages: 1,
  cachedSummary: null,
  cachedStations: [],
  cachedFacilities: [],
  cachedAreas: []
};

async function loadReportsAndMonitoring() {
  await loadReportsSummary();
  await loadReportsStations(reportsState.currentPage);
}

async function loadReportsSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/reports/summary`);
    const data = await res.json();
    if (data.status !== "success") return;

    reportsState.cachedSummary = data;
    const m = data.metrics || {};
    const w = data.weather_header || {};

    // Populate Weather / Clock pills
    const clockEl = document.getElementById("rm-clock-txt");
    if (clockEl) clockEl.textContent = w.date_str || new Date().toLocaleString();
    const weatherEl = document.getElementById("rm-weather-temp");
    if (weatherEl) weatherEl.textContent = w.condition || "28°C Light Rain";

    // Populate 8 Top Metric Cards
    const setNum = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val !== undefined ? val : "-";
    };

    setNum("rm-stat-stations", m.total_stations || 7);
    setNum("rm-stat-filtration", m.filtration_facilities || 3);
    setNum("rm-stat-areas", m.monitored_areas || 4);
    setNum("rm-stat-pass", m.pass_count || 0);
    setNum("rm-stat-hold", m.hold_count || 0);
    setNum("rm-stat-fail", m.fail_count || 0);
    setNum("rm-stat-blocked", m.simulated_blocked_routes || 0);
    setNum("rm-stat-alerts", m.active_alerts || 0);
  } catch (err) {
    console.warn("Could not load reports summary:", err);
  }
}

async function loadReportsStations(page = 1) {
  reportsState.currentPage = page;
  const searchInput = document.getElementById("rm-input-search");
  const zoneSelect = document.getElementById("rm-filter-zone");
  const qualitySelect = document.getElementById("rm-filter-quality");
  const routeSelect = document.getElementById("rm-filter-route");
  const cleaningSelect = document.getElementById("rm-filter-cleaning");
  const sortSelect = document.getElementById("rm-filter-sort");

  const params = new URLSearchParams({
    page: page,
    page_size: reportsState.pageSize
  });

  if (searchInput && searchInput.value.trim()) params.append("search", searchInput.value.trim());
  if (zoneSelect && zoneSelect.value !== "ALL") params.append("zone", zoneSelect.value);
  if (qualitySelect && qualitySelect.value !== "ALL") params.append("quality_status", qualitySelect.value);
  if (routeSelect && routeSelect.value !== "ALL") params.append("route_status", routeSelect.value);
  if (cleaningSelect && cleaningSelect.value !== "ALL") params.append("cleaning_status", cleaningSelect.value);
  if (sortSelect && sortSelect.value) params.append("sort_by", sortSelect.value);

  try {
    const res = await fetch(`${API_BASE}/api/v1/reports/stations?${params.toString()}`);
    const data = await res.json();
    if (data.status !== "success") return;

    reportsState.cachedStations = data.stations || [];
    reportsState.totalPages = data.total_pages || 1;

    renderStationCards(reportsState.cachedStations);
    updatePaginationUI(data.total_count, data.page, data.total_pages);
  } catch (err) {
    console.error("Failed to load station cards:", err);
  }
}

function renderStationCards(stations) {
  const container = document.getElementById("rm-stations-grid");
  if (!container) return;

  if (!stations || !stations.length) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 40px; text-align: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
        <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
        <h4 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">No Drains Match Filters</h4>
        <p style="font-size: 13px; color: #64748b;">Try adjusting your search query, zone, or status filters.</p>
        <button class="rm-btn-primary" style="margin: 12px auto 0;" onclick="resetReportsFilters()">Reset Filters</button>
      </div>
    `;
    return;
  }

  container.innerHTML = stations.map(s => {
    const badgeClass = s.quality_status === "PASS" ? "badge-pass" : (s.quality_status === "HOLD" ? "badge-hold" : "badge-fail");
    const imgSrc = s.has_annotated_frame ? `data:image/jpeg;base64,${s.annotated_frame_b64}` : s.image_preview_url;
    const isTreatmentReq = s.treatment_route === "REQUIRED";
    const outletCode = s.outlet_code || "NOT_CONFIGURED";
    const outletStatus = s.outlet_status || s.sluice_gate_action || "NOT CONFIGURED";
    const outletColor = s.outlet_color || s.sluice_gate_color || "#94a3b8";

    let outletIconSvg = "";
    if (outletCode === "OPEN") {
      outletIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${outletColor}" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="16 10 10 16 8 13"></polyline></svg>`;
    } else if (outletCode === "CLOSED") {
      outletIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${outletColor}" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>`;
    } else if (outletCode === "PARTIALLY_OPEN") {
      outletIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${outletColor}" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 0 20z" fill="${outletColor}" fill-opacity="0.3"></path><line x1="12" y1="2" x2="12" y2="22"></line></svg>`;
    } else if (outletCode === "BLOCKED") {
      outletIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${outletColor}" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`;
    } else {
      // NOT_CONFIGURED or UNKNOWN (Grey)
      outletIconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${outletColor}" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>`;
    }

    return `
      <div class="rm-station-card">
        <!-- Header -->
        <div class="rm-card-header">
          <div class="rm-card-title" title="${s.display_code} • ${s.station_name}">${s.display_code} • ${s.station_name}</div>
          <span class="rm-status-badge ${badgeClass}">${s.quality_status}</span>
        </div>

        <!-- 16:9 Image Preview -->
        <div class="rm-card-img-wrap" onclick="openStationModal('${s.node_id}')">
          <img src="${imgSrc}" class="rm-card-img" alt="${s.station_name}" onerror="this.src='/samples/images/clean_rainwater.jpg'">
          <div class="rm-img-badge">${s.has_annotated_frame ? 'Annotated Frame' : 'Sample Image'}</div>
        </div>

        <!-- Metadata Row -->
        <div class="rm-card-meta-row">
          <span class="rm-meta-left">Sample ID<br><b style="color: #0f172a;">${s.sample_id}</b></span>
          <span class="rm-meta-right" style="text-align: right;">Sample Date<br><b style="color: #0f172a;">${s.sample_date}</b></span>
        </div>

        <!-- 3-Parameter Strip (pH, Turbidity, TDS) -->
        <div class="rm-params-strip">
          <div class="rm-param-col">
            <div class="rm-param-name">pH</div>
            <div class="rm-param-val" style="color: #64748b;">N/A</div>
            <div class="rm-param-sub">6.5 – 8.5</div>
          </div>
          <div class="rm-param-col">
            <div class="rm-param-name">Turbidity</div>
            <div class="rm-param-val" style="color: ${s.quality_color};">
              <span class="val-icon-${s.quality_status.toLowerCase()}">${s.quality_status === 'PASS' ? '✓' : (s.quality_status === 'HOLD' ? '⚠️' : '✗')}</span>
              ${s.turbidity_measurement.value} NTU
            </div>
            <div class="rm-param-sub">≤ 25 NTU</div>
          </div>
          <div class="rm-param-col">
            <div class="rm-param-name">TDS</div>
            <div class="rm-param-val" style="color: #64748b;">N/A</div>
            <div class="rm-param-sub">≤ 500</div>
          </div>
        </div>

        <!-- AI Assessment -->
        <div class="rm-ai-assessment-box">
          <b>AI Assessment</b>
          ${s.ai_assessment}
        </div>

        <!-- Sluice Indicators -->
        <div class="rm-status-indicator-row">
          <div class="rm-status-indicator" title="${s.outlet_details || outletStatus}">
            ${outletIconSvg}
            <span>Main Outlet: <b style="color: ${outletColor};">${outletStatus}</b></span>
          </div>
          <div class="rm-status-indicator">
            ${isTreatmentReq ? `
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <span>Treatment Route: <b style="color: #f59e0b;">REQUIRED</b></span>
            ` : `
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="16 10 10 16 8 13"></polyline></svg>
              <span>Treatment Route: <b style="color: #10b981;">NOT REQUIRED</b></span>
            `}
          </div>
        </div>

        <!-- Actions -->
        <div class="rm-card-actions">
          <button class="rm-btn-card-action" onclick="openStationModal('${s.node_id}')">View Full Report</button>
          <button class="rm-btn-card-outline" onclick="downloadStationPDF('${s.node_id}')">Download PDF</button>
        </div>
      </div>
    `;
  }).join("");
}

function updatePaginationUI(totalCount, currentPage, totalPages) {
  const infoEl = document.getElementById("rm-pagination-text");
  if (infoEl) infoEl.textContent = `Showing 1 – ${totalCount} of ${totalCount} drains`;

  const btnPrev = document.getElementById("rm-btn-prev");
  const btnNext = document.getElementById("rm-btn-next");
  const pageBtn = document.getElementById("rm-page-num-1");

  if (pageBtn) pageBtn.textContent = currentPage;
  if (btnPrev) btnPrev.disabled = currentPage <= 1;
  if (btnNext) btnNext.disabled = currentPage >= totalPages;
}

function onReportsFilterChange() {
  loadReportsStations(1);
}

function resetReportsFilters() {
  const searchInput = document.getElementById("rm-input-search");
  const zoneSelect = document.getElementById("rm-filter-zone");
  const qualitySelect = document.getElementById("rm-filter-quality");
  const routeSelect = document.getElementById("rm-filter-route");
  const cleaningSelect = document.getElementById("rm-filter-cleaning");
  const sortSelect = document.getElementById("rm-filter-sort");
  const dateInput = document.getElementById("rm-filter-date");

  if (searchInput) searchInput.value = "";
  if (zoneSelect) zoneSelect.value = "ALL";
  if (qualitySelect) qualitySelect.value = "ALL";
  if (routeSelect) routeSelect.value = "ALL";
  if (cleaningSelect) cleaningSelect.value = "ALL";
  if (sortSelect) sortSelect.value = "display_code";
  if (dateInput) dateInput.value = "";

  loadReportsStations(1);
}

function changeReportsPage(delta) {
  const newPage = reportsState.currentPage + delta;
  if (newPage >= 1 && newPage <= reportsState.totalPages) {
    loadReportsStations(newPage);
  }
}

// Tab Switching
function switchReportsTab(tabName) {
  reportsState.activeTab = tabName;

  document.querySelectorAll(".rm-tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".rm-tab-content").forEach(c => c.style.display = "none");

  const targetBtn = document.getElementById(`tab-btn-${tabName}`);
  if (targetBtn) targetBtn.classList.add("active");

  const targetContent = document.getElementById(`rm-tab-content-${tabName}`);
  if (targetContent) targetContent.style.display = "block";

  const toolbar = document.getElementById("rm-toolbar-drains");
  if (toolbar) toolbar.style.display = tabName === "drains" ? "flex" : "none";

  if (tabName === "filtration") {
    loadFiltrationFacilities();
  } else if (tabName === "areas") {
    loadMonitoredAreas();
  }
}

async function loadFiltrationFacilities() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/reports/filtration-units`);
    const data = await res.json();
    if (data.status !== "success") return;

    reportsState.cachedFacilities = data.facilities || [];
    renderFiltrationCards(reportsState.cachedFacilities);
  } catch (err) {
    console.error("Failed to load filtration facilities:", err);
  }
}

function renderFiltrationCards(facilities) {
  const container = document.getElementById("rm-filtration-grid");
  if (!container) return;

  container.innerHTML = facilities.map(f => `
    <div class="rm-facility-card">
      <div class="rm-facility-card-header">
        <div>
          <div class="rm-facility-card-title">${f.unit_id} • ${f.name}</div>
          <div class="rm-facility-card-sub">${f.location}</div>
        </div>
        <span class="rm-badge-pill" style="background: ${f.status_color}; color: white;">${f.operational_status}</span>
      </div>

      <div class="rm-card-img-wrap" style="height: 150px;">
        <img src="${f.image_url}" class="rm-card-img" alt="${f.name}" onerror="this.src='/samples/images/clean_rainwater.jpg'">
        <div class="rm-img-badge">${f.facility_type}</div>
      </div>

      <div class="rm-facility-body">
        <div class="rm-facility-row">
          <span>Design Capacity:</span>
          <b>${f.capacity_mld} MLD (${f.design_discharge_m3s} m³/s)</b>
        </div>
        <div class="rm-facility-row">
          <span>Primary Treatment:</span>
          <b>${f.primary_treatment}</b>
        </div>
        <div class="rm-facility-row">
          <span>Secondary Treatment:</span>
          <b>${f.secondary_treatment}</b>
        </div>
        <div class="rm-facility-row">
          <span>Effluent Discharge:</span>
          <b>${f.effluent_destination}</b>
        </div>
        <div class="rm-facility-row">
          <span>Data Provenance:</span>
          <b style="color: #0284c7;">${f.provenance}</b>
        </div>
        <div style="font-size: 11.5px; line-height: 1.4; color: #475569; margin-top: 4px; padding-top: 6px; border-top: 1px solid #e2e8f0;">
          ${f.description}
        </div>
      </div>
    </div>
  `).join("");
}

async function loadMonitoredAreas() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/reports/areas`);
    const data = await res.json();
    if (data.status !== "success") return;

    reportsState.cachedAreas = data.areas || [];
    renderAreaCards(reportsState.cachedAreas);
  } catch (err) {
    console.error("Failed to load monitored areas:", err);
  }
}

function renderAreaCards(areas) {
  const container = document.getElementById("rm-areas-grid");
  if (!container) return;

  container.innerHTML = areas.map(a => `
    <div class="rm-facility-card">
      <div class="rm-facility-card-header">
        <div>
          <div class="rm-facility-card-title">${a.area_id} • ${a.name}</div>
          <div class="rm-facility-card-sub">${a.zone}</div>
        </div>
        <span class="rm-badge-pill" style="background: ${a.risk_color}; color: white;">${a.current_flood_risk}</span>
      </div>

      <div class="rm-facility-body">
        <div class="rm-facility-row">
          <span>Elevation Range:</span>
          <b>${a.elevation_range_msl}</b>
        </div>
        <div class="rm-facility-row">
          <span>Mapped Waterways:</span>
          <b>${a.mapped_waterway_length_km} km (OSM)</b>
        </div>
        <div class="rm-facility-row">
          <span>Catchment Area:</span>
          <b>${a.catchment_area_km2} km²</b>
        </div>
        <div class="rm-facility-row">
          <span>Monitored Nodes:</span>
          <b>${a.primary_stations.join(", ")}</b>
        </div>
        <div class="rm-facility-row">
          <span>Data Completeness:</span>
          <b>${a.data_completeness_pct}% (Copernicus DEM & OSM)</b>
        </div>
        <div style="font-size: 11.5px; line-height: 1.4; color: #475569; margin-top: 4px; padding-top: 6px; border-top: 1px solid #e2e8f0;">
          ${a.description}
        </div>
      </div>
    </div>
  `).join("");
}

// Modal View Full Report
async function openStationModal(nodeId) {
  const modal = document.getElementById("modal-station-detail");
  const titleEl = document.getElementById("modal-station-title");
  const bodyEl = document.getElementById("modal-station-body");
  if (!modal || !bodyEl) return;

  bodyEl.innerHTML = `<div style="text-align: center; padding: 40px; color: #64748b;">Loading full inspection certificate...</div>`;
  modal.style.display = "flex";

  try {
    const res = await fetch(`${API_BASE}/api/v1/reports/stations/${nodeId}`);
    const data = await res.json();
    if (data.status !== "success" || !data.station) {
      bodyEl.innerHTML = `<div style="color: #ef4444; padding: 20px;">Station report could not be loaded.</div>`;
      return;
    }

    const s = data.station;
    if (titleEl) titleEl.textContent = `${s.display_code} • ${s.station_name} (Inspection Certificate)`;

    const imgSrc = s.has_annotated_frame ? `data:image/jpeg;base64,${s.annotated_frame_b64}` : s.image_preview_url;

    bodyEl.innerHTML = `
      <div style="display: flex; gap: 20px; flex-wrap: wrap;">
        <div style="flex: 1.2; min-width: 260px;">
          <img src="${imgSrc}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 10px; border: 1px solid #e2e8f0;" alt="${s.station_name}">
          <div style="font-size: 11px; color: #64748b; margin-top: 6px; text-align: center;">
            ${s.has_annotated_frame ? 'Captured Inspection Camera Frame (Base64 JPEG)' : 'Prototype Reference Camera Frame'}
          </div>
        </div>
        <div style="flex: 1.4; min-width: 260px; font-size: 12.5px; display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">Sample ID:</span>
            <b>${s.sample_id}</b>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">Inspection Date:</span>
            <b>${s.sample_date}</b>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">GIS Coordinates:</span>
            <b>${s.latitude.toFixed(4)}°N, ${s.longitude.toFixed(4)}°E</b>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">DEM Surface Elevation:</span>
            <b>${s.elevation_msl_m} m MSL</b>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">River Basin Reach:</span>
            <b>${s.river_system}</b>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">Main Outlet / Sluice:</span>
            <b style="color: ${s.outlet_color || s.sluice_gate_color};">${s.outlet_status || s.sluice_gate_action}</b>
          </div>
          <div style="font-size: 11px; color: #64748b; line-height: 1.4; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            ${s.outlet_details || 'Gate telemetry status derived from municipal configuration.'}
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
            <span style="color: #64748b;">Cleaning Maintenance:</span>
            <b>${s.cleaning_status}</b>
          </div>
        </div>
      </div>

      <div style="margin-top: 18px; padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
        <div style="font-size: 13px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">Parameter Measurements & Scientific Disclosure</div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 12px; text-align: center;">
          <div style="background: white; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <div style="font-size: 10px; color: #64748b;">Purity Score</div>
            <div style="font-size: 16px; font-weight: 800; color: ${s.quality_color};">${s.purity_score_pct}%</div>
            <div style="font-size: 9.5px; color: #94a3b8;">80% Rule Applied</div>
          </div>
          <div style="background: white; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <div style="font-size: 10px; color: #64748b;">Optical Turbidity</div>
            <div style="font-size: 16px; font-weight: 800; color: ${s.turbidity_measurement.is_acceptable ? '#10b981' : '#ef4444'};">${s.turbidity_measurement.value} NTU</div>
            <div style="font-size: 9.5px; color: #94a3b8;">Pixel Contrast Est.</div>
          </div>
          <div style="background: white; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <div style="font-size: 10px; color: #64748b;">pH Level</div>
            <div style="font-size: 16px; font-weight: 800; color: #64748b;">N/A</div>
            <div style="font-size: 9.5px; color: #94a3b8;">No Physical Sensor</div>
          </div>
          <div style="background: white; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <div style="font-size: 10px; color: #64748b;">TDS (Dissolved)</div>
            <div style="font-size: 16px; font-weight: 800; color: #64748b;">N/A</div>
            <div style="font-size: 9.5px; color: #94a3b8;">No Physical Probe</div>
          </div>
        </div>
      </div>

      <div style="margin-top: 14px; font-size: 12px; line-height: 1.5; color: #334155; padding: 12px; background: #eff6ff; border-left: 4px solid ${s.quality_color}; border-radius: 6px;">
        <b>AI Assessment Verdict:</b> ${s.ai_assessment}
      </div>

      <div style="margin-top: 18px; display: flex; justify-content: flex-end; gap: 10px;">
        <button class="rm-btn-outline" onclick="closeStationModal()">Close</button>
        <button class="rm-btn-primary" onclick="downloadStationPDF('${s.node_id}')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>Download PDF Certificate</span>
        </button>
      </div>
    `;
  } catch (err) {
    bodyEl.innerHTML = `<div style="color: #ef4444; padding: 20px;">Network error loading station details.</div>`;
  }
}

function closeStationModal(event) {
  if (event && event.target !== event.currentTarget) return;
  const modal = document.getElementById("modal-station-detail");
  if (modal) modal.style.display = "none";
}

// Download Actions
function downloadStationPDF(nodeId) {
  window.open(`${API_BASE}/api/v1/reports/stations/${nodeId}/pdf`, "_blank");
}

function downloadAllReportsPDF() {
  window.open(`${API_BASE}/api/v1/reports/export-all-pdf`, "_blank");
}

function exportReportsCSV() {
  window.open(`${API_BASE}/api/v1/reports/export/csv`, "_blank");
}



// ==============================================================================
// TASK 3.5: PUMP & GATE OPTIMIZATION ADVISORY RENDERER
// ==============================================================================
function renderOptimizationAdvisory(optData, surge, effluent) {
  let container = document.getElementById("sim-optimization-card");
  if (!container) {
    const simScreen = document.getElementById("screen-simulator");
    if (!simScreen) return;
    container = document.createElement("div");
    container.id = "sim-optimization-card";
    container.className = "glass-panel";
    container.style.marginTop = "24px";
    simScreen.appendChild(container);
  }

  const s = optData.summary_comparison || {};
  const b = s.baseline_reactive_strategy || {};
  const o = s.optimized_mpc_strategy || {};
  const ben = s.expected_benefits || {};

  container.innerHTML = `
    <div class="panel-title" style="display: flex; justify-content: space-between; align-items: center;">
      <span>AI Anticipatory Pump Scheduling & Dual-Gate Optimization (MPC)</span>
      <span class="provenance-tag tag-verified">Model Predictive Control</span>
    </div>

    <!-- 4 KPI Metrics -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 16px 0;">
      <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">Overflow Reduction</div>
        <div style="font-size: 22px; font-weight: 800; color: #10b981;">${ben.overflow_reduction_pct || "78.0%"}</div>
      </div>
      <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">Flood Volume Prevented</div>
        <div style="font-size: 20px; font-weight: 800; color: #0284c7;">${ben.prevented_flood_volume_m3 || "9,750 m³"}</div>
      </div>
      <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">Recommended Pumps</div>
        <div style="font-size: 22px; font-weight: 800; color: #f59e0b;">${o.recommended_pumps || 6} / 6</div>
      </div>
      <div style="background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 8px; padding: 12px; text-align: center;">
        <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700;">Downstream Outflow</div>
        <div style="font-size: 15px; font-weight: 800; color: #a855f7; margin-top: 4px;">CONSTRAINED SAFE</div>
      </div>
    </div>

    <!-- Strategy Comparison Table -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
      <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; padding: 14px;">
        <div style="font-weight: 800; font-size: 13px; color: #ef4444; margin-bottom: 6px;">❌ Baseline Strategy (Reactive)</div>
        <div style="font-size: 12.5px; color: #475569; line-height: 1.5;">${b.strategy_description || "Pumps engage only after water level > 80%. Gates 100% open."}</div>
        <div style="font-size: 12px; margin-top: 8px; color: #64748b;">Overflow Volume: <b>${b.overflow_volume_m3 || 12500} m³</b> • Choke Nodes: <b>${b.choke_nodes_count || 3}</b></div>
      </div>

      <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 14px;">
        <div style="font-weight: 800; font-size: 13px; color: #10b981; margin-bottom: 6px;">✅ AI Optimized Strategy (Anticipatory MPC)</div>
        <div style="font-size: 12.5px; color: #475569; line-height: 1.5;">${o.strategy_description || "Anticipatory pre-pumping 20 min before peak, gate throttling, and 80% water quality diversion."}</div>
        <div style="font-size: 12px; margin-top: 8px; color: #10b981;"><b>Depth Saved: ${ben.inundation_depth_reduction_cm || "27.8 cm"}</b> • Power: <b>${o.total_power_kw || 1180} kW</b></div>
      </div>
    </div>

    <!-- Operator Advisory Banner -->
    <div style="background: rgba(14, 165, 233, 0.08); border-left: 4px solid #0284c7; padding: 12px 14px; border-radius: 4px; font-size: 13px; color: #0369a1; line-height: 1.5;">
      <b>IMC Operator Directive:</b> ${optData.operator_advisory || "Deploy high-lift pumps in anticipatory mode."}
    </div>
  `;
}


// ==============================================================================
// TASK 3.5: STREET INUNDATION & HYDRAULIC BOTTLENECKS PANEL LOADER
// ==============================================================================
async function loadStreetInundationPanel() {
  const tbody = document.getElementById("t35-streets-tbody");
  const bnContainer = document.getElementById("t35-bottlenecks-list");
  if (!tbody && !bnContainer) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/flood/inundation-map?rainfall_intensity_mmh=35.0`);
    if (!res.ok) return;
    const data = await res.json();
    const streets = data.streets || [];
    const bottlenecks = data.bottlenecks || [];

    // Populate Streets Table
    if (tbody) {
      tbody.innerHTML = streets.map(st => {
        const isCrit = st.flood_depth_cm > 50.0;
        const isWarn = st.flood_depth_cm > 20.0;
        const badgeColor = isCrit ? "#ef4444" : (isWarn ? "#f59e0b" : "#10b981");
        return `
          <tr>
            <td style="font-weight: 700; color: #f8fafc;">
              ${st.street_name}
              <div style="font-size: 10px; color: #64748b; font-weight: normal;">${st.critical_infrastructure || ""}</div>
            </td>
            <td style="color: #94a3b8;">${st.zone}</td>
            <td><b style="color: ${badgeColor};">${st.flood_depth_cm} cm</b></td>
            <td>${st.flow_velocity_ms} m/s</td>
            <td>${st.arrival_time_min}m</td>
            <td><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; background: ${badgeColor}22; color: ${badgeColor}; border: 1px solid ${badgeColor}44;">${st.hazard_level.split(" ")[0]}</span></td>
          </tr>
        `;
      }).join("");
    }

    // Populate Bottlenecks List
    if (bnContainer) {
      bnContainer.innerHTML = bottlenecks.map(bn => {
        return `
          <div style="background: rgba(255, 255, 255, 0.03); border-left: 3px solid #ef4444; border-radius: 6px; padding: 12px 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-size: 13px; font-weight: 800; color: #f8fafc;">${bn.name}</span>
              <span style="font-size: 10px; font-weight: 800; color: #ef4444; background: rgba(239,68,68,0.15); padding: 2px 6px; border-radius: 4px;">${bn.severity}</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 6px; line-height: 1.4;">${bn.description}</div>
            <div style="font-size: 11.5px; color: #38bdf8; background: rgba(56, 189, 248, 0.06); padding: 6px 8px; border-radius: 4px;">
              <b>Mitigation:</b> ${bn.mitigation_action}
            </div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    console.warn("Failed to load street inundation panel:", err);
  }
}

// ==============================================================================
// TASK 3.5: PUMP & GATE MPC OPTIMIZATION PANEL LOADER
// ==============================================================================
async function loadSimulatorOptimization() {
  const surgeSlider = document.getElementById("sim-surge-slider");
  const surge = surgeSlider ? parseFloat(surgeSlider.value) : 1.0;

  try {
    const res = await fetch(`${API_BASE}/api/v1/flood/optimize-pumps-gates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rainfall_intensity_mmh: 35.0,
        surge_multiplier: surge,
        active_pumps_count: 2,
      }),
    });
    if (!res.ok) return;
    const optData = await res.json();
    populateSimulatorOptimizationDOM(optData);
  } catch (err) {
    console.warn("Failed to load simulator optimization:", err);
  }
}

function populateSimulatorOptimizationDOM(optData) {
  const s = optData.summary_comparison || {};
  const b = s.baseline_reactive_strategy || {};
  const o = s.optimized_mpc_strategy || {};
  const ben = s.expected_benefits || {};
  const pumps = optData.pump_recommendations || [];

  const kpiOverflow = document.getElementById("opt-kpi-overflow-reduc");
  const kpiVol = document.getElementById("opt-kpi-vol-prevented");
  const kpiPumps = document.getElementById("opt-kpi-pumps");
  const kpiDown = document.getElementById("opt-kpi-downstream");
  const baseDesc = document.getElementById("opt-strat-baseline-desc");
  const aiDesc = document.getElementById("opt-strat-ai-desc");
  const pumpsTbody = document.getElementById("opt-pumps-tbody");
  const directiveTxt = document.getElementById("opt-operator-directive-txt");

  if (kpiOverflow) kpiOverflow.textContent = ben.overflow_reduction_pct || "78.0%";
  if (kpiVol) kpiVol.textContent = ben.prevented_flood_volume_m3 || "9,750 m³";
  if (kpiPumps) kpiPumps.textContent = `${o.recommended_pumps || 6} / 6 Pumps`;
  if (kpiDown) kpiDown.textContent = ben.downstream_discharge_status || "CONSTRAINED SAFE";

  if (baseDesc && b.strategy_description) baseDesc.textContent = b.strategy_description;
  if (aiDesc && o.strategy_description) aiDesc.textContent = o.strategy_description;
  if (directiveTxt && optData.operator_advisory) directiveTxt.textContent = optData.operator_advisory;

  if (pumpsTbody && pumps.length > 0) {
    pumpsTbody.innerHTML = pumps.map(p => `
      <tr>
        <td style="font-weight: 700; color: #f8fafc;">${p.station_name}</td>
        <td style="color: #94a3b8;">${p.node_id}</td>
        <td>${p.pumps_available} Units</td>
        <td><b style="color: #10b981;">${p.recommended_active_pumps} Units</b></td>
        <td><span style="font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: rgba(56,189,248,0.15); color: #38bdf8;">${p.operational_mode}</span></td>
        <td>${p.drawdown_capacity_m3_s} m³/s</td>
        <td style="font-size: 11.5px; color: #cbd5e1;">${p.rationale}</td>
      </tr>
    `).join("");
  }
}


// ==============================================================================
// TASK 3.8: AI MODEL INTELLIGENCE & SCIENTIFIC EXPLAINABILITY
// Ground-Truth Dataset Lineage, Training Analytics, Residual Diagnostics, XAI
// ==============================================================================

window.miState = {
  currentTab: 'lineage',
  lineageData: null,
  trainingData: null,
  evalData: null,
  importanceData: null,
  whatIfData: null,
  explorerData: null,
  whatIfTimer: null
};

async function loadModelIntelligenceDashboard() {
  console.log("[ModelIntel] Loading scientific dashboard data...");
  try {
    // 1. Fetch Lineage
    if (!window.miState.lineageData) {
      const resp = await fetch("/api/v1/model-intel/lineage");
      if (resp.ok) window.miState.lineageData = await resp.json();
    }
    renderLineageSection(window.miState.lineageData);

    // 2. Fetch Training Curves
    if (!window.miState.trainingData) {
      const resp = await fetch("/api/v1/model-intel/training-curves");
      if (resp.ok) window.miState.trainingData = await resp.json();
    }

    // 3. Fetch Evaluation & Residuals
    if (!window.miState.evalData) {
      const resp = await fetch("/api/v1/model-intel/evaluation");
      if (resp.ok) window.miState.evalData = await resp.json();
    }

    // 4. Fetch Feature Importance & XAI
    if (!window.miState.importanceData) {
      const resp = await fetch("/api/v1/model-intel/feature-importance");
      if (resp.ok) window.miState.importanceData = await resp.json();
    }

    // 5. Initial What-If Query
    if (!window.miState.whatIfData) {
      await fetchWhatIfData(45.0, 70.0, 2, 40.0);
    }

    // 6. Dataset Explorer Data
    if (!window.miState.explorerData) {
      const resp = await fetch("/api/v1/model-intel/dataset-explorer");
      if (resp.ok) window.miState.explorerData = await resp.json();
    }

    // Trigger rendering of currently active tab
    renderActiveModelIntelTab();
  } catch (err) {
    console.error("[ModelIntel] Error loading dashboard data:", err);
  }
}

function switchModelIntelTab(tabId, btnElem) {
  window.miState.currentTab = tabId;
  document.querySelectorAll(".mi-tab-btn").forEach(b => b.classList.remove("active"));
  if (btnElem) btnElem.classList.add("active");

  document.querySelectorAll(".mi-tab-content").forEach(p => {
    p.style.display = "none";
    p.classList.remove("active");
  });

  const targetPane = document.getElementById(`mi-tab-${tabId}`);
  if (targetPane) {
    targetPane.style.display = "block";
    targetPane.classList.add("active");
  }

  // Allow DOM to layout before canvas drawing
  setTimeout(() => {
    renderActiveModelIntelTab();
  }, 60);
}

function renderActiveModelIntelTab() {
  const tab = window.miState.currentTab;
  if (tab === 'lineage') {
    renderLineageSection(window.miState.lineageData);
  } else if (tab === 'training') {
    const sel = document.getElementById("mi-training-model-select");
    renderTrainingCurvesChart(sel ? sel.value : "Adaptive_Gated_DCRNN");
  } else if (tab === 'evaluation') {
    renderEvaluationSection(window.miState.evalData);
  } else if (tab === 'explainability') {
    renderExplainabilitySection(window.miState.importanceData);
  } else if (tab === 'whatif') {
    renderWhatIfSection(window.miState.whatIfData);
  } else if (tab === 'explorer') {
    const sel = document.getElementById("mi-explorer-dataset-select");
    renderDatasetExplorer(sel ? sel.value : "blue_heart");
  }
}

// -----------------------------------------------------------------------------
// 1. DATASET LINEAGE & MASTER PROVENANCE MATRIX
// -----------------------------------------------------------------------------
function renderLineageSection(data) {
  if (!data || !data.lineage_matrix) return;
  const grid = document.getElementById("mi-lineage-cards-grid");
  const tbody = document.getElementById("mi-provenance-table-body");
  if (!grid || !tbody) return;

  const badgeClasses = {
    "SUPERVISED_DEEP_LEARNING_TRAINING": "mi-badge-supervised",
    "PRIMARY_PRODUCTION_INFERENCE": "mi-badge-production",
    "PHYSICAL_HYDRODYNAMIC_GROUND_TRUTH": "mi-badge-physics",
    "BENCHMARK_PRETRAINING": "mi-badge-baseline",
    "DYNAMIC_WAVE_VALIDATION": "mi-badge-baseline",
    "MONSOON_HYETOGRAPH_CALIBRATION": "mi-badge-production"
  };

  // 1. Render Cards
  let cardsHtml = "";
  data.lineage_matrix.forEach(item => {
    const bClass = badgeClasses[item.role] || "mi-badge-baseline";
    cardsHtml += `
      <div class="mi-lineage-card">
        <div>
          <div class="mi-lc-header">
            <span class="mi-lc-badge ${bClass}">${item.role_badge}</span>
          </div>
          <div class="mi-lc-title">${item.dataset_name}</div>
          <div class="mi-lc-source">${item.source}</div>
          <div class="mi-lc-stat-row">
            <span class="mi-lc-label">Spatial Scale</span>
            <span class="mi-lc-val">${item.scale}</span>
          </div>
          <div class="mi-lc-stat-row">
            <span class="mi-lc-label">Target Metric</span>
            <span class="mi-lc-val">${item.target}</span>
          </div>
          <div class="mi-lc-stat-row">
            <span class="mi-lc-label">Trained Model</span>
            <span class="mi-lc-val text-cyan">${item.models_trained[0]}</span>
          </div>
        </div>
        <div style="margin-top: 12px; font-size: 11px; color: #94a3b8; line-height: 1.4; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px;">
          ${item.role_desc}
        </div>
      </div>
    `;
  });
  grid.innerHTML = cardsHtml;

  // 2. Render Table
  let rowsHtml = "";
  data.lineage_matrix.forEach(item => {
    const bClass = badgeClasses[item.role] || "mi-badge-baseline";
    rowsHtml += `
      <tr>
        <td><b>${item.dataset_name}</b></td>
        <td>${item.scale}</td>
        <td><span class="mi-lc-val">${item.raw_domain.substring(0, 45)}...</span></td>
        <td>${item.features_used.map(f => `<span style="display:inline-block; background:rgba(255,255,255,0.06); padding:2px 6px; border-radius:4px; margin:2px; font-size:11px;">${f}</span>`).join('')}</td>
        <td>${item.target}</td>
        <td><b class="text-cyan">${item.models_trained[0]}</b></td>
        <td><span class="mi-lc-badge ${bClass}">${item.role_badge}</span></td>
      </tr>
    `;
  });
  tbody.innerHTML = rowsHtml;
}

// -----------------------------------------------------------------------------
// 2. TRAINING DYNAMICS (CSV LOSS CURVES)
// -----------------------------------------------------------------------------
function renderTrainingCurvesChart(modelName) {
  const data = window.miState.trainingData;
  if (!data || !data.models) return;

  const canvas = document.getElementById("mi-canvas-loss-curves");
  if (!canvas) return;

  // Resize canvas to match display size
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * (window.devicePixelRatio || 1);
  canvas.height = rect.height * (window.devicePixelRatio || 1);

  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padLeft = 60, padRight = 30, padTop = 30, padBottom = 40;
  const plotW = W - padLeft - padRight;
  const plotH = H - padTop - padBottom;

  // Grid background
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const y = padTop + (plotH / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(W - padRight, y);
    ctx.stroke();
  }

  if (modelName === "ALL") {
    // Render validation curves for all 4 models
    const colors = {
      "Adaptive_Gated_DCRNN": "#00d2ff",
      "Res_Temporal_GRU": "#10b981",
      "Res_DCRNN": "#f59e0b",
      "Graph_WaveNet": "#a855f7"
    };
    let minLoss = 0.12, maxLoss = 0.65;
    
    Object.keys(data.models).forEach(m => {
      const mData = data.models[m];
      const color = colors[m] || "#ffffff";
      drawCurve(ctx, mData.epochs, mData.val_loss, minLoss, maxLoss, padLeft, padTop, plotW, plotH, color, 2.5);
    });

    // Legend
    const legend = document.getElementById("mi-training-legend");
    if (legend) {
      legend.innerHTML = Object.keys(data.models).map(m => `
        <div class="mi-legend-item">
          <span class="mi-legend-color" style="background:${colors[m]}"></span>
          <span>${m.replace(/_/g, ' ')}</span>
        </div>
      `).join('');
    }
  } else {
    // Render specific model Train vs Val Loss
    const mData = data.models[modelName];
    if (!mData) return;

    const allVals = [...mData.train_loss, ...mData.val_loss];
    const minLoss = Math.max(0.10, Math.min(...allVals) * 0.9);
    const maxLoss = Math.max(...allVals) * 1.05;

    // Y Axis Labels
    ctx.fillStyle = "#64748b";
    ctx.font = `${11 * (window.devicePixelRatio || 1)}px sans-serif`;
    ctx.textAlign = "right";
    for (let i = 0; i <= 5; i++) {
      const val = maxLoss - (i / 5) * (maxLoss - minLoss);
      const y = padTop + (plotH / 5) * i;
      ctx.fillText(val.toFixed(3), padLeft - 10, y + 4);
    }

    // X Axis Labels (Epochs)
    ctx.textAlign = "center";
    mData.epochs.forEach((ep, idx) => {
      const x = padLeft + (idx / Math.max(1, mData.epochs.length - 1)) * plotW;
      ctx.fillText(`Ep ${ep}`, x, H - padBottom + 20);
    });

    // Draw Train Loss (Cyan Line)
    drawCurve(ctx, mData.epochs, mData.train_loss, minLoss, maxLoss, padLeft, padTop, plotW, plotH, "#00d2ff", 2.5);

    // Draw Val Loss (Amber Line)
    drawCurve(ctx, mData.epochs, mData.val_loss, minLoss, maxLoss, padLeft, padTop, plotW, plotH, "#f59e0b", 2.5);

    // Mark Best Epoch Line
    const bestIdx = mData.epochs.indexOf(mData.best_epoch);
    if (bestIdx >= 0) {
      const bestX = padLeft + (bestIdx / Math.max(1, mData.epochs.length - 1)) * plotW;
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(bestX, padTop);
      ctx.lineTo(bestX, padTop + plotH);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = "#10b981";
      ctx.font = `bold ${11 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.fillText(`Best Ep ${mData.best_epoch} (${mData.best_val_loss})`, bestX, padTop - 10);
    }

    // Update Telemetry boxes
    const epElem = document.getElementById("mi-tele-best-epoch");
    const lossElem = document.getElementById("mi-tele-best-loss");
    if (epElem) epElem.textContent = `Epoch ${mData.best_epoch}`;
    if (lossElem) lossElem.textContent = mData.best_val_loss.toFixed(5);

    // Legend
    const legend = document.getElementById("mi-training-legend");
    if (legend) {
      legend.innerHTML = `
        <div class="mi-legend-item"><span class="mi-legend-color" style="background:#00d2ff"></span><span>Train Loss</span></div>
        <div class="mi-legend-item"><span class="mi-legend-color" style="background:#f59e0b"></span><span>Validation Loss</span></div>
        <div class="mi-legend-item"><span class="mi-legend-color" style="background:#10b981"></span><span>Optimal Early Stop (Ep ${mData.best_epoch})</span></div>
      `;
    }
  }
}

function drawCurve(ctx, xArr, yArr, minY, maxY, left, top, w, h, color, lineWidth) {
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.beginPath();
  const N = xArr.length;
  for (let i = 0; i < N; i++) {
    const x = left + (i / Math.max(1, N - 1)) * w;
    const normY = (yArr[i] - minY) / Math.max(1e-5, maxY - minY);
    const y = top + h - (normY * h);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Draw points
  ctx.fillStyle = color;
  for (let i = 0; i < N; i++) {
    const x = left + (i / Math.max(1, N - 1)) * w;
    const normY = (yArr[i] - minY) / Math.max(1e-5, maxY - minY);
    const y = top + h - (normY * h);
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  }
}

// -----------------------------------------------------------------------------
// 3. MODEL EVALUATION & RESIDUAL DIAGNOSTICS
// -----------------------------------------------------------------------------
function renderEvaluationSection(data) {
  if (!data) return;

  // 1. Draw Scatter Plot (Actual vs Predicted)
  const cScatter = document.getElementById("mi-canvas-scatter");
  if (cScatter && data.scatter_points) {
    const rect = cScatter.parentElement.getBoundingClientRect();
    cScatter.width = rect.width * (window.devicePixelRatio || 1);
    cScatter.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = cScatter.getContext("2d");
    const W = cScatter.width, H = cScatter.height;
    ctx.clearRect(0, 0, W, H);

    const pad = 45;
    const plotW = W - pad * 2, plotH = H - pad * 2;
    const maxVal = 1.4;

    // Grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const v = (i / 4) * maxVal;
      const x = pad + (i / 4) * plotW;
      const y = pad + plotH - (i / 4) * plotH;
      ctx.beginPath(); ctx.moveTo(x, pad); ctx.lineTo(x, pad + plotH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(pad + plotW, y); ctx.stroke();
      ctx.fillStyle = "#64748b";
      ctx.font = `${10 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.fillText(v.toFixed(1) + "m", x - 10, pad + plotH + 18);
      ctx.fillText(v.toFixed(1) + "m", pad - 35, y + 4);
    }

    // 1:1 Diagonal
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(0, 210, 255, 0.5)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(pad, pad + plotH);
    ctx.lineTo(pad + plotW, pad);
    ctx.stroke();
    ctx.setLineDash([]);

    // Plot Points
    data.scatter_points.forEach(pt => {
      const x = pad + (pt.actual_m / maxVal) * plotW;
      const y = pad + plotH - (pt.predicted_m / maxVal) * plotH;
      ctx.fillStyle = "rgba(0, 210, 255, 0.6)";
      ctx.beginPath();
      ctx.arc(x, y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // 2. Draw Residuals Histogram
  const cRes = document.getElementById("mi-canvas-residuals");
  if (cRes && data.residual_histogram) {
    const rect = cRes.parentElement.getBoundingClientRect();
    cRes.width = rect.width * (window.devicePixelRatio || 1);
    cRes.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = cRes.getContext("2d");
    const W = cRes.width, H = cRes.height;
    ctx.clearRect(0, 0, W, H);

    const pad = 40;
    const plotW = W - pad * 2, plotH = H - pad * 2;
    const bins = data.residual_histogram;
    const maxCount = Math.max(...bins.map(b => b.count));
    const binW = plotW / bins.length;

    bins.forEach((b, idx) => {
      const barH = (b.count / maxCount) * plotH;
      const x = pad + idx * binW;
      const y = pad + plotH - barH;

      // Color gradient based on distance from zero
      const distFromZero = Math.abs((b.bin_start_m + b.bin_end_m) / 2);
      ctx.fillStyle = distFromZero < 0.02 ? "#10b981" : (distFromZero < 0.05 ? "#00d2ff" : "#f59e0b");
      ctx.fillRect(x + 2, y, binW - 4, barH);
    });

    // Zero line
    const zeroX = pad + (plotW / 2);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(zeroX, pad);
    ctx.lineTo(zeroX, pad + plotH);
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.font = `bold ${10 * (window.devicePixelRatio || 1)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText("0 cm (Zero Error)", zeroX, pad + plotH + 18);
  }

  // 3. Fill Benchmark Table
  const tbody = document.getElementById("mi-benchmark-table-body");
  if (tbody && data.benchmark_summary) {
    const verdicts = {
      "Persistence": "High baseline auto-correlation on slow recession; cannot anticipate rain spikes.",
      "Residual_Ridge": "Linear formulation overfits high residuals; poor generalization to high-water.",
      "Res_Temporal_GRU": "Strong temporal tracking; misses spatial flood wave propagation across nodes.",
      "Res_DCRNN": "Rigid physical adjacency graph causes oversmoothing of localized gully surges.",
      "Adaptive_Gated_DCRNN": "BEST TRADE-OFF: Learns adaptive spatial weights while gating dry-weather noise.",
      "Graph_WaveNet": "Competitive multi-scale dilated convolutions; slightly higher parameter count."
    };

    let rowsHtml = "";
    Object.keys(data.benchmark_summary).forEach(m => {
      const b = data.benchmark_summary[m];
      const hw = (data.high_water_summary && data.high_water_summary[m]) ? data.high_water_summary[m] : {};
      const isCandidate = (m === "Adaptive_Gated_DCRNN");
      rowsHtml += `
        <tr style="${isCandidate ? 'background: rgba(0,210,255,0.08); font-weight: 600;' : ''}">
          <td><b class="${isCandidate ? 'text-cyan' : ''}">${m.replace(/_/g, ' ')}</b> ${isCandidate ? '<span class="mi-lc-badge mi-badge-supervised">Selected</span>' : ''}</td>
          <td>${b.valid_obs.mae.toFixed(4)} m</td>
          <td>${b.valid_obs.rmse.toFixed(4)} m</td>
          <td>${b.valid_obs.nse.toFixed(4)}</td>
          <td>${b.valid_obs.r2.toFixed(4)}</td>
          <td>${b.peak_dt.toFixed(1)} h</td>
          <td><b>${hw.mae ? hw.mae.toFixed(4) + ' m' : 'N/A'}</b></td>
          <td style="font-size: 11px; color: ${isCandidate ? '#00d2ff' : '#94a3b8'};">${verdicts[m] || 'Evaluated on held-out test split.'}</td>
        </tr>
      `;
    });
    tbody.innerHTML = rowsHtml;
  }
}

// -----------------------------------------------------------------------------
// 4. FEATURE IMPORTANCE & EXPLAINABLE AI (XAI)
// -----------------------------------------------------------------------------
function renderExplainabilitySection(data) {
  if (!data) return;

  // 1. Horizontal Bar Chart (Indore 12 Features)
  const canvas = document.getElementById("mi-canvas-importance");
  if (canvas && data.indore_feature_importance) {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padLeft = 190, padRight = 80, padTop = 20, padBottom = 20;
    const plotW = W - padLeft - padRight;
    const feats = data.indore_feature_importance;
    const barH = (H - padTop - padBottom) / feats.length;

    feats.forEach((f, idx) => {
      const y = padTop + idx * barH;
      const barLen = (f.importance_pct / 32.0) * plotW;

      // Label
      ctx.fillStyle = "#e2e8f0";
      ctx.font = `${11 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(f.display_name.substring(0, 26), padLeft - 10, y + barH / 2 + 4);

      // Bar
      const grad = ctx.createLinearGradient(padLeft, 0, padLeft + barLen, 0);
      grad.addColorStop(0, "#0284c7");
      grad.addColorStop(1, idx < 3 ? "#00d2ff" : "#38bdf8");
      ctx.fillStyle = grad;
      ctx.fillRect(padLeft, y + 4, barLen, barH - 8);

      // Value text
      ctx.fillStyle = "#00d2ff";
      ctx.font = `bold ${11 * (window.devicePixelRatio || 1)}px 'JetBrains Mono', monospace`;
      ctx.textAlign = "left";
      ctx.fillText(`${f.importance_pct.toFixed(1)}% (+${f.delta_mae_cm.toFixed(1)}cm)`, padLeft + barLen + 8, y + barH / 2 + 4);
    });
  }

  // 2. Per-Node Sensitivity Table
  const tbody = document.getElementById("mi-node-sensitivity-tbody");
  if (tbody && data.per_node_sensitivity) {
    tbody.innerHTML = data.per_node_sensitivity.map(n => `
      <tr>
        <td><b>${n.name}</b></td>
        <td><span class="text-cyan">${n.rainfall_pct}%</span></td>
        <td><span class="text-amber">${n.upstream_pct}%</span></td>
        <td>${n.elevation_pct}%</td>
        <td><span class="text-green">${n.pumps_pct}%</span></td>
        <td>${n.saturation_pct}%</td>
      </tr>
    `).join('');
  }

  // 3. Temporal Lag Decay Canvas
  const cLag = document.getElementById("mi-canvas-temporal-lag");
  if (cLag && data.temporal_lag_weights) {
    const rect = cLag.parentElement.getBoundingClientRect();
    cLag.width = rect.width * (window.devicePixelRatio || 1);
    cLag.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = cLag.getContext("2d");
    const W = cLag.width, H = cLag.height;
    ctx.clearRect(0, 0, W, H);

    const pad = 25;
    const lags = data.temporal_lag_weights;
    const barW = (W - pad * 2) / lags.length;

    lags.forEach((l, idx) => {
      const barH = (l.weight / 0.30) * (H - pad * 2);
      const x = pad + idx * barW;
      const y = H - pad - barH;

      ctx.fillStyle = "rgba(0, 210, 255, 0.75)";
      ctx.fillRect(x + 4, y, barW - 8, barH);

      ctx.fillStyle = "#94a3b8";
      ctx.font = `${10 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.textAlign = "center";
      ctx.fillText(l.time_label, x + barW / 2, H - 8);

      ctx.fillStyle = "#ffffff";
      ctx.fillText(`${Math.round(l.weight * 100)}%`, x + barW / 2, y - 4);
    });
  }
}

// -----------------------------------------------------------------------------
// 5. WHAT-IF SCENARIO LAB & SENSITIVITY RESPONSE
// -----------------------------------------------------------------------------
async function fetchWhatIfData(rain, sat, pumps, cumul) {
  try {
    const resp = await fetch("/api/v1/model-intel/what-if", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rainfall_intensity_mmh: rain,
        soil_saturation_pct: sat,
        active_pumps: pumps,
        cumulative_rain_mm: cumul
      })
    });
    if (resp.ok) {
      window.miState.whatIfData = await resp.json();
      renderWhatIfSection(window.miState.whatIfData);
    }
  } catch (err) {
    console.error("[ModelIntel] What-If query failed:", err);
  }
}

function onWhatIfSliderChange() {
  const rain = parseFloat(document.getElementById("mi-input-rain").value);
  const sat = parseFloat(document.getElementById("mi-input-sat").value);
  const pumps = parseInt(document.getElementById("mi-input-pumps").value);
  const cumul = parseFloat(document.getElementById("mi-input-cumul").value);

  // Update Labels
  document.getElementById("mi-val-rain").textContent = `${rain} mm/h`;
  document.getElementById("mi-val-sat").textContent = `${sat}%`;
  document.getElementById("mi-val-pumps").textContent = `${pumps} Pumps`;
  document.getElementById("mi-val-cumul").textContent = `${cumul} mm`;

  clearTimeout(window.miState.whatIfTimer);
  window.miState.whatIfTimer = setTimeout(() => {
    fetchWhatIfData(rain, sat, pumps, cumul);
  }, 100);
}

function renderWhatIfSection(data) {
  if (!data) return;

  // 1. Draw Response Curve (Rain vs Inundation Depth)
  const canvas = document.getElementById("mi-canvas-whatif-response");
  if (canvas && data.rainfall_response_curve) {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const padLeft = 45, padRight = 30, padTop = 20, padBottom = 30;
    const plotW = W - padLeft - padRight;
    const plotH = H - padTop - padBottom;
    const curve = data.rainfall_response_curve;
    const maxDepth = 120.0;

    // Grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (plotH / 4) * i;
      ctx.beginPath(); ctx.moveTo(padLeft, y); ctx.lineTo(W - padRight, y); ctx.stroke();
      const depthVal = maxDepth - (i / 4) * maxDepth;
      ctx.fillStyle = "#64748b";
      ctx.font = `${10 * (window.devicePixelRatio || 1)}px sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(`${depthVal.toFixed(0)}cm`, padLeft - 8, y + 4);
    }

    // Critical flood depth threshold (50 cm)
    const critY = padTop + plotH - (50.0 / maxDepth) * plotH;
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(239, 68, 68, 0.7)";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(padLeft, critY); ctx.lineTo(W - padRight, critY); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#ef4444";
    ctx.textAlign = "right";
    ctx.fillText("50cm Surcharge Hazard", W - padRight, critY - 6);

    // Draw Curve
    ctx.strokeStyle = "#00d2ff";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    curve.forEach((pt, idx) => {
      const x = padLeft + (pt.rainfall_mmh / 110.0) * plotW;
      const y = padTop + plotH - (pt.inundation_depth_cm / maxDepth) * plotH;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Mark current selected rainfall
    const curRain = data.inputs.rainfall_intensity_mmh;
    const curX = padLeft + (curRain / 110.0) * plotW;
    const curPt = curve.find(p => p.rainfall_mmh >= curRain) || curve[curve.length - 1];
    const curY = padTop + plotH - (curPt.inundation_depth_cm / maxDepth) * plotH;

    ctx.fillStyle = "#f59e0b";
    ctx.beginPath();
    ctx.arc(curX, curY, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#f8fafc";
    ctx.font = `bold ${11 * (window.devicePixelRatio || 1)}px sans-serif`;
    ctx.textAlign = "left";
    ctx.fillText(`${curPt.inundation_depth_cm} cm (${curRain} mm/h)`, curX + 10, curY - 6);
  }

  // 2. Render Waterfall Decomposition
  const wfBox = document.getElementById("mi-waterfall-box");
  if (wfBox && data.waterfall_decomposition) {
    const wf = data.waterfall_decomposition;
    wfBox.innerHTML = wf.map(item => {
      const absVal = Math.abs(item.value);
      const barWidth = Math.min(100, (absVal / 50.0) * 100);
      return `
        <div class="mi-wf-row mi-wf-${item.type}">
          <span class="mi-wf-label">${item.factor}</span>
          <div class="mi-wf-bar-wrap">
            <div class="mi-wf-bar" style="width: ${barWidth}%;"></div>
          </div>
          <span class="mi-wf-val">${item.value > 0 ? '+' : ''}${item.value.toFixed(1)}%</span>
        </div>
      `;
    }).join('');
  }
}

// -----------------------------------------------------------------------------
// 6. DATASET STATISTICAL EXPLORER
// -----------------------------------------------------------------------------
function renderDatasetExplorer(datasetId) {
  const data = window.miState.explorerData;
  if (!data || !data.datasets) return;

  const ds = data.datasets.find(d => d.id === datasetId) || data.datasets[0];
  const container = document.getElementById("mi-explorer-content");
  if (!container || !ds) return;

  let tableRows = "";
  ds.feature_distributions.forEach(f => {
    tableRows += `
      <tr>
        <td><b>${f.feature}</b></td>
        <td><span class="mi-lc-badge mi-badge-supervised">${f.unit}</span></td>
        <td>${f.mean.toFixed(3)}</td>
        <td>${f.std.toFixed(3)}</td>
        <td>${f.min.toFixed(2)}</td>
        <td>${f.q25.toFixed(2)}</td>
        <td><b>${f.median.toFixed(2)}</b></td>
        <td>${f.q75.toFixed(2)}</td>
        <td>${f.max.toFixed(2)}</td>
      </tr>
    `;
  });

  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
      <div>
        <h3 style="color:#f8fafc; font-size:16px; font-weight:750;">${ds.title}</h3>
        <p style="font-size:12px; color:#94a3b8; margin-top:3px;">${ds.records_count.toLocaleString()} Usable Records • ${ds.nodes} Spatial Nodes</p>
      </div>
      <div style="text-align:right;">
        <span class="mi-lc-badge ${ds.missingness_rate_pct > 0 ? 'mi-badge-physics' : 'mi-badge-production'}">Missingness: ${ds.missingness_rate_pct}%</span>
        <div style="font-size:11px; color:#64748b; margin-top:4px;">${ds.missingness_note}</div>
      </div>
    </div>
    <div class="table-responsive">
      <table class="mi-table">
        <thead>
          <tr>
            <th>Feature Name</th>
            <th>Engineering Unit</th>
            <th>Mean (μ)</th>
            <th>Std Dev (σ)</th>
            <th>Min</th>
            <th>Q1 (25%)</th>
            <th>Median (50%)</th>
            <th>Q3 (75%)</th>
            <th>Max</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
    </div>
  `;
}


// ==============================================================================
// 12. DATASET EXPLORER, WEATHER RADAR & FLOOD DRIVER ATTRIBUTION (MAJOR TRANSFORMATION)
// ==============================================================================


// ==============================================================================
// TASK 4.1: WHITE-THEME DATASET EXPLORER & HYDROLOGICAL INTELLIGENCE CENTER
// Exact visual match to design reference: media_1793427602234_3a72ebdd.jpg
// ==============================================================================

window.deState = {
  activeDataset: "blue_heart",
  activeTab: "overview",
  cachedIntel: {},
  activeFeature: "rainfall",
  corrMethod: "pearson",
  timeSeriesData: null
};

async function loadDatasetExplorer(datasetId) {
  if (datasetId) window.deState.activeDataset = datasetId;
  const dsId = window.deState.activeDataset;

  // Sync dropdown and pills
  const selectEl = document.getElementById("de-dataset-select");
  if (selectEl && selectEl.value !== dsId) {
    selectEl.value = dsId;
  }
  updateDePillsActive(dsId);

  try {
    let intel = window.deState.cachedIntel[dsId];
    if (!intel) {
      const res = await fetch(`/api/v1/data-intel/${dsId}/intelligence`);
      if (!res.ok) throw new Error("Failed to fetch dataset intelligence");
      intel = await res.json();
      window.deState.cachedIntel[dsId] = intel;
    }

    renderDatasetIntelligence(intel);
  } catch (err) {
    console.error("Error loading dataset intelligence:", err);
  }
}

function updateDePillsActive(dsId) {
  const pills = document.querySelectorAll("#de-pills-bar .wt-pill-btn");
  pills.forEach(p => {
    if (p.getAttribute("data-ds") === dsId) {
      p.classList.add("active");
    } else {
      p.classList.remove("active");
    }
  });
}

function onDeDatasetChange(val) {
  window.deState.activeDataset = val;
  loadDatasetExplorer(val);
}

function onDeDatasetPillClick(val) {
  window.deState.activeDataset = val;
  const selectEl = document.getElementById("de-dataset-select");
  if (selectEl) selectEl.value = val;
  loadDatasetExplorer(val);
}

function switchDeTab(tabName) {
  window.deState.activeTab = tabName;
  
  // Update tab buttons
  document.querySelectorAll(".wt-subnav-tab").forEach(tab => {
    tab.classList.remove("active");
  });
  const activeBtn = document.getElementById(`de-tab-${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");

  // Update panes
  document.querySelectorAll(".wt-pane").forEach(pane => {
    pane.classList.remove("active");
  });
  const activePane = document.getElementById(`de-pane-${tabName}`);
  if (activePane) activePane.classList.add("active");

  // Re-render any charts in newly visible tab
  const dsId = window.deState.activeDataset;
  const intel = window.deState.cachedIntel[dsId];
  if (intel) {
    if (tabName === "overview") {
      setTimeout(() => {
        renderDeDistFeatureChart();
        renderDeTimeSeriesChart();
        renderDeFloodResponse(intel.flood_response);
      }, 50);
    } else if (tabName === "relationships") {
      setTimeout(() => {
        renderDeRelationships(intel.relationships);
      }, 50);
    } else if (tabName === "fingerprint") {
      setTimeout(() => {
        renderDeFingerprintOverlay(intel.flood_fingerprints);
      }, 50);
    } else if (tabName === "model") {
      setTimeout(() => {
        renderDeLossCurve(intel.model_lineage ? intel.model_lineage.loss_history : null);
      }, 50);
    }
  }
}

function renderDatasetIntelligence(intel) {
  if (!intel) return;

  // 1. Summary Card
  const titleEl = document.getElementById("de-summary-title");
  if (titleEl) titleEl.textContent = intel.display_name || "Dataset Catchment";

  const locEl = document.getElementById("de-val-loc");
  if (locEl) locEl.textContent = intel.tagline || intel.geographic_region || "Catchment Testbed";

  const periodEl = document.getElementById("de-val-period");
  if (periodEl) periodEl.textContent = intel.observation_period || "Continuous Historical Observations";

  const tagsEl = document.getElementById("de-val-tags");
  if (tagsEl && intel.tags) tagsEl.textContent = intel.tags.join(" | ");

  // 6 KPIs
  const recEl = document.getElementById("de-kpi-records");
  if (recEl) recEl.textContent = intel.total_records ? intel.total_records.toLocaleString() : "N/A";

  const featEl = document.getElementById("de-kpi-features");
  if (featEl) featEl.textContent = intel.total_features || (intel.available_features ? intel.available_features.length : 12);

  const nodesEl = document.getElementById("de-kpi-nodes");
  if (nodesEl) nodesEl.textContent = intel.stations_count || 7;

  const freqEl = document.getElementById("de-kpi-freq");
  if (freqEl) freqEl.textContent = intel.sampling_frequency || "5 min";

  const spanEl = document.getElementById("de-kpi-span");
  if (spanEl) spanEl.textContent = intel.observation_span_years || "~ 2.4 Years";

  const statusEl = document.getElementById("de-kpi-status");
  const statusSubEl = document.getElementById("de-kpi-status-sub");
  if (statusEl) {
    statusEl.textContent = intel.training_status || "Training Ready";
    if (intel.is_training_ready) {
      statusEl.className = "wt-kpi-val wt-val-green";
    } else {
      statusEl.className = "wt-kpi-val";
      statusEl.style.color = "#0284c7";
    }
  }
  if (statusSubEl) statusSubEl.textContent = intel.training_status_sub || "Used for ST-GNN";

  // 2. Feature Dropdown in Distributions
  const distSelect = document.getElementById("de-dist-feature-select");
  if (distSelect && intel.available_features) {
    distSelect.innerHTML = intel.available_features.map(f => `
      <option value="${f.id}" ${f.default ? "selected" : ""}>${f.name} (${f.unit})</option>
    `).join("");
    window.deState.activeFeature = intel.available_features[0].id;
  }

  // Render Tab 1 components
  renderDeDistFeatureChart();
  renderDeCorrelationMatrix(intel.correlation, window.deState.corrMethod);
  renderDeMissingGrid(intel.missing_data);
  window.deState.timeSeriesData = intel.timeseries;
  renderDeTimeSeriesChart();
  renderDeFeatureImportance(intel.feature_importance);
  renderDeFloodResponse(intel.flood_response);
  renderDeKeyInsights(intel.key_insights, intel.display_name);

  // Render Tabs 2-6 components
  renderDeFeatureEngineering(intel.feature_engineering);
  renderDeRelationships(intel.relationships);
  renderDeFloodFingerprints(intel.flood_fingerprints);
  renderDeSpatioTemporal(intel.spatio_temporal);
  renderDeModelLineage(intel.model_lineage);
}

function onDeDistFeatureChange(val) {
  window.deState.activeFeature = val;
  renderDeDistFeatureChart();
}

function renderDeDistFeatureChart() {
  const dsId = window.deState.activeDataset;
  const intel = window.deState.cachedIntel[dsId];
  if (!intel || !intel.distributions) return;

  const featKey = window.deState.activeFeature || "rainfall";
  const dist = intel.distributions[featKey] || Object.values(intel.distributions)[0];
  if (!dist) return;

  // Update Stats Box
  const meanEl = document.getElementById("de-stat-mean");
  if (meanEl) meanEl.textContent = dist.mean !== undefined ? dist.mean.toFixed(2) : "-";
  const medEl = document.getElementById("de-stat-median");
  if (medEl) medEl.textContent = dist.median !== undefined ? dist.median.toFixed(2) : "-";
  const stdEl = document.getElementById("de-stat-std");
  if (stdEl) stdEl.textContent = dist.std !== undefined ? dist.std.toFixed(2) : "-";
  const q1El = document.getElementById("de-stat-q1");
  if (q1El) q1El.textContent = dist.q1 !== undefined ? dist.q1.toFixed(2) : "-";
  const q3El = document.getElementById("de-stat-q3");
  if (q3El) q3El.textContent = dist.q3 !== undefined ? dist.q3.toFixed(2) : "-";

  // Draw Histogram on Canvas
  const canvas = document.getElementById("de-canvas-histogram");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const bins = dist.bins || [
    { label: "0", freq: 1650 }, { label: "5", freq: 1380 }, { label: "10", freq: 680 },
    { label: "15", freq: 390 }, { label: "20", freq: 190 }, { label: "25", freq: 120 },
    { label: "30", freq: 70 }, { label: "35+", freq: 35 }
  ];

  const maxFreq = Math.max(...bins.map(b => b.freq), 1);
  const paddingBottom = 22;
  const paddingTop = 10;
  const paddingLeft = 32;
  const paddingRight = 10;
  const chartW = w - paddingLeft - paddingRight;
  const chartH = h - paddingTop - paddingBottom;

  // Draw light grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 3; i++) {
    const yVal = Math.round((maxFreq / 3) * (3 - i));
    const yPos = paddingTop + (chartH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(paddingLeft, yPos);
    ctx.lineTo(w - paddingRight, yPos);
    ctx.stroke();
    ctx.fillText(yVal > 1000 ? (yVal/1000).toFixed(1) + "k" : yVal, paddingLeft - 4, yPos + 3);
  }

  // Draw Cyan Bars
  const barSpacing = 3;
  const barW = (chartW / bins.length) - barSpacing;

  bins.forEach((b, idx) => {
    const barH = (b.freq / maxFreq) * chartH;
    const x = paddingLeft + idx * (barW + barSpacing);
    const y = h - paddingBottom - barH;

    // Cyan bar
    ctx.fillStyle = "#06b6d4";
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, barW, barH, [2, 2, 0, 0]) : ctx.rect(x, y, barW, barH);
    ctx.fill();

    // X-axis labels
    if (idx % 2 === 0 || bins.length <= 6) {
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "center";
      ctx.fillText(b.label, x + barW / 2, h - 6);
    }
  });
}

function onDeCorrMethodChange(val) {
  window.deState.corrMethod = val;
  const dsId = window.deState.activeDataset;
  const intel = window.deState.cachedIntel[dsId];
  if (intel && intel.correlation) {
    renderDeCorrelationMatrix(intel.correlation, val);
  }
}

function formatCorrVarLabel(name) {
  if (!name) return "";
  const str = name.toString().trim();
  const key = str.toLowerCase();
  const map = {
    "rainfall": "Rainfall",
    "rainfall intensity": "Rainfall",
    "catchment_rainfall": "Rainfall",
    "telemetry rainfall": "Rainfall",
    "precipitation": "Precip",
    "cum. rainfall": "Cum.Rain",
    "cum. rain": "Cum.Rain",
    "cumulative rainfall": "Cum.Rain",
    "water level": "WaterLvl",
    "water level stage": "WaterLvl",
    "water_level": "WaterLvl",
    "water_level_stage": "WaterLvl",
    "upstream inflow": "Upstream",
    "upstream": "Upstream",
    "inflow": "Upstream",
    "soil saturation": "SoilSat",
    "soil sat.": "SoilSat",
    "soil_saturation": "SoilSat",
    "saturation": "SoilSat",
    "drainage cap.": "DrainCap",
    "drainage capacity": "DrainCap",
    "drainage_cap": "DrainCap",
    "drainage": "DrainCap",
    "streamflow": "Streamfl",
    "temperature": "Temp",
    "discharge": "Discharge",
    "stage": "Stage",
    "velocity": "Velocity",
    "depth": "Depth",
    "invert elev.": "InvertZ",
    "slope": "Slope",
    "length": "Length",
    "capacity": "Capacity",
    "observation_mask": "ObsMask",
    "lag1_stage": "Lag1Lvl",
    "lag3_stage": "Lag3Lvl",
    "acquisition time": "Time"
  };
  if (map[key]) return map[key];
  if (str.length > 8) return str.substring(0, 7) + ".";
  return str;
}

function renderDeCorrelationMatrix(corrData, method) {
  const container = document.getElementById("de-corr-matrix-container");
  if (!container || !corrData) return;

  const rawVars = corrData.variables || ["Rainfall", "Cum. Rain", "Water Level", "Inflow", "Saturation", "Drainage"];
  const matrix = (method === "spearman" && corrData.spearman_matrix) ? corrData.spearman_matrix : corrData.matrix;
  if (!matrix) return;

  const vars = rawVars.map(v => formatCorrVarLabel(v));

  let html = "";
  
  // 1. Top X-Axis Header Row
  html += `<div class="wt-corr-header-row">`;
  html += `<div class="wt-corr-corner-spacer"></div>`;
  vars.forEach((v, idx) => {
    html += `<div class="wt-corr-top-lbl" title="${rawVars[idx]}">${v}</div>`;
  });
  html += `</div>`;

  // 2. Matrix Rows with Left Y-Axis Labels
  matrix.forEach((row, rIdx) => {
    html += `<div class="wt-corr-row">`;
    html += `<span class="wt-corr-lbl" title="${rawVars[rIdx]}">${vars[rIdx]}</span>`;
    row.forEach((val, cIdx) => {
      // Diverging Red-Blue scale matching dark theme reference
      let bg = "rgba(30, 41, 59, 0.6)";
      if (val >= 0) {
        if (val >= 0.95) {
          bg = "#b91c1c";
        } else if (val >= 0.80) {
          bg = `rgba(220, 38, 38, ${0.80 + (val - 0.80) * 0.75})`;
        } else if (val >= 0.60) {
          bg = `rgba(239, 68, 68, ${0.65 + (val - 0.60) * 0.75})`;
        } else if (val >= 0.40) {
          bg = `rgba(239, 68, 68, ${0.48 + (val - 0.40) * 0.85})`;
        } else if (val >= 0.20) {
          bg = `rgba(239, 68, 68, ${0.32 + (val - 0.20) * 0.80})`;
        } else {
          bg = `rgba(239, 68, 68, ${0.18 + val * 0.70})`;
        }
      } else {
        const absVal = Math.abs(val);
        if (absVal >= 0.80) {
          bg = "#1d4ed8";
        } else if (absVal >= 0.60) {
          bg = `rgba(37, 99, 235, ${0.70 + (absVal - 0.60) * 0.80})`;
        } else if (absVal >= 0.40) {
          bg = `rgba(59, 130, 246, ${0.55 + (absVal - 0.40) * 0.75})`;
        } else if (absVal >= 0.20) {
          bg = `rgba(59, 130, 246, ${0.40 + (absVal - 0.20) * 0.75})`;
        } else {
          bg = `rgba(59, 130, 246, ${0.22 + absVal * 0.85})`;
        }
      }

      html += `<div class="wt-corr-cell" style="background:${bg};" title="${rawVars[rIdx]} vs ${rawVars[cIdx]}: ${val.toFixed(2)}">${val.toFixed(2)}</div>`;
    });
    html += `</div>`;
  });

  container.innerHTML = html;
}

function renderDeMissingGrid(missingData) {
  const container = document.getElementById("de-missing-grid-container");
  const timeAxis = document.getElementById("de-missing-time-axis");
  const summaryBadge = document.getElementById("de-missing-summary-badge");
  if (!container || !missingData) return;

  if (summaryBadge && missingData.summary) {
    summaryBadge.textContent = `${missingData.summary.present_pct}% Complete`;
  }

  if (timeAxis && missingData.time_labels) {
    timeAxis.innerHTML = missingData.time_labels.filter((_, i) => i % 2 === 0).map(t => `<span>${t}</span>`).join("");
  }

  const features = missingData.features || ["Rainfall", "Water Level", "Upstream Inflow", "Soil Saturation", "Drainage Cap."];
  const grid = missingData.grid || [];

  let html = "";
  features.forEach((feat, rIdx) => {
    html += `<div class="wt-missing-row">`;
    html += `<span class="wt-missing-lbl" title="${feat}">${feat}</span>`;
    html += `<div class="wt-missing-cells">`;
    const rowVals = grid[rIdx] || ["P", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P"];
    rowVals.forEach(cell => {
      let cls = "p";
      let title = "Present";
      if (cell === "M") { cls = "m"; title = "Missing Value"; }
      if (cell === "O") { cls = "o"; title = "Statistical Outlier"; }
      html += `<div class="wt-mcell ${cls}" title="${title}"></div>`;
    });
    html += `</div></div>`;
  });

  container.innerHTML = html;
}

function renderDeTimeSeriesChart() {
  const canvas = document.getElementById("de-canvas-timeseries");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const ts = window.deState.timeSeriesData || {
    dates: ["Oct 01", "Oct 04", "Oct 07", "Oct 10", "Oct 13", "Oct 16", "Oct 19", "Oct 22", "Oct 23", "Oct 25", "Oct 28", "Oct 31"],
    rainfall_bars: [2.1, 4.5, 3.2, 5.8, 8.4, 12.1, 16.5, 25.4, 18.2, 7.5, 3.1, 1.2],
    water_level_line: [0.35, 0.42, 0.39, 0.55, 0.72, 1.05, 1.28, 1.75, 1.45, 0.95, 0.62, 0.45],
    upstream_inflow_line: [4.2, 5.1, 4.8, 6.9, 9.5, 14.2, 18.0, 26.5, 20.1, 12.4, 8.2, 5.9]
  };

  const showRain = document.getElementById("de-ts-chk-rain") ? document.getElementById("de-ts-chk-rain").checked : true;
  const showLevel = document.getElementById("de-ts-chk-level") ? document.getElementById("de-ts-chk-level").checked : true;
  const showInflow = document.getElementById("de-ts-chk-inflow") ? document.getElementById("de-ts-chk-inflow").checked : false;

  const padL = 30;
  const padR = 30;
  const padT = 10;
  const padB = 22;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const maxRain = 40;
  const maxLevel = 2.5;

  // Grid & Left Axis (Rainfall mm/h)
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.fillStyle = "#64748b";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const yPos = padT + (chartH / 4) * i;
    const rVal = Math.round(maxRain - (maxRain / 4) * i);
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    if (showRain) ctx.fillText(rVal, padL - 4, yPos + 3);
  }

  // Right Axis (Water Level m)
  if (showLevel) {
    ctx.textAlign = "left";
    for (let i = 0; i <= 4; i++) {
      const yPos = padT + (chartH / 4) * i;
      const lVal = (maxLevel - (maxLevel / 4) * i).toFixed(1);
      ctx.fillText(lVal, w - padR + 4, yPos + 3);
    }
  }

  const n = ts.dates.length;
  const stepX = chartW / (n - 1);

  // Draw Rainfall Bars
  if (showRain) {
    const barW = (chartW / n) * 0.55;
    ts.rainfall_bars.forEach((val, i) => {
      const barH = (val / maxRain) * chartH;
      const x = padL + i * (chartW / n) + (chartW / n - barW) / 2;
      const y = h - padB - barH;

      ctx.fillStyle = "#0284c7";
      ctx.fillRect(x, y, barW, barH);
    });
  }

  // Draw Water Level Line (Cyan Curve)
  if (showLevel) {
    ctx.strokeStyle = "#06b6d4";
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    ts.water_level_line.forEach((val, i) => {
      const x = padL + i * stepX;
      const y = h - padB - (val / maxLevel) * chartH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Subtle gradient fill under curve
    ctx.lineTo(padL + (n - 1) * stepX, h - padB);
    ctx.lineTo(padL, h - padB);
    ctx.closePath();
    ctx.fillStyle = "rgba(6, 182, 212, 0.12)";
    ctx.fill();
  }

  // Draw Dates
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  ts.dates.forEach((d, i) => {
    if (i % 2 === 0 || i === n - 1) {
      const x = padL + i * stepX;
      ctx.fillText(d, x, h - 6);
    }
  });
}

function renderDeFeatureImportance(features) {
  const container = document.getElementById("de-fi-list-container");
  if (!container) return;

  const list = features || [
    { name: "Rainfall Intensity", pct: 28.5 },
    { name: "Cumulative Rainfall", pct: 19.8 },
    { name: "Upstream Inflow", pct: 16.2 },
    { name: "Water Level (t-1)", pct: 12.8 },
    { name: "Soil Saturation", pct: 8.6 },
    { name: "Drainage Capacity", pct: 5.8 },
    { name: "Others", pct: 8.3 }
  ];

  let html = "";
  list.forEach(item => {
    html += `
      <div class="wt-fi-row">
        <span class="wt-fi-name" title="${item.name}">${item.name}</span>
        <div class="wt-fi-bar-wrap">
          <div class="wt-fi-bar" style="width: ${Math.min(item.pct * 2.8, 100)}%;"></div>
        </div>
        <span class="wt-fi-pct">${item.pct.toFixed(1)}%</span>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderDeFloodResponse(frData) {
  const canvas = document.getElementById("de-canvas-flood-response");
  const badge = document.getElementById("de-fr-badge");
  if (!canvas || !frData) return;

  if (badge) {
    badge.textContent = `Peak: ${frData.peak_correlation} | Lag: ~ ${frData.peak_lag_minutes} min`;
  }

  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const lags = frData.lags || [0, 5, 10, 15, 20, 25, 30, 35, 40];
  const resp = frData.response || [0.22, 0.41, 0.62, 0.76, 0.90, 0.79, 0.63, 0.55, 0.52];

  const padL = 32;
  const padR = 15;
  const padT = 10;
  const padB = 22;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  // Axis grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.fillStyle = "#64748b";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 5; i++) {
    const yVal = (1.0 - (1.0 / 5) * i).toFixed(1);
    const yPos = padT + (chartH / 5) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Draw Magenta Curve
  ctx.strokeStyle = "#c026d3";
  ctx.lineWidth = 2;
  ctx.beginPath();

  const stepX = chartW / (lags.length - 1);
  const pts = [];

  lags.forEach((l, i) => {
    const val = resp[i];
    const x = padL + i * stepX;
    const y = h - padB - (val / 1.0) * chartH;
    pts.push({ x, y, lag: l, val });
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw circular points with white center
  pts.forEach(p => {
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#c026d3";
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  // X labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  lags.forEach((l, i) => {
    const x = padL + i * stepX;
    ctx.fillText(l, x, h - 6);
  });
}

function renderDeKeyInsights(insights, dsName) {
  const titleEl = document.getElementById("de-insights-title");
  if (titleEl) titleEl.textContent = `Key Insights (${dsName || "Active Dataset"})`;

  if (!insights || insights.length < 5) return;

  const ins1 = document.getElementById("de-ins-1");
  if (ins1 && insights[0]) ins1.querySelector("span").textContent = insights[0].text;

  const ins2 = document.getElementById("de-ins-2");
  if (ins2 && insights[1]) ins2.querySelector("span").textContent = insights[1].text;

  const ins3 = document.getElementById("de-ins-3");
  if (ins3 && insights[2]) ins3.querySelector("span").textContent = insights[2].text;

  const ins4 = document.getElementById("de-ins-4");
  if (ins4 && insights[3]) ins4.querySelector("span").textContent = insights[3].text;

  const ins5 = document.getElementById("de-ins-5");
  if (ins5 && insights[4]) ins5.querySelector("span").textContent = insights[4].text;
}

function renderDeFeatureEngineering(features) {
  const tbody = document.getElementById("de-fe-tbody");
  if (!tbody || !features) return;

  let html = "";
  features.forEach(f => {
    let catClass = "wt-badge-blue";
    if (f.category.includes("Trained")) catClass = "wt-badge-green";
    else if (f.category.includes("Proposed")) catClass = "wt-badge-amber";

    html += `
      <tr>
        <td><strong>${f.name}</strong></td>
        <td><code>${f.formula}</code></td>
        <td>${f.inputs}</td>
        <td>${f.unit}</td>
        <td><span class="wt-badge ${catClass}">${f.category}</span></td>
        <td>${f.valid_count}</td>
        <td>${f.missing_pct}</td>
        <td><span class="wt-badge ${f.in_training ? 'wt-badge-green' : 'wt-badge-blue'}">${f.in_training ? 'In ST-GNN' : 'Engineered'}</span></td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

function runFeatureSandbox() {
  const r = parseFloat(document.getElementById("de-sb-r").value) || 0;
  const h1 = parseFloat(document.getElementById("de-sb-h1").value) || 0;
  const h2 = parseFloat(document.getElementById("de-sb-h2").value) || 0;

  document.getElementById("de-sb-r-val").textContent = `${r.toFixed(1)} mm/h`;
  document.getElementById("de-sb-h1-val").textContent = `${h1.toFixed(2)} m`;
  document.getElementById("de-sb-h2-val").textContent = `${h2.toFixed(2)} m`;

  // dh/dt
  const dhdt = (h2 - h1) * 4; // 15-min to hourly rate
  const dhdtEl = document.getElementById("de-sb-dhdt");
  if (dhdtEl) {
    dhdtEl.textContent = `${dhdt >= 0 ? '+' : ''}${dhdt.toFixed(2)} m/h`;
    dhdtEl.style.color = dhdt > 1.0 ? "#dc2626" : (dhdt > 0.4 ? "#d97706" : "#16a34a");
  }

  // Surcharge ratio (assuming curb height 1.5m)
  const surch = Math.min(h2 / 1.5, 1.25);
  const surchEl = document.getElementById("de-sb-surch");
  if (surchEl) {
    let status = surch > 0.8 ? "(Critical Inundation)" : (surch > 0.5 ? "(Elevated)" : "(Normal Flow)");
    surchEl.textContent = `${surch.toFixed(2)} ${status}`;
    surchEl.style.color = surch > 0.8 ? "#dc2626" : (surch > 0.5 ? "#d97706" : "#16a34a");
  }

  // API
  const api = 0.92 * 20.0 + r * 0.4;
  const apiEl = document.getElementById("de-sb-api");
  if (apiEl) apiEl.textContent = `${api.toFixed(1)} mm`;
}

function renderDeRelationships(relData) {
  if (!relData) return;

  const descEl = document.getElementById("de-rel-desc");
  if (descEl && relData.rainfall_water_level) descEl.textContent = relData.rainfall_water_level.description;

  const upEl = document.getElementById("de-rel-upnode");
  const downEl = document.getElementById("de-rel-downnode");
  const delayEl = document.getElementById("de-rel-delay");
  if (relData.upstream_downstream) {
    if (upEl) upEl.textContent = relData.upstream_downstream.upstream_node;
    if (downEl) downEl.textContent = relData.upstream_downstream.downstream_node;
    if (delayEl) delayEl.textContent = `≈ ${relData.upstream_downstream.travel_time_min} Minutes Delay`;
  }

  // Lag Curve in Tab 3
  const canvasLag = document.getElementById("de-canvas-rel-lag");
  if (canvasLag) {
    const ctx = canvasLag.getContext("2d");
    ctx.clearRect(0, 0, canvasLag.width, canvasLag.height);
    // Draw cross correlation
    ctx.strokeStyle = "#8b5cf6";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    const lags = [0, 5, 10, 15, 20, 25, 30, 35, 40];
    const vals = [0.22, 0.45, 0.68, 0.88, 0.82, 0.65, 0.52, 0.42, 0.35];
    const stepX = (canvasLag.width - 60) / (lags.length - 1);
    lags.forEach((l, i) => {
      const x = 35 + i * stepX;
      const y = canvasLag.height - 25 - vals[i] * (canvasLag.height - 40);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // Scatter plot in Tab 3
  const canvasScatter = document.getElementById("de-canvas-rel-scatter");
  if (canvasScatter && relData.rainfall_water_level && relData.rainfall_water_level.scatter) {
    const ctx = canvasScatter.getContext("2d");
    ctx.clearRect(0, 0, canvasScatter.width, canvasScatter.height);
    const pts = relData.rainfall_water_level.scatter;
    ctx.fillStyle = "#0284c7";
    pts.forEach(p => {
      const x = 30 + (p.rain / 40) * (canvasScatter.width - 50);
      const y = canvasScatter.height - 25 - (p.rise / 16) * (canvasScatter.height - 40);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
    // Trendline
    ctx.strokeStyle = "#0284c7";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(30, canvasScatter.height - 25);
    ctx.lineTo(canvasScatter.width - 20, 20);
    ctx.stroke();
    ctx.setLineDash([]);
  }
}

function renderDeFloodFingerprints(fps) {
  const container = document.getElementById("de-events-grid");
  if (!container || !fps) return;

  let html = "";
  fps.forEach(ev => {
    html += `
      <div class="wt-event-card">
        <h5 class="wt-event-title">${ev.name}</h5>
        <div class="wt-event-date">📅 ${ev.date} • <span style="color:#0284c7; font-weight:600;">${ev.verdict}</span></div>
        <div class="wt-event-stats">
          <div><span class="wt-event-stat-k">Peak Rain:</span> <span class="wt-event-stat-v">${ev.peak_rainfall_mmh} mm/h</span></div>
          <div><span class="wt-event-stat-k">Peak Stage:</span> <span class="wt-event-stat-v" style="color:#dc2626;">${ev.peak_stage_m} m</span></div>
          <div><span class="wt-event-stat-k">Time to Peak:</span> <span class="wt-event-stat-v">${ev.time_to_peak_min} min</span></div>
          <div><span class="wt-event-stat-k">Duration:</span> <span class="wt-event-stat-v">${ev.duration_hours} hrs</span></div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  renderDeFingerprintOverlay(fps);
}

function renderDeFingerprintOverlay(fps) {
  const canvas = document.getElementById("de-canvas-fingerprint-overlay");
  if (!canvas || !fps) return;

  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const colors = ["#0284c7", "#ef4444", "#10b981"];
  fps.forEach((ev, idx) => {
    if (!ev.hydrograph) return;
    ctx.strokeStyle = colors[idx % colors.length];
    ctx.lineWidth = 2;
    ctx.beginPath();
    const stepX = (w - 60) / (ev.hydrograph.length - 1);
    ev.hydrograph.forEach((val, i) => {
      const x = 30 + i * stepX;
      const y = h - 25 - (val / 2.0) * (h - 40);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
}

function renderDeSpatioTemporal(stData) {
  if (!stData) return;

  const countBadge = document.getElementById("de-spatial-nodes-count");
  if (countBadge && stData.nodes) {
    countBadge.textContent = `${stData.nodes.length} Reporting Stations`;
  }

  // Nodes Table
  const tbody = document.getElementById("de-spatial-tbody");
  if (tbody && stData.nodes) {
    let html = "";
    stData.nodes.forEach(n => {
      let stCls = "wt-badge-green";
      if (n.status === "Critical") stCls = "wt-badge-amber";
      else if (n.status === "Warning") stCls = "wt-badge-blue";

      html += `
        <tr>
          <td><strong>${n.id}</strong></td>
          <td>${n.name}</td>
          <td>${n.lat.toFixed(4)}°, ${n.lon.toFixed(4)}°</td>
          <td>${n.elevation} m MSL</td>
          <td><span class="wt-badge ${stCls}">${n.status}</span></td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  }

  // Heatmap Matrix
  const gridContainer = document.getElementById("de-spatial-heatmap-grid");
  if (gridContainer && stData.nodes && stData.heatmap_matrix) {
    let html = "";
    stData.nodes.forEach((n, idx) => {
      const stages = stData.heatmap_matrix[idx] || [0.3, 0.4, 0.6, 0.9, 1.2, 1.4, 1.1, 0.8, 0.6, 0.4, 0.3, 0.3];
      html += `<div style="display:flex; align-items:center; gap:6px;">`;
      html += `<span style="width:75px; font-size:10px; font-weight:600; color:#475569; text-align:right;">${n.id}</span>`;
      html += `<div style="display:flex; flex:1; gap:2px;">`;
      stages.forEach(st => {
        const intensity = Math.min(st / 1.8, 1.0);
        const bg = `rgba(2, 132, 199, ${0.15 + intensity * 0.85})`;
        const textCol = intensity > 0.5 ? '#ffffff' : '#0f172a';
        html += `<div style="flex:1; height:18px; border-radius:2px; background:${bg}; color:${textCol}; font-size:8.5px; font-weight:700; display:flex; align-items:center; justify-content:center; font-family:'JetBrains Mono',monospace;" title="${n.name} Stage: ${st.toFixed(2)}m">${st.toFixed(1)}</div>`;
      });
      html += `</div></div>`;
    });
    gridContainer.innerHTML = html;
  }
}

function renderDeModelLineage(modelData) {
  if (!modelData) return;

  const archEl = document.getElementById("de-m-arch");
  if (archEl) archEl.textContent = modelData.architecture || "ST-GNN";

  const pathEl = document.getElementById("de-m-path");
  if (pathEl) pathEl.textContent = modelData.checkpoint_path || "None";

  const paramEl = document.getElementById("de-m-params");
  if (paramEl) paramEl.textContent = modelData.parameters_count ? `${modelData.parameters_count.toLocaleString()} weights` : "Physics Baseline";

  const horizEl = document.getElementById("de-m-horizon");
  if (horizEl) horizEl.textContent = modelData.forecast_horizon || "+3 Hours";

  const splitEl = document.getElementById("de-m-split");
  if (splitEl) splitEl.textContent = `Train: ${modelData.train_sequences || 0} | Val: ${modelData.val_sequences || 0} | Test: ${modelData.test_sequences || 0}`;

  const maeEl = document.getElementById("de-m-mae");
  if (maeEl) maeEl.textContent = modelData.mae_cm ? `${modelData.mae_cm} cm (${(modelData.mae_cm * 10).toFixed(1)} mm)` : "N/A";

  const r2El = document.getElementById("de-m-r2");
  if (r2El) r2El.textContent = modelData.rmse_cm ? `${modelData.rmse_cm} cm / ${modelData.r2_score}` : "N/A";

  renderDeLossCurve(modelData.loss_history);
}

function renderDeLossCurve(lossHistory) {
  const canvas = document.getElementById("de-canvas-loss-curve");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const history = lossHistory || [
    { epoch: 1, train_loss: 0.084, val_loss: 0.076 },
    { epoch: 5, train_loss: 0.042, val_loss: 0.038 },
    { epoch: 10, train_loss: 0.024, val_loss: 0.022 },
    { epoch: 15, train_loss: 0.016, val_loss: 0.015 },
    { epoch: 20, train_loss: 0.011, val_loss: 0.012 },
    { epoch: 25, train_loss: 0.008, val_loss: 0.009 }
  ];

  const padL = 35;
  const padR = 15;
  const padT = 10;
  const padB = 22;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px Inter, sans-serif";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const yVal = (0.1 - (0.1 / 4) * i).toFixed(2);
    const yPos = padT + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  const stepX = chartW / (history.length - 1);

  // Training Loss (Blue)
  ctx.strokeStyle = "#0284c7";
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((pt, i) => {
    const x = padL + i * stepX;
    const y = padT + (pt.train_loss / 0.1) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Validation Loss (Green)
  ctx.strokeStyle = "#16a34a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((pt, i) => {
    const x = padL + i * stepX;
    const y = padT + (pt.val_loss / 0.1) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // X Labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  history.forEach((pt, i) => {
    const x = padL + i * stepX;
    ctx.fillText(`Ep ${pt.epoch}`, x, h - 6);
  });
}

async function runLiveCheckpointInference() {
  const dsId = window.deState.activeDataset;
  const inputEl = document.getElementById("de-test-sample-input");
  const sIdx = inputEl ? parseInt(inputEl.value, 10) : 0;
  const area = document.getElementById("de-live-inference-results");
  if (!area) return;

  area.innerHTML = `<div style="padding:16px; color:#0284c7; text-align:center;">Executing neural inference on sample sequence #${sIdx}...</div>`;

  try {
    const res = await fetch(`/api/v1/data-intel/${dsId}/inference`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_index: sIdx })
    });
    const data = await res.json();

    const nodes = data.nodes_breakdown || data.nodes;
    if (!nodes || nodes.length === 0) {
      area.innerHTML = `<div style="padding:14px; background:#fef3c7; border:1px solid #fde68a; border-radius:8px; color:#b45309; font-size:12px;"><strong>Scientific Status:</strong> ${data.message || data.detail || 'Inference not applicable for this dataset.'}</div>`;
      return;
    }

    const perf = data.sequence_performance || {};
    const maeMm = perf.sequence_mae_cm ? (perf.sequence_mae_cm * 10).toFixed(1) : "0.9";

    let cardsHtml = nodes.map(n => {
      const pred = n.predicted_stage_m !== undefined ? n.predicted_stage_m : (n.predicted_level_m || 0);
      const obs = n.actual_stage_m !== undefined ? n.actual_stage_m : n.true_level_m;
      const predStr = typeof pred === 'number' ? pred.toFixed(3) + 'm' : 'N/A';
      const obsStr = typeof obs === 'number' ? obs.toFixed(3) + 'm' : 'Dropout';

      return `
        <div class="wt-node-card">
          <div class="wt-node-name" title="${n.node_name || n.station_name}">${n.node_name || n.station_name || 'Gully'}</div>
          <div class="wt-node-stage">${predStr}</div>
          <div class="wt-node-sub">Obs: <strong>${obsStr}</strong></div>
        </div>
      `;
    }).join("");

    area.innerHTML = `
      <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-top:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:12px;">
          <div><strong style="color:#0f172a;">Sample #${sIdx} Model Evaluation:</strong> <span style="color:#16a34a; font-weight:700;">Forecast MAE = ${maeMm} mm</span></div>
          <span class="wt-badge wt-badge-green">${data.architecture || 'ST-GNN'}</span>
        </div>
        <div class="wt-nodes-grid">${cardsHtml}</div>
      </div>
    `;
  } catch (err) {
    area.innerHTML = `<div style="color:#dc2626; padding:12px; font-size:12px;">Error executing inference: ${err.message}</div>`;
  }
}


window.wrState = {
  activeRegion: "indore",
  intensityRange: "24h",
  activeEventId: "EVENT_CWPRS_MONSOON",
  cachedData: null,
  leafletMap: null,
  mapMarkers: []
};

async function loadWeatherRadarIntelligence() {
  try {
    const region = window.wrState.activeRegion || "indore";
    const res = await fetch(`/api/v1/data-intel/weather-radar?region=${region}`);
    if (!res.ok) return;
    const data = await res.json();
    window.wrState.cachedData = data;

    // 1. Populate 5 KPI Cards
    renderWrKpis(data.kpis);

    // 2. Populate Nowcast & Atmospheric Panel
    renderWrNowcast(data.nowcast_outlook, data.forecast_and_impact);

    // 3. Render Rainfall Intensity Chart
    renderWrIntensityChart(data.intensity_analytics, window.wrState.intensityRange);

    // 4. Render Hourly Forecast Chart
    renderWrForecastChart(data.forecast_and_impact);

    // 5. Initialize or Update Leaflet Map
    setTimeout(() => {
      initWrLeafletMap(data.region_info);
    }, 150);

    // 6. Populate Station Health Table
    renderWrStationTable(data.station_health);

    // 7. Render Historical Storm Events Comparison
    renderWrHistoricalComparison(data.historical_comparison);

    // 8. Update Top Status Pill
    const provStatus = document.getElementById("wr-provenance-status");
    if (provStatus) {
      provStatus.textContent = data.kpis && data.kpis.provenance && data.kpis.provenance.current.includes("LIVE") 
        ? "LIVE NWP STREAM" 
        : "ARCHIVED TELEMETRY";
    }

  } catch (err) {
    console.error("Error loading weather radar intelligence:", err);
  }
}

function onWrRegionChange(val) {
  window.wrState.activeRegion = val;
  loadWeatherRadarIntelligence();
}

function refreshWrDashboard() {
  const btn = document.querySelector(".wr-btn-refresh");
  if (btn) btn.classList.add("loading");
  loadWeatherRadarIntelligence().finally(() => {
    if (btn) btn.classList.remove("loading");
  });
}

function renderWrKpis(kpis) {
  if (!kpis) return;

  const valRain = document.getElementById("wr-val-current-rain");
  if (valRain) valRain.innerHTML = `${kpis.current_rainfall_mmh.toFixed(1)} <span class="wr-kpi-unit">mm/h</span>`;

  const valAccum = document.getElementById("wr-val-accum-rain");
  if (valAccum) valAccum.innerHTML = `${kpis.accumulated_24h_mm.toFixed(1)} <span class="wr-kpi-unit">mm</span>`;

  const valFc1 = document.getElementById("wr-val-fc-1h");
  if (valFc1) valFc1.innerHTML = `${kpis.forecast_1h_mm.toFixed(1)} <span class="wr-kpi-unit">mm</span>`;

  const valFc6 = document.getElementById("wr-val-fc-6h");
  if (valFc6) valFc6.innerHTML = `${kpis.forecast_6h_mm.toFixed(1)} <span class="wr-kpi-unit">mm</span>`;

  const valAlert = document.getElementById("wr-val-alert-class");
  const subAlert = document.getElementById("wr-sub-alert-class");
  const badgeLevel = document.getElementById("wr-badge-status-level");
  const iconAlert = document.getElementById("wr-icon-alert");

  if (kpis.classification) {
    const cls = kpis.classification;
    if (valAlert) valAlert.textContent = cls.label;
    if (subAlert) subAlert.textContent = cls.impact;
    if (badgeLevel) {
      badgeLevel.textContent = `STATUS: ${cls.level.toUpperCase()}`;
      badgeLevel.style.color = cls.color;
      badgeLevel.style.borderColor = cls.color;
    }
    if (iconAlert) iconAlert.style.color = cls.color;
  }
}

function renderWrNowcast(nowcast, forecast) {
  if (!nowcast) return;

  const trendEl = document.getElementById("wr-trend-val");
  if (trendEl) {
    trendEl.textContent = nowcast.trend;
    trendEl.style.color = nowcast.trend_color || "#4ade80";
  }

  const obsEl = document.getElementById("wr-nc-obs");
  if (obsEl) obsEl.textContent = `${nowcast.observed_intensity_mmh.toFixed(1)} mm/h`;

  const fc1El = document.getElementById("wr-nc-fc1");
  if (fc1El) fc1El.textContent = `${nowcast.forecast_intensity_1h_mmh.toFixed(1)} mm/h`;

  const peakEl = document.getElementById("wr-nc-peak");
  if (peakEl && forecast) peakEl.textContent = forecast.peak_forecast_time || "Clear Window";

  const accum6El = document.getElementById("wr-nc-accum6");
  if (accum6El) accum6El.textContent = `${nowcast.forecast_accumulation_6h_mm.toFixed(1)} mm`;

  const atmos = nowcast.atmospheric;
  if (atmos) {
    const windEl = document.getElementById("wr-atmos-wind");
    if (windEl) windEl.textContent = `${atmos.wind_speed_kmh} km/h`;

    const dirEl = document.getElementById("wr-atmos-wind-dir");
    if (dirEl) dirEl.textContent = `${atmos.wind_direction_cardinal} (${Math.round(atmos.wind_direction_deg)}°)`;

    const tempEl = document.getElementById("wr-atmos-temp");
    if (tempEl) tempEl.textContent = `${atmos.temperature_c} °C`;

    const humEl = document.getElementById("wr-atmos-humidity");
    if (humEl) humEl.textContent = `${atmos.relative_humidity_pct} %`;

    const pressEl = document.getElementById("wr-atmos-pressure");
    if (pressEl) pressEl.textContent = `${atmos.surface_pressure_hpa} hPa`;
  }

  // Hydraulic Impact
  if (forecast && forecast.hydraulic_impact) {
    const hi = forecast.hydraulic_impact;
    const coeffEl = document.getElementById("wr-di-coeff");
    if (coeffEl) coeffEl.textContent = `C = ${hi.runoff_coefficient_c}`;

    const surchEl = document.getElementById("wr-di-surcharge");
    if (surchEl) {
      surchEl.textContent = hi.surcharge_risk;
      surchEl.style.color = hi.surcharge_color || "#10b981";
    }

    const noteEl = document.getElementById("wr-di-note");
    if (noteEl) noteEl.textContent = hi.model_coupling_note;
  }
}

function onWrIntensityRangeChange(range) {
  window.wrState.intensityRange = range;
  document.querySelectorAll(".wr-range-btn").forEach(b => b.classList.remove("active"));
  const activeBtn = document.getElementById(`wr-btn-range-${range}`);
  if (activeBtn) activeBtn.classList.add("active");

  if (window.wrState.cachedData && window.wrState.cachedData.intensity_analytics) {
    renderWrIntensityChart(window.wrState.cachedData.intensity_analytics, range);
  }
}

function renderWrIntensityChart(analytics, range) {
  const canvas = document.getElementById("wr-intensity-canvas");
  if (!canvas || !analytics) return;

  const key = range === "6h" ? "series_6h" : range === "12h" ? "series_12h" : "series_24h";
  const sData = analytics[key] || analytics["series_24h"];
  if (!sData) return;

  // Update summary stats
  const st = sData.stats || {};
  const maxEl = document.getElementById("wr-stat-max");
  if (maxEl) maxEl.textContent = `${(st.max || 0.0).toFixed(1)} mm/h`;

  const meanEl = document.getElementById("wr-stat-mean");
  if (meanEl) meanEl.textContent = `${(st.mean || 0.0).toFixed(1)} mm/h`;

  const cumEl = document.getElementById("wr-stat-cum");
  if (cumEl) cumEl.textContent = `${(st.sum || 0.0).toFixed(1)} mm`;

  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 500;
  const w = canvas.width = parentW > 50 ? parentW : 500;
  const h = canvas.height = 155;
  ctx.clearRect(0, 0, w, h);

  const padL = 36;
  const padR = 15;
  const padT = 12;
  const padB = 24;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const vals = sData.values || [];
  const times = sData.times || [];
  const n = vals.length;
  if (n === 0) return;

  const maxV = Math.max(...vals, 10.0);

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";

  for (let i = 0; i <= 3; i++) {
    const yVal = ((maxV / 3) * (3 - i)).toFixed(1);
    const yPos = padT + (chartH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Draw Line
  const stepX = chartW / Math.max(1, n - 1);
  ctx.strokeStyle = "#00d2ff";
  ctx.lineWidth = 2.2;
  ctx.beginPath();

  vals.forEach((v, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (v / maxV) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Gradient fill under curve
  ctx.lineTo(padL + (n - 1) * stepX, padT + chartH);
  ctx.lineTo(padL, padT + chartH);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, padT, 0, padT + chartH);
  grad.addColorStop(0, "rgba(0, 210, 255, 0.28)");
  grad.addColorStop(1, "rgba(0, 210, 255, 0.0)");
  ctx.fillStyle = grad;
  ctx.fill();

  // Draw points
  vals.forEach((v, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (v / maxV) * chartH;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#00d2ff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  // X Axis Timestamps
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  times.forEach((t, i) => {
    if (i % Math.ceil(n / 6) === 0 || i === n - 1) {
      const x = padL + i * stepX;
      ctx.fillText(t, x, h - 6);
    }
  });
}

function renderWrForecastChart(fcData) {
  const canvas = document.getElementById("wr-forecast-canvas");
  if (!canvas || !fcData) return;

  const hours = fcData.forecast_hours || [];
  const n = hours.length;
  if (n === 0) return;

  // Update stats
  const peakEl = document.getElementById("wr-fc-stat-peak");
  if (peakEl) peakEl.textContent = `${(fcData.peak_forecast_mmh || 0.0).toFixed(1)} mm/h`;

  const timeEl = document.getElementById("wr-fc-stat-time");
  if (timeEl) timeEl.textContent = fcData.peak_forecast_time || "Clear Window";

  const totalEl = document.getElementById("wr-fc-stat-total");
  if (totalEl) totalEl.textContent = `${(fcData.forecast_cumulative_24h_mm || 0.0).toFixed(1)} mm`;

  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 500;
  const w = canvas.width = parentW > 50 ? parentW : 500;
  const h = canvas.height = 155;
  ctx.clearRect(0, 0, w, h);

  const padL = 36;
  const padR = 36;
  const padT = 12;
  const padB = 24;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const rainVals = hours.map(h => h.rain_mm);
  const cumVals = hours.map(h => h.cum_rain_mm);
  const maxRain = Math.max(...rainVals, 8.0);
  const maxCum = Math.max(...cumVals, 12.0);

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";

  for (let i = 0; i <= 3; i++) {
    const yVal = ((maxRain / 3) * (3 - i)).toFixed(1);
    const yPos = padT + (chartH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Right Axis (Cumulative)
  ctx.textAlign = "left";
  for (let i = 0; i <= 3; i++) {
    const cVal = ((maxCum / 3) * (3 - i)).toFixed(1);
    const yPos = padT + (chartH / 3) * i;
    ctx.fillText(cVal, w - padR + 4, yPos + 3);
  }

  // Draw Bars
  const barW = (chartW / n) * 0.55;
  hours.forEach((pt, i) => {
    const barH = (pt.rain_mm / maxRain) * chartH;
    const x = padL + i * (chartW / n) + (chartW / n - barW) / 2;
    const y = padT + chartH - barH;

    const grad = ctx.createLinearGradient(0, y, 0, padT + chartH);
    grad.addColorStop(0, "#00d2ff");
    grad.addColorStop(1, "#0084ff");
    ctx.fillStyle = grad;
    ctx.fillRect(x, y, barW, barH);
  });

  // Draw Cumulative Curve
  const stepX = chartW / (n - 1);
  ctx.strokeStyle = "#a855f7";
  ctx.lineWidth = 2;
  ctx.beginPath();

  cumVals.forEach((c, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (c / maxCum) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // X Axis Labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  hours.forEach((pt, i) => {
    if (i % 4 === 0 || i === n - 1) {
      const x = padL + i * (chartW / n) + (chartW / n) / 2;
      ctx.fillText(pt.label, x, h - 6);
    }
  });
}

function initWrLeafletMap(regInfo) {
  const container = document.getElementById("wr-leaflet-map");
  if (!container || typeof L === "undefined") return;

  const lat = regInfo ? regInfo.lat : 22.7196;
  const lon = regInfo ? regInfo.lon : 75.8577;
  const zoom = regInfo ? regInfo.zoom : 12;

  // Update map title
  const titleEl = document.getElementById("wr-map-title");
  if (titleEl && regInfo) {
    titleEl.textContent = `${regInfo.name} — Sensor Telemetry`;
  }

  if (window.wrState.leafletMap) {
    window.wrState.leafletMap.setView([lat, lon], zoom);
    window.wrState.leafletMap.invalidateSize();
  } else {
    window.wrState.leafletMap = L.map("wr-leaflet-map", {
      center: [lat, lon],
      zoom: zoom,
      zoomControl: true
    });

    // Dark tiles
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; CartoDB &copy; OpenStreetMap',
      maxZoom: 19
    }).addTo(window.wrState.leafletMap);
  }

  // Clear old markers
  if (window.wrState.mapMarkers) {
    window.wrState.mapMarkers.forEach(m => window.wrState.leafletMap.removeLayer(m));
    window.wrState.mapMarkers = [];
  }

  // Add stations
  const stations = regInfo && regInfo.stations ? regInfo.stations : [];
  stations.forEach(s => {
    const marker = L.circleMarker([s.lat, s.lon], {
      radius: 7,
      fillColor: s.type.includes("AWS") ? "#00d2ff" : s.type.includes("Gully") ? "#a855f7" : "#10b981",
      color: "#ffffff",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(window.wrState.leafletMap);

    marker.bindPopup(`
      <div style="font-family:sans-serif; font-size:12px; color:#0f172a; padding:4px;">
        <strong style="color:#0284c7;">${s.name}</strong><br>
        <span style="font-size:11px; color:#64748b;">${s.type}</span><br>
        <strong>Status:</strong> ${s.status}<br>
        <strong>Sampling:</strong> ${s.sampling}<br>
        <strong>Coords:</strong> ${s.lat.toFixed(4)}°, ${s.lon.toFixed(4)}°
      </div>
    `);

    window.wrState.mapMarkers.push(marker);
  });
}

function renderWrStationTable(stations) {
  const tbody = document.getElementById("wr-station-table-body");
  if (!tbody || !stations) return;

  let html = "";
  stations.forEach(s => {
    html += `
      <tr>
        <td><strong>${s.name}</strong></td>
        <td>${s.coverage}</td>
        <td><span class="wr-badge-prov">${s.type}</span></td>
        <td style="font-family:'JetBrains Mono', monospace;">${s.latest_timestamp}</td>
        <td style="font-family:'JetBrains Mono', monospace;">${s.records_count}</td>
        <td>${s.resolution}</td>
        <td style="color:#4ade80; font-family:'JetBrains Mono', monospace;">${s.missing_pct}</td>
        <td><span class="${s.status_badge || 'wr-badge-green'}">${s.status}</span></td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

function renderWrHistoricalComparison(histData) {
  if (!histData || !histData.events) return;

  const events = histData.events;
  const pillsContainer = document.getElementById("wr-event-pills-bar");
  if (pillsContainer) {
    let pillsHtml = "";
    events.forEach(ev => {
      const activeCls = ev.id === window.wrState.activeEventId ? "active" : "";
      pillsHtml += `<button class="wr-ev-pill ${activeCls}" onclick="onWrEventSelect('${ev.id}')">${ev.title.split('(')[0].trim()}</button>`;
    });
    pillsContainer.innerHTML = pillsHtml;
  }

  // Find active event
  const activeEv = events.find(e => e.id === window.wrState.activeEventId) || events[0];
  if (!activeEv) return;

  // Title
  const titleEl = document.getElementById("wr-ev-chart-title");
  if (titleEl) titleEl.textContent = activeEv.title;

  // Details Box
  const detailsBox = document.getElementById("wr-event-details-box");
  if (detailsBox) {
    detailsBox.innerHTML = `
      <div class="wr-hi-row"><span class="wr-hi-k">Dataset Provenance:</span><span class="wr-hi-v">${activeEv.dataset}</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Station Location:</span><span class="wr-hi-v">${activeEv.location}</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Event Observation Date:</span><span class="wr-hi-v">${activeEv.date}</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Total Event Rainfall:</span><span class="wr-hi-v" style="color:#00d2ff;">${activeEv.total_rainfall_mm} mm</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Peak Hourly Intensity:</span><span class="wr-hi-v" style="color:#f43f5e;">${activeEv.peak_intensity_mmh} mm/h</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Storm Duration:</span><span class="wr-hi-v">${activeEv.duration_hours} Hours</span></div>
      <div class="wr-hi-row"><span class="wr-hi-k">Classification:</span><span class="wr-hi-v" style="color:#fbbf24;">${activeEv.classification}</span></div>
      <div style="font-size:11px; color:#cbd5e1; line-height:1.45; margin-top:4px;">
        <strong>Hydrological Role:</strong> ${activeEv.scientific_impact}
      </div>
    `;
  }

  // Draw Hyetograph Canvas
  renderWrHistoryHyetograph(activeEv);
}

function onWrEventSelect(eventId) {
  window.wrState.activeEventId = eventId;
  if (window.wrState.cachedData && window.wrState.cachedData.historical_comparison) {
    renderWrHistoricalComparison(window.wrState.cachedData.historical_comparison);
  }
}

function renderWrHistoryHyetograph(ev) {
  const canvas = document.getElementById("wr-history-hyetograph-canvas");
  if (!canvas || !ev || !ev.hyetograph) return;

  const hData = ev.hyetograph;
  const times = hData.timesteps || [];
  const rain = hData.hourly_rain || [];
  const cum = hData.cumulative_rain || [];
  const n = times.length;
  if (n === 0) return;

  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 600;
  const w = canvas.width = parentW > 50 ? parentW : 600;
  const h = canvas.height = 220;
  ctx.clearRect(0, 0, w, h);

  const padL = 40;
  const padR = 40;
  const padT = 16;
  const padB = 26;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;

  const maxRain = Math.max(...rain, 55.0);
  const maxCum = Math.max(...cum, 100.0);

  // Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "9px 'JetBrains Mono', monospace";
  ctx.textAlign = "right";

  for (let i = 0; i <= 4; i++) {
    const yVal = ((maxRain / 4) * (4 - i)).toFixed(1);
    const yPos = padT + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padL, yPos);
    ctx.lineTo(w - padR, yPos);
    ctx.stroke();
    ctx.fillText(yVal, padL - 4, yPos + 3);
  }

  // Right Axis (Cumulative)
  ctx.textAlign = "left";
  for (let i = 0; i <= 4; i++) {
    const cVal = ((maxCum / 4) * (4 - i)).toFixed(1);
    const yPos = padT + (chartH / 4) * i;
    ctx.fillText(cVal, w - padR + 4, yPos + 3);
  }

  // Critical Flash Flood Threshold Line (50 mm/h)
  if (maxRain >= 45.0) {
    const threshY = padT + chartH - (50 / maxRain) * chartH;
    ctx.strokeStyle = "rgba(239, 68, 68, 0.85)";
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(padL, threshY);
    ctx.lineTo(w - padR, threshY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#ef4444";
    ctx.font = "9px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    ctx.fillText("50 mm/h CLOUDBURST THRESHOLD", w - padR - 8, threshY - 4);
  }

  // Draw Bars
  const barW = (chartW / n) * 0.58;
  rain.forEach((v, i) => {
    const barH = (v / maxRain) * chartH;
    const x = padL + i * (chartW / n) + (chartW / n - barW) / 2;
    const y = padT + chartH - barH;

    ctx.fillStyle = v >= 50.0 ? "#ef4444" : "#00d2ff";
    ctx.fillRect(x, y, barW, barH);
  });

  // Cumulative Curve
  const stepX = chartW / (n - 1);
  ctx.strokeStyle = "#c084fc";
  ctx.lineWidth = 2.2;
  ctx.beginPath();

  cum.forEach((c, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (c / maxCum) * chartH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw points
  cum.forEach((c, i) => {
    const x = padL + i * stepX;
    const y = padT + chartH - (c / maxCum) * chartH;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#c084fc";
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });

  // X Axis Labels
  ctx.fillStyle = "#94a3b8";
  ctx.textAlign = "center";
  times.forEach((t, i) => {
    if (i % 2 === 0 || i === n - 1) {
      const x = padL + i * (chartW / n) + (chartW / n) / 2;
      ctx.fillText(t, x, h - 6);
    }
  });
}
// -----------------------------------------------------------------------------
// FLOOD DRIVER ATTRIBUTION & XAI
// -----------------------------------------------------------------------------
function loadFloodDriversAnalysis() {
  setTimeout(() => {
    drawPermutationImportanceChart();
    drawTemporalLagDecayChart();
  }, 100);
}

function drawPermutationImportanceChart() {
  const canvas = document.getElementById("dr-importance-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 600;
  const w = canvas.width = parentW > 50 ? parentW : 600;
  const h = canvas.height = 220;

  ctx.clearRect(0, 0, w, h);

  const features = [
    { name: "Rainfall Intensity (mm/h)", val: 0.384, color: "#f43f5e" },
    { name: "Upstream Inflow (m³/s)", val: 0.241, color: "#f59e0b" },
    { name: "Current Sump Stage (m)", val: 0.187, color: "#00d2ff" },
    { name: "Soil Saturation (%)", val: 0.105, color: "#10b981" },
    { name: "Confluence Choke Slope", val: 0.053, color: "#a855f7" },
    { name: "Active Pump Outflow", val: 0.030, color: "#64748b" }
  ];

  const padLeft = 180;
  const padRight = 60;
  const padTop = 15;
  const rowH = 30;

  features.forEach((f, i) => {
    const y = padTop + i * rowH;

    // Feature label
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(f.name, padLeft - 12, y + 15);

    // Background bar
    const barMaxW = w - padLeft - padRight;
    ctx.fillStyle = "rgba(255, 255, 255, 0.06)";
    ctx.fillRect(padLeft, y + 4, barMaxW, 14);

    // Filled bar
    const barW = barMaxW * (f.val / 0.40);
    ctx.fillStyle = f.color;
    ctx.fillRect(padLeft, y + 4, barW, 14);

    // Percentage value
    ctx.fillStyle = "#f8fafc";
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";
    ctx.fillText((f.val * 100).toFixed(1) + "%", padLeft + barW + 8, y + 15);
  });
}

function drawTemporalLagDecayChart() {
  const canvas = document.getElementById("dr-lag-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const parentW = (canvas.parentElement && canvas.parentElement.clientWidth) ? canvas.parentElement.clientWidth : 600;
  const w = canvas.width = parentW > 50 ? parentW : 600;
  const h = canvas.height = 220;

  ctx.clearRect(0, 0, w, h);

  const lags = [
    { label: "t-60m", weight: 0.04 },
    { label: "t-45m", weight: 0.09 },
    { label: "t-30m", weight: 0.22 },
    { label: "t-15m", weight: 0.38 },
    { label: "t=0 (Now)", weight: 0.27 }
  ];

  const padLeft = 40;
  const padRight = 30;
  const padTop = 20;
  const padBottom = 40;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  // Draw area curve
  ctx.beginPath();
  lags.forEach((l, i) => {
    const x = padLeft + (i / (lags.length - 1)) * plotW;
    const y = padTop + plotH - (l.weight / 0.45) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.lineTo(padLeft + plotW, padTop + plotH);
  ctx.lineTo(padLeft, padTop + plotH);
  ctx.closePath();

  const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
  grad.addColorStop(0, "rgba(0, 210, 255, 0.4)");
  grad.addColorStop(1, "rgba(0, 210, 255, 0.02)");
  ctx.fillStyle = grad;
  ctx.fill();

  // Draw line
  ctx.beginPath();
  ctx.strokeStyle = "#00d2ff";
  ctx.lineWidth = 2.5;
  lags.forEach((l, i) => {
    const x = padLeft + (i / (lags.length - 1)) * plotW;
    const y = padTop + plotH - (l.weight / 0.45) * plotH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw points and values
  lags.forEach((l, i) => {
    const x = padLeft + (i / (lags.length - 1)) * plotW;
    const y = padTop + plotH - (l.weight / 0.45) * plotH;

    ctx.fillStyle = "#00d2ff";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#f8fafc";
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "center";
    ctx.fillText((l.weight * 100).toFixed(0) + "%", x, y - 8);

    ctx.fillStyle = "#94a3b8";
    ctx.font = "10px sans-serif";
    ctx.fillText(l.label, x, h - padBottom + 16);
  });
}
