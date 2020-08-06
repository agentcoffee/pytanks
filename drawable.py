from vector import Vector
from interval import Interval


class Drawable:
    def __init__(self, x, y, screen, window, gc):
        self.image = [Vector(2, 2), Vector(-2, -2), Vector(2, -2), Vector(-2, 2)]

        self.screen         = screen
        self.window         = window
        self.gc             = gc

        self.colormap       = self.screen.default_colormap
        self.red            = self.colormap.alloc_named_color("red").pixel
        self.green          = self.colormap.alloc_named_color("green").pixel
        self.white          = self.screen.white_pixel
        self.black          = self.screen.black_pixel

        self.position       = Vector(x, y)

        self.hitbox_radius  = 1

    def draw(self):
        self.gc.change(foreground = self.white)
        self.window.poly_line(self.gc, X.CoordModeOrigin,
                [(int(dot.x), int(dot.y)) for dot in self.image])
        
    def collisionBox(self):
        return (Interval(self.position.x - self.hitbox_radius,
                         self.position.x + self.hitbox_radius),
                Interval(self.position.y - self.hitbox_radius,
                         self.position.y + self.hitbox_radius))

    def collides(self, other):
        box      = self.collisionBox()
        otherBox = other.collisionBox()

        if box[0].overlaps(otherBox[0]) and box[1].overlaps(otherBox[1]):
            return True

    def collision(self, other, sprites):
        print("Movable:" + str(self) + " collides with " + str(other))
