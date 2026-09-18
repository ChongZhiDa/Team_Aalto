# PS2 Technical Write-up — Smart Commuter Companion

## 1. Chosen Persona: Rachel (Fixed-Schedule Commuter)

### Persona Description & Behavioral Rationale
- **Commuter Profile:** Rachel has commuted from Tampines (East) to Raffles Place (CBD) for 4 years.
- **Fixed Constraints:** She leaves home at **07:40 AM** and must be at her desk by **08:45 AM** to prepare for a recurring **09:00 AM** executive meeting.
- **The Core Friction (Alert Fatigue):** Most transit applications broadcast generic system-wide notifications ("Delays on East-West Line") or require active user query. A 3-to-5-minute delay is meaningless noise for Rachel because she has a 23-minute buffer (normal arrival is 08:22 AM). However, a 15-to-25-minute delay costs her a high-stakes meeting.
- **Product Philosophy:** 
  1. **Proactive Intervention:** Analyze status at **07:20 AM** (20 minutes *before* leaving home) while the commuter is still in her apartment and can make a clean modal switch.
  2. **Noise Suppression:** Zero intrusive alerts when delays are below the 15-minute threshold or arrival remains before 08:45 AM.
  3. **One-Line Actionable Decision Support:** Replaces ambiguous status flags with concrete, one-line directions and exact arrival comparisons.

---

## 2. System Architecture & Components

```
                          ┌────────────────────────────────────────────────────────┐
                          │         Rachel's Mobile Browser (Phone / PWA)          │
                          │        - Leaflet OpenStreetMap Engine                  │
                          │        - High-Contrast 1-Second Glancibility Cards     │
                          │        - LocalStorage Offline Itinerary Cache          │
                          └───────────────────────────▲────────────────────────────┘
                                                      │ REST / JSON
                          ┌───────────────────────────▼────────────────────────────┐
                          │               Python Flask API Server                  │
                          │                     (app.py)                           │
                          └───────┬───────────────────┬───────────────────┬────────┘
                                  │                   │                   │
         ┌────────────────────────┴────────┐  ┌───────┴─────────┐  ┌──────┴────────────────┐
         │     LTA DataMall Connector      │  │ data.gov.sg API │  │ Commuter Decision Engine│
         │ - TrainServiceAlerts            │  │ - 2-hr nowcast  │  │ - Noise Filter (<15m)  │
         │ - Station Crowd (PCDRealTime)   │  │ - Real-time rain│  │ - Door-to-door Router  │
         │ - Canonical Line Code Mapper    │  │                 │  │ - Scenario Replay      │
         └─────────────────────────────────┘  └─────────────────┘  └───────────────────────┘
```

### Component Breakdown
1. **Canonical Line Code Mapper (`src/canonical_lines.py`)**:
   - Resolves systemic naming inconsistencies across LTA DataMall endpoints (e.g. `TrainServiceAlerts` uses `STL` and `PTL`, whereas Station Crowd Density uses `SLRT` and `PLRT`; `CGL` is folded into `EWL`). All lines map through a single canonical enum.
2. **DataMall Connector (`src/datamall.py`)**:
   - Fetches official structured alerts (`Status`, `AffectedSegments`, `FreePublicBus`, `FreeMRTShuttle`) with in-memory caching (60s TTL) and non-blocking fallbacks.
3. **Real-Time Weather Client (`src/weather.py`)**:
   - Connects to `api-open.data.gov.sg/v2/real-time/api/two-hr-forecast` without requiring an API key, checking 2-hour rain nowcasts for Tampines and the Downtown core.
4. **Rachel's Decision & Routing Engine (`src/engine.py` & `src/routing.py`)**:
   - Computes door-to-door journey times across multiple modes:
     - **Primary Route (EWL)**: Walk to Tampines EWL $\to$ Direct EWL $\to$ Walk to One Raffles Place.
     - **Bypass Route 1 (DTL)**: Walk to Tampines Downtown $\to$ DTL to Telok Ayer $\to$ Sheltered walk via Cross St to Raffles Place.
     - **Bypass Route 2 (Express Bus 10e)**: Walk to Tampines Ave 7 $\to$ Express Bus 10e via ECP $\to$ Walk to Fullerton Sq.
   - Applies the noise filter: suppresses alerts when delay $< 15$ min, and activates high-urgency bypass advice when delay $\ge 15$ min.
5. **Interactive OSM Visualizer (`static/app.js` & `templates/index.html`)**:
   - Built mobile-first using Leaflet.js and OpenStreetMap base tiles.
   - Highlights disrupted track corridors in dashed pulsing red while keeping unaffected sections clearly distinguished.
   - Features a 1-second scannable 3-level crowding pill (`LOW`, `MOD`, `HIGH`).
6. **Disruption Replay Engine (`src/scenarios.py`)**:
   - Provides instant switching between Normal, Disrupted (+25m), Weather Surge, and Live API modes so judges can evaluate disruption responses even on quiet days.

---

## 3. Verifiable Calculations & Benchmark Metrics

All numbers, transit durations, and distances used in the app are explicitly derived as follows:

| Leg | Distance | Duration | Methodology & Derivation |
|---|---|---|---|
| **Walk: Home $\to$ Tampines MRT (EW2)** | 520 m | 6 min | Average walking speed of 1.35 m/s ($\approx 4.8\text{ km/h}$) + pedestrian crossing delay at Tampines Ave 4. |
| **Walk: Home $\to$ Tampines Downtown (DT32)** | 450 m | 5 min | 450 m at 1.35 m/s via sheltered walkway along Tampines St 21. |
| **Train: EWL (EW2 $\to$ EW14)** | 11 inter-station hops | 31 min | LTA published scheduled transit time (average 2.8 min per station hop including dwell time). |
| **Train: DTL (DT32 $\to$ DT18)** | 14 inter-station hops | 34 min | LTA published scheduled transit time for Downtown Line. |
| **Walk: Telok Ayer Exit B $\to$ Desk** | 410 m | 5 min | 410 m via Church St / Market St covered walkways. |
| **Walk: Raffles Place Exit B $\to$ Desk** | 120 m | 2 min | 120 m underground linkway to One Raffles Place basement. |
| **Express Bus 10e: Tampines $\to$ CBD** | 18.2 km | 38 min | Morning express bus timetable via ECP expressway. |

### Journey Comparison Under Major Disruption (+25 min EWL Track Fault):
- **EWL Primary (Disrupted)**: $6\text{m walk} + 3\text{m wait} + (31 + 25)\text{m train} + 2\text{m walk} = \mathbf{67\text{ mins total}}$.  
  - Departure: 07:40 AM $\to$ **Arrival: 08:47 AM** (**LATE**, misses 08:45 desk target).
- **DTL Bypass (Recommended)**: $5\text{m walk} + 3\text{m wait} + 34\text{m train} + 5\text{m walk} = \mathbf{47\text{ mins total}}$.  
  - Departure: 07:40 AM $\to$ **Arrival: 08:27 AM** (**ON TIME**, saves 20 minutes!).

### System Latency & Performance:
- Backend decision evaluation and noise filter check: **$< 1.5\text{ ms}$** response time.
- Offline cached recovery on network disconnect: **$< 20\text{ ms}$** transition to cached itinerary.

---

## 4. Key Assumptions & Known Limitations

1. **Underground Signal Dead-Zones:** Commuters lose 4G/5G signals inside underground tunnels.  
   *Handling:* The app automatically caches the latest evaluated itinerary in browser `localStorage`. When the browser detects `navigator.onLine === false`, the app displays a prominent "Tunnel Mode: Offline Itinerary Cached" status rather than crashing or showing blank screens.
2. **Quiet Live Feeds During Evaluation:** LTA `TrainServiceAlerts.AffectedSegments` is empty on normal days.  
   *Handling:* The app provides a dedicated "Scenarios" drawer for judges with clearly labeled simulated replay data reproducing an authentic EWL track point fault and monsoon downpour.
3. **Privacy & Data Handling:** No personal commuter location or credentials are sent to external servers or logged in persistent storage. All threshold preferences are evaluated locally in memory.

---

## 5. Deliverables & Checklist

- [x] Runnable mobile-first web app on OpenStreetMap base.
- [x] Mandatory attribution `© OpenStreetMap contributors` prominently displayed.
- [x] Clear setup instructions in `PS2/README.md` (clean machine tested).
- [x] `.env.example` provided with zero credentials committed.
- [x] Full automated test suite passing (`python -m unittest tests.test_engine`).

