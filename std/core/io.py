# io module : Mostly wrapping around syscalls for now

def write(fd, addr, len):
    __syscall__(0, fd, addr, len)

def read(fd, addr, len):
    __syscall__(1, fd, addr, len)

def exit(code):
    __syscall__(2, code, 0, 0)
