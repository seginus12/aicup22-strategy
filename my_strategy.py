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
import copy
from my_modules.game_math import *

PROB_OF_DIRECTION_CHANGE = 0.007
MAX_APPROACH_TO_ZONE = 4
MAX_APPROACH_TO_OBSTACLE = 2
SHOOTING_DISTANCE_MULTIPLIER = 1.1
WEAPONS = {"Magic wand": 0, "Staff": 1, "Bow": 2}
LOOT = {"Weapon": 0, "Shield": 1, "Ammo": 2}

class MyStrategy:
    my_units: List[Unit]
    enemies: List[Unit]
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
    initial_direction: Vec2
    obstacle_passed: bool
    remembered_enemies: List[Unit]

    def set_view_direction(self, target_point: Vec2):
        self.view_direction.x = target_point.x - self.my_units[0].position.x
        self.view_direction.y = target_point.y - self.my_units[0].position.y

    def set_move_direction(self, target_point: Vec2, speed: int):
        self.move_direction.x = (target_point.x - self.my_units[0].position.x) * speed
        self.move_direction.y = (target_point.y - self.my_units[0].position.y) * speed

    def predict_enemy_position(self, enemy: Vec2):
        coef = calc_distance(self.my_units[0].position, enemy.position) / self.constants.weapons[self.my_units[0].weapon].projectile_speed
        return Vec2(enemy.position.x + enemy.velocity.x * coef, enemy.position.y + enemy.velocity.y * coef)

    def shooting(self):
        predicted_position = self.predict_enemy_position(self.target_enemy)
        self.set_view_direction(predicted_position)
        if calc_distance(self.target_enemy.position, self.my_units[0].position) < self.constants.weapons[self.my_units[0].weapon].projectile_speed * SHOOTING_DISTANCE_MULTIPLIER:
            self.action = ActionOrder.Aim(True)
        else:
            self.action = ActionOrder.Aim(False)

    def calc_view_angle(self):
        return self.constants.field_of_view - (self.constants.field_of_view - self.constants.weapons[self.my_units[0].weapon].aim_field_of_view) * self.my_units[0].aim

    def calc_extreme_view_angles(self):
        view_point = calc_angle(self.my_units[0].direction)
        fov = self.calc_view_angle()
        if view_point - fov / 2 >= 0:
            smaller_angle = view_point - fov / 2
        else:
            smaller_angle = view_point - fov / 2 + 360
        if view_point + fov / 2 <= 360:
            larger_angle = view_point + fov / 2
        else:
            larger_angle = view_point + fov / 2 - 360
        return [smaller_angle, larger_angle]

    def remember_enemy(self, enemy: Unit):
        is_rembered = self.unit_in_list(self.remembered_enemies, enemy)
        if is_rembered >= 0:
            self.remembered_enemies[is_rembered] = enemy
        else:
            self.remembered_enemies.append(enemy)

    def update_remebered_enemies(self, game: Game, debug_interface):
        visible_enemies = self.get_visible_enemies(game.units)
        remembrered_enemies_count = len(self.remembered_enemies)
        i = 0
        while i < remembrered_enemies_count:
            is_visible = self.unit_in_list(visible_enemies, self.remembered_enemies[i])
            if is_visible < 0:
                if self.enemy_in_visible_zone(self.remembered_enemies[i]):
                    self.remembered_enemies.pop(i)
                    remembrered_enemies_count -= 1
            i += 1

    def enemy_in_visible_zone(self, enemy: Unit):
        extreme_angles = self.calc_extreme_view_angles()
        max_enemy_displacement = calc_tangent_points(enemy.position, self.constants.unit_radius + self.max_tick_passed_distance, self.my_units[0].position)
        max_enemy_displacement_angle_0 = calc_angle(get_vec(self.my_units[0].position, max_enemy_displacement[0]))
        max_enemy_displacement_angle_1 = calc_angle(get_vec(self.my_units[0].position, max_enemy_displacement[1]))
        max_displacement_length = calc_distance(self.my_units[0].position, enemy.position) + self.max_tick_passed_distance
        if max_enemy_displacement_angle_0 > extreme_angles[0] and max_enemy_displacement_angle_1 < extreme_angles[1] and max_displacement_length < self.constants.view_distance:
            return True
        return False

    def check_remebrered_enemies(self, units: List[Unit]):
        self.set_move_direction(self.remembered_enemies[-1].position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.remembered_enemies[-1].position)

    def get_visible_enemies(self, units: List[Unit]):
        visible_enemies = copy.deepcopy(units)
        for i in range(self.constants.team_size):
            visible_enemies.pop(i)
        return visible_enemies

    def distribute_units(self, units: List[Unit], my_id):
        my_units = []
        enemeis = []
        for unit in units:
            if unit.player_id == my_id:
                my_units.append(unit)
            else:
                enemeis.append(unit)
        return my_units, enemeis

    def unit_in_list(self, list: List[Unit], unit: Unit):
        for i in range(len(list)):
            if list[i].id == unit.id:
                return i
        return -1

    def choose_enemy(self, game: Game, enemy: Unit):
        distance_to_enemy = calc_distance(self.my_units[0].position, enemy.position)
        if distance_to_enemy < self.distance_to_nearest_enemy:
            self.distance_to_nearest_enemy = distance_to_enemy
            self.target_enemy = enemy

    def choose_shield(self, loot: Game.loot, item_tag: int):
        self.target_shield = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
                if calc_distance(self.my_units[0].position, loot_instance.position) < calc_distance(self.my_units[0].position, self.target_shield.position):
                    self.target_shield = loot_instance
    
    def choose_ammo(self, loot: Game.loot, item_tag: int, weapon_type: int):
        self.target_ammo = loot[0]
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag and loot_instance.item.weapon_type_index == weapon_type:
                if calc_distance(self.my_units[0].position, loot_instance.position) < calc_distance(self.my_units[0].position, self.target_ammo.position):
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
        closest_obstacle = self.get_closest_obstacle(self.my_units[0].position)
        self.maneuver(closest_obstacle.position)
        if self.obstacle_passed == True:
            self.move_direction.x = self.initial_direction.x
            self.move_direction.y = self.initial_direction.y

    def maneuver(self, obstacle_position: Vec2):
        target_vec = to_ort(self.move_direction)
        target_angle = calc_angle(self.move_direction)
        obstacle_vec = to_ort(get_vec(self.my_units[0].position, obstacle_position))
        obstacle_angle = calc_angle(obstacle_vec)
        not_is_normal = abs(obstacle_angle - calc_angle(self.initial_direction))
        if not_is_normal < 90 or not_is_normal > 270:
            correction_vec = self.get_correction_vector(target_angle, obstacle_angle, obstacle_vec)
            sum_vector = add_vectors(target_vec, correction_vec)
            self.move_direction.x = sum_vector.x * self.constants.max_unit_forward_speed
            self.move_direction.y = sum_vector.y * self.constants.max_unit_forward_speed
        else:
            self.obstacle_passed = True

    def get_correction_vector(self, target_angle: float, obstacle_angle: float, obstacle_vec: Vec2):
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
        closest_obstacle = self.get_closest_obstacle(self.my_units[0].position)
        dist_to_closest_obstacle = calc_distance(self.my_units[0].position, closest_obstacle.position)
        obstacle_approach_distance = self.constants.unit_radius * MAX_APPROACH_TO_OBSTACLE + closest_obstacle.radius
        if dist_to_closest_obstacle < obstacle_approach_distance:
            return True
        return False

    def replenish_shields(self, game: Game):
        self.choose_shield(game.loot, LOOT["Shield"])
        self.set_move_direction(self.target_shield.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_shield.position)
        if calc_distance(self.my_units[0].position, self.target_shield.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_shield.id)

    def replenish_ammo(self, game: Game, weapon_index: int):
        self.choose_ammo(game.loot, LOOT["Ammo"], weapon_index)
        self.set_move_direction(self.target_ammo.position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.target_ammo.position)
        if calc_distance(self.my_units[0].position, self.target_ammo.position) < self.constants.unit_radius:
            self.action = ActionOrder.Pickup(self.target_ammo.id)

    def free_movement(self):
        random_point = Vec2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.set_move_direction(random_point, self.constants.max_unit_forward_speed)
        self.set_view_direction(random_point)

    def move_to_next_zone(self, zone_next_center: Vec2):
        self.set_move_direction(zone_next_center, self.constants.max_unit_forward_speed)
        self.set_view_direction(zone_next_center)

    def move_to_obstacle(self):
        distace_to_target_obstacle = calc_distance(self.my_units[0].position, self.target_obstacle.position)
        if distace_to_target_obstacle < (self.target_obstacle.radius + self.constants.unit_radius * MAX_APPROACH_TO_OBSTACLE) or distace_to_target_obstacle > self.constants.view_distance:
            self.target_obstacle = self.get_closest_obstacle(self.my_units[0].position)
            self.passed_obstacles.append(self.target_obstacle)
        self.set_move_direction(self.target_obstacle.position, 1)
        self.set_view_direction(self.target_obstacle.position)

    def enemy_is_near_actions(self, game: Game, unit: Unit, debug_interface):
        self.remember_enemy(unit)
        self.choose_enemy(game, unit)
        if unit == game.units[-1]:
            while True:
                if self.my_units[0].ammo[self.my_units[0].weapon] == 0:
                    self.action = None
                    self.replenish_ammo(game, self.my_units[0].weapon)
                    if self.obstacle_is_near():
                        self.go_around_an_obstacle()
                    break
                self.shooting()
                if calc_distance(self.target_enemy.position, self.my_units[0].position) > self.constants.weapons[self.my_units[0].weapon].projectile_speed:
                    self.set_move_direction(self.target_enemy.position, 1)
                else:
                    self.set_move_direction(self.target_enemy.position, -self.constants.max_unit_backward_speed)
                if game.zone.current_radius - calc_distance(self.my_units[0].position, game.zone.current_center) < self.constants.unit_radius * MAX_APPROACH_TO_ZONE:
                    vec_to_zone = get_vec(self.my_units[0].position, game.zone.current_center)
                    self.set_move_direction(add_vectors(self.move_direction, vec_to_zone), 1)
                if self.obstacle_is_near() and (self.move_direction.x != 0 or self.move_direction.y != 0):
                    self.go_around_an_obstacle()
                break
        self.passed_obstacles.clear()

    def enemy_is_not_near_actions(self, game: Game, unit: Unit):
        distance_to_current_zone_centre = calc_distance(self.my_units[0].position, game.zone.current_center)
        self.action = None
        self.enemy_is_near = False
        if self.obstacle_is_near():
            self.go_around_an_obstacle()
        elif game.zone.current_radius - distance_to_current_zone_centre < self.constants.unit_radius * MAX_APPROACH_TO_ZONE:
            self.move_to_next_zone(game.zone.next_center)
        elif unit.shield_potions > 0 and unit.shield < self.constants.max_shield:
            self.action = ActionOrder.UseShieldPotion()
        elif unit.ammo[unit.weapon] < self.constants.weapons[unit.weapon].max_inventory_ammo and game.loot:
            self.replenish_ammo(game, unit.weapon)
        elif random.random() < PROB_OF_DIRECTION_CHANGE:
            self.free_movement()

    def __init__(self, constants: Constants):
        self.max_tick_passed_distance = constants.max_unit_forward_speed / constants.ticks_per_second
        x = random.uniform(-1, 1) * constants.max_unit_forward_speed
        y = random.uniform(-1, 1) * constants.max_unit_forward_speed
        self.move_direction = Vec2(x, y)
        self.view_direction = Vec2(x, y)
        self.my_units = []
        self.enemies = []
        self.enemy_is_near = False # Remove
        self.target_enemy = None
        self.target_ammo = None
        self.target_shield = None
        self.target_obstacle = constants.obstacles[0]
        self.passed_obstacles = []
        self.action = None
        self.constants = constants
        self.initial_direction = Vec2(1, 1)
        self.obstacle_passed = True
        self.remembered_enemies = []

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.distance_to_nearest_enemy = self.constants.view_distance
        orders = {}
        self.my_units, self.enemies = self.distribute_units(game.units, game.my_id)
        self.target_enemy = game.units[0] # Replace
        self.update_remebered_enemies(game, debug_interface)
        for unit in game.units:
            if unit.player_id != game.my_id:
                self.enemy_is_near_actions(game, unit, debug_interface)
                # debug_interface.add_placed_text(unit.position, "{}".format(unit.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
                continue
            if unit == game.units[-1]:
                if len(self.remembered_enemies) != 0:
                    self.check_remebrered_enemies(game.units)
                else:
                    self.enemy_is_not_near_actions(game, unit)
            else:
                self.enemy_is_near = True
            orders[unit.id] = UnitOrder(self.move_direction, self.view_direction, self.action)
        extreme_angles = self.calc_extreme_view_angles()
        debug_interface.add_placed_text(self.my_units[0].position, "{}\n{:.1f} {:.1f}".format(self.remembered_enemies, extreme_angles[0], extreme_angles[1]), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass
    
    ":.1f"