import dis

from rec.emitter import Emitter
from rec.env import Env, StackEvent, ConstVal
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
        
        env = Env(code)

        # if we are not at the toplevel we setup the function prologue
        if level_name != "<module>":
            csts = env.getConsts()
            
            # Emit const strings before function definition
            for i, v in enumerate(csts):
                if v.type == ConstVal.Addr:
                    self.emitter.emitString(env.getStringRef(i), v.value)

            self.emitter.emitLabel(level_name)
            self.emitter.emitPrologue(code.co_nlocals)
            
            # Copy args into slot
            for i in range(code.co_argcount):
                self.emitter.emitStoreSlot(REGS[i], i)

        for ins in btc:
            if ins.opname == "MAKE_FUNCTION":
                name = env.popEvent().value
                code = env.popEvent().value

                if not isinstance(code, type(self.compileBytecode.__code__)):
                    raise Exception("MAKE_FUNCTION instruction with no code object")

                self.compileBytecode(code)
            if ins.opname == "CALL_FUNCTION":
                arg_count = ins.argval
                args = []

                if arg_count >= len(REGS)-1:
                    raise Exception("Functions must have at most {} arguments".format(len(REGS)-1))
                
                for i in range(arg_count):
                    args.append(env.popEvent())
                
                args = args[::-1]

                for i, v in enumerate(args):
                    if v.type == StackEvent.LOAD_CONST:
                        print(v.index)
                        print(env.getConsts())
                        cstval = env.getConsts()[v.index]

                        if cstval.type == ConstVal.Addr:
                            self.emitter.emitMovRef(REGS[i], env.getStringRef(i))
                        if cstval.type == ConstVal.Imm:
                            self.emitter.emitMovImm(REGS[i], cstval.value)
                    if v.type == StackEvent.LOAD_FAST:
                        self.emitter.emitLoadSlot(REGS[i], v.index)

                # TODO: Emit movs of variables into regs

                func = env.popEvent().value
                self.emitter.emitRaw("call #{}".format(func))
                
                env.pushEvent(StackEvent(StackEvent.MAKE_FUNCTION_DUMMY, 0, 0))

            if ins.opname == "LOAD_FAST":
                env.pushEvent(StackEvent(StackEvent.LOAD_FAST, ins.argval, ins.arg))
            if ins.opname == "LOAD_CONST":
                env.pushEvent(StackEvent(StackEvent.LOAD_CONST, ins.argval, ins.arg))
            if ins.opname == "LOAD_GLOBAL":
                env.pushEvent(StackEvent(StackEvent.LOAD_GLOBAL, ins.argval, ins.arg))
            if ins.opname == "STORE_FAST":
                evt = env.popEvent()
                
                # We returned from a function
                if evt.type == StackEvent.MAKE_FUNCTION_DUMMY:
                    self.emitter.emitStoreSlot(REGS[0], evt.index)
            if ins.opname == "RETURN_VALUE":
                evt = env.popEvent()

                if evt.type == StackEvent.LOAD_FAST:
                    self.emitter.emitLoadSlot(REGS[0], evt.index)
                if evt.type == StackEvent.LOAD_CONST:
                    cstval = env.getConsts()[evt.index]

                    if cstval.type == ConstVal.Imm:
                        self.emitter.emitMovImm(REGS[0], cstval.value)
                    if cstval.type == ConstVal.Addr:
                        self.emitter.emitMovAddr(REGS[0], env.getStringRef(evt.index))

        if level_name != "<module>":
            self.emitter.emitEpilogue()
