/**
 * StationBuddy — UI & Interaction Controller.
 * Manages Google Maps style search inputs, arrival timing picker,
 * proactive incident banners, and route options.
 * Owned by: Teammate A (Frontend & Mobile UX)
 */

export class UIController {
  constructor(handlers = {}) {
    this.handlers = handlers; // onSelectRoute, onSwitchScenario, onThresholdChange, onArrivalChange, onLocationChange, onRecenter
    this.bindEvents();
  }

  bindEvents() {
    // Switch to bypass button in proactive detour banner
    document.getElementById('btn-accept-bypass')?.addEventListener('click', () => {
      if (this.handlers.onSelectRoute) this.handlers.onSelectRoute('bypass_dtl');
    });

    // Transit route cards with collapsible step expansion
    const toggleRoute = (routeId, legsId, chevronId) => {
      if (this.currentActiveRouteId === routeId) {
        const legs = document.getElementById(legsId);
        const chevron = document.getElementById(chevronId);
        if (legs) {
          legs.classList.toggle('hidden');
          chevron?.classList.toggle('rotate-180');
        }
      } else {
        this.currentActiveRouteId = routeId;
        if (this.handlers.onSelectRoute) this.handlers.onSelectRoute(routeId);
      }
    };

    document.getElementById('card-primary-ewl')?.addEventListener('click', () => {
      toggleRoute('primary_ewl', 'ewl-legs-container', 'ewl-chevron');
    });
    document.getElementById('card-bypass-dtl')?.addEventListener('click', () => {
      toggleRoute('bypass_dtl', 'dtl-legs-container', 'dtl-chevron');
    });
    document.getElementById('card-bypass-bus10e')?.addEventListener('click', () => {
      toggleRoute('bypass_bus10e', 'bus-legs-container', 'bus-chevron');
    });
    document.getElementById('card-arbitrary-route')?.addEventListener('click', () => {
      toggleRoute('arbitrary_route', 'arbitrary-legs-container', 'arbitrary-chevron');
    });

    // Arrival timing input (editable down to the minute)
    const arrivalInput = document.getElementById('input-arrival-time');

    const triggerArrivalChange = (val24) => {
      if (!val24) return;
      const formatted12h = this.formatTime12h(val24);
      const deskLabel = document.getElementById('target-desk-label');
      if (deskLabel) deskLabel.textContent = formatted12h;
      if (this.handlers.onArrivalChange) this.handlers.onArrivalChange(formatted12h);
    };

    arrivalInput?.addEventListener('change', (e) => {
      triggerArrivalChange(e.target.value);
    });

    arrivalInput?.addEventListener('input', (e) => {
      if (e.target.value && e.target.value.length === 5) {
        triggerArrivalChange(e.target.value);
      }
    });

    const adjustMinutes = (deltaMinutes) => {
      if (!arrivalInput) return;
      const val = arrivalInput.value || '08:45';
      const parts = val.split(':');
      if (parts.length < 2) return;
      let totalMins = (parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10) + deltaMinutes + 1440) % 1440;
      const newH = String(Math.floor(totalMins / 60)).padStart(2, '0');
      const newM = String(totalMins % 60).padStart(2, '0');
      const newVal = `${newH}:${newM}`;
      arrivalInput.value = newVal;
      triggerArrivalChange(newVal);
    };

    document.getElementById('btn-minute-dec')?.addEventListener('click', () => adjustMinutes(-1));
    document.getElementById('btn-minute-inc')?.addEventListener('click', () => adjustMinutes(1));

    // Location inputs & Search actions
    const originInput = document.getElementById('origin-input');
    const destInput = document.getElementById('dest-input');

    const triggerLocationChange = () => {
      if (originInput && destInput && this.handlers.onLocationChange) {
        this.handlers.onLocationChange(originInput.value, destInput.value);
      }
    };

    // Swap locations button
    document.getElementById('btn-swap-locations')?.addEventListener('click', () => {
      if (originInput && destInput) {
        const temp = originInput.value;
        originInput.value = destInput.value;
        destInput.value = temp;
        triggerLocationChange();
      }
    });

    // Search button
    document.getElementById('btn-search-route')?.addEventListener('click', () => {
      triggerLocationChange();
    });

    // Auto-search on change or enter key
    originInput?.addEventListener('change', triggerLocationChange);
    destInput?.addEventListener('change', triggerLocationChange);

    originInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        triggerLocationChange();
      }
    });

    destInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        triggerLocationChange();
      }
    });

    // Real-time postal detection hint
    const updatePostalHint = () => {
      const origVal = originInput?.value || '';
      const destVal = destInput?.value || '';
      const origPostal = origVal.match(/(?:^|[^\d])[sS]?(\d{6})(?:[^\d]|$)/);
      const destPostal = destVal.match(/(?:^|[^\d])[sS]?(\d{6})(?:[^\d]|$)/);
      const hintBar = document.getElementById('location-hint-bar');
      const hintText = document.getElementById('location-hint-text');

      if (hintBar && hintText) {
        if (origPostal || destPostal) {
          hintBar.classList.remove('hidden');
          const parts = [];
          if (origPostal) parts.push(`Origin: S${origPostal[1]}`);
          if (destPostal) parts.push(`Dest: S${destPostal[1]}`);
          hintText.innerHTML = `<i class="fa-solid fa-location-crosshairs text-blue-400 animate-pulse"></i> <span>Postal Geocoding: <strong>${parts.join(' • ')}</strong></span>`;
        } else {
          hintBar.classList.add('hidden');
        }
      }
    };

    originInput?.addEventListener('input', updatePostalHint);
    destInput?.addEventListener('input', updatePostalHint);
    updatePostalHint();

    // Recenter map button
    document.getElementById('btn-recenter')?.addEventListener('click', () => {
      if (this.handlers.onRecenter) this.handlers.onRecenter();
    });

    // Toggle alternative routes button
    document.getElementById('btn-toggle-all-routes')?.addEventListener('click', () => {
      if (this.handlers.onToggleAllRoutes) this.handlers.onToggleAllRoutes();
    });

    // Scenario modal
    const toggleBtn = document.getElementById('scenario-toggle-btn');
    const closeBtn = document.getElementById('scenario-close-btn');
    const drawer = document.getElementById('scenario-drawer');

    toggleBtn?.addEventListener('click', () => {
      if (this.handlers.onOpenScenarios) this.handlers.onOpenScenarios();
      drawer?.classList.remove('hidden');
    });

    closeBtn?.addEventListener('click', () => {
      drawer?.classList.add('hidden');
    });

    // Threshold dropdown
    document.getElementById('select-noise-threshold')?.addEventListener('change', (e) => {
      if (this.handlers.onThresholdChange) this.handlers.onThresholdChange(e.target.value);
    });
  }

  updateTopBar(data) {
    const badge = document.getElementById('source-badge');
    if (!badge) return;
    const badgeText = data.source_badge || 'Live';
    const lower = badgeText.toLowerCase();

    if (lower.includes('live') || lower.includes('datamall') || lower.includes('weather')) {
      badge.className = 'px-2.5 py-0.5 text-[10px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-500 rounded-full flex items-center gap-1.5 shadow-[0_0_8px_rgba(16,185,129,0.3)]';
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> ${data.source_badge || 'LTA DataMall & Weather (Live)'}`;
    } else if (lower.includes('disruption') || lower.includes('fault')) {
      badge.className = 'px-2.5 py-0.5 text-[10px] font-semibold bg-rose-950 text-rose-300 border border-rose-500 rounded-full flex items-center gap-1.5 shadow-[0_0_8px_rgba(244,63,94,0.3)]';
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-rose-400 animate-bounce"></span> ${data.source_badge || 'Disruption Mode'}`;
    } else {
      badge.className = 'px-2.5 py-0.5 text-[10px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-700 rounded-full flex items-center gap-1.5';
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-indigo-400"></span> ${data.source_badge || 'Simulation Mode'}`;
    }
  }

  updateAlertBanner(data) {
    const decision = data.decision;
    const banner = document.getElementById('alert-banner');
    const alertIcon = document.getElementById('alert-icon');
    const statusLabel = document.getElementById('alert-status-label');
    const headline = document.getElementById('alert-headline');
    const detail = document.getElementById('alert-detail');
    const actionRow = document.getElementById('alert-action-row');
    const weatherChip = document.getElementById('weather-chip');
    const filterBadge = document.getElementById('noise-filter-badge');

    if (filterBadge) filterBadge.textContent = `Noise Filter: <${decision.threshold_minutes}m Silent`;

    if (data.weather && weatherChip) {
      const isRain = data.weather.rain_alert;
      weatherChip.innerHTML = isRain
        ? `<i class="fa-solid fa-cloud-showers-heavy text-blue-400"></i><span>${data.weather.origin_forecast}</span>`
        : `<i class="fa-solid fa-sun text-amber-400"></i><span>${data.weather.origin_forecast}</span>`;
    }

    if (decision.urgency === 'CALM') {
      banner.className = 'pointer-events-auto rounded-xl p-3 border shadow-2xl transition-all duration-300 bg-emerald-950/80 border-emerald-700/80';
      alertIcon.className = 'w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px]';
      alertIcon.innerHTML = '<i class="fa-solid fa-check"></i>';
      statusLabel.className = 'text-[11px] font-bold uppercase tracking-wider text-emerald-400';
      statusLabel.textContent = 'On Schedule';
      headline.textContent = decision.headline;
      detail.textContent = decision.one_line_advice;
      actionRow.classList.add('hidden');
    } else {
      banner.className = 'pointer-events-auto rounded-xl p-3 border shadow-2xl transition-all duration-300 bg-rose-950/90 border-rose-600/90 ring-1 ring-rose-500/40';
      alertIcon.className = 'w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center text-[10px]';
      alertIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation animate-bounce"></i>';
      statusLabel.className = 'text-[11px] font-bold uppercase tracking-wider text-rose-400';
      statusLabel.textContent = 'Detour Recommendation';
      headline.textContent = decision.headline;
      detail.textContent = decision.one_line_advice;
      actionRow.classList.remove('hidden');
    }
  }

  renderCrowdChip(element, crowdLevel) {
    if (!element) return;
    const cl = (crowdLevel || 'm').toLowerCase();
    if (cl === 'l' || cl === 'low') {
      element.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-emerald-950 text-emerald-300 border border-emerald-800';
      element.textContent = 'CROWD: LOW';
    } else if (cl === 'h' || cl === 'high') {
      element.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-rose-950 text-rose-300 border border-rose-800';
      element.textContent = 'CROWD: HIGH';
    } else {
      element.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-950 text-amber-300 border border-amber-800';
      element.textContent = 'CROWD: MOD';
    }
  }

  renderBusCrowdBadge(element, bus) {
    if (!element) return;
    const cl = (bus.crowd_level || '').toLowerCase();
    const statusText = (bus.status || '').toUpperCase();
    const isLive = bus.bus_load_source === 'live';

    if (cl === 'l' || statusText.includes('SEA') || statusText.includes('SEATS') || statusText.includes('SEAT')) {
      // SEA / l -> 🟢 Green pill: "Seats Available"
      element.className = 'px-2 py-0.5 text-[9px] font-bold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-600 flex items-center gap-1 shadow-sm';
      element.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Seats Available${isLive ? ' (Live)' : ''}`;
    } else if (cl === 'h' || statusText.includes('LSD') || statusText.includes('LIMITED') || statusText.includes('CROWDED')) {
      // LSD / h -> 🔴 Red pill: "Crowded (Limited Standing)"
      element.className = 'px-2 py-0.5 text-[9px] font-bold rounded-full bg-rose-950 text-rose-300 border border-rose-600 flex items-center gap-1 shadow-sm';
      element.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse"></span> Crowded (Limited Standing)${isLive ? ' (Live)' : ''}`;
    } else {
      // SDA / m -> 🟡 Yellow pill: "Standing Only"
      element.className = 'px-2 py-0.5 text-[9px] font-bold rounded-full bg-amber-950 text-amber-300 border border-amber-600 flex items-center gap-1 shadow-sm';
      element.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Standing Only${isLive ? ' (Live)' : ''}`;
    }
  }

  updateRouteCards(data, activeRouteId) {
    const routes = data.routes || {};

    // 1. Primary EWL Card
    const ewl = routes.primary_ewl;
    if (ewl) {
      const ewlArrival = document.getElementById('ewl-arrival-time');
      const ewlDelay = document.getElementById('ewl-delay-tag');
      const ewlMeta = document.getElementById('ewl-route-meta');
      const ewlCrowd = document.getElementById('ewl-crowd-chip');

      if (ewlArrival) ewlArrival.textContent = ewl.estimated_arrival;
      const ewlShelter = ewl.sheltered_percent ? ` (${ewl.sheltered_percent}% covered)` : '';
      if (ewlMeta) ewlMeta.textContent = `Leaves 07:40 • ${ewl.total_duration_min} mins total${ewlShelter}`;

      const ewlShelterChip = document.getElementById('ewl-shelter-chip');
      if (ewlShelterChip && ewl.sheltered_percent) {
        ewlShelterChip.textContent = `🛡️ ${ewl.sheltered_percent}% SHELTER`;
      }

      if (ewl.delay_minutes > 0) {
        if (ewlArrival) ewlArrival.className = 'text-sm font-bold text-rose-400';
        if (ewlDelay) {
          ewlDelay.className = 'text-[10px] text-rose-400 font-semibold';
          ewlDelay.textContent = `+${ewl.delay_minutes}m Delay (LATE)`;
        }
        this.renderCrowdChip(ewlCrowd, ewl.crowd_level || 'h');
      } else {
        if (ewlArrival) ewlArrival.className = 'text-sm font-bold text-emerald-400';
        if (ewlDelay) {
          ewlDelay.className = 'text-[10px] text-emerald-400';
          ewlDelay.textContent = 'On Time';
        }
        this.renderCrowdChip(ewlCrowd, ewl.crowd_level || 'm');
      }
    }

    // 2. Downtown Line Bypass Card
    const dtl = routes.bypass_dtl;
    if (dtl) {
      const dtlArrival = document.getElementById('dtl-arrival-time');
      const dtlDelay = document.getElementById('dtl-delay-tag');
      const dtlMeta = document.getElementById('dtl-route-meta');
      const dtlCrowd = document.getElementById('dtl-crowd-chip');

      if (dtlArrival) dtlArrival.textContent = dtl.estimated_arrival;
      const dtlShelter = dtl.sheltered_percent ? ` (${dtl.sheltered_percent}% covered)` : '';
      if (dtlMeta) dtlMeta.textContent = `Tampines DTL → Telok Ayer • ${dtl.total_duration_min} mins${dtlShelter}`;

      const dtlShelterChip = document.getElementById('dtl-shelter-chip');
      if (dtlShelterChip && dtl.sheltered_percent) {
        dtlShelterChip.textContent = `🛡️ ${dtl.sheltered_percent}% SHELTER`;
      }

      if (dtlDelay) {
        if (dtl.is_recommended) {
          dtlDelay.className = 'text-[10px] text-blue-400 font-semibold';
          dtlDelay.textContent = '★ Recommended Bypass';
        } else {
          dtlDelay.className = 'text-[10px] text-slate-400';
          dtlDelay.textContent = 'Reliable Alternative';
        }
      }
      this.renderCrowdChip(dtlCrowd, dtl.crowd_level || 'l');
    }

    // 3. Express Bus 10e Card
    const bus = routes.bypass_bus10e;
    if (bus) {
      const busArrival = document.getElementById('bus-arrival-time');
      const busDelay = document.getElementById('bus-delay-tag');
      const busMeta = document.getElementById('bus-route-meta');
      const busCrowd = document.getElementById('bus-crowd-chip');

      if (busArrival) busArrival.textContent = bus.estimated_arrival;
      if (busMeta) busMeta.textContent = `Expressway via ECP to CBD • ${bus.total_duration_min} mins`;

      const busShelterChip = document.getElementById('bus-shelter-chip');
      if (busShelterChip && bus.sheltered_percent) {
        busShelterChip.textContent = `☂️ ${bus.sheltered_percent}% SHELTER`;
      }

      // Color-coded crowd badge: SEA/l -> Green, SDA/m -> Yellow, LSD/h -> Red
      this.renderBusCrowdBadge(busCrowd, bus);

      if (busDelay) {
        const isLive = bus.bus_load_source === 'live';
        busDelay.className = isLive ? 'text-[10px] text-emerald-400 font-semibold flex items-center justify-end gap-1' : 'text-[10px] text-slate-400';
        busDelay.innerHTML = isLive
          ? `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Live LTA Load`
          : (bus.status || 'Guaranteed Seat');
      }
    }

    // Render turn-by-turn steps inside each card with station exit guidance
    if (ewl) this.renderRouteLegs('ewl-legs-container', ewl.legs, 'emerald', {
      exitStation: 'Raffles Place (EW14)',
      exitDoor: 'Exit B',
      exitNote: 'Direct underground linkway to One Raffles Place basement',
      shelterPercent: ewl.sheltered_percent || 80
    });
    if (dtl) this.renderRouteLegs('dtl-legs-container', dtl.legs, 'blue', {
      exitStation: 'Telok Ayer (DT18)',
      exitDoor: 'Exit B',
      exitNote: 'Sheltered linkway via Cross St & Church St to desk',
      shelterPercent: dtl.sheltered_percent || 95
    });
    if (bus) this.renderRouteLegs('bus-legs-container', bus.legs, 'purple', {
      exitStation: 'Fullerton Sq Stop (03011)',
      exitDoor: 'Bus Stop',
      exitNote: 'Walk via Battery Rd to One Raffles Place',
      shelterPercent: bus.sheltered_percent || 55
    });

    this.highlightActiveCard(activeRouteId);
  }

  renderRouteLegs(containerId, legs, corridorColor = 'emerald', exitInfo = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (!legs || !legs.length) {
      container.innerHTML = '';
      return;
    }

    let html = '<div class="flex flex-col gap-2 pt-2 border-t border-slate-700/60 mt-1">';
    legs.forEach((leg, index) => {
      const isLast = index === legs.length - 1;
      let modeIcon = 'fa-person-walking';
      let iconColor = 'text-slate-300';
      let badgeHtml = '';
      let exitBadge = '';

      // Detect specific station exit in leg name
      const exitMatch = leg.name.match(/Exit\s+[A-Z]/i);
      if (exitMatch) {
        exitBadge = `<span class="px-1.5 py-0.2 rounded bg-blue-900/90 text-blue-200 border border-blue-600 text-[9px] font-bold flex items-center gap-1 shadow-sm"><i class="fa-solid fa-door-open text-[8px] text-blue-400"></i> ${exitMatch[0]}</span>`;
      }

      if (leg.mode === 'TRAIN') {
        modeIcon = 'fa-train-subway';
        iconColor = corridorColor === 'blue' ? 'text-blue-400' : 'text-emerald-400';
        badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[9px] font-mono">${leg.stops || 0} stops</span>`;
      } else if (leg.mode === 'BUS') {
        modeIcon = 'fa-bus';
        iconColor = 'text-purple-400';
        badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[9px] font-mono">${leg.stops || 0} stops</span>`;
      } else if (leg.mode === 'WALK') {
        modeIcon = 'fa-person-walking';
        iconColor = 'text-amber-400';
        const pct = leg.sheltered_percent;
        if (pct !== undefined) {
          if (pct >= 85) {
            badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-emerald-950/90 text-emerald-300 border border-emerald-800 text-[9px] font-semibold flex items-center gap-1">🛡️ ${pct}% Covered Walkway</span>`;
          } else if (pct >= 60) {
            badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-amber-950/90 text-amber-300 border border-amber-800 text-[9px] font-semibold flex items-center gap-1">☂️ ${pct}% Covered</span>`;
          } else {
            badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[9px] font-semibold">⚠️ ${pct}% Open Footpath</span>`;
          }
        }
      }

      // Exact turn-by-turn walking steps breakdown
      let walkingStepsHtml = '';
      if (leg.mode === 'WALK') {
        const details = this.getDetailedWalkingSteps(leg.name, exitInfo);
        if (details && details.steps && details.steps.length > 0) {
          walkingStepsHtml = `
            <div class="mt-2 p-2.5 rounded-lg bg-slate-900/95 border border-slate-700/80 text-[10px] flex flex-col gap-1.5 shadow-md">
              <div class="flex items-center justify-between text-amber-300 font-bold border-b border-slate-800 pb-1">
                <span class="flex items-center gap-1.5"><i class="fa-solid fa-diamond-turn-right text-amber-400"></i> Exact Walking Guidance</span>
                <span class="text-slate-400 font-mono text-[9px] font-normal">${details.shelter || ''}</span>
              </div>
              <ol class="flex flex-col gap-1.5 pl-0.5">
                ${details.steps.map((step, sIdx) => `
                  <li class="flex items-start gap-2 text-slate-200 leading-snug">
                    <span class="w-4 h-4 rounded-full bg-amber-950 text-amber-300 border border-amber-800/80 flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5">${sIdx + 1}</span>
                    <span class="text-[11px]">${step}</span>
                  </li>
                `).join('')}
              </ol>
            </div>
          `;
        }
      }

      html += `
        <div class="flex items-start gap-2 text-xs">
          <div class="flex flex-col items-center mt-0.5 shrink-0">
            <div class="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] ${iconColor}">
              <i class="fa-solid ${modeIcon}"></i>
            </div>
            ${!isLast ? '<div class="w-0.5 h-full min-h-[16px] bg-slate-700/80 my-0.5"></div>' : ''}
          </div>
          <div class="flex-1 pb-1">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-semibold text-slate-100 leading-tight">${leg.name}</span>
              <span class="text-[10px] text-slate-300 font-mono font-bold shrink-0 ml-1.5">${leg.duration}</span>
            </div>
            <div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
              ${leg.distance ? `<span class="text-[10px] text-slate-400">${leg.distance}</span>` : ''}
              ${exitBadge}
              ${badgeHtml}
            </div>
            ${walkingStepsHtml}
          </div>
        </div>
      `;
    });

    // Exit Guidance & Shelter Summary Box
    if (exitInfo) {
      const isHighShelter = exitInfo.shelterPercent >= 80;
      const boxBorder = isHighShelter ? 'border-emerald-800/60 bg-emerald-950/30' : 'border-amber-800/60 bg-amber-950/30';
      const shelterColor = isHighShelter ? 'text-emerald-300' : 'text-amber-300';
      const shelterIcon = isHighShelter ? 'fa-shield-halved' : 'fa-umbrella';

      html += `
        <div class="mt-2 p-2 rounded-lg border ${boxBorder} flex flex-col gap-1 text-[11px]">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5 text-blue-300 font-semibold">
              <i class="fa-solid fa-door-open text-blue-400"></i>
              <span>Alight: <strong>${exitInfo.exitStation} &rarr; ${exitInfo.exitDoor}</strong></span>
            </div>
            <span class="${shelterColor} font-bold flex items-center gap-1 text-[10px]">
              <i class="fa-solid ${shelterIcon} text-[9px]"></i> ${exitInfo.shelterPercent}% Door-to-Door Shelter
            </span>
          </div>
          <p class="text-[10px] text-slate-400">${exitInfo.exitNote}</p>
        </div>
      `;
    }

    html += '</div>';
    container.innerHTML = html;
  }

  highlightActiveCard(activeRouteId) {
    this.currentActiveRouteId = activeRouteId;
    document.querySelectorAll('.route-card').forEach(card => card.classList.remove('active-route'));

    const routeConfigs = [
      { id: 'arbitrary_route', cardId: 'card-arbitrary-route', legsId: 'arbitrary-legs-container', chevronId: 'arbitrary-chevron' },
      { id: 'primary_ewl', cardId: 'card-primary-ewl', legsId: 'ewl-legs-container', chevronId: 'ewl-chevron' },
      { id: 'bypass_dtl', cardId: 'card-bypass-dtl', legsId: 'dtl-legs-container', chevronId: 'dtl-chevron' },
      { id: 'bypass_bus10e', cardId: 'card-bypass-bus10e', legsId: 'bus-legs-container', chevronId: 'bus-chevron' },
    ];

    routeConfigs.forEach(({ id, cardId, legsId, chevronId }) => {
      const card = document.getElementById(cardId);
      const legsContainer = document.getElementById(legsId);
      const chevron = document.getElementById(chevronId);
      const isActive = id === activeRouteId;

      if (isActive) {
        card?.classList.add('active-route');
        legsContainer?.classList.remove('hidden');
        chevron?.classList.add('rotate-180');
      } else {
        legsContainer?.classList.add('hidden');
        chevron?.classList.remove('rotate-180');
      }
    });
  }

  renderScenariosList(scenarios, currentId, onSelect) {
    const container = document.getElementById('scenarios-options-container');
    if (!container) return;
    container.innerHTML = '';

    scenarios.forEach(sc => {
      const isSelected = sc.id === currentId;
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
      btn.addEventListener('click', () => {
        onSelect(sc.id);
        document.getElementById('scenario-drawer')?.classList.add('hidden');
      });
      container.appendChild(btn);
    });

    // Live Feed button
    const liveBtn = document.createElement('button');
    const isLive = currentId === 'live';
    liveBtn.className = `w-full text-left p-2.5 rounded-lg border transition flex flex-col gap-1 ${
      isLive ? 'bg-indigo-950/70 border-indigo-500/80 ring-1 ring-indigo-500/40' : 'bg-slate-800/60 border-slate-700 hover:bg-slate-800'
    }`;
    liveBtn.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-xs text-white">📡 Live LTA DataMall & Weather</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded ${isLive ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300'}">Live Feed</span>
      </div>
      <p class="text-[11px] text-slate-400 leading-snug">Polls actual DataMall TrainServiceAlerts & data.gov.sg nowcasts directly.</p>
    `;
    liveBtn.addEventListener('click', () => {
      onSelect('live');
      document.getElementById('scenario-drawer')?.classList.add('hidden');
    });
    container.appendChild(liveBtn);
  }

  setOfflineStatus(isOffline) {
    const badge = document.getElementById('offline-indicator');
    if (!badge) return;
    if (isOffline) {
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }

  setAllRoutesButtonState(isShowingAll) {
    const btn = document.getElementById('btn-toggle-all-routes');
    const icon = document.getElementById('toggle-all-icon');
    const label = document.getElementById('toggle-all-label');
    if (!btn || !icon || !label) return;

    if (isShowingAll) {
      label.textContent = 'Hide Other Routes';
      icon.className = 'fa-solid fa-eye-slash text-blue-400';
      btn.classList.add('bg-blue-950/90', 'border-blue-500/80', 'text-blue-200');
      btn.classList.remove('bg-slate-900/90', 'border-slate-700', 'text-slate-300');
    } else {
      label.textContent = 'Show Other Routes';
      icon.className = 'fa-solid fa-layer-group text-blue-400';
      btn.classList.remove('bg-blue-950/90', 'border-blue-500/80', 'text-blue-200');
      btn.classList.add('bg-slate-900/90', 'border-slate-700', 'text-slate-300');
    }
  }

  renderArbitraryRouteCard(routeData) {
    const card = document.getElementById('card-arbitrary-route');
    if (!card) return;

    card.classList.remove('hidden');

    const titleEl = document.getElementById('arbitrary-route-title');
    const metaEl = document.getElementById('arbitrary-route-meta');
    const arrivalEl = document.getElementById('arbitrary-arrival-time');
    const statusEl = document.getElementById('arbitrary-status-tag');
    const shelterChip = document.getElementById('arbitrary-shelter-chip');
    const graphChip = document.getElementById('arbitrary-graph-chip');

    if (titleEl) titleEl.textContent = routeData.title || 'Arbitrary Graph Route';
    if (metaEl) metaEl.textContent = `${routeData.status || ''} • ${routeData.total_duration_min} mins total`;
    if (arrivalEl) arrivalEl.textContent = routeData.estimated_arrival || '--:-- AM';
    if (statusEl) statusEl.textContent = `${routeData.total_duration_min} min path`;
    if (shelterChip && routeData.sheltered_percent) {
      shelterChip.textContent = `🛡️ ${routeData.sheltered_percent}% SHELTER`;
    }
    if (graphChip && routeData.lines_used) {
      graphChip.textContent = routeData.lines_used.join(' → ');
    }

    // Render turn-by-turn legs
    const destStn = routeData.title?.split(' to ')[1]?.split(' (')[0] || 'Destination';
    this.renderRouteLegs('arbitrary-legs-container', routeData.legs, 'indigo', {
      exitStation: `${destStn} MRT`,
      exitDoor: 'Exit B',
      exitNote: 'Optimal graph pathfinder connection',
      shelterPercent: routeData.sheltered_percent || 80
    });

    this.highlightActiveCard('arbitrary_route');
  }

  hideArbitraryRouteCard() {
    const card = document.getElementById('card-arbitrary-route');
    if (card) card.classList.add('hidden');
  }

  extractStationName(inputStr) {
    if (!inputStr) return '';
    const trimmed = inputStr.trim();

    // 1. Check for 6-digit Singapore postal code (e.g. "529538", "S529538", or embedded in address)
    const postalMatch = trimmed.match(/(?:^|[^\d])[sS]?(\d{6})(?:[^\d]|$)/);
    if (postalMatch) {
      return postalMatch[1];
    }

    const knownStations = [
      "Marina South Pier", "Gardens by the Bay", "Orchard Boulevard", "Woodlands North", 
      "Woodlands South", "Botanic Gardens", "King Albert Park", "Bukit Panjang", 
      "Beauty World", "Sixth Avenue", "Tan Kah Kee", "Little India", "Fort Canning", 
      "Geylang Bahru", "Bedok Reservoir", "Tampines West", "Tampines East", "Upper Changi", 
      "Choa Chu Kang", "Bukit Batok", "Bukit Gombak", "Yio Chu Kang", "Ang Mo Kio", 
      "Toa Payoh", "Dhoby Ghaut", "Marina Bay", "HarbourFront", "Clarke Quay", "Farrer Park", 
      "Potong Pasir", "Bras Basah", "Nicoll Highway", "Lorong Chuan", "Holland Village", 
      "Buona Vista", "Kent Ridge", "Haw Par Villa", "Pasir Panjang", "Labrador Park", 
      "Telok Blangah", "Upper Thomson", "Shenton Way", "Chinese Garden", "Tanjong Pagar", 
      "Outram Park", "Tiong Bahru", "Jurong East", "Tanah Merah", "Paya Lebar", 
      "Raffles Place", "City Hall", "Boon Keng", "Woodleigh", "Serangoon", "MacPherson", 
      "Tai Seng", "Caldecott", "one-north", "Mayflower", "Bright Hill", "Springleaf", 
      "Admiralty", "Sembawang", "Canberra", "Marsiling", "Woodlands", "Bencoolen", 
      "Bayfront", "Downtown", "Telok Ayer", "Chinatown", "Kaki Bukit", "Bedok North", 
      "Pasir Ris", "Tampines", "Kembangan", "Aljunied", "Lavender", "Redhill", 
      "Queenstown", "Commonwealth", "Clementi", "Lakeside", "Boon Lay", "Pioneer", 
      "Joo Koon", "Yew Tee", "Kranji", "Yishun", "Khatib", "Bishan", "Braddell", 
      "Novena", "Newton", "Orchard", "Somerset", "Hougang", "Buangkok", "Sengkang", 
      "Punggol", "Stadium", "Dakota", "Bartley", "Marymount", "Stevens", "Napier", 
      "Havelock", "Maxwell", "Cashew", "Hillview", "Rochor", "Bugis", "Promenade", 
      "Mattar", "Simei", "Bedok", "Eunos", "Kallang", "Dover", "Lentor", "Ubi", "Expo"
    ];
    const upper = trimmed.toUpperCase();
    for (const stn of knownStations) {
      if (upper.includes(stn.toUpperCase())) {
        return stn;
      }
    }
    const cleaned = trimmed.replace(/\(.*?\)/g, '').replace(/Blk\s+\w+/gi, '').replace(/St\s+\w+/gi, '').trim();
    return cleaned || trimmed;
  }

  getDetailedWalkingSteps(legName, exitInfo) {
    const nameLower = (legName || '').toLowerCase();
    
    // 1. Destination Walk to One Raffles Place / Desk from Raffles Place EWL
    if (nameLower.includes('raffles place') && (nameLower.includes('desk') || nameLower.includes('destination') || nameLower.includes('office') || nameLower.includes('final'))) {
      return {
        landmark: 'Exit B Direct Underpass Linkway',
        shelter: '🛡️ 100% Covered & Air-Conditioned',
        steps: [
          'Concourse Level &rarr; Tap out at fare gates and follow overhead signs for <strong>Exit B (One Raffles Place / Chulia St)</strong>.',
          'Take the Exit B descending escalator directly into the <strong>B1 retail underpass linkway</strong>.',
          'Walk straight 120m through the air-conditioned underpass past Starbucks directly into <strong>One Raffles Place Tower 1 lobby elevators</strong> (zero rain exposure).'
        ]
      };
    }

    // 2. Destination Walk from Telok Ayer DTL to One Raffles Place / Desk
    if (nameLower.includes('telok ayer') && (nameLower.includes('desk') || nameLower.includes('destination') || nameLower.includes('office') || nameLower.includes('final'))) {
      return {
        landmark: 'Cross St & Church St Covered Arcade',
        shelter: '🛡️ 95% Covered Linkway',
        steps: [
          'Concourse Level &rarr; Tap out and take <strong>Exit B escalator</strong> up to street level at Cross Street.',
          'Walk 180m under the <strong>Cross Street covered arcade</strong> pavement past Far East Square.',
          'Turn left onto <strong>Church Street covered walkway</strong> past Prudential Tower (150m).',
          'Enter through the <strong>One Raffles Place rear glass atrium entrance</strong> (80m).'
        ]
      };
    }

    // 3. Destination Walk from Fullerton Sq to One Raffles Place
    if (nameLower.includes('fullerton')) {
      return {
        landmark: 'Battery Rd & Chulia St Pavement',
        shelter: '☂️ 55% Sheltered (Open Crossing)',
        steps: [
          'Alight at <strong>Fullerton Sq (Bus Stop 03011)</strong> along Fullerton Road.',
          'Walk 120m along Battery Road pavement towards Raffles Place square.',
          'Cross Chulia Street at the signalized pedestrian crossing into <strong>One Raffles Place main lobby</strong>.'
        ]
      };
    }

    // 4. Origin Walk to Jurong East MRT
    if (nameLower.includes('jurong east')) {
      return {
        landmark: 'JEM / Westgate Elevated Linkbridge',
        shelter: '🛡️ 75% Covered Linkway',
        steps: [
          'Access station via <strong>JEM / Westgate Level 2 elevated covered bridge</strong> or Bus Interchange Exit A.',
          'Tap in at the <strong>EWL Concourse fare gates</strong>.',
          'Take the central escalator up to <strong>Platform A/B</strong> for East-West Line trains towards Pasir Ris.'
        ]
      };
    }

    // 5. Origin Walk from Home to Tampines EWL
    if (nameLower.includes('tampines') && (nameLower.includes('home') || nameLower.includes('ewl') || nameLower.includes('ew2'))) {
      return {
        landmark: 'Tampines Central 1 Covered Linkway',
        shelter: '🛡️ 80% Sheltered Linkway',
        steps: [
          'Depart Blk 230 via the <strong>continuous HDB high-covered walkway corridor</strong> (300m).',
          'Follow the sheltered footpath past Tampines Central 1 and Tampines 1 mall (150m).',
          'Enter Tampines MRT Concourse through <strong>Entrance Exit A</strong> (70m to fare gates).'
        ]
      };
    }

    // 6. Origin Walk from Home to Tampines DTL
    if (nameLower.includes('tampines') && (nameLower.includes('dtl') || nameLower.includes('dt32') || nameLower.includes('downtown'))) {
      return {
        landmark: 'Tampines East / DTL Covered Connector',
        shelter: '🛡️ 90% Sheltered Linkway',
        steps: [
          'Depart Blk 230 heading South towards Tampines Central along covered walkway.',
          'Follow covered linkway to <strong>Tampines DTL Entrance Exit B</strong>.',
          'Tap in at fare gates and descend escalator to Platform B2.'
        ]
      };
    }

    // 7. Interchange transfer: Buona Vista (EWL <-> CCL)
    if (nameLower.includes('buona vista')) {
      return {
        landmark: 'Exit C Sheltered Transfer Gantry',
        shelter: '🛡️ 100% Sheltered Transfer',
        steps: [
          'Alight at elevated EWL platform & take the central escalator down to Concourse level.',
          'Pass through the sheltered transfer linkway (Exit C connection) following <strong>yellow Circle Line floor decals</strong>.',
          'Descend 2 escalators to the <strong>Circle Line B2 underground platform</strong> (3 min transfer walk).'
        ]
      };
    }

    // 8. Interchange transfer: Bugis (EWL <-> DTL)
    if (nameLower.includes('bugis')) {
      return {
        landmark: 'Air-Conditioned Transfer Linkway',
        shelter: '🛡️ 100% Covered & Air-Conditioned',
        steps: [
          'Exit EWL platform towards B2 concourse.',
          'Follow <strong>blue Downtown Line signage</strong> through 220m air-conditioned underground linkway.',
          'Descend escalator to B3 Downtown Line platform (4 min transfer walk).'
        ]
      };
    }

    // 9. Interchange transfer: Outram Park (EWL <-> TEL / NEL)
    if (nameLower.includes('outram park')) {
      return {
        landmark: 'Concourse Moving Travelator Link',
        shelter: '🛡️ 100% Sheltered Connector',
        steps: [
          'Follow overhead signs towards the Thomson-East Coast / North-East Line transfer linkway.',
          'Step onto the <strong>concourse moving travelator connector</strong> (4 min walk, 100% sheltered).'
        ]
      };
    }

    // 10. General Interchange / Transfer
    if (nameLower.includes('interchange') || nameLower.includes('transfer')) {
      return {
        landmark: 'Internal Station Transfer Linkway',
        shelter: '🛡️ 100% Sheltered Linkway',
        steps: [
          'Alight from train and proceed to concourse level following line color-coded overhead signage.',
          'Pass through the internal platform transfer gantry to connecting line platform.'
        ]
      };
    }

    // 11. Generic final destination walk
    if (nameLower.includes('destination') || nameLower.includes('final')) {
      const exitDoor = exitInfo?.exitDoor || 'Exit B';
      const exitStation = exitInfo?.exitStation || 'MRT Station';
      return {
        landmark: `${exitStation} to Destination`,
        shelter: `🛡️ ${exitInfo?.shelterPercent || 80}% Covered Walkway`,
        steps: [
          `Alight at platform and take escalators to Concourse level.`,
          `Tap out at fare gates and follow overhead signs to <strong>${exitDoor}</strong>.`,
          `Follow covered walkway and pedestrian crossings directly to destination lobby.`
        ]
      };
    }

    // 12. Generic walk to MRT
    if (nameLower.includes('walk to') || nameLower.includes('mrt')) {
      return {
        landmark: 'Street to Station Concourse',
        shelter: '🛡️ Covered Footpath',
        steps: [
          'Follow nearest covered pedestrian linkway towards station entrance.',
          'Enter station concourse via Entrance Exit A/B and tap in at fare gates.'
        ]
      };
    }

    return null;
  }

  formatTime12h(timeStr) {
    if (!timeStr) return '08:45 AM';
    if (timeStr.includes('AM') || timeStr.includes('PM')) return timeStr;
    const parts = timeStr.split(':');
    if (parts.length < 2) return timeStr;
    let h = parseInt(parts[0], 10);
    const m = parts[1];
    const ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12;
    if (h === 0) h = 12;
    const hStr = String(h).padStart(2, '0');
    return `${hStr}:${m} ${ampm}`;
  }
}

