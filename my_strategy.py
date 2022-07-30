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
    my_unit_position: Vec2
    target_point: Vec2
    target_direction: Vec2
    enemy_is_near: bool
    view_distance: float
    distance_to_nearest_enemy: float
    aim = bool

    def __init__(self, constants: Constants):
        x = random.uniform(-6, 6)
        y = random.uniform(-6, 6)
        self.target_point = Vec2(x ,y)
        self.target_direction = Vec2(x, y)
        self.my_unit_position = Vec2(0, 0)
        self.enemy_is_near = False
        self.distance_to_nearest_enemy = constants.view_distance
        self.aim = False

        self.view_distance = constants.view_distance

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.enemy_is_near = False
        self.distance_to_nearest_enemy = self.view_distance
        orders = {}
        for unit in game.units:
            if unit.player_id != game.my_id:
                self.enemy_is_near = True
                self.aim = True
                sina = self.my_unit_position.x - unit.position.x    
                cosa = self.my_unit_position.y - unit.position.y
                distance_to_enemy = pow(pow(sina, 2) + pow(cosa, 2), 0.5)
                if distance_to_enemy < self.distance_to_nearest_enemy:
                    self.distance_to_nearest_enemy = distance_to_enemy
                    self.target_direction.x = -sina
                    self.target_direction.y = -cosa
                    if distance_to_enemy > 30:
                        self.target_point.x = -sina * 10
                        self.target_point.y = -cosa * 10
                    else:
                        self.target_point.x = sina * 10
                        self.target_point.y = cosa * 10
                continue
            
            self.my_unit_position.x = unit.position.x
            self.my_unit_position.y = unit.position.y

            if not self.enemy_is_near and unit == game.units[-1]:
                self.aim = False
                if random.random() < 0.015:
                    a = random.uniform(-6, 6)
                    b = random.uniform(-6, 6)
                    self.target_point.x = a
                    self.target_point.y = b
                    self.target_direction.x = a
                    self.target_direction.y = b

            distance_to_current_zone_centre = pow((pow(game.zone.current_center.x - unit.position.x, 2) + pow(game.zone.current_center.y - unit.position.y, 2)), 0.5)
            if game.zone.current_radius - distance_to_current_zone_centre < 2:
                sina = unit.position.x - game.zone.next_center.x
                cosa = unit.position.y - game.zone.next_center.y
                self.target_point.x = -sina * 10
                self.target_point.y = -cosa * 10
                self.target_direction.x = -sina
                self.target_direction.y = -cosa
                orders[unit.id] = UnitOrder(Vec2(sina * 10, cosa * 10), Vec2(sina, cosa), ActionOrder.Aim(False))
            
            orders[unit.id] = UnitOrder(Vec2(self.target_point.x * 10, self.target_point.y * 10), Vec2(self.target_direction.x, self.target_direction.y), ActionOrder.Aim(self.aim))
            # debug_interface.add_placed_text(Vec2(unit.position.x, unit.position.y), "{:.1f} {:.1f}".format(unit.velocity.x, unit.velocity.y), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass