from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from sim.core.world import World


class NodeKind(Enum):
    STATIC = auto()
    DYNAMIC = auto()


@dataclass
class GridPos:
    col: int
    row: int


@dataclass
class Node(ABC):
    node_id: str
    label: str
    pos: GridPos
    color: tuple[int, int, int]
    size_tiles: int = 1
    visible: bool = True
    is_collidable: bool = True
    world: World | None = field(default=None, init=False, repr=False, compare=False)

    @property
    @abstractmethod
    def kind(self) -> NodeKind:
        """Return the high-level node family."""
        ...

    def occupied_tiles(self) -> list[GridPos]:
        return [
            GridPos(col=self.pos.col + col_offset, row=self.pos.row + row_offset)
            for row_offset in range(self.size_tiles)
            for col_offset in range(self.size_tiles)
        ]


@dataclass
class StaticNode(Node):
    @property
    def kind(self) -> NodeKind:
        return NodeKind.STATIC


@dataclass
class DynamicNode(Node):
    move_speed_tiles: float = 1.0
    vision_range_tiles: int = 4
    target_pos: GridPos | None = None
    queued_target_pos: GridPos | None = None
    move_progress: float = 0.0
    screen_offset_px: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))

    @property
    def kind(self) -> NodeKind:
        return NodeKind.DYNAMIC


NodeType: TypeAlias = StaticNode | DynamicNode
