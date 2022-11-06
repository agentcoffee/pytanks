DEBUG_LATENCY = False
DEBUG_INPUT   = True
DEBUG_OBJECTS = False

def latency(msg):
    if DEBUG_LATENCY:
        logging.info(msg)

def input(msg):
    if DEBUG_INPUT:
        logging.info(msg)

def objects(msg):
    if DEBUG_OBJECTS:
        logging.info(msg)
