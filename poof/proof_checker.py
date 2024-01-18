from abstract_syntax import *
from error import error

def check_implies(loc, frm1, frm2):
  # print('check_implies? ' + str(frm1) + ' => ' + str(frm2))
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
    case PAnnot(loc, claim, reason):
      check_proof_of(reason, claim, env)
      ret = claim
    case PTuple(loc, pfs):
      frms = [check_proof(pf, env) for pf in pfs]
      ret = And(loc, frms)
    case ImpIntro(loc, label, prem, body):
      new_env = {l: f for (l,f) in env.items()}
      new_env[label] = prem
      conc = check_proof(body, new_env)
      ret = IfThen(loc, prem, conc)
    case AllIntro(loc, vars, body):
      formula = check_proof(body, env)
      ret = All(loc, vars, formula)
    case AllElim(loc, univ, args):
      allfrm = check_proof(univ, env)
      match allfrm:
        case All(loc, vars, frm):
          if len(args) == len(vars):
            return substitute({var: arg for (var,arg) in zip(vars,args)}, frm)
          else:
            error(loc, 'expected ' + len(vars) + ' arguments, not ' + len(args))
        case _:
          error(loc, 'expected all formula to instantiate, not ' + str(allfrm))
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
  #print('\t=> ' + str(ret))
  return ret

def substitute(sub, frm):
  match frm:
    case TVar(loc, name):
      if name in sub.keys():
        return sub[name]
      else:
        return frm
    case And(loc, args):
      return And(loc, [substitute(sub, arg) for arg in args])
    case Or(loc, args):
      return Or(loc, [substitute(sub, arg) for arg in args])
    case IfThen(loc, prem, conc):
      return IfThen(loc, substitute(sub, prem), substitute(sub, conc))
    case All(loc, vars, frm2):
      new_sub = {x:e for (x,e) in sub.items()}
      for var in vars:
        new_sub[var] = TVar(loc,var)
      return All(loc, vars, substitute(new_sub, frm2))
    case PrimitiveCall(loc, op, args):
      return PrimitiveCall(loc, op, [substitute(sub, arg) for arg in args])
    case _:
      return frm

def check_proof_of(proof, formula, env):
  print('nts: ' + str(formula) + '?')
  print('\t' + str(proof))
  match proof:
    case PReflexive(loc):
      match formula:
        case PrimitiveCall(loc2, 'equal', [lhs, rhs]):
          lhsNF = lhs.reduce(env)
          rhsNF = rhs.reduce(env)
          # print('reflexive: ' + str(lhsNF) + ' =? ' + str(rhsNF))
          if lhsNF != rhsNF:
            error(proof.location, str(lhsNF) + ' != ' + str(rhsNF))
        case _:
          error(proof.location, 'reflexive proves an equality, not ' + str(formula))
    case AllIntro(loc, vars, body):
      match formula:
        case All(loc2, vars2, formula2):
          if len(vars) != len(vars2):
            error(proof.location, 'mismatch in number of variables')
          sub = { var2: TVar(loc, var) for (var,var2) in zip(vars,vars2)}
          frm2 = substitute(sub, formula2)
          check_proof_of(body, frm2, env)

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
    case RecFun(loc, name, params, returns, cases):
      env[name] = stmt
    
def check_poof(ast):
  env = {}
  for s in ast:
    check_statement(s, env)
  
