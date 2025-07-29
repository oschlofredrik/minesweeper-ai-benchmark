// Competition Manager - Frontend for AI competitions and tournaments

class CompetitionManager {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.competitions = [];
    this.activeCompetition = null;
  }
  
  // Initialize the competition UI
  init() {
    this.render();
    this.attachEventListeners();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="competition-manager">
        <div class="competition-header">
          <h2>AI Competitions</h2>
          <div class="competition-actions">
            <button class="button button-primary" onclick="competitionManager.showCreateModal()">
              Create Competition
            </button>
          </div>
        </div>
        
        <div class="competition-tabs">
          <button class="tab-button active" data-tab="active">Active</button>
          <button class="tab-button" data-tab="upcoming">Upcoming</button>
          <button class="tab-button" data-tab="completed">Completed</button>
        </div>
        
        <div class="competition-content">
          <div id="competition-list" class="competition-list">
            <!-- Competitions will be listed here -->
          </div>
        </div>
      </div>
      
      <!-- Create Competition Modal -->
      <div id="create-competition-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content modal-large">
          <div class="modal-header">
            <h2>Create New Competition</h2>
            <button class="modal-close" onclick="competitionManager.hideCreateModal()">&times;</button>
          </div>
          
          <form id="create-competition-form">
            <div class="form-section">
              <h3>Competition Type</h3>
              <div class="competition-type-grid">
                <label class="competition-type-card">
                  <input type="radio" name="type" value="tournament" checked>
                  <div class="card-content">
                    <h4>Elimination Tournament</h4>
                    <p>Single or double elimination bracket</p>
                  </div>
                </label>
                
                <label class="competition-type-card">
                  <input type="radio" name="type" value="league">
                  <div class="card-content">
                    <h4>League</h4>
                    <p>Round-robin competition</p>
                  </div>
                </label>
                
                <label class="competition-type-card">
                  <input type="radio" name="type" value="team">
                  <div class="card-content">
                    <h4>Team Challenge</h4>
                    <p>AI models work together</p>
                  </div>
                </label>
              </div>
            </div>
            
            <div class="form-section">
              <label class="label">Competition Name</label>
              <input type="text" class="input" name="name" required 
                     placeholder="e.g., Winter AI Championship 2025">
            </div>
            
            <div class="form-section">
              <label class="label">Game Type</label>
              <select class="select" name="gameType" required>
                <option value="minesweeper">Minesweeper</option>
                <option value="risk">Risk</option>
              </select>
            </div>
            
            <div class="form-section">
              <label class="label">Difficulty</label>
              <select class="select" name="difficulty">
                <option value="easy">Easy</option>
                <option value="medium" selected>Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            
            <div id="tournament-settings" class="form-section competition-settings">
              <h3>Tournament Settings</h3>
              <label class="label">Format</label>
              <select class="select" name="roundFormat">
                <option value="single-game">Single Game</option>
                <option value="best-of-3" selected>Best of 3</option>
                <option value="best-of-5">Best of 5</option>
              </select>
            </div>
            
            <div id="league-settings" class="form-section competition-settings" style="display: none;">
              <h3>League Settings</h3>
              <label class="label">Number of Rounds</label>
              <input type="number" class="input" name="rounds" min="1" max="10" value="2">
              
              <label class="label">Point System</label>
              <div class="point-system">
                <div>
                  <label>Win:</label>
                  <input type="number" class="input input-small" name="winPoints" value="3">
                </div>
                <div>
                  <label>Draw:</label>
                  <input type="number" class="input input-small" name="drawPoints" value="1">
                </div>
                <div>
                  <label>Loss:</label>
                  <input type="number" class="input input-small" name="lossPoints" value="0">
                </div>
              </div>
            </div>
            
            <div id="team-settings" class="form-section competition-settings" style="display: none;">
              <h3>Team Settings</h3>
              <label class="label">Team Name</label>
              <input type="text" class="input" name="teamName" placeholder="AI Alliance">
              
              <label class="label">Communication Style</label>
              <select class="select" name="communicationStyle">
                <option value="sequential">Sequential (Each builds on previous)</option>
                <option value="consensus">Consensus (Vote on best move)</option>
                <option value="hierarchical">Hierarchical (Strategist decides)</option>
              </select>
            </div>
            
            <div class="form-section">
              <h3>Participants</h3>
              <div id="participants-list" class="participants-list">
                <!-- Participants will be added here -->
              </div>
              <button type="button" class="button button-secondary" 
                      onclick="competitionManager.showAddParticipant()">
                Add Participant
              </button>
            </div>
            
            <div class="form-actions">
              <button type="button" class="button button-secondary" 
                      onclick="competitionManager.hideCreateModal()">
                Cancel
              </button>
              <button type="submit" class="button button-primary">
                Create Competition
              </button>
            </div>
          </form>
        </div>
      </div>
    `;
    
    this.loadCompetitions();
  }
  
  attachEventListeners() {
    // Tab switching
    this.container.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', (e) => {
        this.container.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        this.filterCompetitions(e.target.dataset.tab);
      });
    });
    
    // Competition type switching
    const typeRadios = this.container.querySelectorAll('input[name="type"]');
    typeRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.showCompetitionSettings(e.target.value);
      });
    });
    
    // Form submission
    const form = document.getElementById('create-competition-form');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.createCompetition();
    });
  }
  
  showCompetitionSettings(type) {
    // Hide all settings
    this.container.querySelectorAll('.competition-settings').forEach(el => {
      el.style.display = 'none';
    });
    
    // Show relevant settings
    const settingsId = `${type}-settings`;
    const settings = document.getElementById(settingsId);
    if (settings) {
      settings.style.display = 'block';
    }
    
    // Update participant UI based on type
    this.updateParticipantUI(type);
  }
  
  updateParticipantUI(type) {
    const participantsList = document.getElementById('participants-list');
    
    if (type === 'team') {
      // For team games, show role selection
      participantsList.innerHTML = `
        <div class="team-roles-info">
          <p>Build your AI team with different roles:</p>
          <ul>
            <li><strong>Strategist</strong>: Makes final decisions</li>
            <li><strong>Analyst</strong>: Provides detailed analysis</li>
            <li><strong>Executor</strong>: Focuses on tactical moves</li>
          </ul>
        </div>
      `;
    } else {
      // For tournaments/leagues, clear any team-specific content
      if (participantsList.querySelector('.team-roles-info')) {
        participantsList.innerHTML = '';
      }
    }
  }
  
  showAddParticipant() {
    const type = document.querySelector('input[name="type"]:checked').value;
    const isTeam = type === 'team';
    
    const participantForm = `
      <div class="participant-form">
        <div class="form-row">
          <select class="select" id="add-provider">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
          
          <select class="select" id="add-model">
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-4-turbo">GPT-4 Turbo</option>
            <option value="claude-3-opus">Claude 3 Opus</option>
            <option value="claude-3-sonnet">Claude 3 Sonnet</option>
          </select>
          
          ${isTeam ? `
            <select class="select" id="add-role">
              <option value="strategist">Strategist</option>
              <option value="analyst">Analyst</option>
              <option value="executor">Executor</option>
            </select>
          ` : ''}
          
          <input type="text" class="input" id="add-name" placeholder="Nickname (optional)">
          
          <button class="button button-primary" onclick="competitionManager.addParticipant()">
            Add
          </button>
        </div>
      </div>
    `;
    
    // Insert form if not already present
    const participantsList = document.getElementById('participants-list');
    if (!participantsList.querySelector('.participant-form')) {
      participantsList.insertAdjacentHTML('beforeend', participantForm);
    }
  }
  
  addParticipant() {
    const provider = document.getElementById('add-provider').value;
    const model = document.getElementById('add-model').value;
    const name = document.getElementById('add-name').value;
    const roleSelect = document.getElementById('add-role');
    const role = roleSelect ? roleSelect.value : null;
    
    const participant = {
      provider,
      model,
      name: name || `${provider}-${model}`,
      ...(role && { role })
    };
    
    // Add to UI
    const participantEl = document.createElement('div');
    participantEl.className = 'participant-item';
    participantEl.innerHTML = `
      <span class="participant-name">${participant.name}</span>
      <span class="participant-details">${provider} / ${model}${role ? ` (${role})` : ''}</span>
      <button class="button-remove" onclick="competitionManager.removeParticipant(this)">×</button>
    `;
    participantEl.dataset.participant = JSON.stringify(participant);
    
    const participantsList = document.getElementById('participants-list');
    const form = participantsList.querySelector('.participant-form');
    if (form) {
      participantsList.insertBefore(participantEl, form);
      // Clear form
      document.getElementById('add-name').value = '';
    }
  }
  
  removeParticipant(button) {
    button.parentElement.remove();
  }
  
  async createCompetition() {
    const formData = new FormData(document.getElementById('create-competition-form'));
    const type = formData.get('type');
    
    // Collect participants
    const participants = [];
    document.querySelectorAll('.participant-item').forEach(item => {
      participants.push(JSON.parse(item.dataset.participant));
    });
    
    if (participants.length < 2 && type !== 'team') {
      alert('Please add at least 2 participants');
      return;
    }
    
    if (type === 'team' && participants.length < 1) {
      alert('Please add at least 1 team member');
      return;
    }
    
    // Build competition config
    const config = {
      type,
      name: formData.get('name'),
      gameType: formData.get('gameType'),
      difficulty: formData.get('difficulty'),
      participants
    };
    
    // Add type-specific settings
    if (type === 'tournament') {
      config.roundFormat = formData.get('roundFormat');
    } else if (type === 'league') {
      config.rounds = parseInt(formData.get('rounds'));
      config.pointSystem = {
        win: parseInt(formData.get('winPoints')),
        draw: parseInt(formData.get('drawPoints')),
        loss: parseInt(formData.get('lossPoints'))
      };
    } else if (type === 'team') {
      config.team = {
        name: formData.get('teamName') || 'AI Team',
        members: participants,
        communicationStyle: formData.get('communicationStyle')
      };
    }
    
    try {
      const response = await fetch('/api/competition-sdk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error('Failed to create competition');
      }
      
      const competition = await response.json();
      console.log('Competition created:', competition);
      
      this.hideCreateModal();
      this.loadCompetitions();
      
      // Show success message
      this.showNotification('Competition created successfully!', 'success');
      
    } catch (error) {
      console.error('Error creating competition:', error);
      this.showNotification('Failed to create competition', 'error');
    }
  }
  
  showCreateModal() {
    document.getElementById('create-competition-modal').style.display = 'flex';
  }
  
  hideCreateModal() {
    document.getElementById('create-competition-modal').style.display = 'none';
  }
  
  async loadCompetitions() {
    // Load from local storage or API
    const stored = localStorage.getItem('competitions');
    this.competitions = stored ? JSON.parse(stored) : [];
    
    this.renderCompetitions();
  }
  
  renderCompetitions() {
    const list = document.getElementById('competition-list');
    
    if (this.competitions.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <p>No competitions yet</p>
          <button class="button button-primary" onclick="competitionManager.showCreateModal()">
            Create First Competition
          </button>
        </div>
      `;
      return;
    }
    
    list.innerHTML = this.competitions.map(comp => `
      <div class="competition-card">
        <div class="competition-header">
          <h3>${comp.name}</h3>
          <span class="competition-type">${comp.type}</span>
        </div>
        <div class="competition-details">
          <p>Game: ${comp.gameType} / ${comp.difficulty}</p>
          <p>Participants: ${comp.participants.length}</p>
          <p>Status: ${comp.status}</p>
        </div>
        <div class="competition-actions">
          <button class="button" onclick="competitionManager.viewCompetition('${comp.id}')">
            View Details
          </button>
          ${comp.status === 'created' ? `
            <button class="button button-primary" onclick="competitionManager.startCompetition('${comp.id}')">
              Start Competition
            </button>
          ` : ''}
        </div>
      </div>
    `).join('');
  }
  
  filterCompetitions(tab) {
    // Filter competitions based on status
    // Implementation depends on competition status tracking
  }
  
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('competition-container')) {
    window.competitionManager = new CompetitionManager('competition-container');
    window.competitionManager.init();
  }
});