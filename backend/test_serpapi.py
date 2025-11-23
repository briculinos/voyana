"""
Quick test script to debug SerpAPI integration
Run with: python test_serpapi.py
"""
import os
import sys
from datetime import datetime, timedelta
from serpapi import GoogleSearch
import json

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.config import settings

def test_serpapi():
    """Test SerpAPI with a simple Copenhagen to London search"""

    api_key = settings.serpapi_key
    print(f"🔑 API Key configured: {bool(api_key)}")
    print(f"🔑 API Key (first 10 chars): {api_key[:10] if api_key else 'MISSING'}...")

    # Simple test: Copenhagen to London, 7 days from now
    departure_date = datetime.now() + timedelta(days=7)
    return_date = departure_date + timedelta(days=7)

    params = {
        "api_key": api_key,
        "engine": "google_flights",
        "departure_id": "CPH",  # Copenhagen
        "arrival_id": "LON",    # London
        "outbound_date": departure_date.strftime("%Y-%m-%d"),
        "return_date": return_date.strftime("%Y-%m-%d"),
        "adults": 2,
        "currency": "EUR",
        "hl": "en",
    }

    print(f"\n📋 Search Parameters:")
    print(json.dumps(params, indent=2, default=str))

    try:
        print(f"\n🔍 Executing SerpAPI search...")
        search = GoogleSearch(params)
        results = search.get_dict()

        print(f"\n✅ Response received!")
        print(f"📊 Response keys: {list(results.keys())}")

        if 'error' in results:
            print(f"\n❌ ERROR: {results['error']}")
            return

        if 'search_metadata' in results:
            print(f"\n📈 Search Metadata:")
            print(f"  Status: {results['search_metadata'].get('status')}")
            print(f"  ID: {results['search_metadata'].get('id')}")
            print(f"  Created: {results['search_metadata'].get('created_at')}")

        best_flights = results.get('best_flights', [])
        other_flights = results.get('other_flights', [])

        print(f"\n✈️  Flight Results:")
        print(f"  Best flights: {len(best_flights)}")
        print(f"  Other flights: {len(other_flights)}")

        if best_flights:
            print(f"\n🎯 First Best Flight Sample:")
            first_flight = best_flights[0]
            print(f"  Price: {first_flight.get('price', 'N/A')}")
            print(f"  Flights segments: {len(first_flight.get('flights', []))}")
            print(f"  Keys: {list(first_flight.keys())}")

        # Save full response for inspection
        output_file = "serpapi_test_response.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Full response saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_serpapi()
