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
            viewportDistance: float = 1.0,
    ) -> None:

        self.position = np.array([x, y, z])
        self.angle = np.array([ax, ay, az])

        self.viewportDistance = viewportDistance

        self._getClippingPlanes(hFOV = 90)

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
        
        #vWidth, vHeight = self.viewportWidth, self.viewportHeight
        scale = max(width, height)

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

        # Backface culling

        backfaceCulling = getattr(object, 'backfaceCulling', False)
        if backfaceCulling and self._normal(*points) <= 0: return

        # Clip

        for normal, distance in zip(clippingNormals, clippingDistances):
            # Point-to-Plane distance
            p2pd = list(
                np.dot(normal, point) + distance
                for point in points
            )

            if all(d <= 0 for d in p2pd):
                return

            elif any(d <= 0 for d in p2pd):
                # Line intersection
                if has_2p and not has_3p:
                    intersect = self._intersect(points[0], points[1], normal, distance)
                    if intersect is not None:
                        if p2pd[0] <= 0: points[0] = intersect
                        elif p2pd[1] <= 0: points[1] = intersect

                # Triangle / polygon intersection
                if has_3p:
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
                        elif p2pd[i1] > 0 and p2pd[i2] > 0:
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
            if has_2p: new_obj.p2 = Coord(*points[1])
            if has_3p: new_obj.p3 = Coord(*points[2])

            new_obj._modified = True

        # Drawing and finalising

        temp_xOff, temp_yOff = canvas._xOff, canvas._yOff
        canvas.translate(wCenter, hCenter)
        canvas.draw(new_obj)
        canvas.translate(temp_xOff, temp_yOff)

    # Other methods

    def _getClippingPlanes(self, hFOV = 90, vFOV = 90) -> None:
        hFOV_half, vFOV_half = hFOV / 2, vFOV / 2

        hFOV_r = hFOV_half / 180 * pi
        vFOV_r = vFOV_half / 180 * pi

        hx, hz = sin(hFOV_r), cos(hFOV_r)
        vy, vz = sin(vFOV_r), cos(vFOV_r)

        d = self.viewportDistance

        nearPlane   = np.array([0.0, 0.0, 1.0])
        leftPlane   = np.array([ hx, 0.0, hz])
        rightPlane  = np.array([-hx, 0.0, hz])
        bottomPlane = np.array([0.0,  vy, vz])
        topPlane    = np.array([0.0, -vy, vz])

        self.clippingNormals = (nearPlane, leftPlane, rightPlane, bottomPlane, topPlane)
        self.clippingDistances = (-d, 0.0, 0.0, 0.0, 0.0)

        self.viewportWidth = d * tan(hFOV_half) * 2
        self.viewportHeight = d * tan(vFOV_half) * 2

    def _intersect(self, p1, p2, normal, distance):
        num = - (distance + np.dot(normal, p1))
        denom = np.dot(normal, p2 - p1)

        if denom == 0: return None

        t = num / denom

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