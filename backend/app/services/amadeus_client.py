"""
Amadeus API Client for flight searches.
Documentation: https://developers.amadeus.com/
"""
from datetime import date, datetime
from typing import List, Optional
from amadeus import Client, ResponseError
from app.models.travel import FlightOption, FlightSegment, TravelIntent
from app.utils.config import settings
import logging

logger = logging.getLogger(__name__)


class AmadeusFlightService:
    """
    Service for searching flights using Amadeus API.
    Provides free tier access to flight search and pricing.
    """

    def __init__(self):
        self.client = Client(
            client_id=settings.amadeus_api_key,
            client_secret=settings.amadeus_api_secret
        )

    def search_flights(
        self,
        intent: TravelIntent,
        max_results: int = 10
    ) -> List[FlightOption]:
        """
        Search for flights based on travel intent.
        Tries multiple airports if first attempt returns no results.
        Returns list of FlightOption objects.
        """
        if not intent.origin or not intent.destination:
            logger.warning("Missing origin or destination for flight search")
            return []

        if not intent.departure_date or not intent.return_date:
            logger.warning(f"Missing dates for flight search - departure: {intent.departure_date}, return: {intent.return_date}")
            return []

        # Get primary IATA codes
        origin_code = self._get_iata_code(intent.origin)
        dest_code = self._get_iata_code(intent.destination)

        # Get alternative airports
        origin_alternatives = self._get_alternative_airports(intent.origin, origin_code)
        dest_alternatives = self._get_alternative_airports(intent.destination, dest_code)

        logger.info(f"Searching flights: {intent.origin} ({origin_code}) -> {intent.destination} ({dest_code})")
        logger.info(f"Alternative origins: {origin_alternatives}")
        logger.info(f"Alternative destinations: {dest_alternatives}")
        logger.info(f"Dates: {intent.departure_date.isoformat()} to {intent.return_date.isoformat()}")
        logger.info(f"Travelers: {intent.num_adults} adults, {intent.num_children} children")

        # Try primary route first
        flight_options = self._search_route(
            origin_code, dest_code, intent, max_results
        )

        if flight_options:
            logger.info(f"✅ Found {len(flight_options)} flights on primary route {origin_code} -> {dest_code}")
            return flight_options

        # Try alternative destination airports
        for alt_dest in dest_alternatives:
            logger.info(f"Trying alternative destination: {origin_code} -> {alt_dest}")
            flight_options = self._search_route(
                origin_code, alt_dest, intent, max_results
            )
            if flight_options:
                logger.info(f"✅ Found {len(flight_options)} flights using alternative destination {alt_dest}")
                return flight_options

        # Try alternative origin airports
        for alt_origin in origin_alternatives:
            logger.info(f"Trying alternative origin: {alt_origin} -> {dest_code}")
            flight_options = self._search_route(
                alt_origin, dest_code, intent, max_results
            )
            if flight_options:
                logger.info(f"✅ Found {len(flight_options)} flights using alternative origin {alt_origin}")
                return flight_options

        # Try combinations of alternative airports
        for alt_origin in origin_alternatives[:2]:  # Limit to avoid too many requests
            for alt_dest in dest_alternatives[:2]:
                logger.info(f"Trying alternative combo: {alt_origin} -> {alt_dest}")
                flight_options = self._search_route(
                    alt_origin, alt_dest, intent, max_results
                )
                if flight_options:
                    logger.info(f"✅ Found {len(flight_options)} flights on {alt_origin} -> {alt_dest}")
                    return flight_options

        logger.error(f"❌ No flights found after trying all airport combinations")
        return []

    def _search_route(
        self,
        origin_code: str,
        dest_code: str,
        intent: TravelIntent,
        max_results: int
    ) -> List[FlightOption]:
        """
        Search for flights on a specific route.
        Returns empty list if no flights found.
        """
        try:
            # Build search parameters
            search_params = {
                'originLocationCode': origin_code,
                'destinationLocationCode': dest_code,
                'departureDate': intent.departure_date.isoformat(),
                'returnDate': intent.return_date.isoformat(),
                'adults': intent.num_adults,
                'max': max_results,
                'currencyCode': 'EUR'
            }

            # Only include children parameter if there are children
            if intent.num_children > 0:
                search_params['children'] = intent.num_children

            # Search for round-trip flights
            response = self.client.shopping.flight_offers_search.get(**search_params)

            # Parse response into FlightOption objects
            flight_options = []
            for offer in response.data:
                try:
                    flight_option = self._parse_flight_offer(offer)
                    flight_options.append(flight_option)
                except Exception as e:
                    logger.error(f"Error parsing flight offer: {e}")
                    continue

            return flight_options

        except ResponseError as error:
            logger.warning(f"No flights on {origin_code} -> {dest_code}: {error.response.status_code}")
            # Always log error details to diagnose issues
            logger.error(f"Error details: {error.response.body}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching {origin_code} -> {dest_code}: {e}")
            return []

    def _get_alternative_airports(self, city: str, primary_code: str) -> List[str]:
        """
        Get alternative airport codes for a city.
        Returns list of alternative IATA codes to try.
        """
        # Strip country if present
        if ',' in city:
            city = city.split(',')[0].strip()

        city_lower = city.lower().strip()

        # Map cities to alternative airports
        alternatives = {
            # Japan - multiple airport options
            "kyoto": ["OSA", "ITM", "UKB"],  # Osaka region: Kansai, Itami, Kobe
            "osaka": ["ITM", "UKB"],  # Also try Itami and Kobe besides Kansai
            "tokyo": ["NRT", "HND"],  # Narita and Haneda

            # Europe - cities with multiple airports
            "london": ["LHR", "LGW", "STN", "LTN"],  # Heathrow, Gatwick, Stansted, Luton
            "paris": ["CDG", "ORY"],  # Charles de Gaulle, Orly
            "rome": ["FCO", "CIA"],  # Fiumicino, Ciampino
            "milan": ["MXP", "LIN", "BGY"],  # Malpensa, Linate, Bergamo
            "barcelona": ["BCN", "GRO"],  # El Prat, Girona

            # North America
            "new york": ["JFK", "EWR", "LGA"],  # JFK, Newark, LaGuardia
            "los angeles": ["LAX", "BUR", "ONT"],
            "chicago": ["ORD", "MDW"],
            "san francisco": ["SFO", "OAK", "SJC"],

            # Asia
            "bangkok": ["BKK", "DMK"],  # Suvarnabhumi, Don Mueang
            "seoul": ["ICN", "GMP"],  # Incheon, Gimpo
            "shanghai": ["PVG", "SHA"],  # Pudong, Hongqiao
            "beijing": ["PEK", "PKX"],  # Capital, Daxing
        }

        return alternatives.get(city_lower, [])

    def _parse_flight_offer(self, offer: dict) -> FlightOption:
        """Parse Amadeus flight offer into FlightOption model"""
        itineraries = offer['itineraries']
        price = offer['price']

        # Parse outbound (first itinerary)
        outbound_segments = self._parse_segments(itineraries[0]['segments'])

        # Parse return (second itinerary)
        return_segments = self._parse_segments(itineraries[1]['segments'])

        # Calculate total duration
        total_duration = sum(
            seg.duration_minutes for seg in outbound_segments + return_segments
        )

        # Count stops
        num_stops = (len(outbound_segments) - 1) + (len(return_segments) - 1)

        return FlightOption(
            outbound_segments=outbound_segments,
            return_segments=return_segments,
            total_price=float(price['total']),
            currency=price['currency'],
            total_duration_minutes=total_duration,
            number_of_stops=num_stops,
            booking_link=None,  # Amadeus doesn't provide direct booking links
            source="amadeus"
        )

    def _parse_segments(self, segments: List[dict]) -> List[FlightSegment]:
        """Parse flight segments from Amadeus response"""
        parsed_segments = []

        for segment in segments:
            departure = datetime.fromisoformat(segment['departure']['at'].replace('Z', '+00:00'))
            arrival = datetime.fromisoformat(segment['arrival']['at'].replace('Z', '+00:00'))

            duration_str = segment['duration']  # Format: PT2H30M
            duration_minutes = self._parse_duration(duration_str)

            parsed_segments.append(FlightSegment(
                origin=segment['departure']['iataCode'],
                destination=segment['arrival']['iataCode'],
                departure=departure,
                arrival=arrival,
                carrier=segment['carrierCode'],
                flight_number=segment['number'],
                duration_minutes=duration_minutes,
                aircraft=segment.get('aircraft', {}).get('code'),
                booking_class=segment.get('cabin', 'economy').lower()
            ))

        return parsed_segments

    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration (PT2H30M) to minutes"""
        import re
        hours = 0
        minutes = 0

        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))

        minute_match = re.search(r'(\d+)M', duration_str)
        if minute_match:
            minutes = int(minute_match.group(1))

        return hours * 60 + minutes

    def _get_iata_code(self, location: str) -> str:
        """
        Convert city name to IATA code.
        In production, use a proper geocoding service or IATA lookup.
        For MVP, handle common cases.
        """
        # Strip country names (e.g., "Rome, Italy" -> "Rome")
        if ',' in location:
            location = location.split(',')[0].strip()

        common_codes = {
            # Major European Cities
            "london": "LON",
            "paris": "PAR",
            "rome": "ROM",
            "barcelona": "BCN",
            "madrid": "MAD",
            "berlin": "BER",
            "amsterdam": "AMS",
            "lisbon": "LIS",
            "copenhagen": "CPH",
            "stockholm": "STO",
            "oslo": "OSL",
            "helsinki": "HEL",
            "vienna": "VIE",
            "prague": "PRG",
            "budapest": "BUD",
            "warsaw": "WAW",
            "dublin": "DUB",
            "athens": "ATH",
            "istanbul": "IST",

            # Beach Destinations
            "nice": "NCE",
            "cannes": "NCE",  # Uses Nice airport
            "valencia": "VLC",
            "malaga": "AGP",
            "alicante": "ALC",
            "palma": "PMI",
            "ibiza": "IBZ",
            "mykonos": "JMK",
            "santorini": "JTR",
            "split": "SPU",
            "dubrovnik": "DBV",
            "faro": "FAO",
            "porto": "OPO",

            # Additional European
            "milan": "MIL",
            "venice": "VCE",
            "florence": "FLR",
            "naples": "NAP",
            "zurich": "ZRH",
            "geneva": "GVA",
            "brussels": "BRU",
            "lyon": "LYS",
            "marseille": "MRS",
            "edinburgh": "EDI",
            "manchester": "MAN",
            "munich": "MUC",
            "frankfurt": "FRA",
            "hamburg": "HAM",

            # International
            "new york": "NYC",
            "los angeles": "LAX",
            "san francisco": "SFO",
            "chicago": "CHI",
            "miami": "MIA",
            "orlando": "MCO",
            "las vegas": "LAS",

            # Japan
            "tokyo": "TYO",
            "kyoto": "KIX",  # Uses Osaka Kansai International Airport
            "osaka": "KIX",  # Kansai International Airport
            "yokohama": "TYO",  # Uses Tokyo airports
            "nagoya": "NGO",
            "sapporo": "SPK",
            "fukuoka": "FUK",
            "nara": "KIX",  # Uses Osaka Kansai (close to Kyoto)
            "nagano": "TYO",  # Route through Tokyo (no international flights to Nagano)

            # Other Asia-Pacific
            "dubai": "DXB",
            "singapore": "SIN",
            "hong kong": "HKG",
            "bangkok": "BKK",
            "bali": "DPS",
            "phuket": "HKT",
            "seoul": "SEL",
            "beijing": "BJS",
            "shanghai": "SHA",
            "delhi": "DEL",
            "mumbai": "BOM",
            "sydney": "SYD",
            "melbourne": "MEL",

            # Americas
            "cancun": "CUN",
            "mexico city": "MEX",
            "rio de janeiro": "RIO",
            "sao paulo": "SAO",
            "buenos aires": "BUE",
            "toronto": "YTO",
            "vancouver": "YVR",
            "montreal": "YMQ",

            # Canary Islands
            "tenerife": "TCI",
            "gran canaria": "LPA",
            "lanzarote": "ACE",

            # Small cities without international airports (route through hubs)
            "takayama": "TYO",  # Japan - route through Tokyo
            "hakone": "TYO",  # Japan - route through Tokyo
            "nikko": "TYO",  # Japan - route through Tokyo
            "kanazawa": "TYO",  # Japan - route through Tokyo
            "kobe": "KIX",  # Japan - route through Osaka
            "siena": "ROM",  # Italy - route through Rome or Florence
            "assisi": "ROM",  # Italy - route through Rome
            "verona": "MIL",  # Italy - route through Milan
            "bologna": "MIL",  # Italy - route through Milan
            "cinque terre": "MIL",  # Italy - route through Milan
            "positano": "NAP",  # Italy - route through Naples
            "granada": "MAD",  # Spain - route through Madrid
            "san sebastian": "MAD",  # Spain - route through Madrid
            "seville": "MAD",  # Spain - route through Madrid
            "tours": "PAR",  # France - route through Paris
            "avignon": "PAR",  # France - route through Paris
            "annecy": "PAR",  # France - route through Paris
            "salzburg": "VIE",  # Austria - route through Vienna
            "innsbruck": "VIE",  # Austria - route through Vienna
        }

        location_lower = location.lower().strip()

        # If already an IATA code (3 letters), return as-is
        if len(location) == 3 and location.isalpha():
            return location.upper()

        # Look up in common codes
        return common_codes.get(location_lower, location.upper()[:3])

    def get_airport_suggestions(self, query: str, max_results: int = 5) -> List[dict]:
        """
        Get airport suggestions for autocomplete.
        Useful for frontend.
        """
        try:
            response = self.client.reference_data.locations.get(
                keyword=query,
                subType="AIRPORT",
                page={'limit': max_results}
            )

            return [
                {
                    "iata_code": loc['iataCode'],
                    "name": loc['name'],
                    "city": loc['address']['cityName'],
                    "country": loc['address']['countryName']
                }
                for loc in response.data
            ]
        except ResponseError as error:
            logger.error(f"Airport search error: {error}")
            return []
