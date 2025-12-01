import numpy as np
import math
from typing import List, Tuple, Optional

class Node:
    """Node class for RRT* tree"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.parent: Optional[Node] = None
        self.cost = 0.0

class RRTStar:
    """RRT* Path Planning Algorithm"""

    def __init__(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        obstacles: List[dict],
        bounds: Tuple[float, float, float, float],
        step_size: float = 1.0,
        goal_sample_rate: float = 0.1,
        search_radius: float = 3.0,
        max_iterations: int = 1000
    ):
        """
        Initialize RRT* planner

        Args:
            start: Start position (x, y)
            goal: Goal position (x, y)
            obstacles: List of obstacles [{'x': x, 'y': y, 'radius': r}, ...]
            bounds: Search space bounds (min_x, max_x, min_y, max_y)
            step_size: Maximum distance to extend tree
            goal_sample_rate: Probability of sampling goal
            search_radius: Radius for rewiring neighbors
            max_iterations: Maximum number of iterations
        """
        self.start = Node(start[0], start[1])
        self.goal = Node(goal[0], goal[1])
        self.obstacles = obstacles
        self.min_x, self.max_x, self.min_y, self.max_y = bounds
        self.step_size = step_size
        self.goal_sample_rate = goal_sample_rate
        self.search_radius = search_radius
        self.max_iterations = max_iterations
        self.node_list = [self.start]

    def plan(self) -> Tuple[Optional[List[Tuple[float, float]]], List[dict]]:
        """
        Execute RRT* planning

        Returns:
            path: List of (x, y) coordinates from start to goal, or None if no path found
            tree_data: List of edges for visualization
        """
        tree_edges = []

        for i in range(self.max_iterations):
            # Sample random node
            if np.random.random() < self.goal_sample_rate:
                rnd_node = Node(self.goal.x, self.goal.y)
            else:
                rnd_node = self.get_random_node()

            # Find nearest node in tree
            nearest_node = self.get_nearest_node(rnd_node)

            # Extend tree towards random node
            new_node = self.steer(nearest_node, rnd_node)

            # Check if path is collision-free
            if not self.check_collision(nearest_node, new_node):
                # Find nearby nodes
                near_nodes = self.find_near_nodes(new_node)

                # Choose best parent
                new_node = self.choose_parent(new_node, near_nodes)

                if new_node:
                    self.node_list.append(new_node)
                    tree_edges.append({
                        'from': {'x': new_node.parent.x, 'y': new_node.parent.y},
                        'to': {'x': new_node.x, 'y': new_node.y}
                    })

                    # Rewire tree
                    self.rewire(new_node, near_nodes)

                    # Check if goal is reached
                    if self.is_near_goal(new_node):
                        if not self.check_collision(new_node, self.goal):
                            last_node = self.steer(new_node, self.goal)
                            if last_node:
                                self.node_list.append(last_node)
                                path = self.generate_final_path()
                                return path, tree_edges

        # No path found
        return None, tree_edges

    def get_random_node(self) -> Node:
        """Generate random node within bounds"""
        x = np.random.uniform(self.min_x, self.max_x)
        y = np.random.uniform(self.min_y, self.max_y)
        return Node(x, y)

    def get_nearest_node(self, target_node: Node) -> Node:
        """Find nearest node in tree to target node"""
        distances = [(node.x - target_node.x) ** 2 + (node.y - target_node.y) ** 2
                    for node in self.node_list]
        min_idx = distances.index(min(distances))
        return self.node_list[min_idx]

    def steer(self, from_node: Node, to_node: Node) -> Node:
        """Steer from from_node towards to_node with step_size"""
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance <= self.step_size:
            new_node = Node(to_node.x, to_node.y)
        else:
            theta = math.atan2(dy, dx)
            new_node = Node(
                from_node.x + self.step_size * math.cos(theta),
                from_node.y + self.step_size * math.sin(theta)
            )

        new_node.parent = from_node
        new_node.cost = from_node.cost + distance
        return new_node

    def check_collision(self, from_node: Node, to_node: Node) -> bool:
        """Check if path from from_node to to_node collides with obstacles"""
        # Check multiple points along the path
        num_checks = int(math.sqrt((to_node.x - from_node.x) ** 2 +
                                   (to_node.y - from_node.y) ** 2) / 0.1)
        num_checks = max(num_checks, 1)

        for i in range(num_checks + 1):
            t = i / num_checks
            x = from_node.x + t * (to_node.x - from_node.x)
            y = from_node.y + t * (to_node.y - from_node.y)

            # Check collision with each obstacle
            for obstacle in self.obstacles:
                dx = x - obstacle['x']
                dy = y - obstacle['y']
                distance = math.sqrt(dx ** 2 + dy ** 2)
                if distance <= obstacle['radius']:
                    return True

        return False

    def find_near_nodes(self, target_node: Node) -> List[Node]:
        """Find nodes within search_radius of target_node"""
        n = len(self.node_list)
        r = min(self.search_radius * math.sqrt(math.log(n) / n), self.step_size)
        r = max(r, self.search_radius)

        near_nodes = []
        for node in self.node_list:
            distance = math.sqrt((node.x - target_node.x) ** 2 +
                               (node.y - target_node.y) ** 2)
            if distance <= r:
                near_nodes.append(node)

        return near_nodes

    def choose_parent(self, new_node: Node, near_nodes: List[Node]) -> Optional[Node]:
        """Choose best parent for new_node from near_nodes"""
        if not near_nodes:
            return new_node

        costs = []
        for near_node in near_nodes:
            if not self.check_collision(near_node, new_node):
                cost = near_node.cost + math.sqrt(
                    (near_node.x - new_node.x) ** 2 +
                    (near_node.y - new_node.y) ** 2
                )
                costs.append(cost)
            else:
                costs.append(float('inf'))

        if not costs or all(c == float('inf') for c in costs):
            return None

        min_cost_idx = costs.index(min(costs))
        new_node.parent = near_nodes[min_cost_idx]
        new_node.cost = costs[min_cost_idx]

        return new_node

    def rewire(self, new_node: Node, near_nodes: List[Node]):
        """Rewire tree to optimize paths"""
        for near_node in near_nodes:
            if near_node == new_node.parent:
                continue

            new_cost = new_node.cost + math.sqrt(
                (near_node.x - new_node.x) ** 2 +
                (near_node.y - new_node.y) ** 2
            )

            if new_cost < near_node.cost:
                if not self.check_collision(new_node, near_node):
                    near_node.parent = new_node
                    near_node.cost = new_cost

    def is_near_goal(self, node: Node) -> bool:
        """Check if node is near goal"""
        distance = math.sqrt((node.x - self.goal.x) ** 2 +
                           (node.y - self.goal.y) ** 2)
        return distance <= self.step_size

    def generate_final_path(self) -> List[Tuple[float, float]]:
        """Generate final path from start to goal"""
        path = []
        node = self.node_list[-1]

        while node.parent is not None:
            path.append((node.x, node.y))
            node = node.parent

        path.append((self.start.x, self.start.y))
        path.reverse()

        return path
