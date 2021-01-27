import time
import math
import random
from Xlib import X, display, threaded

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.movable import Movable
from sprites.tank import Tank
from sprites.projectile import Projectile
from commands import Input


EVENT_LOOP_TIME = 5 #in ms


class CollisionEngine:
    def __init__(self, field):
        self.field = field

    def getCollisions(self, objects):
        collisions = []
        for i in range(0, len(objects)):
            for j in range(i+1, len(objects)):
                if objects[i].collides(objects[j]):
                    collisions.append((objects[i], objects[j]))
        return collisions

class Field:
    def __init__(self, width, height):
        self.width  = width
        self.height = height

class Window:
    def __init__(self, display, pipe):
        self.display    = display
        self.pipe       = pipe
 
        self.screen = self.display.screen()
        self.window = self.screen.root.create_window(
            10, 10, 100, 100, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.KeyReleaseMask,
            )
        self.gc = self.window.create_gc(
            foreground = self.screen.black_pixel,
            background = self.screen.white_pixel,
            )
 
        self.window.map()
 
    def loop(self):
        objects      = []
        movables     = []
        __idle_total = 0
        __run_start  = (time.monotonic_ns() / 1000000)

        e = self.display.next_event()

        if e.type == X.Expose:
            self.field = Field(e.width, e.height)
        else:
            print("Need an expose event first.")

        self.collisions = CollisionEngine(self.field)

        while True:
            deadline = (time.monotonic_ns() / 1000000) + EVENT_LOOP_TIME
            __run_total  = (time.monotonic_ns() / 1000000) - __run_start

            self.display.sync()

            # Draw objects and let them do stuff
            for o in objects:
                o.draw()
                o.action(objects)
            # end for

            # Collision detection and notify involved objects
            for c in self.collisions.getCollisions(objects):
                c[0].collision(c[1], objects)
                c[1].collision(c[0], objects)
            # end for

            # Add new tanks
            while self.pipe.poll():
                tank_pipe = self.pipe.recv()
                tank = Tank(self.field,
                        random.random() * self.field.width, random.random() * self.field.width,
                        self.screen, self.window, self.gc, tank_pipe)

                movables.append(tank)
                objects.append(tank)
            # end while

            # First the game inputs
            for m in movables:
                while m.input_pipe.poll():
                    k = m.input_pipe.recv()
                    m.handler(k)

                    if k.event == Input.Event.PRESS:
                        print("> " + str(k.key.name))
                    if k.event == Input.Event.RELEASE:
                        print("< " + str(k.key.name))
                        print("[ idle %: " + str(100 * __idle_total / __run_total) + " ]")
                # end while
            # end for

            # Then X11 events
            while self.display.pending_events() > 0:
                e = self.display.next_event()

                if e.type == X.Expose:
                    self.field.width = e.width
                    self.field.height = e.height
                    for o in objects:
                        o.draw()
                elif e.type == X.KeyPress:
                    if e.detail == 9 or e.detail == 66: # ESC
                        raise SystemExit
                # end if
            # end while

            __idle_start = (time.monotonic_ns() / 1000000)

            # Coarse grained waiting
            while ( deadline - (time.monotonic_ns() / 1000000) ) > (EVENT_LOOP_TIME / 5) :
                time.sleep( EVENT_LOOP_TIME / (5 * 1000) )
            # end while

            # Fine grained waiting
            while time.monotonic_ns() / 1000000 < deadline:
                continue
            # end while

            __idle_total += (time.monotonic_ns() / 1000000) - __idle_start
        # end while
