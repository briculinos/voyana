"""
Test the full flow from TravelIntent to flight results
This mimics exactly what happens in production
"""
import os
import sys
from datetime import datetime, timedelta
import logging

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.models.travel import TravelIntent
from app.services.amadeus_client import AmadeusFlightService
from app.services.serpapi_client import SerpAPIFlightService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_with_intent():
    """Test flight search with a TravelIntent object (just like production)"""

    # Create a TravelIntent for Copenhagen to Kyoto
    # This mimics what the intent parser would create
    departure_date = datetime.now() + timedelta(days=14)
    return_date = departure_date + timedelta(days=14)

    intent = TravelIntent(
        origin="Copenhagen",
        destination="Kyoto, Japan",
        departure_date=departure_date.date(),
        return_date=return_date.date(),
        num_adults=2,
        num_children=0,
        total_budget=3000.0,
        interests=["culture", "food"],
        travel_style="balanced"
    )

    print("=" * 80)
    print("TESTING FLIGHT SEARCH WITH TRAVELINTENT")
    print("=" * 80)
    print(f"\n📋 TravelIntent:")
    print(f"  Origin: {intent.origin}")
    print(f"  Destination: {intent.destination}")
    print(f"  Departure: {intent.departure_date}")
    print(f"  Return: {intent.return_date}")
    print(f"  Adults: {intent.num_adults}")
    print(f"  Children: {intent.num_children}")
    print(f"  Budget: {intent.total_budget}")

    # Test Amadeus (this is what the production code does)
    print(f"\n" + "=" * 80)
    print("TESTING AMADEUS SERVICE")
    print("=" * 80)

    amadeus_service = AmadeusFlightService()

    try:
        flights = amadeus_service.search_flights(intent, max_results=5)
        print(f"\n✅ Amadeus returned {len(flights)} flights")

        if flights:
            print(f"\n🎯 Sample Flight:")
            flight = flights[0]
            print(f"  Price: {flight.total_price} {flight.currency}")
            print(f"  Duration: {flight.total_duration_minutes} minutes")
            print(f"  Stops: {flight.number_of_stops}")
            print(f"  Outbound: {flight.outbound_segments[0].origin} -> {flight.outbound_segments[-1].destination}")
            print(f"  Return: {flight.return_segments[0].origin} -> {flight.return_segments[-1].destination}")
        else:
            print(f"\n⚠️  No flights found")

    except Exception as e:
        print(f"\n❌ Amadeus error: {e}")
        import traceback
        traceback.print_exc()

    # Test SerpAPI
    print(f"\n" + "=" * 80)
    print("TESTING SERPAPI SERVICE")
    print("=" * 80)

    serpapi_service = SerpAPIFlightService()

    try:
        flights = serpapi_service.search_flights(intent, max_results=5)
        print(f"\n✅ SerpAPI returned {len(flights)} flights")

        if flights:
            print(f"\n🎯 Sample Flight:")
            flight = flights[0]
            print(f"  Price: {flight.total_price} {flight.currency}")
            print(f"  Duration: {flight.total_duration_minutes} minutes")
            print(f"  Stops: {flight.number_of_stops}")
        else:
            print(f"\n⚠️  No flights found")

    except Exception as e:
        print(f"\n⚠️  SerpAPI error (expected - quota exceeded): {e}")

if __name__ == "__main__":
    test_with_intent()
