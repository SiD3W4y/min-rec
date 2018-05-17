import os

class Preprocessor:
    def __init__(self, search_paths):
        self.paths = search_paths
        self.modules = set()

    def resolveModule(self, name):
        name = name.replace(".", "/")

        for include_path in self.paths:
            fullpath = include_path+name+".py"
            if os.path.exists(fullpath):
                return fullpath 

        return ""

    def processFile(self, path):
        """ Preprocesses from a single python source file"""
        # TODO: Add existence checking
        if not os.path.exists(path):
            raise Exception("file {} not found".format(path))

        f = open(path, "r")
        data_str = f.read()

        return self.processString(data_str)

    def processString(self, data_str):
        """ Preprocesses an input code string """
        lines = data_str.split("\n")
        source = [] # final source
        imports = [] # import list
        processed = [] # imported module source
        
        # we have to resolve imports on the behalf of python and concatenate
        # all required files in a single one
        for line in lines:
            if line.startswith("import"):
                imports.append(line[6:].strip())
            else:
                source.append(line)

        for mod in imports:
            fullpath = self.resolveModule(mod)

            if fullpath == "":
                raise Exception("Import \"{}\" could not be resolved".format(mod))
            
            # We don't want to import two times the same file
            if mod not in self.modules:
                self.modules.add(mod)
                processed.append(self.processFile(fullpath))
        
        return "".join(processed) + "\n".join(source)
