/**
 * StationBuddy — UI & Interaction Controller.
 * Manages Google Maps style search inputs, arrival timing picker,
 * proactive incident banners, and route options.
 * Owned by: Teammate A (Frontend & Mobile UX)
 */
export class UIController {
  constructor(handlers = {}) {
    this.handlers = handlers; // onSelectRoute, onSwitchScenario, onThresholdChange, onArrivalChange, onLocationChange, onRecenter
    this.defaultRouteCardsHtml = document.getElementById('route-cards-list')?.innerHTML || '';
    this.bindEvents();
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  bindEvents() {
    // Switch to bypass button in proactive detour banner
    document.getElementById('btn-accept-bypass')?.addEventListener('click', () => {
      if (this.handlers.onSelectRoute) this.handlers.onSelectRoute('bypass_dtl');
    });

    // Transit route cards with collapsible step expansion (using delegation on container)
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

    document.getElementById('route-cards-list')?.addEventListener('click', (e) => {
      const card = e.target.closest('.route-card');
      if (!card) return;
      if (card.id === 'card-primary-ewl') {
        toggleRoute('primary_ewl', 'ewl-legs-container', 'ewl-chevron');
      } else if (card.id === 'card-bypass-dtl') {
        toggleRoute('bypass_dtl', 'dtl-legs-container', 'dtl-chevron');
      } else if (card.id === 'card-bypass-bus10e') {
        toggleRoute('bypass_bus10e', 'bus-legs-container', 'bus-chevron');
      } else if (card.id === 'card-arbitrary-route') {
        toggleRoute('arbitrary_route', 'arbitrary-legs-container', 'arbitrary-chevron');
      }
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

    // Bottom sheet minimise / expand toggle
    let sheetMinimised = false;
    document.getElementById('btn-toggle-sheet')?.addEventListener('click', () => {
      const body = document.getElementById('sheet-body');
      const footer = document.getElementById('bottom-sheet');
      const icon = document.getElementById('sheet-toggle-icon');
      if (!body || !footer) return;
      sheetMinimised = !sheetMinimised;
      if (sheetMinimised) {
        body.classList.add('hidden');
        footer.classList.remove('max-h-[24rem]', 'md:max-h-96', 'overflow-y-auto');
        footer.classList.add('max-h-10', 'overflow-hidden');
        if (icon) { icon.className = 'fa-solid fa-chevron-up'; }
      } else {
        body.classList.remove('hidden');
        footer.classList.remove('max-h-10', 'overflow-hidden');
        footer.classList.add('max-h-[24rem]', 'md:max-h-96', 'overflow-y-auto');
        if (icon) { icon.className = 'fa-solid fa-chevron-down'; }
      }
      // Notify map to recalculate its visible size after transition
      setTimeout(() => { window.dispatchEvent(new Event('resize')); }, 320);
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

    // Persona toggle button & drawer buttons (Step A / C)
    const personaToggleBtn = document.getElementById('persona-toggle-btn');
    personaToggleBtn?.addEventListener('click', () => {
      this.openPersonaDrawer();
    });

    // Persona Customizer drawer open / close
    document.getElementById('persona-drawer-close-btn')?.addEventListener('click', () => {
      this.closePersonaDrawer();
    });

    document.getElementById('btn-open-persona-drawer-from-scenarios')?.addEventListener('click', () => {
      document.getElementById('scenario-drawer')?.classList.add('hidden');
      this.openPersonaDrawer();
    });

    document.getElementById('btn-dismiss-custom-error')?.addEventListener('click', () => {
      this.dismissCustomRouteError();
    });

    // Persona dropdown change in customizer
    document.getElementById('persona-select-dropdown')?.addEventListener('change', (e) => {
      if (this.handlers.onSelectPersonaDropdown) {
        this.handlers.onSelectPersonaDropdown(e.target.value);
      }
    });

    // New persona button
    document.getElementById('btn-new-persona')?.addEventListener('click', () => {
      if (this.handlers.onNewPersona) this.handlers.onNewPersona();
    });

    // Submit custom journey calculation
    document.getElementById('btn-submit-custom-route')?.addEventListener('click', () => {
      if (this.handlers.onSubmitCustomRoute) this.handlers.onSubmitCustomRoute();
    });

    // Save persona profile
    document.getElementById('btn-save-persona')?.addEventListener('click', () => {
      if (this.handlers.onSavePersona) this.handlers.onSavePersona();
    });

    // Load saved personas
    document.getElementById('btn-load-persona')?.addEventListener('click', () => {
      if (this.handlers.onLoadPersona) this.handlers.onLoadPersona();
    });

    // Reset to live default commute
    const triggerResetCommute = () => {
      if (this.handlers.onResetStandardCommute) this.handlers.onResetStandardCommute();
    };
    document.getElementById('btn-reset-standard-commute')?.addEventListener('click', triggerResetCommute);
    document.getElementById('btn-reset-standard-commute-bottom')?.addEventListener('click', triggerResetCommute);

    ['rachel', 'arjun', 'mdm_lim'].forEach((pId) => {
      const btn = document.getElementById(`btn-persona-${pId.replace('_', '-')}`);
      btn?.addEventListener('click', () => {
        if (this.handlers.onSelectPersona) this.handlers.onSelectPersona(pId);
        document.getElementById('scenario-drawer')?.classList.add('hidden');
      });
    });
    // Autocomplete dropdowns for search inputs
    this.setupAutocomplete('origin-input', 'origin-suggestions');
    this.setupAutocomplete('dest-input', 'dest-suggestions');
  }

  setupAutocomplete(inputId, dropdownId) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown) return;

    let debounceTimer = null;

    const escapeHtml = (str) => {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    };

    const renderSuggestions = (items) => {
      if (!items || items.length === 0) {
        dropdown.classList.add('hidden');
        dropdown.innerHTML = '';
        return;
      }

      dropdown.innerHTML = items.map((item) => {
        let iconHtml = '<i class="fa-solid fa-location-dot text-blue-400"></i>';
        let badgeColor = 'bg-blue-900/60 text-blue-300 border-blue-800';
        let badgeText = 'Landmark';

        if (item.type === 'postal_code') {
          iconHtml = '<i class="fa-solid fa-envelope-open-text text-amber-400"></i>';
          badgeColor = 'bg-amber-950 text-amber-300 border-amber-800';
          badgeText = 'Postal Code';
        } else if (item.type === 'station') {
          iconHtml = '<i class="fa-solid fa-train-subway text-emerald-400"></i>';
          badgeColor = 'bg-emerald-950 text-emerald-300 border-emerald-800';
          badgeText = 'MRT Station';
        }

        return `
          <div class="px-3 py-2 hover:bg-slate-800 active:bg-slate-700 cursor-pointer flex items-center justify-between gap-2 transition text-left suggestion-item" data-value="${escapeHtml(item.value)}">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-6 h-6 rounded-md bg-slate-800 flex items-center justify-center shrink-0 text-xs">
                ${iconHtml}
              </div>
              <div class="min-w-0">
                <div class="text-xs font-semibold text-slate-100 truncate">${escapeHtml(item.display)}</div>
                <div class="text-[10px] text-slate-400 truncate">Nearest MRT: <span class="text-blue-300 font-medium">${escapeHtml(item.station)}</span></div>
              </div>
            </div>
            <span class="text-[9px] px-1.5 py-0.5 rounded border shrink-0 ${badgeColor}">${badgeText}</span>
          </div>
        `;
      }).join('');

      dropdown.querySelectorAll('.suggestion-item').forEach(el => {
        el.addEventListener('mousedown', (e) => {
          e.preventDefault(); // Prevents blur before click registers
          const val = el.getAttribute('data-value');
          if (val) {
            input.value = val;
            dropdown.classList.add('hidden');
            const originInput = document.getElementById('origin-input');
            const destInput = document.getElementById('dest-input');
            if (this.handlers.onLocationChange && originInput && destInput) {
              this.handlers.onLocationChange(originInput.value, destInput.value);
            }
          }
        });
      });

      dropdown.classList.remove('hidden');
    };

    const fetchSuggestions = async (val) => {
      const q = (val || '').trim();
      if (!q) {
        dropdown.classList.add('hidden');
        dropdown.innerHTML = '';
        return;
      }
      try {
        const resp = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`);
        if (!resp.ok) return;
        const data = await resp.json();
        renderSuggestions(data);
      } catch (err) {
        console.warn('Autocomplete fetch error:', err);
      }
    };

    input.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        fetchSuggestions(e.target.value);
      }, 150);
    });

    input.addEventListener('focus', () => {
      if (input.value.trim().length >= 2) {
        fetchSuggestions(input.value);
      }
    });

    input.addEventListener('blur', () => {
      setTimeout(() => dropdown.classList.add('hidden'), 200);
    });

    input.addEventListener('change', () => {
      const originInput = document.getElementById('origin-input');
      const destInput = document.getElementById('dest-input');
      if (this.handlers.onLocationChange && originInput && destInput) {
        this.handlers.onLocationChange(originInput.value, destInput.value);
      }
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        dropdown.classList.add('hidden');
      } else if (e.key === 'Enter') {
        dropdown.classList.add('hidden');
        const originInput = document.getElementById('origin-input');
        const destInput = document.getElementById('dest-input');
        if (this.handlers.onLocationChange && originInput && destInput) {
          this.handlers.onLocationChange(originInput.value, destInput.value);
        }
      }
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
    const decision = data.decision || {};
    const banner = document.getElementById('proactive-alert-banner') || document.getElementById('alert-banner');
    const alertIcon = document.getElementById('alert-icon');
    const statusLabel = document.getElementById('alert-status-label');
    const headline = document.getElementById('alert-headline');
    const detail = document.getElementById('alert-detail');
    const actionRow = document.getElementById('alert-action-row');
    const weatherChip = document.getElementById('weather-chip');
    const filterBadge = document.getElementById('noise-filter-badge');
    const aiMetaBadge = document.getElementById('ai-meta-badge');
    const pcdForecastBanner = document.getElementById('pcd-forecast-banner');
    const pcdForecastText = document.getElementById('pcd-forecast-text');

    if (filterBadge) filterBadge.textContent = `Noise Filter: <${decision.threshold_minutes || 15}m Silent`;

    // Step D: AI Metadata display (compression ratio and latency)
    if (aiMetaBadge) {
      const aiMeta = decision.ai_metadata || {};
      if (aiMeta.compression_ratio) {
        aiMetaBadge.classList.remove('hidden');
        aiMetaBadge.textContent = `🤖 AI Compressed: ${aiMeta.compression_ratio} | Latency: ${aiMeta.latency_ms || 1.2}ms`;
        aiMetaBadge.title = `Model: ${aiMeta.model || 'Gemini 1.5 Flash'}`;
      } else {
        aiMetaBadge.classList.add('hidden');
      }
    }

    // Step D: Pre-emptive PCD Crowd Forecast Warning
    if (pcdForecastBanner && pcdForecastText) {
      const pcdForecast = data.pcd_forecast || {};
      if (pcdForecast.advice) {
        pcdForecastBanner.classList.remove('hidden');
        pcdForecastText.textContent = pcdForecast.advice;
      } else {
        pcdForecastBanner.classList.add('hidden');
      }
    }

    if (data.weather && weatherChip) {
      const isRain = data.weather.rain_alert;
      weatherChip.innerHTML = isRain
        ? `<i class="fa-solid fa-cloud-showers-heavy text-blue-400"></i><span>${data.weather.origin_forecast}</span>`
        : `<i class="fa-solid fa-sun text-amber-400"></i><span>${data.weather.origin_forecast}</span>`;
    }

    if (headline) headline.textContent = decision.headline || 'All trains operating normally.';
    if (detail) detail.textContent = decision.one_line_advice || decision.headline || 'On schedule.';

    if (banner && alertIcon && statusLabel) {
      if (decision.urgency === 'CALM') {
        banner.className = 'pointer-events-auto rounded-2xl p-3 border shadow-2xl transition-all duration-300 bg-emerald-950/90 border-emerald-700/80 backdrop-blur-md w-full md:w-80 lg:w-96 shrink-0';
        alertIcon.className = 'w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px]';
        alertIcon.innerHTML = '<i class="fa-solid fa-check"></i>';
        statusLabel.className = 'text-[11px] font-bold uppercase tracking-wider text-emerald-400';
        statusLabel.textContent = 'On Schedule';
        if (actionRow) actionRow.classList.add('hidden');
      } else {
        banner.className = 'pointer-events-auto rounded-2xl p-3 border shadow-2xl transition-all duration-300 bg-rose-950/90 border-rose-600/90 ring-1 ring-rose-500/40 backdrop-blur-md w-full md:w-80 lg:w-96 shrink-0';
        alertIcon.className = 'w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center text-[10px]';
        alertIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation animate-bounce"></i>';
        statusLabel.className = 'text-[11px] font-bold uppercase tracking-wider text-rose-400';
        statusLabel.textContent = 'Detour Recommendation';
        if (actionRow) actionRow.classList.remove('hidden');
      }
    }
  }

  updatePersonaDisplay(data) {
    const pId = (data.persona_id || 'rachel').toLowerCase();
    const label = document.getElementById('active-persona-label');
    const display = document.getElementById('persona-name-display');
    const nameStr = data.profile && data.profile.name 
      ? `${data.profile.name} (${data.profile.tag || data.profile.persona || 'Active'})`
      : (pId === 'arjun' ? 'Arjun (Cycle/CCL)' : pId === 'mdm_lim' ? 'Mdm Lim (Step-Free)' : 'Rachel (EWL)');
    if (label) label.textContent = nameStr;
    if (display) display.textContent = nameStr;

    ['rachel', 'arjun', 'mdm_lim'].forEach((id) => {
      const btn = document.getElementById(`btn-persona-${id.replace('_', '-')}`);
      if (btn) {
        if (id === pId) {
          btn.className = 'persona-btn p-2 rounded-lg border bg-indigo-950/80 border-indigo-500 text-white text-left flex flex-col transition ring-1 ring-indigo-400/50';
        } else {
          btn.className = 'persona-btn p-2 rounded-lg border bg-slate-800/60 border-slate-700 text-slate-300 text-left flex flex-col transition hover:text-white';
        }
      }
    });

    const selectDropdown = document.getElementById('persona-select-dropdown');
    if (selectDropdown && data.persona_id) {
      selectDropdown.value = data.persona_id;
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
    const ewl = routes.primary_ewl;
    const container = document.getElementById('route-cards-list');

    // Default Corridor Mode: Restore 3 alternative routes if needed
    if (container && this.defaultRouteCardsHtml && !document.getElementById('card-bypass-dtl')) {
      container.innerHTML = this.defaultRouteCardsHtml;
    }

    const ewlIcon = document.getElementById('ewl-icon');
    const dtlCard = document.getElementById('card-bypass-dtl');
    const busCard = document.getElementById('card-bypass-bus10e');

    // 0. Custom Commuter Route Card (Persona Builder Mode)
    if (routes.primary_custom && !data.is_custom) {
      const custom = routes.primary_custom;
      const titleEl = document.getElementById('ewl-route-name');
      if (titleEl) titleEl.textContent = custom.title || 'Custom Commuter Route';

      const arrivalEl = document.getElementById('ewl-arrival-time');
      if (arrivalEl) {
        arrivalEl.className = 'text-sm font-bold text-indigo-400';
        arrivalEl.textContent = custom.estimated_arrival;
      }

      const metaEl = document.getElementById('ewl-route-meta');
      const depTime = data.profile?.departure_time || '08:00 AM';
      const shelter = custom.sheltered_percent ? ` • ${custom.sheltered_percent}% covered` : '';
      if (metaEl) metaEl.textContent = `Leaves ${depTime} • ${custom.total_duration_min} mins total${shelter}`;

      if (ewlIcon) {
        if (custom.cycling_enabled) {
          ewlIcon.className = 'fa-solid fa-bicycle text-emerald-400';
        } else if (custom.step_free_certified) {
          ewlIcon.className = 'fa-solid fa-wheelchair text-blue-400';
        } else {
          ewlIcon.className = 'fa-solid fa-route text-indigo-400';
        }
      }

      const exitChip = document.getElementById('ewl-exit-chip');
      if (exitChip) {
        if (custom.step_free_certified) {
          exitChip.innerHTML = `<i class="fa-solid fa-elevator text-[8px]"></i> STEP-FREE`;
        } else if (custom.cycling_enabled) {
          exitChip.innerHTML = `<i class="fa-solid fa-bicycle text-[8px]"></i> CYCLE`;
        } else {
          exitChip.innerHTML = `<i class="fa-solid fa-sliders text-[8px]"></i> CUSTOM`;
        }
      }

      const shelterChip = document.getElementById('ewl-shelter-chip');
      if (shelterChip) {
        if (custom.step_free_certified) {
          shelterChip.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-0.5';
          shelterChip.textContent = `🛡️ 100% STEP-FREE`;
        } else if (custom.accessibility_status === 'unverified' && (data.profile?.requires_step_free || data.profile?.stair_aversion)) {
          shelterChip.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-0.5';
          shelterChip.textContent = `⚠️ ACCESSIBILITY UNVERIFIED`;
        } else {
          shelterChip.className = 'px-1.5 py-0.2 text-[9px] font-bold rounded bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-0.5';
          shelterChip.textContent = `🛡️ ${custom.sheltered_percent || 80}% SHELTER`;
        }
      }

      const crowdChip = document.getElementById('ewl-crowd-chip');
      this.renderCrowdChip(crowdChip, custom.crowd_level || 'm');

      const delayEl = document.getElementById('ewl-delay-tag');
      if (delayEl) {
        if (custom.warnings && custom.warnings.length > 0) {
          delayEl.className = 'text-[10px] text-amber-400 font-semibold';
          delayEl.textContent = 'Advisory Notice';
        } else {
          delayEl.className = 'text-[10px] text-emerald-400 font-semibold';
          delayEl.textContent = 'Constraint Verified';
        }
      }

      const exitStationName = data.profile?.alighting_station ? `${data.profile.alighting_station} MRT` : 'Destination MRT';
      const exitNoteText = custom.warnings && custom.warnings.length > 0
        ? custom.warnings.join(' • ')
        : (custom.step_free_certified ? 'Certified step-free path to destination' : 'Verified path via multimodal network');

      this.renderRouteLegs('ewl-legs-container', custom.legs, 'indigo', {
        exitStation: exitStationName,
        exitDoor: 'Exit B',
        exitNote: exitNoteText,
        shelterPercent: custom.sheltered_percent || 80
      });

      if (dtlCard) dtlCard.classList.add('hidden');
      if (busCard) busCard.classList.add('hidden');

    // 1. Primary Route Card (Persona-Specific Routing)
    } else if (routes.primary_arjun) {
      // Render Arjun's multimodal cycling card
      const arjun = routes.primary_arjun;
      const titleEl = document.getElementById('ewl-route-name');
      if (titleEl) titleEl.textContent = arjun.title || 'Cycle + NEL/CCL Train';
      const arrivalEl = document.getElementById('ewl-arrival-time');
      if (arrivalEl) {
        arrivalEl.className = 'text-sm font-bold text-emerald-400';
        arrivalEl.textContent = arjun.estimated_arrival;
      }
      const metaEl = document.getElementById('ewl-route-meta');
      if (metaEl) metaEl.textContent = `${arjun.total_duration_min} mins total • ${arjun.status}`;

      if (ewlIcon) ewlIcon.className = 'fa-solid fa-bicycle text-emerald-400';

      const exitChip = document.getElementById('ewl-exit-chip');
      if (exitChip) exitChip.innerHTML = `<i class="fa-solid fa-bicycle text-[8px]"></i> CYCLE 4M`;
      const shelterChip = document.getElementById('ewl-shelter-chip');
      if (shelterChip) shelterChip.textContent = `🚲 ${arjun.sheltered_percent || 40}% SHELTER`;
      const crowdChip = document.getElementById('ewl-crowd-chip');
      this.renderCrowdChip(crowdChip, arjun.crowd_level || 'l');

      const delayEl = document.getElementById('ewl-delay-tag');
      if (delayEl) {
        delayEl.className = 'text-[10px] text-emerald-400 font-semibold';
        delayEl.textContent = arjun.rain_active ? 'Rain Adapted' : 'Optimal Cycle Link';
      }

      this.renderRouteLegs('ewl-legs-container', arjun.legs, 'emerald', {
        exitStation: 'one-north (CC23)',
        exitDoor: 'Exit B',
        exitNote: 'Direct cycling link to Galaxis / Fusionopolis lobby',
        shelterPercent: arjun.sheltered_percent || 40
      });

      // Hide Rachel's corridor bypasses for Arjun's direct transit corridor
      if (dtlCard) dtlCard.classList.add('hidden');
      if (busCard) busCard.classList.add('hidden');

    } else if (routes.primary_mdm_lim) {
      // Render Mdm Lim's step-free accessibility card
      const lim = routes.primary_mdm_lim;
      const titleEl = document.getElementById('ewl-route-name');
      if (titleEl) titleEl.textContent = lim.title || 'East-West Line (Step-Free Direct to SGH)';
      const arrivalEl = document.getElementById('ewl-arrival-time');
      if (arrivalEl) {
        arrivalEl.className = 'text-sm font-bold text-blue-400';
        arrivalEl.textContent = lim.estimated_arrival;
      }
      const metaEl = document.getElementById('ewl-route-meta');
      if (metaEl) metaEl.textContent = `${lim.total_duration_min} mins total • ${lim.status}`;

      if (ewlIcon) ewlIcon.className = 'fa-solid fa-wheelchair text-blue-400';

      const exitChip = document.getElementById('ewl-exit-chip');
      if (exitChip) exitChip.innerHTML = `<i class="fa-solid fa-elevator text-[8px]"></i> LIFT ACCESS`;
      const shelterChip = document.getElementById('ewl-shelter-chip');
      if (shelterChip) shelterChip.textContent = `🛡️ 100% STEP-FREE`;
      const crowdChip = document.getElementById('ewl-crowd-chip');
      this.renderCrowdChip(crowdChip, lim.crowd_level || 'l');

      const delayEl = document.getElementById('ewl-delay-tag');
      if (delayEl) {
        delayEl.className = 'text-[10px] text-blue-400 font-semibold';
        delayEl.textContent = lim.has_lift_alert ? 'Lift Advisory' : '100% Barrier-Free';
      }

      this.renderRouteLegs('ewl-legs-container', lim.legs, 'blue', {
        exitStation: 'Outram Park (EW16/NE3/TE17)',
        exitDoor: 'Lift Gantry A',
        exitNote: 'Barrier-free ramp and lift linkway directly to clinic concourse',
        shelterPercent: lim.sheltered_percent || 95
      });

      // Hide Rachel's corridor bypasses for Mdm Lim's accessibility corridor
      if (dtlCard) dtlCard.classList.add('hidden');
      if (busCard) busCard.classList.add('hidden');

    } else if (routes.primary_ewl) {
      // Rachel (Default Corporate Commuter corridor)
      const ewl = routes.primary_ewl;
      const titleEl = document.getElementById('ewl-route-name');
      if (titleEl) titleEl.textContent = ewl.title || 'East-West Line (Direct)';

      if (ewlIcon) ewlIcon.className = 'fa-solid fa-train text-emerald-400';

      const ewlArrival = document.getElementById('ewl-arrival-time');
      const ewlDelay = document.getElementById('ewl-delay-tag');
      const ewlMeta = document.getElementById('ewl-route-meta');
      const ewlCrowd = document.getElementById('ewl-crowd-chip');

      if (ewlArrival) ewlArrival.textContent = ewl.estimated_arrival;
      const depTime = data.profile?.departure_time || '07:40 AM';
      const ewlShelter = ewl.sheltered_percent ? ` (${ewl.sheltered_percent}% covered)` : '';
      if (ewlMeta) {
        if (data.is_custom) {
          ewlMeta.textContent = `${ewl.status || 'Optimal Transit Path'} • ${ewl.total_duration_min} mins total${ewlShelter}`;
        } else {
          ewlMeta.textContent = `Leaves ${depTime} • ${ewl.total_duration_min} mins total${ewlShelter}`;
        }
      }

      const ewlShelterChip = document.getElementById('ewl-shelter-chip');
      if (ewlShelterChip && ewl.sheltered_percent) {
        ewlShelterChip.textContent = `🛡️ ${ewl.sheltered_percent}% SHELTER`;
      }
      const exitChip = document.getElementById('ewl-exit-chip');
      if (exitChip) {
        if (data.is_custom) {
          exitChip.innerHTML = `<i class="fa-solid fa-flag-checkered text-[8px]"></i> TO DEST`;
        } else {
          exitChip.innerHTML = `<i class="fa-solid fa-door-open text-[8px]"></i> EXIT B`;
        }
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
          ewlDelay.textContent = data.is_custom ? 'Primary Route' : 'On Time';
        }
        this.renderCrowdChip(ewlCrowd, ewl.crowd_level || 'm');
      }

      const exitDestName = data.map_layers?.destination?.name || 'Destination';
      this.renderRouteLegs('ewl-legs-container', ewl.legs, 'emerald', {
        exitStation: data.is_custom ? exitDestName : 'Raffles Place (EW14)',
        exitDoor: 'Exit B',
        exitNote: data.is_custom ? 'Follow turn-by-turn pedestrian and transit guidance' : 'Direct underground linkway to One Raffles Place basement',
        shelterPercent: ewl.sheltered_percent || 80
      });

      // 2. Downtown Line Bypass / Dynamic Alternative Card
      const dtl = routes.bypass_dtl;
      if (dtl && dtlCard) {
        dtlCard.classList.remove('hidden');
        const dtlTitle = document.getElementById('dtl-route-name');
        if (dtlTitle) dtlTitle.textContent = dtl.title || 'Alternative Route';

        const dtlArrival = document.getElementById('dtl-arrival-time');
        const dtlDelay = document.getElementById('dtl-delay-tag');
        const dtlMeta = document.getElementById('dtl-route-meta');
        const dtlCrowd = document.getElementById('dtl-crowd-chip');

        if (dtlArrival) dtlArrival.textContent = dtl.estimated_arrival;
        const dtlShelter = dtl.sheltered_percent ? ` (${dtl.sheltered_percent}% covered)` : '';
        if (dtlMeta) {
          if (data.is_custom) {
            dtlMeta.textContent = `${dtl.status || 'Alternative Transit Path'} • ${dtl.total_duration_min} mins${dtlShelter}`;
          } else {
            dtlMeta.textContent = `Tampines DTL → Telok Ayer • ${dtl.total_duration_min} mins${dtlShelter}`;
          }
        }

        const dtlShelterChip = document.getElementById('dtl-shelter-chip');
        if (dtlShelterChip && dtl.sheltered_percent) {
          dtlShelterChip.textContent = `🛡️ ${dtl.sheltered_percent}% SHELTER`;
        }

        const dtlExitChip = document.getElementById('dtl-exit-chip');
        if (dtlExitChip) {
          if (data.is_custom) {
            dtlExitChip.innerHTML = `<i class="fa-solid fa-flag-checkered text-[8px]"></i> TO DEST`;
          } else {
            dtlExitChip.innerHTML = `<i class="fa-solid fa-door-open text-[8px]"></i> EXIT B`;
          }
        }

        if (dtlDelay) {
          if (dtl.is_recommended) {
            dtlDelay.className = 'text-[10px] text-blue-400 font-semibold';
            dtlDelay.textContent = '★ Recommended Bypass';
          } else {
            dtlDelay.className = 'text-[10px] text-slate-400';
            dtlDelay.textContent = data.is_custom ? 'Alternative Option' : 'Reliable Alternative';
          }
        }
        this.renderCrowdChip(dtlCrowd, dtl.crowd_level || 'l');

        this.renderRouteLegs('dtl-legs-container', dtl.legs, 'blue', {
          exitStation: data.is_custom ? exitDestName : 'Telok Ayer (DT18)',
          exitDoor: data.is_custom ? 'Doorstep / Alighting' : 'Exit B',
          exitNote: data.is_custom ? 'Alternative transit path to destination' : 'Sheltered linkway via Cross St & Church St to desk',
          shelterPercent: dtl.sheltered_percent || 95
        });
      } else if (dtlCard) {
        dtlCard.classList.add('hidden');
      }

      // 3. Express Bus 10e / Public Bus Service Card
      const bus = routes.bypass_bus10e;
      if (bus && busCard) {
        busCard.classList.remove('hidden');
        const busName = document.getElementById('bus-route-name');
        if (busName) busName.textContent = bus.title || 'Public Bus Service';

        const busArrival = document.getElementById('bus-arrival-time');
        const busDelay = document.getElementById('bus-delay-tag');
        const busMeta = document.getElementById('bus-route-meta');
        const busCrowd = document.getElementById('bus-crowd-chip');

        if (busArrival) busArrival.textContent = bus.estimated_arrival;
        if (busMeta) {
          if (data.is_custom) {
            busMeta.textContent = `${bus.status || 'Public Bus Connection'} • ${bus.total_duration_min} mins`;
          } else {
            busMeta.textContent = `Expressway via ECP to CBD • ${bus.total_duration_min} mins`;
          }
        }

        const busShelterChip = document.getElementById('bus-shelter-chip');
        if (busShelterChip && bus.sheltered_percent) {
          busShelterChip.textContent = `☂️ ${bus.sheltered_percent}% SHELTER`;
        }

        const busExitChip = document.getElementById('bus-exit-chip');
        if (busExitChip) {
          if (data.is_custom) {
            busExitChip.innerHTML = `<i class="fa-solid fa-flag-checkered text-[8px]"></i> TO DEST`;
          } else {
            busExitChip.innerHTML = `<i class="fa-solid fa-bus text-[8px]"></i> STOP 03011`;
          }
        }

        // Color-coded crowd badge: SEA/l -> Green, SDA/m -> Yellow, LSD/h -> Red
        this.renderBusCrowdBadge(busCrowd, bus);

        if (busDelay) {
          const isLive = bus.bus_load_source === 'live';
          busDelay.className = isLive ? 'text-[10px] text-emerald-400 font-semibold flex items-center justify-end gap-1' : 'text-[10px] text-slate-400';
          busDelay.innerHTML = isLive
            ? `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Live LTA Load`
            : (bus.status || (data.is_custom ? 'Public Bus' : 'Guaranteed Seat'));
        }

        this.renderRouteLegs('bus-legs-container', bus.legs, 'purple', {
          exitStation: data.is_custom ? exitDestName : 'Fullerton Sq Stop (03011)',
          exitDoor: data.is_custom ? 'Doorstep / Alighting' : 'Bus Stop',
          exitNote: data.is_custom ? 'Surface bus connection to destination' : 'Walk via Battery Rd to One Raffles Place',
          shelterPercent: bus.sheltered_percent || 60
        });
      } else if (busCard) {
        busCard.classList.add('hidden');
      }
    }

    this.highlightActiveCard(activeRouteId);
  }

  renderCustomRouteSteps(ewl) {
    const container = document.getElementById('route-cards-list');
    if (!container || !ewl) return;

    const legs = ewl.legs || [];
    const lineStyles = {
      'NEL': { badge: 'bg-purple-950 text-purple-300 border-purple-800', iconBg: 'bg-purple-600/20 text-purple-400 border-purple-500/40' },
      'CCL': { badge: 'bg-amber-950 text-amber-300 border-amber-800', iconBg: 'bg-amber-600/20 text-amber-400 border-amber-500/40' },
      'NSL': { badge: 'bg-rose-950 text-rose-300 border-rose-800', iconBg: 'bg-red-600/20 text-red-400 border-red-500/40' },
      'EWL': { badge: 'bg-emerald-950 text-emerald-300 border-emerald-800', iconBg: 'bg-emerald-600/20 text-emerald-400 border-emerald-500/40' },
      'DTL': { badge: 'bg-blue-950 text-blue-300 border-blue-800', iconBg: 'bg-blue-600/20 text-blue-400 border-blue-500/40' },
      'TEL': { badge: 'bg-yellow-950 text-yellow-300 border-yellow-800', iconBg: 'bg-yellow-600/20 text-yellow-400 border-yellow-500/40' },
    };

    let html = `
      <!-- Overall Route Summary Card -->
      <div id="card-primary-ewl" class="route-card p-2.5 rounded-xl border bg-slate-800/90 border-blue-500/60 shadow-lg flex items-center justify-between transition cursor-pointer active-route">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/40 flex items-center justify-center font-bold text-xs shrink-0">
            <i class="fa-solid fa-diamond-turn-right"></i>
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="font-semibold text-xs text-white truncate">${this.escapeHtml(ewl.title || 'Custom Route')}</span>
              <span class="px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-950 text-amber-300 border border-amber-800">CROWD: MOD</span>
            </div>
            <p class="text-[11px] text-slate-400 truncate">${this.escapeHtml(ewl.status || '')} • ${ewl.total_duration_min} mins total</p>
          </div>
        </div>
        <div class="text-right shrink-0 ml-2">
          <div class="text-sm font-bold text-emerald-400">${ewl.estimated_arrival}</div>
          <div class="text-[10px] text-emerald-400 font-medium">On Time</div>
        </div>
      </div>

      <!-- Step-by-Step Directions Header -->
      <div class="flex items-center justify-between px-1 pt-1.5 pb-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-t border-slate-800/60">
        <span><i class="fa-solid fa-list-ol mr-1 text-blue-400"></i> Step-by-Step Directions (${legs.length} Steps)</span>
        <span class="text-slate-500 font-normal lowercase">${ewl.total_duration_min} mins total</span>
      </div>
    `;

    legs.forEach((leg, idx) => {
      const stepNum = idx + 1;
      if (leg.mode === 'TRAIN') {
        const line = leg.line || 'MRT';
        const style = lineStyles[line] || { badge: 'bg-blue-950 text-blue-300 border-blue-800', iconBg: 'bg-blue-600/20 text-blue-400 border-blue-500/40' };
        const stopsCount = leg.stops || 1;
        const stopsText = `${stopsCount} ${stopsCount === 1 ? 'stop' : 'stops'}`;
        const stationsPath = leg.stations && leg.stations.length > 0 
          ? `<div class="text-[10px] text-slate-400 mt-0.5 truncate"><i class="fa-solid fa-angles-right text-[8px] text-slate-500 mr-1"></i>${leg.stations.map(s => this.escapeHtml(s)).join(' ➔ ')}</div>`
          : '';

        html += `
          <div class="p-2.5 rounded-xl border bg-slate-800/60 border-slate-700/80 flex items-center justify-between transition hover:border-slate-600">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 rounded-lg ${style.iconBg} flex items-center justify-center font-bold text-xs shrink-0">
                <i class="fa-solid fa-train-subway"></i>
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="font-semibold text-xs text-white">Step ${stepNum}: Take ${this.escapeHtml(leg.line_name || `${line} Line`)}</span>
                  <span class="px-1.5 py-0.2 text-[9px] font-bold rounded border ${style.badge}">${line} (${stopsText.toUpperCase()})</span>
                </div>
                <p class="text-[11px] text-slate-300 truncate">${this.escapeHtml(leg.name)} • <strong>${stopsText}</strong></p>
                ${stationsPath}
              </div>
            </div>
            <div class="text-right shrink-0 ml-2">
              <div class="text-xs font-bold text-blue-300">${leg.duration}</div>
              <div class="text-[10px] text-slate-400">${stopsText}</div>
            </div>
          </div>
        `;
      } else if (leg.mode === 'BUS') {
        html += `
          <div class="p-2.5 rounded-xl border bg-slate-800/60 border-slate-700/80 flex items-center justify-between transition hover:border-slate-600">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 rounded-lg bg-teal-600/20 text-teal-400 border border-teal-500/40 flex items-center justify-center font-bold text-xs shrink-0">
                <i class="fa-solid fa-bus"></i>
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="font-semibold text-xs text-white">Step ${stepNum}: Feeder Bus</span>
                  <span class="px-1.5 py-0.2 text-[9px] font-bold rounded bg-teal-950 text-teal-300 border border-teal-800">FEEDER BUS</span>
                </div>
                <p class="text-[11px] text-slate-300 truncate">${this.escapeHtml(leg.name)}${leg.distance ? ` (${leg.distance})` : ''}</p>
              </div>
            </div>
            <div class="text-right shrink-0 ml-2">
              <div class="text-xs font-bold text-teal-300">${leg.duration}</div>
              <div class="text-[10px] text-slate-400">Frequent Service</div>
            </div>
          </div>
        `;
      } else {
        // WALK
        let badgeText = 'WALK';
        let badgeColor = 'bg-slate-800 text-slate-300 border-slate-700';
        let iconBg = 'bg-sky-600/20 text-sky-400 border-sky-500/40';
        let subText = leg.sheltered_percent ? `${leg.sheltered_percent}% sheltered` : 'Doorstep';

        if (leg.is_first_mile) {
          badgeText = 'FIRST MILE';
          badgeColor = 'bg-sky-950 text-sky-300 border-sky-800';
        } else if (leg.is_last_mile) {
          badgeText = 'LAST MILE';
          badgeColor = 'bg-emerald-950 text-emerald-300 border-emerald-800';
          iconBg = 'bg-emerald-600/20 text-emerald-400 border-emerald-500/40';
          subText = 'Destination Doorstep';
        } else if (leg.is_transfer) {
          badgeText = 'INTERCHANGE';
          badgeColor = 'bg-indigo-950 text-indigo-300 border-indigo-800';
          iconBg = 'bg-indigo-600/20 text-indigo-400 border-indigo-500/40';
          subText = 'Sheltered Linkway';
        }

        html += `
          <div class="p-2.5 rounded-xl border bg-slate-800/60 border-slate-700/80 flex items-center justify-between transition hover:border-slate-600">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center font-bold text-xs shrink-0">
                <i class="fa-solid fa-person-walking"></i>
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="font-semibold text-xs text-white">Step ${stepNum}: ${leg.is_transfer ? 'Interchange Transfer' : 'Walk'}</span>
                  <span class="px-1.5 py-0.2 text-[9px] font-bold rounded border ${badgeColor}">${badgeText}</span>
                </div>
                <p class="text-[11px] text-slate-300 truncate">${this.escapeHtml(leg.name)}${leg.distance ? ` (${leg.distance})` : ''}</p>
              </div>
            </div>
            <div class="text-right shrink-0 ml-2">
              <div class="text-xs font-bold text-slate-200">${leg.duration}</div>
              <div class="text-[10px] text-slate-400">${subText}</div>
            </div>
          </div>
        `;
      }
    });

    container.innerHTML = html;
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
        badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[9px] font-mono">${leg.stops ? `${leg.stops} stops` : (leg.line || 'MRT Line')}</span>`;
      } else if (leg.mode === 'BUS') {
        modeIcon = 'fa-bus';
        iconColor = 'text-purple-400';
        badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-purple-950/80 text-purple-300 border border-purple-800 text-[9px] font-mono">${leg.stops ? `${leg.stops} stops` : (leg.line || 'Public Bus')}</span>`;
      } else if (leg.mode === 'CYCLE') {
        modeIcon = 'fa-bicycle';
        iconColor = 'text-emerald-400';
        badgeHtml = `<span class="px-1.5 py-0.2 rounded bg-emerald-950/90 text-emerald-300 border border-emerald-800 text-[9px] font-semibold flex items-center gap-1">🚲 Park Connector Link</span>`;
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

    // Interchange transfer: Serangoon (NEL <-> CCL)
    if (nameLower.includes('serangoon')) {
      return {
        landmark: 'Internal Underground Transfer Concourse',
        shelter: '🛡️ 100% Sheltered & Air-Conditioned',
        steps: [
          'Alight from NEL train & follow overhead <strong>yellow Circle Line signs</strong>.',
          'Take the transfer escalator up to the intermediate concourse level (120m).',
          'Descend the connecting escalator directly to <strong>Circle Line Platform A/B</strong> (4 min transfer).'
        ]
      };
    }

    // Destination walk: one-north / Biopolis Desk
    if (nameLower.includes('one-north') || nameLower.includes('biopolis')) {
      return {
        landmark: 'Exit A Covered Linkway to Biopolis',
        shelter: '🛡️ 95% Covered Linkway',
        steps: [
          'Alight from CCL train & take escalator to Concourse level.',
          'Tap out at fare gates and take <strong>Exit A</strong> towards Biopolis / Fusionopolis.',
          'Follow the covered pedestrian linkway past Galaxis directly to the lobby entrance (350m, 4 min).'
        ]
      };
    }

    // Step-free destination walk: SGH / Outram Park
    if (nameLower.includes('sgh') || (nameLower.includes('outram') && (nameLower.includes('exit') || nameLower.includes('ramp')))) {
      return {
        landmark: 'Barrier-Free Hospital Linkway',
        shelter: '🛡️ 100% Barrier-Free & Sheltered',
        steps: [
          'Alight at Outram Park platform & take the priority lift up to Concourse level.',
          'Tap out at the accessible wide gantry following signs for <strong>Exit F / SGH Medical Centre</strong>.',
          'Proceed through the step-free lift linkway directly into the SGH hospital lobby without steps or curbs.'
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

  openPersonaDrawer() {
    const drawer = document.getElementById('persona-drawer');
    drawer?.classList.remove('hidden');
  }

  closePersonaDrawer() {
    const drawer = document.getElementById('persona-drawer');
    drawer?.classList.add('hidden');
  }

  populatePersonaDropdown(personas = [], activeId = 'rachel') {
    const dropdown = document.getElementById('persona-select-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = '';

    personas.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p.id;
      const originStn = p.boarding_station || p.origin || 'MRT';
      const destStn = p.alighting_station || p.destination || 'MRT';
      opt.textContent = `${p.name} — ${p.tag || p.persona || 'Profile'} (${originStn} → ${destStn})`;
      if (p.id === activeId) opt.selected = true;
      dropdown.appendChild(opt);
    });
  }

  fillPersonaForm(profile = {}) {
    if (!profile) return;
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val !== undefined && val !== null ? val : '';
    };
    const setChecked = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.checked = Boolean(val);
    };

    setVal('pref-name', profile.name || '');
    setVal('pref-tag', profile.tag || '');
    setVal('pref-walking-speed', profile.walking_speed_mps || 1.35);
    setVal('pref-cycling-speed', profile.cycling_speed_mps || 4.0);
    setVal('pref-max-walk-m', profile.max_walking_distance_m !== null && profile.max_walking_distance_m !== undefined ? profile.max_walking_distance_m : '');
    setVal('pref-max-transfers', profile.max_transfers !== null && profile.max_transfers !== undefined ? profile.max_transfers : '');
    setVal('pref-crowd-tolerance', profile.crowd_tolerance || 'normal');
    setVal('pref-crowd-advance-lead', profile.crowd_advance_lead_min || 10);
    setVal('pref-delay-threshold', profile.delay_threshold_min || 15);

    setChecked('pref-requires-step-free', profile.requires_step_free);
    setChecked('pref-requires-lift-monitoring', profile.requires_lift_monitoring);
    setChecked('pref-stair-aversion', profile.stair_aversion);
    setChecked('pref-cycling-enabled', profile.cycling_enabled);
    setChecked('pref-avoid-cycling-rain', profile.avoid_cycling_in_rain !== false);
  }

  readPersonaForm() {
    const getVal = (id) => document.getElementById(id)?.value?.trim() || '';
    const getChecked = (id) => Boolean(document.getElementById(id)?.checked);
    const getNum = (id) => {
      const val = document.getElementById(id)?.value?.trim();
      return val ? parseFloat(val) : null;
    };

    const maxWalk = getNum('pref-max-walk-m');
    const maxTransfers = getNum('pref-max-transfers');

    return {
      name: getVal('pref-name') || 'Custom Commuter',
      tag: getVal('pref-tag') || 'Custom Route',
      walking_speed_mps: getNum('pref-walking-speed') || 1.35,
      cycling_speed_mps: getNum('pref-cycling-speed') || 4.0,
      max_walking_distance_m: maxWalk !== null && !isNaN(maxWalk) ? maxWalk : null,
      max_transfers: maxTransfers !== null && !isNaN(maxTransfers) ? Math.round(maxTransfers) : null,
      requires_step_free: getChecked('pref-requires-step-free'),
      requires_lift_monitoring: getChecked('pref-requires-lift-monitoring'),
      stair_aversion: getChecked('pref-stair-aversion'),
      cycling_enabled: getChecked('pref-cycling-enabled'),
      avoid_cycling_in_rain: getChecked('pref-avoid-cycling-rain'),
      crowd_tolerance: getVal('pref-crowd-tolerance') || 'normal',
      crowd_advance_lead_min: Math.round(getNum('pref-crowd-advance-lead') || 10),
      delay_threshold_min: Math.round(getNum('pref-delay-threshold') || 15),
      rain_active: getChecked('pref-rain-active')
    };
  }

  renderCustomRouteError(errorData = {}) {
    const banner = document.getElementById('custom-error-banner');
    const title = document.getElementById('custom-error-title');
    const msg = document.getElementById('custom-error-message');
    const violations = document.getElementById('custom-error-violations');
    const icon = document.getElementById('custom-error-icon');
    if (!banner || !title || !msg) return;

    banner.classList.remove('hidden');
    const code = errorData.code || 'ROUTING_ERROR';

    if (code === 'UNKNOWN_STATION') {
      banner.className = 'p-2.5 rounded-xl border bg-rose-950/90 border-rose-600/90 text-xs leading-snug flex items-start gap-2 shadow-lg transition-all text-rose-200';
      if (icon) icon.innerHTML = '<i class="fa-solid fa-circle-xmark text-rose-400"></i>';
      title.textContent = 'Unknown Station Location';
      msg.textContent = errorData.message || 'One or more stations could not be resolved to a known Singapore MRT station. Please check station spelling (e.g., "Tampines", "Raffles Place", "Jurong East").';
      if (violations) violations.classList.add('hidden');
    } else if (code === 'NO_FEASIBLE_ROUTE') {
      banner.className = 'p-2.5 rounded-xl border bg-amber-950/90 border-amber-600/90 text-xs leading-snug flex items-start gap-2 shadow-lg transition-all text-amber-200';
      if (icon) icon.innerHTML = '<i class="fa-solid fa-triangle-exclamation text-amber-400"></i>';
      title.textContent = 'Constraint Conflict — No Feasible Route';
      msg.textContent = errorData.message || 'Transit paths exist between your stations, but none satisfy your strict profile limits.';
      
      if (violations && errorData.candidate_routes && errorData.candidate_routes.length > 0) {
        const violationList = [];
        errorData.candidate_routes.forEach((cand, idx) => {
          if (cand.constraint_violations && cand.constraint_violations.length > 0) {
            violationList.push(`• Option ${idx + 1} (${cand.title}): ${cand.constraint_violations.join(', ')}`);
          }
        });
        if (violationList.length > 0) {
          violations.classList.remove('hidden');
          violations.innerHTML = `<div class="mt-1 text-amber-300 font-semibold">Violations detected:</div>${violationList.join('<br>')}<div class="mt-1 text-slate-300 text-[10px]">Tip: Try relaxing max transfers or walking distance limits.</div>`;
        } else {
          violations.classList.add('hidden');
        }
      } else if (violations) {
        violations.classList.add('hidden');
      }
    } else if (code === 'NO_ROUTE') {
      banner.className = 'p-2.5 rounded-xl border bg-rose-950/90 border-rose-600/90 text-xs leading-snug flex items-start gap-2 shadow-lg transition-all text-rose-200';
      if (icon) icon.innerHTML = '<i class="fa-solid fa-circle-xmark text-rose-400"></i>';
      title.textContent = 'No Transit Route Found';
      msg.textContent = errorData.message || 'Could not find a connected transit path between the specified origin and destination.';
      if (violations) violations.classList.add('hidden');
    } else {
      banner.className = 'p-2.5 rounded-xl border bg-rose-950/90 border-rose-600/90 text-xs leading-snug flex items-start gap-2 shadow-lg transition-all text-rose-200';
      if (icon) icon.innerHTML = '<i class="fa-solid fa-circle-exclamation text-rose-400"></i>';
      title.textContent = 'Custom Route Request Failed';
      msg.textContent = errorData.message || 'An unexpected error occurred while calculating your custom route.';
      if (violations) violations.classList.add('hidden');
    }
  }

  dismissCustomRouteError() {
    const banner = document.getElementById('custom-error-banner');
    if (banner) banner.classList.add('hidden');
  }

  showPersonaSaveStatus(message, isError = false) {
    const status = document.getElementById('persona-save-status');
    if (!status) return;
    status.className = isError ? 'text-[10px] text-rose-400 font-medium' : 'text-[10px] text-emerald-400 font-medium';
    status.textContent = message;
    setTimeout(() => {
      if (status.textContent === message) status.textContent = '';
    }, 4000);
  }

  setCustomJourneyActive(isActive, profileName = 'Custom Commuter', summary = '') {
    const banner = document.getElementById('custom-journey-active-banner');
    const nameLabel = document.getElementById('custom-journey-name-label');
    const summaryLabel = document.getElementById('custom-journey-summary-label');
    if (!banner) return;

    if (isActive) {
      banner.classList.remove('hidden');
      if (nameLabel) nameLabel.textContent = `Custom Journey: ${profileName}`;
      if (summaryLabel) summaryLabel.textContent = summary || 'Active profile overrides with verified constraints';
    } else {
      banner.classList.add('hidden');
    }
  }
}

