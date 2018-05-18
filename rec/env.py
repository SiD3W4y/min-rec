
class ConstVal:
    Addr = 0
    Imm = 1
    Unk = 2

    def __init__(self, cst_type, cst_value, cst_index):
        self.cst_type = cst_type
        self.cst_value = cst_value
        self.cst_index = cst_index
    
    @property
    def type(self):
        return self.cst_type

    @property
    def value(self):
        return self.cst_value

    @property
    def index(self):
        return self.cst_index

class StackEvent:
    LOAD_FAST = 0
    LOAD_CONST = 1
    LOAD_GLOBAL = 2
    MAKE_FUNCTION_DUMMY = 3 # push a dummy return value on the stack

    def __init__(self, evt_type, evt_val, evt_idx):
        self.evt_type = evt_type
        self.evt_val = evt_val
        self.evt_idx = evt_idx

    @property
    def value(self):
        return self.evt_val

    @property
    def type(self):
        return self.evt_type

    @property
    def index(self):
        return self.evt_idx

class Env:
    def __init__(self, code):
        self.function_name = code.co_name
        self.consts = [] 
        self.locals = code.co_varnames 
        self.events = []
        self.loops = []
        self.loop_cnt = 0
        self.compare_stack = []
        
        # Builtin functions
        self.builtin_funcs = {
            "__slot__": lambda a: a,
            "__str__": lambda a: a
        }

        # Preparing constants
        cst = list(code.co_consts)

        for i, c in enumerate(cst):
            if isinstance(c, int):
                self.consts.append(ConstVal(ConstVal.Imm, c, i))
            elif isinstance(c, str) and len(c) == 1:
                self.consts.append(ConstVal(ConstVal.Imm, ord(c), i))
            elif isinstance(c, str):
                self.consts.append(ConstVal(ConstVal.Addr, c, i))
            else:
                self.consts.append(ConstVal(ConstVal.Unk, c, i))
    @property
    def name(self):
        return self.function_name

    def getLocalSlot(self, name):
        """ Returns the local variable position inside locals array """
        if name in self.locals:
            return self.locals.index(name)
        return -1
    
    def addComparison(self, cmp):
        self.compare_stack.append(cmp)

    def popComparison(self):
        return self.compare_stack.pop()

    def addLoop(self):
        self.loops.append(self.loop_cnt)
        loop_str = self.formatLoop(self.loop_cnt)         
        self.loop_cnt += 1

        return loop_str
    
    def getLoopTop(self):
        if len(self.loops) == 0:
            raise Exception("Jump stack empty")

        return self.formatLoop(self.loops[-1])

    def popLoop(self):
        if len(self.loops) == 0:
            raise Exception("Jump stack empty")

        return "fn loop_{}_{}_end".format(self.name, self.loops.pop())

    def formatLoop(self, cnt):
        return "loop_{}_{}".format(self.name, cnt)

    def getLocalAddr(self, name):
        """ Returns the BP relative offset to the specified local variable """
        res = self.getLocalSlot(name)

        if res != -1:
            return 4 + (4 * res)

        return -1

    def pushEvent(self, evt):
        """ Pushes a StackEvent onto the function stack """
        self.events.append(evt)

    def popEvent(self):
        """ Pops a StackEvent from the main stack """
        return self.events.pop()
    
    def getConsts(self):
        return self.consts
    
    def getStringRef(self, idx):
        return "str_{}_{}".format(idx, self.name)

    def setupArgs(self, argcount, emitter):
        """ Temp function moving n arguments from the stack to registers """
        # TODO: Find a proper way to structure the object hierarchy

        args = []
        REGS = ["$A", "$B", "$C", "$D", "$E", "$F"]

        for i in range(argcount):
            args.append(self.popEvent())
        
        args = args[::-1]

        for i, v in enumerate(args):
            if v.type == StackEvent.LOAD_CONST:
                cstval = self.getConsts()[v.index]

                if cstval.type == ConstVal.Addr:
                    emitter.emitMovRef(REGS[i], self.getStringRef(cstval.index))
                if cstval.type == ConstVal.Imm:
                    emitter.emitMovImm(REGS[i], cstval.value)
            if v.type == StackEvent.LOAD_FAST:
                emitter.emitLoadSlot(REGS[i], v.index)


