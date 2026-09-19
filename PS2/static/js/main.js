/**
 * StationBuddy — Main Application Coordinator.
 * Orchestrates MapController, UIController, offline caching,
 * dynamic arrival timing changes, and custom persona journey calculations.
 * Owned by: Teammate A (Frontend & Mobile UX)
 */

import { MapController } from './map_controller.js?v=20260919i';
import { UIController } from './ui_controller.js?v=20260919i';
import { offlineCache } from './offline_cache.js?v=20260919i';

let currentData = null;
let currentArbitraryRoute = null;
let currentSearchedRoutes = [];
let activeRouteId = 'primary_ewl';
let currentArrivalTime = '08:45 AM';
let currentOrigin = 'Blk 230 Tampines St 21 (Home)';
let currentDest = 'One Raffles Place, CBD (Office)';

// Custom persona & routing state
let isCustomJourneyActive = false;
let customJourneyResult = null;
let savedPersonas = [];
let activeCustomPersonaId = 'rachel';

let mapController;
let uiController;

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Map
  mapController = new MapController('map');
  mapController.init();

  // 2. Initialize UI Controller with comprehensive callbacks
  uiController = new UIController({
    onSelectRoute: (routeId) => {
      activeRouteId = routeId;
      uiController.highlightActiveCard(activeRouteId);
      if (isCustomJourneyActive && routeId === 'primary_ewl' && customJourneyResult) {
        mapController.renderCustomRoute(customJourneyResult.route, customJourneyResult.profile);
      } else if (currentData) {
        mapController.renderLayers(currentData, activeRouteId);
        updateBannerForSelectedRoute(routeId, currentData);
      } else if (routeId === 'arbitrary_route' && currentArbitraryRoute) {
        mapController.renderArbitraryRoute(currentArbitraryRoute);
      }
    },
    onToggleAllRoutes: () => {
      if (currentData) {
        const isShowingAll = mapController.toggleAllRoutes(currentData, activeRouteId);
        uiController.setAllRoutesButtonState(isShowingAll, false);
      }
    },
    onOpenScenarios: () => {
      loadAndRenderScenarios();
    },
    onThresholdChange: async (threshold) => {
      await updateSettings({ delay_threshold_min: threshold });
    },
    onArrivalChange: async (newTime) => {
      currentArrivalTime = newTime;
      if (!isCustomJourneyActive) {
        await loadCommuteStatus(currentArrivalTime, currentOrigin, currentDest);
      }
    },
    onLocationChange: async (origin, dest) => {
      await handleLocationChange(origin, dest);
    },
    onSelectSearchedRoute: (routeIndex) => {
      const selected = currentSearchedRoutes[routeIndex];
      if (!selected) return;
      currentArbitraryRoute = selected;
      uiController.renderArbitraryRouteCard(selected, currentSearchedRoutes);
      mapController.renderArbitraryRoute(selected);
    },
    onRecenter: () => {
      mapController.panToCenter();
    },
    onSelectPersona: async (pId) => {
      await switchPersona(pId);
    },
    onCyclePersona: async () => {
      await cyclePersona();
    },
    // Custom Persona & Adapter Callbacks
    onSelectPersonaDropdown: async (personaId) => {
      await handleSelectPersonaDropdown(personaId);
    },
    onNewPersona: () => {
      handleNewPersona();
    },
    onSubmitCustomRoute: async () => {
      await handleSubmitCustomRoute();
    },
    onSavePersona: async () => {
      await handleSavePersona();
    },
    onLoadPersona: async () => {
      await handleLoadPersona();
    },
    onResetStandardCommute: async () => {
      await handleResetStandardCommute();
    }
  });

  // 3. Setup Offline Resilience
  offlineCache.initOfflineListeners((isOnline) => {
    uiController.setOfflineStatus(!isOnline);
  });

  // 4. Initial Personas Load from Flask Adapter (/api/custom/personas)
  await loadCustomPersonas();

  // 5. Initial Data Load (Check for active custom journey in localStorage first)
  const savedCustom = localStorage.getItem('stationbuddy_custom_journey');
  if (savedCustom) {
    try {
      const parsed = JSON.parse(savedCustom);
      if (parsed && parsed.status === 'success' && parsed.route) {
        applyCustomJourneyResult(parsed);
      } else {
        await loadCommuteStatus(currentArrivalTime, currentOrigin, currentDest);
      }
    } catch (e) {
      await loadCommuteStatus(currentArrivalTime, currentOrigin, currentDest);
    }
  } else {
    await loadCommuteStatus(currentArrivalTime, currentOrigin, currentDest);
  }
});

/**
 * Standard commute status polling.
 * Suppresses background overwrites when a custom journey is actively displayed.
 */
async function loadCommuteStatus(arrivalTime = currentArrivalTime, origin = currentOrigin, dest = currentDest) {
  if (isCustomJourneyActive) {
    console.log('Custom journey is currently active; suppressing background polling overwrite.');
    return;
  }

  try {
    let url = `/api/status?arrival_time=${encodeURIComponent(arrivalTime)}`;
    if (origin) url += `&origin=${encodeURIComponent(origin)}`;
    if (dest) url += `&destination=${encodeURIComponent(dest)}`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    currentData = data;

    offlineCache.save(data);
    uiController.setOfflineStatus(false);
    updateAppView(data);
  } catch (err) {
    console.warn('Network issue, attempting offline recovery:', err);
    const cached = offlineCache.load();
    if (cached) {
      currentData = cached;
      uiController.setOfflineStatus(true);
      updateAppView(cached);
    }
  }
}

const PERSONA_CYCLE = ['rachel', 'arjun', 'mdm_lim'];

function updateAppView(data) {
  const routes = data.routes || {};
  if (routes.primary_arjun) {
    activeRouteId = 'primary_arjun';
  } else if (routes.primary_mdm_lim) {
    activeRouteId = 'primary_mdm_lim';
  } else if (data.decision?.is_delayed) {
    activeRouteId = 'bypass_dtl';
  } else {
    activeRouteId = 'primary_ewl';
  }

  uiController.updateTopBar(data);
  uiController.updatePersonaDisplay(data);
  uiController.updateAlertBanner(data);
  uiController.updateRouteCards(data, activeRouteId);
  uiController.highlightActiveCard(activeRouteId);
  uiController.setAllRoutesButtonState(mapController.showAllRoutes);

  mapController.renderLayers(data, activeRouteId);

  // Update top bar persona label if profile exists
  if (data.profile) {
    const label = document.getElementById('active-persona-label');
    if (label) label.textContent = `${data.profile.name} (${data.profile.tag || 'Active'})`;
  }
}

function updateBannerForSelectedRoute(routeId, data) {
  const routes = data.routes || {};
  const selectedRoute = routes[routeId];
  if (!selectedRoute) return;

  const headline = document.getElementById('alert-headline');
  const detail = document.getElementById('alert-detail');
  const statusLabel = document.getElementById('alert-status-label');

  if (headline && selectedRoute.title) {
    headline.textContent = selectedRoute.title;
  }
  if (detail) {
    const eta = selectedRoute.estimated_arrival ? `ETA: ${selectedRoute.estimated_arrival} (${selectedRoute.total_duration_min} mins)` : `${selectedRoute.total_duration_min} mins`;
    detail.textContent = `${selectedRoute.status || 'Active Journey'} • ${eta}`;
  }
  if (statusLabel) {
    if (routeId === 'primary_ewl') {
      statusLabel.textContent = data.decision?.is_delayed ? 'Disrupted (Primary)' : 'Primary Active';
    } else if (routeId === 'bypass_dtl') {
      statusLabel.textContent = 'Alternative MRT Active';
    } else if (routeId === 'bypass_bus10e') {
      statusLabel.textContent = 'Public Bus Active';
    }
  }
}

async function switchPersona(personaId) {
  isCustomJourneyActive = false;
  customJourneyResult = null;
  currentArbitraryRoute = null;
  localStorage.removeItem('stationbuddy_custom_journey');
  uiController.setCustomJourneyActive(false);

  try {
    const resp = await fetch('/api/persona/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ persona_id: personaId })
    });
    const res = await resp.json();
    if (res.data) {
      currentData = res.data;
      if (currentData.profile) {
        currentOrigin = currentData.profile.origin;
        currentDest = currentData.profile.destination;
        const originInput = document.getElementById('origin-input');
        const destInput = document.getElementById('dest-input');
        if (originInput) originInput.value = currentOrigin;
        if (destInput) destInput.value = currentDest;
      }
      activeCustomPersonaId = personaId;
      offlineCache.save(currentData);
      updateAppView(currentData);

      // Keep dropdown in sync
      const dropdown = document.getElementById('persona-select-dropdown');
      if (dropdown) dropdown.value = personaId;
    }
  } catch (err) {
    console.error('Failed to switch persona:', err);
  }
}

async function cyclePersona() {
  const currentPersona = (currentData?.persona_id || 'rachel').toLowerCase();
  const currentIndex = PERSONA_CYCLE.indexOf(currentPersona);
  const nextIndex = (currentIndex + 1) % PERSONA_CYCLE.length;
  await switchPersona(PERSONA_CYCLE[nextIndex]);
}

async function loadAndRenderScenarios() {
  try {
    const resp = await fetch('/api/scenarios');
    const res = await resp.json();
    uiController.renderScenariosList(res.scenarios, res.current, async (scenarioId) => {
      await switchScenario(scenarioId);
    });
  } catch (err) {
    console.error('Failed to load scenarios:', err);
  }
}

async function switchScenario(scenarioId) {
  isCustomJourneyActive = false;
  customJourneyResult = null;
  currentArbitraryRoute = null;
  localStorage.removeItem('stationbuddy_custom_journey');
  uiController.setCustomJourneyActive(false);

  try {
    const resp = await fetch('/api/scenario/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        scenario_id: scenarioId,
        arrival_time: currentArrivalTime,
        origin: currentOrigin,
        destination: currentDest
      })
    });
    const res = await resp.json();
    if (res.data) {
      currentOrigin = res.data.profile?.origin || currentOrigin;
      currentDest = res.data.profile?.destination || currentDest;
      currentData = res.data;
      offlineCache.save(currentData);
      updateAppView(currentData);
    }
  } catch (err) {
    console.error('Scenario switch failed:', err);
  }
}

async function updateSettings(settings) {
  try {
    const resp = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...settings,
        arrival_time: currentArrivalTime
      })
    });
    const res = await resp.json();
    if (res.data) {
      currentData = res.data;
      offlineCache.save(currentData);
      updateAppView(currentData);
    }
  } catch (err) {
    console.error('Settings update failed:', err);
  }
}

async function handleLocationChange(origin, dest) {
  currentOrigin = origin;
  currentDest = dest;

  if (isCustomJourneyActive) {
    // If user changes location during custom journey, re-run custom journey calculation
    await handleSubmitCustomRoute();
    return;
  }

  currentArbitraryRoute = null;
  uiController.hideArbitraryRouteCard();

  // Load commute status with the custom origin & destination.
  // The backend enriches this with full custom routes (primary & alternative),
  // walking footpaths, and exact coordinates without spikes.
  await loadCommuteStatus(currentArrivalTime, origin, dest);

  // Sync baseline settings to backend silently
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest, arrival_time: currentArrivalTime })
    });
  } catch (_) { /* non-critical */ }
}

async function queryGraphRoute(origin, dest) {
  const origQuery = origin;
  const destQuery = dest;
  if (!origQuery || !destQuery) return;

  try {
    const isRain = currentData?.weather?.rain_alert?.is_raining ? '1' : '0';
    const url = `/api/route?origin=${encodeURIComponent(origQuery)}&destination=${encodeURIComponent(destQuery)}&rain=${isRain}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      console.warn(`No graph path found between ${origQuery} and ${destQuery}: HTTP ${resp.status}`);
      uiController.hideArbitraryRouteCard();
      return;
    }
    const routeData = await resp.json();
    if (routeData && routeData.legs) {
      currentArbitraryRoute = routeData;
      currentSearchedRoutes = [routeData, ...(routeData.alternatives || [])];
      activeRouteId = 'arbitrary_route';
      uiController.renderArbitraryRouteCard(routeData, currentSearchedRoutes);

      if (routeData.polyline && routeData.polyline.length > 0) {
        mapController.renderArbitraryRoute(routeData);
      } else {
        mapController.renderCustomRoute(routeData, {
          origin: routeData.origin_resolved?.station || origQuery,
          destination: routeData.dest_resolved?.station || destQuery,
          boarding_station: routeData.origin_resolved?.station,
          alighting_station: routeData.dest_resolved?.station
        });
      }

      // Sync proactive alert banner with queried journey (clearing Tampines default)
      const originDisplay = routeData.origin_resolved?.display || routeData.title || origQuery;
      const destDisplay = routeData.dest_resolved?.display || destQuery;
      const totalMin = routeData.total_duration_min || 0;
      const eta = routeData.estimated_arrival || '--:--';
      const headlineText = `${originDisplay} → ${destDisplay}`;
      const detailText = `${routeData.status || 'Direct MRT corridor'} • ETA: ${eta} (${totalMin} mins)`;

      const alertData = {
        decision: {
          headline: headlineText,
          one_line_advice: detailText,
          urgency: (routeData.delay_minutes && routeData.delay_minutes > 0) ? 'CRITICAL' : 'CALM',
          threshold_minutes: 15,
          is_delayed: Boolean(routeData.delay_minutes && routeData.delay_minutes > 0)
        },
        weather: currentData?.weather,
        pcd_forecast: { advice: null }
      };
      uiController.updateAlertBanner(alertData);
    }
  } catch (err) {
    console.error('Failed to query graph route:', err);
  }
}

// ============================================================================
// COMMUTER PERSONA & CUSTOM ROUTE ADAPTER HANDLERS (Issue 2 / Teammate 1 Handover)
// ============================================================================

/**
 * Loads registered commuter personas from /api/custom/personas.
 * Populates dropdown, restores saved preferences, and syncs form.
 */
async function loadCustomPersonas() {
  try {
    const resp = await fetch('/api/custom/personas');
    if (!resp.ok) return;
    const res = await resp.json();
    savedPersonas = res.personas || [];
    if (res.current) activeCustomPersonaId = res.current;

    // Check localStorage for user profile edits
    const storedProfileStr = localStorage.getItem('stationbuddy_custom_profile');
    let profileToFill = savedPersonas.find(p => p.id === activeCustomPersonaId) || savedPersonas[0];

    if (storedProfileStr) {
      try {
        const stored = JSON.parse(storedProfileStr);
        if (stored && stored.id) {
          profileToFill = stored;
          activeCustomPersonaId = stored.id;
          const existIdx = savedPersonas.findIndex(p => p.id === stored.id);
          if (existIdx >= 0) {
            savedPersonas[existIdx] = { ...savedPersonas[existIdx], ...stored };
          } else {
            savedPersonas.push(stored);
          }
        }
      } catch (e) {
        console.warn('Could not parse stored persona:', e);
      }
    }

    uiController.populatePersonaDropdown(savedPersonas, activeCustomPersonaId);
    if (profileToFill) {
      uiController.fillPersonaForm(profileToFill);
    }
  } catch (err) {
    console.warn('Failed to load custom personas:', err);
  }
}

/**
 * Handles dropdown change in the persona drawer.
 */
async function handleSelectPersonaDropdown(personaId) {
  activeCustomPersonaId = personaId;
  const profile = savedPersonas.find(p => p.id === personaId);
  if (profile) {
    uiController.fillPersonaForm(profile);
    if (profile.origin) {
      currentOrigin = profile.origin;
      const oInput = document.getElementById('origin-input');
      if (oInput) oInput.value = currentOrigin;
    }
    if (profile.destination) {
      currentDest = profile.destination;
      const dInput = document.getElementById('dest-input');
      if (dInput) dInput.value = currentDest;
    }
  }
}

/**
 * Creates a blank custom persona template for rapid user personalization.
 */
function handleNewPersona() {
  const newId = `custom_${Date.now()}`;
  activeCustomPersonaId = newId;
  const newProfile = {
    id: newId,
    name: 'My Custom Commuter',
    tag: 'Custom',
    walking_speed_mps: 1.35,
    cycling_speed_mps: 4.0,
    max_walking_distance_m: null,
    max_transfers: 2,
    requires_step_free: false,
    requires_lift_monitoring: false,
    stair_aversion: false,
    cycling_enabled: false,
    avoid_cycling_in_rain: true,
    crowd_tolerance: 'normal',
    crowd_advance_lead_min: 10,
    delay_threshold_min: 15
  };
  savedPersonas.push(newProfile);
  uiController.populatePersonaDropdown(savedPersonas, newId);
  uiController.fillPersonaForm(newProfile);
}

/**
 * Calls POST /api/custom/route with active persona, origin, destination,
 * timing, and behavioral overrides. Renders returned route and advice.
 */
async function handleSubmitCustomRoute() {
  try {
    const formOverrides = uiController.readPersonaForm();
    const originInput = document.getElementById('origin-input')?.value || currentOrigin;
    const destInput = document.getElementById('dest-input')?.value || currentDest;
    const arrivalTimeInput = document.getElementById('input-arrival-time')?.value || currentArrivalTime;

    const payload = {
      persona_id: activeCustomPersonaId,
      origin: originInput,
      destination: destInput,
      deadline_arrival: uiController.formatTime12h(arrivalTimeInput),
      ...formOverrides
    };

    uiController.dismissCustomRouteError();

    const resp = await fetch('/api/custom/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await resp.json();

    if (!resp.ok || result.status === 'error') {
      uiController.renderCustomRouteError(result);
      return;
    }

    applyCustomJourneyResult(result);
    uiController.closePersonaDrawer();
  } catch (err) {
    console.error('Custom route request failed:', err);
    uiController.renderCustomRouteError({
      code: 'NETWORK_ERROR',
      message: err.message || 'Could not connect to custom route service'
    });
  }
}

/**
 * Applies returned custom user route:
 * - Updates top bar, persona badge, and proactive alert banner
 * - Updates route cards, replacing fixed Rachel/EWL labels with response values
 * - Coordinates map visualization with fallback geometry
 * - Sets isCustomJourneyActive = true to prevent background polling overwrites
 */
function applyCustomJourneyResult(result) {
  isCustomJourneyActive = true;
  customJourneyResult = result;
  currentData = result;

  localStorage.setItem('stationbuddy_custom_journey', JSON.stringify(result));

  const profileName = result.profile?.name || 'Custom Commuter';
  const headline = result.decision?.headline || 'Custom Route Planned';
  uiController.setCustomJourneyActive(true, profileName, headline);

  activeRouteId = 'primary_ewl'; // Renders onto primary transit card

  uiController.updateTopBar({
    source_badge: 'Custom Profile Route (Verified)'
  });

  uiController.updatePersonaDisplay(result);
  uiController.updateAlertBanner(result);
  uiController.updateRouteCards(result, 'primary_ewl');
  uiController.highlightActiveCard('primary_ewl');

  // Coordinated map integration: station pins & dashed corridor line without requiring polyline geometry
  mapController.renderCustomRoute(result.route, result.profile);
}

/**
 * Saves persona preferences to backend JSON storage (/api/custom/personas/save)
 * and localStorage so preferences survive a restart.
 */
async function handleSavePersona() {
  try {
    const formOverrides = uiController.readPersonaForm();
    const originVal = document.getElementById('origin-input')?.value || currentOrigin;
    const destVal = document.getElementById('dest-input')?.value || currentDest;

    const updatedProfile = {
      id: activeCustomPersonaId,
      ...formOverrides,
      origin: originVal,
      destination: destVal
    };

    // 1. Update or register persona on backend
    try {
      const putResp = await fetch(`/api/custom/personas/${encodeURIComponent(activeCustomPersonaId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProfile)
      });
      if (!putResp.ok && putResp.status === 404) {
        await fetch('/api/custom/personas', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedProfile)
        });
      }
    } catch (e) {
      console.warn('Backend persona register warning:', e);
    }

    // 2. Persist to file on backend so preferences survive a restart
    try {
      await fetch('/api/custom/personas/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath: 'data/custom_personas.json' })
      });
    } catch (e) {
      console.warn('Backend persona file save warning:', e);
    }

    // 3. Persist to browser localStorage
    localStorage.setItem('stationbuddy_custom_profile', JSON.stringify(updatedProfile));

    const idx = savedPersonas.findIndex(p => p.id === activeCustomPersonaId);
    if (idx >= 0) {
      savedPersonas[idx] = { ...savedPersonas[idx], ...updatedProfile };
    } else {
      savedPersonas.push(updatedProfile);
    }

    uiController.populatePersonaDropdown(savedPersonas, activeCustomPersonaId);
    uiController.showPersonaSaveStatus('Preferences saved successfully!');
  } catch (err) {
    console.error('Save persona failed:', err);
    uiController.showPersonaSaveStatus('Failed to save: ' + err.message, true);
  }
}

/**
 * Loads persona preferences from backend JSON file (/api/custom/personas/load).
 */
async function handleLoadPersona() {
  try {
    const resp = await fetch('/api/custom/personas/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath: 'data/custom_personas.json' })
    });
    const res = await resp.json();
    if (resp.ok && res.status === 'success') {
      await loadCustomPersonas();
      uiController.showPersonaSaveStatus(`Loaded ${res.loaded_count || 'all'} saved profiles.`);
    } else {
      uiController.showPersonaSaveStatus(res.message || 'No saved profile file found on disk.', true);
    }
  } catch (err) {
    console.error('Load personas failed:', err);
    uiController.showPersonaSaveStatus('Failed to load: ' + err.message, true);
  }
}

/**
 * Clears active custom journey mode and switches back to live standard commute.
 */
async function handleResetStandardCommute() {
  isCustomJourneyActive = false;
  customJourneyResult = null;
  localStorage.removeItem('stationbuddy_custom_journey');
  uiController.setCustomJourneyActive(false);
  uiController.closePersonaDrawer();
  await loadCommuteStatus(currentArrivalTime, currentOrigin, currentDest);
  uiController.showPersonaSaveStatus('Switched back to standard live commute.');
}
