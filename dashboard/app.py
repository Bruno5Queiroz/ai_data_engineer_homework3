"""
Weather Dashboard: a Flask app to VISUALIZE real-time weather data from
multiple cities using the Open-Meteo API via weather_broker.py.

This app provides a live dashboard showing:
- Current weather for multiple cities
- 5-day forecasts
- Umbrella recommendations
- Weather comparisons

Deploy this as a separate Databricks App from the weather MCP server -
one app serves MCP tool calls (for the agent), the other serves the
human-facing UI.

Run locally:
    python app.py
"""

import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

import weather_broker

app = Flask(__name__)

# Default cities to monitor
DEFAULT_CITIES = [
    "Chicago",
    "New York",
    "Los Angeles",
    "Austin, Texas",
    "Seattle",
    "Miami"
]


@app.route("/healthz")
def healthz():
    """Health check endpoint for Databricks Apps."""
    return jsonify({"status": "ok"})


@app.errorhandler(Exception)
def handle_exception(err):
    """Ensure all unhandled errors return JSON (not an HTML error page)."""
    status_code = getattr(err, "code", 500)
    if not isinstance(status_code, int):
        status_code = 500
    return jsonify({"error": str(err)}), status_code


@app.route("/")
def index():
    """Weather dashboard UI showing live weather data for multiple cities."""
    return render_template("index.html", default_cities=DEFAULT_CITIES)


@app.route("/api/current")
def api_current():
    """
    Get current weather for one or more cities.
    
    Query params:
        - cities: Comma-separated list of city names (e.g., "Chicago,Seattle")
        
    Returns:
        List of current weather data for each city
    """
    cities_param = request.args.get("cities", "")
    if not cities_param:
        cities = DEFAULT_CITIES
    else:
        cities = [c.strip() for c in cities_param.split(",") if c.strip()]
    
    results = []
    for city in cities:
        try:
            weather = weather_broker.get_current_weather(city)
            results.append({
                "city": city,
                "success": True,
                "data": weather
            })
        except Exception as e:
            results.append({
                "city": city,
                "success": False,
                "error": str(e)
            })
    
    return jsonify(results)


@app.route("/api/forecast")
def api_forecast():
    """
    Get weather forecast for a specific city.
    
    Query params:
        - city: City name (required)
        - days: Number of days (1-16, default 5)
        
    Returns:
        Forecast data for the city
    """
    city = request.args.get("city", "")
    if not city:
        return jsonify({"error": "city query param is required"}), 400
    
    days = int(request.args.get("days", 5))
    days = max(1, min(16, days))  # Clamp to valid range
    
    try:
        forecast = weather_broker.get_forecast(city, days)
        return jsonify({"success": True, "data": forecast})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/umbrella")
def api_umbrella():
    """
    Get umbrella recommendation for a specific city and date.
    
    Query params:
        - city: City name (required)
        - date: Date in YYYY-MM-DD format (default: tomorrow)
        
    Returns:
        Umbrella recommendation data
    """
    city = request.args.get("city", "")
    if not city:
        return jsonify({"error": "city query param is required"}), 400
    
    # Default to tomorrow if no date specified
    date_str = request.args.get("date", "")
    if not date_str:
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime("%Y-%m-%d")
    
    try:
        prediction = weather_broker.predict_umbrella_needed(city, date_str)
        return jsonify({"success": True, "data": prediction})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/compare")
def api_compare():
    """
    Compare current weather across multiple cities.
    
    Query params:
        - cities: Comma-separated list of city names (required)
        
    Returns:
        Comparison data for all cities with summary stats
    """
    cities_param = request.args.get("cities", "")
    if not cities_param:
        return jsonify({"error": "cities query param is required"}), 400
    
    cities = [c.strip() for c in cities_param.split(",") if c.strip()]
    
    results = []
    temps_c = []
    
    for city in cities:
        try:
            weather = weather_broker.get_current_weather(city)
            results.append({
                "city": city,
                "success": True,
                "data": weather
            })
            temps_c.append(weather["temperature_celsius"])
        except Exception as e:
            results.append({
                "city": city,
                "success": False,
                "error": str(e)
            })
    
    # Calculate summary stats
    summary = {}
    if temps_c:
        summary = {
            "avg_temp_celsius": round(sum(temps_c) / len(temps_c), 1),
            "max_temp_celsius": max(temps_c),
            "min_temp_celsius": min(temps_c),
            "temp_range_celsius": round(max(temps_c) - min(temps_c), 1)
        }
    
    return jsonify({
        "cities": results,
        "summary": summary
    })


if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", 8000))
    app.run(debug=True, host=host, port=port)
