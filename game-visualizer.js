// Multi-Game Visualization Framework

// Base Game Visualizer Interface
class GameVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.gameState = null;
        this.lastMove = null;
    }
    
    // Methods that must be implemented by subclasses
    initialize(gameConfig) {
        throw new Error('initialize() must be implemented by subclass');
    }
    
    updateState(gameState) {
        throw new Error('updateState() must be implemented by subclass');
    }
    
    highlightMove(move) {
        throw new Error('highlightMove() must be implemented by subclass');
    }
    
    render() {
        throw new Error('render() must be implemented by subclass');
    }
    
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Minesweeper Visualizer
class MinesweeperVisualizer extends GameVisualizer {
    constructor(containerId) {
        super(containerId);
        this.rows = 0;
        this.cols = 0;
        this.board = [];
    }
    
    initialize(gameConfig) {
        const { rows, cols, mines } = gameConfig;
        this.rows = rows || 9;
        this.cols = cols || 9;
        this.mines = mines || 10;
        
        // Initialize empty board
        this.board = Array(this.rows).fill(null).map(() => 
            Array(this.cols).fill(null).map(() => ({
                state: 'hidden',
                value: null,
                flagged: false
            }))
        );
        
        this.render();
    }
    
    updateState(gameState) {
        if (!gameState || !gameState.board) return;
        
        // Parse board state from string representation
        const lines = gameState.board.split('\n');
        
        // Skip header lines (column numbers and separator)
        let startLine = 0;
        if (lines[0] && lines[0].trim().includes(' 0 ')) {
            startLine = 2; // Skip column headers and separator line
        }
        
        for (let r = 0; r < this.rows && r + startLine < lines.length; r++) {
            const line = lines[r + startLine];
            if (!line) continue;
            
            // Extract cells after row number and pipe
            const match = line.match(/^\s*\d+\|\s*(.+)$/);
            if (!match) continue;
            
            const cells = match[1].trim().split(/\s+/);
            for (let c = 0; c < this.cols && c < cells.length; c++) {
                const cell = cells[c];
                if (cell === '?') {
                    this.board[r][c] = { state: 'hidden', value: null, flagged: false };
                } else if (cell === '🚩' || cell === 'F') {
                    this.board[r][c] = { state: 'hidden', value: null, flagged: true };
                } else if (cell === '💣' || cell === '*') {
                    this.board[r][c] = { state: 'revealed', value: -1, flagged: false };
                } else if (cell === '.') {
                    this.board[r][c] = { state: 'revealed', value: 0, flagged: false };
                } else {
                    const num = parseInt(cell);
                    if (!isNaN(num)) {
                        this.board[r][c] = { state: 'revealed', value: num, flagged: false };
                    }
                }
            }
        }
        
        this.render();
    }
    
    highlightMove(move) {
        if (!move || typeof move.row === 'undefined' || typeof move.col === 'undefined') return;
        
        const cell = this.container.querySelector(`[data-row="${move.row}"][data-col="${move.col}"]`);
        if (cell) {
            cell.classList.add('last-move');
            setTimeout(() => cell.classList.remove('last-move'), 2000);
        }
    }
    
    render() {
        this.clear();
        
        const table = document.createElement('table');
        table.className = 'minesweeper-board';
        table.id = 'tilts-board';
        
        // Add column headers
        const headerRow = document.createElement('tr');
        headerRow.appendChild(document.createElement('th')); // Empty corner cell
        for (let c = 0; c < this.cols; c++) {
            const th = document.createElement('th');
            th.textContent = c;
            th.style.fontSize = '0.8em';
            th.style.color = '#666';
            headerRow.appendChild(th);
        }
        table.appendChild(headerRow);
        
        for (let r = 0; r < this.rows; r++) {
            const tr = document.createElement('tr');
            
            // Add row header
            const rowHeader = document.createElement('th');
            rowHeader.textContent = r;
            rowHeader.style.fontSize = '0.8em';
            rowHeader.style.color = '#666';
            rowHeader.style.width = '2em';
            tr.appendChild(rowHeader);
            
            for (let c = 0; c < this.cols; c++) {
                const td = document.createElement('td');
                const cell = this.board[r][c];
                
                td.dataset.row = r;
                td.dataset.col = c;
                
                if (cell.state === 'revealed') {
                    td.classList.add('revealed');
                    if (cell.value === -1) {
                        td.classList.add('bomb');
                        td.textContent = '●';
                    } else if (cell.value === 0) {
                        td.textContent = '';
                    } else {
                        td.textContent = cell.value;
                        td.dataset.adjBombs = cell.value;
                    }
                } else if (cell.flagged) {
                    td.classList.add('flagged');
                } else {
                    td.classList.add('hidden');
                }
                
                tr.appendChild(td);
            }
            
            table.appendChild(tr);
        }
        
        this.container.appendChild(table);
    }
}

// Risk Visualizer
class RiskVisualizer extends GameVisualizer {
    constructor(containerId) {
        super(containerId);
        this.territories = new Map();
        this.continents = new Map();
        this.selectedTerritory = null;
        this.phase = 'reinforce';
    }
    
    initialize(gameConfig) {
        // Define continents with colors
        this.continents = new Map([
            ['north_america', { name: 'North America', color: '#4B8BFF', territories: [] }],
            ['south_america', { name: 'South America', color: '#FF6B6B', territories: [] }],
            ['europe', { name: 'Europe', color: '#4ECDC4', territories: [] }],
            ['africa', { name: 'Africa', color: '#FFD93D', territories: [] }],
            ['asia', { name: 'Asia', color: '#95E1D3', territories: [] }],
            ['australia', { name: 'Australia', color: '#F38181', territories: [] }]
        ]);
        
        // Initialize territories with positions (simplified grid layout)
        this.initializeTerritories();
        this.render();
    }
    
    initializeTerritories() {
        // Simplified territory layout - in a real implementation, this would be more complex
        const territoryData = [
            // North America
            { id: 'alaska', name: 'Alaska', continent: 'north_america', x: 1, y: 1 },
            { id: 'northwest_territory', name: 'NW Territory', continent: 'north_america', x: 3, y: 1 },
            { id: 'greenland', name: 'Greenland', continent: 'north_america', x: 5, y: 1 },
            { id: 'alberta', name: 'Alberta', continent: 'north_america', x: 2, y: 2 },
            { id: 'ontario', name: 'Ontario', continent: 'north_america', x: 3, y: 2 },
            { id: 'eastern_canada', name: 'E. Canada', continent: 'north_america', x: 4, y: 2 },
            { id: 'western_us', name: 'W. United States', continent: 'north_america', x: 2, y: 3 },
            { id: 'eastern_us', name: 'E. United States', continent: 'north_america', x: 3, y: 3 },
            { id: 'central_america', name: 'Central America', continent: 'north_america', x: 2, y: 4 },
            
            // South America
            { id: 'venezuela', name: 'Venezuela', continent: 'south_america', x: 3, y: 5 },
            { id: 'peru', name: 'Peru', continent: 'south_america', x: 2, y: 6 },
            { id: 'brazil', name: 'Brazil', continent: 'south_america', x: 3, y: 6 },
            { id: 'argentina', name: 'Argentina', continent: 'south_america', x: 2, y: 7 },
            
            // Europe
            { id: 'iceland', name: 'Iceland', continent: 'europe', x: 6, y: 2 },
            { id: 'great_britain', name: 'Great Britain', continent: 'europe', x: 6, y: 3 },
            { id: 'scandinavia', name: 'Scandinavia', continent: 'europe', x: 7, y: 2 },
            { id: 'ukraine', name: 'Ukraine', continent: 'europe', x: 8, y: 3 },
            { id: 'northern_europe', name: 'N. Europe', continent: 'europe', x: 7, y: 3 },
            { id: 'western_europe', name: 'W. Europe', continent: 'europe', x: 6, y: 4 },
            { id: 'southern_europe', name: 'S. Europe', continent: 'europe', x: 7, y: 4 },
            
            // Africa
            { id: 'north_africa', name: 'North Africa', continent: 'africa', x: 6, y: 5 },
            { id: 'egypt', name: 'Egypt', continent: 'africa', x: 7, y: 5 },
            { id: 'east_africa', name: 'East Africa', continent: 'africa', x: 7, y: 6 },
            { id: 'central_africa', name: 'Central Africa', continent: 'africa', x: 6, y: 6 },
            { id: 'south_africa', name: 'South Africa', continent: 'africa', x: 6, y: 7 },
            { id: 'madagascar', name: 'Madagascar', continent: 'africa', x: 8, y: 7 },
            
            // Asia
            { id: 'ural', name: 'Ural', continent: 'asia', x: 9, y: 2 },
            { id: 'siberia', name: 'Siberia', continent: 'asia', x: 10, y: 2 },
            { id: 'yakutsk', name: 'Yakutsk', continent: 'asia', x: 11, y: 2 },
            { id: 'kamchatka', name: 'Kamchatka', continent: 'asia', x: 12, y: 2 },
            { id: 'afghanistan', name: 'Afghanistan', continent: 'asia', x: 9, y: 4 },
            { id: 'middle_east', name: 'Middle East', continent: 'asia', x: 8, y: 5 },
            { id: 'india', name: 'India', continent: 'asia', x: 10, y: 5 },
            { id: 'china', name: 'China', continent: 'asia', x: 11, y: 4 },
            { id: 'siam', name: 'Siam', continent: 'asia', x: 11, y: 5 },
            { id: 'irkutsk', name: 'Irkutsk', continent: 'asia', x: 10, y: 3 },
            { id: 'mongolia', name: 'Mongolia', continent: 'asia', x: 11, y: 3 },
            { id: 'japan', name: 'Japan', continent: 'asia', x: 12, y: 4 },
            
            // Australia
            { id: 'indonesia', name: 'Indonesia', continent: 'australia', x: 10, y: 6 },
            { id: 'new_guinea', name: 'New Guinea', continent: 'australia', x: 11, y: 6 },
            { id: 'western_australia', name: 'W. Australia', continent: 'australia', x: 10, y: 7 },
            { id: 'eastern_australia', name: 'E. Australia', continent: 'australia', x: 11, y: 7 }
        ];
        
        territoryData.forEach(t => {
            this.territories.set(t.id, {
                ...t,
                owner: null,
                armies: 0
            });
            
            const continent = this.continents.get(t.continent);
            if (continent) {
                continent.territories.push(t.id);
            }
        });
    }
    
    updateState(gameState) {
        if (!gameState || !gameState.territories) return;
        
        // Update territory ownership and armies
        Object.entries(gameState.territories).forEach(([tid, tdata]) => {
            const territory = this.territories.get(tid);
            if (territory) {
                territory.owner = tdata.owner;
                territory.armies = tdata.armies || 0;
            }
        });
        
        this.phase = gameState.phase || 'reinforce';
        this.render();
    }
    
    highlightMove(move) {
        // Highlight territories involved in the move
        if (move.territory) {
            this.highlightTerritory(move.territory);
        }
        if (move.from) {
            this.highlightTerritory(move.from, 'source');
        }
        if (move.to) {
            this.highlightTerritory(move.to, 'target');
        }
    }
    
    highlightTerritory(territoryId, type = 'default') {
        const elem = this.container.querySelector(`[data-territory="${territoryId}"]`);
        if (elem) {
            elem.classList.add('highlight', `highlight-${type}`);
            setTimeout(() => {
                elem.classList.remove('highlight', `highlight-${type}`);
            }, 2000);
        }
    }
    
    render() {
        this.clear();
        
        const board = document.createElement('div');
        board.className = 'risk-board';
        
        // Create grid-based layout
        const grid = document.createElement('div');
        grid.className = 'risk-grid';
        grid.style.display = 'grid';
        grid.style.gridTemplateColumns = 'repeat(12, 1fr)';
        grid.style.gridTemplateRows = 'repeat(8, 1fr)';
        grid.style.gap = '4px';
        grid.style.width = '100%';
        grid.style.aspectRatio = '1.5';
        
        // Render territories
        this.territories.forEach((territory, tid) => {
            const elem = document.createElement('div');
            elem.className = 'risk-territory';
            elem.dataset.territory = tid;
            elem.style.gridColumn = territory.x;
            elem.style.gridRow = territory.y;
            
            // Set background color based on continent
            const continent = this.continents.get(territory.continent);
            if (continent) {
                elem.style.backgroundColor = continent.color + '33'; // 20% opacity
            }
            
            // Add owner color border
            if (territory.owner) {
                const ownerColors = {
                    'player_0': '#FF4444',
                    'player_1': '#4444FF',
                    'player_2': '#44FF44',
                    'player_3': '#FFFF44'
                };
                elem.style.border = `3px solid ${ownerColors[territory.owner] || '#888'}`;
            }
            
            // Add territory info
            const name = document.createElement('div');
            name.className = 'territory-name';
            name.textContent = territory.name;
            
            const armies = document.createElement('div');
            armies.className = 'territory-armies';
            armies.textContent = territory.armies || '0';
            
            elem.appendChild(name);
            elem.appendChild(armies);
            
            // Add click handler for interactions
            elem.addEventListener('click', () => this.onTerritoryClick(tid));
            
            grid.appendChild(elem);
        });
        
        // Add legend
        const legend = document.createElement('div');
        legend.className = 'risk-legend';
        legend.innerHTML = `
            <h4>Continents</h4>
            <div class="continent-list">
                ${Array.from(this.continents.entries()).map(([id, cont]) => `
                    <div class="continent-item">
                        <span class="continent-color" style="background-color: ${cont.color}"></span>
                        <span>${cont.name}</span>
                    </div>
                `).join('')}
            </div>
            <div class="phase-info">
                <strong>Phase:</strong> ${this.phase.toUpperCase()}
            </div>
        `;
        
        board.appendChild(grid);
        board.appendChild(legend);
        this.container.appendChild(board);
        
        // Add CSS if not already added
        if (!document.getElementById('risk-styles')) {
            const style = document.createElement('style');
            style.id = 'risk-styles';
            style.textContent = `
                .risk-board {
                    width: 100%;
                    font-family: var(--font-family);
                }
                
                .risk-territory {
                    border: 2px solid #ccc;
                    border-radius: 4px;
                    padding: 8px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    min-height: 60px;
                }
                
                .risk-territory:hover {
                    transform: scale(1.05);
                    z-index: 10;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                .territory-name {
                    font-size: 11px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }
                
                .territory-armies {
                    font-size: 18px;
                    font-weight: bold;
                }
                
                .risk-territory.highlight {
                    animation: pulse 0.5s ease-in-out;
                }
                
                .risk-territory.highlight-source {
                    background-color: #FFE066 !important;
                }
                
                .risk-territory.highlight-target {
                    background-color: #FF6B6B !important;
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                    100% { transform: scale(1); }
                }
                
                .risk-legend {
                    margin-top: 20px;
                    padding: 16px;
                    background: #f5f5f5;
                    border-radius: 4px;
                }
                
                .continent-list {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                    margin: 8px 0;
                }
                
                .continent-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .continent-color {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 1px solid #ccc;
                }
                
                .phase-info {
                    margin-top: 12px;
                    font-size: 14px;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    onTerritoryClick(territoryId) {
        console.log('Territory clicked:', territoryId);
        // This would be connected to game logic for making moves
    }
}

// Factory function to create appropriate visualizer
function createGameVisualizer(gameType, containerId) {
    switch (gameType) {
        case 'minesweeper':
            return new MinesweeperVisualizer(containerId);
        case 'risk':
            return new RiskVisualizer(containerId);
        default:
            throw new Error(`Unknown game type: ${gameType}`);
    }
}

// Export for use in other modules
window.GameVisualizer = GameVisualizer;
window.MinesweeperVisualizer = MinesweeperVisualizer;
window.RiskVisualizer = RiskVisualizer;
window.createGameVisualizer = createGameVisualizer;