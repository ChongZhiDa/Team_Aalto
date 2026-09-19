# StationBuddy: PS2 Technical Write-up

## Product Focus: Rachel as a Navigation User

StationBuddy is built for **Rachel, a fixed-schedule commuter who uses the app
as a navigation device**. She can enter any starting location and destination,
inspect the resulting door-to-door route, save her own journey preferences, and
receive a route change recommendation when a simulated disruption affects her
trip.

Rachel is the only persona presented in this write-up. The default demonstration
is Tampines to Raffles Place, but the navigation workflow also supports other
stations, landmarks and Singapore postal-code locations.

## What Makes StationBuddy Unique

StationBuddy is not only a route finder or a generic transport-alert feed. Its
distinctive feature is **personalized disruption decision support** for Rachel:

- **It evaluates Rachel's actual journey.** An EWL failure produces an alert only
  when her selected route uses EWL; an unaffected route remains quiet.
- **It filters operational noise.** Rachel's configured delay threshold and
  arrival deadline determine whether the app stays silent or interrupts her with
  a recommendation.
- **It recommends an action, not just a warning.** When her EWL journey is
  affected, the app presents a Downtown Line alternative that Rachel can select
  and view on the map with its walking and interchange legs.
- **It adapts the journey to conditions.** During the simulated monsoon
  scenario, exposed walking legs receive rain penalties and routes with more
  sheltered coverage are surfaced with shelter details.
- **It keeps the plan personal and reusable.** Rachel can change her locations,
  deadline and delay tolerance, then save the customized journey for later use.

These capabilities are implemented in the Flask decision layer, routing engine
and custom persona adapter described below, rather than being presentation-only
features.

## Judge Walkthrough

The following is the intended end-to-end demonstration. The disruption and
weather cases are local simulated scenarios, so the judge can reproduce them
without waiting for a real incident.

### 1. Plan a journey

1. Open the app at `http://localhost:5000`.
2. In the origin field, enter a starting location such as `Tampines`.
3. In the destination field, enter `Raffles Place`.
4. Select an autocomplete result if one is shown. The app resolves the two
    locations and displays a door-to-door route with walking and MRT legs on the
    map.
5. Repeat with a different pair, such as `Woodlands` to `Raffles Place`, to show
    that Rachel is using the app for navigation rather than only viewing a fixed
    status page.

This exercises `/api/suggest`, `/api/status` and the custom location-routing
path. The route duration is a modeled estimate, not a guaranteed live ETA.

### 2. Customize and save Rachel's journey

1. Open the **Commuter Persona Customizer**.
2. Edit Rachel's origin, destination, arrival deadline and delay threshold.
3. Add or update the journey route in the customizer.
4. Select **Save**. The app saves the customized profile and its scheduled route.
5. Close and reopen the customizer, then select the saved Rachel profile to show
    that the journey can be loaded again.

This exercises the custom persona adapter under `/api/custom/personas*` and the
custom route calculation under `/api/custom-route` or `/api/custom/route`.
The browser may also retain the active journey in local storage for the current
device.

### 3. EWL fault: unaffected journey

1. Keep a saved Rachel journey whose route does not use the East-West Line, for
    example a journey beginning at `Woodlands` and ending at `Raffles Place` if
    the resolved route does not include EWL.
2. Open **Scenarios** and select **Whole EWL Line Failure (+25 min)**.
3. Check Rachel's route decision and notification surfaces. The immediate
  scenario response is represented by the in-app status/banner; the saved-plan
  notification balloon is populated by the next-day notification check.

The product behavior is that an EWL disruption is relevant only when Rachel's
saved route uses EWL. An unaffected journey remains notification-suppressed and
does not activate the EWL bypass. The scenario remains labelled as simulated.

### 4. EWL fault: affected journey and bypass

1. Change Rachel's journey back to the default `Tampines` to `Raffles Place`
    corridor, or save another journey that uses EWL.
2. Select **Whole EWL Line Failure (+25 min)** again.
3. The proactive in-app status/banner should appear because the selected
    journey is affected. It explains that the normal route is delayed and shows a
    Downtown Line bypass recommendation.
4. Select the bypass action or click the alternative route card.
5. Confirm that the map switches to the alternative route and that its walking,
    interchange and arrival details are shown.

The route decision is based on the configured delay threshold and arrival
deadline. In the supplied Rachel fixture, the normal scenario contains a
2-minute delay, while the EWL-fault scenario contains a simulated 25-minute
delay. These are fixture inputs, not measured real-world performance.

### 5. Monsoon downpour: prefer sheltered walking

1. Return to Rachel's affected or default journey.
2. Open **Scenarios** and select **Monsoon Downpour + Crowd Surge (+16 min)**.
3. Check the weather chip, route status and walking legs.
4. Confirm that the recommendation prioritizes covered or more sheltered
    walkways and indoor transfers, and that the map shows the selected route's
    sheltered walking details.

The weather scenario sets a rain alert and increases the modeled cost of exposed
walking legs. The app therefore favors routes with higher sheltered coverage;
it does not claim that every real-world footpath is currently open or covered.

## Architecture

1. `templates/index.html`, `static/app.js` and `static/js/` provide the mobile
    navigation interface, search fields, customizer, route cards, notifications,
    Leaflet map and browser-side offline cache.
2. `app.py` is the Flask composition layer. It serves the page and exposes JSON
    routes for status, suggestions, routing, scenarios, settings, custom
    personas and next-day notifications.
3. `src/engine.py` combines Rachel's profile, scenario state, weather, crowd and
    delay decisions into one evaluation response.
4. `src/routing/` provides station graph routing, location resolution, GeoJSON
    station metadata, pedestrian legs and alternative route geometry.
5. `src/intelligence/` provides Rachel's profile, delay noise filtering,
    actionable advice, custom profile validation and persistence.
6. `src/api/` contains optional DataMall, OneMap and weather clients plus cache
    and rate-limiting helpers. Empty credentials use fallback data where
    supported, allowing the simulated walkthrough to run without API keys.

The main request path is:

```text
Rachel's browser -> Flask endpoint -> CommuterEngine / MultimodalRouter
                        -> local data and optional APIs -> JSON decision -> map/UI
```

## Main Functions Used in the Walkthrough

| Function | Role in Rachel's journey |
|---|---|
| `index` | Serves the navigation interface. |
| `get_suggestions` | Finds matching stations, landmarks, addresses and postal codes. |
| `get_arbitrary_route` | Calculates a door-to-door route for arbitrary locations. |
| `_enrich_evaluation_with_custom_route` | Adds walking paths, station tracks and alternative map layers. |
| `get_commute_status` | Returns Rachel's current route, weather and disruption decision. |
| `get_scenarios` | Lists the normal, EWL-fault and monsoon simulation scenarios. |
| `select_scenario` | Recalculates Rachel's journey after a scenario is selected. |
| `get_personas` | Loads the available Rachel/custom profiles for the customizer. |
| `create_custom_route` | Calculates Rachel's customized journey. |
| `update_settings` | Updates Rachel's locations, deadline and delay threshold. |
| `get_next_day_notifications` | Checks saved journeys for next-day disruption notifications and replacement routes. |

The registered custom-persona blueprint supplies the save, load, create and
update endpoints used by the customizer.

## Assumptions

- Rachel's route is modeled using the local Singapore MRT graph, station GeoJSON
    metadata and modeled pedestrian legs.
- Scenario values are deterministic fixtures for repeatable judging, not claims
  about current service conditions.
- Route durations, walking times, transfer penalties and shelter percentages are
  estimates used to compare options.
- Live weather, DataMall or OneMap services may be unavailable or stale; fallback
  data is used where implemented.
- OpenStreetMap tiles are rendered in the browser and attribution is displayed.
- Rachel's settings are prototype-level application/browser state, not a
  production account, privacy system or operating-system push service.

## Limitations

- The simulated EWL fault and monsoon downpour do not prove real-time service
  accuracy. They exist so a judge can test the decision flow on demand.
- The route planner estimates travel and walking time; it cannot guarantee train
  arrivals, pedestrian access, lift availability or road conditions.
- The notification is an in-app proactive alert and next-day notification flow;
  the prototype does not send native mobile push notifications.
- Live API behavior depends on external services, credentials, network access and
  rate limits.
- The prototype does not provide production authentication, multi-user storage,
  complete accessibility certification or production-scale monitoring.

## Numeric Claims and Reproduction

The numeric values used in the walkthrough are traceable to source fixtures and
tests: Rachel's default 15-minute threshold, the normal 2-minute delay, the
simulated EWL-fault 25-minute delay and the monsoon scenario's 16-minute delay.
They are not accuracy, speed-up or live-feed benchmark results.

Reproduce the behavior from `PS2` with:

```powershell
python -m unittest discover tests -v
```

`tests/test_engine.py` verifies delay suppression, proactive EWL alerting,
threshold changes and scenario switching. `tests/test_routing.py` verifies
route durations, walking/rain behavior and alternative routing. The API and
custom-persona tests verify fallback clients, saving/loading and customized
journeys. The unaffected custom-route EWL case is additionally a manual smoke
check in the walkthrough; it is not currently a dedicated automated regression
test. No accuracy or comparative speed claim is made because the repository does
not contain a controlled benchmark dataset.
