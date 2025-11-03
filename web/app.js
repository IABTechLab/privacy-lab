// API Configuration
const API_BASE_URL = 'http://localhost:8000';

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

// k-Anonymity Form Handler
document.getElementById('k-anonymity-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading();

    const formData = {
        k: parseInt(document.getElementById('k-value').value),
        supp_level: parseInt(document.getElementById('k-supp').value),
        use_sample_data: document.getElementById('k-sample-data').checked
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/k-anonymity`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
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

    const formData = {
        epsilon: parseFloat(document.getElementById('epsilon-value').value),
        split_evenly_over: parseInt(document.getElementById('split-over').value),
        use_sample_data: document.getElementById('dp-sample-data').checked
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/differential-privacy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
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

    const formData = {
        use_sample_data: document.getElementById('he-sample-data').checked
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/homomorphic-encryption`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
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
