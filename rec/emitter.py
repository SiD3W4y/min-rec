import io

class Emitter:

    def __init__(self):
        self.stream = io.StringIO()

    def emitRaw(self, raw):
        self.stream.write("{}\n".format(raw))

    def emitLabel(self, label):
        self.emitRaw("fn {}".format(label))

    def emitSlot(self, name, size):
        self.emitRaw("slot {} {}".format(name, size))

    def emitString(self, name, string):
        self.emitRaw("string {} \"{}\"".format(name, string))
    
    def emitMovImm(self, reg, cst):
        self.emitRaw("mov {} {}".format(reg, hex(cst)))
    
    def emitMovRef(self, reg, refname):
        self.emitRaw("mov {} #{}".format(reg, refname))

    def emitStoreSlot(self, arg, stackidx):
        self.emitRaw("mov $F $BP")
        self.emitRaw("sub $F {}".format(4 + stackidx * 4))
        self.emitRaw("str {} $F".format(arg))

    def emitLoadSlot(self, dest, slot):
        self.emitRaw("mov $F $BP")
        self.emitRaw("sub $F {}".format(4 + slot * 4))
        self.emitRaw("ldr {} $F".format(dest)) 

    def emitPrologue(self, varcount):
        self.emitRaw("push $BP")
        self.emitRaw("mov $BP $SP")
        self.emitRaw("sub $SP {}".format(varcount * 4))

    def emitEpilogue(self):
        self.emitRaw("mov $SP $BP")
        self.emitRaw("pop $BP")
        self.emitRaw("ret\n")

    @property
    def value(self):
        return self.stream.getvalue()
