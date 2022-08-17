from argparse import Action
from email.errors import ObsoleteHeaderDefect
from ssl import VERIFY_CRL_CHECK_LEAF
from threading import Thread
import zoneinfo
from model.game import Game
from model.obstacle import Obstacle
from model.unit import Unit
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
from my_modules.game_math import calc_distance, calc_angle, add_vectors, to_ort

EPS = 0.01
PROB_OF_DIRECTION_CHANGE = 0.007
weapons = {"Magic wand": 0, "Staff": 1, "Bow": 2}
loot = {"Weapon": 0, "Shield": 1, "Ammo": 2}

class MyStrategy:
    my_unit: Unit
    move_direction: Vec2
    view_direction: Vec2
    enemy_is_near: bool
    target_enemy: Unit
    target_ammo: Game.loot
    target_shield: Game.loot
    target_obstacle: Obstacle
    passed_obstacles: List[Obstacle]
    action: ActionOrder
    constants: Constants

    def set_view_direction(self, target_point: Vec2):
        self.view_direction.x = target_point.x - self.my_unit.position.x
        self.view_direction.y = target_point.y - self.my_unit.position.y

    def set_move_direction(self, target_point: Vec2, speed: int):
        self.move_direction.x = (target_point.x - self.my_unit.position.x) * speed
        self.move_direction.y = (target_point.y - self.my_unit.position.y) * speed

    def predict_enemy_position(self, enemy: Vec2):
        coef = calc_distance(self.my_unit.position, enemy.position) / self.constants.weapons[self.my_unit.weapon].projectile_speed
        return Vec2(enemy.position.x + enemy.velocity.x * coef, enemy.position.y + enemy.velocity.y * coef)

    def shooting(self):
        predicted_position = self.predict_enemy_position(self.target_enemy)
        self.set_view_direction(predicted_position)
        if calc_distance(self.target_enemy.position, self.my_unit.position) < self.constants.weapons[weapons["Magic wand"]].projectile_speed + 5:
            self.action = ActionOrder.Aim(True)
        else:
            self.action = ActionOrder.Aim(False)

    def choose_enemy(self, game: Game, enemy: Unit):
        distance_to_enemy = calc_distance(self.my_unit.position, enemy.position)
        if distance_to_enemy < self.distance_to_nearest_enemy:
            self.distance_to_nearest_enemy = distance_to_enemy
            self.target_enemy = enemy

    def choose_shield(self, loot: Game.loot, item_tag: int):
        self.target_shield = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
                if calc_distance(self.my_unit.position, loot_instance.position) < calc_distance(self.my_unit.position, self.target_shield.position):
                    self.target_shield = loot_instance
    
    def choose_ammo(self, loot: Game.loot, item_tag: int, weapon_type: int):
        self.target_ammo = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag and loot_instance.item.weapon_type_index == weapon_type:
                if calc_distance(self.my_unit.position, loot_instance.position) < calc_distance(self.my_unit.position, self.target_ammo.position):
                    self.target_ammo = loot_instance
    
    def get_closest_obstacle(self, initial_position: Vec2):
        if self.constants.obstacles[0] != self.target_obstacle:
            closest_obstacle = self.constants.obstacles[0]
        else:
            closest_obstacle = self.constants.obstacles[1]
        dist_to_closest_obstacle = calc_distance(closest_obstacle.position, initial_position)
        for obstacle in self.constants.obstacles:
            distance_to_obstacle = calc_distance(initial_position, obstacle.position)
            if distance_to_obstacle < dist_to_closest_obstacle and obstacle not in self.passed_obstacles:
                closest_obstacle = obstacle
                dist_to_closest_obstacle = distance_to_obstacle
        return closest_obstacle

    def go_around_an_obstacle(self):
        if self.obstacle_passed == True:
            self.initial_direction.x = self.move_direction.x
            self.initial_direction.y = self.move_direction.y
            self.obstacle_passed = False
        closest_obstacle = self.get_closest_obstacle(self.my_unit.position)
        self.maneuver(closest_obstacle.position)
        if self.obstacle_passed == True:
            self.move_direction.x = self.initial_direction.x
            self.move_direction.y = self.initial_direction.y

    def maneuver(self, obstacle_position: Vec2):
        target_vec = to_ort(self.move_direction)
        target_angle = calc_angle(self.move_direction)
        obstacle_vec = to_ort(Vec2(obstacle_position.x - self.my_unit.position.x, obstacle_position.y - self.my_unit.position.y))
        obstacle_angle = calc_angle(obstacle_vec)
        not_is_normal = abs(obstacle_angle - calc_angle(self.initial_direction))
        if not_is_normal < 90 or not_is_normal > 270:
            correction_vec = self.get_correction_vector(target_angle, obstacle_angle, obstacle_vec)
            sum_vector = add_vectors(target_vec, correction_vec)
            self.move_direction.x = sum_vector.x * self.constants.max_unit_forward_speed
            self.move_direction.y = sum_vector.y * self.constants.max_unit_forward_speed
        else:
            self.obstacle_passed = True

    def get_correction_vector(self, target_angle, obstacle_angle, obstacle_vec):
        if abs(obstacle_angle - target_angle) < 180:
            if target_angle < obstacle_angle:
                correction_vec = Vec2(obstacle_vec.y, -obstacle_vec.x)
            else:
                correction_vec = Vec2(-obstacle_vec.y, obstacle_vec.x)
        else:
            if target_angle < obstacle_angle:
                correction_vec = Vec2(-obstacle_vec.y, obstacle_vec.x)
            else:
                correction_vec = Vec2(obstacle_vec.y, -obstacle_vec.x)
        return correction_vec

    def obstacle_is_near(self):
        closest_obstacle = self.get_closest_obstacle(self.my_unit.position)
        dist_to_closest_obstacle = calc_distance(self.my_unit.position, closest_obstacle.position)
        obstacle_approach_distance = self.constants.unit_radius*2 + closest_obstacle.radius
        if dist_to_closest_obstacle < obstacle_approach_distance:
            return True
        return False

    def replenish_shields(self, game: Game):
        self.choose_shield(game.loot, loot["Shield"])
        self.set_move_direction(self.target_shield.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_shield.position)
        if calc_distance(self.my_unit.position, self.target_shield.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_shield.id)

    def replenish_ammo(self, game: Game, weapon_index: int):
        self.choose_ammo(game.loot, loot["Ammo"], weapon_index)
        self.set_move_direction(self.target_ammo.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_ammo.position)
        if calc_distance(self.my_unit.position, self.target_ammo.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_ammo.id)

    def free_movement(self):
        random_point = Vec2(random.uniform(-10, 10), random.uniform(-10, 10))
        self.set_move_direction(random_point, self.constants.max_unit_forward_speed)
        self.set_view_direction(random_point)

    def move_to_next_zone(self, zone_next_center: Vec2):
        self.set_move_direction(zone_next_center, self.constants.max_unit_forward_speed)
        self.set_view_direction(zone_next_center)

    def move_to_obstacle(self):
        distace_to_target_obstacle = calc_distance(self.my_unit.position, self.target_obstacle.position)
        if distace_to_target_obstacle < (self.target_obstacle.radius + self.constants.unit_radius * 2) or distace_to_target_obstacle > self.constants.view_distance:
            self.target_obstacle = self.get_closest_obstacle(self.my_unit.position)
            self.passed_obstacles.append(self.target_obstacle)
        self.set_move_direction(self.target_obstacle.position, 1)
        self.set_view_direction(self.target_obstacle.position)

    def enemy_is_near_actions(self, game, unit):
        self.enemy_is_near = True
        self.choose_enemy(game, unit)
        if unit == game.units[-1]:
            while True:
                if self.my_unit.ammo[self.my_unit.weapon] == 0:
                    self.action = None
                    self.replenish_ammo(game, self.my_unit.weapon)
                    if self.obstacle_is_near():
                        self.go_around_an_obstacle()
                    break
                self.shooting()
                if calc_distance(self.target_enemy.position, self.my_unit.position) > self.constants.weapons[weapons["Magic wand"]].projectile_speed:
                    self.set_move_direction(self.target_enemy.position, 1)
                else:
                    self.set_move_direction(self.target_enemy.position, -1)
                if game.zone.current_radius - calc_distance(self.my_unit.position, game.zone.current_center) < self.constants.unit_radius*2:
                    vec_to_zone = Vec2(game.zone.current_center.x - self.my_unit.position.x, game.zone.current_center.y - self.my_unit.position.y)
                    self.set_move_direction(add_vectors(self.move_direction, vec_to_zone), 1)
                if self.obstacle_is_near():
                    self.go_around_an_obstacle()
                break
        self.passed_obstacles.clear()

    def enemy_is_not_near_actions(self, game, unit):
        distance_to_current_zone_centre = calc_distance(self.my_unit.position, game.zone.current_center)
        self.action = None
        self.enemy_is_near = False
        while True:
            if self.obstacle_is_near():
                self.go_around_an_obstacle()
                break
            if game.zone.current_radius - distance_to_current_zone_centre < self.constants.unit_radius*4:
                self.move_to_next_zone(game.zone.next_center)
                break
            if unit.shield_potions > 0 and unit.shield < self.constants.max_shield:
                self.action = ActionOrder.UseShieldPotion()
                break
            if unit.shield_potions < self.constants.max_shield_potions_in_inventory and game.loot:
                self.replenish_shields(game)
                break
            if unit.ammo[unit.weapon] < self.constants.weapons[unit.weapon].max_inventory_ammo and game.loot:
                self.replenish_ammo(game, unit.weapon)
                break
            if random.random() < PROB_OF_DIRECTION_CHANGE:
                self.free_movement()
                break
            break

    def __init__(self, constants: Constants):
        x = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        y = random.uniform(-constants.max_unit_forward_speed, constants.max_unit_forward_speed)
        self.move_direction = Vec2(x*10, y*10)
        self.view_direction = Vec2(x, y)
        self.my_unit = None
        self.enemy_is_near = False
        self.target_enemy = None
        self.target_ammo = None
        self.target_shield = None
        self.target_obstacle = constants.obstacles[0]
        self.passed_obstacles = []
        self.action = None
        self.constants = constants

        self.initial_direction = Vec2(1, 1)
        self.obstacle_passed = True

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.distance_to_nearest_enemy = self.constants.view_distance
        orders = {}
        self.my_unit = game.units[0]
        self.target_enemy = game.units[0]
        for unit in game.units:
            if unit.player_id != game.my_id:
                self.enemy_is_near_actions(game, unit)
                continue
            if unit == game.units[-1]:
                self.enemy_is_not_near_actions(game, unit)     
            orders[unit.id] = UnitOrder(self.move_direction, self.view_direction, self.action)
        debug_interface.add_placed_text(self.my_unit.position, "{}".format(self.target_enemy.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass
    
    ":.1f"