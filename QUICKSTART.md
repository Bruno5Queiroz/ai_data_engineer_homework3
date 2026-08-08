# Weather MCP Server - Quick Start Guide

**5-minute setup for the impatient!** 🚀

For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## What You're Building

```
User asks: "What's the weather in Chicago?"
  ↓
Databricks Agent (Weather Forecast Assistant)
  ↓ calls MCP tool: get_current_weather("Chicago")
Weather MCP Server (Databricks App)
  ↓ HTTP request
Open-Meteo API (free, no auth)
  ↓ returns data
Agent responds: "Currently 24°C (75°F), partly cloudy..."
```

## Prerequisites

- Databricks workspace
- Permissions to create Apps and register MCPs
- 5 minutes

## 3-Step Deployment

### Step 1: Deploy MCP Server (2 min)

1. Go to **Compute** → **Apps** → **Create App**
2. Settings:
   - **Type:** Custom
   - **Name:** `weather-mcp-server`
   - **Source:** `/Workspace/Users/<your-email>/ai_data_engineer_homework3/mcp_server`
3. Click **Deploy**
4. **Copy the App URL** when it starts

### Step 2: Register MCP (1 min)

1. Go to **AI Gateway** → **MCPs** → **Add MCP**
2. Settings:
   - **Name:** `weather-forecast-mcp`
   - **URL:** Paste the app URL from Step 1
   - **Protocol:** Streamable HTTP
3. Click **Save**
4. Verify 5 tools appear (get_current_weather, get_forecast, etc.)

### Step 3: Create Agent (2 min)

1. Go to **AI/BI** → **Agents** → **Create Agent**
2. Settings:
   - **Name:** `Weather Forecast Assistant`
   - **Model:** claude-3-5-sonnet (or gpt-4o)
   - **Temperature:** 0.1
   - **External Tools:** Enable and select `weather-forecast-mcp`
   - **System Prompt:** Copy from `agent/agent_config.yaml` (lines 15-147)
3. Click **Deploy**

## Test It!

Try these queries in the agent chat:

```
1. What's the weather in Chicago?
2. Should I bring an umbrella to Seattle tomorrow?
3. Give me a 5-day forecast for Austin, Texas
4. I'm traveling to Miami on August 20th. What should I pack?
```

Expected: Agent calls the right tool, returns helpful weather info with temps, rain chances, and advice.

## Troubleshooting

**MCP server won't start:**
- Check logs in Compute → Apps → weather-mcp-server
- Verify `requirements.txt` and `app.yaml` are in the mcp_server folder

**Agent doesn't call tools:**
- Verify MCP is registered with exact name `weather-forecast-mcp`
- Check that external tools are enabled in agent config
- Confirm system prompt is copied correctly

**Tool returns errors:**
- Test locally: `cd mcp_server && python test_mcp_local.py`
- Check Open-Meteo status: https://status.open-meteo.com/
- Verify location spelling (e.g., "Chicago" not "Chicagoo")

## What's Inside

```
ai_data_engineer_homework3/
├── README.md                      # Full documentation
├── DEPLOYMENT_GUIDE.md            # Detailed deployment steps
├── QUICKSTART.md                  # This file
├── mcp_server/                    # Weather MCP Server
│   ├── weather_mcp_server.py      # FastMCP server (5 tools)
│   ├── weather_broker.py          # Open-Meteo API integration
│   ├── requirements.txt           # Python dependencies
│   ├── app.yaml                   # Databricks App config
│   └── test_mcp_local.py          # Local test suite
└── agent/
    └── agent_config.yaml          # Agent system prompt
```

## 5 MCP Tools Available

1. **get_current_weather(location)** - Current conditions
2. **get_forecast(location, days)** - Multi-day forecast (1-16 days)
3. **predict_umbrella_needed(location, date)** - Umbrella recommendation
4. **get_travel_recommendation(location, date)** - Comprehensive travel advice
5. **get_current_user()** - User identity (for logging/personalization)

## API Details

- **Provider:** [Open-Meteo](https://open-meteo.com/)
- **Auth:** None required (100% free)
- **Rate Limit:** 10,000 calls/day per IP
- **Coverage:** Global
- **Data Quality:** Combines NOAA, DWD, MeteoFrance models

## Local Testing (Optional)

```bash
cd ai_data_engineer_homework3/mcp_server

# Install dependencies
pip install -r requirements.txt

# Run test suite
python test_mcp_local.py

# Run MCP server locally
python weather_mcp_server.py
# Access at http://localhost:8000

# Test with curl
curl http://localhost:8000/tools
curl -X POST http://localhost:8000/tools/get_current_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Chicago"}'
```

## Next Steps

- [ ] Add air quality tool
- [ ] Create weather dashboard
- [ ] Add caching layer (Redis/Lakebase)
- [ ] Implement severe weather alerts
- [ ] Support multi-location comparison

## Resources

- **Full Documentation:** [README.md](README.md)
- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Open-Meteo API:** https://open-meteo.com/en/docs
- **Databricks MCP Docs:** https://docs.databricks.com/aws/en/agents/mcp-tools/
- **Reference Pattern:** `/Workspace/Users/brunotqgfc@gmail.com/Zach_Bootcamp/databricks-lakebase-app-day-3`

## Need Help?

1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) Troubleshooting section
2. Run `python test_mcp_local.py` to test broker functions
3. Check MCP server logs in Databricks Apps
4. Verify all 5 tools are visible in MCP registration
5. Test agent with explicit tool names ("Use get_current_weather for Chicago")

---

**Ready? Let's deploy!** 🌦️

```bash
# Verify everything is here
ls mcp_server/
# Expected: weather_mcp_server.py, weather_broker.py, requirements.txt, app.yaml

# Run tests
cd mcp_server && python test_mcp_local.py
# Expected: All tests pass

# Now follow Steps 1-3 above!
```
