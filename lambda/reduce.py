import sys
from parser import parse, set_filename
from utilities import tracing_on

if __name__ == "__main__":
  filename = sys.argv[1]
  set_filename(filename)
  file = open(filename, 'r')
  p = file.read()
  ast = parse(p, trace=False)
  print(ast)
