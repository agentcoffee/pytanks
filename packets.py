class InputPacket:
    def __init__(self, key_input, uid):
        self.key_input = key_input
        self.uid       = uid

class StatePacket:
    def __init__(self, state, uid):
        self.state = state
        self.uid = uid

class JoinReqPacket:
    def __init__(self, tank_name):
        self.tank_name = tank_name

class JoinAckPacket:
    def __init__(self, uid, field):
        self.uid = uid
        self.field = field
