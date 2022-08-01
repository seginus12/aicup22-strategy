from argparse import Action
# from asyncio.windows_events import NULL
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

PROB_OF_DIRECTION_CHANGE = 0.015

class MyStrategy:
    my_unit_position: Vec2
    target_point: Vec2
    target_direction: Vec2
    enemy_is_near: bool
    constants: Constants

    def __init__(self, constants: Constants):
        x = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        y = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        self.target_move_direction = Vec2(x ,y)
        self.target_view_direction = Vec2(x, y)
        self.my_unit_position = Vec2(0, 0)
        self.enemy_is_near = False
        self.aim = False
        self.constants = constants

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.enemy_is_near = False
        self.distance_to_nearest_enemy = self.constants.view_distance
        orders = {}
        for unit in game.units:
            if unit.player_id != game.my_id:
                self.enemy_is_near = True
                self.aim = True
                x_projection = self.my_unit_position.x - unit.position.x    
                y_projection = self.my_unit_position.y - unit.position.y
                distance_to_enemy = pow(pow(x_projection, 2) + pow(y_projection, 2), 0.5)
                if distance_to_enemy < self.distance_to_nearest_enemy:
                    self.distance_to_nearest_enemy = distance_to_enemy
                    self.target_view_direction.x = -x_projection
                    self.target_view_direction.y = -y_projection
                    if distance_to_enemy > self.constants.weapons[0].projectile_speed:
                        self.target_move_direction.x = -x_projection * self.constants.max_unit_forward_speed
                        self.target_move_direction.y = -y_projection * self.constants.max_unit_forward_speed
                    else:
                        self.target_move_direction.x = x_projection * self.constants.max_unit_forward_speed
                        self.target_move_direction.y = y_projection * self.constants.max_unit_forward_speed
                continue
            
            self.my_unit_position.x = unit.position.x
            self.my_unit_position.y = unit.position.y

            if not self.enemy_is_near and unit == game.units[-1]:
                self.aim = False
                if unit.shield_potions < self.constants.max_shield_potions_in_inventory:
                    pass
                    '''
                    for loot in game.loot:
                        if loot.item.TAG == 1:
                            x_projection = self.my_unit_position.x - loot.position.x
                            y_projection = self.my_unit_position.y - loot.position.y
                            distance_to_shield_potion = pow(pow(x_projection, 2) + pow(y_projection, 2), 0.5)
                            if distance_to_shield_potion < self.distance_to_nearest_shield_potion:
                                self.distance_to_nearest_shield_potion = distance_to_shield_potion
                                self.target_view_direction.x = -x_projection
                                self.target_view_direction.y = -y_projection
                                self.target_move_direction.x = -x_projection * self.constants.max_unit_forward_speed
                                self.target_move_direction.y = -y_projection * self.constants.max_unit_forward_speed
                    '''
                elif random.random() < PROB_OF_DIRECTION_CHANGE:
                    a = random.uniform(-self.constants.max_unit_forward_speed, self.constants.max_unit_forward_speed)
                    b = random.uniform(-self.constants.max_unit_forward_speed, self.constants.max_unit_forward_speed)
                    self.target_move_direction.x = a
                    self.target_move_direction.y = b
                    self.target_view_direction.x = a
                    self.target_view_direction.y = b

            distance_to_current_zone_centre = pow((pow(game.zone.current_center.x - unit.position.x, 2) + pow(game.zone.current_center.y - unit.position.y, 2)), 0.5)
            if game.zone.current_radius - distance_to_current_zone_centre < 2 * self.constants.unit_radius:
                x_projection = unit.position.x - game.zone.next_center.x
                y_projection = unit.position.y - game.zone.next_center.y
                self.target_move_direction.x = -x_projection * self.constants.max_unit_forward_speed
                self.target_move_direction.y = -y_projection * self.constants.max_unit_forward_speed
                if not self.enemy_is_near and unit == game.units[-1]:
                    self.target_view_direction.x = -x_projection
                    self.target_view_direction.y = -y_projection
                orders[unit.id] = UnitOrder(Vec2(x_projection * self.constants.max_unit_forward_speed, y_projection * self.constants.max_unit_forward_speed), Vec2(x_projection, y_projection), ActionOrder.Aim(False))
            
            orders[unit.id] = UnitOrder(Vec2(self.target_move_direction.x * self.constants.max_unit_forward_speed, self.target_move_direction.y * self.constants.max_unit_forward_speed), Vec2(self.target_view_direction.x, self.target_view_direction.y), ActionOrder.Aim(self.aim))
            # debug_interface.add_placed_text(Vec2(unit.position.x, unit.position.y), "{:.1f} {:.1f}".format(unit.velocity.x, unit.velocity.y), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass