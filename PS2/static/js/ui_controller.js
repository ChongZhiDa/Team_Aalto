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

    // Swap locations button
    document.getElementById('btn-swap-locations')?.addEventListener('click', () => {
      const originInput = document.getElementById('origin-input');
      const destInput = document.getElementById('dest-input');
      if (originInput && destInput) {
        const temp = originInput.value;
        originInput.value = destInput.value;
        destInput.value = temp;
        if (this.handlers.onLocationChange) {
          this.handlers.onLocationChange(originInput.value, destInput.value);
        }
      }
    });

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
    badge.textContent = data.source_badge || 'Live';
    if (data.source_badge && data.source_badge.toLowerCase().includes('disruption')) {
      badge.className = 'px-2 py-0.5 text-[10px] font-semibold bg-rose-950 text-rose-400 border border-rose-800 rounded-full';
    } else {
      badge.className = 'px-2 py-0.5 text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full';
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

      if (busDelay) {
        busDelay.className = 'text-[10px] text-slate-400';
        busDelay.textContent = 'Guaranteed Seat';
      }
      if (busCrowd) {
        busCrowd.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-emerald-950 text-emerald-300 border border-emerald-800';
        busCrowd.textContent = 'SEATS AVAIL';
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

      html += `
        <div class="flex items-start gap-2 text-xs">
          <div class="flex flex-col items-center mt-0.5 shrink-0">
            <div class="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] ${iconColor}">
              <i class="fa-solid ${modeIcon}"></i>
            </div>
            ${!isLast ? '<div class="w-0.5 h-4 bg-slate-700/80 my-0.5"></div>' : ''}
          </div>
          <div class="flex-1 pb-0.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-medium text-slate-200 leading-tight">${leg.name}</span>
              <span class="text-[10px] text-slate-400 font-mono shrink-0 ml-1.5">${leg.duration}</span>
            </div>
            <div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
              ${leg.distance ? `<span class="text-[10px] text-slate-400">${leg.distance}</span>` : ''}
              ${exitBadge}
              ${badgeHtml}
            </div>
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

