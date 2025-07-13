// Minesweeper AI Benchmark Web App

// Global state
let currentMetric = 'global_score';
let currentTaskType = '';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
    loadPlatformStats();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                showSection(link.getAttribute('href').substring(1));
            }
        });
    });

    // Filters
    document.getElementById('metric-select').addEventListener('change', (e) => {
        currentMetric = e.target.value;
        loadLeaderboard();
    });

    document.getElementById('task-type-select').addEventListener('change', (e) => {
        currentTaskType = e.target.value;
        loadLeaderboard();
    });

    // Task generation form
    const taskForm = document.getElementById('task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', handleTaskGeneration);
    }

    // Evaluation form
    const evalForm = document.getElementById('eval-form');
    if (evalForm) {
        evalForm.addEventListener('submit', handleEvaluation);
    }
}

// Show section
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    document.getElementById(sectionId).style.display = 'block';

    // Update nav active state
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
        }
    });
}

// Load leaderboard data
async function loadLeaderboard() {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '<tr><td colspan="8" class="loading">Loading...</td></tr>';

    try {
        let url = `/api/leaderboard?metric=${currentMetric}`;
        if (currentTaskType) {
            url += `&task_type=${currentTaskType}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">No results found</td></tr>';
            return;
        }

        data.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${entry.rank}</td>
                <td><strong>${formatModelName(entry.model_name)}</strong></td>
                <td>${formatScore(entry.global_score)}</td>
                <td>${formatPercent(entry.win_rate)}</td>
                <td>${formatPercent(entry.accuracy)}</td>
                <td>${formatPercent(entry.coverage)}</td>
                <td>${formatScore(entry.reasoning_score)}</td>
                <td>${entry.num_games}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="8" class="loading">Error loading data: ${error.message}</td></tr>`;
    }
}

// Load platform statistics
async function loadPlatformStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('total-evaluations').textContent = data.total_evaluations;
        document.getElementById('unique-models').textContent = data.unique_models;
        document.getElementById('total-tasks').textContent = data.total_tasks;
    } catch (error) {
        console.error('Failed to load platform stats:', error);
    }
}

// Format model name
function formatModelName(name) {
    // Extract just the model name from provider/model format
    const parts = name.split('/');
    const modelName = parts[parts.length - 1];
    
    // Add provider badge
    if (name.includes('openai')) {
        return `${modelName} <span class="muted">(OpenAI)</span>`;
    } else if (name.includes('anthropic')) {
        return `${modelName} <span class="muted">(Anthropic)</span>`;
    }
    return modelName;
}

// Format score
function formatScore(score) {
    if (score === null || score === undefined) return '-';
    
    const value = (score * 100).toFixed(1);
    const className = score >= 0.7 ? 'score-high' : score >= 0.4 ? 'score-medium' : 'score-low';
    
    return `<span class="score-badge ${className}">${value}</span>`;
}

// Format percentage
function formatPercent(value) {
    if (value === null || value === undefined) return '-';
    return (value * 100).toFixed(1) + '%';
}

// Auto-refresh leaderboard every 30 seconds
setInterval(() => {
    if (document.querySelector('nav a[href="#leaderboard"]').classList.contains('active')) {
        loadLeaderboard();
    }
}, 30000);

// Model configurations
const modelConfigs = {
    openai: [
        {id: 'gpt-4', name: 'GPT-4'},
        {id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo'},
        {id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo'}
    ],
    anthropic: [
        {id: 'claude-3-opus-20240229', name: 'Claude 3 Opus'},
        {id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet'},
        {id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku'}
    ]
};

// Update model list based on provider
function updateModelList() {
    const provider = document.getElementById('model-provider').value;
    const modelSelect = document.getElementById('model-name');
    
    modelSelect.innerHTML = '';
    modelConfigs[provider].forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        modelSelect.appendChild(option);
    });
}

// Handle task generation
async function handleTaskGeneration(e) {
    e.preventDefault();
    
    const button = e.target.querySelector('button[type="submit"]');
    const statusDiv = document.getElementById('task-status');
    
    button.disabled = true;
    statusDiv.className = 'status-message info';
    statusDiv.textContent = 'Generating tasks...';
    
    const data = {
        num_tasks: parseInt(document.getElementById('num-tasks').value),
        difficulty: document.getElementById('task-difficulty').value || null,
        task_type: document.getElementById('task-type').value || null
    };
    
    try {
        const response = await fetch('/api/evaluation/generate-tasks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusDiv.className = 'status-message success';
            statusDiv.textContent = `✅ ${result.message}`;
            pollJobStatus(result.job_id);
            updateJobsList();
        } else {
            statusDiv.className = 'status-message error';
            statusDiv.textContent = `❌ Error: ${result.detail}`;
        }
    } catch (error) {
        statusDiv.className = 'status-message error';
        statusDiv.textContent = `❌ Error: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

// Handle evaluation
async function handleEvaluation(e) {
    e.preventDefault();
    
    const button = e.target.querySelector('button[type="submit"]');
    const statusDiv = document.getElementById('eval-status');
    
    button.disabled = true;
    statusDiv.className = 'status-message info';
    statusDiv.textContent = 'Starting evaluation...';
    
    const data = {
        model_name: document.getElementById('model-name').value,
        model_provider: document.getElementById('model-provider').value,
        num_games: parseInt(document.getElementById('num-games').value),
        api_key: document.getElementById('api-key').value || null
    };
    
    try {
        const response = await fetch('/api/evaluation/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusDiv.className = 'status-message success';
            statusDiv.textContent = `✅ ${result.message}`;
            pollJobStatus(result.job_id);
            updateJobsList();
        } else {
            statusDiv.className = 'status-message error';
            statusDiv.textContent = `❌ Error: ${result.detail}`;
        }
    } catch (error) {
        statusDiv.className = 'status-message error';
        statusDiv.textContent = `❌ Error: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

// Poll job status
async function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/evaluation/jobs/${jobId}/status`);
            const job = await response.json();
            
            updateJobsList();
            
            if (job.status === 'completed' || job.status === 'failed') {
                clearInterval(interval);
                if (job.status === 'completed') {
                    loadLeaderboard();
                    loadPlatformStats();
                }
            }
        } catch (error) {
            clearInterval(interval);
        }
    }, 2000);
}

// Update jobs list
async function updateJobsList() {
    try {
        const response = await fetch('/api/evaluation/jobs');
        const jobs = await response.json();
        
        const jobsList = document.getElementById('jobs-list');
        if (!jobsList) return;
        
        if (jobs.length === 0) {
            jobsList.innerHTML = '<p class="empty-state">No active jobs</p>';
        } else {
            jobsList.innerHTML = jobs.map(job => `
                <div class="job-item ${job.status}">
                    <div class="job-header">
                        <strong>${job.job_id}</strong>
                        <span class="job-status ${job.status}">${job.status.toUpperCase()}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${job.progress * 100}%"></div>
                    </div>
                    <p class="job-message">${job.message}</p>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

// Auto-refresh jobs when on evaluate page
setInterval(() => {
    if (document.querySelector('nav a[href="#evaluate"]')?.classList.contains('active')) {
        updateJobsList();
    }
}, 5000);