from dataclasses import dataclass
from lark.tree import Meta
import numbers
from typing import Any, Optional
from ast_base import *
from error import *

# flag for tracing

trace = False

def set_trace(b: bool):
  global trace
  trace = b

def tracing_on():
  return trace

# flag for debugging

debug_flag = False

def debug():
  return debug_flag

def set_debug(v):
  global debug_flag
  debug_flag = v

# debug mode

debug_cmd = 's'

def debug_mode():
  return debug_cmd

def set_debug_mode(cmd):
  global debug_cmd
  debug_cmd = cmd


# flag for verbose

verbose_flag = False

def verbose():
  return verbose_flag

def set_verbose(v):
  global verbose_flag
  verbose_flag = v

# interpreting primitives

interp_prim = {}

def set_primitive_interp(op, fun):
  interp_prim[op] = fun

def get_primitive_interp(op):
  return interp_prim[op]

# type checking primitives

type_check_prim = {}

def set_primitive_type_check(op, fun):
  type_check_prim[op] = fun

def get_primitive_type_check(op):
  if not op in type_check_prim.keys():
    raise Exception('unrecognized primitive operation ' + op)
  return type_check_prim[op]
  
def getch():
    import termios
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    return _getch()  

def print_dict(dict):
  for (k,v) in dict.items():
    print(str(k) + ': ' + str(v))
  print()

