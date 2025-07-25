import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Leaderboard from './components/Leaderboard'
import GameView from './components/GameView'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Tilts AI Benchmark</h1>
          <nav>
            <a href="/">Leaderboard</a>
            <a href="/play">Play</a>
            <a href="/docs">Documentation</a>
          </nav>
        </header>
        
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Leaderboard />} />
            <Route path="/play" element={<GameView />} />
            <Route path="/docs" element={<div>Documentation (Coming Soon)</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App