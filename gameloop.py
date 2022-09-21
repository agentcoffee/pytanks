import time
import math
import random
import pickle

from packets import * 

from clients.state_enum import ClientState
from sprites.collidable import Collidable

from maths.vector import Vector
from sprites.tank import TankObject, TankState

from unique_id import UniqueID

import debug
from config.event_loop_time import EVENT_LOOP_TIME


class CollisionEngine:
    def __init__(self, field):
        self.field = field

    def get_collisions(self, objects):
        collisions = []
        for i in range(0, len(objects)):
            for j in range(i+1, len(objects)):
                if objects[i].collides(objects[j]):
                    collisions.append((objects[i], objects[j]))
                # end if
            # end for
        # end for
        return collisions

    def split_x(self, objects, inf, sup):
        if objects is []:
            return []
        # end if

        if len(objects) < 5:
            return self.get_collisions(objects)
        # end if

        left_half  = []
        right_half = []
        neither    = []

        middle     = (inf + (sup - inf + 1) / 2)

        for o in objects:
            if o.getPosition().x + o.getHitboxRadius() < middle:
                left_half.append(o)
            elif o.getPosition().x - o.getHitboxRadius() >= middle:
                right_half.append(o)
            else:
                neither.append(o)
            # end if
        # end for

        collisions_left    = self.split_x(left_half,  inf, middle-1)
        collisions_right   = self.split_x(right_half, middle, sup)
        collisions_neither = self.get_collisions(neither)
        # TODO split_y for neither?

        for o in neither:
            for p in left_half:
                if o.collides(p):
                    collisions_left.append((o, p))
                # end if
            # end for
            for p in right_half:
                if o.collides(p):
                    collisions_left.append((o, p))
                # end if
            # end for
        # end for

        return collisions_left + collisions_right + collisions_neither

    def run(self, objects):
        return self.split_x(objects, self.field.x_inf, self.field.x_sup)

# The Field class is interpreted as:
#
#       x_inf   x_sup
#  y_inf  0------>
#         |
#         |
#  y_sup  v
#

class Field(Collidable):
    def __init__(self, width, height):
        self.x_inf  = 1
        self.x_sup  = width
        self.y_inf  = 1
        self.y_sup  = height
        self.width  = width
        self.height = height
        self.collisionbox = (Interval(self.x_inf, self.x_sup,
                                      inverted = True),
                             Interval(self.y_inf, self.y_sup,
                                      inverted = True))

    def get_collisionbox(self):
        return self.collisionbox

    def get_hitboxradius(self):
        raise NotImplementedError("The field has no hitbox.")

    def get_position(self):
        raise NotImplementedError("The field has no position.")

class GameLoop:
    def __init__(self, io_server, field):
        self.io_server      = io_server
        self.field          = field
        self.id_generator   = UniqueID()

    def loop(self):
        try:
            self.gameloop()
        except KeyboardInterrupt:
            print("CTRL-C received")
        finally:
            print("Cleanup")
            self.io_server.close()
 
    def gameloop(self):
        """
        @objects are all objects which want to be placed on the gamefield.
            Thats any tank, any projectile and also texts, for example.
        """
        clients = []
        objects = []

        # dummy tank
#        objects += [ TankObject(
#                        field = self.field,
#                        tank_state = TankState(
#                            position = Vector(
#                                x = self.field.x_inf +
#                                    random.random() * (self.field.x_sup - self.field.x_inf + 1),
#                                y = self.field.y_inf +
#                                    random.random() * (self.field.y_sup - self.field.y_inf + 1)),
#                            angle = math.pi/2,
#                            speed = 0,
#                            health = 100,
#                            name = "Dummy1",
#                            uid = self.id_generator.get()),
#                        id_generator = self.id_generator) ]

        # Diagnostic variables
        __round_number = 0
        __idle_total = 0
        __run_start  = (time.monotonic_ns() / 1000000)

        self.collisions = CollisionEngine(self.field)

        cmd_id_list = []

        try:
            while True:
                __t         = (time.monotonic_ns() / 1000000)
                deadline    = __t + EVENT_LOOP_TIME
                __run_total = __t - __run_start

                # Blast the game state back
                object_states = []
                for c in clients:
                    object_states += [ o.getState() for o in c.get_movables() ]

                object_states += [ o.getState() for o in objects ]

                game_state = StatePacket(__round_number, object_states, cmd_id_list)
                for c in [ c for c in clients if c.state is ClientState.READY ]:
                    c.put(game_state)

                # Diagnostics
                if len(cmd_id_list) != 0:
                    debug.latency("Gameloop replied to Inputs: {} at {}".format(
                        cmd_id_list, (time.monotonic_ns() / 1000000)))

                cmd_id_list = []

                # Advance the client state machine. Add a Tank, process inputs, etc.
                for c in clients:
                    c.step(self.field, self.id_generator, cmd_id_list)

                # Sort out dead clients
                clients = [ c for c in clients if c.state is not ClientState.DEAD ]

                # Step all the movables connected to clients
                for c in clients:
                    for m in c.get_movables():
                        m.step(objects)

                # Step all the objects, the movables might have appended some
                for o in objects:
                    o.step(objects)

                # Collision detection and notify involved objects
                # TODO: not very performant
                collidables  = [ o for o in objects if isinstance(o, Collidable) ]
                for c in clients:
                    for m in c.get_movables():
                        collidables += [ m ]

                for c in self.collisions.run(collidables):
                    c[0].collision(c[1])
                    c[1].collision(c[0])

                # check if somebody wants to join
                new_clients = self.io_server.step(self.field)
                clients    += new_clients

                # Ez debugging
                if (__round_number % 100) == 0:
                    print("[ idle %: " +
                            str(100 * __idle_total / __run_total) + " round: " +
                            str(__round_number) + " ]")

                __idle_start = (time.monotonic_ns() / 1000000)

                if __idle_start > deadline:
                    print("Missed round " + str(__round_number) + " by: " +
                            str(__idle_start - deadline))

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
        finally:
            for c in clients:
                c.close()
