from argparse import Action
#from asyncio.windows_events import NULL
from cmath import sqrt
import zoneinfo
from model.game import Game
from model.order import Order
from model.unit_order import UnitOrder
from model.vec2 import Vec2
from model.action_order import ActionOrder
from model.constants import Constants
from typing import Optional
from debug_interface import DebugInterface
from debugging.color import Color
import random

# round(game.zone.next_radius)
class MyStrategy:
    def __init__(self, constants: Constants):
        pass
    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        orders = {}
        # direction = random.random() * (1 + 1) - 1
        # target_point = Vec2(random.randint(1, 500), random.randint(1, 500))
        for unit in game.units:
            if unit.player_id != game.my_id:
                continue
            distance_to_current_zone_centre = pow((pow(game.zone.current_center.x - unit.position.x, 2) + pow(game.zone.current_center.y - unit.position.y, 2)), 0.5)
            distance_to_dest = pow(pow(unit.position.x - game.zone.next_center.x, 2) + pow(unit.position.y - game.zone.next_center.y, 2), 0.5)
            if (game.zone.current_radius - distance_to_current_zone_centre < 1):
                sina = (unit.position.x - game.zone.next_center.x)/distance_to_dest
                cosa = (unit.position.y - game.zone.next_center.y)/distance_to_dest
                orders[unit.id] = UnitOrder(Vec2(-sina * 10, -cosa * 10), Vec2(-sina, -cosa), ActionOrder.Aim(False))
                continue
            
            if (random.random() < 0.007):
                target_point = Vec2(random.randint(0, 100) - 50, random.randint(0, 100) - 50)
                distance_to_target_point = pow((pow(target_point.x - unit.position.x, 2) + pow(target_point.y - unit.position.y, 2)), 0.5)
                sina = (unit.position.x - target_point.x)/distance_to_target_point
                cosa = (unit.position.y - target_point.y)/distance_to_target_point
                orders[unit.id] = UnitOrder(Vec2(-sina * 10, -cosa * 10), Vec2(-sina, -cosa), ActionOrder.Aim(False))
            else:
                sina = unit.position.x
                cosa = unit.position.y
                orders[unit.id] = UnitOrder(Vec2(unit.position.x, unit.position.y), Vec2(-unit.position.x, -unit.position.y), ActionOrder.Aim(False))

            debug_interface.add_placed_text(Vec2(unit.position.x, unit.position.y), "{:.1f}\n{:.1f} {:.1f}\n{:.1f} {:.1f}".format(game.zone.current_radius - distance_to_current_zone_centre, unit.position.x, unit.position.y, sina, cosa), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass