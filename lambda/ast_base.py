from __future__ import annotations # To refer to class type in the class.

from dataclasses import dataclass
from lark.tree import Meta
from typing import Any
from error import error

def copy(exp):
  if exp is None:
    return exp
  else:
    return exp.copy()

def copy_type_env(type_env):
  return {x: info.copy() for x,info in type_env.items()}

def merge_type_env(tyenv1, tyenv2):
  tyenv3 = {}
  for x, info in tyenv1.items():
    tyenv3[x] = info.copy()
  for x, info in tyenv2.items():
    if x in tyenv3.keys():
      tyenv3[x] = info.merge(tyenv3[x])
    else:
      tyenv3[x] = info.copy()
  return tyenv3
    

@dataclass
class AST:
    location: Meta
    
    def debug_skip(self):
      return False

@dataclass(frozen=True)
class Type:
    location: Meta

@dataclass
class Exp(AST):
  
  # Returns the set of free variables of this expression.
  def free_vars(self) -> set[str]:
    raise Exception('Exp.free_vars unimplemented')

  # Checks that the expression obeys the type checking rules.
  # The environment `env` provides the types for all of the
  # variables that are currently in scope.
  # Returns the type of this expression and a translation
  # of this expression.
  def type_check(self, env: dict[str,Type]) -> tuple[Type,Exp]:
    raise Exception('Exp.type_check unimplemented')

  def __str__(self):
    raise Exception('Exp.__str__ unimplemented')
  
  def __repr__(self):
    raise Exception('Exp.__repr__ unimplemented')

@dataclass
class Value:
  pass
