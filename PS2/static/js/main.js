/**
 * StationBuddy — Main Application Coordinator.
 * Orchestrates MapController, UIController, offline caching,
 * and dynamic arrival timing changes.
 */

import { MapController } from './map_controller.js';
import { UIController } from './ui_controller.js';
import { offlineCache } from './offline_cache.js';

let currentData = null;
let currentArbitraryRoute = null;
let activeRouteId = 'primary_ewl';
let currentArrivalTime = '08:45 AM';
let mapController;
let uiController;

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Map
  mapController = new MapController('map');
  mapController.init();

  // 2. Initialize UI Controller with callbacks
  uiController = new UIController({
    onSelectRoute: (routeId) => {
      activeRouteId = routeId;
      uiController.highlightActiveCard(activeRouteId);
      if (routeId === 'arbitrary_route' && currentArbitraryRoute) {
        mapController.renderArbitraryRoute(currentArbitraryRoute);
      } else if (currentData) {
        mapController.renderLayers(currentData, activeRouteId);
      }
    },
    onToggleAllRoutes: () => {
      if (currentData) {
        const isShowingAll = mapController.toggleAllRoutes(currentData, activeRouteId);
        uiController.setAllRoutesButtonState(isShowingAll);
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
      await loadCommuteStatus(currentArrivalTime);
    },
    onLocationChange: async (origin, dest) => {
      await handleLocationChange(origin, dest);
    },
    onRecenter: () => {
      mapController.panToCenter();
    }
  });

  // 3. Setup Offline Resilience
  offlineCache.initOfflineListeners((isOnline) => {
    uiController.setOfflineStatus(!isOnline);
  });

  // 4. Initial Data Load
  loadCommuteStatus(currentArrivalTime);
});

async function loadCommuteStatus(arrivalTime = '08:45 AM') {
  try {
    const url = `/api/status?arrival_time=${encodeURIComponent(arrivalTime)}`;
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

function updateAppView(data) {
  if (data.decision.is_delayed) {
    activeRouteId = 'bypass_dtl';
  } else {
    activeRouteId = 'primary_ewl';
  }

  uiController.updateTopBar(data);
  uiController.updateAlertBanner(data);
  uiController.updateRouteCards(data, activeRouteId);
  uiController.setAllRoutesButtonState(mapController.showAllRoutes);
  mapController.renderLayers(data, activeRouteId);
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
  try {
    const resp = await fetch('/api/scenario/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        scenario_id: scenarioId,
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
  // 1. Update baseline settings & commuter engine profile
  await updateSettings({ origin, destination: dest });

  // 2. Query T2's live Singapore MRT graph router endpoint (/api/route)
  await queryGraphRoute(origin, dest);
}

async function queryGraphRoute(origin, dest) {
  const origStation = uiController.extractStationName(origin);
  const destStation = uiController.extractStationName(dest);
  if (!origStation || !destStation) return;

  try {
    const isRain = currentData?.weather?.rain_alert?.is_raining ? '1' : '0';
    const url = `/api/route?origin=${encodeURIComponent(origStation)}&destination=${encodeURIComponent(destStation)}&rain=${isRain}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      console.warn(`No graph path found between ${origStation} and ${destStation}: HTTP ${resp.status}`);
      uiController.hideArbitraryRouteCard();
      return;
    }
    const routeData = await resp.json();
    if (routeData && routeData.legs) {
      currentArbitraryRoute = routeData;
      activeRouteId = 'arbitrary_route';
      uiController.renderArbitraryRouteCard(routeData);
      if (routeData.polyline && routeData.polyline.length > 0) {
        mapController.renderArbitraryRoute(routeData);
      }
    }
  } catch (err) {
    console.error('Failed to query graph route:', err);
  }
}
