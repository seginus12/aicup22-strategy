from email.errors import ObsoleteHeaderDefect
from ssl import VERIFY_CRL_CHECK_LEAF
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
from typing import List
import random
from my_modules.game_math import *
from debug_functions import *

PROB_OF_DIRECTION_CHANGE = 0.007
MAX_APPROACH_TO_ZONE = 4
MAX_APPROACH_TO_OBSTACLE = 2
SHOOTING_DISTANCE_MULTIPLIER = 1.1
WEAPONS = {"Magic wand": 0, "Staff": 1, "Bow": 2}
LOOT = {"Weapon": 0, "Shield": 1, "Ammo": 2}

class MyStrategy:
    my_units: List[Unit]
    enemies: List[Unit]
    remembered_enemies: List[Unit]
    closest_obstacles: List[Obstacle]
    move_direction: Vec2
    view_direction: Vec2
    enemy_is_near: bool
    target_enemy: Unit
    target_shield: Game.loot # remove
    target_obstacle: Obstacle
    passed_obstacles: List[Obstacle]
    action: ActionOrder
    constants: Constants
    initial_direction: Vec2
    obstacle_passed: bool

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
        if calc_distance(self.target_enemy.position, self.my_units[0].position) < self.constants.weapons[self.my_units[0].weapon].projectile_speed * SHOOTING_DISTANCE_MULTIPLIER and not self.obstacle_on_the_way(self.target_enemy.position):
            self.action = ActionOrder.Aim(True)
        else:
            self.action = ActionOrder.Aim(False)

    def obstacle_on_the_way(self, enemy_position):
        vec_to_enemy = get_vec(self.my_units[0].position, enemy_position)
        enemy_angle = calc_angle(vec_to_enemy)
        distance_to_enemy = calc_distance(self.my_units[0].position, enemy_position)
        for obstacle in self.closest_obstacles:
            if not obstacle.can_shoot_through:
                distance_to_obstacle = calc_distance(self.my_units[0].position, obstacle.position)
                if distance_to_enemy > distance_to_obstacle:
                    tangent_points = calc_tangent_points(obstacle.position, obstacle.radius, self.my_units[0].position)
                    tangent_angle_0 = calc_angle(get_vec(self.my_units[0].position, tangent_points[0]))
                    tangent_angle_1 = calc_angle(get_vec(self.my_units[0].position, tangent_points[1]))
                    if abs(tangent_angle_0 - tangent_angle_1) < 180:
                        if enemy_angle > tangent_angle_0 and enemy_angle < tangent_angle_1:
                            return True
                    else:
                        if enemy_angle > tangent_angle_0 and enemy_angle > tangent_angle_1 or enemy_angle < tangent_angle_0 and enemy_angle < tangent_angle_1:
                            return True
        return False

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

    def remember_new_enemies(self):
        for enemy in self.enemies:
            is_rembered = self.unit_in_list(self.remembered_enemies, enemy)
            if is_rembered >= 0:
                self.remembered_enemies[is_rembered] = enemy
            else:
                self.remembered_enemies.append(enemy)

    def check_missing_enemies(self):
        remembrered_enemies_count = len(self.remembered_enemies)
        i = 0
        while i < remembrered_enemies_count:
            is_visible = self.unit_in_list(self.enemies, self.remembered_enemies[i])
            if is_visible < 0:
                if self.enemy_in_visible_zone(self.remembered_enemies[i]):
                    self.remembered_enemies.pop(i)
                    remembrered_enemies_count -= 1
            i += 1

    def update_remebered_enemies(self, debug_interface):
        self.check_missing_enemies()
        self.remember_new_enemies()

    def unit_in_list(self, list: List[Unit], unit: Unit):
        for i in range(len(list)):
            if list[i].id == unit.id:
                return i
        return -1

    def enemy_in_visible_zone(self, enemy: Unit):
        extreme_angles = self.calc_extreme_view_angles()
        max_enemy_displacement = calc_tangent_points(enemy.position, self.constants.unit_radius + self.max_tick_passed_distance, self.my_units[0].position)
        max_enemy_displacement_angle_0 = calc_angle(get_vec(self.my_units[0].position, max_enemy_displacement[0]))
        max_enemy_displacement_angle_1 = calc_angle(get_vec(self.my_units[0].position, max_enemy_displacement[1]))
        max_displacement_length = calc_distance(self.my_units[0].position, enemy.position) + self.max_tick_passed_distance
        if  abs(max_enemy_displacement_angle_0 - extreme_angles[0]) < 180 and abs(max_enemy_displacement_angle_1 - extreme_angles[1]) < 180:
            if max_enemy_displacement_angle_0 > extreme_angles[0] and max_enemy_displacement_angle_1 < extreme_angles[1] and max_displacement_length < self.constants.view_distance:
                return True
            return False
        if  abs(max_enemy_displacement_angle_0 - extreme_angles[0]) > 180 and abs(max_enemy_displacement_angle_1 - extreme_angles[1]) < 180:
            if max_enemy_displacement_angle_0 < extreme_angles[0] and max_enemy_displacement_angle_1 < extreme_angles[1] and max_displacement_length < self.constants.view_distance:
                return True
            return False
        if  abs(max_enemy_displacement_angle_0 - extreme_angles[0]) < 180 and abs(max_enemy_displacement_angle_1 - extreme_angles[1]) > 180:
            if max_enemy_displacement_angle_0 > extreme_angles[0] and max_enemy_displacement_angle_1 > extreme_angles[1] and max_displacement_length < self.constants.view_distance:
                return True
            return False

    def go_to_remebrered_enemies(self):
        self.set_move_direction(self.remembered_enemies[-1].position, self.constants.max_unit_forward_speed)
        self.set_view_direction(self.remembered_enemies[-1].position)

    def distribute_units(self, units: List[Unit], my_id):
        my_units = []
        enemeis = []
        for unit in units:
            if unit.player_id == my_id:
                my_units.append(unit)
            else:
                enemeis.append(unit)
        return my_units, enemeis

    def choose_enemy(self):
        for enemy in self.enemies: # should be remembered enemies
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
        target_ammo = None
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag:
                target_ammo = loot_instance
                break
        if target_ammo == None:
            return target_ammo
        for loot_instance in loot:
            if loot_instance.item.TAG == item_tag and loot_instance.item.weapon_type_index == weapon_type:
                if calc_distance(self.my_units[0].position, loot_instance.position) < calc_distance(self.my_units[0].position, target_ammo.position):
                    target_ammo = loot_instance
        return target_ammo
    
    def get_closest_obstacle(self, initial_position: Vec2):
        if self.closest_obstacles[0] != self.target_obstacle:
            closest_obstacle = self.closest_obstacles[0]
        else:
            closest_obstacle = self.closest_obstacles[1]
        dist_to_closest_obstacle = calc_distance(closest_obstacle.position, initial_position)
        for obstacle in self.closest_obstacles:
            distance_to_obstacle = calc_distance(initial_position, obstacle.position)
            if distance_to_obstacle < dist_to_closest_obstacle and obstacle not in self.passed_obstacles:
                closest_obstacle = obstacle
                dist_to_closest_obstacle = distance_to_obstacle
        return closest_obstacle

    def get_closest_obstacles(self):
        closest_obstacles = []
        for obstacle in self.constants.obstacles:
            if abs(obstacle.position.x - self.my_units[0].position.x < self.constants.view_distance) and abs(obstacle.position.y - self.my_units[0].position.y) < self.constants.view_distance:
                closest_obstacles.append(obstacle)
        self.closest_obstacles = closest_obstacles

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
        target_ammo = self.choose_ammo(game.loot, LOOT["Ammo"], weapon_index) # replace
        if target_ammo != None:
            self.set_move_direction(target_ammo.position, self.constants.max_unit_forward_speed)
            self.set_view_direction(target_ammo.position)
            if calc_distance(self.my_units[0].position, target_ammo.position) < self.constants.unit_radius:
                self.action = ActionOrder.Pickup(target_ammo.id)

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

    def keep_distance_to_enemy(self):
        if calc_distance(self.target_enemy.position, self.my_units[0].position) > self.constants.weapons[self.my_units[0].weapon].projectile_speed:
            self.set_move_direction(self.target_enemy.position, 1)
        else:
            self.set_move_direction(self.target_enemy.position, -self.constants.max_unit_backward_speed)

    def actions(self, game: Game):
        self.action = None
        if game.zone.current_radius - calc_distance(self.my_units[0].position, game.zone.current_center) < self.constants.unit_radius * MAX_APPROACH_TO_ZONE:
            self.move_to_next_zone(game.zone.next_center)
        elif self.obstacle_is_near():
            self.go_around_an_obstacle()
        elif self.my_units[0].shield_potions > 0 and self.my_units[0].shield == 0:
            self.action = ActionOrder.UseShieldPotion()
        elif self.my_units[0].ammo[self.my_units[0].weapon] == 0:
            self.replenish_ammo(game, self.my_units[0].weapon)
        elif self.enemies:
            self.keep_distance_to_enemy()
            self.shooting()
        elif self.remembered_enemies:
            self.go_to_remebrered_enemies()
        elif self.my_units[0].shield_potions > 0 and self.my_units[0].shield < self.constants.max_shield:
            self.action = ActionOrder.UseShieldPotion()
        elif self.my_units[0].shield_potions == 0:
            self.replenish_shields(game)
        elif self.my_units[0].ammo[self.my_units[0].weapon] < self.constants.weapons[self.my_units[0].weapon].max_inventory_ammo and game.loot:
            self.replenish_ammo(game, self.my_units[0].weapon)
        elif self.my_units[0].shield_potions < self.constants.max_shield_potions_in_inventory:
            self.replenish_shields(game)
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
        self.remembered_enemies = []
        self.closest_obstacles = []
        self.target_enemy = None
        self.target_shield = None
        self.target_obstacle = constants.obstacles[0]
        self.passed_obstacles = []
        self.action = None
        self.constants = constants
        self.initial_direction = Vec2(1, 1)
        self.obstacle_passed = True

    def get_order(self, game: Game, debug_interface: Optional[DebugInterface]) -> Order:
        self.distance_to_nearest_enemy = self.constants.view_distance # Remove
        orders = {}
        self.my_units, self.enemies = self.distribute_units(game.units, game.my_id)
        self.update_remebered_enemies(debug_interface)
        if self.remembered_enemies:
            self.choose_enemy()
        self.get_closest_obstacles()
        self.actions(game)
        orders[self.my_units[0].id] = UnitOrder(self.move_direction, self.view_direction, self.action)
        if self.target_enemy != None:
            display_enemies_id(debug_interface, self.remembered_enemies)
        display_distance_to_enemy(debug_interface, self.my_units[0], self.remembered_enemies)
        return Order(orders)
    def debug_update(self, displayed_tick: int, debug_interface: DebugInterface):
        pass
    def finish(self):
        pass
    