"""
Test the AmadeusFlightService directly with Intent Parser output
"""
import logging
from datetime import date
from app.services.amadeus_client import AmadeusFlightService
from app.models.travel import TravelIntent

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

# Create intent exactly as Intent Parser would
intent = TravelIntent(
    origin="Copenhagen",
    destination="Rome, Italy",  # This is what Intent Parser returns
    departure_date=date(2026, 4, 20),
    return_date=date(2026, 4, 30),
    duration_days=10,
    total_budget=5000.0,
    num_adults=2,
    num_children=0
)

print("Testing AmadeusFlightService.search_flights()")
print(f"Intent:")
print(f"  Origin: {intent.origin}")
print(f"  Destination: {intent.destination}")
print(f"  Dates: {intent.departure_date} to {intent.return_date}")
print(f"  Adults: {intent.num_adults}")
print("\n" + "="*80 + "\n")

service = AmadeusFlightService()
results = service.search_flights(intent, max_results=5)

print(f"Results: {len(results)} flights")
if len(results) > 0:
    print(f"\n✅ SUCCESS!")
    for i, flight in enumerate(results[:3], 1):
        print(f"  {i}. €{flight.total_price} - {flight.number_of_stops} stops")
else:
    print(f"\n❌ NO FLIGHTS FOUND")
