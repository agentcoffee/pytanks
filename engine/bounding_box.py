from engine.maths.interval import Interval
from engine.maths.vector import Vector

# If only a is given, then b = c = d = a is set.
# 
#    ---------------
#    |      ^      |
#    |      c      |
#    |      v      |
#    |             |
#    | <a>  P  <b> |
#    |             |
#    |      ^      |
#    |      d      |
#    |      v      |
#    ---------------

class BoundingBox:
    def __init__(self, x1, x2, b=None, c=None, d=None,
            x_inverted=False, y_inverted=False):

        if isinstance(x1, Interval) and isinstance(x2, Interval):
            self.xrange = x1
            self.yrange = x2
        else:
            assert isinstance(x1, Vector) and isinstance(x2, int)
            if b is None:
                b = x2
            if c is None:
                c = x2
            if d is None:
                d = x2

            self.xrange = Interval(x1.x - x2, x1.x + b, x_inverted)
            self.yrange = Interval(x1.y - c, x1.y + d, y_inverted)

    def overlaps(self, other):
        return self.xrange.overlaps(other.xrange) or self.yrange.overlaps(other.yrange)

    def x_overlaps(self, other):
        return self.xrange.overlaps(other.xrange)

    def y_overlaps(self, other):
        return self.yrange.overlaps(other.yrange)

    def __contains__(self, v):
        if isinstance(v, Vector):
            return ( v.x in self.xrange and v.y in self.yrange )

    def __str__(self):
        return f"BoundingBox x {self.xrange} y {self.yrange}"
