

class InputPacket:
    def __init__(self, key_input, tank_id):
        self.key_input  = key_input
        self.tank_id    = tank_id

class JoinReqPacket:
    def __init__(self):
        return

class JoinAckPacket:
    def __init__(self, tank_id):
        self.tank_id = tank_id
