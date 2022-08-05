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
    move_direction: Vec2
    view_direction: Vec2
    enemy_is_near: bool
    target_enemy: Unit
    target_ammo: Game.loot
    target_shield: Game.loot
    action: ActionOrder
    constants: Constants

    def calc_distance(self, point1: Vec2, point2: Vec2):
        x_projection = point2.x - point1.x
        y_projection = point2.y - point1.y
        return pow(pow(x_projection, 2) + pow(y_projection, 2), 0.5)

    def set_view_direction(self, target_point: Vec2):
        self.view_direction.x = target_point.x - self.my_unit_position.x
        self.view_direction.y = target_point.y - self.my_unit_position.y

    def set_move_direction(self, target_point: Vec2, speed: int):
        self.move_direction.x = (target_point.x - self.my_unit_position.x) * speed
        self.move_direction.y = (target_point.y - self.my_unit_position.y) * speed

    def choose_enemy(self, game: Game, enemy: Unit):
        distance_to_enemy = self.calc_distance(self.my_unit_position, enemy.position)
        if distance_to_enemy < self.distance_to_nearest_enemy:
            self.target_enemy = enemy

    def choose_shield(self, loot: Game.loot, item_tag: int):
        self.target_shield = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
                if self.calc_distance(self.my_unit_position, loot_instance.position) < self.calc_distance(self.my_unit_position, self.target_shield.position):
                    self.target_shield = loot_instance
    
    def choose_ammo(self, loot: Game.loot, item_tag: int, weapon_type: int):
        self.target_ammo = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag and loot_instance.item.weapon_type_index == weapon_type:
                if self.calc_distance(self.my_unit_position, loot_instance.position) < self.calc_distance(self.my_unit_position, self.target_ammo.position):
                    self.target_ammo = loot_instance
    
    def replenish_shileds(self, game: Game):
        self.choose_shield(game.loot, loot["Shield"])
        self.set_move_direction(self.target_shield.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_shield.position)
        if self.calc_distance(self.my_unit_position, self.target_shield.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_shield.id)

    def replenish_ammo(self, game: Game, weapon_index: int):
        self.choose_ammo(game.loot, loot["Ammo"], weapon_index)
        self.set_move_direction(self.target_ammo.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_ammo.position)
        if self.calc_distance(self.my_unit_position, self.target_ammo.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_ammo.id)

    def free_movement(self):
        random_point = Vec2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.set_move_direction(random_point, self.constants.max_unit_forward_speed)
        self.set_view_direction(random_point)

    def move_to_next_zone(self, zone_next_center: Vec2):
        self.set_move_direction(zone_next_center, self.constants.max_unit_forward_speed)
        self.set_view_direction(zone_next_center)

    def __init__(self, constants: Constants):
        x = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        y = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        self.move_direction = Vec2(x ,y)
        self.view_direction = Vec2(x, y)
        self.my_unit_position = Vec2(0, 0)
        self.enemy_is_near = False
        self.target_enemy = None
        self.target_ammo = None
        self.target_shield = None
        self.action = None
        self.constants = constants

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.distance_to_nearest_enemy = self.constants.view_distance
        orders = {}
        for unit in game.units:
            if unit.player_id != game.my_id:
                self.enemy_is_near = True
                self.choose_enemy(game, unit)
                if unit == game.units[-1]:
                    self.set_view_direction(unit.position)
                if self.calc_distance(unit.position, self.my_unit_position) < self.constants.weapons[weapons["Magic wand"]].projectile_speed + 5:
                    self.action = ActionOrder.Aim(True)
                else:
                    self.action = ActionOrder.Aim(False)
                if self.calc_distance(unit.position, self.my_unit_position) > self.constants.weapons[weapons["Magic wand"]].projectile_speed:
                    self.set_move_direction(unit.position, self.constants.max_unit_forward_speed)
                else:
                    self.set_move_direction(unit.position, -self.constants.max_unit_forward_speed)
                continue
            
            self.my_unit_position = unit.position
            distance_to_current_zone_centre = self.calc_distance(self.my_unit_position, game.zone.current_center)

            if unit == game.units[-1]:
                self.action = None
                self.enemy_is_near = False
                while True:
                    if game.zone.current_radius - distance_to_current_zone_centre < self.constants.unit_radius*4:
                        self.move_to_next_zone(game.zone.next_center)
                        break
                    if unit.shield_potions > 0 and unit.shield < self.constants.max_shield:
                        self.action = ActionOrder.UseShieldPotion()
                        break
                    if unit.shield_potions < self.constants.max_shield_potions_in_inventory:
                        self.replenish_shileds(game)
                        break
                    if unit.ammo[unit.weapon] < self.constants.weapons[unit.weapon].max_inventory_ammo:
                        self.replenish_ammo(game, unit.weapon)
                        break
                    if random.random() < PROB_OF_DIRECTION_CHANGE:
                        # self.free_movement()
                        self.set_move_direction(Vec2(0, 0), self.constants.max_unit_forward_speed)
                        self.set_view_direction(Vec2(0, 0))
                        break
                    break     
            orders[unit.id] = UnitOrder(self.move_direction, self.view_direction, self.action)
            debug_interface.add_placed_text(unit.position, "{:.1f}\n{:.1f}".format(unit.velocity.x, unit.velocity.y), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass

    ":.1f"