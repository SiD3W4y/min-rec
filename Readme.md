# Min-Rec

Python bytecode to min assembly recompiler

## Status
This project is an experiment and not a stable product so use at your own risk.

## Sample code
As both the vm and the recompiler are not in a usable state, only simple programs can run for now. Such as this one.

```python
import core.io

def print(addr, size):
    write(0, addr, size)

def main():
    sz = 14

    print("Hello World !\n", sz)

    exit(0)
```

## Note
The python bytecode changes a lot between releases so the recompiler may not work on your platform. If you want to be sure that everythingworks you can try running it on python 3.6+
