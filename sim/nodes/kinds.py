from dataclasses import dataclass

from sim.nodes.base import DynamicNode, GridPos, StaticNode
from sim.nodes.behaviors.moveable import Moveable


@dataclass
class TreeNode(StaticNode):
    wood: int = 5


@dataclass
class TownCenterNode(StaticNode):
    storage_wood: int = 0
    storage_food: int = 0
    size_tiles: int = 2


@dataclass
class VillagerNode(Moveable):
    carrying_wood: int = 0
    carrying_food: int = 0


def demo_nodes() -> list[StaticNode | DynamicNode]:
    return [
        TownCenterNode(
            node_id="town_center",
            label="Town Center",
            pos=GridPos(col=10, row=8),
            color=(176, 142, 92),
        ),
        TreeNode(
            node_id="tree_1",
            label="Tree",
            pos=GridPos(col=15, row=6),
            color=(64, 140, 74),
        ),
        TreeNode(
            node_id="tree_2",
            label="Tree",
            pos=GridPos(col=16, row=8),
            color=(64, 140, 74),
        ),
        VillagerNode(
            node_id="villager_1",
            label="Villager",
            pos=GridPos(col=12, row=10),
            color=(114, 186, 245),
            move_speed_tiles=2,
            vision_range_tiles=3,
        ),
        VillagerNode(
            node_id="villager_2",
            label="Villager",
            pos=GridPos(col=13, row=10),
            color=(114, 186, 245),
            move_speed_tiles=2,
            vision_range_tiles=3,
        ),
        VillagerNode(
            node_id="villager_3",
            label="Villager",
            pos=GridPos(col=12, row=11),
            color=(114, 186, 245),
            move_speed_tiles=2,
            vision_range_tiles=3,
        ),
        VillagerNode(
            node_id="villager_4",
            label="Villager",
            pos=GridPos(col=13, row=11),
            color=(114, 186, 245),
            move_speed_tiles=2,
            vision_range_tiles=3,
        ),
        VillagerNode(
            node_id="villager_5",
            label="Villager",
            pos=GridPos(col=14, row=10),
            color=(114, 186, 245),
            move_speed_tiles=2,
            vision_range_tiles=3,
        ),
    ]
