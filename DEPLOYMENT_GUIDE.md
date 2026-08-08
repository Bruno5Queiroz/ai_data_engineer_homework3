# Weather MCP Server + Agent Deployment Guide

This guide walks you through deploying both the Weather MCP Server and the Weather Forecast Agent as Databricks Apps.

## Prerequisites

- Databricks workspace access
- Permissions to create Databricks Apps
- Permissions to register external MCPs in AI Gateway

## Architecture Overview

```
User
  ↓
  Chats with Agent Bricks Agent (Databricks App)
  ↓
  Agent calls tools via MCP
  ↓
Weather MCP Server (Databricks App)
  ↓
  Makes HTTP calls to Open-Meteo API
  ↓
Open-Meteo API (free, no auth)
```

## Step-by-Step Deployment

### Step 1: Deploy the Weather MCP Server

The MCP server must be deployed first so you can get its URL for the agent configuration.

#### Via Databricks UI (Recommended)

1. **Navigate to Apps:**
   - In your Databricks workspace, go to **Compute** → **Apps**
   - Click **Create App**

2. **Configure the App:**
   - **App Type:** Custom
   - **App Name:** `weather-mcp-server`
   - **Source Code:**
     - If using Git folder: Select your Git folder and choose the `ai_data_engineer_homework3/mcp_server/` subfolder
     - If using workspace path: `/Workspace/Users/<your-email>/ai_data_engineer_homework3/mcp_server`
   - **Environment Variables:** None required (Open-Meteo needs no API key)

3. **Deploy:**
   - Click **Deploy**
   - Wait 1-2 minutes for the app to start
   - Status will change from "Starting" to "Running"

4. **Copy the App URL:**
   - Once running, click on the app name
   - Copy the **App URL** (looks like: `https://<id>.cloud.databricks.com`)
   - You'll need this URL in Step 2
   - **Test the URL:** Open `<APP_URL>/tools` in a browser - should show 5 available tools

#### Via Databricks CLI (Alternative)

```bash
# From project root
cd ai_data_engineer_homework3/mcp_server

# Deploy the app
databricks apps deploy weather-mcp-server --source-code-path .

# Get the app URL
databricks apps get weather-mcp-server --output json | jq -r '.url'
```

### Step 2: Register the MCP Server in AI Gateway

Once the MCP server is running, register it as an external MCP so agents can discover its tools.

1. **Navigate to AI Gateway:**
   - In Databricks, go to **AI Gateway** → **MCPs**
   - Click **Add MCP** or **Register external MCP**

2. **Configure the MCP:**
   - **MCP Name:** `weather-forecast-mcp` (must match `agent_config.yaml`)
   - **Description:** "Provides weather forecasts, umbrella recommendations, and travel advice"
   - **Server URL:** Paste the app URL from Step 1
   - **Protocol:** Streamable HTTP (FastMCP)
   - **Authentication:** None required

3. **Save and Introspect:**
   - Click **Save**
   - Databricks will connect to the MCP server and discover its tools
   - You should see 5 tools listed:
     - `get_current_weather`
     - `get_forecast`
     - `predict_umbrella_needed`
     - `get_travel_recommendation`
     - `get_current_user`

4. **Verify Registration:**
   - Click on the registered MCP
   - Confirm all 5 tools are visible with their descriptions
   - Test one tool using the "Try it" feature if available

### Step 3: Create the Agent Bricks Agent

Now that the MCP is registered, create an agent that uses it.

#### Option A: Via Databricks UI (Easier)

1. **Navigate to Agents:**
   - Go to **AI/BI** → **Agents**
   - Click **Create Agent**

2. **Configure the Agent:**
   - **Agent Name:** `Weather Forecast Assistant`
   - **Description:** "AI assistant for weather forecasts and travel planning"
   - **Foundation Model:** Choose one:
     - `claude-3-5-sonnet` (recommended for quality)
     - `gpt-4o` (good alternative)
     - `llama-3.1-70b-instruct` (faster, less accurate)
   - **Temperature:** 0.1 (for consistent, factual responses)

3. **Enable External Tools:**
   - In the **Tools** section, enable **External MCPs**
   - Select `weather-forecast-mcp` from the dropdown
   - All 5 tools should appear as available

4. **Set System Prompt:**
   - Copy the entire system prompt from `agent/agent_config.yaml`
   - Paste it into the **System Prompt** field
   - The prompt is comprehensive and includes:
     - Tool usage guidelines
     - Error handling instructions
     - Example interactions
     - Response formatting rules

5. **Deploy the Agent:**
   - Click **Create** or **Deploy**
   - Wait for the agent to initialize
   - Once ready, you'll see a chat interface

#### Option B: Via Configuration File (Alternative)

If your Databricks workspace supports agent deployment from config:

```bash
# From project root
cd ai_data_engineer_homework3/agent

# Deploy using the config file
databricks agents deploy weather-assistant --config agent_config.yaml
```

### Step 4: Test the Agent

Once deployed, test the agent with various queries:

#### Test Query 1: Current Weather
```
What's the weather like in Chicago right now?
```

**Expected Behavior:**
- Agent calls `get_current_weather("Chicago")`
- Returns temperature, humidity, wind, conditions
- Response includes both Celsius and Fahrenheit

#### Test Query 2: Umbrella Recommendation
```
Should I bring an umbrella to Seattle tomorrow?
```

**Expected Behavior:**
- Agent calls `predict_umbrella_needed("Seattle")`
- Returns one of: BRING_UMBRELLA, MAYBE_BRING_UMBRELLA, NO_UMBRELLA_NEEDED
- Includes precipitation probability and reasoning

#### Test Query 3: Multi-Day Forecast
```
Give me a 5-day forecast for Austin, Texas
```

**Expected Behavior:**
- Agent calls `get_forecast("Austin, Texas", 5)`
- Returns 5 days of high/low temps and rain chances
- Formatted as a bulleted list

#### Test Query 4: Travel Planning
```
I'm traveling to Miami on August 20th, 2026. What should I pack?
```

**Expected Behavior:**
- Agent calls `get_travel_recommendation("Miami", "2026-08-20")`
- Returns comprehensive packing list
- Includes clothing, items, and activity suggestions

#### Test Query 5: Error Handling
```
What's the weather in Zzyzx?
```

**Expected Behavior:**
- Tool returns location not found error
- Agent explains the error clearly
- Suggests checking spelling or trying a different format

### Step 5: Verify End-to-End Flow

1. **Check MCP Server Logs:**
   - Go to **Compute** → **Apps** → `weather-mcp-server`
   - Click **Logs**
   - Look for INFO messages like:
     ```
     Getting current weather for: Chicago
     Successfully retrieved weather for Chicago, Illinois, United States
     ```

2. **Check Agent Response Quality:**
   - Responses should be conversational and helpful
   - Should include specific numbers (temps, percentages)
   - Should provide actionable advice, not just raw data

3. **Verify Tool Selection:**
   - Agent should choose the right tool for each query type
   - Should not call multiple tools unnecessarily
   - Should handle errors gracefully

## Troubleshooting

### Issue: MCP Server won't start

**Symptoms:**
- App status stuck on "Starting"
- App status shows "Failed"

**Solutions:**
1. Check the app logs for errors
2. Verify `requirements.txt` dependencies are valid
3. Ensure `app.yaml` points to `weather_mcp_server.py`
4. Check Python version (requires 3.9+)

**Common Errors:**
```
ModuleNotFoundError: No module named 'fastmcp'
→ Solution: Verify requirements.txt is in the same folder as app.yaml

ImportError: cannot import name 'FastMCP'
→ Solution: Update fastmcp to >= 3.2.0 in requirements.txt
```

### Issue: Agent can't connect to MCP server

**Symptoms:**
- Agent says "I don't have access to weather tools"
- Agent tries to make up weather data
- Agent returns "Tool not found" errors

**Solutions:**
1. Verify MCP server is running (check Apps page)
2. Confirm MCP is registered in AI Gateway with the correct URL
3. Check that MCP name in AI Gateway matches `agent_config.yaml` (`weather-forecast-mcp`)
4. Verify external MCPs are enabled in agent configuration
5. Test MCP server directly: `<APP_URL>/tools` should return tool list

### Issue: Tools return errors

**Symptoms:**
- "Location not found" for valid cities
- "API unavailable" messages
- Timeout errors

**Solutions:**
1. Test the weather broker locally (see README)
2. Check Open-Meteo API status: https://status.open-meteo.com/
3. Verify Databricks Apps can make outbound HTTPS calls
4. Check for typos in location names
5. Ensure dates are within 16-day forecast window

**Common Errors:**
```
ValueError: Location not found: Chicagoo
→ Solution: Check spelling (should be "Chicago")

ValueError: Date 2026-09-30 is not in the forecast range
→ Solution: Choose a date within the next 7-16 days

requests.exceptions.ConnectionError
→ Solution: Check Open-Meteo API status or retry in a moment
```

### Issue: Agent gives generic responses

**Symptoms:**
- Agent doesn't call any tools
- Agent says "I don't know" without trying tools
- Agent makes up weather data

**Solutions:**
1. Verify system prompt is copied correctly (from `agent_config.yaml`)
2. Check that external MCP tools are enabled
3. Ensure MCP registration was successful (all 5 tools visible)
4. Test agent with explicit tool-triggering phrases:
   - "Use the get_current_weather tool for Chicago"
   - "Call the forecast tool for Austin"

### Issue: Slow responses

**Symptoms:**
- Agent takes 30+ seconds to respond
- Timeout errors

**Solutions:**
1. Open-Meteo API typically responds in <500ms (not the bottleneck)
2. Databricks Apps cold starts can take 30-60 seconds on first request
3. Keep MCP server app "warm" with periodic health checks
4. Consider using a lighter foundation model (e.g., Llama over Claude)

**Warm-up Strategy:**
```bash
# Ping the MCP server every 5 minutes to keep it warm
watch -n 300 curl -s <APP_URL>/tools > /dev/null
```

## Updating the Deployment

### Update MCP Server Code

1. Edit files in `ai_data_engineer_homework3/mcp_server/`
2. If using Git folder: commit and push changes, then sync in Databricks
3. Restart the MCP server app:
   - Go to **Compute** → **Apps** → `weather-mcp-server`
   - Click **Restart** or **Redeploy**
4. Changes take effect after restart (1-2 minutes)

### Update Agent System Prompt

1. Edit `agent/agent_config.yaml`
2. In Databricks, go to **AI/BI** → **Agents** → Your agent
3. Update the **System Prompt** field
4. Click **Save**
5. Changes take effect immediately (no restart needed)

### Add New Tools

1. Add function to `mcp_server/weather_broker.py`
2. Add `@mcp.tool` decorator in `mcp_server/weather_mcp_server.py`
3. Redeploy MCP server app
4. Re-register MCP in AI Gateway (or click **Refresh** if available)
5. Update agent system prompt to mention the new tool
6. Test the new tool

## Production Considerations

### Rate Limiting

- Open-Meteo: 10,000 API calls/day per IP
- For production: implement caching layer (Redis, Lakebase, etc.)
- Cache current weather for 10 minutes
- Cache forecasts for 1 hour

### Monitoring

1. **MCP Server Health:**
   - Monitor app logs for errors
   - Set up alerting for app downtime
   - Track response times

2. **Agent Performance:**
   - Monitor tool call success rates
   - Track average response times
   - Review user feedback

3. **API Usage:**
   - Monitor Open-Meteo API call volume
   - Check for rate limit warnings
   - Track error rates by error type

### Security

- MCP server runs as a service principal (not as the calling user)
- No secrets needed (Open-Meteo is public API)
- Agent has access to MCP server URL (should be internal only)
- User identity passed via X-Forwarded-User header

### Scaling

- Databricks Apps auto-scale based on demand
- Open-Meteo API is highly available (99.9% uptime)
- For high traffic:
  - Deploy multiple MCP server instances
  - Use load balancer in front of MCP servers
  - Implement caching layer

## Next Steps

1. **Add More Tools:**
   - Air quality index
   - Severe weather alerts (requires different API)
   - Historical weather comparisons
   - Multi-location comparison

2. **Create Dashboard:**
   - Build a Flask/Streamlit dashboard
   - Show real-time weather visualizations
   - Display agent conversation history

3. **Integrate with Other Systems:**
   - Send weather alerts via email/Slack
   - Trigger workflows based on weather conditions
   - Store historical forecasts in Delta Lake

4. **Improve Agent:**
   - Add memory/context retention
   - Support follow-up questions
   - Implement user preferences (default location, units, etc.)

## Resources

- **Open-Meteo API Docs:** https://open-meteo.com/en/docs
- **Databricks MCP Docs:** https://docs.databricks.com/aws/en/agents/mcp-tools/
- **FastMCP Docs:** https://gofastmcp.com/
- **Agent Bricks Docs:** https://docs.databricks.com/aws/en/agents/

## Support

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Review MCP server logs in Databricks Apps
3. Test the weather broker locally
4. Check Open-Meteo API status
5. Verify all deployment steps were completed

## Summary Checklist

- [ ] MCP server deployed and running
- [ ] MCP server URL copied
- [ ] MCP registered in AI Gateway as `weather-forecast-mcp`
- [ ] All 5 tools visible in MCP registration
- [ ] Agent created with correct system prompt
- [ ] External MCP tools enabled in agent
- [ ] Agent tested with all 5 query types
- [ ] Errors handled gracefully
- [ ] Responses are helpful and actionable

Once all items are checked, your Weather MCP Server and Agent are production-ready! 🌦️
