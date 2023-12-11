from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Any
import sys
sys.path.append('..')
from lark.tree import Meta
from ast_base import *
from ast_types import *
from values import *
from primitive_operations import eval_prim

    
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
      
# Reduces the first expression in rands that can be reduced (not a value).
def reduce_one_of(rands):
  new_rands = []
  i = 0
  while i != len(rands):
    if rands[i].is_value():
      new_rands.append(rands[i])
      i += 1
    else:
      new_rands.append(rands[i].reduce())
      i += 1
      break
  while i != len(rands):
    new_rands.append(rands[i])
    i += 1
  return new_rands

@dataclass
class Int(Exp):
  value: int
  __match_args__ = ("value",)

  def __str__(self):
      return "'" + str(self.value) + "'"

  def __repr__(self):
      return "'" + str(self) + "'"

  def free_vars(self):
      return set()

  def type_check(self, env, ctx):
    return IntType(self.location), self

  def is_value(self):
    return True

  def substitute(self, env):
    return self
  
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

  def is_value(self):
    return True
  
  def substitute(self, env):
    return self
      
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

  def substitute(self, env):
    return IfExp(self.location, self.cond.substitute(env),
                 self.thn.substitute(env), self.els.substitute(env))
    
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
    
  def reduce(self):
    if self.cond.is_value():
      match self.cond:
        case Bool(True):
          return self.thn
        case Bool(False):
          return self.els
        case _:
          raise Exception('if expected a boolean condition, not ' + str(self.cond))
    else:
      return IfExp(self.location, self.cond.reduce(), self.thn, self.els)
  
def to_value(e):
  match e:
    case Int(n):
      return Number(n)
    case Bool(b):
      return Boolean(b)
    case _:
      raise Exception('unrecognized constant ' + repr(e))

def from_value(v, location):
  match v:
    case Number(n):
      return Int(location, n)
    case Boolean(b):
      return Bool(location, b)
    case _:
      raise Exception('unrecognized value ' + repr(v))

@dataclass
class PrimitiveCall(Exp):
    op: str
    args: list[Exp]
    __match_args__ = ("op", "args")

    def __str__(self):
        return self.op + \
               "(" + ", ".join([str(arg) for arg in self.args]) + ")"

    def __repr__(self):
        return str(self)

    def free_vars(self):
        return set().union(*[arg.free_vars() for arg in self.args])

    def substitute(self, env):
        return PrimitiveCall(self.location, self.op,
                             [arg.substitute(env) for arg in self.args])
      
    def type_check(self, env, ctx):
        if tracing_on():
            print("starting to type checking " + str(self))
        arg_types = []
        new_args = []
        for arg in self.args:
            arg_type, new_arg = arg.type_check(env, 'none')
            arg_types.append(arg_type)
            new_args.append(new_arg)
        if tracing_on():
            print("checking primitive " + str(self.op))
        ret, cast_args = type_check_prim(self.location, self.op, arg_types, new_args)
        if tracing_on():
            print("finished type checking " + str(self))
            print("type: " + str(ret))
        return ret, PrimitiveCall(self.location, self.op, cast_args)

    def is_value(self):
        return False

    def reduce(self):
      if all([arg.is_value() for arg in self.args]):
        rands = [to_value(arg) for arg in self.args]
        return from_value(eval_prim(self.op, rands, self.location), self.location)
      else:
        return PrimitiveCall(self.location, self.op, reduce_one_of(self.args))
        
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

    def substitute(self, env):
        return Call(self.location, self.fun.substitute(env),
                    [arg.substitute(env) for arg in self.args])
      
    def reduce(self):
      if self.fun.is_value():
        if all([rand.is_value() for rand in self.args]):
          return self.fun.apply(self.args)
        else:
          return Call(self.location, self.fun, reduce_one_of(self.args))
      else:
          return Call(self.location, self.fun.reduce(), self.args)
      
      
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

    def substitute(self, env):
      new_env = env.deepcopy()
      for p in self.params:
          del new_env[p.ident]
      return Lambda(params, self.body.substitute(new_env), name)
      
    def is_value(self):
      return True

    def apply(self, args):
      env = {p.ident : arg for p in self.params for arg in args}
      return self.body.substitute(env)
      
    
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

    def is_value(self):
      return True

    def substitute(self, env):
      if self.ident in env.keys():
        return env[self.ident]
      else:
        return self
    
@dataclass
class LetExp(Exp):
    param: Param
    arg: Exp
    body: Exp
    __match_args__ = ("param", "arg", "body")

    def __str__(self):
      return "let " + str(self.param) + " = " + str(self.arg) + " in " \
        + str(self.body)

    def __repr__(self):
        return str(self)

    def free_vars(self):
        return self.arg.free_vars() \
               | (self.body.free_vars() - set([self.param.ident]))

    def substitute(self, env):
      new_env = env.deepcopy()
      del new_env[self.param.ident]
      return LetExp(self.location, self.param, self.arg.substitute(env),
                    self.body.sustitute(new_env))

    def reduce(self):
      if self.arg.is_value():
        env = {self.param.ident : self.arg}
        return self.body.substitute(env)
      else:
        return LetExp(self.location, self.param, self.arg.reduce(), self.body)
      
    
# Tuple Creation

@dataclass
class TupleExp(Exp):
  inits: list[Exp]
  __match_args__ = ("inits",)

  def __str__(self):
      return '⟨' + ', '.join([str(e) for e in self.inits]) + '⟩'

  def __repr__(self):
      return str(self)

  def free_vars(self):
      return set().union(*[init.free_vars() for init in self.inits])

  def substitute(self, env):
    return TupleExp(self.location, [init.substitute(env) for init in self.inits])
    
  def is_value(self):
    return all([init.is_value() for init in self.inits])

  def reduce(self):
    return TupleExp(self.location, reduce_one_of(self.inits))

  def get(self, index):
    return self.inits[index.value]
    
# Element Access

@dataclass
class Index(Exp):
  arg: Exp
  index: Exp
  __match_args__ = ("arg", "index")
  
  def __str__(self):
      return str(self.arg) + "[" + str(self.index) + "]"
  
  def __repr__(self):
      return str(self)
  
  def free_vars(self):
      return self.arg.free_vars() | self.index.free_vars()

  def substitute(self, env):
      return Index(self.location, self.arg.substitute(env),
                   self.index.substitute(env))
                    
  def reduce(self):
      if self.arg.is_value():
        if self.index.is_value():
          return self.arg.get(self.index)
        else:
          return Index(self.location, self.arg, self.index.reduce())
      else:
        return Index(self.location, self.arg.reduce(), self.index)
    
