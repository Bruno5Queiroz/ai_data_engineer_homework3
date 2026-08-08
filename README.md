# Weather Forecast MCP Server + Databricks Agent Bricks Agent

## Overview

This project implements a weather forecasting system using:
- **Weather MCP Server** (`mcp_server/`) - Exposes weather forecast tools over the Model Context Protocol (MCP)
- **Databricks Agent Bricks Agent** - Connects to the MCP server and answers weather questions

The MCP server provides real-time weather data and intelligent recommendations powered by the free [Open-Meteo API](https://open-meteo.com/), requiring **no API key or registration**.

## Architecture

```
Databricks Agent Bricks Agent  --(MCP tool calls)-->  weather_mcp_server.py  --(REST)-->  Open-Meteo API
                                                               |
                                                               v
                                                       weather_broker.py
                                                    (API integration layer)
```

**Design Pattern:**
- `weather_mcp_server.py` - Thin MCP tool definitions using FastMCP decorators
- `weather_broker.py` - All HTTP calls, data parsing, and business logic
- This separation keeps tool functions focused and makes it easy to swap data sources

## Weather API: Open-Meteo

**API Provider:** [Open-Meteo](https://open-meteo.com/)

**Why Open-Meteo?**
- **100% Free** - No paid tier, no credit card required
- **No API Key** - No registration or authentication needed
- **High Quality** - Combines data from multiple weather models (NOAA, DWD, MeteoFrance, etc.)
- **Global Coverage** - Weather data for any location worldwide
- **Rich Data** - Current conditions, forecasts, historical data

**Authentication:** None required. Open-Meteo is completely open and free to use.

**Rate Limits:** 10,000 API calls per day per IP address (sufficient for development and demos).

**API Endpoints Used:**
1. **Geocoding API** - Converts location names to coordinates
   - `https://geocoding-api.open-meteo.com/v1/search`
2. **Weather Forecast API** - Current conditions and forecasts
   - `https://api.open-meteo.com/v1/forecast`

## MCP Tools Exposed

The MCP server exposes **5 tools** that agents can call:

### 1. `get_current_weather(location: str)`
Get real-time weather conditions for any location.

**Returns:**
- Temperature (Celsius & Fahrenheit)
- Feels-like temperature
- Humidity percentage
- Wind speed (km/h & mph)
- Precipitation amount
- Weather description
- Timestamp

**Example:**
```python
get_current_weather("Chicago")
# Returns current temperature, humidity, wind, etc.
```


### 2. `get_forecast(location: str, days: int = 7)`
Get multi-day weather forecast (1-16 days).

**Returns:**
- Daily high/low temperatures
- Precipitation probability
- Weather conditions
- Timezone-adjusted dates

**Example:**
```python
get_forecast("Austin, Texas", 5)
# Returns 5-day forecast with temps and rain chances
```

### 3. `predict_umbrella_needed(location: str, date: str = None)`
Intelligent umbrella recommendation based on precipitation probability.

**Logic:**
- **HIGH risk (≥60%)**: BRING_UMBRELLA
- **MEDIUM risk (30-59%)**: MAYBE_BRING_UMBRELLA  
- **LOW risk (<30%)**: NO_UMBRELLA_NEEDED

**Returns:**
- Recommendation (BRING_UMBRELLA / MAYBE_BRING_UMBRELLA / NO_UMBRELLA_NEEDED)
- Risk level (HIGH / MEDIUM / LOW)
- Precipitation probability
- Temperature forecast
- Reasoning explanation

**Example:**
```python
predict_umbrella_needed("Seattle", "2026-08-15")
# Returns: BRING_UMBRELLA, HIGH risk, 75% rain chance
```

### 4. `get_travel_recommendation(location: str, date: str = None)`
Comprehensive travel weather assessment with actionable advice.

**Returns:**
- Weather summary
- Clothing recommendations
- Items to bring (umbrella, sunscreen, etc.)
- Activity suggestions
- Overall suitability rating (EXCELLENT / GOOD / FAIR / POOR)

**Example:**
```python
get_travel_recommendation("Miami", "2026-08-20")
# Returns: Wear light clothing, bring sunscreen, great for beach activities
```

### 5. `get_current_user()`
Utility tool to identify the end user making requests.

**Returns:**
- User email (from X-Forwarded-User header in Databricks Apps)
- Source (request_header or service_principal)

## Recommended System Prompt Configuration

For optimal agent behavior, include these guidelines in your agent's system prompt:

### Default Location
**When a user asks about weather without specifying a location, assume they mean Boston, MA.**

### Response Sequence
**Always follow this sequence:**
1. **Current Weather First**: Start with current conditions (temperature, precipitation, wind, etc.)
2. **Forecast Next**: Follow with the multi-day forecast (default 7 days)
3. **Severe Weather Check**: If checking more than 3 days ahead, proactively check for severe weather alerts
4. **Actionable Advice**: End with practical recommendations (umbrella needed, what to wear, etc.)

This ensures consistent, comprehensive responses that provide maximum value to users.

## File Structure

```
ai_data_engineer_homework3/
├── README.md                      # This file
├── mcp_server/                    # Weather MCP Server (Databricks App #1)
│   ├── weather_mcp_server.py      # FastMCP server with tool definitions
│   ├── weather_broker.py          # Open-Meteo API integration layer
│   ├── requirements.txt           # Python dependencies
│   └── app.yaml                   # Databricks App config
└── agent/                         # Agent Bricks Agent (Databricks App #2)
    ├── agent_config.yaml          # Agent configuration and system prompt
    └── app.yaml                   # Databricks App config
```

## Setup Instructions

### Prerequisites
- Databricks workspace
- Python 3.9+
- Git (for deployment via Git folders)

### Step 1: Local Development (Optional)

Test the MCP server locally before deploying:

```bash
# Navigate to mcp_server directory
cd mcp_server

# Install dependencies
pip install -r requirements.txt

# Run the server
python weather_mcp_server.py
# Server starts on http://0.0.0.0:8000
```

Test with curl:
```bash
curl http://localhost:8000/tools
# Should list 5 available tools

curl -X POST http://localhost:8000/tools/get_current_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Chicago"}'
```

### Step 2: Deploy MCP Server as Databricks App

#### Option A: Via Git Folder (Recommended)

1. **Create or sync a Git folder** in Databricks:
   - Go to **Workspace** > **Create** > **Git folder**
   - Connect to this repo
   - Clone or pull latest changes

2. **Deploy the MCP Server App:**
   - Navigate to **Compute** > **Apps** > **Create App**
   - Choose **Custom** app type
   - **Name:** `weather-mcp-server`
   - **Source:** Select the Git folder's `ai_data_engineer_homework3/mcp_server/` subfolder
   - **Deploy** and wait for startup
   - **Copy the App URL** - you'll need this for the agent

#### Option B: Via Databricks CLI

```bash
# From project root
cd mcp_server
databricks apps deploy weather-mcp-server --source-code-path .
```

### Step 3: Register MCP Server as External MCP

1. In Databricks workspace, go to **AI Gateway** > **MCPs** > **Add MCP** (or **Register external MCP**)
2. **Server URL:** Paste the app URL from Step 2 (ends in `.cloud.databricks.com`)
3. **Protocol:** Streamable HTTP (FastMCP)
4. **Name:** `weather-forecast-mcp`
5. **Save** - Databricks will introspect and list the 5 tools

### Step 4: Create Agent Bricks Agent

1. Go to **AI/BI** > **Agents** > **Create Agent**
2. **Name:** `Weather Forecast Assistant`
3. **Model:** Choose a foundation model (e.g., `claude-3-5-sonnet`, `gpt-4o`)
4. **External Tools:** Enable and select `weather-forecast-mcp`
5. **System Prompt:**

> **Note:** See the "Recommended System Prompt Configuration" section above for best practices on default locations and response sequencing.

```
You are a helpful weather assistant that provides accurate, actionable weather information.

You have access to weather forecast tools via an external MCP server. Use them to:
- Answer questions about current weather conditions
- Provide multi-day forecasts
- Make umbrella recommendations based on precipitation
- Give travel planning advice

AVAILABLE TOOLS:
- get_current_weather(location): Current conditions (temp, humidity, wind, precipitation)
- get_forecast(location, days): Multi-day forecast (1-16 days)
- predict_umbrella_needed(location, date): Umbrella recommendation with reasoning
- get_travel_recommendation(location, date): Comprehensive travel weather advice

GUIDELINES:
1. Location handling:
   - If user doesn't specify a location, assume Boston, MA as the default
   - Accept city names, "city, state", or "city, country" formats
   - Handle ambiguous locations by asking for clarification

2. Date handling:
   - If no date specified for umbrella/travel tools, they default to tomorrow
   - Dates must be in YYYY-MM-DD format
   - Forecasts available for up to 16 days ahead

3. Error handling:
   - If a tool returns an error, explain the issue clearly
   - Common errors: location not found, date out of range, API unavailable
   - Suggest alternatives when appropriate

4. Response format:
   - Be concise but informative
   - Include specific numbers (temperature, %, etc.)
   - Provide actionable advice
   - Use appropriate units (show both Celsius and Fahrenheit for temperature)

5. Proactive recommendations:
   - For travel questions, suggest using get_travel_recommendation
   - For "should I bring an umbrella" questions, use predict_umbrella_needed
   - For general weather curiosity, start with current conditions

6. Response sequence (best practice):
   - Start with current weather conditions
   - Follow with multi-day forecast (default 7 days)
   - If checking 3+ days ahead, check for severe weather alerts
   - End with actionable advice (umbrella, clothing, activities)

EXAMPLE INTERACTIONS:

User: "What's the weather like in Chicago?"
Assistant: 
1. Calls get_current_weather("Chicago") for current conditions
2. Calls get_forecast("Chicago", 7) for the week ahead
3. Summarizes both with actionable advice

User: "Should I bring an umbrella to Seattle next week?"
Assistant: Asks for specific date, then calls predict_umbrella_needed("Seattle", "YYYY-MM-DD") and explains recommendation.

User: "I'm traveling to Miami on August 20th. What should I pack?"
Assistant: Calls get_travel_recommendation("Miami", "2026-08-20") and provides clothing, items, and activity suggestions.

User: "What's the weather?" (no location specified)
Assistant: 
1. Assumes Boston, MA as default location
2. Calls get_current_weather("Boston, MA")
3. Calls get_forecast("Boston, MA", 7)
4. Provides comprehensive weather update with actionable advice

Always be helpful, accurate, and weather-wise!
```

6. **Deploy** the agent

### Step 5: Test the Agent

1. Open the deployed agent
2. Try these test queries:
   - "What's the weather in Chicago?"
   - "Should I bring an umbrella to Seattle tomorrow?"
   - "Give me a 5-day forecast for Austin, Texas"
   - "I'm traveling to Miami on August 20th. What should I expect?"

## Usage Examples

### Via Agent Chat Interface

**Query:** "What's the weather like in New York right now?"

**Agent Response:**
> Currently in New York, NY, United States:
> - Temperature: 24.5°C (76.1°F)
> - Feels like: 26.2°C (79.2°F)
> - Humidity: 68%
> - Wind: 12.3 km/h (7.6 mph)
> - Conditions: Partly cloudy
> - No precipitation

---

**Query:** "Should I bring an umbrella to London tomorrow?"

**Agent Response:**
> For London, UK on August 9, 2026:
> 
> **Recommendation: MAYBE_BRING_UMBRELLA**
> 
> Risk Level: MEDIUM  
> Precipitation Probability: 45%  
> High Temperature: 18.5°C (65.3°F)  
> Conditions: Light rain expected
> 
> Reasoning: Moderate chance of precipitation (45%). Consider bringing an umbrella as a precaution.

---

**Query:** "What's the forecast for Miami this weekend?"

**Agent Response:**
> 3-day forecast for Miami, FL, United States:
> 
> **August 9, 2026:**
> - High: 32.1°C (89.8°F), Low: 26.3°C (79.3°F)
> - Precipitation: 30%
> - Conditions: Partly cloudy
> 
> **August 10, 2026:**
> - High: 31.8°C (89.2°F), Low: 26.8°C (80.2°F)
> - Precipitation: 40%
> - Conditions: Partly cloudy
> 
> **August 11, 2026:**
> - High: 32.5°C (90.5°F), Low: 27.1°C (80.8°F)
> - Precipitation: 25%
> - Conditions: Mainly clear

## Error Handling

The MCP server and agent handle various error scenarios:

### Location Not Found
**Error:** `ValueError: Location not found: Zzyzx`  
**Agent Response:** "I couldn't find weather data for that location. Please check the spelling or try a different format (e.g., 'City, State' or 'City, Country')."

### Date Out of Range
**Error:** `ValueError: Date 2026-09-30 is not in the forecast range`  
**Agent Response:** "Forecasts are only available for the next 7-16 days. Please choose a date closer to today."

### API Unavailable
**Error:** `requests.exceptions.ConnectionError`  
**Agent Response:** "I'm having trouble connecting to the weather service right now. Please try again in a moment."

### Invalid Date Format
**Error:** `ValueError: Invalid date format`  
**Agent Response:** "Please provide the date in YYYY-MM-DD format (e.g., 2026-08-15)."

## Advanced Configuration

### Customizing Umbrella Thresholds

Edit `weather_broker.py`, function `predict_umbrella_needed()`, lines ~337-347:

```python
if precip_prob >= 60:  # Change this threshold
    recommendation = "BRING_UMBRELLA"
    risk_level = "HIGH"
elif precip_prob >= 30:  # Change this threshold
    recommendation = "MAYBE_BRING_UMBRELLA"
    risk_level = "MEDIUM"
```

### Adding New Tools

1. **Add business logic to `weather_broker.py`:**
```python
def get_pollen_forecast(location: str) -> dict:
    # Implementation using Open-Meteo air quality API
    pass
```

2. **Expose as MCP tool in `weather_mcp_server.py`:**
```python
@mcp.tool
def get_pollen_forecast(location: str) -> dict:
    """
    Get pollen forecast for allergy planning.
    
    Args:
        location: Location name
    
    Returns:
        Pollen levels and allergy recommendations
    """
    return weather_broker.get_pollen_forecast(location)
```

3. **Update agent system prompt** to mention the new tool
4. **Redeploy** both MCP server and agent

## Troubleshooting

### MCP Server won't start
- Check logs in Databricks Apps UI
- Verify `requirements.txt` dependencies are compatible
- Ensure `app.yaml` points to correct entry file

### Agent can't connect to MCP server
- Verify MCP server is running (check Apps page)
- Confirm MCP server URL is registered correctly in AI Gateway
- Check that external MCP is enabled in agent configuration

### Tools return errors
- Test MCP server locally with curl
- Check Open-Meteo API status: https://status.open-meteo.com/
- Verify location name spelling
- Ensure date is within forecast range (next 16 days)

### Slow responses
- Open-Meteo API typically responds in <500ms
- Databricks Apps cold starts can take 30-60 seconds
- Consider keeping MCP server app "warm" with periodic health checks

## Limitations

1. **Forecast Range:** Open-Meteo provides up to 16 days of forecast data
2. **Rate Limits:** 10,000 API calls/day per IP (sufficient for demos)
3. **Historical Data:** Not implemented in this project (but available via Open-Meteo)
4. **Severe Weather Alerts:** Not included (would require additional API integration)

## Future Enhancements

- [ ] Add air quality index tool
- [ ] Implement severe weather alerts
- [ ] Add historical weather comparisons
- [ ] Create a dashboard app to visualize forecasts
- [ ] Add caching layer to reduce API calls
- [ ] Implement location favorites
- [ ] Add multi-location comparison tool

## References

- **Open-Meteo API Documentation:** https://open-meteo.com/en/docs
- **Databricks MCP Documentation:** https://docs.databricks.com/aws/en/agents/mcp-tools/
- **FastMCP Documentation:** https://gofastmcp.com/
- **Agent Bricks Documentation:** https://docs.databricks.com/aws/en/agents/
- **Reference Pattern (Day 3):** `/Workspace/Users/brunotqgfc@gmail.com/Zach_Bootcamp/databricks-lakebase-app-day-3`

## License

This project is for educational purposes as part of the Databricks AI Data Engineer bootcamp.

## Author

Created as homework assignment #3 for the Databricks AI Data Engineer bootcamp.
