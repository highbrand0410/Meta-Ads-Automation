"""Quick test of core modules without Streamlit dependency."""

import sys
sys.path.insert(0, ".")

# Test config import
from config import COLUMN_MAP, CREATIVE_NAME_DATE_PATTERNS
print("config.py OK")

# Test creative date extraction
from src.creative_age import extract_creative_date

tests = [
    ("BGL|DSA|Hn-Vid12-25Sep25", "2025-09-25"),
    ("WeRize|LAL|En-Img3-01Jan26", "2026-01-01"),
    ("TestAd-15Mar2026", "2026-03-15"),
    ("NoDateHere", None),
]

for name, expected in tests:
    result = extract_creative_date(name)
    status = "PASS" if str(result) == str(expected) else "FAIL"
    print(f"  {status}: extract_creative_date('{name}') = {result} (expected {expected})")

print("\nAll core tests done.")
