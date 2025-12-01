import React, { useState } from 'react';
import PathPlanningCanvas from './components/PathPlanningCanvas';
import './App.css';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [start, setStart] = useState({ x: 10, y: 10 });
  const [goal, setGoal] = useState({ x: 90, y: 90 });
  const [obstacles, setObstacles] = useState([
    { x: 30, y: 30, radius: 5 },
    { x: 50, y: 50, radius: 8 },
    { x: 70, y: 40, radius: 6 }
  ]);
  const [bounds] = useState({ minX: 0, maxX: 100, minY: 0, maxY: 100 });
  const [parameters, setParameters] = useState({
    stepSize: 2.0,
    goalSampleRate: 0.1,
    searchRadius: 5.0,
    maxIterations: 1000
  });

  const [planningResult, setPlanningResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('start'); // 'start', 'goal', 'obstacle', 'none'

  const runPlanning = async () => {
    setLoading(true);
    setError(null);
    setPlanningResult(null);

    try {
      const response = await axios.post(`${API_URL}/plan`, {
        start: [start.x, start.y],
        goal: [goal.x, goal.y],
        obstacles: obstacles,
        bounds: [bounds.minX, bounds.maxX, bounds.minY, bounds.maxY],
        step_size: parameters.stepSize,
        goal_sample_rate: parameters.goalSampleRate,
        search_radius: parameters.searchRadius,
        max_iterations: parameters.maxIterations
      });

      setPlanningResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Planning failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCanvasClick = (point) => {
    if (mode === 'start') {
      setStart(point);
    } else if (mode === 'goal') {
      setGoal(point);
    } else if (mode === 'obstacle') {
      setObstacles([...obstacles, { ...point, radius: 5 }]);
    }
  };

  const addObstacle = () => {
    const newObstacle = {
      x: Math.random() * (bounds.maxX - bounds.minX) + bounds.minX,
      y: Math.random() * (bounds.maxY - bounds.minY) + bounds.minY,
      radius: 3 + Math.random() * 5
    };
    setObstacles([...obstacles, newObstacle]);
  };

  const clearObstacles = () => {
    setObstacles([]);
  };

  const reset = () => {
    setPlanningResult(null);
    setError(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>RRT* Path Planning Visualization</h1>
      </header>

      <div className="container">
        <div className="controls-panel">
          <div className="section">
            <h3>Points</h3>
            <div className="button-group">
              <button
                className={mode === 'start' ? 'active' : ''}
                onClick={() => setMode('start')}
              >
                Set Start
              </button>
              <button
                className={mode === 'goal' ? 'active' : ''}
                onClick={() => setMode('goal')}
              >
                Set Goal
              </button>
              <button
                className={mode === 'obstacle' ? 'active' : ''}
                onClick={() => setMode('obstacle')}
              >
                Add Obstacle
              </button>
              <button onClick={() => setMode('none')}>
                Select Mode Off
              </button>
            </div>

            <div className="coordinates">
              <p><strong>Start:</strong> ({start.x.toFixed(1)}, {start.y.toFixed(1)})</p>
              <p><strong>Goal:</strong> ({goal.x.toFixed(1)}, {goal.y.toFixed(1)})</p>
            </div>
          </div>

          <div className="section">
            <h3>Obstacles ({obstacles.length})</h3>
            <div className="button-group">
              <button onClick={addObstacle}>Add Random</button>
              <button onClick={clearObstacles}>Clear All</button>
            </div>
          </div>

          <div className="section">
            <h3>Parameters</h3>
            <div className="parameter">
              <label>Step Size: {parameters.stepSize}</label>
              <input
                type="range"
                min="0.5"
                max="5"
                step="0.5"
                value={parameters.stepSize}
                onChange={(e) => setParameters({...parameters, stepSize: parseFloat(e.target.value)})}
              />
            </div>
            <div className="parameter">
              <label>Search Radius: {parameters.searchRadius}</label>
              <input
                type="range"
                min="2"
                max="15"
                step="1"
                value={parameters.searchRadius}
                onChange={(e) => setParameters({...parameters, searchRadius: parseFloat(e.target.value)})}
              />
            </div>
            <div className="parameter">
              <label>Max Iterations: {parameters.maxIterations}</label>
              <input
                type="range"
                min="100"
                max="3000"
                step="100"
                value={parameters.maxIterations}
                onChange={(e) => setParameters({...parameters, maxIterations: parseInt(e.target.value)})}
              />
            </div>
          </div>

          <div className="section">
            <h3>Actions</h3>
            <div className="button-group">
              <button
                className="primary"
                onClick={runPlanning}
                disabled={loading}
              >
                {loading ? 'Planning...' : 'Run RRT* Planning'}
              </button>
              <button onClick={reset}>Reset</button>
            </div>
          </div>

          {planningResult && (
            <div className="section results">
              <h3>Results</h3>
              <p><strong>Status:</strong> {planningResult.success ? '✓ Success' : '✗ Failed'}</p>
              <p><strong>Message:</strong> {planningResult.message}</p>
              <p><strong>Iterations:</strong> {planningResult.iterations}</p>
              {planningResult.path && (
                <p><strong>Path Length:</strong> {planningResult.path.length} waypoints</p>
              )}
            </div>
          )}

          {error && (
            <div className="section error">
              <h3>Error</h3>
              <p>{error}</p>
            </div>
          )}
        </div>

        <div className="canvas-container">
          <PathPlanningCanvas
            start={start}
            goal={goal}
            obstacles={obstacles}
            bounds={bounds}
            planningResult={planningResult}
            onCanvasClick={handleCanvasClick}
            mode={mode}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
