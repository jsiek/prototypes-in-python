from abstract_syntax import *
from error import error

def check_implies(loc, frm1, frm2):
  match frm2:
    case Bool(loc, True):
      pass
    case And(loc, args):
      for arg2 in args:
        check_implies(loc, frm1, arg2)
    case IfThen(loc2, prem2, conc2):
      match frm1:
        case IfThen(loc1, prem1, conc1):
          check_implies(loc, prem2, prem1)
          check_implies(loc, conc1, conc2)
        case _:
          error(loc, 'expected ' + str(frm2) + '\nbut only have ' + str(frm1))
    case _:
      match frm1:
        case Bool(loc, False):
          pass
        case And(loc, args):
          for arg1 in args:
            try:
              check_implies(arg1, frm2)
              return
            except:
              pass
        case _:
          error(loc, 'expected ' + str(frm2) + '\nbut only have ' + str(frm1))

def check_proof(proof, env):
  match proof:
    case PVar(loc, name):
      return env[name]
    case PTrue(loc):
      return Bool(loc, True)
    case PLet(loc, label, frm, reason, rest):
      check_proof_of(reason, frm, env)
      new_env = {l: f for (l,f) in env.items()}
      new_env[label] = frm
      return check_proof(rest, new_env)
    case Tuple(loc, pfs):
      frms = [check_proof(pf, env) for pf in pfs]
      return And(loc, frms)
    case ImpIntro(loc, label, prem, body):
      new_env = {l: f for (l,f) in env.items()}
      new_env[label] = prem
      conc = check_proof(body, new_env)
      return IfThen(loc, prem, conc)
    case Apply(loc, imp, arg):
      ifthen = check_proof(imp, env)
      match ifthen:
        case IfThen(loc, prem, conc):
          check_proof_of(arg, prem, env)
          return conc
        case _:
          error(loc, 'expected an if-then, not ' + str(ifthen))
    case _:
      error(proof.location, 'unhandled ' + str(proof))

def check_proof_of(proof, formula, env):
  match proof:
    case ImpIntro(loc, label, None, body):
      match formula:
        case IfThen(loc, prem, conc):
          new_env = {l: f for (l,f) in env.items()}
          new_env[label] = prem
          check_proof_of(body, conc, new_env)
        case _:
          error(proof.location, 'expected proof of if-then, not ' + str(proof))
    case PLet(loc, label, frm, reason, rest):
      check_proof_of(reason, frm, env)
      new_env = {l: f for (l,f) in env.items()}
      new_env[label] = frm
      check_proof_of(rest, formula, new_env)
    case _:
      form = check_proof(proof, env)
      check_implies(proof.location, form, formula)

def check_statement(stmt, env):
  match stmt:
    case Theorem(loc, name, frm, pf):
      check_proof_of(pf, frm, env)
      env[name] = frm
    
def check_poof(ast):
  env = {}
  for s in ast:
    check_statement(s, env)
  
