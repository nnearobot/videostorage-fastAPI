## pagination params - can be used in any modules for pagination purposes

class Paginator:
    def __init__(self, limit: int = 0, skip: int = 0):
        self.limit = limit
        self.skip = skip

