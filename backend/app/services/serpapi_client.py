"""
SerpAPI Client for Google Flights
Scrapes Google Flights to get real-world flight data
"""
from datetime import date, datetime
from typing import List
from serpapi import GoogleSearch
from app.models.travel import FlightOption, FlightSegment, TravelIntent
from app.utils.config import settings
import logging

logger = logging.getLogger(__name__)


class SerpAPIFlightService:
    """
    Service for searching flights using SerpAPI (Google Flights scraper).
    This gives us the exact same results users see on Google Flights.
    """

    def __init__(self):
        self.api_key = settings.serpapi_key

    def search_flights(
        self,
        intent: TravelIntent,
        max_results: int = 10
    ) -> List[FlightOption]:
        """
        Search for flights using SerpAPI's Google Flights scraper.
        Returns list of FlightOption objects.
        """
        if not self.api_key:
            logger.warning("SerpAPI key not configured")
            return []

        if not intent.origin or not intent.destination:
            logger.warning("Missing origin or destination for flight search")
            return []

        if not intent.departure_date or not intent.return_date:
            logger.warning(f"Missing dates for flight search")
            return []

        # Get airport codes
        origin_code = self._get_airport_code(intent.origin)
        dest_code = self._get_airport_code(intent.destination)

        logger.info(f"🔍 SerpAPI searching: {intent.origin} ({origin_code}) -> {intent.destination} ({dest_code})")
        logger.info(f"Dates: {intent.departure_date} to {intent.return_date}")
        logger.info(f"Travelers: {intent.num_adults} adults, {intent.num_children} children")

        try:
            # Build SerpAPI parameters for Google Flights
            params = {
                "api_key": self.api_key,
                "engine": "google_flights",
                "departure_id": origin_code,
                "arrival_id": dest_code,
                "outbound_date": intent.departure_date.strftime("%Y-%m-%d"),
                "return_date": intent.return_date.strftime("%Y-%m-%d"),
                "adults": intent.num_adults,
                "currency": "EUR",
                "hl": "en",
            }

            # Add children if present
            if intent.num_children > 0:
                params["children"] = intent.num_children

            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()

            # Check for errors FIRST
            if 'error' in results:
                error_msg = results['error']
                logger.error(f"❌ SerpAPI Error: {error_msg}")
                if "run out of searches" in error_msg.lower():
                    logger.error("💳 SerpAPI quota exceeded. Please upgrade your plan or use Amadeus fallback.")
                raise Exception(f"SerpAPI Error: {error_msg}")

            # DEBUG: Log raw response
            logger.info(f"🔍 SerpAPI RAW RESPONSE KEYS: {results.keys()}")
            logger.info(f"🔍 Best flights count: {len(results.get('best_flights', []))}")
            logger.info(f"🔍 Other flights count: {len(results.get('other_flights', []))}")

            # Log search metadata
            if 'search_metadata' in results:
                logger.info(f"🔍 Search status: {results['search_metadata'].get('status')}")

            # DEBUG: Log full response for troubleshooting
            import json
            logger.debug(f"🔍 FULL SerpAPI RESPONSE: {json.dumps(results, indent=2, default=str)}")

            # Parse results
            flight_options = self._parse_results(results, intent)

            logger.info(f"✅ SerpAPI found {len(flight_options)} flight options")
            return flight_options[:max_results]

        except Exception as e:
            logger.error(f"SerpAPI error: {e}", exc_info=True)
            return []

    def _parse_results(self, results: dict, intent: TravelIntent) -> List[FlightOption]:
        """Parse SerpAPI results into FlightOption objects"""
        flight_options = []

        # Get best flights from results
        best_flights = results.get("best_flights", [])
        other_flights = results.get("other_flights", [])

        all_flights = best_flights + other_flights

        for flight_data in all_flights:
            try:
                # Parse flights - each flight has multiple segments
                flights = flight_data.get("flights", [])

                if len(flights) < 2:
                    continue  # Need both outbound and return

                # Outbound is first set of segments, return is second set
                # Find where return journey starts (when departure airport matches destination)
                outbound_segments = []
                return_segments = []

                is_return = False
                for segment in flights:
                    if not is_return and segment.get("departure_airport", {}).get("id") == self._get_airport_code(intent.origin):
                        is_return = True if outbound_segments else False

                    if is_return or (outbound_segments and segment.get("departure_airport", {}).get("id") != outbound_segments[-1].get("arrival_airport", {}).get("id")):
                        is_return = True

                    seg = self._parse_segment(segment)
                    if not is_return:
                        outbound_segments.append(seg)
                    else:
                        return_segments.append(seg)

                # If we couldn't split properly, try simpler approach
                if not return_segments:
                    mid_point = len(flights) // 2
                    outbound_segments = [self._parse_segment(seg) for seg in flights[:mid_point]]
                    return_segments = [self._parse_segment(seg) for seg in flights[mid_point:]]

                # Calculate total duration
                total_duration = sum(seg.duration_minutes for seg in outbound_segments + return_segments)

                # Count stops
                num_stops = (len(outbound_segments) - 1) + (len(return_segments) - 1)

                # Get price
                price = flight_data.get("price", 0)
                if isinstance(price, dict):
                    price = price.get("value", 0)

                flight_option = FlightOption(
                    outbound_segments=outbound_segments,
                    return_segments=return_segments,
                    total_price=float(price),
                    currency="EUR",
                    total_duration_minutes=total_duration,
                    number_of_stops=num_stops,
                    booking_link=flight_data.get("booking_token"),
                    source="google_flights"
                )
                flight_options.append(flight_option)

            except Exception as e:
                logger.error(f"Error parsing flight: {e}")
                continue

        return flight_options

    def _parse_segment(self, segment: dict) -> FlightSegment:
        """Parse a flight segment from SerpAPI"""
        # Parse departure and arrival times
        departure_time = segment.get("departure_airport", {}).get("time")
        arrival_time = segment.get("arrival_airport", {}).get("time")

        # Convert to datetime objects
        departure = datetime.fromisoformat(departure_time.replace("Z", "+00:00")) if departure_time else datetime.now()
        arrival = datetime.fromisoformat(arrival_time.replace("Z", "+00:00")) if arrival_time else datetime.now()

        # Parse duration
        duration_minutes = segment.get("duration", 0)

        return FlightSegment(
            origin=segment.get("departure_airport", {}).get("id", ""),
            destination=segment.get("arrival_airport", {}).get("id", ""),
            departure=departure,
            arrival=arrival,
            carrier=segment.get("airline", ""),
            flight_number=segment.get("flight_number", ""),
            duration_minutes=duration_minutes,
            aircraft=segment.get("airplane", ""),
            booking_class="economy"
        )

    def _get_airport_code(self, location: str) -> str:
        """
        Get airport code for a city.
        Uses same logic as Amadeus client for consistency.
        """
        # Strip country if present
        if ',' in location:
            location = location.split(',')[0].strip()

        common_codes = {
            # Europe
            "copenhagen": "CPH",
            "london": "LON",
            "paris": "PAR",
            "rome": "ROM",
            "barcelona": "BCN",
            "madrid": "MAD",
            "berlin": "BER",
            "amsterdam": "AMS",

            # Japan
            "kyoto": "KIX",
            "tokyo": "TYO",
            "osaka": "KIX",

            # Other major cities
            "new york": "NYC",
            "los angeles": "LAX",
            "dubai": "DXB",
            "singapore": "SIN",
        }

        location_lower = location.lower().strip()

        # If already a code, return as-is
        if len(location) == 3 and location.isalpha():
            return location.upper()

        return common_codes.get(location_lower, location.upper()[:3])
