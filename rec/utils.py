import dis

def dumpCodeInfo(code):
    props = {}
    props["consts"] = code.co_consts
    props["name"] = code.co_name
    props["localscnt"] = code.co_nlocals
    props["stacksize"] = code.co_stacksize
    
    print("==== Code info ===")
    for k, v in props.items():
        print("{} = {}".format(k, v))
