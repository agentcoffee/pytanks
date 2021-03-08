import time
import math
import random
import pickle

from Xlib import X, display, threaded

from packets import * 

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.collidable import Collidable
from sprites.movable import Movable
from sprites.tank import TankObject, TankState
from sprites.projectile import ProjectileObject
from unique_id import UniqueID

import debug
from event_loop_time import EVENT_LOOP_TIME


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
    def __init__(self, io_server, field):
        self.io_server      = io_server
        self.field          = field
        self.id_generator   = UniqueID()

    def loop(self):
        try:
            self.gameloop()
        finally:
            print("Cleanup")
            self.io_server.close()
 
    def gameloop(self):
        idle_clients = []
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
            game_state = StatePacket(__round_number, [o.getState() for o in objects], cmd_id_list)
            for client in self.io_server:
                client.put(pickle.dumps(game_state))

            if len(cmd_id_list) != 0:
                debug.latency("Gameloop replied to Inputs: {} at {}".format(
                    cmd_id_list, (time.monotonic_ns() / 1000000)))

            cmd_id_list = []

            # First the game inputs
            for m in movables:
                try:
                    while m.input_pipe.poll():
                        k = pickle.loads(m.input_pipe.get())
                        if type(k) is InputPacket:
                            print("df")
                            cmd_id_list.append(k.cmd_id)
                            debug.latency("Gameloop handled Input: {} at {}".format(
                                k.cmd_id, (time.monotonic_ns() / 1000000)))
                            m.handler(k)
                            if k.event == InputPacket.Event.PRESS:
                                debug.input("> " + str(k.key.name))
                            # end if
                            if k.event == InputPacket.Event.RELEASE:
                                debug.input("< " + str(k.key.name))
                            # end if
                        # end if
                    # end while
                except EOFError:
                    movables.remove(m)
                    objects.remove(m)
                # end try
            # end for

            # Step objects
            for o in objects:
                o.step(objects)
            # end for

            # Collision detection and notify involved objects
            # TODO: not very performant
            for c in self.collisions.getCollisions([o for o in objects if isinstance(o, Collidable)]):
                c[0].collision(c[1])
                c[1].collision(c[0])
            # end for

            # check if somebody wants to join
            try:
                client = self.io_server.accept()
                idle_clients.append(client)
            except BlockingIOError:
                pass
            # end try

            # Only allow 1 client per loop iteration:
            #   No particular reason for this, but removing while iterating is
            #   a hassle, and this makes it very easy. The restriction (1
            #   client per iteration) is very acceptable (and also saves us
            #   from DDOS attacks, at least here).
            if len(idle_clients) > 0:
                client = idle_clients[0]
                if client.poll():
                    packet = pickle.loads(client.get())
                    if type(packet) is JoinReqPacket:
                        tank = TankObject(
                                field = self.field,
                                input_pipe = client,
                                tank_state = TankState(
                                    position = Vector(
                                        x = random.random() * self.field.width,
                                        y = random.random() * self.field.height),
                                    angle = math.pi/2,
                                    speed = 0,
                                    health = 100,
                                    name = packet.tank_name,
                                    uid = self.id_generator.get()),
                                id_generator = self.id_generator)

                        movables.append(tank)
                        objects.append(tank)
                        client.put(pickle.dumps(JoinAckPacket(tank.uid, self.field)))
                        # Client answered, got a Tank, now remove him from the
                        # queue.
                        idle_clients = idle_clients[1:]
                    else:
                        raise Exception("Expected JoinReqPacket, got something else.")
                    # end if
                else:
                    # Round Robin: client did not answer, set him back in the
                    # queue (if there is one).
                    idle_clients = idle_clients[1:].append(client)
                # end if
            # end if

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
