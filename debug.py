DEBUG_LATENCY=False
DEBUG_INPUT=False

def latency(msg):
    if DEBUG_LATENCY:
        print(msg)

def input(msg):
    if DEBUG_INPUT:
        print(msg)
