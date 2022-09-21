
class Interval:
    def __init__(self, a, b, inverted=False):
        self.a = a
        self.b = b
        self.inverted = inverted

    def __str__(self):
        if self.inverted:
            return "[" + str(self.a) + " " + str(self.b) + "]"
        else:
            return "(R \ [" + str(self.a) + " " + str(self.b) + "])"

    def overlaps(self, other):
        if isinstance(other, Interval):
            if not self.inverted and not other.inverted:
                # [a b] and [x y]
                if self.b < other.a or self.a > other.b:
                    return False
            elif not self.inverted and other.inverted:
                # [a b] and x] [y
                if other.x < self.a and self.b < other.y:
                    return False
            elif self.inverted and not other.inverted:
                # a] [b and [x y]
                if self.a < other.x and other.y < self.b:
                    return False
            else: # self.inverted and other.inverted:
                # a] [b and x] [y
                pass

            return True
