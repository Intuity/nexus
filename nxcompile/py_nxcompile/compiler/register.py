class Register:

    def __init__(self, index, width=8):
        self.index    = index
        self.elements = [None] * width
        self.age      = 0
        self.active   = False
        self.novel    = False

    def __getitem__(self, key):
        return self.elements[key]

    def __setitem__(self, key, val):
        self.elements[key]

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def aging(self):
        self.age = (self.age + 1) if self.active else 0

    def __iter__(self):
        return self.elements
