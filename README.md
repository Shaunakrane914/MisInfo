# Project Aegis Protocol

An autonomous intelligence agency that lives in the cloud to fight misinformation in real-time.

## System Architecture

Project Aegis uses a multi-agent AI system to detect, analyze, and debunk misinformation:

1. **Scout Agent**: Discovers new claims from social media and news sources
2. **Analyst Agent**: Uses ML models to detect linguistic patterns associated with misinformation
3. **Source Profiler Agent**: Evaluates the credibility of information sources
4. **Research Agent**: Gathers evidence from Wikipedia and web searches
5. **Investigator Agent**: Makes final determinations using advanced reasoning
6. **Herald Agent**: Communicates findings to the public

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Create a `.env` file with your Supabase and Gemini API credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. **Start the Backend Server**:
   ```bash
   uvicorn app:app --reload
   ```

4. **Open the Frontend**:
   Open `frontend/index.html` in your browser and navigate to the "Live Dashboard"

## Demo Injection Endpoint

For live demos, you can inject a custom claim using the `/seed-demo-claim` endpoint:

```bash
curl -X POST http://127.0.0.1:8000/seed-demo-claim \
  -H "Content-Type: application/json" \
  -d '{
    "claim_text": "Your demo claim here",
    "source_metadata_json": "{\"account_age_days\": 100, \"followers\": 500, \"following\": 300, \"is_verified\": false}"
  }'
```

## Debugging and Monitoring

### Component Debug Script
Run the debug script to verify all components are working:
```bash
python debug_components.py
```

This script will check:
- Environment variables
- Supabase connection
- ML model loading
- Agent functions

### Frontend Debug Console
Open `frontend/debug.html` in your browser to monitor:
- Frontend initialization
- Supabase connection status
- Realtime subscriptions
- Data fetching

### Logging
The system provides comprehensive logging:
- **Backend**: Detailed logs for each agent and process step
- **Frontend**: Console logs for Supabase client and data handling

To view backend logs, check the terminal where you started the server.
To view frontend logs, open the browser's developer console (F12).

### Common Debugging Commands

1. **Check if backend is running**:
   ```bash
   curl http://127.0.0.1:8000/
   ```

2. **Test database connection**:
   ```bash
   curl http://127.0.0.1:8000/test-db
   ```

3. **View recent verified claims**:
   ```bash
   curl http://127.0.0.1:8000/updates
   ```

4. **View agent status logs**:
   ```bash
   curl http://127.0.0.1:8000/agent-status
   ```

## Troubleshooting WebSocket Connection Issues

If you're seeing WebSocket connection errors like:
```
WebSocket connection to 'wss://kyuothttveugcafvleje.supabase.co/realtime/v1/websocket' failed
```

Or CHANNEL_ERROR messages like:
```
[Frontend] Verified claims subscription status: CHANNEL_ERROR
```

Or 401 Unauthorized errors like:
```
Failed to load resource: the server responded with a status of 401 ()
```

Try these solutions:

### 1. CRITICAL FIX: Use Correct API Keys
**The most common cause of 401 errors is using the wrong API key in the frontend:**

- **Backend (.env file)**: Use `SUPABASE_SERVICE_ROLE_KEY` (full database access)
- **Frontend (script.js)**: Use the **anon public key** (limited, public access)

**To get the correct anon key:**
1. Go to your Supabase project dashboard
2. Navigate to **Settings > API**
3. Under "Project API keys", copy the **"anon" public key**
4. It should contain `"role":"anon"` in the JWT payload
5. Update `SUPABASE_ANON_KEY` in `frontend/script.js` with this key

### 2. Enable Table Replication in Supabase
The CHANNEL_ERROR typically indicates that table replication is not enabled:

1. Go to your Supabase project dashboard
2. Navigate to **Database > Tables**
3. For each table (`verified_claims` and `system_logs`):
   - Click on the table name
   - Go to **Replication** tab
   - Enable replication with `REPLICA IDENTITY FULL`

Or run this SQL in the Supabase SQL editor:
```sql
-- Enable replication for verified_claims
ALTER TABLE verified_claims REPLICA IDENTITY FULL;

-- Enable replication for system_logs
ALTER TABLE system_logs REPLICA IDENTITY FULL;
```

### 3. Enable Row Level Security (RLS)
Tables need RLS enabled with public read policies:

```sql
-- Enable RLS on tables
ALTER TABLE verified_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
CREATE POLICY "public_read_verified_claims" ON verified_claims FOR SELECT USING (true);
CREATE POLICY "public_read_system_logs" ON system_logs FOR SELECT USING (true);

-- Grant access to anon role
GRANT SELECT ON verified_claims TO anon;
GRANT SELECT ON system_logs TO anon;
```

### 4. Add Tables to Realtime Publication
```sql
-- Check existing publications
SELECT * FROM supabase_realtime.publications;

-- Add tables to realtime publication
BEGIN;
DROP PUBLICATION IF EXISTS supabase_realtime;
CREATE PUBLICATION supabase_realtime FOR TABLE verified_claims, system_logs;
COMMIT;
```

### 5. Test Supabase Connection
Run the connection test script:
```bash
python test_supabase_connection.py
```

### 6. Network Issues
- Try disabling ad blockers or privacy extensions
- Test on a different network (some corporate firewalls block WebSocket connections)
- Try using a VPN if needed

### 7. Browser Console Debugging
Open the browser's developer tools (F12) and check:
- Console tab for detailed error messages
- Network tab to see WebSocket connection attempts
- Make sure there are no CORS errors

### 8. Supabase Client Configuration
The frontend now includes additional configuration to handle WebSocket issues:
```javascript
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    realtime: {
        params: {
            eventsPerSecond: 2
        }
    }
});
```

### 9. Quick Fixes for Common Issues
1. **Restart services**:
   - Stop the backend server (Ctrl+C)
   - Refresh the frontend page
   - Start the backend server again: `uvicorn app:app --reload`

2. **Verify anon key**:
   - Go to Supabase Dashboard > Settings > API
   - Copy the "anon public" key (not the service role key)
   - Update the frontend script with the correct key

3. **Test with manual insertion**:
   - Use the debug page buttons to manually insert test data
   - Check if realtime updates are received

## Project Structure

- `app.py`: Main FastAPI application with agent coordination logic
- `source_profiler.py`: Source credibility analysis agent
- `research_agent.py`: Evidence gathering agent
- `prompts.py`: AI agent prompt templates
- `train_model.py`: ML model training script
- `frontend/`: HTML, CSS, and JavaScript for the dashboard
- `data/`: Sample datasets for training
- `vectorizer.pkl` and `classifier.pkl`: Pre-trained ML models

## Real-time Dashboard

The live dashboard shows:
- Verified alerts with detailed evidence dossiers
- Real-time agent activity logs
- Expandable evidence sections showing work from all agents