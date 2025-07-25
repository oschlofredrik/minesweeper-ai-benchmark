import React, { useState } from 'react'
import axios from 'axios'

const GameView = () => {
  const [selectedModel, setSelectedModel] = useState('gpt-4')
  const [numGames, setNumGames] = useState(10)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const models = [
    'gpt-4',
    'gpt-4-turbo',
    'claude-3-opus',
    'claude-3-sonnet',
    'o1-preview',
    'o1-mini'
  ]

  const startEvaluation = async () => {
    setLoading(true)
    setResult(null)
    
    try {
      const response = await axios.post('/api/games/start', {
        model_name: selectedModel,
        num_games: numGames,
        board_size: 8,
        num_mines: 10
      })
      
      setResult(response.data)
    } catch (err) {
      setResult({ error: 'Failed to start evaluation' })
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="game-view">
      <h2>Run Evaluation</h2>
      
      <div className="form-group">
        <label htmlFor="model">Model:</label>
        <select 
          id="model"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          disabled={loading}
        >
          {models.map(model => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="numGames">Number of Games:</label>
        <input
          id="numGames"
          type="number"
          min="1"
          max="100"
          value={numGames}
          onChange={(e) => setNumGames(parseInt(e.target.value))}
          disabled={loading}
        />
      </div>
      
      <button 
        onClick={startEvaluation}
        disabled={loading}
        className="start-button"
      >
        {loading ? 'Starting...' : 'Start Evaluation'}
      </button>
      
      {result && (
        <div className="result">
          {result.error ? (
            <p className="error">{result.error}</p>
          ) : (
            <>
              <p>Status: {result.status}</p>
              <p>Job ID: {result.job_id}</p>
              <p>{result.message}</p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default GameView