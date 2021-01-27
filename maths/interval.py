
class Interval:
    def __init__(self, a, b):
        assert(a <= b)
        self.a = a
        self.b = b

    def __str__(self):
        return "[" + str(self.a) + ", " + str(self.b) + "]"

    def overlaps(self, other):
        if isinstance(other, Interval):
            if self.b < other.a or self.a > other.b:
                return False
            else:
                return True
