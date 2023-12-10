from abstract_syntax import *
from error import error

def check_implies(loc, frm1, frm2):
  print('check_implies? ' + str(frm1) + ' => ' + str(frm2))
  match frm2:
    case Bool(loc, True):
      return
    case And(loc, args):
      for arg2 in args:
        check_implies(loc, frm1, arg2)
    case Or(loc, args):
      for arg2 in args:
        try:
          check_implies(loc, frm1, arg2)
          return
        except Exception as e:
          continue
      error(loc, 'expected ' + str(frm2) + '\nbut only have ' + str(frm1))
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
          return
        case And(loc, args1):
          for arg1 in args1:
            try:
              check_implies(loc, arg1, frm2)
              return
            except Exception as e:
              continue
          error(loc, 'expected ' + str(frm2) + '\nbut only have ' + str(frm1))
        case _:
          if frm1 != frm2:
            error(loc, 'expected ' + str(frm2) + '\nbut only have ' + str(frm1))

def check_proof(proof, env):
  print('synthesize')
  print('\t' + str(proof))
  ret = None
  match proof:
    case PVar(loc, name):
      ret = env[name]
    case PTrue(loc):
      ret = Bool(loc, True)
    case PLet(loc, label, frm, reason, rest):
      check_proof_of(reason, frm, env)
      new_env = {l: f for (l,f) in env.items()}
      new_env[label] = frm
      ret = check_proof(rest, new_env)
    case Tuple(loc, pfs):
      frms = [check_proof(pf, env) for pf in pfs]
      ret = And(loc, frms)
    case ImpIntro(loc, label, prem, body):
      new_env = {l: f for (l,f) in env.items()}
      new_env[label] = prem
      conc = check_proof(body, new_env)
      ret = IfThen(loc, prem, conc)
    case AllIntro(loc, vars, body):
      # TODO, deal with vars
      formula = check_proof(body, env)
      ret = All(loc, vars, formula)
    case Apply(loc, imp, arg):
      ifthen = check_proof(imp, env)
      match ifthen:
        case IfThen(loc, prem, conc):
          check_proof_of(arg, prem, env)
          ret = conc
        case _:
          error(loc, 'expected an if-then, not ' + str(ifthen))
    case _:
      error(proof.location, 'unhandled ' + str(proof))
  print('\t=> ' + str(ret))
  return ret

def check_proof_of(proof, formula, env):
  print('nts: ' + str(formula) + '?')
  print('\t' + str(proof))
  match proof:
    case PReflexive(loc):
      match formula:
        case Compare(loc2, '=', [lhs, rhs]):
          if lhs != rhs:
            error(proof.location, str(lhs) + ' != ' + str(rhs))
        case _:
          error(proof.location, 'refl proves an equality, not ' + str(formula))
    case AllIntro(loc, vars, body):
      match formula:
        case All(loc2, vars2, formula2):
          if len(vars) != len(vars2):
            error(proof.location, 'mismatch in number of variables')
          check_proof_of(body, formula2, env)

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
    case Cases(loc, subject, cases):
      sub_frm = check_proof(subject, env)
      match sub_frm:
        case Or(loc, frms):
          for (frm, (label,case)) in zip(frms, cases):
            new_env = {l: f for (l,f) in env.items()}
            new_env[label] = frm
            check_proof_of(case, formula, new_env)
        case _:
          error(proof.location, "expected 'or', not " + str(sub_frm))
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
  
