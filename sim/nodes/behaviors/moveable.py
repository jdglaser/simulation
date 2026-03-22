from sim.nodes.base import DynamicNode, GridPos, Node


class Moveable(DynamicNode):
    def move_towards(self, target: Node | GridPos) -> bool:
        if self.world is None:
            return False
        # Behaviors decide intent; the world decides whether the resolved tile
        # is actually open and how the node gets there over time.
        target_pos = self._resolve_target_pos(target)
        return self.world.set_dynamic_target_pos(self, target_pos)

    def move_away_from(self, target: Node | GridPos) -> bool:
        if self.world is None:
            return False
        target_pos = self._resolve_source_pos(target)
        next_pos = self.world.next_step_away(self.pos, target_pos)
        return self.world.set_dynamic_target_pos(self, next_pos)

    def stop(self) -> bool:
        if self.world is None:
            return False
        return self.world.clear_dynamic_target(self)

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
