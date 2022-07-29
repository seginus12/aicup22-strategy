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

class MyStrategy:
    my_unit_position_x: float
    my_unit_position_y: float
    target_point_x: float
    target_point_y: float
    target_direction_x: float
    target_direction_y: float

    def __init__(self, constants: Constants):
        self.target_point_x = 0
        self.target_point_y = 0
        self.target_direction_x = 0
        self.target_direction_y = 0
        self.my_unit_position_x = 0
        self.my_unit_position_y = 0

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        orders = {}
        for unit in game.units:

            if unit.player_id != game.my_id:
                sina = unit.position.x - self.my_unit_position_x
                cosa = unit.position.y - self.my_unit_position_y
                self.target_point_x = -sina * 10
                self.target_point_y = -cosa * 10
                self.target_direction_x = -sina
                self.target_direction_y = -cosa
                print(sina, cosa)
                continue

            self.my_unit_position_x = unit.position.x
            self.my_unit_position_y = unit.position.y

            distance_to_current_zone_centre = pow((pow(game.zone.current_center.x - unit.position.x, 2) + pow(game.zone.current_center.y - unit.position.y, 2)), 0.5)
            distance_to_dest = pow(pow(unit.position.x - game.zone.next_center.x, 2) + pow(unit.position.y - game.zone.next_center.y, 2), 0.5)
            if (game.zone.current_radius - distance_to_current_zone_centre < 10):
                sina = (unit.position.x - game.zone.next_center.x)/distance_to_dest
                cosa = (unit.position.y - game.zone.next_center.y)/distance_to_dest
                self.target_point_x = -sina * 10
                self.target_point_y = -cosa * 10
                self.target_direction_x = -sina
                self.target_direction_y = -cosa
                orders[unit.id] = UnitOrder(Vec2(-sina * 10, -cosa * 10), Vec2(-sina, -cosa), ActionOrder.Aim(False))
            
            '''
            if (random.random() < 0.015):
                a = random.uniform(-6, 6)
                b = random.uniform(-6, 6)
                self.target_point_x = a
                self.target_point_y = b
                self.target_direction_x = a
                self.target_direction_y = b
                orders[unit.id] = UnitOrder(Vec2(self.target_point_x * 10, self.target_point_y * 10), Vec2(self.target_direction_x, self.target_direction_y), ActionOrder.Aim(False))
            else:
                orders[unit.id] = UnitOrder(Vec2(self.target_point_x * 10, self.target_point_y * 10), Vec2(self.target_direction_x, self.target_direction_y), ActionOrder.Aim(False))
            '''
            orders[unit.id] = UnitOrder(Vec2(-self.target_point_x * 10, -self.target_point_y * 10), Vec2(-self.target_direction_x, -self.target_direction_y), ActionOrder.Aim(True))
            debug_interface.add_placed_text(Vec2(unit.position.x, unit.position.y), "{:.1f} {:.1f}\n{:.1f} {:.1f}".format(unit.velocity.x, unit.velocity.y, game.my_id, unit.player_id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass