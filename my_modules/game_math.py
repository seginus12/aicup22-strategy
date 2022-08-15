from model.vec2 import Vec2
from math import acos, degrees

def calc_distance(point1: Vec2, point2: Vec2):
        x_projection = point2.x - point1.x
        y_projection = point2.y - point1.y
        return pow(pow(x_projection, 2) + pow(y_projection, 2), 0.5)

def calc_angle(vec: Vec2):
        vec_length = calc_distance(Vec2(0, 0), vec)
        arccos = degrees(acos(vec.x / vec_length))
        sin = vec.y / vec_length
        if sin > 0:
            angle = arccos
        else:
            angle = 360 - arccos
        return angle

def add_vectors(vec1: Vec2, vec2: Vec2):
        return Vec2(vec1.x + vec2.x, vec1.y + vec2.y)

def to_ort(vec: Vec2):
        hypotenuse  = calc_distance(Vec2(0, 0), vec)
        sin = vec.y / hypotenuse
        cos = vec.x / hypotenuse
        return Vec2(cos, sin)