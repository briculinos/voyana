"""Test that duration_days is calculated correctly"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from app.models.travel import TravelIntent

# Test 1: Duration calculated from dates
intent1 = TravelIntent(
    origin="Copenhagen",
    destination="Tokyo",
    departure_date=date(2025, 12, 1),
    return_date=date(2025, 12, 15),
    num_adults=2
)

print(f"Test 1 - Duration from dates:")
print(f"  Departure: {intent1.departure_date}")
print(f"  Return: {intent1.return_date}")
print(f"  Duration: {intent1.duration_days} days")
print(f"  Expected: 14 days")
print(f"  ✅ PASS" if intent1.duration_days == 14 else f"  ❌ FAIL")

# Test 2: Explicit duration_days value
intent2 = TravelIntent(
    origin="Copenhagen",
    destination="Tokyo",
    departure_date=date(2025, 12, 1),
    return_date=date(2025, 12, 15),
    duration_days=10,  # Explicitly set
    num_adults=2
)

print(f"\nTest 2 - Explicit duration value:")
print(f"  Duration: {intent2.duration_days} days")
print(f"  Expected: 10 days (explicit value)")
print(f"  ✅ PASS" if intent2.duration_days == 10 else f"  ❌ FAIL")

# Test 3: No dates provided
intent3 = TravelIntent(
    origin="Copenhagen",
    destination="Tokyo",
    num_adults=2
)

print(f"\nTest 3 - No dates:")
print(f"  Duration: {intent3.duration_days}")
print(f"  Expected: None")
print(f"  ✅ PASS" if intent3.duration_days is None else f"  ❌ FAIL")
