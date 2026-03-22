from __future__ import annotations

import pygame

from sim.core.config import CONFIG
from sim.core.render import Renderer
from sim.core.world import World
from sim.nodes.base import GridPos
from sim.nodes.behaviors.moveable import Moveable


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Civ Sim Restart")
    screen = pygame.display.set_mode((CONFIG.screen_width, CONFIG.screen_height))
    clock = pygame.time.Clock()

    world = World()
    renderer = Renderer(CONFIG)

    running = True
    while running:
        dt = min(clock.tick(CONFIG.fps) / 1000.0, 0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                villager = world.get_dynamic_node("villager_1")
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    world.load_demo_scene()
                elif isinstance(villager, Moveable) and event.key == pygame.K_LEFT:
                    villager.move_towards(GridPos(col=8, row=10))
                elif isinstance(villager, Moveable) and event.key == pygame.K_RIGHT:
                    villager.move_towards(GridPos(col=14, row=10))
                elif isinstance(villager, Moveable) and event.key == pygame.K_UP:
                    villager.move_towards(GridPos(col=12, row=6))
                elif isinstance(villager, Moveable) and event.key == pygame.K_DOWN:
                    villager.move_away_from(GridPos(col=12, row=6))

        world.update(dt)
        renderer.draw(screen, world)
        pygame.display.flip()

    pygame.quit()
