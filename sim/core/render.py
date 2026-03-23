from __future__ import annotations

import pygame

from sim.core.config import AppConfig
from sim.core.world import World
from sim.nodes.base import DynamicNode, Node


class Renderer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 16)

    def draw(self, surface: pygame.Surface, world: World) -> None:
        surface.fill(self.config.background_color)
        if self.config.show_grid:
            self._draw_grid(surface)
        self._draw_dynamic_targets(surface, world)
        for node in world.all_nodes:
            if not node.visible:
                continue
            if isinstance(node, DynamicNode):
                self._draw_dynamic_vision(surface, node)
            self._draw_node(surface, node)
        self._draw_hud(surface, world)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        tile = self.config.tile_size
        for x in range(0, self.config.screen_width + 1, tile):
            pygame.draw.line(
                surface,
                self.config.grid_color,
                (x, 0),
                (x, self.config.screen_height),
                1,
            )
        for y in range(0, self.config.screen_height + 1, tile):
            pygame.draw.line(
                surface,
                self.config.grid_color,
                (0, y),
                (self.config.screen_width, y),
                1,
            )

    def _draw_node(self, surface: pygame.Surface, node: Node) -> None:
        rect = self._node_rect(node)
        pygame.draw.rect(surface, node.color, rect)
        pygame.draw.rect(surface, (18, 20, 24), rect, 1)

    def _draw_dynamic_targets(self, surface: pygame.Surface, world: World) -> None:
        tile = self.config.tile_size
        for node in world.dynamic_nodes:
            if node.target_pos is None:
                continue
            rect = pygame.Rect(
                node.target_pos.col * tile,
                node.target_pos.row * tile,
                tile,
                tile,
            )
            pygame.draw.rect(surface, (210, 54, 54), rect, 3)

    def _draw_dynamic_vision(self, surface: pygame.Surface, node: DynamicNode) -> None:
        tile = self.config.tile_size
        rect = self._node_rect(node)
        vision_padding = node.vision_range_tiles * tile
        vision_rect = pygame.Rect(
            rect.x - vision_padding,
            rect.y - vision_padding,
            rect.width + (vision_padding * 2),
            rect.height + (vision_padding * 2),
        )
        self._draw_dotted_rect(surface, vision_rect, (196, 48, 48), dash_length=8, gap_length=6)

    def _draw_dotted_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int],
        dash_length: int,
        gap_length: int,
    ) -> None:
        step = dash_length + gap_length

        for x in range(rect.left, rect.right, step):
            end_x = min(x + dash_length, rect.right)
            pygame.draw.line(surface, color, (x, rect.top), (end_x, rect.top), 2)
            pygame.draw.line(surface, color, (x, rect.bottom), (end_x, rect.bottom), 2)

        for y in range(rect.top, rect.bottom, step):
            end_y = min(y + dash_length, rect.bottom)
            pygame.draw.line(surface, color, (rect.left, y), (rect.left, end_y), 2)
            pygame.draw.line(surface, color, (rect.right, y), (rect.right, end_y), 2)

    def _node_rect(self, node: Node) -> pygame.Rect:
        tile = self.config.tile_size
        x = node.pos.col * tile
        y = node.pos.row * tile
        if isinstance(node, DynamicNode):
            offset_x, offset_y = node.screen_offset_px
            x += offset_x * tile
            y += offset_y * tile
        size = node.size_tiles * tile
        return pygame.Rect(round(x), round(y), size, size)

    def _draw_hud(self, surface: pygame.Surface, world: World) -> None:
        lines = [
            f"Static: {len(world.static_nodes)}",
            f"Dynamic: {len(world.dynamic_nodes)}",
            "Arrow keys: move villager_1",
            "W: villager_1 wander",
            "R: reset demo scene",
        ]
        y = 10
        for line in lines:
            text = self.font.render(line, True, (232, 236, 240))
            surface.blit(text, (10, y))
            y += text.get_height() + 4
