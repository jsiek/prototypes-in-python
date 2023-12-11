import sys
import os
from parser import parse, set_filename
from utilities import tracing_on
from values import *
from abstract_syntax import *
from reduce import run

if __name__ == "__main__":
    homedir = os.getcwd()
    directory = homedir + '/tests/'
    if not os.path.isdir(directory):
        raise Exception('missing directory for test programs: ' \
                        + directory)
    for (dirpath, dirnames, filenames) in os.walk(directory):
        tests = [dirpath + t for t in filenames]
        break
    for filename in tests:
      set_filename(filename)
      file = open(filename, 'r')
      p = file.read()
      ast = parse(p, trace=False)
      trace = False
      if trace:
        print(str(ast))
      result = run(ast, trace=trace)
      match result:
        case Int(n):
          if n != 0:
            raise Exception('test ' + filename + ' failed, result = ' + str(n))
        case _:
          raise Exception('test ' + filename + ' failed, result = ' + str(result))
    print('passed all tests')
  
