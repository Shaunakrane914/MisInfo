# Project Aegis Frontend

This directory contains the frontend files for Project Aegis, an autonomous fact-checking system that uses AI agents to identify and debunk misinformation.

## File Structure

- `index.html` - Landing page that establishes credibility and states the mission
- `how-it-works.html` - Transparency report explaining the AI and ML models
- `dashboard.html` - Live operations center showing real-time fact-checking activities
- `debug.html` - Debug page for testing frontend functionality with sample data
- `style.css` - Stylesheet for all pages
- `script.js` - JavaScript for dashboard functionality and Supabase integration

## Pages Overview

### 1. index.html - Agency Headquarters (Landing Page)
- Professional "front door" of the project
- Hero section with mission statement
- Problem section explaining the impact of misinformation
- Navigation to other pages

### 2. how-it-works.html - Meet the Agents (Transparency Report)
- Explains the role of each AI agent
- Builds trust through transparency
- Details the technology behind the system

### 3. dashboard.html - Live Operations Center
- Real-time window into the agency's operations
- Two-column layout showing both process and results
- Left column: Verified alerts with detailed evidence
- Right column: Live agent status feed
- Uses Supabase Realtime Subscriptions for live updates

### 4. debug.html - Testing Page
- Allows testing of frontend components without backend
- Sample data for alerts and status messages
- Debug controls for adding/clearing content

## Features

### Real-time Updates
The dashboard uses Supabase Realtime Subscriptions to receive live updates:
- New verified claims appear instantly in the alerts feed
- Agent status messages appear in real-time in the status feed

### Interactive Alert Cards
- Each alert shows the verdict (True/False/Misleading) with appropriate emoji
- One-sentence explanation from the Herald Agent
- "Show Evidence" button that expands to show the full dossier
- Detailed evidence breakdown including:
  - Text Analysis (ML Model) - Suspicion Score
  - Source Profile (Heuristics) - Credibility Score
  - Research Dossier (OSINT) - Wikipedia summary
  - Final Verdict By - Investigator Agent

### Responsive Design
- Works on desktop and mobile devices
- Adapts layout for different screen sizes
- Touch-friendly controls

## Development

To run the frontend locally:

1. Make sure you have Python installed
2. Run the server script:
   ```bash
   python serve_frontend.py
   ```
3. Open your browser to http://localhost:8081

## Supabase Integration

The frontend connects to Supabase for real-time data:
- Uses the Supabase JavaScript client
- Connects to the `verified_claims` table for alerts
- Connects to the `system_logs` table for agent status
- Requires proper Supabase URL and ANON key configuration

## Customization

To customize the frontend for your own deployment:
1. Update the Supabase credentials in `script.js`
2. Modify the styling in `style.css`
3. Update content in the HTML files as needed