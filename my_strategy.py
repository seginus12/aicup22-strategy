from argparse import Action
# from asyncio.windows_events import NULL
from cmath import sqrt
from email.errors import ObsoleteHeaderDefect
from threading import Thread
import zoneinfo
from model.game import Game
<<<<<<< HEAD
<<<<<<< HEAD
=======
from model.obstacle import Obstacle
from model.unit import Unit
>>>>>>> 87b35ff (Moving to the obstacles instead of free moving when no enemy is near)
=======
from model.obstacle import Obstacle
from model.unit import Unit
>>>>>>> master
from model.order import Order
from model.unit_order import UnitOrder
from model.vec2 import Vec2
from model.action_order import ActionOrder
from model.constants import Constants
from typing import Optional
from debug_interface import DebugInterface
from debugging.color import Color
from typing import List
import random

<<<<<<< HEAD
PROB_OF_DIRECTION_CHANGE = 0.0015
<<<<<<< HEAD
=======
weapons = {"Magic wand": 0, "Staff": 1, "Bow": 2}
>>>>>>> 5a7d816 (Does not work)
=======
PROB_OF_DIRECTION_CHANGE = 0.007
weapons = {"Magic wand": 0, "Staff": 1, "Bow": 2}
loot = {"Weapon": 0, "Shield": 1, "Ammo": 2}
>>>>>>> master

class MyStrategy:
    my_unit: Unit
    move_direction: Vec2
    view_direction: Vec2
    enemy_is_near: bool
<<<<<<< HEAD
<<<<<<< HEAD
    distance_to_nearest_shield_potion: float
=======
=======
>>>>>>> master
    target_enemy: Unit
    target_ammo: Game.loot
    target_shield: Game.loot
    target_obstacle: Obstacle
    passed_obstacles: List[Obstacle]
<<<<<<< HEAD
>>>>>>> 87b35ff (Moving to the obstacles instead of free moving when no enemy is near)
=======
>>>>>>> master
    action: ActionOrder
    constants: Constants

    def calc_distance(self, point1: Vec2, point2: Vec2):
        x_projection = point2.x - point1.x
        y_projection = point2.y - point1.y
        return pow(pow(x_projection, 2) + pow(y_projection, 2), 0.5)
<<<<<<< HEAD
    
    def choose_target(self, enemy_position: Vec2, debug_interface: Optional[DebugInterface]):
        distance_to_enemy = self.calc_distance(self.my_unit_position, enemy_position)
        debug_interface.add_placed_text(self.my_unit_position, "{}".format(distance_to_enemy), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        if distance_to_enemy < self.distance_to_nearest_enemy:
            self.distance_to_nearest_enemy = distance_to_enemy
            self.target_view_direction.x = enemy_position.x - self.my_unit_position.x
            self.target_view_direction.y = enemy_position.y - self.my_unit_position.y
<<<<<<< HEAD
            if distance_to_enemy > self.constants.weapons[0].projectile_speed:
                self.target_move_direction.x = self.target_view_direction.x * self.constants.max_unit_forward_speed
                self.target_move_direction.y = self.target_view_direction.y * self.constants.max_unit_forward_speed
            else:
                self.target_move_direction.x = -self.target_view_direction.x * self.constants.max_unit_forward_speed
                self.target_move_direction.y = -self.target_view_direction.y * self.constants.max_unit_forward_speed
=======
            if distance_to_enemy > self.constants.weapons[weapons["Magic wand"]].projectile_speed:
                self.target_move_direction.x = (enemy_position.x - self.my_unit_position.x) * self.constants.max_unit_forward_speed
                self.target_move_direction.y = (enemy_position.x - self.my_unit_position.x) * self.constants.max_unit_forward_speed
            else:
                self.target_move_direction.x = -(enemy_position.x - self.my_unit_position.x) * self.constants.max_unit_forward_speed
                self.target_move_direction.y = -(enemy_position.x - self.my_unit_position.x) * self.constants.max_unit_forward_speed
>>>>>>> 5a7d816 (Does not work)

    def choose_shield_item(self, loot: Game.loot, item_tag: int):
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
<<<<<<< HEAD
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
=======
=======

    def add_vectors(self, vec1: Vec2, vec2: Vec2):
        return Vec2(vec1.x + vec2.x, vec1.y + vec2.y) 

    def set_view_direction(self, target_point: Vec2):
        self.view_direction.x = target_point.x - self.my_unit.position.x
        self.view_direction.y = target_point.y - self.my_unit.position.y

    def set_move_direction(self, target_point: Vec2, speed: int):
        self.move_direction.x = (target_point.x - self.my_unit.position.x) * speed
        self.move_direction.y = (target_point.y - self.my_unit.position.y) * speed

    def predict_enemy_position(self, enemy: Vec2):
        coef = self.calc_distance(self.my_unit.position, enemy.position) / self.constants.weapons[self.my_unit.weapon].projectile_speed
        return Vec2(enemy.position.x + enemy.velocity.x * coef, enemy.position.y + enemy.velocity.y * coef)

    def choose_enemy(self, game: Game, enemy: Unit):
        distance_to_enemy = self.calc_distance(self.my_unit.position, enemy.position)
        if distance_to_enemy < self.distance_to_nearest_enemy:
            self.target_enemy = enemy

    def choose_shield(self, loot: Game.loot, item_tag: int):
        self.target_shield = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
>>>>>>> master
                if self.calc_distance(self.my_unit.position, loot_instance.position) < self.calc_distance(self.my_unit.position, self.target_shield.position):
                    self.target_shield = loot_instance
    
    def choose_ammo(self, loot: Game.loot, item_tag: int, weapon_type: int):
        self.target_ammo = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag and loot_instance.item.weapon_type_index == weapon_type:
                if self.calc_distance(self.my_unit.position, loot_instance.position) < self.calc_distance(self.my_unit.position, self.target_ammo.position):
                    self.target_ammo = loot_instance
    
    def get_closest_obstacle(self, initial_position: Vec2):
        if self.constants.obstacles[0] != self.target_obstacle:
            closest_obstacle = self.constants.obstacles[0]
        else:
            closest_obstacle = self.constants.obstacles[1]
        dist_to_closest_obstacle = self.calc_distance(closest_obstacle.position, initial_position)
        for obstacle in self.constants.obstacles:
            distance_to_obstacle = self.calc_distance(initial_position, obstacle.position)
            if distance_to_obstacle < dist_to_closest_obstacle and obstacle not in self.passed_obstacles:
                closest_obstacle = obstacle
                dist_to_closest_obstacle = distance_to_obstacle
        return closest_obstacle

    def go_around_an_obstacle(self, obstacle_position: Vec2):
        
        pass

    def replenish_shields(self, game: Game):
        self.choose_shield(game.loot, loot["Shield"])
        self.set_move_direction(self.target_shield.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_shield.position)
        if self.calc_distance(self.my_unit.position, self.target_shield.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_shield.id)

    def replenish_ammo(self, game: Game, weapon_index: int):
        self.choose_ammo(game.loot, loot["Ammo"], weapon_index)
        self.set_move_direction(self.target_ammo.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_ammo.position)
        if self.calc_distance(self.my_unit.position, self.target_ammo.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_ammo.id)
<<<<<<< HEAD
>>>>>>> 87b35ff (Moving to the obstacles instead of free moving when no enemy is near)
=======
>>>>>>> master

    def free_movement(self):
        random_point = Vec2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.set_move_direction(random_point, self.constants.max_unit_forward_speed)
        self.set_view_direction(random_point)

<<<<<<< HEAD
    def get_out_of_the_zone(self, zone_next_center: Vec2):
<<<<<<< HEAD
        self.target_view_direction.x = zone_next_center.x - self.my_unit_position.x
        self.target_view_direction.y = zone_next_center.y - self.my_unit_position.y
        self.target_move_direction.x = zone_next_center.x - self.my_unit_position.x
        self.target_move_direction.y = zone_next_center.y - self.my_unit_position.y

=======
        self.target_move_direction.x = zone_next_center.x - self.my_unit_position.x
        self.target_move_direction.y = zone_next_center.y - self.my_unit_position.y
        self.target_view_direction = self.target_move_direction
>>>>>>> 5a7d816 (Does not work)
=======
    def move_to_next_zone(self, zone_next_center: Vec2):
        self.set_move_direction(zone_next_center, self.constants.max_unit_forward_speed)
        self.set_view_direction(zone_next_center)
>>>>>>> master

    def move_to_obstacle(self):
        distace_to_target_obstacle = self.calc_distance(self.my_unit.position, self.target_obstacle.position)
        if distace_to_target_obstacle < (self.target_obstacle.radius + self.constants.unit_radius * 2) or distace_to_target_obstacle > self.constants.view_distance:
            self.target_obstacle = self.get_closest_obstacle(self.my_unit.position)
            self.passed_obstacles.append(self.target_obstacle)
        self.set_move_direction(self.target_obstacle.position, 1)
        self.set_view_direction(self.target_obstacle.position)

    def __init__(self, constants: Constants):
        x = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        y = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        self.move_direction = Vec2(x ,y)
        self.view_direction = Vec2(x, y)
        self.my_unit = None
        self.enemy_is_near = False
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> master
        self.target_enemy = None
        self.target_ammo = None
        self.target_shield = None
        self.target_obstacle = constants.obstacles[0]
        self.passed_obstacles = []
<<<<<<< HEAD
>>>>>>> 87b35ff (Moving to the obstacles instead of free moving when no enemy is near)
=======
>>>>>>> master
        self.action = None
        self.constants = constants

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
<<<<<<< HEAD
<<<<<<< HEAD
        self.distance_to_nearest_enemy = self.constants.view_distance + 1
        self.enemy_is_near = False
=======
=======
>>>>>>> master
        self.distance_to_nearest_enemy = self.constants.view_distance
>>>>>>> 5a7d816 (Does not work)
        orders = {}
        self.my_unit = game.units[0]
        self.target_enemy = game.units[0]
        for unit in game.units:
            debug_interface.add_placed_text(unit.position, "{} {}".format(game.my_id, unit.player_id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
            if unit.player_id != game.my_id:
                self.enemy_is_near = True
<<<<<<< HEAD
<<<<<<< HEAD
                self.action = ActionOrder.Aim(True)
<<<<<<< HEAD
                self.choose_target(unit.position, debug_interface)
=======
                self.choose_target(unit.position)
                debug_interface.add_placed_text(self.my_unit_position, "{}\n{}".format(self.my_unit_position, unit.position), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
>>>>>>> 5a7d816 (Does not work)
=======
=======
>>>>>>> master
                self.choose_enemy(game, unit)
                if unit == game.units[-1]:
                    predicted_position = self.predict_enemy_position(self.target_enemy)
                    self.set_view_direction(predicted_position)
                    if self.calc_distance(self.target_enemy.position, self.my_unit.position) < self.constants.weapons[weapons["Magic wand"]].projectile_speed + 5:
                        self.action = ActionOrder.Aim(True)
                    else:
                        self.action = ActionOrder.Aim(False)
                    if self.calc_distance(self.target_enemy.position, self.my_unit.position) > self.constants.weapons[weapons["Magic wand"]].projectile_speed:
                        self.set_move_direction(self.target_enemy.position, 1)
                    else:
                        self.set_move_direction(self.target_enemy.position, -1)
                    if game.zone.current_radius - self.calc_distance(self.my_unit.position, game.zone.current_center) < self.constants.unit_radius*2:
                        vec_to_zone = Vec2(game.zone.current_center.x - self.my_unit.position.x, game.zone.current_center.y - self.my_unit.position.y)
                        self.set_move_direction(self.add_vectors(self.move_direction, vec_to_zone), 1)
                self.passed_obstacles.clear()
<<<<<<< HEAD
>>>>>>> 87b35ff (Moving to the obstacles instead of free moving when no enemy is near)
=======
>>>>>>> master
                continue
            
            self.my_unit = unit
            distance_to_current_zone_centre = self.calc_distance(self.my_unit.position, game.zone.current_center)

<<<<<<< HEAD
<<<<<<< HEAD
            if unit == game.units[-1] and not self.enemy_is_near:
                self.action = None
                print("dfd")
                if game.zone.current_radius - distance_to_current_zone_centre < self.constants.unit_radius*2:
                    self.target_view_direction.x = game.zone.next_center.x - self.my_unit_position.x
                    self.target_view_direction.y = game.zone.next_center.y - self.my_unit_position.y
                    self.target_move_direction.x = game.zone.next_center.x - self.my_unit_position.x
                    self.target_move_direction.y = game.zone.next_center.y - self.my_unit_position.y
                '''
=======
            if unit == game.units[-1]:
                self.enemy_is_near = False

            if not self.enemy_is_near and unit == game.units[-1]:
                self.action = None
>>>>>>> 5a7d816 (Does not work)
=======
            if unit == game.units[-1]:
                self.action = None
                self.enemy_is_near = False
>>>>>>> master
                while True:
                    if game.zone.current_radius - distance_to_current_zone_centre < self.constants.unit_radius*4:
                        self.move_to_next_zone(game.zone.next_center)
                        break
                    if unit.shield_potions > 0 and unit.shield < self.constants.max_shield:
                        self.action = ActionOrder.UseShieldPotion()
                        break
<<<<<<< HEAD
                    if unit.shield_potions < self.constants.max_shield_potions_in_inventory:
                        self.choose_shield_item(game.loot, 1)
                        break
                    if unit.ammo[unit.weapon] < self.constants.weapons[unit.weapon].max_inventory_ammo:
                        self.choose_shield_item(game.loot, 2)
=======
                    if unit.shield_potions < self.constants.max_shield_potions_in_inventory and game.loot:
                        self.replenish_shields(game)
                        break
                    if unit.ammo[unit.weapon] < self.constants.weapons[unit.weapon].max_inventory_ammo and game.loot:
                        self.replenish_ammo(game, unit.weapon)
>>>>>>> master
                        break
                    self.move_to_obstacle()
                    '''
                    if random.random() < PROB_OF_DIRECTION_CHANGE:
                        self.free_movement()
                        break
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                    break
                '''
            
            orders[unit.id] = UnitOrder(self.target_move_direction, self.target_view_direction, self.action)
=======
                    break     
            orders[unit.id] = UnitOrder(self.target_move_direction, self.target_view_direction, self.action)
            # debug_interface.add_placed_text(unit.position, "{}\n{}".format(self.target_view_direction, unit.aim), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
>>>>>>> 5a7d816 (Does not work)
=======
                    '''
                    break     
            orders[unit.id] = UnitOrder(self.move_direction, self.view_direction, self.action)
<<<<<<< HEAD
            debug_interface.add_placed_text(unit.position, "{}".format(self.target_obstacle.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
>>>>>>> 87b35ff (Moving to the obstacles instead of free moving when no enemy is near)
=======
            # debug_interface.add_placed_text(unit.position, "{}".format(self.target_obstacle.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
>>>>>>> cc6b6c3 (Before pull)
=======
                    '''
                    break     
            orders[unit.id] = UnitOrder(self.move_direction, self.view_direction, self.action)
            # debug_interface.add_placed_text(unit.position, "{}".format(self.target_obstacle.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
>>>>>>> master
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass

    ":.1f"