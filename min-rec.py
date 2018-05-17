"""
        Min-Rec : Python bytecode to min assembly recompiler
"""
import os
import sys
import argparse

from rec.preprocessor import Preprocessor

if __name__ == '__main__':
    std_path = os.path.dirname(os.path.realpath(__file__)) + "/std/"
    current_path = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
    include_paths = [std_path, current_path]

    parser = argparse.ArgumentParser(description="Python to nim bytecode recompiler")
    parser.add_argument("-I", "--include", action="append", dest="custom_imports", help="adds a custom include path to the compiler")
    parser.add_argument("-i", "--input", action="store", dest="input_path", required=True, help="Input python script") 

    args = parser.parse_args()
    
    # Appending custom imports to search path
    if args.custom_imports is not None:
        for imp_path in args.custom_imports:
            if os.path.exists(imp_path):
                include_paths.append(os.path.realpath(imp_path) + "/")
            else:
                print("Warn : Include path \"{}\" does not seem to exist".format(imp_path))

    prepro = Preprocessor(include_paths)
    
    try:
        final_source = prepro.processFile(args.input_path)
    except Exception as e:
        print(e)
        sys.exit(0)
