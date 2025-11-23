"""
Hotel Search Service
Supports multiple hotel APIs (Hotelbeds, Amadeus, Booking.com via RapidAPI)
For MVP, includes mock data generator for testing.
"""
from datetime import date, datetime
from typing import List, Optional, Dict
import httpx
import logging
import hashlib
import time
from app.models.travel import AccommodationOption, TravelIntent
from app.utils.config import settings

logger = logging.getLogger(__name__)


# Approximate exchange rates to EUR (updated periodically)
CURRENCY_RATES_TO_EUR = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "JPY": 0.0062,  # 1 JPY = 0.0062 EUR
    "CNY": 0.13,
    "INR": 0.011,
    "AUD": 0.61,
    "CAD": 0.68,
    "CHF": 1.05,
    "SEK": 0.088,
    "NOK": 0.087,
    "DKK": 0.13,
    "SGD": 0.68,
    "HKD": 0.12,
    "NZD": 0.56,
    "THB": 0.026,
    "MXN": 0.054,
    "BRL": 0.18,
    "AED": 0.25,
}


class HotelSearchService:
    """
    Service for searching hotels across multiple providers.
    Supports: Amadeus (primary), Booking.com (via RapidAPI), mock data for testing.
    """

    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        self.hotelbeds_api_key = settings.hotelbeds_api_key if hasattr(settings, 'hotelbeds_api_key') else None
        self.hotelbeds_api_secret = settings.hotelbeds_api_secret if hasattr(settings, 'hotelbeds_api_secret') else None
        self.amadeus_api_key = settings.amadeus_api_key
        self.amadeus_api_secret = settings.amadeus_api_secret
        self.amadeus_access_token = None
        self.rapidapi_key = settings.booking_com_api_key if hasattr(settings, 'booking_com_api_key') else None

    def _convert_to_eur(self, amount: float, from_currency: str) -> float:
        """Convert amount from given currency to EUR"""
        if from_currency == "EUR":
            return amount

        rate = CURRENCY_RATES_TO_EUR.get(from_currency.upper())
        if not rate:
            logger.warning(f"No exchange rate for {from_currency}, using amount as-is")
            return amount

        converted = amount * rate
        logger.info(f"💱 Currency conversion: {amount:,.2f} {from_currency} = {converted:,.2f} EUR")
        return converted

    async def search_hotels(
        self,
        intent: TravelIntent,
        max_results: int = 20
    ) -> List[AccommodationOption]:
        """
        Search for hotels based on travel intent.
        Returns list of AccommodationOption objects.
        """
        if not intent.destination:
            logger.warning("Missing destination for hotel search")
            return []

        # Use mock data if explicitly requested
        if self.use_mock:
            logger.info("Using mock hotel data (explicitly requested)")
            return self._generate_mock_hotels(intent, max_results)

        # Try Hotelbeds first (best coverage and real addresses)
        if self.hotelbeds_api_key and self.hotelbeds_api_secret:
            try:
                logger.info("🔍 Trying Hotelbeds API...")
                hotels = await self._search_hotelbeds(intent, max_results)
                if hotels:
                    logger.info(f"✅ Hotelbeds success: Found {len(hotels)} hotels")
                    return hotels
                logger.warning("⚠️  Hotelbeds returned 0 hotels")
            except Exception as e:
                logger.warning(f"⚠️  Hotelbeds failed: {e}")

        # Fallback to Amadeus
        try:
            logger.info("🔍 Trying Amadeus Hotel Search...")
            hotels = await self._search_amadeus_hotels(intent, max_results)
            if hotels:
                logger.info(f"✅ Amadeus Hotels success: Found {len(hotels)} hotels")
                return hotels
            logger.warning("⚠️  Amadeus returned 0 hotels")
        except Exception as e:
            logger.warning(f"⚠️  Amadeus Hotels failed: {e}")

        # Fallback to Booking.com if available
        if self.rapidapi_key:
            logger.info("🔍 Falling back to Booking.com...")
            return await self._search_booking_com(intent, max_results)

        # Otherwise use mock data
        logger.warning("⚠️  No hotel API available, using mock data")
        return self._generate_mock_hotels(intent, max_results)

    async def _get_amadeus_token(self) -> str:
        """Get Amadeus API access token (cached)"""
        if self.amadeus_access_token:
            return self.amadeus_access_token

        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.amadeus_api_key,
            "client_secret": self.amadeus_api_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=10.0)
            response.raise_for_status()
            token_data = response.json()
            self.amadeus_access_token = token_data["access_token"]
            return self.amadeus_access_token

    def _get_city_iata_code(self, city: str) -> str:
        """Convert city name to IATA city code for hotel search"""
        # Strip country name if present (e.g., "Tokyo, Japan" -> "Tokyo")
        if ',' in city:
            city = city.split(',')[0].strip()

        # Common city mappings (IATA city codes)
        city_codes = {
            # Europe
            "paris": "PAR",
            "rome": "ROM",
            "barcelona": "BCN",
            "london": "LON",
            "amsterdam": "AMS",
            "berlin": "BER",
            "madrid": "MAD",
            "vienna": "VIE",
            "prague": "PRG",
            "budapest": "BUD",
            "lisbon": "LIS",
            "dublin": "DUB",
            "athens": "ATH",
            "copenhagen": "CPH",
            "stockholm": "STO",
            "oslo": "OSL",
            "helsinki": "HEL",
            "warsaw": "WAW",
            "brussels": "BRU",
            "milan": "MIL",
            "venice": "VCE",
            "florence": "FLR",
            "naples": "NAP",
            "zurich": "ZRH",
            "geneva": "GVA",

            # Asia
            "tokyo": "TYO",
            "kyoto": "KIX",  # Osaka/Kyoto region
            "osaka": "OSA",
            "bangkok": "BKK",
            "singapore": "SIN",
            "hong kong": "HKG",
            "dubai": "DXB",
            "mumbai": "BOM",
            "delhi": "DEL",
            "seoul": "SEL",
            "beijing": "BJS",
            "shanghai": "SHA",

            # Americas
            "new york": "NYC",
            "los angeles": "LAX",
            "san francisco": "SFO",
            "miami": "MIA",
            "chicago": "CHI",
            "boston": "BOS",
            "toronto": "YTO",
            "vancouver": "YVR",
            "mexico city": "MEX",
            "buenos aires": "BUE",
            "rio de janeiro": "RIO",
            "sao paulo": "SAO",

            # Oceania
            "sydney": "SYD",
            "melbourne": "MEL",
            "auckland": "AKL",

            # Africa
            "cape town": "CPT",
            "johannesburg": "JNB",
            "cairo": "CAI",
            "marrakech": "RAK",
        }

        city_lower = city.lower().strip()
        return city_codes.get(city_lower, city[:3].upper())

    def _get_hotelbeds_signature(self) -> tuple[str, str]:
        """Generate X-Signature header for Hotelbeds API"""
        timestamp = str(int(time.time()))
        signature_string = self.hotelbeds_api_key + self.hotelbeds_api_secret + timestamp
        signature = hashlib.sha256(signature_string.encode()).hexdigest()
        return signature, timestamp

    async def _search_hotelbeds(
        self,
        intent: TravelIntent,
        max_results: int = 20
    ) -> List[AccommodationOption]:
        """Search hotels using Hotelbeds API"""
        try:
            # Calculate nights
            if intent.departure_date and intent.return_date:
                nights = (intent.return_date - intent.departure_date).days
            else:
                nights = intent.duration_days or 7

            # Get signature
            signature, timestamp = self._get_hotelbeds_signature()

            headers = {
                "Api-key": self.hotelbeds_api_key,
                "X-Signature": signature,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            # Get IATA code for the city
            city_code = self._get_city_iata_code(intent.destination)

            # Hotelbeds uses specific destination codes
            search_payload = {
                "stay": {
                    "checkIn": intent.departure_date.isoformat() if intent.departure_date else None,
                    "checkOut": intent.return_date.isoformat() if intent.return_date else None
                },
                "occupancies": [
                    {
                        "rooms": 1,
                        "adults": intent.num_adults,
                        "children": intent.num_children
                    }
                ],
                "destination": {
                    "code": city_code  # Use IATA city code
                }
            }

            url = "https://api.test.hotelbeds.com/hotel-api/1.0/hotels"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=search_payload,
                    headers=headers,
                    timeout=20.0
                )
                response.raise_for_status()
                data = response.json()

                hotels = []
                for hotel_data in data.get("hotels", {}).get("hotels", [])[:max_results]:
                    try:
                        accommodation = self._parse_hotelbeds_hotel(hotel_data, intent, nights)
                        hotels.append(accommodation)
                    except Exception as e:
                        logger.error(f"Error parsing Hotelbeds hotel '{hotel_data.get('name', 'Unknown')}': {e}")
                        logger.debug(f"Hotel data: {hotel_data}")
                        continue

                logger.info(f"✅ Parsed {len(hotels)} hotels from Hotelbeds")
                return hotels

        except Exception as e:
            logger.error(f"❌ Hotelbeds search error: {e}")
            raise

    def _parse_hotelbeds_hotel(
        self,
        hotel_data: Dict,
        intent: TravelIntent,
        nights: int
    ) -> AccommodationOption:
        """Parse Hotelbeds hotel into AccommodationOption"""
        # Get room data
        rooms = hotel_data.get("rooms", [])
        if not rooms:
            raise ValueError("No rooms available")

        room = rooms[0]
        rates = room.get("rates", [])
        if not rates:
            raise ValueError("No rates available")

        rate = rates[0]

        # Price
        total_price_net = float(rate.get("net", 0))
        currency = rate.get("currency", "EUR")
        total_price = self._convert_to_eur(total_price_net, currency)
        price_per_night = total_price / nights if nights > 0 else total_price

        # Hotel details
        name = hotel_data.get("name", "Hotel")
        address = hotel_data.get("address", {})

        # Parse star rating (categoryName is string like "4 STARS" or "5 STARS")
        category_name = hotel_data.get("categoryName", "")
        rating = None
        if category_name:
            # Extract number from strings like "4 STARS", "5 STARS"
            import re
            match = re.search(r'(\d+)', str(category_name))
            if match:
                star_rating = int(match.group(1))
                # Convert 1-5 stars to 2.0-5.0 rating (5 stars = 5.0, 4 stars = 4.0, etc.)
                rating = float(star_rating) if 1 <= star_rating <= 5 else None

        # Amenities
        amenities = []
        for facility in hotel_data.get("facilities", [])[:8]:
            amenities.append(facility.get("description", ""))

        return AccommodationOption(
            name=name,
            type="hotel",
            address=address.get("content", ""),
            city=intent.destination or "",
            country=address.get("countryCode", ""),
            price_per_night=round(price_per_night, 2),
            total_price=round(total_price, 2),
            currency="EUR",
            rating=rating,
            review_count=None,
            amenities=amenities,
            room_type=room.get("name", "Standard"),
            check_in=intent.departure_date or date.today(),
            check_out=intent.return_date or date.today(),
            latitude=hotel_data.get("latitude"),
            longitude=hotel_data.get("longitude"),
            distance_to_center_km=None,
            booking_link=None,
            source="hotelbeds"
        )

    async def _search_amadeus_hotels(
        self,
        intent: TravelIntent,
        max_results: int = 20
    ) -> List[AccommodationOption]:
        """
        Search hotels using Amadeus Hotel Search API.
        Uses Hotel List + Hotel Offers APIs for comprehensive results.
        """
        try:
            token = await self._get_amadeus_token()
            headers = {"Authorization": f"Bearer {token}"}

            # Get city code
            city_code = self._get_city_iata_code(intent.destination)
            logger.info(f"🏨 Searching hotels in {intent.destination} (code: {city_code})")

            # Calculate nights
            if intent.departure_date and intent.return_date:
                nights = (intent.return_date - intent.departure_date).days
            else:
                nights = intent.duration_days or 7

            # Step 1: Search for hotels in the city
            search_url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
            search_params = {
                "cityCode": city_code,
                "radius": 20,  # 20km radius
                "radiusUnit": "KM",
                "hotelSource": "ALL"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url,
                    params=search_params,
                    headers=headers,
                    timeout=15.0
                )
                response.raise_for_status()
                hotels_data = response.json()

                hotel_ids = [h["hotelId"] for h in hotels_data.get("data", [])[:50]]

                if not hotel_ids:
                    logger.warning(f"No hotels found in {city_code}")
                    return []

                logger.info(f"Found {len(hotel_ids)} hotels, getting offers...")

                # Step 2: Get offers for these hotels
                offers_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
                offers_params = {
                    "hotelIds": ",".join(hotel_ids[:20]),  # Max 20 hotels per request
                    "adults": intent.num_adults,
                    "checkInDate": intent.departure_date.isoformat() if intent.departure_date else None,
                    "checkOutDate": intent.return_date.isoformat() if intent.return_date else None,
                    "roomQuantity": 1,
                    "currency": "EUR",
                    "bestRateOnly": "true"
                }

                response = await client.get(
                    offers_url,
                    params=offers_params,
                    headers=headers,
                    timeout=20.0
                )
                response.raise_for_status()
                offers_data = response.json()

                # Parse results
                hotels = []
                for hotel_offer in offers_data.get("data", []):
                    try:
                        accommodation = self._parse_amadeus_hotel(hotel_offer, intent, nights)
                        hotels.append(accommodation)
                    except Exception as e:
                        logger.error(f"Error parsing Amadeus hotel: {e}")
                        continue

                logger.info(f"✅ Parsed {len(hotels)} hotels with offers from Amadeus")
                return hotels[:max_results]

        except Exception as e:
            logger.error(f"❌ Amadeus Hotel Search error: {e}")
            raise

    def _parse_amadeus_hotel(
        self,
        hotel_data: Dict,
        intent: TravelIntent,
        nights: int
    ) -> AccommodationOption:
        """Parse Amadeus hotel offer into AccommodationOption"""
        hotel = hotel_data.get("hotel", {})
        offer = hotel_data.get("offers", [{}])[0]
        price_info = offer.get("price", {})

        # Get original price and currency
        original_currency = price_info.get("currency", "EUR")
        total_price_original = float(price_info.get("total", 0))

        # Convert to EUR if needed
        total_price = self._convert_to_eur(total_price_original, original_currency)
        price_per_night = total_price / nights if nights > 0 else total_price

        # Extract amenities
        amenities = []
        room = offer.get("room", {})
        if room.get("typeEstimated", {}).get("category"):
            amenities.append(room["typeEstimated"]["category"])
        if offer.get("policies", {}).get("cancellation"):
            amenities.append("Free Cancellation")

        # Get hotel details
        name = hotel.get("name", "Hotel")

        return AccommodationOption(
            name=name,
            type=hotel.get("type", "hotel"),
            address=hotel.get("address", {}).get("lines", [""])[0] if hotel.get("address") else "",
            city=intent.destination or "",
            country=hotel.get("address", {}).get("countryCode", ""),
            price_per_night=round(price_per_night, 2),
            total_price=round(total_price, 2),
            currency="EUR",  # Always EUR after conversion
            rating=hotel.get("rating", 3.5),  # Amadeus doesn't provide ratings in test API
            review_count=None,
            amenities=amenities,
            room_type=room.get("typeEstimated", {}).get("category", "Standard"),
            check_in=intent.departure_date or date.today(),
            check_out=intent.return_date or date.today(),
            latitude=hotel.get("latitude"),
            longitude=hotel.get("longitude"),
            distance_to_center_km=None,
            booking_link=f"https://www.amadeus.com/hotel/{hotel.get('hotelId')}",
            source="amadeus"
        )

    async def _search_booking_com(
        self,
        intent: TravelIntent,
        max_results: int
    ) -> List[AccommodationOption]:
        """
        Search Booking.com via RapidAPI.
        Docs: https://rapidapi.com/apidojo/api/booking
        """
        try:
            url = "https://booking-com.p.rapidapi.com/v1/hotels/search"

            params = {
                "dest_type": "city",
                "dest_id": intent.destination,  # In production, resolve city to dest_id
                "checkin_date": intent.departure_date.isoformat() if intent.departure_date else None,
                "checkout_date": intent.return_date.isoformat() if intent.return_date else None,
                "adults_number": intent.num_adults,
                "children_number": intent.num_children,
                "room_number": 1,  # Can infer from travelers
                "units": "metric",
                "currency": "EUR",
                "locale": "en-gb",
                "order_by": "popularity"
            }

            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                hotels = []
                for hotel in data.get('result', [])[:max_results]:
                    try:
                        accommodation = self._parse_booking_hotel(hotel, intent)
                        hotels.append(accommodation)
                    except Exception as e:
                        logger.error(f"Error parsing hotel: {e}")
                        continue

                logger.info(f"Found {len(hotels)} hotels from Booking.com")
                return hotels

        except Exception as e:
            logger.error(f"Booking.com API error: {e}")
            return self._generate_mock_hotels(intent, max_results)

    def _parse_booking_hotel(
        self,
        hotel: dict,
        intent: TravelIntent
    ) -> AccommodationOption:
        """Parse Booking.com hotel data into AccommodationOption"""
        # Calculate number of nights
        if intent.departure_date and intent.return_date:
            nights = (intent.return_date - intent.departure_date).days
        else:
            nights = intent.duration_days or 7

        price_per_night = float(hotel.get('min_total_price', 0)) / nights if nights > 0 else 0

        return AccommodationOption(
            name=hotel.get('hotel_name', 'Unknown Hotel'),
            type="hotel",
            address=hotel.get('address', ''),
            city=hotel.get('city', intent.destination or ''),
            country=hotel.get('country_trans', ''),
            price_per_night=price_per_night,
            total_price=float(hotel.get('min_total_price', 0)),
            currency="EUR",
            rating=float(hotel.get('review_score', 0)) / 2,  # Booking uses 0-10 scale
            review_count=hotel.get('review_nr', 0),
            amenities=self._extract_amenities(hotel),
            room_type=hotel.get('room_type', 'Standard'),
            check_in=intent.departure_date or date.today(),
            check_out=intent.return_date or date.today(),
            latitude=hotel.get('latitude'),
            longitude=hotel.get('longitude'),
            distance_to_center_km=hotel.get('distance', 0),
            booking_link=hotel.get('url'),
            source="booking.com"
        )

    def _extract_amenities(self, hotel: dict) -> List[str]:
        """Extract amenities from hotel data"""
        amenities = []
        facilities = hotel.get('hotel_facilities', '').split(',')
        for facility in facilities[:10]:  # Limit to top 10
            if facility.strip():
                amenities.append(facility.strip())
        return amenities

    def _generate_mock_hotels(
        self,
        intent: TravelIntent,
        max_results: int
    ) -> List[AccommodationOption]:
        """
        Generate mock hotel data for testing.
        Creates realistic-looking hotel options based on intent.
        """
        import random

        destination = intent.destination or "European City"
        nights = intent.duration_days or 7
        budget_per_night = (intent.total_budget * 0.4) / nights if intent.total_budget else 150

        hotel_templates = [
            {
                "name": f"Grand {destination} Hotel",
                "type": "hotel",
                "rating": 4.5,
                "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Gym", "Bar"],
                "style": "luxury"
            },
            {
                "name": f"{destination} Central Apartments",
                "type": "apartment",
                "rating": 4.2,
                "amenities": ["WiFi", "Kitchen", "Washing Machine", "City View"],
                "style": "apartment"
            },
            {
                "name": f"Budget Inn {destination}",
                "type": "hotel",
                "rating": 3.8,
                "amenities": ["WiFi", "Breakfast", "24h Reception"],
                "style": "budget"
            },
            {
                "name": f"{destination} Family Resort",
                "type": "resort",
                "rating": 4.6,
                "amenities": ["WiFi", "Kids Club", "Pool", "Animation", "Restaurant", "Beach Access"],
                "style": "family"
            },
            {
                "name": f"Boutique Hotel {destination}",
                "type": "hotel",
                "rating": 4.7,
                "amenities": ["WiFi", "Rooftop Bar", "Concierge", "Designer Rooms"],
                "style": "boutique"
            }
        ]

        mock_hotels = []
        for i in range(min(max_results, len(hotel_templates) * 2)):
            template = hotel_templates[i % len(hotel_templates)]

            # Generate price based on style and budget
            if template["style"] == "luxury":
                price_multiplier = random.uniform(1.5, 2.5)
            elif template["style"] == "budget":
                price_multiplier = random.uniform(0.5, 0.8)
            else:
                price_multiplier = random.uniform(0.9, 1.3)

            price_per_night = budget_per_night * price_multiplier
            total_price = price_per_night * nights

            mock_hotels.append(AccommodationOption(
                name=f"{template['name']} - {i+1}",
                type=template["type"],
                address=f"{random.randint(1, 999)} {destination} Street",
                city=destination,
                country="Mock Country",
                price_per_night=round(price_per_night, 2),
                total_price=round(total_price, 2),
                currency="EUR",
                rating=template["rating"] + random.uniform(-0.3, 0.2),
                review_count=random.randint(50, 1500),
                amenities=template["amenities"],
                room_type="Standard Room" if template["type"] == "hotel" else "Apartment",
                check_in=intent.departure_date or date.today(),
                check_out=intent.return_date or date.today(),
                latitude=random.uniform(40.0, 50.0),
                longitude=random.uniform(-5.0, 15.0),
                distance_to_center_km=round(random.uniform(0.5, 5.0), 1),
                booking_link=f"https://booking.com/mock-hotel-{i+1}",
                source="mock_data"
            ))

        # Sort by rating and price balance
        mock_hotels.sort(key=lambda h: h.rating - (h.price_per_night / 1000), reverse=True)

        logger.info(f"Generated {len(mock_hotels)} mock hotels")
        return mock_hotels
