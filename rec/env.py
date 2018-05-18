
class ConstVal:
    Addr = 0
    Imm = 1
    Unk = 2

    def __init__(self, cst_type, cst_value):
        self.cst_type = cst_type
        self.cst_value = cst_value
    
    @property
    def type(self):
        return self.cst_type

    @property
    def value(self):
        return self.cst_value

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
        
        # Builtin functions
        self.builtin_funcs = {
            "__slot__": lambda a: a,
            "__str__": lambda a: a
        }

        # Preparing constants
        cst = list(code.co_consts)

        for c in cst:
            print("cst : {}".format(c))
            if isinstance(c, int):
                self.consts.append(ConstVal(ConstVal.Imm, c))
            elif isinstance(c, str) and len(c) == 1:
                self.consts.append(ConstVal(ConstVal.Imm, ord(c)))
            elif isinstance(c, str):
                self.consts.append(ConstVal(ConstVal.Addr, c))
            else:
                self.consts.append(ConstVal(ConstVal.Unk, c))
    @property
    def name(self):
        return self.function_name

    def getLocalSlot(self, name):
        """ Returns the local variable position inside locals array """
        if name in self.locals:
            return self.locals.index(name)
        return -1

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
