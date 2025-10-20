// Global JavaScript file for Aegis Protocol website

// Supabase Client Initialization
// IMPORTANT: Use the ANON key for frontend, not the service role key
// Supabase configuration - Replace with your actual credentials
const SUPABASE_URL = 'https://kyuothttveugcafvleje.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5dW90aHR0dmV1Z2NhZnZsZWplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1MTc3NTcsImV4cCI6MjA3NjA5Mzc1N30.ayActwdtBDcpw3C2NSnAA_eOi56t7d6qXZPsP4MN7jI';

// Initialize Supabase client
const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Track displayed claims to prevent duplicates
const displayedClaims = new Set();

// Function to create an alert card
function createAlertCard(alertData) {
    const alertContainer = document.getElementById('alerts-container');
    
    // Check if alertContainer exists
    if (!alertContainer) {
        console.error('[Frontend] alerts-container not found in DOM');
        return;
    }
    
    // Check for duplicates - skip if already displayed
    const claimText = alertData.dossier?.claim_text || '';
    if (displayedClaims.has(claimText)) {
        console.log('[Frontend] Skipping duplicate claim:', claimText.substring(0, 50));
        return;
    }
    displayedClaims.add(claimText);
    
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
    
    // Process log for agent activity tracking
    processSystemLog(message);
}

// Function to fetch initial alerts
async function fetchInitialAlerts() {
    // Check if Supabase is available
    if (!supabaseClient) {
        console.warn('[Frontend] Supabase not initialized. Skipping fetchInitialAlerts.');
        return;
    }
    
    try {
        const { data, error} = await supabaseClient
            .from('verified_claims')
            .select('*')
            .order('timestamp_verified', { ascending: false })
            .limit(50);
        
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
        
        // Clear the container and reset tracking
        alertContainer.innerHTML = '';
        displayedClaims.clear();
        
        // Deduplicate claims by claim text
        const seenClaims = new Set();
        const uniqueClaims = data.filter(claim => {
            const claimText = claim.dossier?.claim_text || '';
            if (seenClaims.has(claimText)) {
                return false;
            }
            seenClaims.add(claimText);
            return true;
        });
        
        console.log(`[Frontend] After deduplication: ${uniqueClaims.length} unique claims`);
        
        // Store all claims for analytics
        allClaims = uniqueClaims;
        
        // Add unique alerts only (limit to 10 most recent)
        if (uniqueClaims.length > 0) {
            uniqueClaims.slice(0, 10).forEach(alert => {
                createAlertCard(alert);
            });
            
            addStatusMessage(`Loaded ${uniqueClaims.length} unique verified claims`);
            
            // Update analytics and charts
            updateAnalytics();
            initVerdictChart();
            initTimelineChart();
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
                
                // Add to allClaims array and update analytics
                allClaims.unshift(payload.new);
                if (allClaims.length > 50) {
                    allClaims.pop(); // Keep only last 50
                }
                updateAnalytics();
                initVerdictChart();
                initTimelineChart();
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

// Analytics and Chart Variables
let verdictChart = null;
let timelineChart = null;
let allClaims = [];
let agentStats = {
    scout: 0,
    analyst: 0,
    source: 0,
    research: 0,
    fusion: 0,
    investigator: 0
};

// Update Analytics Cards
function updateAnalytics() {
    const totalClaims = allClaims.length;
    const falseClaims = allClaims.filter(c => c.verification_status === 'False').length;
    const misleadingClaims = allClaims.filter(c => c.verification_status === 'Misleading').length;
    const trueClaims = allClaims.filter(c => c.verification_status === 'True').length;
    
    document.getElementById('total-claims').textContent = totalClaims;
    document.getElementById('false-claims').textContent = falseClaims;
    document.getElementById('misleading-claims').textContent = misleadingClaims;
    document.getElementById('true-claims').textContent = trueClaims;
    
    // Update agent stats
    document.getElementById('scout-count').textContent = agentStats.scout;
    document.getElementById('analyst-count').textContent = agentStats.analyst;
    document.getElementById('source-count').textContent = agentStats.source;
    document.getElementById('research-count').textContent = agentStats.research;
    document.getElementById('fusion-count').textContent = agentStats.fusion;
    document.getElementById('investigator-count').textContent = agentStats.investigator;
}

// Initialize Verdict Distribution Chart
function initVerdictChart() {
    const ctx = document.getElementById('verdictChart');
    if (!ctx) return;
    
    const falseClaims = allClaims.filter(c => c.verification_status === 'False').length;
    const misleadingClaims = allClaims.filter(c => c.verification_status === 'Misleading').length;
    const trueClaims = allClaims.filter(c => c.verification_status === 'True').length;
    
    if (verdictChart) {
        verdictChart.destroy();
    }
    
    verdictChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['False', 'Misleading', 'True'],
            datasets: [{
                data: [falseClaims, misleadingClaims, trueClaims],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(34, 197, 94, 0.8)'
                ],
                borderColor: [
                    'rgba(239, 68, 68, 1)',
                    'rgba(251, 191, 36, 1)',
                    'rgba(34, 197, 94, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cbd5e1',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

// Initialize Timeline Chart
function initTimelineChart() {
    const ctx = document.getElementById('timelineChart');
    if (!ctx) return;
    
    // Group claims by hour
    const claimsByHour = {};
    allClaims.forEach(claim => {
        const date = new Date(claim.timestamp_verified);
        const hour = date.getHours();
        claimsByHour[hour] = (claimsByHour[hour] || 0) + 1;
    });
    
    const hours = Object.keys(claimsByHour).sort((a, b) => a - b);
    const counts = hours.map(h => claimsByHour[h]);
    
    if (timelineChart) {
        timelineChart.destroy();
    }
    
    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours.map(h => `${h}:00`),
            datasets: [{
                label: 'Claims Processed',
                data: counts,
                borderColor: 'rgba(96, 165, 250, 1)',
                backgroundColor: 'rgba(96, 165, 250, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#cbd5e1',
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#cbd5e1'
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                }
            }
        }
    });
}

// Search and Filter Functionality
function setupSearchAndFilter() {
    const searchInput = document.getElementById('search-input');
    const verdictFilter = document.getElementById('verdict-filter');
    
    if (!searchInput || !verdictFilter) return;
    
    function filterClaims() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedVerdict = verdictFilter.value;
        
        const alertCards = document.querySelectorAll('.alert-card');
        
        alertCards.forEach(card => {
            const claimText = card.querySelector('.alert-claim').textContent.toLowerCase();
            const verdict = card.querySelector('.alert-verdict').textContent;
            
            let matchesSearch = claimText.includes(searchTerm);
            let matchesVerdict = selectedVerdict === 'all' || 
                                (selectedVerdict === 'False' && verdict.includes('🔴')) ||
                                (selectedVerdict === 'Misleading' && verdict.includes('🟡')) ||
                                (selectedVerdict === 'True' && verdict.includes('🟢'));
            
            if (matchesSearch && matchesVerdict) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    searchInput.addEventListener('input', filterClaims);
    verdictFilter.addEventListener('change', filterClaims);
}

// Animate Agent Status
function animateAgentStatus(agentId, status) {
    const agentCard = document.getElementById(`${agentId}-agent`);
    if (!agentCard) return;
    
    const statusIndicator = agentCard.querySelector('.agent-status');
    if (!statusIndicator) return;
    
    // Remove all status classes
    statusIndicator.classList.remove('status-idle', 'status-active', 'status-processing');
    
    // Add new status class
    statusIndicator.classList.add(`status-${status}`);
    
    // Add pulse animation to card
    agentCard.style.animation = 'none';
    setTimeout(() => {
        agentCard.style.animation = 'pulse 0.5s ease-in-out';
    }, 10);
}

// Simulate agent activity based on system logs
function processSystemLog(logMessage) {
    if (logMessage.includes('Scout discovered')) {
        const match = logMessage.match(/(\d+) potential claims/);
        if (match) {
            agentStats.scout += parseInt(match[1]);
            animateAgentStatus('scout', 'active');
            setTimeout(() => animateAgentStatus('scout', 'idle'), 2000);
        }
    }
    
    if (logMessage.includes('Analyzing claim') || logMessage.includes('Text suspicion')) {
        agentStats.analyst++;
        animateAgentStatus('analyst', 'processing');
        setTimeout(() => animateAgentStatus('analyst', 'idle'), 1500);
    }
    
    if (logMessage.includes('Source credibility') || logMessage.includes('Profiled')) {
        agentStats.source++;
        animateAgentStatus('source', 'processing');
        setTimeout(() => animateAgentStatus('source', 'idle'), 1500);
    }
    
    if (logMessage.includes('Evidence gathered') || logMessage.includes('Research')) {
        agentStats.research++;
        animateAgentStatus('research', 'processing');
        setTimeout(() => animateAgentStatus('research', 'idle'), 2000);
    }
    
    if (logMessage.includes('resolved by fusion')) {
        agentStats.fusion++;
        animateAgentStatus('fusion', 'active');
        setTimeout(() => animateAgentStatus('fusion', 'idle'), 2000);
    }
    
    if (logMessage.includes('Investigator') || logMessage.includes('investigated')) {
        agentStats.investigator++;
        animateAgentStatus('investigator', 'active');
        setTimeout(() => animateAgentStatus('investigator', 'idle'), 3000);
    }
    
    updateAnalytics();
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
            
            // Initialize charts
            initVerdictChart();
            initTimelineChart();
            
            // Setup search and filter
            setupSearchAndFilter();
            
            // Update analytics
            updateAnalytics();
            
            // Setup real-time subscriptions
            setupRealtimeSubscriptions();
        }
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