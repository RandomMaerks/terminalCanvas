from math import sin, cos, pi, sqrt
from copy import copy
import numpy as np

from .Coord import Coord
from .helper import *

class Camera:
    def __init__(
            self,
            x: float = 0.0, y: float = 0.0, z: float = 0.0,
            ax: float = 0.0, ay: float = 0.0, az: float = 0.0,
            viewportDistance: float = 1.0,
    ) -> None:

        self.position = np.array([x, y, z])
        self.angle = np.array([ax, ay, az])

        self.viewportDistance = viewportDistance

        sqrt2rec = 1 / sqrt(2)

        nearPlane   = np.array([0.0      , 0.0      , 1.0     ])
        leftPlane   = np.array([sqrt2rec , 0.0      , sqrt2rec])
        rightPlane  = np.array([-sqrt2rec, 0.0      , sqrt2rec])
        bottomPlane = np.array([0.0      , sqrt2rec , sqrt2rec])
        topPlane    = np.array([0.0      , -sqrt2rec, sqrt2rec])

        self.clippingNormals = (nearPlane, leftPlane, rightPlane, bottomPlane, topPlane)
        self.clippingDistances = (-self.viewportDistance, 0.0, 0.0, 0.0, 0.0)

    # Camera transformation

    def move(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.position += np.array([x, y, z])

    def rotate(self, ax: float = 0.0, ay: float = 0.0, az: float = 0.0) -> None:
        self.angle += np.array([ax, ay, az])

    def detectInput(
            self,
            canvas: TCanvas,
            movementSpeed: float = 0.1,
            rotationSpeed: float = pi/120,
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
        
        if canvas.keyPressed(keymap["forward"]):
            self.position += forward * movementSpeed
        if canvas.keyPressed(keymap["backward"]):
            self.position -= forward * movementSpeed

        if canvas.keyPressed(keymap["left"]):
            self.position -= right * movementSpeed
        if canvas.keyPressed(keymap["right"]):
            self.position += right * movementSpeed

        if canvas.keyPressed(keymap["up"]):
            self.position[1] += movementSpeed
        if canvas.keyPressed(keymap["down"]):
            self.position[1] -= movementSpeed

        ax = ay = az = 0

        if canvas.keyPressed(keymap["lookup"]):
            ax = rotationSpeed
        if canvas.keyPressed(keymap["lookdown"]):
            ax = -rotationSpeed

        if canvas.keyPressed(keymap["turnleft"]):
            ay = rotationSpeed
        if canvas.keyPressed(keymap["turnright"]):
            ay = -rotationSpeed

        if canvas.keyPressed(keymap["counterclockwise"]):
            az = rotationSpeed
        if canvas.keyPressed(keymap["clockwise"]):
            az = -rotationSpeed

        self.rotate(ax, ay, az)

    # Object translation and projection

    def _draw(self, object: BaseObject, canvas: TCanvas) -> None:
        width, height = canvas.width, canvas.height
        wCenter, hCenter = canvas.wCenter, canvas.hCenter

        hR, vR = (width, height) if width >= height else (height, width)

        pos = self.position
        ax, ay, az = self.angle

        d = self.viewportDistance
        clippingNormals = self.clippingNormals
        clippingDistances = self.clippingDistances        

        if object.p1.dim() == 2:
            raise TypeError(f"{type(object)} is not a 3D object, thus cannot be used with Camera.")

        sin_ax, sin_ay, sin_az = sin(ax), sin(ay), sin(az)
        cos_ax, cos_ay, cos_az = cos(ax), cos(ay), cos(az)

        rotMatrix = np.array([
            [cos_ay * cos_az                           ,-cos_ay * sin_az                           , sin_ay         ],
            [cos_ax * sin_az + sin_ax * sin_ay * cos_az, cos_ax * cos_az - sin_ax * sin_ay * sin_az,-sin_ax * cos_ay],
            [sin_ax * sin_az - cos_ax * sin_ay * cos_az, sin_ax * cos_az - cos_ax * sin_ay * sin_az, cos_ax * cos_ay]
        ])

        has_2p = hasattr(object, "p2")
        has_3p = hasattr(object, "p3")

        # Translate

        points = []

        new_point1 = (object.p1 - pos) @ rotMatrix.T
        points.append(new_point1)

        if has_2p:
            new_point2 = (object.p2 - pos) @ rotMatrix.T
            points.append(new_point2)

        if has_3p:
            new_point3 = (object.p3 - pos) @ rotMatrix.T
            points.append(new_point3)

        # Clip

        for normal, distance in zip(clippingNormals, clippingDistances):
            # Point-to-Plane distance
            p2pd = tuple(
                np.dot(normal, point) + distance
                for point in points
            )

            if all(d <= 0 for d in p2pd):
                return
            elif any(d <= 0 for d in p2pd):
                if has_2p: point_count = 2
                elif has_3p: point_count = 3
                else: continue
                
                for i1 in range(point_count):
                    i2 = i1 + 1 if i1 + 1 < point_count else 0

                    intersect = self._intersect(points[i1], points[i2], normal, distance)
                    if intersect is not None:
                        if p2pd[i1] <= 0: points[i1] = intersect
                        elif p2pd[i2] <= 0: points[i2] = intersect


        # Backface culling

        if has_3p and object.backfaceCulling and self._normal(*points) <= 0: return
        
        # Project

        for i, point in enumerate(points):
            z = max(point[2], d)
            x = (point[0] * d) / z * hR
            y = (point[1] * d) / z * vR

            points[i] = Coord(x, -y, z)

        new_obj = copy(object)
        new_obj.p1 = points[0]
        if has_2p: new_obj.p2 = points[1]
        if has_3p: new_obj.p3 = points[2]

        # Drawing and finalising

        new_obj._modified = True

        temp_xOff, temp_yOff = canvas._xOff, canvas._yOff
        canvas.translate(wCenter, hCenter)
        canvas.draw(new_obj)
        canvas.translate(temp_xOff, temp_yOff)

    # Other methods

    def _intersect(self, p1, p2, normal, distance):
        if Coord(*p1) == Coord(*p2):
            return None

        t = - (distance + np.dot(normal, p1)) / np.dot(normal, p2 - p1)

        if 0 <= t <= 1:
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
            viewportDistance = self.viewportDistance
        )