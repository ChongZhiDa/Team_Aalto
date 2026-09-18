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

    // Transit route cards
    document.getElementById('card-primary-ewl')?.addEventListener('click', () => {
      if (this.handlers.onSelectRoute) this.handlers.onSelectRoute('primary_ewl');
    });
    document.getElementById('card-bypass-dtl')?.addEventListener('click', () => {
      if (this.handlers.onSelectRoute) this.handlers.onSelectRoute('bypass_dtl');
    });
    document.getElementById('card-bypass-bus10e')?.addEventListener('click', () => {
      if (this.handlers.onSelectRoute) this.handlers.onSelectRoute('bypass_bus10e');
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

  updateRouteCards(data, activeRouteId) {
    const routes = data.routes;
    const ewl = routes.primary_ewl;
    const ewlArrival = document.getElementById('ewl-arrival-time');
    const ewlDelay = document.getElementById('ewl-delay-tag');
    const ewlMeta = document.getElementById('ewl-route-meta');
    const ewlCrowd = document.getElementById('ewl-crowd-chip');

    if (ewlArrival) ewlArrival.textContent = ewl.estimated_arrival;
    if (ewlMeta) ewlMeta.textContent = `Leaves 07:40 • ${ewl.total_duration_min} mins total`;

    if (ewl.delay_minutes > 0) {
      if (ewlArrival) ewlArrival.className = 'text-sm font-bold text-rose-400';
      if (ewlDelay) {
        ewlDelay.className = 'text-[10px] text-rose-400 font-semibold';
        ewlDelay.textContent = `+${ewl.delay_minutes}m Delay (LATE)`;
      }
      if (ewlCrowd) {
        ewlCrowd.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-rose-950 text-rose-300 border border-rose-800';
        ewlCrowd.textContent = 'CROWD: HIGH';
      }
    } else {
      if (ewlArrival) ewlArrival.className = 'text-sm font-bold text-emerald-400';
      if (ewlDelay) {
        ewlDelay.className = 'text-[10px] text-emerald-400';
        ewlDelay.textContent = 'On Time';
      }
      if (ewlCrowd) {
        ewlCrowd.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-950 text-amber-300 border border-amber-800';
        ewlCrowd.textContent = 'CROWD: MOD';
      }
    }

    this.highlightActiveCard(activeRouteId);
  }

  highlightActiveCard(activeRouteId) {
    document.querySelectorAll('.route-card').forEach(card => card.classList.remove('active-route'));
    if (activeRouteId === 'primary_ewl') {
      document.getElementById('card-primary-ewl')?.classList.add('active-route');
    } else if (activeRouteId === 'bypass_dtl') {
      document.getElementById('card-bypass-dtl')?.classList.add('active-route');
    } else if (activeRouteId === 'bypass_bus10e') {
      document.getElementById('card-bypass-bus10e')?.classList.add('active-route');
    }
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

