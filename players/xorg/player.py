import time
import math
import random
from Xlib import X, display, threaded
from enum import Enum

from engine.maths.vector import Vector
from engine.maths.matrix import Matrix
from engine.maths.matrix import RotationMatrix

from engine.objects.generics.movable import Movable
from engine.objects.sprites.tank import TankSprite, TankState
from engine.objects.sprites.projectile import ProjectileSprite, ProjectileState
from engine.objects.sprites.explosion import ExplosionSprite, ExplosionState
from engine.objects.sprites.field import FieldSprite, FieldState
from engine.objects.sprites.leaderboard import LeaderboardSprite, LeaderboardState

from server.clients.type_enum import ClientType

import logging
from config.event_loop_time import EVENT_LOOP_TIME

from server.packets import *

class PlayerState(Enum):
    JOINING   = 1
    PLAYING   = 2
    TANK_DIED = 3
    EXIT      = 4

class Player:
    def __init__(self, display, connection, tank_name):
        # Game init
        self.connection = connection
        self.state      = PlayerState.JOINING

        # X11 init
        self.display        = display
        self.tank_name      = tank_name

        self.field          = (100, 100)
 
        logging.info("Sent Initial JoinReq, Listening ...")
        self.connection.put( JoinReqPacket(ClientType.TANK) )

        packet = self.connection.blocking_get()

        if type(packet) != JoinAckPacket:
            raise Exception("Expected JoinAck, got {}".format(type(packet)))

        self.screen = self.display.screen()
        # TODO do some cool splash intro here
        self.window = self.screen.root.create_window(
            10, 10, self.field[0], self.field[1], 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.KeyReleaseMask,
            )
        self.gc = self.window.create_gc(
            foreground = self.screen.black_pixel,
            background = self.screen.white_pixel,
            )
 
        self.window.map()

    def autoRepeatDetection(self):
        events = []

        i = self.display.pending_events()
        while i > 0:
            e = self.display.next_event()
            i -= 1

            if i >= 1 and e.type == X.KeyRelease:
                f = self.display.next_event()
                i -= 1
                if f.type != X.KeyPress or e.detail != f.detail:
                    events.insert(0, e)
                    events.insert(0, f)
            else:
                events.insert(0, e)
        return events

    def loop(self):
        try:
            self._loop()
        finally:
            logging.info("Cleaning up")
            self.connection.close()
 
    def _loop(self):
        ROLLING_AVERAGE_SIZE = 5

        objects      = {}
        round_number = 0
        latency_map  = {}

        __run_start        = (time.monotonic_ns() / 1000000)
        __idle_total       = 0
        __round_number     = 0
        __update_intervals = [0] * ROLLING_AVERAGE_SIZE
        __update_timestamp = 0

        e = self.display.next_event()

        if e.type != X.Expose:
            logging.info("Need an expose event first.")

        # TODO implement sync interval, dont hog CPU
        while True:
            __t         = (time.monotonic_ns() / 1000000)
            deadline    = __t + EVENT_LOOP_TIME
            __run_total = __t - __run_start

            self.display.sync()

            if self.state is PlayerState.JOINING:
                logging.info("Sent JoinReq, Listening ...")
                self.connection.put( CreateTankPacket(self.tank_name) )

                if self.connection.poll():
                    packet = self.connection.get()

                    if type(packet) == TankAckPacket:
                        self.state    = PlayerState.PLAYING
                        self.tank_uid = packet.uid

            elif self.state is PlayerState.PLAYING:
                # Get the lates state packet
                packet = None

                try:
                    while True:
                        packet = self.connection.get()
                except BlockingIOError:
                    pass

                if packet is not None:
                    if type(packet) is StatePacket:
                        round_number = packet.round_nr
                        states_list  = packet.game_state
                        cmd_id_list  = packet.cmd_id_list

                        for c in cmd_id_list:
                            if c in latency_map.keys():
                                __t = (time.monotonic_ns() / 1000000)
                                logging.debug("Client received response to Input: {} at {}" .format(c, __t))
                                try:
                                    logging.info("Latency: " + str(__t - latency_map[c]))
                                except KeyError:
                                    logging.info("OOOPS: Latency > 100ms, deleted key before response came!")
                                del latency_map[c]

                        for state in states_list:
                            if state.uid in objects:
                                objects[state.uid].erase()
                                objects[state.uid].state.set_state(state)
                            else:
                                if   type(state) is TankState:
                                    objects[state.uid] = TankSprite(
                                        self.screen, self.window, self.gc, state)
                                elif type(state) is ProjectileState:
                                    objects[state.uid] = ProjectileSprite(
                                        self.screen, self.window, self.gc, state)
                                elif type(state) is ExplosionState:
                                    objects[state.uid] = ExplosionSprite(
                                        self.screen, self.window, self.gc, state)
                                elif type(state) is FieldState:
                                    if state.width != self.field[0] or state.height != self.field[1]:
                                        self.window.configure(width=state.width, height=state.height)
                                        self.field = (state.width, state.height)
                                        self.display.sync()

                                    objects[state.uid] = FieldSprite(
                                        self.screen, self.window, self.gc, state)
                                elif type(state) is LeaderboardState:
                                    objects[state.uid] = LeaderboardSprite(
                                        self.screen, self.window, self.gc, state)
                                else:
                                    raise NotImplementedError(f"{type(state)}")
                            objects[state.uid].draw()

                        # TODO not very performant
                        uid_list      = [s.uid for s in states_list]
                        orphaned_uids = []
                        # Clean orphaned objects
                        for uid in objects:
                            if uid not in uid_list:
                                objects[uid].erase()
                                orphaned_uids.append(uid)

                        for uid in orphaned_uids:
                            del objects[uid]

                    elif type(packet) is TankDiedPacket:
                        self.state = PlayerState.TANK_DIED

            elif self.state is PlayerState.TANK_DIED:
                logging.info("You died.")
                self.state = PlayerState.EXIT

            elif self.state is PlayerState.EXIT:
                logging.info("Disconnecting from the server")
                self.connection.put( LeavePacket(self.tank_uid) )
                return
            
            # Then X11 events
            for e in self.autoRepeatDetection():
                if e.type == X.Expose:
                    for o in objects.values():
                        o.draw()
                elif e.type == X.KeyPress or e.type == X.KeyRelease:
                    if e.detail == 9 or e.detail == 66: # ESC
                        self.state = PlayerState.EXIT
                    else:
                        try:
                            if e.type is X.KeyPress:
                                event = InputPacket.Event.PRESS
                            elif e.type is X.KeyRelease:
                                event = InputPacket.Event.RELEASE
                            else:
                                raise NotImplementedError

                            if e.detail == 111:
                                key = InputPacket.Key.UP
                            elif e.detail == 116:
                                key = InputPacket.Key.DOWN
                            elif e.detail == 113:
                                key = InputPacket.Key.LEFT
                            elif e.detail == 114:
                                key = InputPacket.Key.RIGHT
                            elif e.detail == 65:
                                key = InputPacket.Key.SPACE
                            elif e.detail == 66:
                                key = InputPacket.Key.ESC
                            else:
                                raise KeyError

                            cmd_id = hex(random.randint(0, 2**16))
                            t = (time.monotonic_ns() / 1000000)
                            latency_map[cmd_id] = t
                            packet = InputPacket(self.tank_uid, key, event, cmd_id, t)
                            self.connection.put( packet )
                            if packet.event == InputPacket.Event.PRESS:
                                logging.info("> " + str(packet.key.name))
                            if packet.event == InputPacket.Event.RELEASE:
                                logging.info("< " + str(packet.key.name))
                            logging.debug("Client sent Input: {} at {}".format(cmd_id, t))
                        except KeyError:
                            pass

            round_number += 1

            __idle_start = (time.monotonic_ns() / 1000000)

            if __idle_start > deadline:
                logging.info("Missed round " + str(__round_number) + " by: " +
                        str(__idle_start - deadline))

            # Ez debugging
            if (__round_number % 100) == 0:
                # Clean the latency_map of orphaned entries,
                #   remove after we haven't received a response for 100 ms.
                latency_map = {uid:timestamp for (uid, timestamp) in latency_map.items()
                        if timestamp > __t + 100}

            # Coarse grained waiting
            while ( deadline - (time.monotonic_ns() / 1000000) ) > (EVENT_LOOP_TIME / 5) :
                time.sleep( EVENT_LOOP_TIME / (5 * 1000) )

            # Fine grained waiting
            while time.monotonic_ns() / 1000000 < deadline:
                continue

            __idle_total   += (time.monotonic_ns() / 1000000) - __idle_start
            __round_number += 1
