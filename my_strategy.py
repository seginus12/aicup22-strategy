from argparse import Action
# from asyncio.windows_events import NULL
from cmath import sqrt
from threading import Thread
import zoneinfo
from model.game import Game
from model.unit import Unit
from model.order import Order
from model.unit_order import UnitOrder
from model.vec2 import Vec2
from model.action_order import ActionOrder
from model.constants import Constants
from typing import Optional
from debug_interface import DebugInterface
from debugging.color import Color
import random

PROB_OF_DIRECTION_CHANGE = 0.007
weapons = {"Magic wand": 0, "Staff": 1, "Bow": 2}
loot = {"Weapon": 0, "Shield": 1, "Ammo": 2}

class MyStrategy:
    my_unit_position: Vec2
    target_move_direction: Vec2
    target_view_direction: Vec2
    enemy_is_near: bool
    distance_to_nearest_enemy: float
    distance_to_nearest_shield_potion: float
    action: ActionOrder
    constants: Constants

    def calc_distance(self, point1: Vec2, point2: Vec2):
        x_projection = point2.x - point1.x
        y_projection = point2.y - point1.y
        return pow(pow(x_projection, 2) + pow(y_projection, 2), 0.5)

    def choose_target(self, game: Game, enemy: Unit):
        distance_to_enemy = self.calc_distance(self.my_unit_position, enemy.position)
        if distance_to_enemy < self.distance_to_nearest_enemy:
            self.distance_to_nearest_enemy = distance_to_enemy
            self.target_view_direction.x = enemy.position.x - self.my_unit_position.x
            self.target_view_direction.y = enemy.position.y - self.my_unit_position.y
            if distance_to_enemy < self.constants.weapons[weapons["Magic wand"]].projectile_speed + 5:
                self.action = ActionOrder.Aim(True)
            else:
                self.action = ActionOrder.Aim(False)
            if distance_to_enemy > self.constants.weapons[weapons["Magic wand"]].projectile_speed:
                self.target_move_direction.x = self.target_view_direction.x * self.constants.max_unit_forward_speed
                self.target_move_direction.y = self.target_view_direction.y * self.constants.max_unit_forward_speed
            else:
                self.target_move_direction.x = -self.target_view_direction.x * self.constants.max_unit_forward_speed
                self.target_move_direction.y = -self.target_view_direction.y * self.constants.max_unit_forward_speed

    def choose_shield(self, loot: Game.loot, item_tag: int):
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
                distance_to_shield_potion = self.calc_distance(loot_instance.position, self.my_unit_position)
                if distance_to_shield_potion < self.constants.unit_radius:
                    self.action = ActionOrder.Pickup(loot_instance.id)
                    self.distance_to_nearest_shield_potion = self.constants.view_distance
                    break
                if distance_to_shield_potion < self.distance_to_nearest_shield_potion:
                    self.distance_to_nearest_shield_potion = distance_to_shield_potion
                    self.target_view_direction.x = loot_instance.position.x - self.my_unit_position.x
                    self.target_view_direction.y = loot_instance.position.y - self.my_unit_position.y
                    self.target_move_direction.x = self.target_view_direction.x * self.constants.max_unit_forward_speed
                    self.target_move_direction.y = self.target_view_direction.y * self.constants.max_unit_forward_speed
    
    def choose_ammo(self, loot: Game.loot, item_tag: int, weapon_type: int):
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag and loot_instance.item.weapon_type_index == weapon_type:
                distance_to_shield_potion = self.calc_distance(loot_instance.position, self.my_unit_position)
                if distance_to_shield_potion < self.constants.unit_radius:
                    self.action = ActionOrder.Pickup(loot_instance.id)
                    self.distance_to_nearest_shield_potion = self.constants.view_distance
                    break
                if distance_to_shield_potion < self.distance_to_nearest_shield_potion:
                    self.distance_to_nearest_shield_potion = distance_to_shield_potion
                    self.target_view_direction.x = loot_instance.position.x - self.my_unit_position.x
                    self.target_view_direction.y = loot_instance.position.y - self.my_unit_position.y
                    self.target_move_direction.x = self.target_view_direction.x * self.constants.max_unit_forward_speed
                    self.target_move_direction.y = self.target_view_direction.y * self.constants.max_unit_forward_speed
                
    def free_movement(self):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        self.target_move_direction.x = x
        self.target_move_direction.y = y
        self.target_view_direction.x = x * self.constants.max_unit_forward_speed
        self.target_view_direction.y = y * self.constants.max_unit_forward_speed

    def get_out_of_the_zone(self, zone_next_center: Vec2):
        self.target_move_direction.x = zone_next_center.x - self.my_unit_position.x
        self.target_move_direction.y = zone_next_center.y - self.my_unit_position.y
        self.target_view_direction.x = zone_next_center.x - self.my_unit_position.x
        self.target_view_direction.y = zone_next_center.y - self.my_unit_position.y

    def __init__(self, constants: Constants):
        x = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        y = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        self.target_move_direction = Vec2(x ,y)
        self.target_view_direction = Vec2(x, y)
        self.my_unit_position = Vec2(0, 0)
        self.enemy_is_near = False
        self.action = None
        self.distance_to_nearest_enemy = constants.view_distance
        self.distance_to_nearest_shield_potion = constants.view_distance
        self.constants = constants

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.distance_to_nearest_enemy = self.constants.view_distance
        orders = {}
        for unit in game.units:
            if unit.player_id != game.my_id:
                self.enemy_is_near = True
                # self.action = ActionOrder.Aim(False)
                self.choose_target(unit)
                # if unit == game.units[-1]:
                    # print(self.distance_to_nearest_enemy)
                continue
            
            self.my_unit_position = unit.position
            distance_to_current_zone_centre = self.calc_distance(self.my_unit_position, game.zone.current_center)

            if unit == game.units[-1]:
                self.action = None
                self.enemy_is_near = False
                while True:
                    if game.zone.current_radius - distance_to_current_zone_centre < self.constants.unit_radius*4:
                        self.get_out_of_the_zone(game.zone.next_center)
                        break
                    if unit.shield_potions > 0 and unit.shield < self.constants.max_shield:
                        self.action = ActionOrder.UseShieldPotion()
                        break
                    if unit.shield_potions < self.constants.max_shield_potions_in_inventory:
                        self.choose_shield(game.loot, loot["Shield"])
                        break
                    if unit.ammo[unit.weapon] < self.constants.weapons[unit.weapon].max_inventory_ammo:
                        self.choose_ammo(game.loot, loot["Ammo"], weapons["Magic wand"])
                        break
                    if random.random() < PROB_OF_DIRECTION_CHANGE:
                        self.free_movement()
                        break
                    break     
            orders[unit.id] = UnitOrder(self.target_move_direction, self.target_view_direction, self.action)
            debug_interface.add_placed_text(unit.position, "{}/{}".format(self.action, self.constants.weapons[weapons["Magic wand"]].projectile_speed + 5), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass

    ":.1f"