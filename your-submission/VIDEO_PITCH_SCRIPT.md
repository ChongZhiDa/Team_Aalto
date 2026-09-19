# StationBuddy: Two-Minute Video Pitch Script

## 0:00-0:15 - The Problem

**On screen:** Show the StationBuddy home screen with Rachel's default journey.

**Voiceover:**

"A normal commute is easy. The difficult day is when a disruption happens and the commuter has to decide whether it actually affects her, whether she should leave earlier, and which alternative route is reliable. Generic alerts create noise. StationBuddy turns a disruption into a personal navigation decision."

## 0:15-0:35 - The Solution

**On screen:** Enter an origin and destination, such as Tampines and Raffles Place.

**Voiceover:**

"Our product is designed around Rachel, a fixed-schedule commuter. She enters any starting point and destination, and StationBuddy creates a door-to-door route with walking, MRT and alternative route information. Rachel can then open the Commuter Persona Customizer, set her locations, arrival deadline and delay tolerance, and save the journey for later use."

## 0:35-1:05 - Route-Aware EWL Disruption

**On screen:** Show an unaffected route, then open Scenarios and select Whole EWL Line Failure.

**Voiceover:**

"The key idea is route-aware decision support. First, we test a journey that does not use the East-West Line. The EWL fault does not trigger a disruption notification, because it is not relevant to Rachel's route."

**On screen:** Change back to Tampines to Raffles Place and select the same scenario.

**Voiceover:**

"Now we test Rachel's usual EWL journey. The simulated fault crosses her route and the app produces a proactive alert with a Downtown Line bypass. Rachel selects the alternative, and the map updates to show the new route, walking legs, interchange details and arrival information."

## 1:05-1:30 - Monsoon Adaptation

**On screen:** Select Monsoon Downpour + Crowd Surge.

**Voiceover:**

"StationBuddy also responds to weather. In the monsoon scenario, rain adds a cost to exposed walking legs. The route cards and map surface alternatives with higher sheltered coverage and show the shelter details, helping Rachel stay informed before she leaves."

## 1:30-1:50 - Why It Is Different

**On screen:** Show the alert decision and route cards.

**Voiceover:**

"What makes StationBuddy different is that it does not simply report a transport status. It checks Rachel's actual route, filters minor delays using her tolerance and deadline, and recommends an action only when it matters. The journey remains customizable and reusable rather than being a one-time search."

## 1:50-2:00 - Technology and Closing

**On screen:** Show the final route on the map.

**Voiceover:**

"StationBuddy uses a Python Flask backend, JavaScript and Leaflet with OpenStreetMap, a local MRT graph and pedestrian routing model, plus optional LTA DataMall, OneMap and weather integrations. It gives Rachel one clear answer to the question that matters: does this disruption affect my journey, and what should I do next?"
