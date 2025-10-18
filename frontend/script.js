// Global JavaScript file for Aegis Protocol website

// Supabase Client Initialization
// IMPORTANT: Use the ANON key for frontend, not the service role key
// Supabase configuration - Replace with your actual credentials
const SUPABASE_URL = 'https://kyuothttveugcafvleje.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5dW90aHR0dmV1Z2NhZnZsZWplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1MTc3NTcsImV4cCI6MjA3NjA5Mzc1N30.ayActwdtBDcpw3C2NSnAA_eOi56t7d6qXZPsP4MN7jI';

// Standardized backend port
const BACKEND_PORT = 8000;

// Initialize Supabase client with proper error handling
let supabaseClient = null;

// Check if Supabase library is available
if (typeof supabase !== 'undefined' && supabase.createClient) {
    try {
        const { createClient } = supabase;
        supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        console.log('[Frontend] Supabase client initialized successfully');
    } catch (error) {
        console.error('[Frontend] Error initializing Supabase client:', error);
    }
} else {
    console.warn('[Frontend] Supabase library not found. Realtime features will be disabled.');
}

// WebSocket connection for real-time updates
let websocket = null;
let reconnectInterval = null;

// Function to connect to WebSocket
function connectWebSocket() {
    // Close existing connection if any
    if (websocket) {
        websocket.close();
    }
    
    // Clear any existing reconnect interval
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
    
    try {
        // Connect to WebSocket endpoint - using standardized backend port
        const wsUrl = `ws://localhost:${BACKEND_PORT}/ws`;
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function(event) {
            console.log('[Frontend] WebSocket connection established');
            addStatusMessage('WebSocket connection established');
        };
        
        websocket.onmessage = function(event) {
            console.log('[Frontend] WebSocket message received:', event.data);
            // Check if this is a ping message
            if (event.data === "ping") {
                // Respond to ping to keep connection alive
                websocket.send("pong");
                return;
            }
            
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'claim_updates') {
                    addStatusMessage(`Received ${message.count} new claim updates`);
                    // Refresh the data to show new claims
                    fetchInitialAlerts();
                }
            } catch (e) {
                console.error('[Frontend] Error parsing WebSocket message:', e);
            }
        };
        
        websocket.onclose = function(event) {
            console.log('[Frontend] WebSocket connection closed');
            addStatusMessage('WebSocket connection closed. Attempting to reconnect...');
            
            // Try to reconnect after 5 seconds
            reconnectInterval = setTimeout(connectWebSocket, 5000);
        };
        
        websocket.onerror = function(error) {
            console.error('[Frontend] WebSocket error:', error);
            addStatusMessage('WebSocket connection error');
        };
    } catch (error) {
        console.error('[Frontend] Error creating WebSocket connection:', error);
        addStatusMessage('Error creating WebSocket connection');
    }
}

// Function to create an alert card
function createAlertCard(alertData) {
    const alertContainer = document.getElementById('alerts-container');
    
    // Check if alertContainer exists
    if (!alertContainer) {
        console.error('[Frontend] alerts-container not found in DOM');
        return;
    }
    
    // Remove placeholder if it exists
    const placeholder = alertContainer.querySelector('.alert-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    // Create alert card element
    const alertCard = document.createElement('div');
    alertCard.className = 'alert-card';
    
    // Format the verdict emoji
    let verdictEmoji = '🟡';
    if (alertData.verification_status === 'True') {
        verdictEmoji = '🟢';
    } else if (alertData.verification_status === 'False') {
        verdictEmoji = '🔴';
    }
    
    // Create the HTML for the alert card
    alertCard.innerHTML = `
        <div class="alert-header">
            <div class="alert-verdict">${verdictEmoji}</div>
            <div class="alert-claim">${alertData.dossier?.claim_text || 'Claim text not available'}</div>
        </div>
        <div class="alert-explanation">${alertData.explanation}</div>
        <button class="btn-secondary" onclick="toggleDossier(this)">Show Evidence</button>
        <div class="dossier">
            <div class="dossier-item">
                <strong>Text Analysis (ML Model):</strong> Suspicion Score: ${(alertData.dossier?.text_suspicion_score * 100).toFixed(0)}%
            </div>
            <div class="dossier-item">
                <strong>Source Profile (Heuristics):</strong> Credibility Score: ${(alertData.dossier?.source_credibility_score * 100).toFixed(0)}%
            </div>
            <div class="dossier-item">
                <strong>Research Dossier (OSINT):</strong> ${alertData.dossier?.research_dossier?.wikipedia_summary || 'No Wikipedia summary available'}
            </div>
            <div class="dossier-item">
                <strong>Final Verdict By:</strong> Investigator Agent
            </div>
        </div>
    `;
    
    // Add the new alert card to the top of the container
    alertContainer.insertBefore(alertCard, alertContainer.firstChild);
    
    console.log('[Frontend] Alert card added to DOM');
}

// Function to toggle the dossier visibility
function toggleDossier(button) {
    const dossier = button.nextElementSibling;
    if (dossier.style.display === 'block') {
        dossier.style.display = 'none';
        button.textContent = 'Show Evidence';
    } else {
        dossier.style.display = 'block';
        button.textContent = 'Hide Evidence';
    }
}

// Function to add a status message
function addStatusMessage(message) {
    const statusContainer = document.getElementById('status-container');
    
    // Check if statusContainer exists
    if (!statusContainer) {
        console.error('[Frontend] status-container not found in DOM');
        return;
    }
    
    // Remove initial status message if it exists
    const initialMessage = statusContainer.querySelector('.status-message p');
    if (initialMessage && initialMessage.textContent.includes('Connecting')) {
        statusContainer.innerHTML = '';
    }
    
    // Create status message element
    const statusMessage = document.createElement('div');
    statusMessage.className = 'status-message';
    
    // Get current time
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    statusMessage.innerHTML = `<p>[${timeString}] ${message}</p>`;
    
    // Add the new status message to the top of the container
    statusContainer.insertBefore(statusMessage, statusContainer.firstChild);
    
    // Keep only the last 10 messages
    if (statusContainer.children.length > 10) {
        statusContainer.removeChild(statusContainer.lastChild);
    }
}

// Function to fetch initial alerts
async function fetchInitialAlerts() {
    // Check if Supabase is available
    if (!supabaseClient) {
        console.warn('[Frontend] Supabase not initialized. Skipping fetchInitialAlerts.');
        return;
    }
    
    try {
        const { data, error } = await supabaseClient
            .from('verified_claims')
            .select('*')
            .order('timestamp_verified', { ascending: false })
            .limit(20);
        
        if (error) {
            console.error('Error fetching initial alerts:', error);
            addStatusMessage('Error fetching claims: ' + error.message);
            return;
        }
        
        // Get the alerts container
        const alertContainer = document.getElementById('alerts-container');
        
        // Check if alertContainer exists
        if (!alertContainer) {
            console.error('[Frontend] alerts-container not found in DOM');
            return;
        }
        
        console.log(`[Frontend] Fetched ${data.length} verified claims`);
        
        // Clear existing alerts only if we have data
        if (data.length > 0) {
            alertContainer.innerHTML = '';
            
            // Add each alert to the dashboard
            data.forEach(alert => {
                createAlertCard(alert);
            });
            
            addStatusMessage(`Loaded ${data.length} verified claims`);
        } else {
            // Show placeholder if no data
            const placeholder = alertContainer.querySelector('.alert-placeholder');
            if (!placeholder) {
                alertContainer.innerHTML = '<div class="alert-placeholder"><p>No verified claims yet. New claims will appear here in real-time.</p></div>';
            }
        }
    } catch (err) {
        console.error('Error fetching initial alerts:', err);
        addStatusMessage('Error fetching claims: ' + err.message);
    }
}

// Function to fetch initial agent status logs
async function fetchInitialStatusLogs() {
    // Check if Supabase is available
    if (!supabaseClient) {
        console.warn('[Frontend] Supabase not initialized. Skipping fetchInitialStatusLogs.');
        return;
    }
    
    try {
        const { data, error } = await supabaseClient
            .from('system_logs')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(5);
        
        if (error) {
            console.error('Error fetching initial status logs:', error);
            return;
        }
        
        // Get the status container
        const statusContainer = document.getElementById('status-container');
        
        // Check if statusContainer exists
        if (!statusContainer) {
            console.error('[Frontend] status-container not found in DOM');
            return;
        }
        
        // Add each log to the status feed
        data.forEach(log => {
            addStatusMessage(log.log_message);
        });
        
        if (data.length > 0) {
            addStatusMessage('Connected to Aegis Protocol');
        }
    } catch (err) {
        console.error('Error fetching initial status logs:', err);
    }
}

// Function to setup real-time subscriptions
function setupRealtimeSubscriptions() {
    // Check if Supabase is available
    if (!supabaseClient) {
        console.warn('[Frontend] Supabase not initialized. Skipping real-time subscriptions.');
        return;
    }
    
    // Subscribe to new verified claims
    supabaseClient
        .channel('verified_claims')
        .on(
            'postgres_changes',
            {
                event: 'INSERT',
                schema: 'public',
                table: 'verified_claims',
            },
            (payload) => {
                console.log('New verified claim:', payload);
                createAlertCard(payload.new);
                addStatusMessage(`New verified claim: ${payload.new.verification_status}`);
            }
        )
        .subscribe((status) => {
            console.log('Realtime subscription status:', status);
            if (status === 'SUBSCRIBED') {
                addStatusMessage('Realtime claim updates enabled');
            }
        });
    
    // Subscribe to new system logs (limited messages)
    supabaseClient
        .channel('system_logs')
        .on(
            'postgres_changes',
            {
                event: 'INSERT',
                schema: 'public',
                table: 'system_logs',
            },
            (payload) => {
                console.log('New system log:', payload);
                // Only show important logs
                if (payload.new.log_message.includes('Claim processed') || 
                    payload.new.log_message.includes('results saved')) {
                    addStatusMessage(payload.new.log_message);
                }
            }
        )
        .subscribe((status) => {
            console.log('Realtime logs subscription status:', status);
            if (status === 'SUBSCRIBED') {
                addStatusMessage('Realtime system monitoring enabled');
            }
        });
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', async function() {
    console.log('[Frontend] DOM loaded, initializing application...');
    
    // Check if we're on the dashboard page
    const alertsContainer = document.getElementById('alerts-container');
    const statusContainer = document.getElementById('status-container');
    
    if (alertsContainer && statusContainer) {
        console.log('[Frontend] Initializing dashboard...');
        
        // Check if Supabase is available
        if (!supabaseClient) {
            console.warn('[Frontend] Supabase not initialized. Realtime features will be disabled.');
            addStatusMessage('Warning: Realtime features disabled');
        } else {
            // Fetch initial data immediately
            await fetchInitialAlerts();
            await fetchInitialStatusLogs();
            
            // Setup real-time subscriptions
            setupRealtimeSubscriptions();
        }
        
        // Connect to WebSocket for real-time updates
        connectWebSocket();
    } else {
        console.warn('[Frontend] Not on dashboard page or required containers not found');
    }
});

// Utility functions that can be used across pages
function formatTimestamp(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return 'Just now';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
}

function getStatusEmoji(status) {
    switch (status.toLowerCase()) {
        case 'true':
            return '🟢';
        case 'false':
            return '🔴';
        case 'misleading':
            return '🟡';
        default:
            return '⚪';
    }
}