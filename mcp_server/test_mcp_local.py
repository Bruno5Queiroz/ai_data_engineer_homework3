#!/usr/bin/env python3
"""
Local testing script for the Weather MCP Server.

Run this script to verify that the weather broker functions work correctly
before deploying the MCP server to Databricks Apps.

Usage:
    python test_mcp_local.py

Requirements:
    pip install requests
"""

import sys
import traceback
from datetime import datetime, timedelta

try:
    import weather_broker
except ImportError:
    print("Error: Cannot import weather_broker. Make sure you're running this from the mcp_server directory.")
    sys.exit(1)


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print a success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print an error message."""
    print(f"✗ {text}")


def print_info(text, indent=2):
    """Print an info message."""
    print(" " * indent + text)


def test_get_coordinates():
    """Test the get_coordinates function."""
    print_header("TEST 1: Get Coordinates")
    
    test_cases = [
        ("Chicago", True),
        ("Austin, Texas", True),
        ("London, UK", True),
        ("XyzInvalidCity123", False),  # Should fail
    ]
    
    passed = 0
    for location, should_succeed in test_cases:
        try:
            lat, lon, full_name = weather_broker.get_coordinates(location)
            if should_succeed:
                print_success(f"'{location}' -> {full_name} ({lat}, {lon})")
                passed += 1
            else:
                print_error(f"'{location}' should have failed but succeeded")
        except Exception as e:
            if not should_succeed:
                print_success(f"'{location}' correctly failed: {type(e).__name__}")
                passed += 1
            else:
                print_error(f"'{location}' failed unexpectedly: {e}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_get_current_weather():
    """Test the get_current_weather function."""
    print_header("TEST 2: Get Current Weather")
    
    location = "Chicago"
    try:
        result = weather_broker.get_current_weather(location)
        print_success(f"Retrieved current weather for {result['location']}")
        print_info(f"Temperature: {result['temperature_celsius']}°C ({result['temperature_fahrenheit']}°F)")
        print_info(f"Feels Like: {result['feels_like_celsius']}°C ({result['feels_like_fahrenheit']}°F)")
        print_info(f"Humidity: {result['humidity_percent']}%")
        print_info(f"Wind: {result['wind_speed_kmh']} km/h ({result['wind_speed_mph']} mph)")
        print_info(f"Precipitation: {result['precipitation_mm']} mm")
        print_info(f"Conditions: {result['weather_description']}")
        print_info(f"Timestamp: {result['timestamp']}")
        
        # Validate data types and ranges
        assert isinstance(result['temperature_celsius'], (int, float))
        assert isinstance(result['humidity_percent'], int)
        assert 0 <= result['humidity_percent'] <= 100
        assert result['location'] != ""
        
        print_success("All fields validated successfully")
        return True
    except Exception as e:
        print_error(f"Failed: {e}")
        traceback.print_exc()
        return False


def test_get_forecast():
    """Test the get_forecast function."""
    print_header("TEST 3: Get Forecast")
    
    location = "Austin, Texas"
    days = 5
    
    try:
        result = weather_broker.get_forecast(location, days)
        print_success(f"Retrieved {result['forecast_days']}-day forecast for {result['location']}")
        print_info(f"Timezone: {result['timezone']}")
        print_info(f"Latitude: {result['latitude']}, Longitude: {result['longitude']}")
        print_info("\nDaily Forecast:")
        
        for i, day in enumerate(result['daily_forecast'], 1):
            print_info(f"{i}. {day['date']}:", indent=4)
            print_info(f"   High: {day['temperature_max_celsius']}°C ({day['temperature_max_fahrenheit']}°F)", indent=4)
            print_info(f"   Low: {day['temperature_min_celsius']}°C ({day['temperature_min_fahrenheit']}°F)", indent=4)
            print_info(f"   Rain Chance: {day['precipitation_probability_percent']}%", indent=4)
            print_info(f"   Conditions: {day['weather_description']}", indent=4)
        
        # Validate
        assert len(result['daily_forecast']) == days
        assert result['timezone'] != ""
        
        print_success(f"All {days} days validated successfully")
        return True
    except Exception as e:
        print_error(f"Failed: {e}")
        traceback.print_exc()
        return False


def test_predict_umbrella_needed():
    """Test the predict_umbrella_needed function."""
    print_header("TEST 4: Predict Umbrella Needed")
    
    location = "Seattle"
    # Test with tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        result = weather_broker.predict_umbrella_needed(location, tomorrow)
        print_success(f"Retrieved umbrella prediction for {result['location']} on {result['date']}")
        print_info(f"Recommendation: {result['umbrella_recommendation']}")
        print_info(f"Risk Level: {result['risk_level']}")
        print_info(f"Precipitation Probability: {result['precipitation_probability_percent']}%")
        print_info(f"Temperature: {result['temperature_max_celsius']}°C ({result['temperature_max_fahrenheit']}°F)")
        print_info(f"Weather: {result['weather_description']}")
        print_info(f"Reasoning: {result['reasoning']}")
        
        # Validate
        assert result['umbrella_recommendation'] in ["BRING_UMBRELLA", "MAYBE_BRING_UMBRELLA", "NO_UMBRELLA_NEEDED"]
        assert result['risk_level'] in ["HIGH", "MEDIUM", "LOW"]
        assert 0 <= result['precipitation_probability_percent'] <= 100
        
        print_success("Umbrella prediction validated successfully")
        return True
    except Exception as e:
        print_error(f"Failed: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid inputs."""
    print_header("TEST 5: Error Handling")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Invalid location
    total_tests += 1
    try:
        weather_broker.get_current_weather("InvalidCityXYZ123")
        print_error("Invalid location should have raised an error")
    except ValueError as e:
        print_success(f"Invalid location correctly raised ValueError: {e}")
        tests_passed += 1
    except Exception as e:
        print_error(f"Unexpected error type: {type(e).__name__}: {e}")
    
    # Test 2: Invalid date format
    total_tests += 1
    try:
        weather_broker.predict_umbrella_needed("Chicago", "2026-13-45")  # Invalid date
        print_error("Invalid date should have raised an error")
    except ValueError as e:
        print_success(f"Invalid date correctly raised ValueError: {e}")
        tests_passed += 1
    except Exception as e:
        print_error(f"Unexpected error type: {type(e).__name__}: {e}")
    
    # Test 3: Out of range days
    total_tests += 1
    try:
        result = weather_broker.get_forecast("Chicago", 100)  # Too many days
        # Should clamp to 16 days, not raise an error
        if result['forecast_days'] == 16:
            print_success("Excessive days correctly clamped to 16")
            tests_passed += 1
        else:
            print_error(f"Expected 16 days, got {result['forecast_days']}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
    
    print(f"\nPassed: {tests_passed}/{total_tests}")
    return tests_passed == total_tests


def main():
    """Run all tests."""
    print_header("Weather Broker Test Suite")
    print("Testing all weather broker functions before MCP deployment...")
    
    results = {
        "Coordinates": test_get_coordinates(),
        "Current Weather": test_get_current_weather(),
        "Forecast": test_get_forecast(),
        "Umbrella Prediction": test_predict_umbrella_needed(),
        "Error Handling": test_error_handling(),
    }
    
    print_header("Test Results Summary")
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:.<50} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n  Total: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n" + "=" * 70)
        print("  🎉 ALL TESTS PASSED! Ready to deploy MCP server.")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ⚠️  SOME TESTS FAILED. Fix issues before deploying.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
