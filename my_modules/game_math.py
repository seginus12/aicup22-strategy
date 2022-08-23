from model.vec2 import Vec2
from math import acos, degrees, pow, cos, sin, pi

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

def calc_angle_radians(vec: Vec2):
        vec_length = calc_distance(Vec2(0, 0), vec)
        arccos = acos(vec.x / vec_length)
        sin = vec.y / vec_length
        if sin > 0:
            angle = arccos
        else:
            angle = 2*pi - arccos
        return angle

def add_vectors(vec1: Vec2, vec2: Vec2):
        return Vec2(vec1.x + vec2.x, vec1.y + vec2.y)

def to_ort(vec: Vec2):
        hypotenuse  = calc_distance(Vec2(0, 0), vec)
        sin = vec.y / hypotenuse
        cos = vec.x / hypotenuse
        return Vec2(cos, sin)

def calc_tangent_points(center: Vec2, radius: float, point: Vec2):
        distance_to_center = calc_distance(center, point)
        tangent_length = pow(pow(distance_to_center, 2) - pow(radius, 2), 0.5)
        vec_to_point = Vec2(center.x - point.x, center.y - point.y)
        target_angle = calc_angle_radians(vec_to_point)
        half_angle = acos(tangent_length / distance_to_center)
        tangent_angle_1 = target_angle - half_angle
        tangent_angle_2 = target_angle + half_angle
        tangent_1 = Vec2(point.x + tangent_length * cos(tangent_angle_1), point.y + tangent_length * sin(tangent_angle_1))
        tangent_2 = Vec2(point.x + tangent_length * cos(tangent_angle_2), point.y + tangent_length * sin(tangent_angle_2))
        return [tangent_1, tangent_2]
