import socket

class Telegram:
    def __init__(self, connection):
        assert(type(connection) is socket.socket)
        self.connection    = connection
        self.stream_buffer = bytearray()

        self.connection.setblocking(False)

    def _fetch_from_socket(self, size):
        try:
            self.stream_buffer += self.connection.recv(size)
        except BlockingIOError:
            pass

    def _get_next_telegram(self):
        if len(self.stream_buffer) > 0:
            length_lo = self.stream_buffer[0]
            length_hi = self.stream_buffer[1]
            length = (length_hi << 8) | (length_lo)

            if length <= (len(self.stream_buffer)-2):
                tmp = self.stream_buffer[2 : (length+2)]
                self.stream_buffer = self.stream_buffer[(length+2) :]
                return tmp

        raise BlockingIOError

    def poll(self):
        self._fetch_from_socket(4096)

        if len(self.stream_buffer) > 0:
            length_lo = self.stream_buffer[0]
            length_hi = self.stream_buffer[1]
            length = (length_hi << 8) | (length_lo)

            if length <= (len(self.stream_buffer)-2):
                return True
            # end if
        # end if

        return False

    def put(self, msg):
        length = len(msg)
        length_hi = length >> 8
        length_lo = length & 0xFF
        stream = bytearray([length_lo, length_hi]) + bytearray(msg)
        self.connection.sendall(stream)

    def get(self):
        self._fetch_from_socket(4096)
        return self._get_next_telegram()

    def get_latest(self):
        self._fetch_from_socket(4096)

        latest = None
        try:
            while True:
                latest = self._get_next_telegram()
        except BlockingIOError:
            pass

        if latest is None:
            raise BlockingIOError

        return latest

    def blocking_get(self):
        tmp = None
        while tmp is None:
            try:
                tmp = self.get()
            except BlockingIOError:
                pass
        return tmp

    def close(self):
        self.connection.close()
