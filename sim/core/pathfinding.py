from __future__ import annotations

import heapq
from typing import Callable, Literal, Protocol

from sim.nodes.base import GridPos, Node


class PathfindingContext(Protocol):
    def cardinal_neighbors(self, pos: GridPos) -> list[GridPos]:
        ...

    def is_tile_blocked(self, pos: GridPos, exclude: Node | None = None) -> bool:
        ...

    @staticmethod
    def tile_distance(a: GridPos, b: GridPos) -> int:
        ...


PathfindingAlgorithmName = Literal["astar", "greedy"]
PathfindingAlgorithm = Callable[[PathfindingContext, GridPos, GridPos, Node | None], GridPos | None]


def greedy_next_step(
    context: PathfindingContext,
    start: GridPos,
    goal: GridPos,
    exclude: Node | None = None,
) -> GridPos | None:
    if start == goal:
        return None

    candidates = context.cardinal_neighbors(start)
    open_candidates = [
        pos for pos in candidates if not context.is_tile_blocked(pos, exclude=exclude)
    ]
    if not open_candidates:
        return None

    return min(
        open_candidates,
        key=lambda pos: (context.tile_distance(pos, goal), pos.row, pos.col),
    )


def astar_next_step(
    context: PathfindingContext,
    start: GridPos,
    goal: GridPos,
    exclude: Node | None = None,
) -> GridPos | None:
    if start == goal:
        return None

    frontier: list[tuple[int, int, int, tuple[int, int]]] = []
    start_key = (start.col, start.row)
    heapq.heappush(
        frontier,
        (context.tile_distance(start, goal), start.row, start.col, start_key),
    )

    came_from: dict[tuple[int, int], tuple[int, int] | None] = {
        start_key: None,
    }
    cost_so_far: dict[tuple[int, int], int] = {
        start_key: 0,
    }

    while frontier:
        _, _, _, current_key = heapq.heappop(frontier)
        current = GridPos(col=current_key[0], row=current_key[1])

        if current == goal:
            break

        for neighbor in context.cardinal_neighbors(current):
            # Never path through blocked tiles. Higher-level behaviors are
            # responsible for resolving "move toward a collidable thing" into
            # a reachable open destination first.
            if context.is_tile_blocked(neighbor, exclude=exclude):
                continue

            neighbor_key = (neighbor.col, neighbor.row)
            new_cost = cost_so_far[current_key] + 1
            if neighbor_key in cost_so_far and new_cost >= cost_so_far[neighbor_key]:
                continue

            cost_so_far[neighbor_key] = new_cost
            priority = new_cost + context.tile_distance(neighbor, goal)
            heapq.heappush(
                frontier,
                (priority, neighbor.row, neighbor.col, neighbor_key),
            )
            came_from[neighbor_key] = current_key

    goal_key = (goal.col, goal.row)
    if goal_key not in came_from:
        return None

    step_key = goal_key
    while came_from[step_key] != start_key:
        parent = came_from[step_key]
        if parent is None:
            return None
        step_key = parent

    return GridPos(col=step_key[0], row=step_key[1])


ALGORITHMS: dict[PathfindingAlgorithmName, PathfindingAlgorithm] = {
    "astar": astar_next_step,
    "greedy": greedy_next_step,
}


def next_path_step(
    algorithm: PathfindingAlgorithmName,
    context: PathfindingContext,
    start: GridPos,
    goal: GridPos,
    exclude: Node | None = None,
) -> GridPos | None:
    return ALGORITHMS[algorithm](context, start, goal, exclude)
