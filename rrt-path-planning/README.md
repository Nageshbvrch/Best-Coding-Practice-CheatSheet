# RRT* Path Planning Application

A full-stack application implementing the RRT* (Rapidly-exploring Random Tree Star) algorithm for optimal path planning. Built with FastAPI backend and React frontend.

## Features

- **RRT* Algorithm**: Optimal path planning with dynamic obstacle avoidance
- **Interactive Visualization**: Real-time canvas-based visualization of the planning process
- **Customizable Parameters**: Adjust step size, search radius, and iteration count
- **Dynamic Obstacles**: Add, remove, and position obstacles interactively
- **Real-time Planning**: Execute path planning with visual feedback
- **RESTful API**: FastAPI backend with automatic documentation

## Project Structure

```
rrt-path-planning/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── rrt_star.py          # RRT* algorithm implementation
│   ├── requirements.txt     # Python dependencies
│   └── .gitignore
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   └── PathPlanningCanvas.js  # Visualization component
│   │   ├── App.js           # Main application component
│   │   ├── App.css          # Application styles
│   │   ├── index.js         # React entry point
│   │   └── index.css        # Global styles
│   ├── package.json         # Node dependencies
│   ├── .env.example         # Environment variables example
│   └── .gitignore
└── README.md
```

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd rrt-path-planning/backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

API documentation will be available at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd rrt-path-planning/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Start the development server:
```bash
npm start
```

The application will open in your browser at `http://localhost:3000`

## Usage

### Setting Up the Planning Problem

1. **Set Start Point**: Click "Set Start" button, then click on the canvas to place the start point (blue circle with "S")
2. **Set Goal Point**: Click "Set Goal" button, then click on the canvas to place the goal point (red circle with "G")
3. **Add Obstacles**:
   - Click "Add Obstacle" button and click on canvas to place obstacles
   - Or use "Add Random" to add random obstacles
   - Use "Clear All" to remove all obstacles

### Adjusting Parameters

- **Step Size** (0.5-5.0): Maximum distance the tree extends in each iteration
- **Search Radius** (2-15): Radius for finding nearby nodes during rewiring
- **Max Iterations** (100-3000): Maximum number of iterations before giving up

### Running Path Planning

1. Configure start, goal, obstacles, and parameters
2. Click "Run RRT* Planning"
3. Wait for the algorithm to complete
4. View results:
   - **Light blue lines**: RRT* exploration tree
   - **Green line**: Optimal path found
   - **Green dots**: Path waypoints

### Results

The results panel shows:
- Success status
- Number of iterations used
- Number of waypoints in the path
- Any error messages if planning failed

## API Endpoints

### `POST /plan`

Execute RRT* path planning.

**Request Body:**
```json
{
  "start": [10, 10],
  "goal": [90, 90],
  "obstacles": [
    {"x": 30, "y": 30, "radius": 5},
    {"x": 50, "y": 50, "radius": 8}
  ],
  "bounds": [0, 100, 0, 100],
  "step_size": 2.0,
  "goal_sample_rate": 0.1,
  "search_radius": 5.0,
  "max_iterations": 1000
}
```

**Response:**
```json
{
  "success": true,
  "path": [[10, 10], [12.5, 13.2], ..., [90, 90]],
  "tree_edges": [...],
  "message": "Path found with 25 waypoints",
  "iterations": 453
}
```

### `GET /health`

Health check endpoint.

### `GET /`

Root endpoint with API information.

### `GET /docs`

Interactive API documentation (Swagger UI).

## RRT* Algorithm

RRT* is an optimal sampling-based path planning algorithm that:

1. Randomly samples points in the configuration space
2. Extends the tree towards sampled points
3. Rewires the tree to optimize path cost
4. Finds collision-free paths while avoiding obstacles

Key features:
- **Asymptotic optimality**: Converges to optimal solution
- **Anytime algorithm**: Improves solution over time
- **Handles complex environments**: Works with arbitrary obstacles

## Development

### Backend Development

Run with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

The React development server supports hot-reloading automatically.

### Building for Production

Frontend:
```bash
cd frontend
npm run build
```

This creates an optimized production build in the `build/` directory.

## Troubleshooting

### CORS Errors

If you encounter CORS errors, ensure:
1. Backend is running on `http://localhost:8000`
2. Frontend is configured with correct API URL in `.env`
3. CORS middleware is properly configured in `main.py`

### No Path Found

If the algorithm can't find a path:
- Increase max iterations
- Reduce step size for finer exploration
- Check if start/goal are blocked by obstacles
- Verify obstacles aren't creating impossible scenarios

### Slow Performance

For faster planning:
- Reduce max iterations
- Increase step size
- Reduce search radius
- Simplify obstacle configuration

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **NumPy**: Numerical computing library
- **Uvicorn**: ASGI server

### Frontend
- **React**: JavaScript library for building user interfaces
- **Axios**: Promise-based HTTP client
- **HTML5 Canvas**: 2D graphics rendering

## License

This project is provided as-is for educational and demonstration purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Future Enhancements

- [ ] Add different planning algorithms (RRT, PRM, A*)
- [ ] 3D visualization support
- [ ] Path smoothing options
- [ ] Export/import scenarios
- [ ] Animation of planning process
- [ ] Performance metrics and comparison
- [ ] Multi-agent path planning
- [ ] Dynamic obstacle support

## Acknowledgments

Based on the RRT* algorithm by Karaman and Frazzoli (2011).
