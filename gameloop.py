import time
import math
import random

from Xlib import X, display, threaded

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.collidable import Collidable
from sprites.movable import Movable
from sprites.tank import TankObject, TankState
from sprites.projectile import ProjectileObject

import debug
from event_loop_time import EVENT_LOOP_TIME

from commands import *


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

class GameLoop:
    def __init__(self, io_pipe, window_pipe, field):
        self.io_pipe        = io_pipe
        self.window_pipe    = window_pipe
        self.field          = field
 
    def loop(self):
        objects      = []
        movables     = []
        __round_number = 0
        __idle_total = 0
        __run_start  = (time.monotonic_ns() / 1000000)

        self.collisions = CollisionEngine(self.field)

        cmd_id_list = []

        while True:
            __t         = (time.monotonic_ns() / 1000000)
            deadline    = __t + EVENT_LOOP_TIME
            __run_total = __t - __run_start

            # Blast the game state back
            game_state = GameState(__round_number, [o.getState() for o in objects], cmd_id_list)
            self.window_pipe.send(game_state)
            if len(cmd_id_list) != 0:
                debug.latency("Gameloop replied to Inputs: {} at {}".format(
                    cmd_id_list, (time.monotonic_ns() / 1000000)))

            cmd_id_list = []

            # First the game inputs
            for m in movables:
                try:
                    while m.input_pipe.poll():
                        k = m.input_pipe.recv()
                        cmd_id_list.append(k.cmd_id)
                        debug.latency("Gameloop handled Input: {} at {}".format(
                            k.cmd_id, (time.monotonic_ns() / 1000000)))
                        m.handler(k)
                        if k.event == Input.Event.PRESS:
                            print("> " + str(k.key.name))
                        if k.event == Input.Event.RELEASE:
                            print("< " + str(k.key.name))
                    # end while
                except EOFError:
                    movables.remove(m)
                    objects.remove(m)
            # end for

            # Step objects
            for o in objects:
                #o.erase()
                o.step(objects)
                #o.draw()
            # end for

            # Collision detection and notify involved objects
            # TODO: not very performant
            for c in self.collisions.getCollisions([o for o in objects if isinstance(o, Collidable)]):
                c[0].collision(c[1])
                c[1].collision(c[0])
            # end for

            # Add new tanks
            while self.io_pipe.poll():
                cmd = self.io_pipe.recv()
                if type(cmd) is NewTank:
                    tank = TankObject(
                            field = self.field,
                            input_pipe = cmd.pipe,
                            tank_state = TankState(
                                position = Vector(
                                    x = random.random() * self.field.width,
                                    y = random.random() * self.field.width),
                                angle = math.pi/2,
                                speed = 0,
                                health = 100,
                                name = cmd.name,
                                uid = cmd.uid))

                    movables.append(tank)
                    objects.append(tank)
                # end if
            # end while

            # Ez debugging
            if (__round_number % 1000) == 0:
                print("Game State : " + str(game_state.game_state))
                print("[ idle %: " +
                        str(100 * __idle_total / __run_total) + " round: " +
                        str(__round_number) + " ]")

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
            __round_number += 1
        # end while
