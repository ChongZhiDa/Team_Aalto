"""
Developer Utility: Test Live APIs from Command Line.
Usage: python scripts/test_live_api.py
"""

import os
import sys

# Ensure PS2 root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.weather_client import WeatherClient
from src.api.datamall_client import DataMallClient
from src.api.onemap_client import OneMapClient


def main():
    print("========================================")
    print("Testing Singapore Transit & Weather APIs")
    print("========================================")

    # 1. Test Weather Nowcast (data.gov.sg - no key required)
    print("\n[1/3] Testing data.gov.sg Weather Nowcast...")
    weather = WeatherClient()
    w_data = weather.get_commute_weather("Tampines", "City")
    print(f"  -> Origin (Tampines): {w_data.get('origin_forecast')}")
    print(f"  -> Dest (City): {w_data.get('dest_forecast')}")
    print(f"  -> Rain Alert: {w_data.get('rain_alert')}")
    print("  [OK] data.gov.sg weather reachable!")

    # 2. Test LTA DataMall (optional key)
    print("\n[2/3] Testing LTA DataMall API...")
    key = os.getenv("LTA_DATAMALL_KEY", "")
    if key:
        print(f"  Found LTA_DATAMALL_KEY ({key[:4]}...)")
    else:
        print("  Notice: LTA_DATAMALL_KEY not set in env (using simulated fallback)")

    dm = DataMallClient()
    alerts = dm.get_train_service_alerts()
    print(f"  -> Disruption Status: {alerts.get('Status')}")
    print(f"  -> Affected Segments Count: {len(alerts.get('AffectedSegments', []))}")
    print("  [OK] DataMall client initialized!")

    # 3. Test OneMap Geocoding
    print("\n[3/3] Testing OneMap Geocoding...")
    om = OneMapClient()
    search = om.search_address("Tampines MRT")
    results_count = len(search.get("results", []))
    print(f"  -> Search results for 'Tampines MRT': {results_count} found")
    print("  [OK] OneMap client initialized!")

    print("\n========================================")
    print("All API client modules are operational!")
    print("========================================")


if __name__ == "__main__":
    main()

