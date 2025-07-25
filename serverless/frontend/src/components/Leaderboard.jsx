import React, { useState, useEffect } from 'react'
import axios from 'axios'

const Leaderboard = () => {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchLeaderboard()
  }, [])

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get('/api/leaderboard')
      setEntries(response.data)
    } catch (err) {
      setError('Failed to load leaderboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading...</div>
  if (error) return <div className="error">{error}</div>

  return (
    <div className="leaderboard">
      <h2>Model Leaderboard</h2>
      <table className="leaderboard-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Win Rate</th>
            <th>Valid Move Rate</th>
            <th>Games Played</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, index) => (
            <tr key={entry.model_name}>
              <td>{index + 1}</td>
              <td>{entry.model_name}</td>
              <td>{(entry.win_rate * 100).toFixed(1)}%</td>
              <td>{(entry.valid_move_rate * 100).toFixed(1)}%</td>
              <td>{entry.games_played}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Leaderboard