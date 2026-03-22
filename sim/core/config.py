from dataclasses import dataclass

from sim.core.pathfinding import PathfindingAlgorithmName


@dataclass(frozen=True)
class AppConfig:
    screen_width: int = 960
    screen_height: int = 640
    fps: int = 60
    tile_size: int = 32
    show_grid: bool = True
    background_color: tuple[int, int, int] = (24, 28, 32)
    grid_color: tuple[int, int, int] = (44, 50, 54)
    pathfinding_algorithm: PathfindingAlgorithmName = "astar"


CONFIG = AppConfig()
