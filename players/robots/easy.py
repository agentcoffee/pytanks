import time
import math
import random
from enum import Enum

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.movable import Movable
from sprites.tank import TankState
from sprites.projectile import ProjectileSprite, ProjectileState
from sprites.explosion import ExplosionSprite, ExplosionState
from clients.type_enum import ClientType

import debug
from config.event_loop_time import EVENT_LOOP_TIME

from packets import *

class PlayerState(Enum):
    JOINING   = 1
    PLAYING   = 2
    TANK_DIED = 3
    EXIT      = 4

class EasyRobot:
    def __init__(self, connection, tank_name):
        # Game init
        self.connection = connection
        self.state      = PlayerState.JOINING
        self.tank_name  = tank_name
        self.target     = "esteban"
        self.input      = None
        self.move       = False
        self.shoot_timeout = 0
 
        print("Sent Initial JoinReq, Listening ...")
        self.connection.put( JoinReqPacket(ClientType.TANK) )

        packet = self.connection.blocking_get()

        if type(packet) == JoinAckPacket:
            self.field = packet.field
        else:
            raise Exception("Expected JoinAck, got {}".format(type(packet)))

    def loop(self):
        try:
            self._loop()
        finally:
            print("Cleaning up")
            self.connection.close()
 
    def _loop(self):
        ROLLING_AVERAGE_SIZE = 5

        objects      = {}
        round_number = 0

        __run_start        = (time.monotonic_ns() / 1000000)
        __idle_total       = 0
        __round_number     = 0

        # TODO implement sync interval, dont hog CPU
        while True:
            __t         = (time.monotonic_ns() / 1000000)
            deadline    = __t + EVENT_LOOP_TIME
            __run_total = __t - __run_start

            if self.state is PlayerState.JOINING:
                print("Sent JoinReq, Listening ...")
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

                        responses = self.robot_compute(states_list)

                        for m in responses:
                            self.connection.put(m)

                    elif type(packet) is TankDiedPacket:
                        self.state = PlayerState.TANK_DIED

            elif self.state is PlayerState.TANK_DIED:
                print("You died.")
                self.state = PlayerState.EXIT

            elif self.state is PlayerState.EXIT:
                print("Disconnecting from the server")
                self.connection.put( LeavePacket(self.tank_uid) )
                return

            round_number += 1

            __idle_start = (time.monotonic_ns() / 1000000)

            if __idle_start > deadline:
                print("Missed round " + str(__round_number) + " by: " +
                        str(__idle_start - deadline))

            # Coarse grained waiting
            while ( deadline - (time.monotonic_ns() / 1000000) ) > (EVENT_LOOP_TIME / 5) :
                time.sleep( EVENT_LOOP_TIME / (5 * 1000) )

            # Fine grained waiting
            while time.monotonic_ns() / 1000000 < deadline:
                continue

            __idle_total   += (time.monotonic_ns() / 1000000) - __idle_start
            __round_number += 1

    def robot_compute(self, states_list):
        commands = []

        for s in states_list:
            if type(s) is TankState and s.name == self.tank_name:
                me = s

            if type(s) is TankState and s.name == self.target:
                target = s

        try:
            shoot_line = target.position - me.position
            shoot_line_norm  = shoot_line.normalize()
            shoot_line_angle = math.asin(shoot_line_norm.y)

            if shoot_line.x < 0:
                if shoot_line.y > 0:
                    # 2. Quartal
                    shoot_line_angle = math.pi - shoot_line_angle
                else:
                    # 3. Quartal
                    shoot_line_angle = math.pi - shoot_line_angle
            else:
                if shoot_line.y > 0:
                    # 1. Quartal
                    pass
                else:
                    # 4. Quartal
                    shoot_line_angle = 2*math.pi + shoot_line_angle

            angle_diff = shoot_line_angle - me.angle

            if angle_diff > math.pi:
                angle_diff = -(2*math.pi - angle_diff)
            elif angle_diff < -math.pi:
                angle_diff =  (2*math.pi + angle_diff)

            if -0.1 < angle_diff < 0.1:
                if self.input is not None:
                    commands.append(InputPacket(self.tank_uid,
                        self.input, InputPacket.Event.RELEASE))

                if (time.time() - self.shoot_timeout) > 0.1:
                    self.shoot_timeout = time.time()
                    commands.append(InputPacket(self.tank_uid,
                        InputPacket.Key.SPACE, InputPacket.Event.PRESS))

                self.input = None
            elif angle_diff > 0:
                if self.input is not None:
                    commands.append(InputPacket(self.tank_uid,
                        self.input, InputPacket.Event.RELEASE))

                self.input = InputPacket.Key.RIGHT
                commands.append(InputPacket(self.tank_uid,
                    InputPacket.Key.RIGHT, InputPacket.Event.PRESS))
            else:
                if self.input is not None:
                    commands.append(InputPacket(self.tank_uid,
                        self.input, InputPacket.Event.RELEASE))

                self.input = InputPacket.Key.LEFT
                commands.append(InputPacket(self.tank_uid,
                    InputPacket.Key.LEFT, InputPacket.Event.PRESS))

            if self.move == False:
                commands.append(InputPacket(self.tank_uid,
                    InputPacket.Key.UP, InputPacket.Event.PRESS))
                self.move = True

#            if shoot_line.length() > 100:
#                commands.append(InputPacket(self.tank_uid,
#                    InputPacket.Key.UP, InputPacket.Event.PRESS))
#                self.move = True
#            elif self.move is True:
#                commands.append(InputPacket(self.tank_uid,
#                    InputPacket.Key.UP, InputPacket.Event.RELEASE))
#                self.move = False

        except UnboundLocalError:
            pass

        return commands
