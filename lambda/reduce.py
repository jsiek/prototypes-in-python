import sys
from parser import parse, set_filename
from utilities import tracing_on
from values import *
from abstract_syntax import *

def run(e, trace=False):
  while not e.is_value():
    e = e.reduce()
    if trace:
      print('--->')
      print(str(e))
  if trace:
    print()
  return e
    
    
if __name__ == "__main__":
  filename = sys.argv[1]
  set_filename(filename)
  file = open(filename, 'r')
  p = file.read()
  ast = parse(p, trace=True)
  print(str(ast))
  print('result: ' + str(run(ast, trace=True)))
