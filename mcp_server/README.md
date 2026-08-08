# Weather MCP Server

## Overview

A production-ready Model Context Protocol (MCP) server that exposes weather forecast tools to Databricks Agent Bricks agents.

**Key Features:**
* 5 weather forecast tools via MCP protocol
* Powered by [Open-Meteo API](https://open-meteo.com/) (free, no API key required)
* Global coverage for any location worldwide
* Built with FastMCP for easy Databricks integration
* Comprehensive error handling with explicit error returns

## Files

* **weather_mcp_server.py** - FastMCP server with tool definitions
* **weather_broker.py** - Open-Meteo API integration layer (handles HTTP calls and parsing)
* **app.yaml** - Databricks App deployment configuration
* **requirements.txt** - Python dependencies
* **test_mcp_local.py** - Local testing script

## MCP Tools Exposed

### 1. get_current_weather(location: str)
Get real-time weather conditions.

**Parameters:**
* `location` (str): Location name (e.g., "Chicago", "Tokyo, Japan")

**Returns:**
```json
{
  "location": "Chicago, United States",
  "temperature_celsius": 24.5,
  "temperature_fahrenheit": 76.1,
  "feels_like_celsius": 23.8,
  "feels_like_fahrenheit": 74.8,
  "humidity_percent": 62,
  "wind_speed_kmh": 15.3,
  "wind_speed_mph": 9.5,
  "precipitation_mm": 0.0,
  "weather_description": "Partly cloudy",
  "timestamp": "2026-08-08T15:30:00"
}
```

---

### 2. get_forecast(location: str, days: int = 7)
Get multi-day weather forecast (1-16 days).

**Parameters:**
* `location` (str): Location name
* `days` (int): Number of days to forecast (1-16, default 7)

**Returns:**
```json
{
  "location": "Austin, Texas, United States",
  "forecast_days": 5,
  "daily_forecast": [
    {
      "date": "2026-08-08",
      "temperature_max_celsius": 38.2,
      "temperature_max_fahrenheit": 100.8,
      "temperature_min_celsius": 26.5,
      "temperature_min_fahrenheit": 79.7,
      "precipitation_probability_percent": 15,
      "weather_description": "Sunny"
    }
  ]
}
```

---

### 3. predict_umbrella_needed(location: str, date: str = None)
Intelligent umbrella recommendation.

**Parameters:**
* `location` (str): Location name
* `date` (str, optional): Target date (YYYY-MM-DD). Defaults to tomorrow.

**Returns:**
```json
{
  "location": "Seattle, Washington, United States",
  "date": "2026-08-15",
  "umbrella_recommendation": "BRING_UMBRELLA",
  "risk_level": "HIGH",
  "precipitation_probability_percent": 75,
  "temperature_max_celsius": 19.5,
  "temperature_max_fahrenheit": 67.1,
  "weather_description": "Rain showers",
  "reasoning": "High precipitation probability (75%) indicates significant rain likelihood."
}
```

---

### 4. get_travel_recommendation(location: str, date: str = None)
Comprehensive travel weather assessment.

**Parameters:**
* `location` (str): Location name
* `date` (str, optional): Target date (YYYY-MM-DD). Defaults to tomorrow.

**Returns:**
```json
{
  "location": "Miami, Florida, United States",
  "date": "2026-08-20",
  "weather_summary": "Hot and sunny conditions",
  "temperature_celsius": 32.5,
  "temperature_fahrenheit": 90.5,
  "precipitation_probability_percent": 20,
  "clothing_recommendation": "Light, breathable clothing (shorts, t-shirt, sunhat)",
  "items_to_bring": [
    "Sunscreen",
    "Sunglasses",
    "Water bottle"
  ],
  "activity_recommendation": "Excellent for beach activities, water sports, and outdoor dining.",
  "overall_suitability": "EXCELLENT"
}
```

---

### 5. get_severe_weather_alerts(location: str, days: int = 7)
Check for severe weather warnings.

**Parameters:**
* `location` (str): Location name
* `days` (int): Number of days to check (1-16, default 7)

**Returns:**
```json
{
  "location": "Houston, Texas, United States",
  "alert_days": 7,
  "severe_weather_detected": false,
  "alerts": [],
  "temperature_range": {
    "min_celsius": 25.3,
    "max_celsius": 35.8,
    "min_fahrenheit": 77.5,
    "max_fahrenheit": 96.4
  },
  "summary": "No severe weather alerts for the next 7 days."
}
```

---

## Error Handling

All MCP tools implement comprehensive error handling with explicit error returns. When an error occurs (invalid location, API failure, etc.), the tool returns a structured error response instead of raising an exception.

### Error Response Format

All tools return errors in this consistent format:

```json
{
  "error": "<error_type_or_message>",
  "location": "<requested_location>",
  "message": "<human_readable_error_description>"
}
```

### Common Error Scenarios

#### 1. Invalid Location

**Request:**
```json
{
  "tool": "get_current_weather",
  "arguments": {"location": "InvalidCityXYZ123"}
}
```

**Response:**
```json
{
  "error": "Location not found: InvalidCityXYZ123",
  "location": "InvalidCityXYZ123",
  "message": "Failed to retrieve current weather for InvalidCityXYZ123"
}
```

**Explanation:** The geocoding API couldn't find the requested location. The agent should ask the user to clarify or provide a different location name.

---

#### 2. Invalid Date Format

**Request:**
```json
{
  "tool": "predict_umbrella_needed",
  "arguments": {
    "location": "Chicago",
    "date": "08/15/2026"
  }
}
```

**Response:**
```json
{
  "error": "Invalid date format. Expected YYYY-MM-DD, got: 08/15/2026",
  "location": "Chicago",
  "date": "08/15/2026",
  "message": "Failed to predict umbrella need for Chicago"
}
```

**Explanation:** Dates must be in ISO format (YYYY-MM-DD). The agent should reformat and retry, or ask the user for the correct format.

---

#### 3. Date Out of Range

**Request:**
```json
{
  "tool": "get_forecast",
  "arguments": {
    "location": "Austin",
    "days": 30
  }
}
```

**Response:**
```json
{
  "error": "Invalid days parameter: 30. Must be between 1 and 16.",
  "location": "Austin",
  "days": 30,
  "message": "Failed to retrieve forecast for Austin"
}
```

**Explanation:** Open-Meteo only provides up to 16 days of forecast data. The agent should adjust the request to 16 days or less.

---

#### 4. API Connection Failure

**Request:**
```json
{
  "tool": "get_current_weather",
  "arguments": {"location": "Chicago"}
}
```

**Response:**
```json
{
  "error": "HTTPError: Connection timeout to Open-Meteo API",
  "location": "Chicago",
  "message": "Failed to retrieve current weather for Chicago"
}
```

**Explanation:** Network issue or API outage. The agent should inform the user of temporary unavailability and suggest retrying later.

---

#### 5. Missing Required Parameter

**Request:**
```json
{
  "tool": "get_current_weather",
  "arguments": {}
}
```

**Response:**
```json
{
  "error": "TypeError: missing 1 required positional argument: 'location'",
  "location": null,
  "message": "Failed to retrieve current weather for None"
}
```

**Explanation:** The `location` parameter is required. FastMCP enforces this at the tool definition level, but the explicit error return ensures agents can handle it gracefully.

---

### Error Handling Best Practices for Agents

When integrating this MCP server with an agent:

1. **Always check for the `error` field** in tool responses
2. **Parse the error message** to understand the failure type
3. **Don't show raw error messages** to users - translate them into user-friendly language
4. **Retry with corrections** when possible (e.g., adjust date format, reduce days)
5. **Provide alternatives** when a location fails (suggest nearby cities or ask for clarification)

**Example Agent Error Handling:**

```python
response = call_tool("get_current_weather", {"location": user_input})

if "error" in response:
    if "Location not found" in response["error"]:
        return "I couldn't find weather data for that location. Could you try a different city name or add a state/country?"
    elif "API" in response["error"]:
        return "Weather service is temporarily unavailable. Please try again in a moment."
    else:
        return f"Couldn't retrieve weather data: {response['message']}"
else:
    # Process successful weather data
    return format_weather_response(response)
```

---

## Deployment

### Deploy as Databricks App

1. **Create App via UI:**
   - Compute > Apps > Create App
   - Name: `weather-mcp-server` (or your preferred name)
   - Source: Select this `mcp_server/` directory
   - Deploy

2. **Deploy via CLI:**
   ```bash
   cd mcp_server
   databricks apps deploy weather-mcp-server --source-code-path .
   ```

3. **Copy the App URL** - needed for agent integration

### Register as External MCP

1. Go to **AI Gateway** > **MCPs** > **Add MCP**
2. **Server URL:** Paste your app URL
3. **Protocol:** Streamable HTTP (FastMCP)
4. **Name:** `weather-forecast-mcp`
5. Save - Databricks will introspect and list the 5 tools

### Connect to Agent

In your agent configuration, add the MCP server:

```python
MCP_SERVERS = [
    ('weather-forecast-mcp', '<your-app-url>/mcp'),
]
```

---

## Local Testing

### Run Locally

```bash
cd mcp_server
pip install -r requirements.txt
python weather_mcp_server.py
```

Server starts on `http://0.0.0.0:8000`

### Test Tools

**List available tools:**
```bash
curl http://localhost:8000/tools
```

**Call a tool:**
```bash
curl -X POST http://localhost:8000/tools/get_current_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Chicago"}'
```

**Test error handling:**
```bash
# Invalid location
curl -X POST http://localhost:8000/tools/get_current_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "InvalidCity123"}'

# Invalid date format
curl -X POST http://localhost:8000/tools/predict_umbrella_needed \
  -H "Content-Type: application/json" \
  -d '{"location": "Chicago", "date": "08/15/2026"}'

# Days out of range
curl -X POST http://localhost:8000/tools/get_forecast \
  -H "Content-Type: application/json" \
  -d '{"location": "Austin", "days": 30}'
```

---

## Weather API Details

**Provider:** [Open-Meteo](https://open-meteo.com/)  
**Authentication:** None (100% free, no API key)  
**Rate Limits:** 10,000 API calls per day per IP  
**Coverage:** Global weather data for any location  
**Data Sources:** NOAA, DWD, MeteoFrance, and other national weather services  

**API Endpoints Used:**
1. **Geocoding:** `https://geocoding-api.open-meteo.com/v1/search`
2. **Weather Forecast:** `https://api.open-meteo.com/v1/forecast`

---

## Architecture

```
Agent Request
     |
     v
weather_mcp_server.py  (FastMCP tool definitions)
     |
     v
weather_broker.py      (API integration layer)
     |
     v
Open-Meteo API        (weather data source)
```

**Design Pattern:**
* **weather_mcp_server.py** - Thin tool wrappers with FastMCP decorators
* **weather_broker.py** - All HTTP calls, error handling, and data parsing
* This separation makes it easy to swap data sources without changing tool interfaces

---

## Dependencies

See `requirements.txt`:

* **fastmcp** - FastMCP server framework
* **httpx** - Async HTTP client for API calls
* **uvicorn** - ASGI server

---

## License

MIT License - see project root for details.
