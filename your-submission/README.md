# StationBuddy — Universal Smart Commuter Companion (PS2)

> **Universal Google Maps-Style Interface:** Floating origin/destination search box, arrival timing selector, proactive traffic incident detour banners, and multi-modal routing on an OpenStreetMap base.  
> **Hero Journey Persona:** **Rachel** — Fixed-schedule corporate commuter (Tampines $\to$ Raffles Place, arrive by 08:45 AM).  
> **Core Value:** Proactive pre-departure decision support (at 07:20 AM, 20 minutes before stepping out), intelligent delay noise filtering ($<15$ min delay silent vs. $\ge 15$ min actionable bypass), and 1-tap detour recommendations.

---

## 1. Prerequisites

- **Python**: Version 3.9 or higher (tested on Python 3.10, 3.11, 3.12, 3.14).
- **Package Manager**: `pip`.
- **Web Browser**: Any modern browser (Google Chrome, Safari, Firefox, Edge). Scored on mobile viewports (e.g. 390x844).

No Node.js or complex build toolchain is required.

---

## 2. Installation & Quick Start

Follow these exact commands to run the application on any clean machine:

```bash
# 1. Navigate to the PS2 directory
cd PS2

# 2. Install dependencies (lightweight: Flask & Requests)
pip install -r requirements.txt

# 3. Start the application
python app.py
```

The app will start immediately:
```
Starting Smart Commuter Companion on http://localhost:5000
 * Running on http://127.0.0.1:5000
```

Open your browser at: **[http://localhost:5000](http://localhost:5000)**  
*(For mobile testing, open Developer Tools and press `Ctrl+Shift+M` or open `http://<your-lan-ip>:5000` on your smartphone browser).*

---

## 3. Configuration & API Keys

Copy the template configuration:

```bash
cp .env.example .env
```

| Variable | Description | Required? |
|---|---|---|
| `LTA_DATAMALL_KEY` | LTA DataMall AccountKey (free at [datamall.lta.gov.sg](https://datamall.lta.gov.sg)) | **Optional** (App comes with built-in realistic disruption scenarios so an API key is not required to evaluate full functionality) |
| `PORT` | Server listening port | Optional (Default: `5000`) |

---

## 4. "What to Click" — Guided Tour for Judges (5-Minute Evaluation)

To evaluate Rachel's journey and test all mandatory capabilities, follow this 4-step walk:

### Step 1: Baseline / Normal Morning (07:20 AM)
1. Open [http://localhost:5000](http://localhost:5000).
2. Observe the **Proactive Alert Banner**: It is calm green (`On Schedule`).
3. Notice the **Noise Filter**: Train headway is $+2$ min. Because $+2\text{m} < 15\text{m}$, the notification is **suppressed** so Rachel is not spammed with commute noise.
4. On the map: View the green East-West Line (EWL) track, station pins, walking first-and-last-mile dashed links, and the legal attribution **`© OpenStreetMap contributors`** in the bottom right.

### Step 2: Simulate Major Disruption (The Hero Moment)
1. Tap the **"Scenarios"** button in the top right.
2. Select **"EWL Track Point Fault (+25 min)"**.
3. Observe the immediate reactive shift:
   - Status shifts to **Proactive Interruption** (Red alert with warning icon).
   - The noise filter evaluates $+25\text{m} \ge 15\text{m}$ (meeting arrival at 08:47 AM risks her 08:45 desk target).
   - The app synthesizes a **one-line actionable headline**:  
     *"⚠️ EWL Disruption (+25 min). Switch to Downtown Line at Tampines Downtown: Arrive 08:24 AM (On Time for 09:00 meeting)."*
   - On the map: The disrupted corridor between Bedok (EW5) and Bugis (EW12) turns into a **pulsing dashed red line**.

### Step 3: One-Tap Bypass Routing
1. In the alert banner, tap **"Switch to Downtown Line Bypass"** (or tap the DTL card in the bottom drawer).
2. The map immediately highlights the **Downtown Line (DTL)** blue bypass track from Tampines Downtown (DT32) to Telok Ayer (DT18) with a 5-minute sheltered walk to One Raffles Place.
3. Rachel arrives at **08:24 AM**, completely dodging the 25-minute bottleneck.

### Step 4: Evaluate Weather Surge & Noise Sensitivity
1. Open the **"Scenarios"** drawer again.
2. Select **"Monsoon Downpour + Crowd Surge"**: Notice the weather chip updates with live rain nowcast and switches walking legs to prioritized sheltered covered linkways.
3. Test dynamic filter adjustment: Change the threshold dropdown from `15 min` to `10 min` or `20 min` to see how the decision engine adapts to user tolerance.

---

## 5. Running Automated Tests

Run the unit test suite to verify canonical line mapping, threshold filtering, and scenario models:

```bash
python -m unittest tests.test_engine
```

Expected output:
```
Ran 5 tests in 0.001s
OK
```

---

## 6. OpenStreetMap Compliance

This application strictly adheres to the brief's geospatial requirements:
- **ODbL Attribution**: Displayed on the interactive map: `© OpenStreetMap contributors`.
- **Tile Usage Policy**: Tile requests are rendered client-side using standard Leaflet slippy map conventions with tile caching, avoiding bulk scraping or hammering donated servers.

