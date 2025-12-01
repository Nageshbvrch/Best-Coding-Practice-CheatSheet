import React, { useEffect, useRef } from 'react';

const PathPlanningCanvas = ({
  start,
  goal,
  obstacles,
  bounds,
  planningResult,
  onCanvasClick,
  mode
}) => {
  const canvasRef = useRef(null);
  const canvasWidth = 800;
  const canvasHeight = 800;

  // Convert world coordinates to canvas coordinates
  const worldToCanvas = (x, y) => {
    const scaleX = canvasWidth / (bounds.maxX - bounds.minX);
    const scaleY = canvasHeight / (bounds.maxY - bounds.minY);
    return {
      x: (x - bounds.minX) * scaleX,
      y: canvasHeight - (y - bounds.minY) * scaleY // Flip Y axis
    };
  };

  // Convert canvas coordinates to world coordinates
  const canvasToWorld = (x, y) => {
    const scaleX = (bounds.maxX - bounds.minX) / canvasWidth;
    const scaleY = (bounds.maxY - bounds.minY) / canvasHeight;
    return {
      x: x * scaleX + bounds.minX,
      y: (canvasHeight - y) * scaleY + bounds.minY // Flip Y axis
    };
  };

  const handleClick = (event) => {
    if (!canvasRef.current || mode === 'none') return;

    const rect = canvasRef.current.getBoundingClientRect();
    const canvasX = event.clientX - rect.left;
    const canvasY = event.clientY - rect.top;
    const worldCoords = canvasToWorld(canvasX, canvasY);

    onCanvasClick(worldCoords);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Draw grid
    ctx.strokeStyle = '#f0f0f0';
    ctx.lineWidth = 1;
    const gridSize = 10;
    for (let i = 0; i <= bounds.maxX - bounds.minX; i += gridSize) {
      const pos = worldToCanvas(bounds.minX + i, bounds.minY);
      ctx.beginPath();
      ctx.moveTo(pos.x, 0);
      ctx.lineTo(pos.x, canvasHeight);
      ctx.stroke();
    }
    for (let i = 0; i <= bounds.maxY - bounds.minY; i += gridSize) {
      const pos = worldToCanvas(bounds.minX, bounds.minY + i);
      ctx.beginPath();
      ctx.moveTo(0, pos.y);
      ctx.lineTo(canvasWidth, pos.y);
      ctx.stroke();
    }

    // Draw obstacles
    ctx.fillStyle = 'rgba(100, 100, 100, 0.7)';
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    obstacles.forEach(obstacle => {
      const pos = worldToCanvas(obstacle.x, obstacle.y);
      const scaleX = canvasWidth / (bounds.maxX - bounds.minX);
      const radius = obstacle.radius * scaleX;

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });

    // Draw tree edges if available
    if (planningResult && planningResult.tree_edges) {
      ctx.strokeStyle = 'rgba(150, 150, 255, 0.3)';
      ctx.lineWidth = 1;
      planningResult.tree_edges.forEach(edge => {
        const from = worldToCanvas(edge.from.x, edge.from.y);
        const to = worldToCanvas(edge.to.x, edge.to.y);

        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      });
    }

    // Draw path if available
    if (planningResult && planningResult.path) {
      ctx.strokeStyle = '#4CAF50';
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      planningResult.path.forEach((point, index) => {
        const pos = worldToCanvas(point[0], point[1]);
        if (index === 0) {
          ctx.moveTo(pos.x, pos.y);
        } else {
          ctx.lineTo(pos.x, pos.y);
        }
      });
      ctx.stroke();

      // Draw waypoints
      ctx.fillStyle = '#4CAF50';
      planningResult.path.forEach(point => {
        const pos = worldToCanvas(point[0], point[1]);
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 4, 0, 2 * Math.PI);
        ctx.fill();
      });
    }

    // Draw start point
    const startPos = worldToCanvas(start.x, start.y);
    ctx.fillStyle = '#2196F3';
    ctx.strokeStyle = '#1565C0';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(startPos.x, startPos.y, 10, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Draw start label
    ctx.fillStyle = '#1565C0';
    ctx.font = 'bold 14px Arial';
    ctx.fillText('S', startPos.x - 5, startPos.y + 5);

    // Draw goal point
    const goalPos = worldToCanvas(goal.x, goal.y);
    ctx.fillStyle = '#FF5722';
    ctx.strokeStyle = '#D84315';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(goalPos.x, goalPos.y, 10, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Draw goal label
    ctx.fillStyle = '#D84315';
    ctx.font = 'bold 14px Arial';
    ctx.fillText('G', goalPos.x - 5, goalPos.y + 5);

    // Draw mode indicator
    if (mode !== 'none') {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.font = 'bold 16px Arial';
      ctx.fillText(`Mode: ${mode.toUpperCase()}`, 10, 30);
    }

  }, [start, goal, obstacles, bounds, planningResult, mode]);

  return (
    <canvas
      ref={canvasRef}
      width={canvasWidth}
      height={canvasHeight}
      onClick={handleClick}
      style={{ maxWidth: '100%', height: 'auto' }}
    />
  );
};

export default PathPlanningCanvas;
