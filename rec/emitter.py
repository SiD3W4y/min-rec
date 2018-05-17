import io

class Emitter:

    def __init__(self):
        self.stream = io.StringIO()

    def emitLabel(self, label):
        self.stream.write("fn {}\n".format(label))

    def emitRaw(self, raw):
        self.stream.write("{}\n".format(raw))

    def emitSlot(self, name, size):
        self.stream.write("slot {} {}\n".format(name, size))

    def emitString(self, name, string):
        self.stream.write("string {} \"{}\"\n".format(name, string))

    @property
    def value(self):
        return self.stream.getvalue()
