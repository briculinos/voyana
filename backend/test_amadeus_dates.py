"""
Test if Amadeus has data for the dates the Intent Parser is suggesting
"""
import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError

load_dotenv()

client = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET')
)

# Test the exact dates from Intent Parser
test_dates = [
    ("2026-04-20", "2026-04-30", "Intent Parser suggested dates (Apr 2026)"),
    ("2025-12-22", "2025-12-29", "Near future (Dec 2025)"),
    ("2026-01-15", "2026-01-22", "Early 2026 (Jan)"),
]

for departure, return_date, description in test_dates:
    print(f"\nTesting: {description}")
    print(f"  Dates: {departure} to {return_date}")

    try:
        response = client.shopping.flight_offers_search.get(
            originLocationCode='CPH',
            destinationLocationCode='ROM',
            departureDate=departure,
            returnDate=return_date,
            adults=2,
            max=5,
            currencyCode='EUR'
        )

        print(f"  ✅ Found {len(response.data)} flights")
        if len(response.data) > 0:
            print(f"     Price: {response.data[0]['price']['total']} EUR")

    except ResponseError as error:
        print(f"  ❌ ERROR: {error.description}")
        print(f"     Status: {error.response.status_code}")
