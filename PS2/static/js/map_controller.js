/**
 * OpenStreetMap & Leaflet Controller.
 * Handles map rendering, tile attribution, track polylines, and station pins.
 * Owned by: Teammate A (Frontend & Mobile UX)
 */

export class MapController {
  constructor(containerId = 'map') {
    this.containerId = containerId;
    this.map = null;
    this.layersGroup = null;
    this.showAllRoutes = false;
  }

  toggleAllRoutes(data, activeRouteId) {
    this.showAllRoutes = !this.showAllRoutes;
    if (data) {
      this.renderLayers(data, activeRouteId);
    }
    return this.showAllRoutes;
  }

  init() {
    this.map = L.map(this.containerId, {
      zoomControl: false,
      attributionControl: true
    }).setView([1.3190, 103.8980], 12);

    L.control.zoom({ position: 'topright' }).addTo(this.map);

    // Mandatory OpenStreetMap base layer with attribution
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
    }).addTo(this.map);

    this.layersGroup = L.featureGroup().addTo(this.map);
  }

  renderLayers(data, activeRouteId = 'primary_ewl') {
    if (!this.map || !this.layersGroup) return;
    this.layersGroup.clearLayers();

    const layers = data.map_layers;
    const isEwlDisrupted = data.decision.is_delayed;
    const showAll = this.showAllRoutes;

    const isEwlActive = activeRouteId === 'primary_ewl';
    const isDtlActive = activeRouteId === 'bypass_dtl';
    const isBusActive = activeRouteId === 'bypass_bus10e';

    // 1. Walking legs (filtered to active route unless showAll is true)
    Object.entries(layers.walking_legs || {}).forEach(([key, walk]) => {
      let shouldDraw = showAll;
      if (!shouldDraw) {
        if (isEwlActive) {
          shouldDraw = key.includes('ewl') || key === 'home_to_tampines_ewl' || key === 'raffles_place_ewl_to_desk';
        } else if (isDtlActive) {
          shouldDraw = key.includes('dtl') || key === 'home_to_tampines_dtl' || key === 'telok_ayer_dtl_to_desk';
        } else if (isBusActive) {
          shouldDraw = key.includes('bus') || key === 'home_to_bus10e' || key === 'fullerton_bus10e_to_desk';
        }
      }

      if (shouldDraw) {
        L.polyline(walk.coords, {
          color: '#38bdf8',
          weight: 4.5,
          dashArray: '6, 6',
          opacity: 0.95
        }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1.5 text-xs">
            <strong class="text-blue-600 flex items-center gap-1">
              <i class="fa-solid fa-person-walking text-blue-500"></i> ${walk.name}
            </strong>
            <div class="text-[11px] text-slate-600 my-0.5">
              <strong>${walk.distance_m}m</strong> • ~<strong>${walk.duration_min} mins</strong>
            </div>
            <span class="inline-block px-1.5 py-0.2 rounded text-[10px] font-bold ${walk.sheltered_percent >= 80 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
              🛡️ ${walk.sheltered_percent}% Covered Walkway (LTA GIS)
            </span>
          </div>
        `);
      }
    });

    // 2. DTL Bypass track
    if (showAll || isDtlActive) {
      const dtlPoly = L.polyline(layers.dtl_track, {
        color: '#005EC4',
        weight: isDtlActive ? 6 : 3,
        opacity: isDtlActive ? 1.0 : 0.4,
      }).addTo(this.layersGroup);
      dtlPoly.bindPopup('<b>Downtown Line (DTL)</b><br>Reliable alternative bypass');
    }

    // 3. EWL Primary Track
    if (showAll || isEwlActive) {
      if (!isEwlDisrupted) {
        const ewlPoly = L.polyline(layers.ewl_track, {
          color: '#009645',
          weight: isEwlActive ? 6 : 3,
          opacity: isEwlActive ? 1.0 : 0.4,
        }).addTo(this.layersGroup);
        ewlPoly.bindPopup('<b>East-West Line (EWL)</b><br>Operating normally');
      } else {
        const ewlStations = layers.ewl_stations;
        const preCoords = ewlStations.slice(0, 4).map(s => s.coords);
        const disruptedCoords = ewlStations.slice(3, 11).map(s => s.coords);
        const postCoords = ewlStations.slice(10).map(s => s.coords);

        L.polyline(preCoords, { color: '#009645', weight: isEwlActive ? 5 : 3, opacity: isEwlActive ? 0.9 : 0.4 }).addTo(this.layersGroup);
        L.polyline(postCoords, { color: '#009645', weight: isEwlActive ? 5 : 3, opacity: isEwlActive ? 0.9 : 0.4 }).addTo(this.layersGroup);

        const disruptedPoly = L.polyline(disruptedCoords, {
          color: '#EF4444',
          weight: isEwlActive ? 6 : 4,
          dashArray: '6, 8',
          opacity: 1.0,
          lineCap: 'round'
        }).addTo(this.layersGroup);

        disruptedPoly.bindPopup(
          '<div class="text-xs"><b>⚠️ EWL Disrupted Corridor</b><br>' +
          '<span class="text-rose-600 font-semibold">Track fault: Bedok - Bugis</span><br>' +
          'Free bridging buses activated at affected stations.</div>'
        );
      }
    }

    // 4. Express Bus 10e Track
    if (layers.bus10e_track && (showAll || isBusActive)) {
      L.polyline(layers.bus10e_track, {
        color: '#8b5cf6',
        weight: isBusActive ? 5 : 2.5,
        dashArray: '3, 5',
        opacity: isBusActive ? 0.9 : 0.4
      }).addTo(this.layersGroup).bindPopup('<b>Express Bus 10e</b><br>Direct ECP corridor');
    }

    // 5. Stations Markers (filtered to active line unless showAll is true)
    if (showAll || isEwlActive) {
      layers.ewl_stations.forEach(stn => {
        const isDisruptedStn = isEwlDisrupted && ['EW5','EW6','EW7','EW8','EW9','EW10','EW11','EW12'].includes(stn.code);
        const pinClass = isDisruptedStn ? 'station-pin pin-disrupted' : 'station-pin pin-ewl';

        const icon = L.divIcon({
          className: '',
          html: `<div class="${pinClass}"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        });

        const marker = L.marker(stn.coords, { icon }).addTo(this.layersGroup);
        
        let exitDetails = '';
        if (stn.code === 'EW14') {
          exitDetails = '<div class="mt-1 pt-1 border-t border-slate-200 text-[11px]"><strong class="text-blue-600"><i class="fa-solid fa-door-open"></i> Take Exit B</strong><br><span class="text-emerald-700 font-medium">🛡️ 100% Covered Linkway to One Raffles Place</span></div>';
        } else if (stn.code === 'EW2') {
          exitDetails = '<div class="mt-1 pt-1 border-t border-slate-200 text-[11px]"><span class="text-slate-600">Concourse Entrance Exit A</span><br><span class="text-emerald-700 font-medium">🛡️ 80% Covered Linkway from Home</span></div>';
        }

        marker.bindPopup(`
          <div class="p-1 text-xs">
            <strong>${stn.code} — ${stn.name}</strong><br>
            <span class="${isDisruptedStn ? 'text-rose-600 font-bold' : 'text-emerald-700'}">
              ${isDisruptedStn ? '⚠️ Track Fault Delay' : 'Service Normal'}
            </span>
            ${exitDetails}
          </div>
        `);
      });
    }

    if (showAll || isDtlActive) {
      layers.dtl_stations.forEach(stn => {
        const icon = L.divIcon({
          className: '',
          html: `<div class="station-pin pin-dtl"></div>`,
          iconSize: [12, 12],
          iconAnchor: [6, 6]
        });
        const marker = L.marker(stn.coords, { icon }).addTo(this.layersGroup);

        let dtlExitDetails = '';
        if (stn.code === 'DT18') {
          dtlExitDetails = '<div class="mt-1 pt-1 border-t border-slate-200 text-[11px]"><strong class="text-blue-600"><i class="fa-solid fa-door-open"></i> Take Exit B</strong><br><span class="text-emerald-700 font-medium">🛡️ 95% Covered Linkway via Cross St</span></div>';
        } else if (stn.code === 'DT32') {
          dtlExitDetails = '<div class="mt-1 pt-1 border-t border-slate-200 text-[11px]"><strong class="text-blue-600"><i class="fa-solid fa-door-open"></i> Entrance Exit B</strong><br><span class="text-emerald-700 font-medium">🛡️ 90% Covered Linkway from Home</span></div>';
        }

        marker.bindPopup(`
          <div class="p-1 text-xs">
            <strong>${stn.code} — ${stn.name}</strong><br>
            <span class="text-blue-700">Downtown Line Bypass</span>
            ${dtlExitDetails}
          </div>
        `);
      });
    }

    // 6. Home & Destination Markers (Always visible)
    const homeIcon = L.divIcon({
      className: '',
      html: '<div class="w-6 h-6 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-house"></i></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    L.marker(layers.origin.coords, { icon: homeIcon }).addTo(this.layersGroup).bindPopup(`
      <div class="p-1 text-xs">
        <b>Rachel's Home</b><br>
        Blk 230 Tampines St 21<br>
        <span class="text-slate-500">Leaves 07:40 AM</span><br>
        <span class="text-emerald-700 font-medium">🛡️ 80%-90% Sheltered to MRT</span>
      </div>
    `);

    const officeIcon = L.divIcon({
      className: '',
      html: '<div class="w-6 h-6 rounded-full bg-amber-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-briefcase"></i></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    L.marker(layers.destination.coords, { icon: officeIcon }).addTo(this.layersGroup).bindPopup(`
      <div class="p-1 text-xs">
        <b>Rachel's Desk — One Raffles Place</b><br>
        <span class="text-slate-500">Target: 08:45 AM (09:00 Meeting)</span><br>
        <strong class="text-blue-600"><i class="fa-solid fa-door-open"></i> Arrive via Exit B</strong><br>
        <span class="text-emerald-700 font-medium">🛡️ 100% Underground / Covered Access</span>
      </div>
    `);
  }

  renderArbitraryRoute(routeData) {
    if (!this.map || !this.layersGroup) return;
    this.layersGroup.clearLayers();

    const polylineCoords = routeData.polyline || routeData.route_polyline || [];
    const stations = routeData.stations || routeData.route_stations || [];

    const lineColors = {
      'EWL': '#009645',
      'NSL': '#D42E12',
      'NEL': '#9900AA',
      'CCL': '#FA9E0D',
      'DTL': '#005EC4',
      'TEL': '#9D5B25'
    };

    const primaryLine = routeData.line || (routeData.lines_used && routeData.lines_used[0]) || 'EWL';
    const trackColor = lineColors[primaryLine] || '#6366f1';

    // 1. Draw route polyline
    if (polylineCoords.length > 0) {
      const poly = L.polyline(polylineCoords, {
        color: trackColor,
        weight: 6,
        opacity: 0.95,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(this.layersGroup);

      poly.bindPopup(`<b>${routeData.title}</b><br>${routeData.status || ''} • ${routeData.total_duration_min} mins`);

      this.map.fitBounds(poly.getBounds(), { padding: [60, 60] });
    }

    // 2. Draw stations along route
    stations.forEach((stn, idx) => {
      const isOrigin = idx === 0;
      const isDest = idx === stations.length - 1;

      if (isOrigin) {
        const homeIcon = L.divIcon({
          className: '',
          html: `<div class="w-6 h-6 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-location-dot"></i></div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker(stn.coords, { icon: homeIcon }).addTo(this.layersGroup).bindPopup(`<b>Start: ${stn.name}</b><br>Origin Station`);
      } else if (isDest) {
        const destIcon = L.divIcon({
          className: '',
          html: `<div class="w-6 h-6 rounded-full bg-rose-600 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-flag-checkered"></i></div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker(stn.coords, { icon: destIcon }).addTo(this.layersGroup).bindPopup(`<b>Destination: ${stn.name}</b><br>Arrive via Exit B`);
      } else {
        const pinIcon = L.divIcon({
          className: '',
          html: `<div class="station-pin" style="background-color: ${lineColors[stn.line] || trackColor}"></div>`,
          iconSize: [12, 12],
          iconAnchor: [6, 6]
        });
        L.marker(stn.coords, { icon: pinIcon }).addTo(this.layersGroup).bindPopup(`<b>${stn.name}</b><br>${stn.line || ''}`);
      }
    });

    // 3. Draw final pedestrian walking path to office desk if terminating in CBD
    const lastStn = stations[stations.length - 1];
    if (lastStn) {
      const lastStnName = (lastStn.name || '').toUpperCase();
      const officeCoords = [1.2840, 103.8515];

      if (lastStnName.includes('RAFFLES')) {
        const walkCoords = [lastStn.coords, officeCoords];
        L.polyline(walkCoords, {
          color: '#38bdf8',
          weight: 4.5,
          dashArray: '6, 6',
          opacity: 0.95
        }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1.5 text-xs">
            <strong class="text-blue-600 flex items-center gap-1">
              <i class="fa-solid fa-person-walking text-blue-500"></i> Raffles Place Exit B to Desk
            </strong>
            <div class="text-[11px] text-slate-700 my-0.5">
              <strong>120m</strong> • ~<strong>2 mins</strong>
            </div>
            <span class="inline-block px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
              🛡️ 100% Underground & Covered Linkway
            </span>
            <div class="mt-1 pt-1 border-t border-slate-200 text-[10px] text-slate-600 leading-snug">
              Direct B1 retail underpass into One Raffles Place Tower 1 elevators.
            </div>
          </div>
        `);

        const officeIcon = L.divIcon({
          className: '',
          html: '<div class="w-6 h-6 rounded-full bg-amber-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-briefcase"></i></div>',
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker(officeCoords, { icon: officeIcon }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1 text-xs">
            <b>Office Desk — One Raffles Place</b><br>
            <span class="text-emerald-700 font-semibold">🛡️ 100% Covered from Exit B</span>
          </div>
        `);
      } else if (lastStnName.includes('TELOK AYER')) {
        const walkCoords = [lastStn.coords, [1.2833, 103.8500], officeCoords];
        L.polyline(walkCoords, {
          color: '#38bdf8',
          weight: 4.5,
          dashArray: '6, 6',
          opacity: 0.95
        }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1.5 text-xs">
            <strong class="text-blue-600 flex items-center gap-1">
              <i class="fa-solid fa-person-walking text-blue-500"></i> Telok Ayer Exit B via Cross St
            </strong>
            <div class="text-[11px] text-slate-700 my-0.5">
              <strong>410m</strong> • ~<strong>5 mins</strong>
            </div>
            <span class="inline-block px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
              🛡️ 95% Covered Linkway
            </span>
            <div class="mt-1 pt-1 border-t border-slate-200 text-[10px] text-slate-600 leading-snug">
              Cross Street covered arcade past Far East Square, turn left on Church St.
            </div>
          </div>
        `);

        const officeIcon = L.divIcon({
          className: '',
          html: '<div class="w-6 h-6 rounded-full bg-amber-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-briefcase"></i></div>',
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker(officeCoords, { icon: officeIcon }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1 text-xs">
            <b>Office Desk — One Raffles Place</b><br>
            <span class="text-emerald-700 font-semibold">🛡️ 95% Sheltered via Cross St</span>
          </div>
        `);
      }
    }
  }

  panToCenter() {
    if (this.map) this.map.flyTo([1.3190, 103.8980], 12);
  }
}

