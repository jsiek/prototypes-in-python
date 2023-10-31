from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Any
from lark.tree import Meta
from ast_base import *
from ast_types import *
    
# Expressions

def is_constant(e):
  match e:
    case Int(n):
      return True
    case Bool(b):
      return True
    case _:
      return False

def eval_constant(e):
  match e:
    case Int(n):
      return Number(n)
    case Bool(b):
      return Boolean(b)
    case _:
      error(e.location, "expected a constant, not " + str(e))
      

@dataclass
class Int(Exp):
  value: int
  __match_args__ = ("value",)

  def __str__(self):
      return str(self.value)

  def __repr__(self):
      return str(self)

  def free_vars(self):
      return set()

  def type_check(self, env, ctx):
    return IntType(self.location), self
    
    
@dataclass
class Bool(Exp):
  value: bool
  __match_args__ = ("value",)
  
  def __str__(self):
    return str(self.value)
  
  def __repr__(self):
    return str(self)
  
  def free_vars(self):
    return set()
  
  def type_check(self, env, ctx):
    return BoolType(self.location), self
  
      
@dataclass
class IfExp(Exp):
  cond: Exp
  thn: Exp
  els: Exp
  __match_args__ = ("cond", "thn", "els")
  
  def __str__(self):
      return "(" + str(self.cond) + "?" + str(self.thn) \
          + " : " + str(self.els) + ")"
    
  def __repr__(self):
      return str(self)
    
  def free_vars(self):
      return self.cond.free_vars() | self.thn.free_vars() \
          | self.els.free_vars()
    
  def type_check(self, env, ctx):
    cond_type, new_cond = self.cond.type_check(env, 'none')
    thn_type, new_thn = self.thn.type_check(env, ctx)
    els_type, new_els = self.els.type_check(env, ctx)
    if not consistent(cond_type, BoolType(self.location)):
      static_error(self.location, 'in conditional, expected a Boolean, not '
            + str(cond_type))
    if not consistent(thn_type, els_type):
      static_error(self.location,
                   'in conditional, branches must be consistent, not '
                   + str(cond_type))
    return join(thn_type, els_type), \
           IfExp(self.location, new_cond, new_thn, new_els)
    

@dataclass
class Call(Exp):
    fun: Exp
    args: list[Exp]

    __match_args__ = ("fun", "args")

    def __str__(self):
        return str(self.fun) \
               + "(" + ", ".join([str(arg) for arg in self.args]) + ")"

    def __repr__(self):
        return str(self)

    def free_vars(self):
        return self.fun.free_vars() \
               | set().union(*[arg.free_vars() for arg in self.args])

@dataclass(frozen=True)
class Param:
    location: Meta
    ident: str
    type_annot: Type

    def __str__(self):
        return self.ident

    def __repr__(self):
        return str(self)
      
@dataclass
class Lambda(Exp):
    params: list[Param]
    body: Exp
    name: str = "lambda"
    __match_args__ = ("params", "body", "name")

    def __str__(self):
        return "(λ " \
               + ", ".join([str(p) for p in self.params]) + "." \
               + " " + str(self.body) + ")"

    def __repr__(self):
        return str(self)

    def free_vars(self):
        params = set([p.ident for p in self.params])
        return self.body.free_vars() - params

@dataclass
class Var(Exp):
    ident: str
    __match_args__ = ("ident",)

    def __str__(self):
        return self.ident

    def __repr__(self):
        return str(self)

    def free_vars(self):
        return set([self.ident])
      
@dataclass
class LetExp(Exp):
    param: Param
    arg: Exp
    body: Exp
    __match_args__ = ("param", "arg", "body")

    def __str__(self):
        if verbose():
            return "let " + str(self.param) + " = " + str(self.arg) + "in\n" \
                   + str(self.body)
        else:
            return "let " + str(self.param) + " = " + str(self.arg) + "in ..."

    def __repr__(self):
        return str(self)

    def free_vars(self):
        return self.arg.free_vars() \
               | (self.body.free_vars() - set([self.param.ident]))
