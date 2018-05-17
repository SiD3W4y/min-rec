import dis

from rec.emitter import Emitter
import rec.utils as utils

def _makeslot(args):
    pass

def _syscall(args):
    pass

def processConsts(cst):
    if cst is None:
        return 0
    elif isinstance(cst, str) and len(cst) == 1:
        return ord(c)
    else:
        return cst

REGS = ["$A", "$B", "$C", "$D", "$E", "$F"]

class ConstType:
    Addr = 0
    Imm = 1

class StackEvent:
    LOAD_FAST = 0
    LOAD_CONST = 1
    LOAD_GLOBAL = 2
    MAKE_FUNCTION_DUMMY = 3 # push a dummy return value on the stack

    def __init__(self, evt_type, evt_val):
        self.evt_type = evt_type
        self.evt_val = evt_val

    @property
    def value(self):
        return self.evt_val

    @property
    def type(self):
        return self.evt_type

class Recompiler:
    def __init__(self):
        self.builtin_funcs = {}
        self.builtin_consts = {}
        
        # bind builtin functions
        self.builtin_funcs["__slot__"] = _makeslot
        self.builtin_funcs["__syscall__"] = _syscall
        
        # bind builtin constants
        self.builtin_consts["SYS_WRITE"] = 0
        self.builtin_consts["SYS_READ"] = 1
        self.builtin_consts["SYS_EXIT"] = 2

        self.emitter = Emitter()
    
    @staticmethod
    def stackFromSlot(x):
        return 4 + x * 4

    def compileString(self, data):
        code = compile(data, "program", "exec")
        self.compileBytecode(code)

        return self.emitter.value

    def compileBytecode(self, code):
        """ recursively compiles bytecode to min assembly """
        btc = dis.get_instructions(code)
        
        print(dis.code_info(code))
        dis.dis(code)
        
        level_name = code.co_name
        consts = list(map(processConsts, code.co_consts))
        
        events = []

        # if we are not at the toplevel we setup the function prologue
        if level_name != "<module>":
            self.emitter.emitLabel(level_name)

            # TODO: Emit function constants
            self.emitter.emitRaw("push $BP")
            self.emitter.emitRaw("mov $BP, $SP")
            self.emitter.emitRaw("sub $SP, {}".format(code.co_nlocals * 4))

            # TODO: Copy arguments into local slots
            

        for ins in btc:
            if ins.opname == "MAKE_FUNCTION":
                name = events.pop().value
                code = events.pop().value

                if not isinstance(code, type(self.compileBytecode.__code__)):
                    raise Exception("MAKE_FUNCTION instruction with no code object")

                self.compileBytecode(code)
            if ins.opname == "CALL_FUNCTION":
                arg_count = ins.argval
                args = []

                if arg_count >= len(REGS):
                    raise Exception("Functions must have at most {} arguments".format(len(REGS)))
                
                for i in range(arg_count):
                    args.append(events.pop())
                
                # TODO: Emit movs of variables into regs
                func = events.pop().value
                self.emitter.emitRaw("call #{}".format(func))
                
                events.append(StackEvent(StackEvent.MAKE_FUNCTION_DUMMY, 0))

            if ins.opname == "LOAD_FAST":
                events.append(StackEvent(StackEvent.LOAD_FAST, ins.argval))
            if ins.opname == "LOAD_CONST":
                events.append(StackEvent(StackEvent.LOAD_CONST, ins.argval))
            if ins.opname == "LOAD_GLOBAL":
                events.append(StackEvent(StackEvent.LOAD_GLOBAL, ins.argval))

        if level_name != "<module>":
            self.emitter.emitRaw("mov $SP, $BP")
            self.emitter.emitRaw("pop $BP")
            self.emitter.emitRaw("ret\n")
