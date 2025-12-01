from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Tuple
from rrt_star import RRTStar

app = FastAPI(
    title="RRT* Path Planning API",
    description="FastAPI backend for RRT* path planning algorithm",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Obstacle(BaseModel):
    x: float
    y: float
    radius: float

class PlanningRequest(BaseModel):
    start: Tuple[float, float]
    goal: Tuple[float, float]
    obstacles: List[Obstacle]
    bounds: Tuple[float, float, float, float] = (0, 100, 0, 100)
    step_size: float = 2.0
    goal_sample_rate: float = 0.1
    search_radius: float = 5.0
    max_iterations: int = 1000

class Edge(BaseModel):
    from_point: dict
    to_point: dict

class PlanningResponse(BaseModel):
    success: bool
    path: Optional[List[Tuple[float, float]]]
    tree_edges: List[dict]
    message: str
    iterations: int

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RRT* Path Planning API",
        "endpoints": {
            "/plan": "POST - Run RRT* path planning",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/plan", response_model=PlanningResponse)
async def plan_path(request: PlanningRequest):
    """
    Plan a path using RRT* algorithm

    Args:
        request: Planning request containing start, goal, obstacles, and parameters

    Returns:
        Planning response with path and tree visualization data
    """
    try:
        # Convert Pydantic models to dictionaries
        obstacles_list = [
            {"x": obs.x, "y": obs.y, "radius": obs.radius}
            for obs in request.obstacles
        ]

        # Validate input
        if not (request.bounds[0] <= request.start[0] <= request.bounds[1] and
                request.bounds[2] <= request.start[1] <= request.bounds[3]):
            raise HTTPException(
                status_code=400,
                detail="Start position is outside bounds"
            )

        if not (request.bounds[0] <= request.goal[0] <= request.bounds[1] and
                request.bounds[2] <= request.goal[1] <= request.bounds[3]):
            raise HTTPException(
                status_code=400,
                detail="Goal position is outside bounds"
            )

        # Initialize RRT* planner
        planner = RRTStar(
            start=request.start,
            goal=request.goal,
            obstacles=obstacles_list,
            bounds=request.bounds,
            step_size=request.step_size,
            goal_sample_rate=request.goal_sample_rate,
            search_radius=request.search_radius,
            max_iterations=request.max_iterations
        )

        # Run planning
        path, tree_edges = planner.plan()

        if path is not None:
            return PlanningResponse(
                success=True,
                path=path,
                tree_edges=tree_edges,
                message=f"Path found with {len(path)} waypoints",
                iterations=len(tree_edges)
            )
        else:
            return PlanningResponse(
                success=False,
                path=None,
                tree_edges=tree_edges,
                message="No path found within max iterations",
                iterations=request.max_iterations
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Planning failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
