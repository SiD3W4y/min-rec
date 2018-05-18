"""
        Min-Rec : Python bytecode to min assembly recompiler
"""
import os
import sys
import argparse
import dis

from rec.preprocessor import Preprocessor
from rec.recompiler import Recompiler

if __name__ == '__main__':
    std_path = os.path.dirname(os.path.realpath(__file__)) + "/std/"
    current_path = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
    include_paths = [std_path, current_path]
    
    parser = argparse.ArgumentParser(description="Python to nim bytecode recompiler")
    parser.add_argument("-I", "--include", action="append", dest="custom_imports", help="adds a custom include path to the compiler")
    parser.add_argument("-i", "--input", action="store", dest="input_path", required=True, help="Input python script") 
    parser.add_argument("-o", "--output", action="store", dest="output_path", required=True, help="Output assembly file")

    args = parser.parse_args()
    
    # Appending custom imports to search path
    if args.custom_imports is not None:
        for imp_path in args.custom_imports:
            if os.path.exists(imp_path):
                include_paths.append(os.path.realpath(imp_path) + "/")
            else:
                print("Warn : Include path \"{}\" does not seem to exist".format(imp_path))

    prepro = Preprocessor(include_paths)
    recomp = Recompiler()
    
    try:
        final_source = prepro.processFile(args.input_path)
    except Exception as e:
        print("Preprocessor Error : {}".format(e))
        sys.exit(0)

    try:
        res = recomp.compileString(final_source)
    except Exception as e:
        print("Recompiler Error : {}".format(e))
        sys.exit(0)

    # loading internals
    if not os.path.exists(std_path+"internal.min"):
        print("Could not find std/internal.min, please check your repo")
        sys.exit(0)

    internal = open(std_path+"internal.min", 'r').read()

    with open(args.output_path, 'w') as f:
        f.write(internal)
        f.write(res)
