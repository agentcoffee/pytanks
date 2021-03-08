class UniqueID:
    def __init__(self, start = 0):
        self.current_id = start

    def get(self):
        self.current_id += 1
        return self.current_id
