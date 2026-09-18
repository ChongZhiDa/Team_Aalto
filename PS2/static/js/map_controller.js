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

    // --- Custom Door-to-Door Route Rendering ---
    if (layers.is_custom) {
      const allBounds = [];

      // 1. Origin (Start Doorstep / House)
      if (layers.origin && layers.origin.coords) {
        const homeIcon = L.divIcon({
          className: '',
          html: '<div class="w-8 h-8 rounded-full bg-emerald-600 border-2 border-white flex items-center justify-center text-white text-xs shadow-xl"><i class="fa-solid fa-house"></i></div>',
          iconSize: [32, 32],
          iconAnchor: [16, 16]
        });
        L.marker(layers.origin.coords, { icon: homeIcon })
          .addTo(this.layersGroup)
          .bindPopup(`<b>Start Location</b><br>${layers.origin.name}`);
        allBounds.push(layers.origin.coords);
      }

      // 2. Destination (Arrival Doorstep)
      if (layers.destination && layers.destination.coords) {
        const destIcon = L.divIcon({
          className: '',
          html: '<div class="w-8 h-8 rounded-full bg-rose-600 border-2 border-white flex items-center justify-center text-white text-xs shadow-xl"><i class="fa-solid fa-flag-checkered"></i></div>',
          iconSize: [32, 32],
          iconAnchor: [16, 16]
        });
        L.marker(layers.destination.coords, { icon: destIcon })
          .addTo(this.layersGroup)
          .bindPopup(`<b>Destination</b><br>${layers.destination.name}`);
        allBounds.push(layers.destination.coords);
      }

      // 3. Walking legs (turn-by-turn footpaths connecting house to station avoiding buildings)
      if (layers.walking_legs) {
        Object.values(layers.walking_legs).forEach(walk => {
          if (walk.coords && walk.coords.length >= 2) {
            const distLabel = walk.distance_m ? ` (${Math.round(walk.distance_m)}m)` : '';
            L.polyline(walk.coords, {
              color: '#38bdf8',
              weight: 4.5,
              dashArray: '5, 7',
              opacity: 0.95,
              lineCap: 'round',
              lineJoin: 'round'
            }).addTo(this.layersGroup).bindPopup(`<b>Walking Route</b><br>${walk.name || 'Doorstep connection'}${distLabel}`);
            walk.coords.forEach(c => allBounds.push(c));
          }
        });
      }

      // 4. Custom transit track polylines (colored per MRT line)
      if (layers.custom_tracks && layers.custom_tracks.length > 0) {
        layers.custom_tracks.forEach(track => {
          if (track.coords && track.coords.length >= 2) {
            L.polyline(track.coords, {
              color: track.color || '#2563eb',
              weight: 6,
              opacity: 0.95,
              lineCap: 'round',
              lineJoin: 'round'
            }).addTo(this.layersGroup).bindPopup(`<b>${track.line || 'MRT'} Line</b><br>${layers.route_summary || 'Transit Segment'}`);
            track.coords.forEach(c => allBounds.push(c));
          }
        });
      } else if (layers.custom_track && layers.custom_track.length >= 2) {
        const trackColor = layers.track_color || '#2563eb';
        L.polyline(layers.custom_track, {
          color: trackColor,
          weight: 6,
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(this.layersGroup).bindPopup(`<b>Transit Route</b><br>${layers.route_summary || 'MRT Route'}`);
        layers.custom_track.forEach(c => allBounds.push(c));
      }

      // 5. Stations along the route
      if (layers.custom_stations) {
        layers.custom_stations.forEach(stn => {
          const pinClass = stn.line === 'NEL' ? 'bg-purple-600' :
                           (stn.line === 'DTL' ? 'bg-blue-600' :
                           (stn.line === 'EWL' ? 'bg-emerald-600' :
                           (stn.line === 'CCL' ? 'bg-amber-500' :
                           (stn.line === 'NSL' ? 'bg-red-600' :
                           (stn.line === 'TEL' ? 'bg-yellow-800' : 'bg-slate-700')))));
          const icon = L.divIcon({
            className: '',
            html: `<div class="w-3.5 h-3.5 rounded-full ${pinClass} border-2 border-white shadow-md"></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7]
          });
          L.marker(stn.coords, { icon }).addTo(this.layersGroup).bindPopup(`
            <div class="p-1 text-xs">
              <strong>${stn.name}</strong><br>
              <span class="text-slate-600 font-medium">${stn.line || 'MRT'} Line</span>
            </div>
          `);
          allBounds.push(stn.coords);
        });
      }

      // 6. Smoothly pan and zoom map to show whole door-to-door path
      if (allBounds.length > 0) {
        this.map.fitBounds(allBounds, { padding: [70, 70], maxZoom: 15 });
      }
      return;
    }

    // --- Baseline Corridor Rendering ---
    // 1. Walking legs (dashed grey)
    Object.values(layers.walking_legs).forEach(walk => {
      L.polyline(walk.coords, {
        color: '#94a3b8',
        weight: 3,
        dashArray: '4, 6',
        opacity: 0.9
      }).addTo(this.layersGroup);
    });

    // 2. DTL Bypass track
    const isDtlActive = activeRouteId === 'bypass_dtl';
    const dtlPoly = L.polyline(layers.dtl_track, {
      color: '#005EC4',
      weight: isDtlActive ? 6 : 3.5,
      opacity: isDtlActive ? 1.0 : 0.6,
    }).addTo(this.layersGroup);
    dtlPoly.bindPopup('<b>Downtown Line (DTL)</b><br>Reliable alternative bypass');

    // 3. EWL Primary Track
    if (!isEwlDisrupted) {
      const ewlPoly = L.polyline(layers.ewl_track, {
        color: '#009645',
        weight: activeRouteId === 'primary_ewl' ? 6 : 4,
        opacity: 1.0,
      }).addTo(this.layersGroup);
      ewlPoly.bindPopup('<b>East-West Line (EWL)</b><br>Operating normally');
    } else {
      const ewlStations = layers.ewl_stations;
      const preCoords = ewlStations.slice(0, 4).map(s => s.coords);
      const disruptedCoords = ewlStations.slice(3, 11).map(s => s.coords);
      const postCoords = ewlStations.slice(10).map(s => s.coords);

      L.polyline(preCoords, { color: '#009645', weight: 4, opacity: 0.8 }).addTo(this.layersGroup);
      L.polyline(postCoords, { color: '#009645', weight: 4, opacity: 0.8 }).addTo(this.layersGroup);

      const disruptedPoly = L.polyline(disruptedCoords, {
        color: '#EF4444',
        weight: 6,
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

    // 4. Express Bus 10e Track
    if (layers.bus10e_track) {
      const isBusActive = activeRouteId === 'bypass_bus10e';
      L.polyline(layers.bus10e_track, {
        color: '#8b5cf6',
        weight: isBusActive ? 5 : 2.5,
        dashArray: '3, 5',
        opacity: isBusActive ? 0.9 : 0.4
      }).addTo(this.layersGroup).bindPopup('<b>Express Bus 10e</b><br>Direct ECP corridor');
    }

    // 5. Stations Markers
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
      const marker = L.marker(stn.coords, { icon }).addTo(this.layersGroup);
      marker.bindPopup(`
        <div class="p-1 text-xs">
          <strong>${stn.code} — ${stn.name}</strong><br>
          <span class="text-blue-700">Downtown Line Bypass</span>
        </div>
      `);
    });

    // 6. Home & Destination Markers
    const homeIcon = L.divIcon({
      className: '',
      html: '<div class="w-6 h-6 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-house"></i></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    L.marker(layers.origin.coords, { icon: homeIcon }).addTo(this.layersGroup).bindPopup('<b>Rachel\'s Home</b><br>Blk 230 Tampines St 21<br>Leaves 07:40 AM');

    const officeIcon = L.divIcon({
      className: '',
      html: '<div class="w-6 h-6 rounded-full bg-amber-500 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-briefcase"></i></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    L.marker(layers.destination.coords, { icon: officeIcon }).addTo(this.layersGroup).bindPopup('<b>Rachel\'s Desk</b><br>One Raffles Place<br>Target: 08:45 AM');
  }

  panToCenter() {
    if (this.map) this.map.flyTo([1.3190, 103.8980], 12);
  }
}

