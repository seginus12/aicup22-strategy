from debug_interface import DebugInterface
from debugging.color import Color
from model.unit import Unit
from model.vec2 import Vec2
from typing import List
from my_modules.game_math import calc_distance

def display_my_id(debug_interface: DebugInterface, my_unit: Unit):
    debug_interface.add_placed_text(my_unit.position, "{}".format(my_unit.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))

def display_enemies_id(debug_interface: DebugInterface, enemies: List[Unit]):
    for enemy in enemies:
        debug_interface.add_placed_text(enemy.position, "{}".format(enemy.id), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))

def display_distance_to_enemy(debug_interface: DebugInterface, my_unit: Unit, enemies: List[Unit]):
    for enemy in enemies:
        distance = calc_distance(my_unit.position, enemy.position)
        debug_interface.add_placed_text(enemy.position, "{:.1f}".format(distance), Vec2(0.5, 0.5), 1, Color(0, 0, 0, 255))