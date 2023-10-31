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

def is_value(e):
  match e:
    case Lambda(params, body, name):
      return True
    case Int(num):
      return True
    case Bool(b):
      return True
    case _:
      return False

def reduce_arg(rands):
  new_rands = []
  i = 0
  while i != len(rands):
    if is_value(rands[i]):
      new_rands.append(rands[i])
      i += 1
    else:
      new_rands.append(reduce(rands[i]))
      i += 1
      break
  while i != len(rands):
    new_rands.append(rands[i])
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

def reduce(e):
  match e:
    case Call(rator, rands):
      if is_value(rator):
        if all([is_value(rand) for rand in rands]):
          match rator:
            case Lambda(params, body, name):
              env = {p.ident : rand for p in params for rand in rands}
              return substitute(env, body)
            case _:
              raise Exception("can't call " + repr(rator))
        else:
          return Call(rator, reduce_arg(rands))
      else:
          return Call(reduce(rator), rands)
    case PrimitiveCall(op, args):
      if all([is_value(arg) for arg in args]):
        rands = [to_value(arg) for arg in args]
        return from_value(eval_prim(op, rands, e.location), e.location)
      else:
        return PrimitiveCall(op, reduce_args(args))
    case _:
      raise Exception("can't reduce " + repr(e))

def run(e):
  while not is_value(e):
    e = reduce(e)
  return e
    
    
if __name__ == "__main__":
  filename = sys.argv[1]
  set_filename(filename)
  file = open(filename, 'r')
  p = file.read()
  ast = parse(p, trace=False)
  print('program: ' + str(ast))
  print('result: ' + str(run(ast)))
