import dis

from rec.emitter import Emitter
from rec.env import Env, StackEvent, ConstVal
import rec.utils as utils

def _makeslot(args):
    pass

def _syscall(args):
    pass

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

                if arg_count >= len(REGS)-1:
                    raise Exception("Functions must have at most {} arguments".format(len(REGS)-1))
                
                # TODO: Emit movs of variables into regs
                env.setupArgs(arg_count, self.emitter)

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
                if evt.type == StackEvent.LOAD_CONST:
                    cstval = env.getConsts()[evt.index]

                    if cstval.type == ConstVal.Imm:
                        self.emitter.emitMovImm(REGS[0], cstval.value)
                    if cstval.type == ConstVal.Addr:
                        self.emitter.emitMovRef(REGS[0], cstval.value)

                    self.emitter.emitStoreSlot(REGS[0], ins.arg)

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

            if ins.opname.startswith("BINARY") or ins.opname.startswith("INPLACE"):
                env.setupArgs(2, self.emitter)

                if ins.opname == "BINARY_ADD" or ins.opname == "INPLACE_ADD":
                    self.emitter.emitRaw("add $A $B")
                if ins.opname == "BINARY_MULTIPLY" or ins.opname == "INPLACE_MULTIPLY":
                    self.emitter.emitRaw("mul $A $B")
                if ins.opname == "BINARY_SUBSTRACT" or ins.opname == "INPLACE_SUBSTRACT":
                    self.emitter.emitRaw("sub $A $B")
                if ins.opname == "BINARY_LSHIFT":
                    self.emitter.emitRaw("shl $A $B")
                if ins.opname == "BINARY_RSHIFT":
                    self.emitter.emitRaw("shr $A $B")
                if ins.opname == "BINARY_AND":
                    self.emitter.emitRaw("and $A $B")
                if ins.opname == "BINARY_XOR":
                    self.emitter.emitRaw("xor $A $B")
                if ins.opname == "BINARY_OR":
                    self.emitter.emitRaw("or $A $B")

                env.pushEvent(StackEvent(StackEvent.MAKE_FUNCTION_DUMMY, 0, 0))
            if ins.opname == "SETUP_LOOP":
                self.emitter.emitLabel(env.addLoop())
            if ins.opname == "JUMP_ABSOLUTE":
                self.emitter.emitRaw("jmp #{}".format(env.getLoopTop()))
            if ins.opname == "POP_BLOCK":
                self.emitter.emitRaw(env.popLoop())

            if ins.opname == "COMPARE_OP":
                env.setupArgs(2, self.emitter)
                env.addComparison(ins.argval)
                self.emitter.emitRaw("cmp $A $B")
                env.pushEvent(StackEvent(StackEvent.MAKE_FUNCTION_DUMMY, 0, 0))
            
            if ins.opname == "POP_JUMP_IF_TRUE":
                cmp = env.popComparison()
                dest = env.getLoopTop() + "_end"

                if cmp == '>':
                    self.emitter.emitRaw("jbe #{}".format(dest))
                if cmp == '<':
                    self.emitter.emitRaw("jle #{}".format(dest))
                if cmp == "==":
                    self.emitter.emitRaw("je #{}".format(dest))
                if cmp == "!=":
                    self.emitter.emitRaw("jne #{}".format(dest))

            if ins.opname == "POP_JUMP_IF_FALSE":
                cmp = env.popComparison()
                dest = env.getLoopTop() + "_end"

                if cmp == '>':
                    self.emitter.emitRaw("jle #{}".format(dest))
                if cmp == '<':
                    self.emitter.emitRaw("jbe #{}".format(dest))
                if cmp == "==":
                    self.emitter.emitRaw("jne #{}".format(dest))
                if cmp == "!=":
                    self.emitter.emitRaw("je #{}".format(dest))


        if level_name != "<module>":
            self.emitter.emitEpilogue()
