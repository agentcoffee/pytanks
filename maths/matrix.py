import math

from maths.vector import Vector


class Matrix:
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def __add__(self, other):
        return Matrix(self.a + other.a,
                      self.b + other.b,
                      self.c + other.c,
                      self.d + other.d)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, Matrix):
            return Matrix(self.a * other.a + self.b * other.c,
                          self.a * other.b + self.b * other.d,
                          self.c * other.a + self.d * other.c,
                          self.c * other.b + self.d * other.d)
        elif isinstance(other, Vector):
            return Vector(self.a * other.x + self.b * other.y,
                          self.c * other.x + self.d * other.y)

    def __rmul__(self, other):
        return Matrix(self.a * other.a + self.b * other.c,
                      self.a * other.b + self.b * other.d,
                      self.c * other.a + self.d * other.c,
                      self.c * other.b + self.d * other.d)

class RotationMatrix(Matrix):
    def __init__(self, angle):
        self.a = math.cos(angle)
        self.b = -math.sin(angle)
        self.c = math.sin(angle)
        self.d = math.cos(angle)

