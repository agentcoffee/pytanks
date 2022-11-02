from math import sqrt

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        raise NotImplementedError(f"Adding Vector and {type(other)}")

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        raise NotImplementedError(f"Subtracting Vector and {type(other)}")

    def __rsub__(self, other):
        if isinstance(other, Vector):
            return Vector(other.x - self.x, other.y - self.y)
        raise NotImplementedError(f"Subtracting Vector and {type(other)}")

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            # Vector * Scalar : vector scaling
            return Vector(self.x * other, self.y * other)
        if isinstance(other, Vector):
            # Vector * Vector : dot product
            return (self.x * other.x + self.y * other.y)
        raise NotImplementedError(f"Multiplying Vector and {type(other)}")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __eq__(self, other):
        return (self.x == other.x and self.y == other.y)

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    # Note: this is intentionally NOT __len__, because it can return floats and
    # len() does not like that.
    def length(self):
        return sqrt(self.x*self.x + self.y*self.y)

    def round(self):
        return Vector(int(self.x), int(self.y))

    def normalize(self):
        l = self.length()
        return Vector(self.x/l, self.y/l)
