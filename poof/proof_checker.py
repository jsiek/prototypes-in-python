from abstract_syntax import *
from error import error
from parser import parse, set_filename

verbose = False

def set_verbose(b):
  global verbose
  verbose = b

def get_verbose():
  global verbose
  return verbose

name_id = 0

def generate_name(name):
    global name_id
    ls = name.split('.')
    new_id = name_id
    name_id += 1
    return ls[0] + '.' + str(new_id)
  
def check_implies(loc, frm1, frm2):
  if verbose:
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


            
def instantiate(loc, allfrm, args):
  match allfrm:
    case All(loc2, vars, frm):
      if len(args) == len(vars):
        sub = {var[0]: arg for (var,arg) in zip(vars,args)}
        ret = substitute(sub, frm)
        return ret
      else:
        error(loc, 'expected ' + str(len(vars)) + ' arguments, ' \
              + 'not ' + str(len(args)))
    case _:
      error(loc, 'expected all formula to instantiate, not ' + str(allfrm))
  
def str_of_env(env):
  return '{' + ', '.join([k + ": " + str(e) for (k,e) in env.items()]) + '}'

def substitute(sub, frm):
  match frm:
    case Int(loc, value):
      return frm
    case TVar(loc, name):
      if name in sub.keys():
        ret = sub[name]
      else:
        ret = frm
    case And(loc, args):
      ret = And(loc, [substitute(sub, arg) for arg in args])
    case Or(loc, args):
      ret = Or(loc, [substitute(sub, arg) for arg in args])
    case IfThen(loc, prem, conc):
      ret = IfThen(loc, substitute(sub, prem), substitute(sub, conc))
    case All(loc, vars, frm2):
      # TODO: alpha rename
      new_vars = [(generate_name(var[0]),var[1]) for var in vars]
      ren = {var[0]: TVar(loc, new_var[0]) \
              for (var,new_var) in zip(vars, new_vars)}
      frm3 = substitute(ren, frm2)
      # new_sub = copy_dict(sub)
      # for var in vars:
      #   new_sub[var[0]] = TVar(loc,var[0])
      ret = All(loc, new_vars, substitute(sub, frm3))
    # case PrimitiveCall(loc, op, args):
    #   ret = PrimitiveCall(loc, op, [substitute(sub, arg) for arg in args])
    case Call(loc, rator, args, infix):
      ret = Call(loc, substitute(sub, rator),
                 [substitute(sub, arg) for arg in args],
                 infix)
    case _:
      error(frm.location, 'in substitute, unhandled ' + str(frm))
  # print('substitute ' + str(frm) + ' via ' + str_of_env(sub) \
  #       + '\nto ' + str(ret))
  return ret

def pattern_to_term(pat):
  match pat:
    case PatternCons(loc, constr, params):
      if len(params) > 0:
        return Call(loc, TVar(loc, constr), [TVar(loc, param) for param in params],
                    False)
      else:
        return TVar(loc, constr)
    case _:
      error(pat.location, "expected a pattern, not " + str(pat))

def rewrite(loc, formula, equation):
  (lhs, rhs) = split_equation(loc, equation)
  # print('rewrite? ' + str(formula) \
  #       + '\nlhs:     ' + str(lhs) + ' is ' + str(formula == lhs))
  if formula == lhs:
    return rhs
  match formula:
    case TVar(loc2, name):
      return formula
    case And(loc2, args):
      return And(loc2, [rewrite(loc, arg, equation) for arg in args])
    case Or(loc2, args):
      return Or(loc2, [rewrite(loc, arg, equation) for arg in args])
    case IfThen(loc2, prem, conc):
      return IfThen(loc2, rewrite(loc, prem, equation),
                    rewrite(loc, conc, equation))
    case All(loc2, vars, frm2):
      # TODO, deal with variable clash
      return All(loc2, vars, rewrite(loc, frm2, equation))
    # case PrimitiveCall(loc2, op, args):
    #   return PrimitiveCall(loc2, op,
    #                        [rewrite(loc, arg, equation) for arg in args])
    case Call(loc2, rator, args, infix):
      return Call(loc2, rewrite(loc, rator, equation),
                  [rewrite(loc, arg, equation) for arg in args],
                  infix)
    case _:
      error(loc, 'in rewrite, unhandled ' + str(formula))

def facts_to_str(env):
  result = ''
  for (x,p) in env.items():
    if isinstance(p, Formula) or isinstance(p, Term):
      result += x + ': ' + str(p) + '\n'
  return result

def check_proof(proof, env, type_env):
  if verbose:
    print('synthesize formula while checking proof') ; print('\t' + str(proof))
  ret = None
  match proof:
    case RewriteFact(loc, subject, equation_proof):
      formula = check_proof(subject, env, type_env)
      equation = check_proof(equation_proof, env, type_env)
      new_formula = rewrite(loc, formula, equation)
      return new_formula
    case PHole(loc):
      error(loc, 'unfinished proof')
    case PVar(loc, name):
      if name in env.keys():
        ret = env[name]
      else:
        error(loc, 'undefined identifier ' + name)
    case PTrue(loc):
      ret = Bool(loc, True)
    case PLet(loc, label, frm, reason, rest):
      check_proof_of(reason, frm, env, type_env)
      new_env = copy_dict(env)
      new_env[label] = frm
      ret = check_proof(rest, new_env, type_env)
    case PAnnot(loc, claim, reason):
      check_proof_of(reason, claim, env, type_env)
      ret = claim
    case PTuple(loc, pfs):
      frms = [check_proof(pf, env, type_env) for pf in pfs]
      ret = And(loc, frms)
    case ImpIntro(loc, label, prem, body):
      new_env = copy_dict(env)
      new_env[label] = prem
      conc = check_proof(body, new_env, type_env)
      ret = IfThen(loc, prem, conc)
    case AllIntro(loc, vars, body):
      formula = check_proof(body, env, type_env)
      ret = All(loc, vars, formula)
    case AllElim(loc, univ, args):
      allfrm = check_proof(univ, env, type_env)
      return instantiate(loc, allfrm, args)
    case Apply(loc, imp, arg):
      ifthen = check_proof(imp, env, type_env)
      match ifthen:
        case IfThen(loc, prem, conc):
          check_proof_of(arg, prem, env, type_env)
          ret = conc
        case _:
          error(loc, 'expected an if-then, not ' + str(ifthen))
    case PInjective(loc, eq_pf):
      formula = check_proof(eq_pf, env, type_env)
      (a,b) = split_equation(loc, formula)
      match (a,b):
        case (Call(loc2,TVar(loc3,f1),[arg1], infix1),
              Call(loc4,TVar(loc5,f2),[arg2]), infix2):
          if f1 != f2:
            error(loc, 'in injective, ' + f1 + ' ≠ ' + f2)
          if not is_constructor(f1, env):
            error(loc, 'in injective, ' + f1 + ' not a constructor')
          return mkEqual(loc, arg1, arg2)
        case _:
          error(loc, 'in injective, non-applicable formula: ' + str(formula))
    case PSymmetric(loc, eq_pf):
      frm = check_proof(eq_pf, env, type_env)
      (a,b) = split_equation(loc, frm)
      return mkEqual(loc, b, a)
    case _:
      error(proof.location, 'in check_proof, unhandled ' + str(proof))
  if verbose:
    print('\t=> ' + str(ret))
  return ret


def check_proof_of(proof, formula, env, type_env):
  if verbose:
    print('nts: ' + str(formula) + '?')
    print('\t' + str(proof))
  match proof:
    case PHole(loc):
      print('Facts:\n' + facts_to_str(env))
      error(loc, 'unfinished proof:\n' + str(formula))
    
    case PReflexive(loc):
      match formula:
        case Call(loc2, TVar(loc3, '='), [lhs, rhs], _):
          lhsNF = lhs.reduce(env)
          rhsNF = rhs.reduce(env)
          # print('reflexive: ' + str(lhsNF) + ' =? ' + str(rhsNF))
          if lhsNF != rhsNF:
            error(proof.location, 'error in proof by reflexive:\n' \
                  + str(lhsNF) + ' ≠ ' + str(rhsNF))
        case _:
          error(proof.location, 'reflexive proves an equality, not ' \
                + str(formula))
          
    case PSymmetric(loc, eq_pf):
      (a,b) = split_equation(loc, formula)
      flip_formula = mkEqual(loc, b, a)
      check_proof_of(eq_pf, flip_formula, env, type_env)

    case PTransitive(loc, eq_pf1, eq_pf2):
      (a1,c) = split_equation(loc, formula)
      eq1 = check_proof(eq_pf1, env, type_env)
      (a2,b) = split_equation(loc, eq1)
      check_proof_of(eq_pf2, mkEqual(loc, b, c), env, type_env)
      if a1 != a2:
        error(loc, 'for transitive, ' + str(a1) + ' ≠ ' + str(a2))

    case PInjective(loc, eq_pf):
      (a,b) = split_equation(loc, formula)
      flip_formula = mkEqual(loc, Call(loc, TVar(loc,'suc'), [a], False),
                             Call(loc, TVar(loc,'suc'), [b], False))
      check_proof_of(eq_pf, flip_formula, env, type_env)
        
    case AllIntro(loc, vars, body):
      match formula:
        case All(loc2, vars2, formula2):
          if len(vars) != len(vars2):
            error(proof.location, 'mismatch in number of variables')
          sub = { var2[0]: TVar(loc, var[0]) for (var,var2) in zip(vars,vars2)}
          frm2 = substitute(sub, formula2)
          new_type_env = copy_dict(type_env)
          for v in vars:
            new_type_env[v[0]] = v[1]
          check_proof_of(body, frm2, env, new_type_env)

    case ImpIntro(loc, label, None, body):
      match formula:
        case IfThen(loc, prem, conc):
          new_env = copy_dict(env)
          new_env[label] = prem
          check_proof_of(body, conc, new_env, type_env)
        case _:
          error(proof.location, 'expected proof of if-then, not ' + str(proof))
    case ImpIntro(loc, label, prem1, body):
      match formula:
        case IfThen(loc, prem2, conc):
          new_env = copy_dict(env)
          new_env[label] = prem2
          if prem1.reduce(env) != prem2.reduce(env):
            error(loc, 'mismatch in premise:\n' \
                  + str(prem1) + ' ≠ ' + str(prem2))
          check_proof_of(body, conc, new_env, type_env)
        case _:
          error(proof.location, 'expected proof of if-then, not ' + str(proof))
      
    case PLet(loc, label, frm, reason, rest):
      check_proof_of(reason, frm, env, type_env)
      new_env = copy_dict(env)
      new_env[label] = frm
      check_proof_of(rest, formula, new_env, type_env)
    case Cases(loc, subject, cases):
      sub_frm = check_proof(subject, env, type_env)
      match sub_frm:
        case Or(loc, frms):
          for (frm, (label,case)) in zip(frms, cases):
            new_env = copy_dict(env)
            new_env[label] = frm
            check_proof_of(case, formula, new_env, type_env)
        case _:
          error(proof.location, "expected 'or', not " + str(sub_frm))
    case Induction(loc, type_name, cases):
      match env[type_name]:
        case Union(loc2, name, alts):
          for (constr,indcase) in zip(alts, cases):
            #print('induction case ' + str(indcase.pattern))
            if indcase.pattern.constructor != constr.name:
              error(indcase.location, "expected a case for " + constr.name \
                    + " not " + indcase.pattern.constructor)
            if len(indcase.pattern.parameters) != len(constr.parameters):
              error(indcase.location, "expected " + len(constr.parameters) \
                    + " arguments to " + constr.name \
                    + " not " + len(indcase.pattern.parameters))
            induction_hypotheses = [instantiate(loc, formula, [TVar(loc,param)])
                                    for (param, typ) in 
                                    zip(indcase.pattern.parameters,
                                        constr.parameters)
                                    if typ.name == type_name]
            if len(induction_hypotheses) > 1:
              induction_hypotheses = And(indcase.location, induction_hypotheses)
            elif len(induction_hypotheses) == 1:
              induction_hypotheses = induction_hypotheses[0]
            new_env = copy_dict(env)
            new_env['IH'] = induction_hypotheses
            trm = pattern_to_term(indcase.pattern)
            goal = instantiate(loc, formula, [trm])
            check_proof_of(indcase.body, goal, new_env, type_env)
        case _:
          error(loc, "induction expected name of union, not " + type_name)

    case SwitchProof(loc, subject, cases):
      ty = synth_term(subject, type_env, env, None, [])
      match ty:
        case TypeName(loc2, name):
          type_name = name
        case _:
          error(loc, 'expected term of union type, not ' + str(ty))
      match env[type_name]:
        case Union(loc2, name, alts):
          for (constr,scase) in zip(alts, cases):
            if scase.pattern.constructor != constr.name:
              error(scase.location, "expected a case for " + constr.name \
                    + " not " + scase.pattern.constructor)
            if len(scase.pattern.parameters) != len(constr.parameters):
              error(scase.location, "expected " + len(constr.parameters) \
                    + " arguments to " + constr.name \
                    + " not " + len(scase.pattern.parameters))
            new_env = copy_dict(env)
            new_env['EQ'] = mkEqual(scase.location, 
                                    subject, pattern_to_term(scase.pattern))
            check_proof_of(scase.body, formula, new_env, type_env)
        case _:
          error(loc, "switch expected union type, not " + type_name)
          
    case RewriteGoal(loc, equation_proof, body):
      equation = check_proof(equation_proof, env, type_env)
      new_formula = rewrite(loc, formula, equation)
      # print('rewrite goal using equation ' + str(equation) \
      #       + '\nfrom ' + str(formula) + '\nto   ' + str(new_formula))
      check_proof_of(body, new_formula, env, type_env)
    case _:
      form = check_proof(proof, env, type_env)
      check_implies(proof.location, form.reduce(env), formula.reduce(env))


def type_check_call(loc, rator, args, type_env, env, recfun, subterms):
  ty = synth_term(rator, type_env, env, recfun, subterms)
  match ty:
    case FunctionType(loc, param_types, return_type):
      for (param_type, arg) in zip(param_types, args):
        check_term(arg, param_type, type_env, env, recfun, subterms)
      return return_type
    case _:
      error(loc, 'expected operator to have function type, not ' + str(ty))

# TODO: add env parameter
def synth_term(term, type_env, env, recfun, subterms):
  match term:
    case Int(loc, value):
      return IntType(loc)
    case Bool(loc, value):
      return BoolType(loc)
    case TVar(loc, name):
      if name in type_env.keys():
        return type_env[name]
      else:
        error(loc, 'undefined name ' + name)
    case Call(loc, TVar(loc2, name), args, infix) if name == recfun:
      # print('************* check recursive call ' + str(term))
      match args[0]:
        case TVar(loc3, arg_name):
            if not (arg_name in subterms):
              error(loc, "ill-formed recursive call, " \
                    + "expected first argument to be " \
                    + " or ".join(subterms) + ", not " + arg_name)
        case _:
          error(loc, "ill-formed recursive call, " \
                + "expected first argument to be " \
                + " or ".join(subterms) + ", not " + str(args[0]))
      return type_check_call(loc, TVar(loc2,name), args, type_env, env,
                             recfun, subterms)
    case Call(loc, rator, args, infix):
      # print('************* check non-recursive call ' + str(term))
      return type_check_call(loc, rator, args, type_env, env, recfun, subterms)
    case Switch(loc, subject, cases):
      ty = synth_term(subject, type_env, env, recfun, subterms)
      # TODO: check for completeness
      result_type = None
      for c in cases:
        new_type_env = copy_dict(type_env)
        check_pattern(c.pattern, ty, env, new_type_env)
        case_type = synth_term(c.body, new_type_env, env, recfun, subterms)
        if not result_type:
          result_type = case_type
        elif case_type != result_type:
          error(c.location, 'bodies of cases must have same type, but ' \
                + str(case_type) + ' ≠ ' + str(result_type))
        return result_type
    case _:
      error(term.location, 'cannot deduce a type for ' + str(term))
    
  
def check_term(term, typ, type_env, env, recfun, subterms):
  match term:
    # case PrimitiveCall(loc, op, args):
    #   # TODO
    #   return
    case Lambda(loc, vars, body):
      match typ:
        case FunctionType(loc, param_types, return_type):
          new_type_env = copy_dict(type_env)
          for (x,ty) in zip(vars, param_types):
            new_type_env[x] = ty
          check_term(body, return_type, new_type_env, env, recfun, subterms)
        case _:
          error(loc, 'expected a term of type ' + str(typ) + ' but instead got a lambda')
    case _:
      ty = synth_term(term, type_env, env, recfun, subterms)
      if ty != typ:
        error(term.location, 'expected term of type ' + str(typ) + ' but got ' + str(ty))

def is_constructor(constr_name, env):
  for (name,defn) in env.items():
    match defn:
      case Union(loc2, name, alts):
        for constr in alts:
          if constr.name == constr_name:
            return True
      case _:
        continue
  return False
        
def check_constructor_pattern(loc, constr_name, env, tyname, params, type_env):
  for (name,defn) in env.items():
    if name == tyname:
      match defn:
        case Union(loc2, name, alts):
          for constr in alts:
            if constr.name == constr_name:
              for (param, param_type) in zip(params, constr.parameters):
                type_env[param] = param_type
              return
        case _:
          error(loc, tyname + ' is not a union type')
  error(loc, tyname + ' is not a union type')
        
def check_pattern(pattern, typ, env, type_env):
  match pattern:
    case PatternCons(loc, constr, params):
      match typ:
        case TypeName(loc2, name):
          check_constructor_pattern(loc, constr, env, name, params, type_env)
        case _:
          error(loc, 'expected ' + str(typ) + ' not ' + constr)
    case _:
      error(pattern.location, 'expected a constructor pattern, not ' + str(pattern))
      
def check_statement(stmt, env, type_env):
  match stmt:
    case Define(loc, name, body):
      ty = synth_term(body, type_env, env, None, [])
      env[name] = body
      type_env[name] = ty
    case Theorem(loc, name, frm, pf):
      check_proof_of(pf, frm, env, type_env)
      env[name] = frm
    case RecFun(loc, name, params, returns, cases):
      type_env[name] = FunctionType(loc, params, returns)
      for fun_case in cases:
        check_pattern(fun_case.pattern, params[0], env, type_env)
        for (x,typ) in zip(fun_case.parameters, params[1:]):
          type_env[x] = typ
        check_term(fun_case.body, returns, type_env, env,
                   name, fun_case.pattern.parameters)
      env[name] = stmt
    case Union(loc, name, alts):
      # TODO: check for well-defined types in the constructor definitions
      env[name] = stmt
      for constr in alts:
        if constr.name in type_env.keys():
          error(loc, 'duplicate constructor name: ' + constr.name)
        if len(constr.parameters) > 0:
          type_env[constr.name] = FunctionType(constr.location,
                                               constr.parameters,
                                               TypeName(loc, name))
        else:
          type_env[constr.name] = TypeName(loc, name)
    case Import(loc, name):
      filename = name + ".pf"
      file = open(filename, 'r')
      src = file.read()
      set_filename(filename)
      ast = parse(src, trace=False)
      # TODO: cache the proof-checking of files
      for s in ast:
        check_statement(s, env, type_env)
      
    case _:
      error(stmt.location, "unrecognized statement:\n" + str(stmt))
      
def check_poof(ast):
  env = {}
  type_env = {}
  for s in ast:
    check_statement(s, env, type_env)
  
