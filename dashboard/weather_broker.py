"""
Weather broker module for Open-Meteo API.

Provides weather data retrieval functions using the free Open-Meteo API
(https://open-meteo.com/). No API key required.

This module handles all HTTP calls and data parsing, keeping the MCP tool
functions in weather_mcp_server.py thin and focused on tool logic.

Functions:
    - get_current_weather(location): Current conditions for a location
    - get_forecast(location, days): Multi-day forecast
    - predict_umbrella_needed(location, date): Recommendation based on precipitation
    - get_coordinates(location): Convert location name to lat/lon
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Open-Meteo API endpoints
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

# Weather code mappings (WMO Weather interpretation codes)
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_coordinates(location: str) -> Tuple[float, float, str]:
    """
    Convert a location name (city, address, etc.) to latitude/longitude coordinates.
    
    Args:
        location: Location name (e.g., "Chicago", "New York, NY", "Austin, Texas")
    
    Returns:
        Tuple of (latitude, longitude, full_location_name)
    
    Raises:
        ValueError: If location cannot be found
    """
    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    response = requests.get(GEOCODING_API, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if not data.get("results"):
        raise ValueError(f"Location not found: {location}")
    
    result = data["results"][0]
    lat = result["latitude"]
    lon = result["longitude"]
    
    # Build full location name
    name_parts = [result["name"]]
    if result.get("admin1"):
        name_parts.append(result["admin1"])
    if result.get("country"):
        name_parts.append(result["country"])
    full_name = ", ".join(name_parts)
    
    return lat, lon, full_name


def get_current_weather(location: str) -> Dict:
    """
    Get current weather conditions for a location.
    
    Args:
        location: Location name (city, address, etc.)
    
    Returns:
        Dict with current weather data:
        {
            "location": str,
            "latitude": float,
            "longitude": float,
            "temperature_celsius": float,
            "temperature_fahrenheit": float,
            "feels_like_celsius": float,
            "feels_like_fahrenheit": float,
            "humidity_percent": int,
            "wind_speed_kmh": float,
            "wind_speed_mph": float,
            "precipitation_mm": float,
            "weather_description": str,
            "weather_code": int,
            "timestamp": str (ISO format)
        }
    """
    lat, lon, full_location = get_coordinates(location)
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m"
        ],
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh"
    }
    
    response = requests.get(WEATHER_API, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    current = data["current"]
    temp_c = current["temperature_2m"]
    feels_like_c = current["apparent_temperature"]
    wind_kmh = current["wind_speed_10m"]
    weather_code = current["weather_code"]
    
    return {
        "location": full_location,
        "latitude": lat,
        "longitude": lon,
        "temperature_celsius": round(temp_c, 1),
        "temperature_fahrenheit": round(temp_c * 9/5 + 32, 1),
        "feels_like_celsius": round(feels_like_c, 1),
        "feels_like_fahrenheit": round(feels_like_c * 9/5 + 32, 1),
        "humidity_percent": current["relative_humidity_2m"],
        "wind_speed_kmh": round(wind_kmh, 1),
        "wind_speed_mph": round(wind_kmh * 0.621371, 1),
        "precipitation_mm": current["precipitation"],
        "weather_description": WEATHER_CODES.get(weather_code, "Unknown"),
        "weather_code": weather_code,
        "timestamp": current["time"]
    }


def get_forecast(location: str, days: int = 7) -> Dict:
    """
    Get weather forecast for the next N days.
    
    Args:
        location: Location name (city, address, etc.)
        days: Number of days to forecast (1-16, default 7)
    
    Returns:
        Dict with forecast data:
        {
            "location": str,
            "latitude": float,
            "longitude": float,
            "timezone": str,
            "forecast_days": int,
            "daily_forecast": [
                {
                    "date": str (YYYY-MM-DD),
                    "temperature_max_celsius": float,
                    "temperature_max_fahrenheit": float,
                    "temperature_min_celsius": float,
                    "temperature_min_fahrenheit": float,
                    "precipitation_probability_percent": int,
                    "weather_description": str,
                    "weather_code": int
                },
                ...
            ]
        }
    """
    # Validate days parameter
    days = max(1, min(16, days))  # Open-Meteo supports up to 16 days
    
    lat, lon, full_location = get_coordinates(location)
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "weather_code"
        ],
        "temperature_unit": "celsius",
        "timezone": "auto",
        "forecast_days": days
    }
    
    response = requests.get(WEATHER_API, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    daily = data["daily"]
    forecast_list = []
    
    for i in range(len(daily["time"])):
        temp_max_c = daily["temperature_2m_max"][i]
        temp_min_c = daily["temperature_2m_min"][i]
        weather_code = daily["weather_code"][i]
        
        forecast_list.append({
            "date": daily["time"][i],
            "temperature_max_celsius": round(temp_max_c, 1),
            "temperature_max_fahrenheit": round(temp_max_c * 9/5 + 32, 1),
            "temperature_min_celsius": round(temp_min_c, 1),
            "temperature_min_fahrenheit": round(temp_min_c * 9/5 + 32, 1),
            "precipitation_probability_percent": daily["precipitation_probability_max"][i],
            "weather_description": WEATHER_CODES.get(weather_code, "Unknown"),
            "weather_code": weather_code
        })
    
    return {
        "location": full_location,
        "latitude": lat,
        "longitude": lon,
        "timezone": data["timezone"],
        "forecast_days": days,
        "daily_forecast": forecast_list
    }


def predict_umbrella_needed(location: str, date: str = None) -> Dict:
    """
    Predict whether an umbrella is needed for a specific location and date.
    
    This is a derived judgment call based on precipitation probability:
    - HIGH: >= 60% chance of rain
    - MEDIUM: 30-59% chance of rain
    - LOW: < 30% chance of rain
    
    Args:
        location: Location name (city, address, etc.)
        date: Optional date string (YYYY-MM-DD). Defaults to tomorrow.
    
    Returns:
        Dict with umbrella recommendation:
        {
            "location": str,
            "date": str,
            "umbrella_recommendation": str ("BRING_UMBRELLA", "MAYBE_BRING_UMBRELLA", "NO_UMBRELLA_NEEDED"),
            "risk_level": str ("HIGH", "MEDIUM", "LOW"),
            "precipitation_probability_percent": int,
            "temperature_max_celsius": float,
            "temperature_max_fahrenheit": float,
            "weather_description": str,
            "reasoning": str
        }
    """
    # Default to tomorrow if no date specified
    if date is None:
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
            target_date = date
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
    
    # Get forecast
    forecast = get_forecast(location, days=7)
    
    # Find the target date in the forecast
    target_forecast = None
    for day in forecast["daily_forecast"]:
        if day["date"] == target_date:
            target_forecast = day
            break
    
    if target_forecast is None:
        raise ValueError(f"Date {target_date} is not in the forecast range. Choose a date within the next 7 days.")
    
    # Make umbrella decision based on precipitation probability
    precip_prob = target_forecast["precipitation_probability_percent"]
    
    if precip_prob >= 60:
        recommendation = "BRING_UMBRELLA"
        risk_level = "HIGH"
        reasoning = f"High chance of precipitation ({precip_prob}%). Umbrella strongly recommended."
    elif precip_prob >= 30:
        recommendation = "MAYBE_BRING_UMBRELLA"
        risk_level = "MEDIUM"
        reasoning = f"Moderate chance of precipitation ({precip_prob}%). Consider bringing an umbrella."
    else:
        recommendation = "NO_UMBRELLA_NEEDED"
        risk_level = "LOW"
        reasoning = f"Low chance of precipitation ({precip_prob}%). Umbrella likely not needed."
    
    return {
        "location": forecast["location"],
        "date": target_date,
        "umbrella_recommendation": recommendation,
        "risk_level": risk_level,
        "precipitation_probability_percent": precip_prob,
        "temperature_max_celsius": target_forecast["temperature_max_celsius"],
        "temperature_max_fahrenheit": target_forecast["temperature_max_fahrenheit"],
        "weather_description": target_forecast["weather_description"],
        "reasoning": reasoning
    }
