from __future__ import annotations

from math import sin, cos, tan, pi, sqrt
from copy import copy
import numpy as np

from .Coord import Coord
from .objects.Polygon3D import Polygon3D
from .helper import *

class Camera:
    def __init__(
            self,
            x: float = 0.0, y: float = 0.0, z: float = 0.0,
            ax: float = 0.0, ay: float = 0.0, az: float = 0.0,
            viewport_distance: float = 1.0,
            hFOV: int = 90, vFOV: int = 90
    ) -> None:

        self.position = np.array([x, y, z])
        self.angle = np.array([ax, ay, az])

        self._prev_angle = self.angle
        self._get_rotation_matrix()

        self.viewport_distance = viewport_distance

        self._get_clipping_planes(
            hFOV = clamp(hFOV, 1, 179),
            vFOV = clamp(vFOV, 1, 179)
        )

    # Camera transformation

    def set_position(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.position = np.array([x, y, z], dtype=np.float64)

    def set_angle(self, ax: float = 0.0, ay: float = 0.0, az: float = 0.0) -> None:
        self.angle = np.array([ax, ay, az], dtype=np.float64)

    def move(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.position += np.array([x, y, z])

    def rotate(self, ax: float = 0.0, ay: float = 0.0, az: float = 0.0) -> None:
        self.angle += np.array([ax, ay, az])

    def detect_input(
            self,
            canvas: TCanvas,
            movement_speed: float = 0.1,
            rotation_speed: float = pi/120,
            keymap: dict = None,
    ) -> None:
        yaw = self.angle[1]

        forward = np.array([-sin(yaw), 0, cos(yaw)])
        right = np.array([cos(yaw), 0, sin(yaw)])

        if keymap is None:
            keymap = {
                "forward": "W",
                "backward": "S",
                "left": "A",
                "right": "D",
                "up": "Q",
                "down": "E",

                "lookup": "I",
                "lookdown": "K",
                "turnleft": "J",
                "turnright": "L",
                "counterclockwise": "U",
                "clockwise": "O",
            }
        
        if canvas.key_pressed(keymap["forward"]):
            self.position += forward * movement_speed
        if canvas.key_pressed(keymap["backward"]):
            self.position -= forward * movement_speed

        if canvas.key_pressed(keymap["left"]):
            self.position -= right * movement_speed
        if canvas.key_pressed(keymap["right"]):
            self.position += right * movement_speed

        if canvas.key_pressed(keymap["up"]):
            self.position[1] += movement_speed
        if canvas.key_pressed(keymap["down"]):
            self.position[1] -= movement_speed

        ax = ay = az = 0

        if canvas.key_pressed(keymap["lookup"]):
            ax = rotation_speed
        if canvas.key_pressed(keymap["lookdown"]):
            ax = -rotation_speed

        if canvas.key_pressed(keymap["turnleft"]):
            ay = rotation_speed
        if canvas.key_pressed(keymap["turnright"]):
            ay = -rotation_speed

        if canvas.key_pressed(keymap["counterclockwise"]):
            az = rotation_speed
        if canvas.key_pressed(keymap["clockwise"]):
            az = -rotation_speed

        self.rotate(ax, ay, az)

    # Object translation and projection

    def _draw(self, object: BaseObject, canvas: TCanvas) -> None:
        if hasattr(object, "p1") and object.p1.dim() == 2:
            raise TypeError(f"{type(object)} is not a 3D object, thus cannot be used with Camera.")

        width, height = canvas.width, canvas.height
        width_center, height_center = canvas.width_center, canvas.height_center
        scale = max(width, height) * self.scale_mult

        pos = self.position

        d = self.viewport_distance
        clipping_planes = zip(self.clipping_normals, self.clipping_distances)       

        if not np.array_equal(self._prev_angle, self.angle):
            self._get_rotation_matrix()
        rotation_matrix = self._rotation_matrix

        has_p2 = hasattr(object, "p2")
        has_p3 = hasattr(object, "p3")
        has_multipoints = hasattr(object, "points")

        # Translate

        if has_multipoints:
            points = []
            for point in object.points:
                new_point = (point - pos) @ rotation_matrix
                points.append(new_point)
        else:
            points = []

            new_point1 = (object.p1 - pos) @ rotation_matrix
            points.append(new_point1)

            if has_p2:
                new_point2 = (object.p2 - pos) @ rotation_matrix
                points.append(new_point2)

            if has_p3:
                new_point3 = (object.p3 - pos) @ rotation_matrix
                points.append(new_point3)            

        # Backface culling

        backface_culling = getattr(object, 'backface_culling', False)
        if backface_culling and self._normal(*points) <= 0: return

        # Clip

        for normal, distance in clipping_planes:
            # Point-to-Plane distance
            p2pd = list(
                np.dot(normal, point) + distance
                for point in points
            )

            if all(d <= 0 for d in p2pd):
                return

            elif any(d <= 0 for d in p2pd):
                # Line intersection
                if has_p2 and not has_p3:
                    intersect = self._intersect(points[0], points[1], normal, distance)
                    if intersect is not None:
                        if p2pd[0] <= 0: points[0] = intersect
                        elif p2pd[1] <= 0: points[1] = intersect

                # Triangle / polygon intersection
                elif has_p3 or has_multipoints:
                    new_points = []

                    for i1 in range(len(points)):
                        i2 = i1 + 1 if i1 + 1 < len(points) else 0

                        intersect = self._intersect(points[i1], points[i2], normal, distance)
                        if intersect is not None:
                            if p2pd[i1] <= 0:
                                new_points.append(intersect)
                            elif p2pd[i2] <= 0:
                                new_points.append(points[i1])
                                new_points.append(intersect)
                        elif p2pd[i1] >= 0:
                            new_points.append(points[i1])

                    points = copy(new_points)

        # Project

        for i, point in enumerate(points):
            z = max(point[2], d)
            x = (point[0] * d) / z * scale
            y = (point[1] * d) / z * scale

            points[i] = (x, -y, z)

        if len(points) > 3:
            new_obj = Polygon3D(
                points = points,
                color = object.color
            )
        else:
            new_obj = copy(object)
            new_obj.p1 = Coord(*points[0])
            if has_p2: new_obj.p2 = Coord(*points[1])
            if has_p3: new_obj.p3 = Coord(*points[2])

            new_obj._modified = True

        # Drawing and finalising

        temp_xOff, temp_yOff = canvas._x_off, canvas._y_off
        canvas.translate(width_center, height_center)
        canvas.draw(new_obj)
        canvas.translate(temp_xOff, temp_yOff)

    def fov(self, hFOV: int = 90, vFOV: int = 90) -> None:
        self._get_clipping_planes(
            hFOV = clamp(hFOV, 1, 179),
            vFOV = clamp(vFOV, 1, 179)
        )

    # Other methods

    def _get_rotation_matrix(self) -> None:
        ax, ay, az = self.angle

        sx, sy, sz = sin(ax), sin(ay), sin(az)
        cx, cy, cz = cos(ax), cos(ay), cos(az)

        self._rotation_matrix = np.array([
            [ cy*cz, cx*sz + sx*sy*cz, sx*sz - cx*sy*cz],
            [-cy*sz, cx*cz - sx*sy*sz, sx*cz - cx*sy*sz],
            [ sy   ,-sx*cy           , cx*cy           ]
        ])

        self._prev_angle = np.array([ax, ay, az])

    def _get_clipping_planes(self, hFOV: int = 90, vFOV: int = 90) -> None:
        hFOV_half, vFOV_half = hFOV / 2, vFOV / 2

        hFOV_r = hFOV_half * pi / 180
        vFOV_r = vFOV_half * pi / 180

        hx, hz = cos(hFOV_r), sin(hFOV_r)
        vy, vz = cos(vFOV_r), sin(vFOV_r)

        d = self.viewport_distance

        nearPlane   = np.array([0.0, 0.0, 1.0])
        leftPlane   = np.array([ hx, 0.0, hz])
        rightPlane  = np.array([-hx, 0.0, hz])
        bottomPlane = np.array([0.0,  vy, vz])
        topPlane    = np.array([0.0, -vy, vz])

        self.clipping_normals = (nearPlane, leftPlane, rightPlane, bottomPlane, topPlane)
        self.clipping_distances = (-d, 0.0, 0.0, 0.0, 0.0)

        self.scale_mult = tan(vFOV_r) / tan(hFOV_r)

    def _intersect(self, p1, p2, normal, distance):
        num = - (distance + np.dot(normal, p1))
        denom = np.dot(normal, p2 - p1)

        if denom == 0: return None

        t = num / denom

        if 0 < t < 1:
            return p1 + t * (p2 - p1)
        else:
            return None

    def _normal(self, p1, p2, p3) -> float:
        n = np.cross(p2 - p1, p3 - p1)

        return np.dot(p1, n)

    def __copy__(self):
        return Camera(
            width = self.width, height = self.height,
            x = self.position[0], y = self.position[1], z = self.position[2],
            ax = self.angle[0], ay = self.angle[1], az = self.angle[2],
            viewport_distance = self.viewport_distance
        )