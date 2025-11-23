"""
LangGraph Workflow
Orchestrates all agents in a sequential pipeline:
Intent Parser -> Search Orchestrator -> Taste Profiler -> Synthesis Agent
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.models.travel import AgentState
from app.agents.intent_parser import parse_intent_node
from app.agents.search_orchestrator import search_node
from app.agents.taste_profiler import taste_profile_node
from app.agents.synthesis_agent import synthesis_node

logger = logging.getLogger(__name__)


class TravelConciergeWorkflow:
    """
    Main workflow orchestrating all travel agents.
    Uses LangGraph's StateGraph for agent coordination.
    """

    def __init__(self):
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Flow:
        1. Intent Parser: Extract structured requirements
        2. Search Orchestrator: Find flights and hotels
        3. Taste Profiler: Rank options by user preferences
        4. Synthesis Agent: Create 3 complete itineraries
        """
        # Create state graph
        graph = StateGraph(AgentState)

        # Add nodes (agents)
        graph.add_node("parse_intent", self._wrap_sync_node(parse_intent_node))
        graph.add_node("search", search_node)
        graph.add_node("taste_profile", self._wrap_sync_node(taste_profile_node))
        graph.add_node("synthesize", synthesis_node)

        # Define edges (flow)
        graph.set_entry_point("parse_intent")

        # Conditional routing based on intent parsing success
        graph.add_conditional_edges(
            "parse_intent",
            self._should_continue_after_intent,
            {
                "continue": "search",
                "end": END
            }
        )

        # After search, always go to taste profiling
        graph.add_edge("search", "taste_profile")

        # Conditional routing based on search results
        graph.add_conditional_edges(
            "taste_profile",
            self._should_continue_after_search,
            {
                "continue": "synthesize",
                "end": END
            }
        )

        # After synthesis, we're done
        graph.add_edge("synthesize", END)

        return graph

    def _wrap_sync_node(self, sync_func):
        """Wrap synchronous node functions to work with async graph"""
        async def wrapped(state: AgentState) -> AgentState:
            return sync_func(state)
        return wrapped

    def _should_continue_after_intent(self, state: AgentState) -> str:
        """
        Conditional edge: Check if intent parsing succeeded.
        """
        if state.parsed_intent is None:
            logger.warning("Intent parsing failed, ending workflow")
            return "end"

        # Check for critical missing fields
        intent = state.parsed_intent
        if not intent.destination and not intent.total_budget:
            state.errors.append("Missing critical information: destination or budget")
            return "end"

        return "continue"

    def _should_continue_after_search(self, state: AgentState) -> str:
        """
        Conditional edge: Check if search returned sufficient results.
        """
        if not state.flight_options and not state.accommodation_options:
            logger.warning("No search results found, ending workflow")
            state.errors.append("No travel options found matching your criteria")
            return "end"

        if len(state.flight_options) == 0:
            logger.warning("No flights found")
            state.errors.append("No flights available for your dates")
            # Continue anyway if we have hotels

        if len(state.accommodation_options) < 3:
            logger.warning(f"Limited accommodation options: {len(state.accommodation_options)}")
            # Continue anyway

        return "continue"

    async def run(self, user_message: str, user_id: str | None = None) -> Dict[str, Any]:
        """
        Execute the full workflow.

        Args:
            user_message: Natural language travel request
            user_id: Optional user ID for personalization

        Returns:
            Dict containing itineraries, messages, and metadata
        """
        # Initialize state
        initial_state = AgentState(
            user_message=user_message,
            user_id=user_id,
            conversation_id=None,  # Generate if needed
            agent_messages=[],
            errors=[]
        )

        try:
            # Run the graph
            logger.info(f"Starting workflow for user: {user_id}")
            final_state = await self.compiled_graph.ainvoke(initial_state)

            # Extract results
            result = {
                "success": len(final_state.itineraries) > 0,
                "itineraries": [itinerary.model_dump(mode='json') for itinerary in final_state.itineraries],
                "agent_messages": final_state.agent_messages,
                "errors": final_state.errors,
                "parsed_intent": final_state.parsed_intent.model_dump(mode='json') if final_state.parsed_intent else None,
                "metadata": {
                    "num_flight_options": len(final_state.flight_options),
                    "num_hotel_options": len(final_state.accommodation_options),
                    "num_itineraries": len(final_state.itineraries)
                }
            }

            logger.info(f"Workflow completed successfully. Generated {len(final_state.itineraries)} itineraries")
            return result

        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            return {
                "success": False,
                "itineraries": [],
                "agent_messages": [f"Workflow error: {str(e)}"],
                "errors": [str(e)],
                "parsed_intent": None,
                "metadata": {}
            }

    async def run_with_streaming(self, user_message: str, user_id: str | None = None):
        """
        Execute workflow with streaming updates.
        Yields state updates as agents complete.
        """
        initial_state = AgentState(
            user_message=user_message,
            user_id=user_id,
            agent_messages=[],
            errors=[]
        )

        try:
            final_state_dict = {}
            # Stream events from the graph
            async for event in self.compiled_graph.astream(initial_state):
                # event is a dict with node name as key
                node_name = list(event.keys())[0]
                node_state = event[node_name]

                # Store the latest state
                final_state_dict = node_state

                # LangGraph can return either dict or Pydantic model
                if isinstance(node_state, dict):
                    agent_messages = node_state.get("agent_messages", [])
                    current_step = node_state.get("current_step", "")
                    errors = node_state.get("errors", [])
                else:
                    # It's a Pydantic model
                    agent_messages = node_state.agent_messages
                    current_step = node_state.current_step
                    errors = node_state.errors

                # Yield progress update
                yield {
                    "type": "agent_update",
                    "agent": node_name,
                    "messages": agent_messages[-1] if agent_messages else "",
                    "current_step": current_step,
                    "errors": errors
                }

            # Final result - handle both dict and Pydantic model
            if isinstance(final_state_dict, dict):
                itineraries = final_state_dict.get("itineraries", [])
                parsed_intent = final_state_dict.get("parsed_intent")
                flight_options = final_state_dict.get("flight_options", [])
                accommodation_options = final_state_dict.get("accommodation_options", [])
            else:
                itineraries = final_state_dict.itineraries
                parsed_intent = final_state_dict.parsed_intent
                flight_options = final_state_dict.flight_options
                accommodation_options = final_state_dict.accommodation_options

            # Convert Pydantic models to dicts if needed
            itinerary_dicts = []
            for itinerary in itineraries:
                if hasattr(itinerary, 'model_dump'):
                    itinerary_dicts.append(itinerary.model_dump(mode='json'))
                elif isinstance(itinerary, dict):
                    itinerary_dicts.append(itinerary)

            yield {
                "type": "complete",
                "success": len(itineraries) > 0,
                "itineraries": itinerary_dicts,
                "parsed_intent": parsed_intent.model_dump(mode='json') if parsed_intent and hasattr(parsed_intent, 'model_dump') else parsed_intent,
                "metadata": {
                    "num_flight_options": len(flight_options),
                    "num_hotel_options": len(accommodation_options),
                }
            }

        except Exception as e:
            logger.error(f"Streaming workflow error: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }


# Global workflow instance
workflow = TravelConciergeWorkflow()
