
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

    def __contains__(self, x):
        if self.inverted:
            return not ( self.a < x < self.b )
        else:
            return ( self.a <= x <= self.b)

    def overlaps(self, other):
        if isinstance(other, Interval):
            if not self.inverted and not other.inverted:
                # [a b] and [x y]
                if self.b < other.a or self.a > other.b:
                    return False
            elif not self.inverted and other.inverted:
                # [a b] and x] [y
                if other.a < self.a and self.b < other.b:
                    return False
            elif self.inverted and not other.inverted:
                # a] [b and [x y]
                if self.a < other.a and other.b < self.b:
                    return False
            else: # self.inverted and other.inverted:
                # a] [b and x] [y
                pass

            return True
        else:
            raise NotImplementedError(f"Cannot overlap Interval and {other}")
