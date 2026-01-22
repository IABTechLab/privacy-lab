// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// JWT Token - In production, this should be obtained from authentication service
// For now, using localStorage or a configurable token
function getJWTToken() {
    // Try to get from localStorage first
    const token = localStorage.getItem('jwt_token');
    if (token) {
        return token;
    }
    
    // If not in localStorage, try to get from environment/config
    // In production, this should come from your auth service
    // For development, you can set it manually:
    // localStorage.setItem('jwt_token', 'your-jwt-token-here');
    
    // Return null if no token found - API will return 401
    return null;
}

// Helper function to make authenticated API calls
async function authenticatedFetch(url, options = {}) {
    const token = getJWTToken();
    const headers = {
        ...options.headers,
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return fetch(url, {
        ...options,
        headers
    });
}

// Check for stored files on page load
async function checkStoredFiles() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/user/files`);
        if (response.ok) {
            const data = await response.json();
            if (data.files && data.files.length > 0) {
                console.log(`User has ${data.count} stored file(s)`);
                // You can display this information in the UI if needed
                // For example, show a notification or update a status indicator
            }
        } else if (response.status === 401) {
            console.log('No valid JWT token found. Please authenticate.');
        }
    } catch (error) {
        console.error('Error checking stored files:', error);
    }
}

// Check stored files when page loads
document.addEventListener('DOMContentLoaded', () => {
    checkStoredFiles();
});

// Tab functionality
function openTab(evt, tabName) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }

    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
}

// Loading overlay
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Range slider updates
document.getElementById('k-value').addEventListener('input', (e) => {
    document.getElementById('k-value-display').textContent = e.target.value;
});

document.getElementById('k-supp').addEventListener('input', (e) => {
    document.getElementById('k-supp-display').textContent = e.target.value;
});

document.getElementById('epsilon-value').addEventListener('input', (e) => {
    document.getElementById('epsilon-value-display').textContent = e.target.value;
});

// Toggle file upload visibility based on sample data checkbox
document.getElementById('k-sample-data').addEventListener('change', (e) => {
    document.getElementById('k-file-uploads').style.display = e.target.checked ? 'none' : 'block';
});

document.getElementById('dp-sample-data').addEventListener('change', (e) => {
    document.getElementById('dp-file-uploads').style.display = e.target.checked ? 'none' : 'block';
});

document.getElementById('he-sample-data').addEventListener('change', (e) => {
    document.getElementById('he-file-uploads').style.display = e.target.checked ? 'none' : 'block';
});

// k-Anonymity Form Handler
document.getElementById('k-anonymity-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading();

    const useSampleData = document.getElementById('k-sample-data').checked;
    let response;

    try {
        // Always use FormData for consistency
        const formData = new FormData();
        formData.append('k', document.getElementById('k-value').value);
        formData.append('supp_level', document.getElementById('k-supp').value);
        formData.append('use_sample_data', useSampleData ? 'true' : 'false');

        if (!useSampleData) {
            const eventsFile = document.getElementById('k-events-file').files[0];
            const conversionsFile = document.getElementById('k-conversions-file').files[0];

            if (!eventsFile || !conversionsFile) {
                throw new Error('Please select both events and conversions CSV files');
            }

            formData.append('events', eventsFile);
            formData.append('conversions', conversionsFile);
        }

        response = await authenticatedFetch(`${API_BASE_URL}/api/k-anonymity`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayKAnonymityResults(data);
    } catch (error) {
        displayError('k-anonymity-results', error.message);
    } finally {
        hideLoading();
    }
});

// Differential Privacy Form Handler
document.getElementById('dp-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading();

    const useSampleData = document.getElementById('dp-sample-data').checked;
    let response;

    try {
        // Always use FormData for consistency
        const formData = new FormData();
        formData.append('epsilon', document.getElementById('epsilon-value').value);
        formData.append('split_evenly_over', document.getElementById('split-over').value);
        formData.append('use_sample_data', useSampleData ? 'true' : 'false');

        if (!useSampleData) {
            const eventsFile = document.getElementById('dp-events-file').files[0];
            const conversionsFile = document.getElementById('dp-conversions-file').files[0];

            if (!eventsFile || !conversionsFile) {
                throw new Error('Please select both events and conversions CSV files');
            }

            formData.append('events', eventsFile);
            formData.append('conversions', conversionsFile);
        }

        response = await authenticatedFetch(`${API_BASE_URL}/api/differential-privacy`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayDPResults(data);
    } catch (error) {
        displayError('dp-results', error.message);
    } finally {
        hideLoading();
    }
});

// Homomorphic Encryption Form Handler
document.getElementById('he-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading();

    const useSampleData = document.getElementById('he-sample-data').checked;
    let response;

    try {
        // Always use FormData for consistency
        const formData = new FormData();
        formData.append('use_sample_data', useSampleData ? 'true' : 'false');

        if (!useSampleData) {
            const eventsFile = document.getElementById('he-events-file').files[0];
            const conversionsFile = document.getElementById('he-conversions-file').files[0];

            if (!eventsFile || !conversionsFile) {
                throw new Error('Please select both events and conversions CSV files');
            }

            formData.append('events', eventsFile);
            formData.append('conversions', conversionsFile);
        }

        response = await authenticatedFetch(`${API_BASE_URL}/api/homomorphic-encryption`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayHEResults(data);
    } catch (error) {
        displayError('he-results', error.message);
    } finally {
        hideLoading();
    }
});

// Display Functions
function displayKAnonymityResults(data) {
    const resultsDiv = document.getElementById('k-anonymity-results');

    let html = `
        <h3>k-Anonymity Results</h3>
        <div class="params">
            <strong>Parameters:</strong> k=${data.parameters.k}, Suppression Level=${data.parameters.suppression_level}
        </div>
        <div class="metadata">
            ${data.metadata.description} (${data.metadata.total_records} records)
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        ${Object.keys(data.result[0] || {}).filter(k => k !== 'index').map(key => `<th>${key}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.result.slice(0, 50).map(row => `
                        <tr>
                            ${Object.entries(row).filter(([k]) => k !== 'index').map(([_, value]) => `<td>${value}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        ${data.result.length > 50 ? `<p class="info">Showing first 50 of ${data.result.length} records</p>` : ''}
    `;

    resultsDiv.innerHTML = html;
}

function displayDPResults(data) {
    const resultsDiv = document.getElementById('dp-results');

    let html = `
        <h3>Differential Privacy Results</h3>
        <div class="params">
            <strong>Parameters:</strong> ε=${data.parameters.epsilon}, Split over ${data.parameters.split_evenly_over} queries
        </div>
        <div class="metadata">
            ${data.metadata.description}
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Campaign</th>
                        <th>Non-DP Count</th>
                        <th>DP Count</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.result.map(row => {
                        const diff = row.dp_count - row.non_dp_count;
                        const diffClass = diff >= 0 ? 'positive' : 'negative';
                        return `
                            <tr>
                                <td>${row.campaign}</td>
                                <td>${row.non_dp_count}</td>
                                <td>${row.dp_count}</td>
                                <td class="${diffClass}">${diff > 0 ? '+' : ''}${diff}</td>
                            </tr>
                        `;
                    }).join('')}
                    <tr class="total-row">
                        <td><strong>Total</strong></td>
                        <td><strong>${data.result.reduce((sum, r) => sum + r.non_dp_count, 0)}</strong></td>
                        <td><strong>${data.result.reduce((sum, r) => sum + r.dp_count, 0)}</strong></td>
                        <td><strong>${data.result.reduce((sum, r) => sum + r.dp_count, 0) - data.result.reduce((sum, r) => sum + r.non_dp_count, 0)}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="chart-container">
            ${createBarChart(data.result)}
        </div>
    `;

    resultsDiv.innerHTML = html;
}

function displayHEResults(data) {
    const resultsDiv = document.getElementById('he-results');

    let html = `
        <h3>Homomorphic Encryption Results</h3>
        <div class="metadata">
            ${data.metadata.description}
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Campaign</th>
                        <th>Purchase Count</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.result.map(row => `
                        <tr>
                            <td>${row.campaign}</td>
                            <td>${row.purchase_count}</td>
                        </tr>
                    `).join('')}
                    <tr class="total-row">
                        <td><strong>Total</strong></td>
                        <td><strong>${data.result.reduce((sum, r) => sum + r.purchase_count, 0)}</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;

    resultsDiv.innerHTML = html;
}

function createBarChart(data) {
    const maxValue = Math.max(...data.map(r => Math.max(r.non_dp_count, r.dp_count)));

    return `
        <div class="bar-chart">
            <h4>Comparison Chart</h4>
            ${data.map(row => `
                <div class="chart-row">
                    <div class="chart-label">${row.campaign}</div>
                    <div class="chart-bars">
                        <div class="bar non-dp" style="width: ${(row.non_dp_count / maxValue) * 100}%">
                            ${row.non_dp_count}
                        </div>
                        <div class="bar dp" style="width: ${(row.dp_count / maxValue) * 100}%">
                            ${row.dp_count}
                        </div>
                    </div>
                </div>
            `).join('')}
            <div class="legend">
                <span class="legend-item"><span class="legend-color non-dp"></span> Non-DP</span>
                <span class="legend-item"><span class="legend-color dp"></span> DP</span>
            </div>
        </div>
    `;
}

function displayError(elementId, message) {
    const resultsDiv = document.getElementById(elementId);
    resultsDiv.innerHTML = `
        <div class="error">
            <h3>Error</h3>
            <p>${message}</p>
            <p>Please make sure the API server is running on ${API_BASE_URL}</p>
        </div>
    `;
}
