def exit(exit_code):
    __syscall(SYS_EXIT, exit_code, 0, 0)
