DEBUG_LATENCY=False
DEBUG_INPUT  =False
DEBUG_OBJECTS=False

def latency(msg):
    if DEBUG_LATENCY:
        print(msg)

def input(msg):
    if DEBUG_INPUT:
        print(msg)

def objects(msg):
    if DEBUG_OBJECTS:
        print(msg)
