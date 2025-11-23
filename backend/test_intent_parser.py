"""
Test the Intent Parser with the exact message format from frontend
"""
import asyncio
from app.models.travel import AgentState
from app.agents.intent_parser import parse_intent_node

# Exact message format from frontend
user_message = "We want to visit Rome, Italy for 10 days with 5000€. Traveling from Copenhagen. 2 adults."

print(f"Testing Intent Parser with message:")
print(f"'{user_message}'")
print("\n" + "="*80 + "\n")

# Create initial state
state = AgentState(
    user_message=user_message,
    agent_messages=[],
    errors=[]
)

# Run intent parser
result_state = parse_intent_node(state)

# Print results
if result_state.parsed_intent:
    intent = result_state.parsed_intent
    print("✅ Intent Parsed Successfully!")
    print(f"\nExtracted Fields:")
    print(f"  Origin: {intent.origin}")
    print(f"  Destination: {intent.destination}")
    print(f"  Departure Date: {intent.departure_date}")
    print(f"  Return Date: {intent.return_date}")
    print(f"  Duration: {intent.duration_days} days")
    print(f"  Budget: €{intent.total_budget}")
    print(f"  Adults: {intent.num_adults}")
    print(f"  Children: {intent.num_children}")

    print(f"\nFlight Search Requirements:")
    if intent.origin and intent.destination and intent.departure_date and intent.return_date:
        print(f"  ✅ ALL required fields present")
        print(f"  Route: {intent.origin} → {intent.destination}")
        print(f"  Dates: {intent.departure_date} to {intent.return_date}")
    else:
        print(f"  ❌ MISSING required fields:")
        if not intent.origin:
            print(f"     - origin")
        if not intent.destination:
            print(f"     - destination")
        if not intent.departure_date:
            print(f"     - departure_date")
        if not intent.return_date:
            print(f"     - return_date")
else:
    print("❌ Intent parsing FAILED")
    print(f"Errors: {result_state.errors}")
