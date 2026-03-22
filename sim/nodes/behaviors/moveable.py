import random

from sim.nodes.base import DynamicNode, GridPos, Node


class Moveable(DynamicNode):
    def move_towards(self, target: Node | GridPos) -> bool:
        if self.world is None:
            return False
        self.wandering = False
        # Behaviors decide intent; the world decides whether the resolved tile
        # is actually open and how the node gets there over time.
        target_pos = self._resolve_target_pos(target)
        return self.world.set_dynamic_target_pos(self, target_pos)

    def move_away_from(self, target: Node | GridPos) -> bool:
        if self.world is None:
            return False
        self.wandering = False
        target_pos = self._resolve_source_pos(target)
        next_pos = self.world.next_step_away(self.pos, target_pos)
        return self.world.set_dynamic_target_pos(self, next_pos)

    def stop(self) -> bool:
        if self.world is None:
            return False
        self.wandering = False
        return self.world.clear_dynamic_target(self)

    def wander(self, max_distance_tiles: int = 4) -> bool:
        if self.world is None:
            return False
        self.wandering = True
        self.wander_distance_tiles = max_distance_tiles

        candidates: list[GridPos] = []
        for row_delta in range(-max_distance_tiles, max_distance_tiles + 1):
            for col_delta in range(-max_distance_tiles, max_distance_tiles + 1):
                if col_delta == 0 and row_delta == 0:
                    continue
                candidate = GridPos(
                    col=self.pos.col + col_delta,
                    row=self.pos.row + row_delta,
                )
                if not self.world.is_in_bounds(candidate):
                    continue
                if self.world.is_tile_blocked(candidate, exclude=self):
                    continue
                candidates.append(candidate)

        if not candidates:
            return False

        return self.world.set_dynamic_target_pos(self, random.choice(candidates))

    def _resolve_target_pos(self, target: Node | GridPos) -> GridPos:
        if isinstance(target, GridPos):
            if self.world is None:
                return target
            # For raw grid targets, adjust to the nearest reachable tile if the
            # requested destination is blocked.
            return self.world.closest_open_tile(self.pos, target, exclude=self)

        if self.world is None:
            return target.pos
        if target.is_collidable and target is not self:
            # For solid targets, "move toward" means "move to an open tile next
            # to them", not "try to occupy the same tile(s)".
            return self.world.closest_open_tile_adjacent_to_node(self.pos, target, exclude=self)
        return self.world.closest_open_tile(self.pos, target.pos, exclude=self)

    @staticmethod
    def _resolve_source_pos(target: Node | GridPos) -> GridPos:
        if isinstance(target, GridPos):
            return target
        return target.pos
