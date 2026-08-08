# Weather Dashboard 🌦️

A Flask-based web dashboard that visualizes real-time weather data from multiple cities using the Open-Meteo API. This dashboard provides a human-friendly UI for monitoring weather conditions, forecasts, and umbrella recommendations.

## Overview

This dashboard is part of the weather MCP server + Agent Bricks agent ecosystem:

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│                 │       │                 │       │                  │
│  Weather MCP    │◄──────│  Agent Bricks   │       │    Weather       │
│  Server         │       │  Agent          │       │    Dashboard     │
│  (mcp_server/)  │       │                 │       │   (dashboard/)   │
│                 │       └─────────────────┘       │                  │
└─────────────────┘                                 │                  │
        │                                           │                  │
        │                                           │                  │
        └───────────────────────────────────────────┴──────────────────┘
                                │
                                ▼
                        Open-Meteo API
                     (Free, No API Key)
```

* **Weather MCP Server** (`mcp_server/`): Provides tools for the agent to query weather data
* **Weather Dashboard** (`dashboard/`): Provides UI for humans to view weather data
* **Agent Bricks Agent**: Uses the MCP server to answer weather questions

Both apps use the **same `weather_broker.py`** module to access Open-Meteo API.

## Features

### 🌍 Multi-City Current Weather
* Live weather cards for 6 default cities (Chicago, New York, LA, Austin, Seattle, Miami)
* Click any city to see detailed forecast
* Temperature (°C and °F), humidity, wind speed, precipitation
* Weather icons and descriptions

### 📅 5-Day Forecast
* Daily high/low temperatures
* Weather conditions with icons
* Precipitation probability
* Click a city card to load its forecast

### ☂️ Umbrella Recommendation
* Smart umbrella prediction for tomorrow
* Risk level visualization (HIGH/MEDIUM/LOW)
* Reasoning based on precipitation probability
* Dynamic color-coding

### 🔄 Auto-Refresh
* Manual refresh button
* Automatic refresh every 5 minutes
* Last updated timestamp

## Quick Start

### Local Development

```bash
# Navigate to dashboard folder
cd dashboard

# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py

# Open browser
open http://localhost:8000
```

### Deploy to Databricks Apps

1. **Go to Compute → Apps → Create App**
2. **Settings:**
   * Type: Custom
   * Name: `weather-dashboard`
   * Source: `/Workspace/Users/<your-email>/ai_data_engineer_homework3/dashboard`
3. **Click Deploy**
4. **Access the Dashboard** via the app URL

No secrets or environment variables needed — Open-Meteo is 100% free!

## API Endpoints

The Flask app exposes several JSON API endpoints:

### `GET /api/current`
Get current weather for one or more cities.

**Query Params:**
* `cities` (optional): Comma-separated city names (default: all default cities)

**Example:**
```bash
curl "http://localhost:8000/api/current?cities=Chicago,Seattle"
```

**Response:**
```json
[
  {
    "city": "Chicago",
    "success": true,
    "data": {
      "location": "Chicago, Illinois, United States",
      "temperature_celsius": 24.5,
      "temperature_fahrenheit": 76.1,
      "humidity_percent": 65,
      "wind_speed_kmh": 12.3,
      "precipitation_mm": 0,
      "weather_description": "Partly cloudy",
      "timestamp": "2026-08-08T15:00"
    }
  }
]
```

### `GET /api/forecast`
Get weather forecast for a specific city.

**Query Params:**
* `city` (required): City name
* `days` (optional): Number of days (1-16, default 5)

**Example:**
```bash
curl "http://localhost:8000/api/forecast?city=Austin&days=5"
```

### `GET /api/umbrella`
Get umbrella recommendation for a specific city and date.

**Query Params:**
* `city` (required): City name
* `date` (optional): Date in YYYY-MM-DD format (default: tomorrow)

**Example:**
```bash
curl "http://localhost:8000/api/umbrella?city=Seattle&date=2026-08-10"
```

### `GET /api/compare`
Compare current weather across multiple cities with summary statistics.

**Query Params:**
* `cities` (required): Comma-separated city names

**Example:**
```bash
curl "http://localhost:8000/api/compare?cities=Chicago,Miami,Seattle"
```

## Architecture

```
dashboard/
├── app.py                    # Flask web application
├── weather_broker.py         # Open-Meteo API integration (same as mcp_server)
├── requirements.txt          # Python dependencies
├── app.yaml                  # Databricks App configuration
├── templates/
│   └── index.html           # Dashboard UI
└── README.md                # This file
```

### Key Components

**app.py**
* Flask web server with 5 API endpoints
* Serves HTML dashboard UI
* Error handling and health check

**weather_broker.py**
* Reusable module (shared with MCP server)
* Handles all HTTP calls to Open-Meteo API
* Data parsing and formatting

**templates/index.html**
* Interactive weather dashboard
* Responsive grid layout
* Real-time data fetching via JavaScript
* Auto-refresh every 5 minutes

## Customization

### Change Default Cities

Edit `DEFAULT_CITIES` in `app.py`:

```python
DEFAULT_CITIES = [
    "London",
    "Paris",
    "Tokyo",
    "Sydney"
]
```

### Change Refresh Interval

Edit the `setInterval` call in `templates/index.html`:

```javascript
// Change from 5 minutes (300000ms) to 10 minutes (600000ms)
setInterval(refresh, 600000);
```

### Add More Weather Details

Extend the `get_current_weather()` call in `weather_broker.py` to fetch additional fields from Open-Meteo:

```python
params = {
    "current": [
        "temperature_2m",
        "relative_humidity_2m",
        # Add more fields:
        "cloud_cover",
        "visibility",
        "uv_index"
    ]
}
```

Then update the UI in `index.html` to display them.

## Troubleshooting

### Dashboard won't start

**Check logs:**
```bash
# Local
python app.py
# Look for Flask errors

# Databricks Apps
Compute → Apps → weather-dashboard → Logs
```

**Common issues:**
* Missing `requirements.txt` dependencies
* Port 8000 already in use (change `FLASK_RUN_PORT`)
* Missing `templates/` folder or `index.html`

### Weather data not loading

**Check Open-Meteo status:**
https://status.open-meteo.com/

**Test the broker directly:**
```python
import weather_broker
print(weather_broker.get_current_weather("Chicago"))
```

**Check network/firewall:**
* Ensure outbound HTTPS is allowed
* Open-Meteo endpoints: `api.open-meteo.com`, `geocoding-api.open-meteo.com`

### City not found

**Use specific location names:**
* ✅ "Austin, Texas"
* ✅ "Portland, Oregon" (not just "Portland")
* ✅ "London, UK"
* ❌ "NYC" (use "New York")

### Forecast not updating

* Click **Refresh** button manually
* Check browser console for JavaScript errors
* Verify API endpoint returns valid JSON: `/api/forecast?city=Chicago`

## Performance

**API Call Volume:**
* Dashboard initial load: 1 current weather call (covers all default cities)
* Select city: 2 calls (forecast + umbrella)
* Auto-refresh: 1 call every 5 minutes

**Rate Limits:**
* Open-Meteo: 10,000 calls/day per IP
* This dashboard uses ~300 calls/day with 6 cities and 5-min refresh

## Comparison with MCP Server

| Feature | MCP Server | Dashboard |
|---------|------------|----------|
| **Purpose** | Agent tool provider | Human UI |
| **Protocol** | MCP (JSON-RPC) | HTTP/REST |
| **Consumer** | Agent Bricks agent | Web browser |
| **Endpoints** | 5 MCP tools | 4 REST endpoints |
| **UI** | None | Interactive web UI |
| **Refresh** | On-demand (agent calls) | Auto (5 min) |
| **Deployment** | Databricks App | Databricks App |

Both use the **same `weather_broker.py`** module, ensuring consistency.

## Next Steps

* [ ] Add more cities to monitor
* [ ] Implement city search (add custom cities)
* [ ] Save favorite cities to browser localStorage
* [ ] Add historical weather data comparison
* [ ] Integrate air quality index (AQI)
* [ ] Add severe weather alerts
* [ ] Create weather map view
* [ ] Export weather data to CSV

## Resources

* **Open-Meteo API Docs:** https://open-meteo.com/en/docs
* **Flask Documentation:** https://flask.palletsprojects.com/
* **Databricks Apps:** https://docs.databricks.com/apps/
* **Parent README:** `/ai_data_engineer_homework3/README.md`
* **MCP Server:** `/ai_data_engineer_homework3/mcp_server/`
* **Reference Pattern:** `/Zach_Bootcamp/databricks-lakebase-app-day-3/dashboard/`

## License

This is a homework/demo project. Open-Meteo API is free for non-commercial use.

---

**Ready to visualize weather data!** 🌞⛅🌧️
