from maths.vector import Vector
from maths.interval import Interval


class Drawable:
    def __init__(self, screen, window, gc):
        self.image = [Vector(2, 2), Vector(-2, -2), Vector(2, -2), Vector(-2, 2)]

        self.screen         = screen
        self.window         = window
        self.gc             = gc

        self.colormap       = self.screen.default_colormap
        self.red            = self.colormap.alloc_named_color("red").pixel
        self.green          = self.colormap.alloc_named_color("green").pixel
        self.white          = self.screen.white_pixel
        self.black          = self.screen.black_pixel

    def draw(self):
        raise NotImplementedError("You have to provide the draw method yourself.")

    def erase(self):
        raise NotImplementedError("You have to provide the erase method yourself.")
