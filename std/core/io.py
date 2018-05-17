def read(fd, addr, len):
    __syscall(SYS_READ, fd, addr, len)

def write(fd, addr, len):
    __syscall(SYS_WRITE, fd, addr, len)
