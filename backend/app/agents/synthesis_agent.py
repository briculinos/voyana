"""
Synthesis Agent
Creates 3 complete, curated itineraries from search results.
Uses OpenAI GPT-4 for creative trip planning and reasoning.
"""
import logging
from typing import List
from datetime import timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.travel import (
    AgentState,
    Itinerary,
    DayPlan,
    FlightOption,
    AccommodationOption,
    Activity
)
from app.utils.config import settings

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """
    Agent that synthesizes search results into complete trip itineraries.
    Creates 3 distinct options: budget-friendly, balanced, and premium.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.7,  # More creative for itinerary generation
        )

    async def synthesize(self, state: AgentState) -> AgentState:
        """
        Main agent function called by LangGraph.
        Creates 3 complete itineraries.
        """
        try:
            state.agent_messages.append(
                "Synthesis Agent: Creating your personalized itineraries..."
            )

            if not state.flight_options or not state.accommodation_options:
                error_msg = "Synthesis Agent: Insufficient search results"
                state.errors.append(error_msg)
                state.agent_messages.append(error_msg)
                return state

            # Create 3 different itinerary styles
            itineraries = []

            # 1. Budget-friendly option
            budget_itinerary = await self._create_budget_itinerary(state)
            if budget_itinerary:
                itineraries.append(budget_itinerary)

            # 2. Balanced option
            balanced_itinerary = await self._create_balanced_itinerary(state)
            if balanced_itinerary:
                itineraries.append(balanced_itinerary)

            # 3. Premium option
            premium_itinerary = await self._create_premium_itinerary(state)
            if premium_itinerary:
                itineraries.append(premium_itinerary)

            state.itineraries = itineraries
            state.agent_messages.append(
                f"Synthesis Agent: Created {len(itineraries)} complete itineraries"
            )
            state.current_step = "synthesis_complete"

        except Exception as e:
            error_msg = f"Synthesis Agent Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state.errors.append(error_msg)
            state.agent_messages.append(error_msg)

        return state

    async def _create_budget_itinerary(self, state: AgentState) -> Itinerary | None:
        """Create budget-friendly itinerary option"""
        try:
            # Select cheapest flight
            flights = sorted(state.flight_options, key=lambda f: f.total_price)
            if not flights:
                return None
            selected_flight = flights[0]

            # Select cheapest hotel with decent rating for budget option
            hotels = sorted(
                state.accommodation_options,
                key=lambda h: h.price_per_night  # Sort by price, cheapest first
            )
            if not hotels:
                return None

            # Select the cheapest hotel for budget
            selected_hotels = [hotels[0]] if hotels else []

            # Skip daily plans initially - will be generated after user selects interests
            daily_plans = []

            # Calculate costs
            flight_cost = selected_flight.total_price
            accommodation_cost = sum(h.total_price for h in selected_hotels)
            # Activities cost will be calculated after user selects interests
            activities_cost = 0
            food_cost = (state.parsed_intent.duration_days or 7) * 40 * (
                state.parsed_intent.num_adults + state.parsed_intent.num_children
            )

            # Calculate duration safely
            duration = state.parsed_intent.duration_days or 7

            return Itinerary(
                title=f"Budget Option - {state.parsed_intent.destination}",
                summary=f"Smart spending without missing out. This {duration}-day trip maximizes experiences while keeping costs down.",
                style_tag="Budget",
                flights=selected_flight,
                accommodations=selected_hotels,
                daily_plans=daily_plans,
                flight_cost=flight_cost,
                accommodation_cost=accommodation_cost,
                activities_cost=activities_cost,
                estimated_food_cost=food_cost,
                total_cost=flight_cost + accommodation_cost + activities_cost + food_cost,
                why_this_option="This itinerary prioritizes value and authentic experiences. You'll stay in well-rated, centrally-located accommodations that free up budget for memorable activities and local food.",
                tradeoffs="To stay within budget, flights may include connections and hotels focus on location over luxury amenities. Perfect for travelers who prefer spending on experiences rather than lodging."
            )

        except Exception as e:
            logger.error(f"Budget itinerary creation failed: {e}")
            return None

    async def _create_balanced_itinerary(self, state: AgentState) -> Itinerary | None:
        """Create balanced itinerary option"""
        try:
            # Select mid-range flight (good balance of price and convenience)
            flights = sorted(
                state.flight_options,
                key=lambda f: f.total_price / (24 - f.number_of_stops * 8)  # Penalize stops
            )
            if not flights:
                return None
            selected_flight = flights[len(flights) // 2]  # Middle option

            # Select mid-range hotel (middle option by price)
            hotels_by_price = sorted(
                state.accommodation_options,
                key=lambda h: h.price_per_night
            )
            if not hotels_by_price:
                return None

            # Pick the middle-priced hotel for balanced option
            # If only 2 hotels, pick the cheaper one (to differentiate from luxury)
            if len(hotels_by_price) == 2:
                mid_index = 0  # Pick cheaper one
            else:
                mid_index = len(hotels_by_price) // 2
            selected_hotels = [hotels_by_price[mid_index]] if hotels_by_price else []

            # Skip daily plans initially - will be generated after user selects interests
            daily_plans = []

            # Calculate costs
            flight_cost = selected_flight.total_price
            accommodation_cost = sum(h.total_price for h in selected_hotels)
            # Activities cost will be calculated after user selects interests
            activities_cost = 0
            food_cost = (state.parsed_intent.duration_days or 7) * 60 * (
                state.parsed_intent.num_adults + state.parsed_intent.num_children
            )

            # Calculate duration safely
            duration = state.parsed_intent.duration_days or 7

            return Itinerary(
                title=f"Balanced Option - {state.parsed_intent.destination}",
                summary=f"The sweet spot between comfort and adventure. {duration} days of well-paced exploration with quality accommodations.",
                style_tag="Balanced Family",
                flights=selected_flight,
                accommodations=selected_hotels,
                daily_plans=daily_plans,
                flight_cost=flight_cost,
                accommodation_cost=accommodation_cost,
                activities_cost=activities_cost,
                estimated_food_cost=food_cost,
                total_cost=flight_cost + accommodation_cost + activities_cost + food_cost,
                why_this_option="This itinerary strikes the perfect balance - comfortable flights, well-located hotels with good amenities, and a mix of must-see attractions with local experiences.",
                tradeoffs="Mid-range pricing means good value without extremes. You get comfort and convenience while leaving room in your budget for spontaneous discoveries."
            )

        except Exception as e:
            logger.error(f"Balanced itinerary creation failed: {e}")
            return None

    async def _create_premium_itinerary(self, state: AgentState) -> Itinerary | None:
        """Create premium itinerary option"""
        try:
            # Select best flights (fewest stops, best times)
            flights = sorted(
                state.flight_options,
                key=lambda f: (f.number_of_stops, f.total_duration_minutes)
            )
            if not flights:
                return None
            selected_flight = flights[0]

            # Select most expensive hotel (assuming higher price = luxury)
            hotels_by_price = sorted(
                state.accommodation_options,
                key=lambda h: h.price_per_night,
                reverse=True  # Most expensive first
            )
            if not hotels_by_price:
                return None

            # Pick the most expensive hotel for luxury option
            selected_hotels = [hotels_by_price[0]] if hotels_by_price else []

            # Skip daily plans initially - will be generated after user selects interests
            daily_plans = []

            # Calculate costs
            flight_cost = selected_flight.total_price
            accommodation_cost = sum(h.total_price for h in selected_hotels)
            # Activities cost will be calculated after user selects interests
            activities_cost = 0
            food_cost = (state.parsed_intent.duration_days or 7) * 100 * (
                state.parsed_intent.num_adults + state.parsed_intent.num_children
            )

            # Calculate duration safely
            duration = state.parsed_intent.duration_days or 7

            return Itinerary(
                title=f"Luxury Option - {state.parsed_intent.destination}",
                summary=f"Elevated travel with every detail perfected. {duration} days of luxury accommodations, seamless logistics, and curated experiences.",
                style_tag="Luxury",
                flights=selected_flight,
                accommodations=selected_hotels,
                daily_plans=daily_plans,
                flight_cost=flight_cost,
                accommodation_cost=accommodation_cost,
                activities_cost=activities_cost,
                estimated_food_cost=food_cost,
                total_cost=flight_cost + accommodation_cost + activities_cost + food_cost,
                why_this_option="This itinerary prioritizes comfort, convenience, and memorable experiences. Direct flights, top-rated hotels with excellent amenities, and premium activities that showcase the destination's finest offerings.",
                tradeoffs="Higher investment in quality means less budget flexibility, but delivers stress-free travel with elevated experiences throughout your journey."
            )

        except Exception as e:
            logger.error(f"Premium itinerary creation failed: {e}")
            return None

    def _select_hotels_for_trip(
        self,
        hotels: List[AccommodationOption],
        intent
    ) -> List[AccommodationOption]:
        """Select one or more hotels for the trip duration"""
        # For MVP, use same hotel for entire stay
        # In future: could split stay between different hotels/cities
        if hotels:
            return [hotels[0]]
        return []

    async def _generate_daily_plans(
        self,
        state: AgentState,
        style: str,
        hotels: List[AccommodationOption]
    ) -> List[DayPlan]:
        """
        Generate day-by-day plans using Claude.
        For MVP: Create structured but simple daily plans.
        """
        daily_plans = []
        intent = state.parsed_intent
        duration = intent.duration_days or 7
        start_date = intent.departure_date

        # Generate activities for each day using LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planner creating day-by-day itineraries.
For each day, suggest 2-4 activities that match the travel style and interests.
Be specific to the destination and consider pacing (don't overschedule).

Return a structured plan with activity names, categories, and estimated duration."""),
            ("human", """Create {duration} days of activities for a {style} trip to {destination}.
Travelers: {num_adults} adults, {num_children} children
Interests: {interests}
Travel style: {travel_style}

For each day, provide realistic activities with variety and good pacing.""")
        ])

        try:
            # For MVP, create simple structured plans without LLM call to save costs
            # In production, use LLM for creative, personalized suggestions
            for day in range(1, duration + 1):
                current_date = start_date + timedelta(days=day-1) if start_date else None

                # Create sample activities based on style
                activities = self._generate_sample_activities(day, style, intent)

                daily_plan = DayPlan(
                    day_number=day,
                    date=current_date,
                    location=intent.destination or "Destination",
                    activities=activities,
                    accommodation=hotels[0] if hotels else None,
                    estimated_cost=sum(a.price_per_person for a in activities) * (intent.num_adults + intent.num_children)
                )
                daily_plans.append(daily_plan)

        except Exception as e:
            logger.error(f"Daily plan generation error: {e}")

        return daily_plans

    def _generate_sample_activities(
        self,
        day_number: int,
        style: str,
        intent
    ) -> List[Activity]:
        """Generate sample activities for MVP"""
        destination = intent.destination or "City"

        base_activities = {
            1: Activity(
                name=f"Welcome to {destination} - City Walking Tour",
                description="Orientation walk covering main landmarks and neighborhoods",
                category="tour",
                duration_hours=3,
                price_per_person=15 if style == "budget" else 25,
                location=f"{destination} Old Town",
                rating=4.5,
                suitable_for_children=True,
                physical_intensity="low"
            ),
            2: Activity(
                name=f"{destination} Main Attraction Visit",
                description="Explore the city's iconic landmark or museum",
                category="cultural",
                duration_hours=4,
                price_per_person=20 if style == "budget" else 40,
                location=f"{destination} Center",
                rating=4.7,
                suitable_for_children=True,
                physical_intensity="low"
            ),
            3: Activity(
                name="Local Food Experience",
                description="Food tour or cooking class featuring regional cuisine",
                category="food",
                duration_hours=3,
                price_per_person=40 if style == "budget" else 80,
                location=f"{destination} Market District",
                rating=4.8,
                suitable_for_children=True,
                physical_intensity="low"
            )
        }

        # Return activity for this day (cycle through if more days than activities)
        activity_index = ((day_number - 1) % 3) + 1
        return [base_activities[activity_index]]


# Standalone async function for LangGraph node
async def synthesis_node(state: AgentState) -> AgentState:
    """LangGraph node wrapper for Synthesis Agent"""
    agent = SynthesisAgent()
    return await agent.synthesize(state)
