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