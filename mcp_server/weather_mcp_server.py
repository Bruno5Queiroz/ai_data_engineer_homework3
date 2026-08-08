"""
Version: 2.0
Weather Forecast MCP Server.

Exposes weather forecast tools over MCP (Model Context Protocol) so a
Databricks Agent Bricks agent can call them like any other tool:
    - get_current_weather(location): Current conditions
    - get_forecast(location, days): Multi-day forecast
    - predict_umbrella_needed(location, date): Umbrella recommendation
    - get_travel_recommendation(location, date): Travel weather assessment
    - get_severe_weather_alerts(location, days): Check for severe weather alerts

These tools are backed by the free Open-Meteo API (https://open-meteo.com/),
which requires no API key or registration. All HTTP calls and parsing are
handled in weather_broker.py to keep these tool functions thin.

Deploy this as a Databricks App (see app.yaml) so an Agent Bricks agent
can register its URL as an external MCP server.

Run locally:
    python weather_mcp_server.py
"""

import os
import logging

from fastmcp import FastMCP

import weather_broker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-mcp-server")

mcp = FastMCP("weather-forecast")


@mcp.tool
def get_current_weather(location: str) -> dict:
    """
    Get current weather conditions for a specific location.
    
    Provides real-time temperature, humidity, wind speed, precipitation,
    and weather conditions for any city or location worldwide.
    
    Args:
        location: Location name (e.g., "Chicago", "New York, NY", "Austin, Texas", "London, UK")
    
    Returns:
        A dict with current weather data including:
        - location: Full location name with country
        - temperature (Celsius and Fahrenheit)
        - feels_like temperature
        - humidity_percent
        - wind_speed (km/h and mph)
        - precipitation_mm
        - weather_description
        - timestamp (ISO format)
    
    Examples:
        - get_current_weather("Chicago")
        - get_current_weather("San Francisco, CA")
        - get_current_weather("Tokyo, Japan")
    """
    logger.info(f"Getting current weather for: {location}")
    try:
        result = weather_broker.get_current_weather(location)
        logger.info(f"Successfully retrieved weather for {result['location']}")
        return result
    except Exception as e:
        logger.error(f"Error getting current weather for {location}: {e}")
        return {
            "error": str(e),
            "location": location,
            "message": f"Failed to retrieve current weather for {location}"
        }


@mcp.tool
def get_forecast(location: str, days: int = 7) -> dict:
    """
    Get weather forecast for the next N days (1-16 days).
    
    Provides daily forecast including high/low temperatures, precipitation
    probability, and weather conditions for the specified location.
    
    Args:
        location: Location name (e.g., "Chicago", "Austin, Texas")
        days: Number of days to forecast (1-16, default 7)
    
    Returns:
        A dict with forecast data:
        - location: Full location name
        - forecast_days: Number of days forecasted
        - daily_forecast: List of daily forecasts, each containing:
            - date (YYYY-MM-DD)
            - temperature_max/min (Celsius and Fahrenheit)
            - precipitation_probability_percent
            - weather_description
    
    Examples:
        - get_forecast("Chicago", 3)  # 3-day forecast
        - get_forecast("Austin, Texas")  # Default 7-day forecast
        - get_forecast("Seattle, WA", 14)  # 14-day forecast
    """
    logger.info(f"Getting {days}-day forecast for: {location}")
    try:
        result = weather_broker.get_forecast(location, days)
        logger.info(f"Successfully retrieved {days}-day forecast for {result['location']}")
        return result
    except Exception as e:
        logger.error(f"Error getting forecast for {location}: {e}")
        return {
            "error": str(e),
            "location": location,
            "days": days,
            "message": f"Failed to retrieve forecast for {location}"
        }


@mcp.tool
def predict_umbrella_needed(location: str, date: str = None) -> dict:
    """
    Predict whether an umbrella is needed for a specific location and date.
    
    Makes a derived judgment call based on precipitation probability:
    - HIGH risk (>=60%): BRING_UMBRELLA
    - MEDIUM risk (30-59%): MAYBE_BRING_UMBRELLA
    - LOW risk (<30%): NO_UMBRELLA_NEEDED
    
    Args:
        location: Location name (e.g., "Chicago", "New York")
        date: Optional date string (YYYY-MM-DD). Defaults to tomorrow if not specified.
    
    Returns:
        A dict with umbrella recommendation:
        - location: Full location name
        - date: Target date
        - umbrella_recommendation: "BRING_UMBRELLA", "MAYBE_BRING_UMBRELLA", or "NO_UMBRELLA_NEEDED"
        - risk_level: "HIGH", "MEDIUM", or "LOW"
        - precipitation_probability_percent: Chance of rain
        - temperature_max: High temperature for the day
        - weather_description: Expected conditions
        - reasoning: Explanation of the recommendation
    
    Examples:
        - predict_umbrella_needed("Chicago")  # Tomorrow's forecast
        - predict_umbrella_needed("Austin", "2026-08-15")  # Specific date
        - predict_umbrella_needed("Seattle, WA", "2026-08-20")
    """
    logger.info(f"Predicting umbrella need for {location} on {date or 'tomorrow'}")
    try:
        result = weather_broker.predict_umbrella_needed(location, date)
        logger.info(f"Umbrella prediction for {result['location']}: {result['umbrella_recommendation']}")
        return result
    except Exception as e:
        logger.error(f"Error predicting umbrella need for {location}: {e}")
        return {
            "error": str(e),
            "location": location,
            "date": date,
            "message": f"Failed to predict umbrella need for {location}"
        }


@mcp.tool
def get_travel_recommendation(location: str, date: str = None) -> dict:
    """
    Get a comprehensive travel weather recommendation for a specific location and date.
    
    Analyzes temperature, precipitation, and weather conditions to provide
    actionable travel advice (what to wear, what to bring, activity suggestions).
    
    Args:
        location: Location name (e.g., "Miami", "Denver, CO")
        date: Optional date string (YYYY-MM-DD). Defaults to tomorrow if not specified.
    
    Returns:
        A dict with travel recommendations:
        - location: Full location name
        - date: Target date
        - weather_summary: Overall conditions summary
        - temperature_celsius/fahrenheit: High temperature
        - precipitation_probability_percent: Chance of rain
        - clothing_recommendation: What to wear
        - items_to_bring: List of recommended items
        - activity_recommendation: Suitable activities
        - overall_suitability: "EXCELLENT", "GOOD", "FAIR", or "POOR"
    
    Examples:
        - get_travel_recommendation("Miami")  # Tomorrow
        - get_travel_recommendation("Denver", "2026-08-15")
        - get_travel_recommendation("Portland, OR", "2026-08-20")
    """
    logger.info(f"Getting travel recommendation for {location} on {date or 'tomorrow'}")
    try:
        # Get umbrella prediction which includes forecast data
        umbrella_data = weather_broker.predict_umbrella_needed(location, date)
        
        temp_c = umbrella_data["temperature_max_celsius"]
        temp_f = umbrella_data["temperature_max_fahrenheit"]
        precip_prob = umbrella_data["precipitation_probability_percent"]
        weather_desc = umbrella_data["weather_description"]
        
        # Generate clothing recommendation based on temperature
        if temp_c >= 30:
            clothing = "Light, breathable clothing (shorts, t-shirt, sunhat)"
        elif temp_c >= 20:
            clothing = "Comfortable warm weather clothing (light pants, short sleeves)"
        elif temp_c >= 10:
            clothing = "Layered clothing (long pants, long sleeves, light jacket)"
        else:
            clothing = "Warm clothing (heavy jacket, sweater, long pants)"
        
        # Build items to bring list
        items = []
        if precip_prob >= 30:
            items.append("Umbrella")
        if temp_c >= 25:
            items.extend(["Sunscreen", "Sunglasses", "Water bottle"])
        if temp_c < 10:
            items.extend(["Warm gloves", "Scarf"])
        
        # Activity recommendation
        if precip_prob >= 60:
            activity = "Indoor activities recommended (museums, shopping, restaurants)"
        elif temp_c >= 25 and precip_prob < 30:
            activity = "Great for outdoor activities (hiking, sightseeing, beach)"
        elif temp_c < 5:
            activity = "Cold weather activities (skiing, ice skating) or indoor venues"
        else:
            activity = "Good for general outdoor activities with some flexibility"
        
        # Overall suitability rating
        if precip_prob >= 70 or temp_c > 38 or temp_c < -5:
            suitability = "POOR"
            summary = "Challenging weather conditions for travel"
        elif precip_prob >= 40 or temp_c > 35 or temp_c < 0:
            suitability = "FAIR"
            summary = "Manageable weather with some precautions needed"
        elif precip_prob >= 20 or temp_c > 32 or temp_c < 5:
            suitability = "GOOD"
            summary = "Pleasant weather for most activities"
        else:
            suitability = "EXCELLENT"
            summary = "Ideal weather conditions for travel and outdoor activities"
        
        logger.info(f"Travel recommendation for {umbrella_data['location']}: {suitability}")
        
        return {
            "location": umbrella_data["location"],
            "date": umbrella_data["date"],
            "weather_summary": summary,
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": temp_f,
            "precipitation_probability_percent": precip_prob,
            "weather_description": weather_desc,
            "clothing_recommendation": clothing,
            "items_to_bring": items,
            "activity_recommendation": activity,
            "overall_suitability": suitability
        }
    except Exception as e:
        logger.error(f"Error getting travel recommendation for {location}: {e}")
        return {
            "error": str(e),
            "location": location,
            "date": date,
            "message": f"Failed to get travel recommendation for {location}"
        }


@mcp.tool
def get_severe_weather_alerts(location: str, days: int = 7) -> dict:
    """
    Check for severe weather alerts in the forecast for a specific location.
    
    Analyzes forecast data to identify potential severe weather conditions including:
    - Extreme temperatures (dangerously hot or cold)
    - Heavy precipitation (high probability of rain/snow)
    - Severe weather events (thunderstorms, heavy rain, heavy snow, hail)
    
    Args:
        location: Location name (e.g., "Chicago", "Miami, FL", "Denver, CO")
        days: Number of days to check for alerts (1-16, default 7)
    
    Returns:
        A dict with alert information:
        - location: Full location name
        - checked_days: Number of days analyzed
        - alerts_found: Number of alerts detected
        - has_severe_weather: Boolean indicating if any alerts exist
        - alerts: List of alert objects, each containing:
            - date: Date of the alert (YYYY-MM-DD)
            - severity: "HIGH" or "MODERATE"
            - type: Type of severe weather
            - description: Detailed description of the alert
            - temperature_max: High temperature for the day
            - precipitation_probability_percent: Chance of precipitation
            - weather_description: Overall weather conditions
    
    Examples:
        - get_severe_weather_alerts("Miami")  # Check next 7 days
        - get_severe_weather_alerts("Chicago", 3)  # Check next 3 days
        - get_severe_weather_alerts("Denver, CO", 14)  # Check next 14 days
    """
    logger.info(f"Checking severe weather alerts for {location} over {days} days")
    try:
        result = weather_broker.get_severe_weather_alerts(location, days)
        if result["has_severe_weather"]:
            logger.warning(f"Found {result['alerts_found']} severe weather alert(s) for {result['location']}")
        else:
            logger.info(f"No severe weather alerts for {result['location']}")
        return result
    except Exception as e:
        logger.error(f"Error checking severe weather alerts for {location}: {e}")
        return {
            "error": str(e),
            "location": location,
            "days": days,
            "message": f"Failed to check severe weather alerts for {location}"
        }


@mcp.tool
def get_current_user() -> dict:
    """
    Get information about the currently authenticated end user accessing the MCP server.
    
    When running as a Databricks App, this returns the service principal information.
    Request headers (like X-Forwarded-User) are handled by the App infrastructure.
    
    Returns:
        A dict with user_name and status.
    """
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        current_user = w.current_user.me()
        
        return {
            "status": "success",
            "user_name": current_user.user_name or 'unknown',
            "display_name": current_user.display_name or 'Unknown User',
            "source": "workspace_client",
        }
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve user information"
        }


if __name__ == "__main__":
    # Databricks Apps route external HTTP traffic to this port via app.yaml;
    # http transport is what Databricks' MCP client/gateway expects
    port = int(os.getenv("DATABRICKS_APP_PORT", os.getenv("PORT", 8000)))
    logger.info(f"Starting Weather MCP Server on http://0.0.0.0:{port}")
    mcp.run(transport="http", host="0.0.0.0", port=port)

