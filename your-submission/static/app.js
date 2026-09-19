/**
 * Rachel's Smart Commuter Companion — Frontend Application.
 * Integrates OpenStreetMap (Leaflet), dynamic disruption layers,
 * proactive noise filtering, and offline tunnel caching.
 */

let map;
let layersGroup;
let currentData = null;
let activeRouteId = 'primary_ewl';

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  loadCommuteStatus();
  setupEventListeners();
  setupOfflineDetection();
});

/**
 * Initializes Leaflet Map with required OpenStreetMap base and attribution.
 */
function initMap() {
  // Center roughly between Tampines and Raffles Place
  map = L.map('map', {
    zoomControl: false,
    attributionControl: true
  }).setView([1.3190, 103.8980], 12);

  // Position zoom controls in upper right for mobile thumb ergonomics
  L.control.zoom({ position: 'topright' }).addTo(map);

  // REQUIRED BY BRIEF: OpenStreetMap tile base with legal attribution
  const osmTileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
  });
  osmTileLayer.addTo(map);

  layersGroup = L.featureGroup().addTo(map);
}

/**
 * Fetches commute evaluation from backend API or loads from offline cache.
 */
async function loadCommuteStatus() {
  try {
    const resp = await fetch('/api/status');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    currentData = data;
    
    // Save to local storage for offline tunnel resilience
    localStorage.setItem('rachel_commute_cache', JSON.stringify(data));
    hideOfflineBadge();
    renderUI(data);
  } catch (err) {
    console.warn('Network unavailable, attempting offline cache:', err);
    const cached = localStorage.getItem('rachel_commute_cache');
    if (cached) {
      currentData = JSON.parse(cached);
      showOfflineBadge();
      renderUI(currentData);
    }
  }
}

/**
 * Renders all UI elements, status banner, route cards, and map layers.
 */
function renderUI(data) {
  updateTopBar(data);
  updateAlertCard(data);
  updateRouteCards(data);
  renderMapLayers(data);
}

function updateTopBar(data) {
  document.getElementById('sim-time').textContent = data.simulated_time || '07:20 AM';
  const badge = document.getElementById('source-badge');
  badge.textContent = data.source_badge || 'Live';
  if (data.source_badge && data.source_badge.toLowerCase().includes('disruption')) {
    badge.className = 'px-1.5 py-0.5 text-[10px] font-semibold bg-rose-950/80 text-rose-400 border border-rose-800/60 rounded';
  } else {
    badge.className = 'px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 rounded';
  }
}

function updateAlertCard(data) {
  const decision = data.decision;
  const alertCard = document.getElementById('alert-card');
  const alertIcon = document.getElementById('alert-icon');
  const statusLabel = document.getElementById('alert-status-label');
  const headline = document.getElementById('alert-headline');
  const detail = document.getElementById('alert-detail');
  const actionRow = document.getElementById('alert-action-row');
  const weatherChip = document.getElementById('weather-chip');
  const filterBadge = document.getElementById('noise-filter-badge');

  filterBadge.textContent = `Filter: <${decision.threshold_minutes}m Silent`;

  // Weather chip update
  if (data.weather) {
    const isRain = data.weather.rain_alert;
    weatherChip.innerHTML = isRain
      ? `<i class="fa-solid fa-cloud-showers-heavy text-blue-400"></i> ${data.weather.origin_forecast}`
      : `<i class="fa-solid fa-sun text-amber-400"></i> ${data.weather.origin_forecast}`;
  }

  if (decision.urgency === 'CALM') {
    alertCard.className = 'rounded-xl p-3 border transition-all duration-300 shadow-lg bg-emerald-950/40 border-emerald-700/60';
    alertIcon.className = 'w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs';
    alertIcon.innerHTML = '<i class="fa-solid fa-check"></i>';
    statusLabel.className = 'text-xs font-bold uppercase tracking-wider text-emerald-400';
    statusLabel.textContent = 'On Schedule (Quiet)';
    headline.textContent = decision.headline;
    detail.textContent = decision.one_line_advice;
    actionRow.classList.add('hidden');
    activeRouteId = 'primary_ewl';
  } else {
    alertCard.className = 'rounded-xl p-3 border transition-all duration-300 shadow-lg bg-rose-950/70 border-rose-600/80 ring-1 ring-rose-500/40';
    alertIcon.className = 'w-5 h-5 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center text-xs';
    alertIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation animate-bounce"></i>';
    statusLabel.className = 'text-xs font-bold uppercase tracking-wider text-rose-400';
    statusLabel.textContent = 'Proactive Interruption';
    headline.textContent = decision.headline;
    detail.textContent = decision.one_line_advice;
    actionRow.classList.remove('hidden');
    activeRouteId = 'bypass_dtl';
  }
}

function updateRouteCards(data) {
  const routes = data.routes;
  
  // EWL Card
  const ewl = routes.primary_ewl;
  const ewlCard = document.getElementById('card-primary-ewl');
  const ewlArrival = document.getElementById('ewl-arrival-time');
  const ewlDelay = document.getElementById('ewl-delay-tag');
  const ewlMeta = document.getElementById('ewl-route-meta');
  const ewlCrowd = document.getElementById('ewl-crowd-chip');

  ewlArrival.textContent = ewl.estimated_arrival;
  ewlMeta.textContent = `Leaves 07:40 • ${ewl.total_duration_min} mins total`;

  if (ewl.delay_minutes > 0) {
    ewlArrival.className = 'text-sm font-bold text-rose-400';
    ewlDelay.className = 'text-[10px] text-rose-400 font-semibold';
    ewlDelay.textContent = `+${ewl.delay_minutes}m Delay (LATE)`;
    ewlCrowd.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-rose-950 text-rose-300 border border-rose-800';
    ewlCrowd.textContent = 'CROWD: HIGH';
  } else {
    ewlArrival.className = 'text-sm font-bold text-emerald-400';
    ewlDelay.className = 'text-[10px] text-emerald-400';
    ewlDelay.textContent = 'On Time';
    ewlCrowd.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-950 text-amber-300 border border-amber-800';
    ewlCrowd.textContent = 'CROWD: MOD';
  }

  // Highlight active route card
  highlightActiveCard();
}

function highlightActiveCard() {
  document.querySelectorAll('.route-card').forEach(card => card.classList.remove('active-route'));
  if (activeRouteId === 'primary_ewl') {
    document.getElementById('card-primary-ewl')?.classList.add('active-route');
  } else if (activeRouteId === 'bypass_dtl') {
    document.getElementById('card-bypass-dtl')?.classList.add('active-route');
  } else if (activeRouteId === 'bypass_bus10e') {
    document.getElementById('card-bypass-bus10e')?.classList.add('active-route');
  }
}

/**
 * Renders spatial tracks, disrupted corridor styling, and station nodes.
 */
function renderMapLayers(data) {
  layersGroup.clearLayers();
  const layers = data.map_layers;
  const decision = data.decision;
  const isEwlDisrupted = decision.is_delayed;

  // 1. Walking First/Last Mile Legs (Grey dashed lines)
  const walking = layers.walking_legs;
  Object.values(walking).forEach(walk => {
    L.polyline(walk.coords, {
      color: '#94a3b8',
      weight: 3,
      dashArray: '4, 6',
      opacity: 0.9
    }).addTo(layersGroup);
  });

  // 2. DTL Bypass Track (Blue Polyline)
  const dtlPolyline = L.polyline(layers.dtl_track, {
    color: '#005EC4',
    weight: activeRouteId === 'bypass_dtl' ? 6 : 3.5,
    opacity: activeRouteId === 'bypass_dtl' ? 1.0 : 0.6,
  }).addTo(layersGroup);
  dtlPolyline.bindPopup('<b>Downtown Line (DTL)</b><br>Reliable alternative bypass');

  // 3. EWL Primary Track (Green or Disrupted Red)
  if (!isEwlDisrupted) {
    const ewlPoly = L.polyline(layers.ewl_track, {
      color: '#009645',
      weight: activeRouteId === 'primary_ewl' ? 6 : 4,
      opacity: 1.0,
    }).addTo(layersGroup);
    ewlPoly.bindPopup('<b>East-West Line (EWL)</b><br>Operating normally');
  } else {
    // Split EWL into unaffected (Tampines to Tanah Merah, Bugis to Raffles Place)
    // and Disrupted (Bedok to Bugis, red dashed)
    const ewlStations = layers.ewl_stations;
    const preCoords = ewlStations.slice(0, 4).map(s => s.coords); // EW2-EW5
    const disruptedCoords = ewlStations.slice(3, 11).map(s => s.coords); // EW5-EW12
    const postCoords = ewlStations.slice(10).map(s => s.coords); // EW12-EW14

    L.polyline(preCoords, { color: '#009645', weight: 4, opacity: 0.8 }).addTo(layersGroup);
    L.polyline(postCoords, { color: '#009645', weight: 4, opacity: 0.8 }).addTo(layersGroup);

    // High visibility red disrupted segment with warning popup
    const disruptedPoly = L.polyline(disruptedCoords, {
      color: '#EF4444',
      weight: 6,
      dashArray: '6, 8',
      opacity: 1.0,
      lineCap: 'round'
    }).addTo(layersGroup);
    
    disruptedPoly.bindPopup(
      '<div class="text-xs"><b>⚠️ EWL Disrupted Corridor</b><br>' +
      '<span class="text-rose-600 font-semibold">Track fault: Bedok - Bugis</span><br>' +
      'Free bridging buses activated at affected stations.</div>'
    );
  }

  // 4. Express Bus 10e Track (Light Purple / Orange)
  if (layers.bus10e_track) {
    L.polyline(layers.bus10e_track, {
      color: '#8b5cf6',
      weight: activeRouteId === 'bypass_bus10e' ? 5 : 2.5,
      dashArray: '3, 5',
      opacity: activeRouteId === 'bypass_bus10e' ? 0.9 : 0.4
    }).addTo(layersGroup).bindPopup('<b>Express Bus 10e</b><br>Direct ECP route to CBD');
  }

  // 5. Station Markers
  layers.ewl_stations.forEach(stn => {
    const isDisruptedStn = isEwlDisrupted && ['EW5','EW6','EW7','EW8','EW9','EW10','EW11','EW12'].includes(stn.code);
    const pinClass = isDisruptedStn ? 'station-pin pin-disrupted' : 'station-pin pin-ewl';
    
    const icon = L.divIcon({
      className: '',
      html: `<div class="${pinClass}"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });

    const marker = L.marker(stn.coords, { icon }).addTo(layersGroup);
    marker.bindPopup(`
      <div class="p-1 text-xs">
        <strong>${stn.code} — ${stn.name}</strong><br>
        <span class="${isDisruptedStn ? 'text-rose-600 font-bold' : 'text-emerald-700'}">
          ${isDisruptedStn ? '⚠️ Track Fault Delay' : 'Service Normal'}
        </span>
      </div>
    `);
  });

  layers.dtl_stations.forEach(stn => {
    const icon = L.divIcon({
      className: '',
      html: `<div class="station-pin pin-dtl"></div>`,
      iconSize: [12, 12],
      iconAnchor: [6, 6]
    });
    const marker = L.marker(stn.coords, { icon }).addTo(layersGroup);
    marker.bindPopup(`
      <div class="p-1 text-xs">
        <strong>${stn.code} — ${stn.name}</strong><br>
        <span class="text-blue-700">Downtown Line Bypass</span>
      </div>
    `);
  });

  // 6. Home & Office Custom Markers
  const homeIcon = L.divIcon({
    className: '',
    html: '<div class="w-6 h-6 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-house"></i></div>',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
  L.marker(layers.origin.coords, { icon: homeIcon }).addTo(layersGroup).bindPopup('<b>Rachel\'s Home</b><br>Blk 230 Tampines St 21<br>Leaves 07:40 AM');

  const officeIcon = L.divIcon({
    className: '',
    html: '<div class="w-6 h-6 rounded-full bg-amber-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-briefcase"></i></div>',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
  L.marker(layers.destination.coords, { icon: officeIcon }).addTo(layersGroup).bindPopup('<b>Rachel\'s Desk</b><br>One Raffles Place<br>Target: 08:45 AM (Meeting 09:00)');
}

function setupEventListeners() {
  // Switch to bypass button in alert card
  document.getElementById('btn-accept-bypass')?.addEventListener('click', () => {
    activeRouteId = 'bypass_dtl';
    highlightActiveCard();
    if (currentData) renderMapLayers(currentData);
    map.flyTo([1.3190, 103.8980], 12);
  });

  // Clickable route cards
  document.getElementById('card-primary-ewl')?.addEventListener('click', () => {
    activeRouteId = 'primary_ewl';
    highlightActiveCard();
    if (currentData) renderMapLayers(currentData);
  });

  document.getElementById('card-bypass-dtl')?.addEventListener('click', () => {
    activeRouteId = 'bypass_dtl';
    highlightActiveCard();
    if (currentData) renderMapLayers(currentData);
  });

  document.getElementById('card-bypass-bus10e')?.addEventListener('click', () => {
    activeRouteId = 'bypass_bus10e';
    highlightActiveCard();
    if (currentData) renderMapLayers(currentData);
  });

  // Scenario drawer controls
  const toggleBtn = document.getElementById('scenario-toggle-btn');
  const closeBtn = document.getElementById('scenario-close-btn');
  const drawer = document.getElementById('scenario-drawer');

  toggleBtn?.addEventListener('click', () => {
    populateScenariosDrawer();
    drawer.classList.remove('hidden');
  });

  closeBtn?.addEventListener('click', () => {
    drawer.classList.add('hidden');
  });

  // Noise threshold select
  document.getElementById('select-noise-threshold')?.addEventListener('change', async (e) => {
    const threshold = e.target.value;
    try {
      const resp = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delay_threshold_min: threshold })
      });
      const res = await resp.json();
      if (res.data) {
        currentData = res.data;
        renderUI(currentData);
      }
    } catch (err) {
      console.error(err);
    }
  });
}

async function populateScenariosDrawer() {
  const container = document.getElementById('scenarios-options-container');
  container.innerHTML = '<div class="text-xs text-slate-400 py-2">Loading presets...</div>';

  try {
    const resp = await fetch('/api/scenarios');
    const data = await resp.json();
    const current = data.current;
    
    container.innerHTML = '';
    data.scenarios.forEach(sc => {
      const isSelected = sc.id === current;
      const btn = document.createElement('button');
      btn.className = `w-full text-left p-2.5 rounded-lg border transition flex flex-col gap-1 ${
        isSelected 
          ? 'bg-indigo-950/70 border-indigo-500/80 ring-1 ring-indigo-500/40' 
          : 'bg-slate-800/60 border-slate-700 hover:bg-slate-800'
      }`;
      btn.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-xs text-white">${sc.name}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded ${isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'}">${sc.badge}</span>
        </div>
        <p class="text-[11px] text-slate-400 leading-snug">${sc.description}</p>
      `;

      btn.addEventListener('click', async () => {
        await switchScenario(sc.id);
        document.getElementById('scenario-drawer').classList.add('hidden');
      });
      container.appendChild(btn);
    });

    // Add Live API Option
    const liveBtn = document.createElement('button');
    const isLive = current === 'live';
    liveBtn.className = `w-full text-left p-2.5 rounded-lg border transition flex flex-col gap-1 ${
      isLive 
        ? 'bg-indigo-950/70 border-indigo-500/80 ring-1 ring-indigo-500/40' 
        : 'bg-slate-800/60 border-slate-700 hover:bg-slate-800'
    }`;
    liveBtn.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-xs text-white">📡 Live LTA DataMall & Weather</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded ${isLive ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300'}">Live Feed</span>
      </div>
      <p class="text-[11px] text-slate-400 leading-snug">Polls actual DataMall TrainServiceAlerts & data.gov.sg nowcasts directly.</p>
    `;
    liveBtn.addEventListener('click', async () => {
      await switchScenario('live');
      document.getElementById('scenario-drawer').classList.add('hidden');
    });
    container.appendChild(liveBtn);

  } catch (err) {
    container.innerHTML = '<div class="text-xs text-rose-400 py-2">Failed to load scenarios.</div>';
  }
}

async function switchScenario(scenarioId) {
  try {
    const resp = await fetch('/api/scenario/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId })
    });
    const res = await resp.json();
    if (res.data) {
      currentData = res.data;
      localStorage.setItem('rachel_commute_cache', JSON.stringify(currentData));
      renderUI(currentData);
    }
  } catch (err) {
    console.error(err);
  }
}

function setupOfflineDetection() {
  window.addEventListener('offline', () => showOfflineBadge());
  window.addEventListener('online', () => hideOfflineBadge());
}

function showOfflineBadge() {
  const badge = document.getElementById('offline-indicator');
  if (badge) badge.classList.remove('hidden');
}

function hideOfflineBadge() {
  const badge = document.getElementById('offline-indicator');
  if (badge) badge.classList.add('hidden');
}

