#!/usr/bin/env python3
"""
Test script for news_country_crawler.py
Verifies country detection logic without running the crawler
"""

import sys
from news_country_crawler import detect_countries_in_title, COUNTRY_DATA

# Test cases
TEST_TITLES = [
    "UK Prime Minister meets with Japanese officials in Tokyo",
    "French and German leaders discuss European policy",
    "American troops withdraw from Afghan territory",
    "Chinese economy shows signs of recovery",
    "Israeli and Palestinian leaders hold peace talks",
    "Russian forces advance in Ukraine",
    "Brazilian president visits United States",
    "Australian wildfires threaten Sydney",
    "Indian tech sector booms amid global slowdown",
    "Nigerian oil exports increase to Europe",
    "South Korean and North Korean officials meet at DMZ",
    "British and Irish ministers discuss Brexit aftermath",
    "Mexican cartel violence spills into US border towns",
    "Saudi Arabia and UAE strengthen regional ties",
    "Egyptian pyramids attract record tourism",
    "The Pope addresses crowd at Vatican City",
    "Dutch cycling culture influences German urban planning",
    "Norwegian sovereign wealth fund divests from fossil fuels",
    "Swiss banks face new regulations",
    "Singapore emerges as fintech hub"
]

def run_tests():
    """Run country detection tests"""
    print("=" * 70)
    print("News Country Crawler - Test Suite")
    print("=" * 70)
    
    print(f"\nTesting country detection with {len(TEST_TITLES)} sample titles...")
    print(f"Total countries in database: {len(COUNTRY_DATA)}\n")
    
    total_detections = 0
    
    for i, title in enumerate(TEST_TITLES, 1):
        countries = detect_countries_in_title(title)
        total_detections += len(countries)
        
        print(f"{i:2d}. Title: {title}")
        if countries:
            print(f"    → Detected: {', '.join(countries)}")
        else:
            print(f"    → No countries detected")
        print()
    
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Titles tested: {len(TEST_TITLES)}")
    print(f"Total country detections: {total_detections}")
    print(f"Average countries per title: {total_detections / len(TEST_TITLES):.2f}")
    print()
    
    # Test specific aliases
    print("=" * 70)
    print("Testing Specific Aliases")
    print("=" * 70)
    
    alias_tests = [
        ("UK", ["United Kingdom"]),
        ("US", ["United States"]),
        ("USA", ["United States"]),
        ("Japanese", ["Japan"]),
        ("French", ["France"]),
        ("Chinese", ["China"]),
        ("British", ["United Kingdom"]),
        ("American", ["United States"]),
    ]
    
    for alias, expected_countries in alias_tests:
        test_title = f"Testing {alias} detection"
        detected = detect_countries_in_title(test_title)
        status = "✓" if set(detected) == set(expected_countries) else "✗"
        print(f"{status} '{alias}' → {detected if detected else 'NOT DETECTED'}")
    
    print("\n" + "=" * 70)
    print("Test completed! If all checks passed, the crawler is ready to use.")
    print("=" * 70)

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1)
