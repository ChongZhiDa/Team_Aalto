# PS2 Team Collaboration & Role Guide

Welcome to the team workspace for **Problem Statement 2: Smart Commuter Companion**!

To allow all teammates to develop concurrently without stepping on each other's toes or causing git merge conflicts, the codebase has been cleanly decoupled into **4 independent modules**.

---

## 👥 1. Team Role & File Ownership Matrix

| Role | Domain | Primary Directory & Files | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **Teammate A** | **Frontend & Mobile UX** | `static/js/`<br>`static/css/`<br>`templates/index.html` | • Leaflet map rendering & custom pins<br>• High-contrast mobile ergonomics & dark mode<br>• Touch-friendly bottom drawer & scenario modal<br>• Offline tunnel resilience |
| **Teammate B** | **Routing & GIS** | `src/routing/` | • MRT network coordinates & polylines<br>• Pedestrian first/last-mile calculations<br>• Sheltered walkways & CoveredLinkWay GIS<br>• Multi-modal transit travel times & transfer penalties |
| **Teammate C** | **Data & API Integration** | `src/api/`<br>`scripts/test_live_api.py` | • LTA DataMall endpoints (`TrainServiceAlerts`, `PCD`, `BusArrival`)<br>• data.gov.sg 2-hr weather nowcasts & rainfall<br>• OneMap geocoding & routing connector<br>• In-memory caching & rate limiting |
| **Teammate D** | **Commuter Intelligence & AI** | `src/intelligence/` | • Commuter personas (Rachel, Arjun, Mdm Lim)<br>• Proactive pre-departure timing (07:20 AM)<br>• Delay noise filtering algorithms ($<15$m silent vs $\ge15$m action)<br>• 1-line actionable advice & AI/LLM summarizer |
| **Teammate E (or Shared)** | **QA & Submission** | `tests/`<br>`README.md`<br>`WRITEUP.md` | • Unit test suites for each package<br>• Verification on real mobile phone browsers<br>• 3–5 min demo video recording |

---

## 🛠️ 2. Deep Dive by Role

### 🎨 Teammate A: Frontend & Mobile UX

**Your Sandbox:**
- `static/js/map_controller.js`: All Leaflet map logic, zooming, station pins, pulsing red disrupted corridor, and OpenStreetMap attribution.
- `static/js/ui_controller.js`: Status alert cards, dynamic 3-level crowd chips (`LOW`, `MOD`, `HIGH`), route cards, and scenario selector drawer.
- `static/js/offline_cache.js`: LocalStorage caching and offline tunnel status banner.
- `static/js/main.js`: Main coordinator.
- `templates/index.html` & `static/style.css`: HTML structure and custom CSS.

**Things you can add/improve to score higher:**
1. Add turn-by-turn walking steps collapsible inside the route cards.
2. Add a haptic/sound effect or push notification simulation when a disruption occurs.
3. Test on your smartphone browser (`http://<lan-ip>:5000`) and ensure one-thumb ergonomics feel natural.

---

### 🗺️ Teammate B: Routing & GIS Engine

**Your Sandbox:**
- `src/routing/coordinates.py`: MRT station coordinates, line sequences, and origin/destination markers.
- `src/routing/door_to_door.py`: Pedestrian walking legs (distances, durations, and sheltered linkway percentages).
- `src/routing/multimodal_router.py`: Transit duration calculations, delay impact, and bypass routing logic.

**Things you can add/improve to score higher:**
1. Parse station polygons from `data/AmendmenttoMP2014RailStation.geojson` to dynamically compute station centroids and ground levels (`GRND_LEVEL: UNDERGROUND`).
2. Add transfer penalties (e.g. 4 minutes walking between platform levels at interchange stations).
3. Add cycle path connectivity (`CyclingPath`) for Arjun's commute.

---

### 🔌 Teammate C: Data & API Integration

**Your Sandbox:**
- `src/api/datamall_client.py`: Client for LTA DataMall endpoints.
- `src/api/weather_client.py`: Client for data.gov.sg real-time weather.
- `src/api/onemap_client.py`: Connector for OneMap API.
- `src/api/cache_manager.py`: Thread-safe caching and request throttling.
- `scripts/test_live_api.py`: Command-line testing utility.

**Things you can add/improve to score higher:**
1. Plug in your own LTA DataMall key and test `v3/BusArrival` to fetch real-time bus `Load` (`SEA`, `SDA`, `LSD`) for Express Bus 10e.
2. Connect `v2/FacilitiesMaintenance` to detect broken station lifts (crucial for Mdm Lim).
3. Expand `OneMapClient` to perform real-time address geocoding.

---

### 🧠 Teammate D: Commuter Intelligence & AI

**Your Sandbox:**
- `src/intelligence/personas.py`: Commuter profiles, departure routines, and sensitivity parameters.
- `src/intelligence/noise_filter.py`: Noise threshold evaluation logic (preventing alert fatigue).
- `src/intelligence/advisor.py`: Synthesizes concise 1-line actionable directives.
- `src/intelligence/scenarios.py`: Built-in disruption scenarios for hackathon judging.

**Things you can add/improve to score higher:**
1. **AI / LLM Summarizer (Beyond the Brief!)**: Add a prompt function in `advisor.py` that takes raw, messy service notices (such as from the SG MRT Telegram channel) and outputs clean, 1-line personalized advice.
2. Add more realistic disruption scenarios (e.g., Circle Line tunnel fault or North-South Line track failure).
3. Implement adaptive departure countdowns ("Leave 10 mins early to avoid 08:00 rush").

---

## 🌿 3. Git Collaboration Workflow (Avoid Merge Conflicts!)

To ensure smooth teamwork without git clashes:

1. **Create your own branch before starting work**:
   ```bash
   git checkout master
   git pull
   git checkout -b feat/frontend      # for Teammate A
   # or
   git checkout -b feat/routing       # for Teammate B
   # or
   git checkout -b feat/api           # for Teammate C
   # or
   git checkout -b feat/intelligence  # for Teammate D
   ```

2. **Run tests before pushing**:
   ```bash
   python -m unittest discover tests
   ```

3. **Never commit `.env` or API keys**:
   - The `.gitignore` file is already set up to ignore `.env`, `__pycache__`, and temporary files.

4. **Merge back to master**:
   - Create a Pull Request or merge cleanly into `master` after verifying tests pass.

---

## 🚀 4. Quick Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all automated tests (19 tests)
python -m unittest discover tests

# Test external APIs directly from CLI
python scripts/test_live_api.py

# Launch the app
python app.py
```
App URL: **http://localhost:5000**

