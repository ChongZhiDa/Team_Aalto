/**
 * OpenStreetMap & Leaflet Controller.
 * Handles map rendering, tile attribution, track polylines, and station pins.
 * Owned by: Teammate A (Frontend & Mobile UX)
 */

/**
 * Canonical Singapore MRT station coordinate registry for map positioning
 * and coordinate fallback when routing teammate returns paths without polyline geometry.
 */
export const MRT_STATION_COORDS = {
  "Pasir Ris": [1.3730, 103.9493],
  "Tampines": [1.3533, 103.9452],
  "Simei": [1.3432, 103.9533],
  "Tanah Merah": [1.3273, 103.9463],
  "Bedok": [1.3240, 103.9300],
  "Kembangan": [1.3210, 103.9129],
  "Eunos": [1.3197, 103.9030],
  "Paya Lebar": [1.3178, 103.8924],
  "Aljunied": [1.3164, 103.8829],
  "Kallang": [1.3115, 103.8714],
  "Lavender": [1.3073, 103.8628],
  "Bugis": [1.3005, 103.8559],
  "City Hall": [1.2930, 103.8521],
  "Raffles Place": [1.2840, 103.8515],
  "Tanjong Pagar": [1.2764, 103.8457],
  "Outram Park": [1.2803, 103.8395],
  "Tiong Bahru": [1.2861, 103.8270],
  "Redhill": [1.2896, 103.8168],
  "Queenstown": [1.2949, 103.8061],
  "Commonwealth": [1.3025, 103.7983],
  "Buona Vista": [1.3073, 103.7900],
  "Dover": [1.3114, 103.7786],
  "Clementi": [1.3152, 103.7652],
  "Jurong East": [1.3331, 103.7423],
  "Chinese Garden": [1.3424, 103.7326],
  "Lakeside": [1.3442, 103.7209],
  "Boon Lay": [1.3386, 103.7060],
  "Pioneer": [1.3376, 103.6974],
  "Joo Koon": [1.3277, 103.6784],
  "Bukit Batok": [1.3490, 103.7496],
  "Bukit Gombak": [1.3587, 103.7519],
  "Choa Chu Kang": [1.3854, 103.7443],
  "Yew Tee": [1.3975, 103.7474],
  "Kranji": [1.4251, 103.7621],
  "Marsiling": [1.4325, 103.7741],
  "Woodlands": [1.4368, 103.7865],
  "Admiralty": [1.4406, 103.8009],
  "Sembawang": [1.4491, 103.8201],
  "Canberra": [1.4431, 103.8297],
  "Yishun": [1.4294, 103.8350],
  "Khatib": [1.4174, 103.8329],
  "Yio Chu Kang": [1.3817, 103.8449],
  "Ang Mo Kio": [1.3699, 103.8496],
  "Bishan": [1.3508, 103.8481],
  "Braddell": [1.3405, 103.8468],
  "Toa Payoh": [1.3326, 103.8475],
  "Novena": [1.3204, 103.8438],
  "Newton": [1.3123, 103.8380],
  "Orchard": [1.3040, 103.8318],
  "Somerset": [1.3002, 103.8390],
  "Dhoby Ghaut": [1.2989, 103.8463],
  "Marina Bay": [1.2764, 103.8546],
  "Marina South Pier": [1.2694, 103.8631],
  "HarbourFront": [1.2654, 103.8224],
  "Chinatown": [1.2848, 103.8440],
  "Clarke Quay": [1.2884, 103.8466],
  "Little India": [1.3068, 103.8492],
  "Farrer Park": [1.3123, 103.8540],
  "Boon Keng": [1.3194, 103.8617],
  "Potong Pasir": [1.3314, 103.8691],
  "Woodleigh": [1.3392, 103.8708],
  "Serangoon": [1.3498, 103.8736],
  "Kovan": [1.3601, 103.8851],
  "Hougang": [1.3713, 103.8924],
  "Buangkok": [1.3829, 103.8931],
  "Sengkang": [1.3917, 103.8955],
  "Punggol": [1.4052, 103.9023],
  "Bras Basah": [1.2969, 103.8507],
  "Esplanade": [1.2935, 103.8554],
  "Promenade": [1.2932, 103.8608],
  "Nicoll Highway": [1.3001, 103.8636],
  "Stadium": [1.3028, 103.8753],
  "Mountbatten": [1.3063, 103.8825],
  "Dakota": [1.3085, 103.8885],
  "MacPherson": [1.3259, 103.8899],
  "Tai Seng": [1.3353, 103.8879],
  "Bartley": [1.3425, 103.8802],
  "Lorong Chuan": [1.3516, 103.8636],
  "Marymount": [1.3487, 103.8394],
  "Caldecott": [1.3378, 103.8396],
  "Botanic Gardens": [1.3224, 103.8153],
  "Farrer Road": [1.3174, 103.8076],
  "Holland Village": [1.3120, 103.7962],
  "one-north": [1.2997, 103.7874],
  "Kent Ridge": [1.2935, 103.7846],
  "Haw Par Villa": [1.2826, 103.7817],
  "Pasir Panjang": [1.2762, 103.7914],
  "Labrador Park": [1.2722, 103.8029],
  "Telok Blangah": [1.2707, 103.8097],
  "Bayfront": [1.2819, 103.8591],
  "Bukit Panjang": [1.3790, 103.7619],
  "Cashew": [1.3698, 103.7644],
  "Hillview": [1.3623, 103.7674],
  "Beauty World": [1.3412, 103.7758],
  "King Albert Park": [1.3358, 103.7832],
  "Sixth Avenue": [1.3308, 103.7970],
  "Tan Kah Kee": [1.3262, 103.8066],
  "Stevens": [1.3201, 103.8260],
  "Rochor": [1.3038, 103.8526],
  "Downtown": [1.2794, 103.8528],
  "Telok Ayer": [1.2822, 103.8486],
  "Fort Canning": [1.2925, 103.8443],
  "Bencoolen": [1.2988, 103.8507],
  "Jalan Besar": [1.3053, 103.8553],
  "Bendemeer": [1.3138, 103.8629],
  "Geylang Bahru": [1.3214, 103.8716],
  "Mattar": [1.3268, 103.8832],
  "Ubi": [1.3299, 103.8993],
  "Kaki Bukit": [1.3349, 103.9084],
  "Bedok North": [1.3347, 103.9179],
  "Bedok Reservoir": [1.3364, 103.9329],
  "Tampines West": [1.3456, 103.9384],
  "Tampines East": [1.3562, 103.9546],
  "Upper Changi": [1.3417, 103.9614],
  "Expo": [1.3345, 103.9618]
};

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

  renderCustomRoute(routeData, profile = {}) {
    if (!this.map || !this.layersGroup || !routeData) return;
    this.layersGroup.clearLayers();

    // 1. If detailed polyline coordinates were provided, use full arbitrary route renderer
    if (routeData.polyline && routeData.polyline.length > 0) {
      this.renderArbitraryRoute(routeData);
      return;
    }

    // 2. Coordinated fallback geometry when custom results lack polyline geometry
    const resolveStationCoord = (stnName) => {
      if (!stnName) return null;
      const clean = stnName.toLowerCase().replace(/\s+mrt|\s*\(.*?\)/g, '').trim();
      for (const [name, coord] of Object.entries(MRT_STATION_COORDS)) {
        if (clean.includes(name.toLowerCase()) || name.toLowerCase().includes(clean)) {
          return { name, coords: coord };
        }
      }
      return null;
    };

    const originName = profile.boarding_station || profile.origin || '';
    const destName = profile.alighting_station || profile.destination || '';

    const origResolved = resolveStationCoord(originName);
    const destResolved = resolveStationCoord(destName);

    const points = [];

    // Identify intermediate transfer stations from route legs
    (routeData.legs || []).forEach(leg => {
      const legName = leg.name || '';
      for (const [name, coord] of Object.entries(MRT_STATION_COORDS)) {
        if (legName.toLowerCase().includes(name.toLowerCase())) {
          if (!points.some(p => p.coords[0] === coord[0] && p.coords[1] === coord[1])) {
            points.push({ name, coords: coord, leg });
          }
        }
      }
    });

    if (origResolved && !points.some(p => p.name === origResolved.name)) {
      points.unshift(origResolved);
    }
    if (destResolved && !points.some(p => p.name === destResolved.name)) {
      points.push(destResolved);
    }

    // Draw station markers
    points.forEach((stn, idx) => {
      const isFirst = idx === 0;
      const isLast = idx === points.length - 1;

      if (isFirst) {
        const homeIcon = L.divIcon({
          className: '',
          html: `<div class="w-6 h-6 rounded-full bg-indigo-600 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-location-dot"></i></div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker(stn.coords, { icon: homeIcon }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1.5 text-xs">
            <strong class="text-indigo-600">Origin: ${stn.name}</strong><br>
            <span class="text-slate-600">Leaves: ${profile.departure_time || '08:00 AM'}</span>
          </div>
        `);
      } else if (isLast) {
        const destIcon = L.divIcon({
          className: '',
          html: `<div class="w-6 h-6 rounded-full bg-rose-600 border-2 border-white flex items-center justify-center text-white text-[11px] shadow-lg"><i class="fa-solid fa-flag-checkered"></i></div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker(stn.coords, { icon: destIcon }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1.5 text-xs">
            <strong class="text-rose-600">Destination: ${stn.name}</strong><br>
            <span class="text-slate-600">Target ETA: ${routeData.estimated_arrival || '--:--'}</span>
          </div>
        `);
      } else {
        const pinIcon = L.divIcon({
          className: '',
          html: `<div class="w-3.5 h-3.5 rounded-full bg-indigo-500 border-2 border-white shadow"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        });
        L.marker(stn.coords, { icon: pinIcon }).addTo(this.layersGroup).bindPopup(`
          <div class="p-1 text-xs">
            <strong>${stn.name} MRT</strong><br>
            <span class="text-slate-500">Transit hop</span>
          </div>
        `);
      }
    });

    // Draw connecting corridor line and fit bounds
    if (points.length >= 2) {
      const latLngs = points.map(p => p.coords);
      const corridorPoly = L.polyline(latLngs, {
        color: '#6366f1',
        weight: 5,
        dashArray: '8, 8',
        opacity: 0.9
      }).addTo(this.layersGroup);

      corridorPoly.bindPopup(`
        <div class="p-1.5 text-xs">
          <strong class="text-indigo-600">${routeData.title || 'Custom Commuter Route'}</strong><br>
          <span>${routeData.total_duration_min} mins • ${routeData.estimated_arrival}</span><br>
          <span class="text-[10px] text-slate-500">Multimodal path with verified constraints</span>
        </div>
      `);

      this.map.fitBounds(corridorPoly.getBounds(), { padding: [60, 60] });
    } else if (points.length === 1) {
      this.map.setView(points[0].coords, 14);
    } else {
      this.panToCenter();
    }
  }

  panToCenter() {
    if (this.map) this.map.flyTo([1.3190, 103.8980], 12);
  }
}

