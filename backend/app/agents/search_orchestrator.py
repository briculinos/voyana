"""
Search Orchestrator Agent
Coordinates parallel searches across flights, hotels, and activities.
Optimizes for cost, time, and quality.
"""
import asyncio
import logging
from typing import List
from app.models.travel import AgentState, FlightOption, AccommodationOption
from app.services.serpapi_client import SerpAPIFlightService
from app.services.amadeus_client import AmadeusFlightService
from app.services.hotel_client import HotelSearchService
from app.utils.config import settings

logger = logging.getLogger(__name__)


class SearchOrchestratorAgent:
    """
    Agent that orchestrates parallel searches across multiple travel APIs.
    Implements multi-objective optimization (cost, time, quality).
    """

    def __init__(self, use_mock_hotels: bool = False):
        self.serpapi_service = SerpAPIFlightService()
        self.amadeus_service = AmadeusFlightService()
        self.hotel_service = HotelSearchService(use_mock=use_mock_hotels)

    async def search(self, state: AgentState) -> AgentState:
        """
        Main agent function called by LangGraph.
        Performs parallel searches and updates state.
        """
        if not state.parsed_intent:
            error_msg = "Search Orchestrator: No parsed intent found"
            logger.error(error_msg)
            state.errors.append(error_msg)
            state.agent_messages.append(error_msg)
            return state

        intent = state.parsed_intent

        # DEBUG: Log the intent details
        logger.info(f"=" * 80)
        logger.info(f"SEARCH ORCHESTRATOR STARTING")
        logger.info(f"=" * 80)
        logger.info(f"📍 Origin: {intent.origin}")
        logger.info(f"📍 Destination: {intent.destination}")
        logger.info(f"📅 Departure: {intent.departure_date}")
        logger.info(f"📅 Return: {intent.return_date}")
        logger.info(f"👥 Adults: {intent.num_adults}, Children: {intent.num_children}")
        logger.info(f"💰 Budget: {intent.total_budget}")
        logger.info(f"=" * 80)

        state.agent_messages.append(
            f"Search Orchestrator: Searching for flights and hotels..."
        )

        try:
            # Run searches in parallel
            flight_task = asyncio.create_task(
                self._search_flights_async(intent)
            )
            hotel_task = asyncio.create_task(
                self.hotel_service.search_hotels(intent, max_results=20)
            )

            # Wait for both to complete
            flight_results, hotel_results = await asyncio.gather(
                flight_task,
                hotel_task,
                return_exceptions=True
            )

            # Handle results
            if isinstance(flight_results, Exception):
                logger.error(f"❌ Flight search failed: {flight_results}")
                state.errors.append(f"Flight search error: {str(flight_results)}")
                state.flight_options = []
            else:
                logger.info(f"✅ Raw flight results: {len(flight_results)} flights before optimization")
                state.flight_options = flight_results

            if isinstance(hotel_results, Exception):
                logger.error(f"❌ Hotel search failed: {hotel_results}")
                state.errors.append(f"Hotel search error: {str(hotel_results)}")
                state.accommodation_options = []
            else:
                logger.info(f"✅ Raw hotel results: {len(hotel_results)} hotels before optimization")
                state.accommodation_options = hotel_results

            # Filter and optimize results
            state.flight_options = self._optimize_flights(
                state.flight_options,
                intent.total_budget
            )
            logger.info(f"✅ After optimization: {len(state.flight_options)} flights")

            state.accommodation_options = self._optimize_hotels(
                state.accommodation_options,
                intent.total_budget,
                intent.travel_style.value if intent.travel_style else "balanced"
            )
            logger.info(f"✅ After optimization: {len(state.accommodation_options)} hotels")

            logger.info(f"=" * 80)
            logger.info(f"SEARCH ORCHESTRATOR COMPLETE")
            logger.info(f"Final results: {len(state.flight_options)} flights, {len(state.accommodation_options)} hotels")
            logger.info(f"=" * 80)

            state.agent_messages.append(
                f"Search Orchestrator: Found {len(state.flight_options)} flights "
                f"and {len(state.accommodation_options)} hotels"
            )
            state.current_step = "search_complete"

        except Exception as e:
            error_msg = f"Search Orchestrator Error: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            state.agent_messages.append(error_msg)

        return state

    async def _search_flights_async(self, intent) -> List[FlightOption]:
        """
        Async wrapper for flight search with fallback strategy:
        1. Try SerpAPI (Google Flights scraper) - most reliable
        2. Fall back to Amadeus if SerpAPI fails
        """
        flights = []

        # Try SerpAPI first (Google Flights)
        try:
            logger.info("🔍 Trying SerpAPI (Google Flights)...")
            flights = await asyncio.to_thread(
                self.serpapi_service.search_flights,
                intent,
                max_results=15
            )
            if flights:
                logger.info(f"✅ SerpAPI success: Found {len(flights)} flights")
                return flights
            logger.warning("⚠️  SerpAPI returned 0 flights, trying Amadeus...")
        except Exception as e:
            logger.warning(f"⚠️  SerpAPI failed: {e}, trying Amadeus...")

        # Fallback to Amadeus
        try:
            logger.info("🔍 Trying Amadeus...")
            flights = await asyncio.to_thread(
                self.amadeus_service.search_flights,
                intent,
                max_results=15
            )
            if flights:
                logger.info(f"✅ Amadeus success: Found {len(flights)} flights")
            else:
                logger.error("❌ Both SerpAPI and Amadeus returned 0 flights")
        except Exception as e:
            logger.error(f"❌ Amadeus also failed: {e}")

        return flights

    def _optimize_flights(
        self,
        flights: List[FlightOption],
        budget: float | None
    ) -> List[FlightOption]:
        """
        Multi-objective optimization for flights.
        Balances cost, duration, and number of stops.
        """
        if not flights:
            return []

        # Filter by budget if specified
        if budget:
            # Assume 40% of budget for flights
            max_flight_cost = budget * 0.4
            logger.info(f"💰 Budget filter: Max flight cost = {max_flight_cost} EUR (40% of {budget})")
            flights_before_count = len(flights)
            cheapest_price = min(f.total_price for f in flights) if flights else 0
            flights = [f for f in flights if f.total_price <= max_flight_cost]
            logger.info(f"💰 Budget filtered: {flights_before_count} -> {len(flights)} flights (cheapest: {cheapest_price} EUR)")

            if not flights:
                logger.warning(f"⚠️  All flights filtered out by budget! Need {cheapest_price} EUR but budget allows {max_flight_cost} EUR")
                return []

        # Score each flight
        def score_flight(flight: FlightOption) -> float:
            # Normalize price (lower is better)
            price_score = 1 - (flight.total_price / max(f.total_price for f in flights))

            # Normalize duration (shorter is better)
            duration_score = 1 - (flight.total_duration_minutes / max(f.total_duration_minutes for f in flights))

            # Stops penalty (fewer is better)
            stops_score = 1 - (flight.number_of_stops / 3)  # 3+ stops = 0 score

            # Weighted combination
            return (price_score * 0.5) + (duration_score * 0.3) + (stops_score * 0.2)

        # Sort by score
        flights_with_scores = [(f, score_flight(f)) for f in flights]
        flights_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top options (keep variety)
        return [f for f, _ in flights_with_scores[:10]]

    def _optimize_hotels(
        self,
        hotels: List[AccommodationOption],
        budget: float | None,
        style: str
    ) -> List[AccommodationOption]:
        """
        Multi-objective optimization for hotels.
        Balances cost, rating, location, and style match.
        """
        if not hotels:
            return []

        # Filter by budget if specified
        if budget:
            # Assume 40% of budget for accommodation
            max_hotel_budget = budget * 0.4
            hotels = [h for h in hotels if h.total_price <= max_hotel_budget]

        # Score each hotel
        def score_hotel(hotel: AccommodationOption) -> float:
            # Normalize price (lower is better for budget style, higher OK for luxury)
            max_price = max(h.total_price for h in hotels) or 1
            if style in ["budget", "backpacker"]:
                price_score = 1 - (hotel.total_price / max_price)
            elif style in ["luxury", "comfort"]:
                price_score = 0.5  # Neutral
            else:
                price_score = 0.7 - (hotel.total_price / max_price) * 0.4

            # Rating score (higher is better)
            rating_score = (hotel.rating or 0) / 5.0

            # Location score (closer to center is better)
            if hotel.distance_to_center_km:
                location_score = max(0, 1 - (hotel.distance_to_center_km / 10))
            else:
                location_score = 0.5

            # Style match bonus
            style_bonus = 0
            if style == "luxury" and hotel.rating and hotel.rating >= 4.5:
                style_bonus = 0.2
            elif style == "family" and "Kids Club" in hotel.amenities:
                style_bonus = 0.2
            elif style == "budget" and hotel.price_per_night < 80:
                style_bonus = 0.2

            # Weighted combination
            return (
                price_score * 0.35 +
                rating_score * 0.35 +
                location_score * 0.2 +
                style_bonus * 0.1
            )

        # Sort by score
        hotels_with_scores = [(h, score_hotel(h)) for h in hotels]
        hotels_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top options with variety (different price points)
        selected_hotels = []
        price_ranges = {"low": [], "mid": [], "high": []}

        for hotel, score in hotels_with_scores:
            if hotel.price_per_night < 100:
                price_ranges["low"].append(hotel)
            elif hotel.price_per_night < 200:
                price_ranges["mid"].append(hotel)
            else:
                price_ranges["high"].append(hotel)

        # Take best from each range
        selected_hotels.extend(price_ranges["low"][:4])
        selected_hotels.extend(price_ranges["mid"][:4])
        selected_hotels.extend(price_ranges["high"][:2])

        return selected_hotels[:15]


# Standalone async function for LangGraph node
async def search_node(state: AgentState) -> AgentState:
    """LangGraph node wrapper for Search Orchestrator"""
    # Use real APIs (Amadeus hotels). Mock mode disabled since we have Amadeus working.
    agent = SearchOrchestratorAgent(use_mock_hotels=False)
    return await agent.search(state)
