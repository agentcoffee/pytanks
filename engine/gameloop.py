import time
import math
import random
import pickle

from server.packets import * 

from server.clients.state_enum import ClientState
from engine.objects.generics.collidable import Collidable

from engine.maths.vector import Vector
from engine.objects.sprites.tank import TankObject, TankState
from engine.objects.sprites.field import FieldObject, FieldState
from engine.objects.sprites.leaderboard import LeaderboardObject, LeaderboardState
from engine.objects.generics.movable import MovableState

from engine.unique_id import UniqueID

import logging
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

class GameLoop:
    def __init__(self, io_server):
        self.io_server      = io_server
        self.id_generator   = UniqueID()

    def loop(self):
        try:
            self.gameloop()
        except KeyboardInterrupt:
            logging.info("CTRL-C received")
        finally:
            logging.info("Cleanup")
            self.io_server.close()
 
    def gameloop(self):
        """
        @objects are all objects which want to be placed on the gamefield.
            Thats any tank, any projectile and also texts, for example.
        """
        clients  = []
        objects  = [ FieldObject(FieldState(400, 400, self.id_generator.get()), self.id_generator) ]
        objects += [ LeaderboardObject(LeaderboardState(self.id_generator.get()),
                                  self.id_generator) ]

        # dummy tank
#        objects += [ TankObject(
#                        tank_state = TankState(
#                            MovableState(
#                                position = Vector(
#                                    x = 200,
#                                    y = 200),
#                                angle = math.pi/2,
#                                speed = 0),
#                            health = 100,
#                            name = "Dummy",
#                            uid = self.id_generator.get()),
#                        id_generator = self.id_generator) ]

        # Diagnostic variables
        __round_number = 0
        __idle_total = 0
        __run_start  = (time.monotonic_ns() / 1000000)

        #self.collisions = CollisionEngine(self.field)

        cmd_id_list = []

        try:
            while True:
                __t         = (time.monotonic_ns() / 1000000)
                deadline    = __t + EVENT_LOOP_TIME
                __run_total = __t - __run_start

                # Blast the game state back
                object_states  = [ o.state.get_state() for c in clients for o in c.get_movables() ]
                object_states += [ o.state.get_state() for o in objects ]

                game_state = StatePacket(__round_number, object_states, cmd_id_list)
                for c in [ c for c in clients if c.state is ClientState.READY ]:
                    c.put(game_state)

                # Diagnostics
                if len(cmd_id_list) != 0:
                    logging.debug("Gameloop replied to Inputs: {} at {}".format(
                        cmd_id_list, (time.monotonic_ns() / 1000000)))

                cmd_id_list = []

                # Advance the client state machine. Add a Tank, process inputs, etc.
                for c in clients:
                    c.step(self.id_generator, cmd_id_list, objects)

                # Sort out dead clients
                clients = [ c for c in clients if c.state is not ClientState.DEAD ]
                # Get a list of movables
                movables = [ m for c in clients for m in c.get_movables() ]

                # Step all the movables connected to clients
                for m in movables:
                    m.step(objects, movables)

                # Step all the objects, the movables might have appended some
                for o in objects:
                    o.step(objects, movables)

                # check if somebody wants to join
                new_clients = self.io_server.step()
                clients    += new_clients

                # Ez debugging
                if (__round_number % 100) == 0:
                    logging.info("[ idle %: " +
                            str(100 * __idle_total / __run_total) + " round: " +
                            str(__round_number) + " ]")

                __idle_start = (time.monotonic_ns() / 1000000)

                if __idle_start > deadline:
                    logging.info("Missed round " + str(__round_number) + " by: " +
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
