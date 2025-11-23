"""
Quick test script to debug Amadeus API integration
Run with: python test_amadeus.py
"""
import os
import sys
from datetime import datetime, timedelta
from amadeus import Client, ResponseError
import json

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.config import settings

def test_amadeus():
    """Test Amadeus with a simple Copenhagen to London search"""

    print(f"🔑 API Key configured: {bool(settings.amadeus_api_key)}")
    print(f"🔑 API Secret configured: {bool(settings.amadeus_api_secret)}")
    print(f"🔑 API Key (first 10 chars): {settings.amadeus_api_key[:10] if settings.amadeus_api_key else 'MISSING'}...")

    try:
        # Initialize client
        print(f"\n🔧 Initializing Amadeus client...")
        client = Client(
            client_id=settings.amadeus_api_key,
            client_secret=settings.amadeus_api_secret
        )
        print(f"✅ Client initialized")

        # Simple test: Copenhagen to London, 7 days from now
        departure_date = datetime.now() + timedelta(days=7)
        return_date = departure_date + timedelta(days=7)

        params = {
            'originLocationCode': 'CPH',
            'destinationLocationCode': 'LON',
            'departureDate': departure_date.strftime('%Y-%m-%d'),
            'returnDate': return_date.strftime('%Y-%m-%d'),
            'adults': 2,
            'max': 5,
            'currencyCode': 'EUR'
        }

        print(f"\n📋 Search Parameters:")
        print(json.dumps(params, indent=2))

        print(f"\n🔍 Executing Amadeus search...")
        response = client.shopping.flight_offers_search.get(**params)

        print(f"\n✅ Response received!")
        print(f"📊 Number of offers: {len(response.data)}")

        if response.data:
            print(f"\n🎯 First Flight Offer Sample:")
            first_offer = response.data[0]
            print(f"  Price: {first_offer['price']['total']} {first_offer['price']['currency']}")
            print(f"  Itineraries: {len(first_offer['itineraries'])}")

            if first_offer['itineraries']:
                first_itinerary = first_offer['itineraries'][0]
                print(f"  Segments in first itinerary: {len(first_itinerary['segments'])}")

                if first_itinerary['segments']:
                    first_segment = first_itinerary['segments'][0]
                    print(f"  First segment: {first_segment['departure']['iataCode']} -> {first_segment['arrival']['iataCode']}")
                    print(f"  Carrier: {first_segment['carrierCode']} {first_segment['number']}")

            # Save full response
            output_file = "amadeus_test_response.json"
            with open(output_file, 'w') as f:
                # Convert response.data to dict for JSON serialization
                json.dump([dict(offer) for offer in response.data], f, indent=2, default=str)
            print(f"\n💾 Full response saved to: {output_file}")

        else:
            print(f"\n⚠️  No flight offers returned")

    except ResponseError as error:
        print(f"\n❌ Amadeus ResponseError:")
        print(f"  Status Code: {error.response.status_code}")
        print(f"  Error Details: {error.response.body}")

        try:
            error_data = json.loads(error.response.body)
            print(f"\n📋 Parsed Error:")
            print(json.dumps(error_data, indent=2))
        except:
            pass

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_amadeus()
