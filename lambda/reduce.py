import sys
from parser import parse, set_filename
from utilities import tracing_on
from values import *
from abstract_syntax import *
from primitive_operations import eval_prim, PrimitiveCall

def substitute(env, e):
  match e:
    case Call(rator, rands):
      return Call(substitute(env, rator),
                  [substitute(env, rand) for rand in rands])
    case Lambda(params, body, name):
      new_env = env.deepcopy()
      for p in params:
        if p.ident == x:
          del new_env[x]
      return Lambda(params, substitute(new_env, body), name)
    case Var(ident):
      if ident in env:
        return env[ident]
      else:
        return e
    case Int(num):
      return e
    case Bool(b):
      return e
    case PrimitiveCall(op, args):
      return PrimitiveCall(e.location, op, [substitute(env, arg) for arg in args])
    case _:
      raise Exception('substitute, unhandled case ' + repr(e))
    
# Reduces the first expression in rands that can be reduced (not a value).
def reduce_one_of(rands):
  new_rands = []
  i = 0
  while i != len(rands):
    if rands[i].is_value():
      new_rands.append(rands[i])
      i += 1
    else:
      new_rands.append(reduce(rands[i]))
      i += 1
      break
  while i != len(rands):
    new_rands.append(rands[i])
    i += 1
  return new_rands

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

def apply_fun(rator, rands):
  match rator:
    case Lambda(params, body, name):
      env = {p.ident : rand for p in params for rand in rands}
      return substitute(env, body)
    case _:
      raise Exception("can't call " + repr(rator))

def tuple_get(tup, index):
  match tup:
    case TupleExp(elts):
      match index:
        case Int(n):
          return elts[n]
        case _:
          raise Exception('expected an integer in tuple subscript, not ' + str(index))
    case _:
      raise Exception('expected a tuple in tuple subscript, not ' + str(tup))
    
def reduce(e):
  match e:
    case Call(rator, rands):
      if rator.is_value():
        if all([rand.is_value() for rand in rands]):
          return apply_fun(rator, rands)
        else:
          return Call(e.location, rator, reduce_one_of(rands))
      else:
          return Call(e.location, reduce(rator), rands)
    case PrimitiveCall(op, args):
      if all([arg.is_value() for arg in args]):
        rands = [to_value(arg) for arg in args]
        return from_value(eval_prim(op, rands, e.location), e.location)
      else:
        return PrimitiveCall(e.location, op, reduce_one_of(args))
    case Index(tup, index):
      if tup.is_value():
        if index.is_value():
          return tuple_get(tup, index)
        else:
          return Index(e.location, tup, reduce(index))
      else:
        return Index(e.location, reduce(tup), index)
    case TupleExp(args):
      return TupleExp(e.location, reduce_one_of(args))
    case LetExp(param, arg, body):
      if arg.is_value():
        env = {param.ident : arg}
        return substitute(env, body)
      else:
        return LetExp(e.location, param, reduce(arg), body)
    case _:
      raise Exception("can't reduce " + repr(e))

def run(e, trace=False):
  while not e.is_value():
    e = reduce(e)
    if trace:
      print('--->')
      print(str(e))
  return e
    
    
if __name__ == "__main__":
  filename = sys.argv[1]
  set_filename(filename)
  file = open(filename, 'r')
  p = file.read()
  ast = parse(p, trace=True)
  print(str(ast))
  print('result: ' + str(run(ast, trace=True)))
