"""
Taste Profiler Agent
Scores travel options based on user's historical preferences and taste profile.
For MVP: Uses simple heuristics. Phase 2 will add vector embeddings.
"""
import logging
from typing import Dict, Any, List
from app.models.travel import (
    AgentState,
    FlightOption,
    AccommodationOption,
    TravelIntent
)

logger = logging.getLogger(__name__)


class TasteProfilerAgent:
    """
    Agent that evaluates options against user's taste profile.
    Learns from past trips and preferences to personalize recommendations.
    """

    def __init__(self):
        pass

    def profile(self, state: AgentState) -> AgentState:
        """
        Main agent function called by LangGraph.
        Scores all options based on user taste.
        """
        try:
            state.agent_messages.append(
                "Taste Profiler: Analyzing your preferences..."
            )

            # Get or create user taste profile
            taste_profile = state.user_taste_profile or self._create_default_profile(
                state.parsed_intent
            )

            # Score flights
            scored_flights = []
            for flight in state.flight_options:
                score = self._score_flight(flight, taste_profile, state.parsed_intent)
                scored_flights.append((flight, score))

            # Sort by taste score and keep top options
            scored_flights.sort(key=lambda x: x[1], reverse=True)
            state.flight_options = [f for f, _ in scored_flights[:8]]

            # Score hotels
            scored_hotels = []
            for hotel in state.accommodation_options:
                score = self._score_hotel(hotel, taste_profile, state.parsed_intent)
                scored_hotels.append((hotel, score))

            # Sort by taste score and keep diverse options
            scored_hotels.sort(key=lambda x: x[1], reverse=True)
            state.accommodation_options = self._select_diverse_hotels(scored_hotels)

            state.agent_messages.append(
                f"Taste Profiler: Ranked options based on your preferences"
            )
            state.current_step = "taste_profiled"

        except Exception as e:
            error_msg = f"Taste Profiler Error: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            state.agent_messages.append(error_msg)

        return state

    def _create_default_profile(self, intent: TravelIntent | None) -> Dict[str, Any]:
        """
        Create default taste profile from current intent.
        In production, this would load from database and merge with intent.
        """
        if not intent:
            return self._get_neutral_profile()

        profile = {
            "preferred_styles": [intent.travel_style.value] if intent.travel_style else ["balanced"],
            "budget_consciousness": self._infer_budget_consciousness(intent),
            "time_sensitivity": "balanced",  # prefer faster vs. cheaper flights
            "comfort_level": self._infer_comfort_level(intent),
            "accommodation_preferences": intent.accommodation_type or ["hotel"],
            "interests": intent.interests or [],
            "past_destinations": [],
            "preferred_airlines": [],
            "preferred_hotel_chains": [],
            "family_friendly": intent.num_children > 0,
        }

        return profile

    def _get_neutral_profile(self) -> Dict[str, Any]:
        """Neutral profile for users without history"""
        return {
            "preferred_styles": ["balanced"],
            "budget_consciousness": "moderate",
            "time_sensitivity": "balanced",
            "comfort_level": "moderate",
            "accommodation_preferences": ["hotel"],
            "interests": [],
            "past_destinations": [],
            "preferred_airlines": [],
            "preferred_hotel_chains": [],
            "family_friendly": False,
        }

    def _infer_budget_consciousness(self, intent: TravelIntent) -> str:
        """Infer how budget-conscious the user is"""
        if not intent.total_budget:
            return "moderate"

        # Simple heuristic: budget per person per day
        days = intent.duration_days or 7
        travelers = intent.num_adults + intent.num_children
        budget_per_person_per_day = intent.total_budget / (days * travelers) if travelers > 0 else 0

        if budget_per_person_per_day < 100:
            return "high"  # Very budget-conscious
        elif budget_per_person_per_day > 300:
            return "low"  # Luxury traveler
        else:
            return "moderate"

    def _infer_comfort_level(self, intent: TravelIntent) -> str:
        """Infer desired comfort level"""
        if intent.travel_style.value in ["luxury", "relaxed"]:
            return "high"
        elif intent.travel_style.value in ["adventure", "budget"]:
            return "low"
        else:
            return "moderate"

    def _score_flight(
        self,
        flight: FlightOption,
        profile: Dict[str, Any],
        intent: TravelIntent | None
    ) -> float:
        """
        Score a flight option based on taste profile.
        Returns score 0-1 (higher is better match).
        """
        score = 0.5  # Start with neutral

        # Time sensitivity
        if profile["time_sensitivity"] == "high":
            # Penalize long flights and connections
            if flight.number_of_stops == 0:
                score += 0.3
            elif flight.number_of_stops == 1:
                score += 0.1
            else:
                score -= 0.1
        elif profile["time_sensitivity"] == "low":
            # Don't mind connections if price is good
            if flight.number_of_stops >= 1:
                score += 0.1

        # Budget consciousness
        if intent and intent.total_budget:
            price_ratio = flight.total_price / (intent.total_budget * 0.4)
            if profile["budget_consciousness"] == "high":
                # Prefer cheaper flights
                score += max(0, 0.3 - price_ratio * 0.3)
            elif profile["budget_consciousness"] == "low":
                # OK with spending more for quality
                score += 0.1

        # Comfort (booking class preference)
        if profile["comfort_level"] == "high" and flight.outbound_segments[0].booking_class != "economy":
            score += 0.2

        # Preferred airlines
        carriers = set(seg.carrier for seg in flight.outbound_segments + flight.return_segments)
        if profile["preferred_airlines"]:
            if any(carrier in profile["preferred_airlines"] for carrier in carriers):
                score += 0.15

        return min(1.0, max(0.0, score))

    def _score_hotel(
        self,
        hotel: AccommodationOption,
        profile: Dict[str, Any],
        intent: TravelIntent | None
    ) -> float:
        """
        Score a hotel option based on taste profile.
        Returns score 0-1 (higher is better match).
        """
        score = 0.5  # Start with neutral

        # Type preference
        if hotel.type in profile["accommodation_preferences"]:
            score += 0.2

        # Family-friendly
        if profile["family_friendly"]:
            family_amenities = ["Kids Club", "Pool", "Family Room", "Playground"]
            if any(amenity in hotel.amenities for amenity in family_amenities):
                score += 0.2

        # Comfort level
        if profile["comfort_level"] == "high":
            if hotel.rating and hotel.rating >= 4.5:
                score += 0.2
            luxury_amenities = ["Spa", "Concierge", "Pool", "Restaurant"]
            if sum(1 for amenity in luxury_amenities if amenity in hotel.amenities) >= 2:
                score += 0.1
        elif profile["comfort_level"] == "low":
            # Budget travelers care less about amenities
            if hotel.price_per_night < 100:
                score += 0.15

        # Budget consciousness
        if intent and intent.total_budget:
            price_ratio = hotel.total_price / (intent.total_budget * 0.4)
            if profile["budget_consciousness"] == "high":
                score += max(0, 0.3 - price_ratio * 0.3)

        # Rating boost
        if hotel.rating:
            score += (hotel.rating / 5.0) * 0.15

        # Location (closer to center generally preferred)
        if hotel.distance_to_center_km and hotel.distance_to_center_km < 2:
            score += 0.1

        return min(1.0, max(0.0, score))

    def _select_diverse_hotels(
        self,
        scored_hotels: List[tuple],
        max_results: int = 12
    ) -> List[AccommodationOption]:
        """
        Select diverse set of hotels across different types and price points.
        """
        selected = []
        types_seen = []
        price_buckets = {"low": 0, "mid": 0, "high": 0}

        for hotel, score in scored_hotels:
            if len(selected) >= max_results:
                break

            # Determine price bucket
            if hotel.price_per_night < 100:
                bucket = "low"
            elif hotel.price_per_night < 200:
                bucket = "mid"
            else:
                bucket = "high"

            # Ensure diversity
            if price_buckets[bucket] < 4 and types_seen.count(hotel.type) < 3:
                selected.append(hotel)
                types_seen.append(hotel.type)
                price_buckets[bucket] += 1

        # Fill remaining slots if needed
        remaining = max_results - len(selected)
        if remaining > 0:
            for hotel, score in scored_hotels:
                if hotel not in selected:
                    selected.append(hotel)
                    remaining -= 1
                    if remaining == 0:
                        break

        return selected


# Standalone function for LangGraph node
def taste_profile_node(state: AgentState) -> AgentState:
    """LangGraph node wrapper for Taste Profiler"""
    agent = TasteProfilerAgent()
    return agent.profile(state)
