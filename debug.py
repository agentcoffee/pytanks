DEBUG_LATENCY=True
DEBUG_INPUT=False

def latency(msg):
    if DEBUG_LATENCY:
        print(msg)

def input(msg):
    if DEBUG_INPUT:
        print(msg)
