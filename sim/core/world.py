from __future__ import annotations

from dataclasses import dataclass, field

from sim.core.config import CONFIG
from sim.core.pathfinding import next_path_step
from sim.nodes.base import DynamicNode, GridPos, Node, StaticNode
from sim.nodes.behaviors.moveable import Moveable
from sim.nodes.kinds import demo_nodes


def _new_static_nodes() -> list[StaticNode]:
    return []


def _new_dynamic_nodes() -> list[DynamicNode]:
    return []


@dataclass
class World:
    static_nodes: list[StaticNode] = field(default_factory=_new_static_nodes)
    dynamic_nodes: list[DynamicNode] = field(default_factory=_new_dynamic_nodes)

    def __post_init__(self) -> None:
        if not self.static_nodes and not self.dynamic_nodes:
            self.load_demo_scene()

    @property
    def all_nodes(self) -> list[Node]:
        return [*self.static_nodes, *self.dynamic_nodes]

    def load_demo_scene(self) -> None:
        self.static_nodes.clear()
        self.dynamic_nodes.clear()
        for node in demo_nodes():
            self.add_node(node)

    def add_node(self, node: Node) -> None:
        # Nodes keep a back-reference to the world so behavior mixins can ask
        # the world about occupancy, pathing, and movement primitives.
        node.world = self
        match node:
            case StaticNode():
                self.static_nodes.append(node)
            case DynamicNode():
                self.dynamic_nodes.append(node)
            case _:
                raise TypeError(f"Unsupported node type: {type(node)!r}")

    def get_node(self, node_id: str) -> Node | None:
        for node in self.all_nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_dynamic_node(self, node_id: str) -> DynamicNode | None:
        node = self.get_node(node_id)
        if isinstance(node, DynamicNode):
            return node
        return None

    def is_in_bounds(self, pos: GridPos) -> bool:
        max_cols = self.grid_cols
        max_rows = self.grid_rows
        return 0 <= pos.col < max_cols and 0 <= pos.row < max_rows

    @property
    def grid_cols(self) -> int:
        return CONFIG.screen_width // CONFIG.tile_size

    @property
    def grid_rows(self) -> int:
        return CONFIG.screen_height // CONFIG.tile_size

    def is_tile_blocked(self, pos: GridPos, exclude: Node | None = None) -> bool:
        # Out-of-bounds tiles are treated as blocked so movement/path queries
        # can use a single "can I enter this tile?" check.
        if not self.is_in_bounds(pos):
            return True
        for node in self.all_nodes:
            if node is exclude or not node.is_collidable:
                continue
            if pos in node.occupied_tiles():
                return True
        return False

    def closest_open_tile(self, origin: GridPos, desired: GridPos, exclude: Node | None = None) -> GridPos:
        # Used when behavior wants "go to this tile" but the tile itself may be
        # occupied. We first try the desired tile, then fall back to an adjacent
        # open tile that is closest to the mover's current position.
        if not self.is_tile_blocked(desired, exclude=exclude):
            return desired

        candidates = self.cardinal_neighbors(desired)
        open_candidates = [pos for pos in candidates if not self.is_tile_blocked(pos, exclude=exclude)]
        if not open_candidates:
            return origin
        return min(open_candidates, key=lambda pos: self.tile_distance(origin, pos))

    def closest_open_tile_adjacent_to_node(self, origin: GridPos, target: Node, exclude: Node | None = None) -> GridPos:
        # When moving toward a collidable node, the mover usually wants to end
        # up beside it rather than inside it. For larger nodes, that means
        # checking neighbors around every occupied tile.
        candidate_tiles: list[GridPos] = []
        for occupied in target.occupied_tiles():
            candidate_tiles.extend(self.cardinal_neighbors(occupied))

        unique_candidates: list[GridPos] = []
        seen: set[tuple[int, int]] = set()
        for candidate in candidate_tiles:
            key = (candidate.col, candidate.row)
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)

        open_candidates = [
            pos
            for pos in unique_candidates
            if pos not in target.occupied_tiles() and not self.is_tile_blocked(pos, exclude=exclude)
        ]
        if not open_candidates:
            return origin
        return min(open_candidates, key=lambda pos: self.tile_distance(origin, pos))

    def cardinal_neighbors(self, pos: GridPos) -> list[GridPos]:
        candidates = [
            GridPos(col=pos.col + 1, row=pos.row),
            GridPos(col=pos.col - 1, row=pos.row),
            GridPos(col=pos.col, row=pos.row + 1),
            GridPos(col=pos.col, row=pos.row - 1),
        ]
        return [candidate for candidate in candidates if self.is_in_bounds(candidate)]

    @staticmethod
    def tile_distance(a: GridPos, b: GridPos) -> int:
        return abs(a.col - b.col) + abs(a.row - b.row)

    def update(self, dt: float) -> None:
        for node in self.dynamic_nodes:
            if (
                isinstance(node, Moveable)
                and node.wandering
                and node.target_pos is None
                and node.queued_target_pos is None
            ):
                node.wander(max_distance_tiles=node.wander_distance_tiles)

            # Keep simulation state and render interpolation separate so the
            # movement logic stays easier to reason about.
            self._update_dynamic_node_logic(node, dt)
            self._update_dynamic_node_render_state(node)

    def _update_dynamic_node_logic(self, node: DynamicNode, dt: float) -> None:
        if node.target_pos is None and node.queued_target_pos is not None:
            node.target_pos = node.queued_target_pos
            node.queued_target_pos = None

        if node.target_pos is None:
            return

        if node.pos == node.target_pos:
            self._stop_dynamic_node(node)
            return

        # move_progress tracks how many whole tiles of movement budget this node
        # has accumulated so far. A value of 1.0 means "advance one tile".
        node.move_progress += node.move_speed_tiles * dt
        step_col, step_row = self._next_dynamic_step(node)
        if step_col == 0 and step_row == 0:
            self._stop_dynamic_node(node)
            return

        # A fast unit may have enough progress to cross multiple tiles in one
        # update, so we consume movement in whole-tile steps.
        while node.move_progress >= 1.0:
            node.pos = GridPos(col=node.pos.col + step_col, row=node.pos.row + step_row)
            node.move_progress -= 1.0

            # Apply any queued redirect only after reaching a tile center so the
            # render interpolation does not snap to a different direction mid-step.
            if node.queued_target_pos is not None:
                node.target_pos = node.queued_target_pos
                node.queued_target_pos = None

            if node.pos == node.target_pos:
                self._stop_dynamic_node(node)
                return
            step_col, step_row = self._next_dynamic_step(node)
            if step_col == 0 and step_row == 0:
                self._stop_dynamic_node(node)
                return

    def _update_dynamic_node_render_state(self, node: DynamicNode) -> None:
        if node.target_pos is None:
            node.screen_offset_px = (0.0, 0.0)
            return

        # screen_offset_px is really a tile-fraction offset for now. The
        # renderer multiplies it by tile size to smooth motion between tile
        # centers while the logical position stays grid-based.
        step_col, step_row = self._next_dynamic_step(node)
        node.screen_offset_px = (
            step_col * node.move_progress,
            step_row * node.move_progress,
        )

    def _next_dynamic_step(self, node: DynamicNode) -> tuple[int, int]:
        target_pos = node.target_pos
        if target_pos is None:
            return (0, 0)

        if node.pos == target_pos:
            return (0, 0)

        next_pos = next_path_step(
            CONFIG.pathfinding_algorithm,
            self,
            node.pos,
            target_pos,
            exclude=node,
        )
        if next_pos is None:
            return (0, 0)

        return (next_pos.col - node.pos.col, next_pos.row - node.pos.row)

    def _stop_dynamic_node(self, node: DynamicNode) -> None:
        node.target_pos = None
        node.queued_target_pos = None
        node.move_progress = 0.0
        node.screen_offset_px = (0.0, 0.0)

    def set_dynamic_target_pos(self, node: DynamicNode, target_pos: GridPos) -> bool:
        # If the node is between tile centers, queue the redirect and let it
        # finish the current tile step first to avoid visible popping/jitter.
        if node.target_pos is not None and node.move_progress > 0.0:
            node.queued_target_pos = target_pos
            return True

        node.target_pos = target_pos
        node.queued_target_pos = None
        node.move_progress = 0.0
        node.screen_offset_px = (0.0, 0.0)
        return True

    def clear_dynamic_target(self, node: DynamicNode) -> bool:
        self._stop_dynamic_node(node)
        return True

    @staticmethod
    def next_step_toward(origin: GridPos, target: GridPos) -> GridPos:
        dc = target.col - origin.col
        dr = target.row - origin.row
        if dc == 0 and dr == 0:
            return origin

        if abs(dc) >= abs(dr):
            return GridPos(col=origin.col + (1 if dc > 0 else -1), row=origin.row)
        return GridPos(col=origin.col, row=origin.row + (1 if dr > 0 else -1))

    @staticmethod
    def next_step_away(origin: GridPos, source: GridPos) -> GridPos:
        dc = origin.col - source.col
        dr = origin.row - source.row
        if dc == 0 and dr == 0:
            dc = 1

        if abs(dc) >= abs(dr):
            return GridPos(col=origin.col + (1 if dc > 0 else -1), row=origin.row)
        return GridPos(col=origin.col, row=origin.row + (1 if dr > 0 else -1))
