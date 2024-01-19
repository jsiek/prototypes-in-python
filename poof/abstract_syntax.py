from dataclasses import dataclass
from lark.tree import Meta
from typing import Any, Tuple, List

@dataclass
class AST:
    location: Meta

@dataclass
class Term(AST):
    pass

@dataclass
class Formula(AST):
    pass

@dataclass
class Proof(AST):
    pass

@dataclass
class Statement(AST):
    pass

@dataclass
class Type(AST):
    pass

################ Types ######################################

@dataclass
class TypeName(Type):
  name: str
  
  def __str__(self):
    return self.name

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
    if not isinstance(other, TypeName):
      return False
    return self.name == other.name


@dataclass
class IntType(Type):
    pass

@dataclass
class BoolType(Type):
    pass

@dataclass
class FunctionType(Type):
    param_types: List[Type]
    return_type: Type

################ Terms ######################################

@dataclass
class TVar(Term):
  name: str

  def __eq__(self, other):
      if not isinstance(other, TVar):
          return False
      return self.name == other.name
  
  def __str__(self):
      return self.name

  def reduce(self, env):
      if self.name in env:
          return env[self.name]
      else:
          return self
  
  def substitute(self, env):
      if self.name in env.keys():
          return env[self.name]
      else:
          return self
  
@dataclass
class Int(Term):
  value: int

  def __eq__(self, other):
      if not isinstance(other, Int):
          return False
      return self.value == other.value
  
  def __str__(self):
    return str(self.value)

  def reduce(self, env):
      return self

  def substitute(self, env):
      return self
  
@dataclass
class PrimitiveCall(Term):
  op: str
  args: list[Term]

  def __str__(self):
    return self.op + "(" + ",".join([str(arg) for arg in self.args]) + ")"

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
      if not isinstance(other, PrimitiveCall):
          return False
      return self.op == other.op \
          and all([arg1 == arg2 for arg1,arg2 in zip(self.args, other.args)])

  def reduce(self, env):
      return self

  def substitute(self, env):
      return PrimitiveCall(self.location, self.op,
                           [arg.substitute(env) for arg in self.args])

@dataclass
class FieldAccess(Term):
  subject: Term
  field: str

  def __str__(self):
      return str(self.subject) + "." + self.field

  def __repr__(self):
    return str(self)

  def reduce(self, env):
      # TODO
      return self

  def substitute(self, env):
    return FieldAccess(self.location, self.subject, self.field)

@dataclass
class Lambda(Term):
  vars: List[str]
  body: Term
  
  def __str__(self):
    return "λ" + ",".join([v for v in self.vars]) + "{" + str(self.body) + "}"

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
      # to do: alpha-equivalence
      if not isinstance(other, Lambda):
          return False
      return self.vars == other.vars and self.body == other.body

  def reduce(self, env):
      return self

  def substitute(self, env):
      new_env = env.deepcopy()
      for p in self.vars:
          del new_env[p.ident]
      return Lambda(self.vars, self.body.substitute(new_env), name)

def is_match(pattern, arg, subst):
    ret = False
    match (pattern, arg):
      case (PatternCons(loc1, constr, []),
            TVar(loc2, name)):
        ret = constr == name
      case (PatternCons(loc1, constr, params),
            Call(loc2, TVar(loc3, name), args)):
        if constr == name and len(params) == len(args):
            for (k,v) in zip(params, args):
                subst[k] = v
            ret = True
        else:
            ret = False
      case _:
        ret = False
    return ret
        
@dataclass
class Call(Term):
  rator: Term
  args: list[Term]

  def __str__(self):
    return str(self.rator) + "(" + ",".join([str(arg) for arg in self.args]) + ")"

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
      if not isinstance(other, Call):
          return False
      return self.rator == other.rator \
          and all([arg1 == arg2 for arg1,arg2 in zip(self.args, other.args)])

  def reduce(self, env):
      fun = self.rator.reduce(env)
      args = [arg.reduce(env) for arg in self.args]
      match fun:
        case Lambda(loc,vars, body):
          return body.substitute({x:arg for (x,arg) in zip(vars, args)})
        case RecFun(loc, name, params, returns, cases):
          first_arg = args[0]
          rest_args = args[1:]
          for fun_case in cases:
              subst = {}
              if is_match(fun_case.pattern, first_arg, subst):
                  for (k,v) in zip(fun_case.parameters, rest_args):
                      subst[k] = v
                  return fun_case.body.substitute(subst).reduce(env)
          return Call(self.location, fun, args)
        case _:
          return Call(self.location, fun, args)

  def substitute(self, env):
      return Call(self.location, self.rator.substitute(env),
                  [arg.substitute(env) for arg in self.args])

################ Formulas ######################################
  
@dataclass
class Bool(Formula):
  value: bool
  def __eq__(self, other):
      return self.value == other.value
  def __str__(self):
    return str(self.value)
  def __repr__(self):
    return str(self)

@dataclass
class And(Formula):
  args: list[Formula]
  def __str__(self):
    return ' and '.join([str(arg) for arg in self.args])
  def __repr__(self):
    return str(self)

@dataclass
class Or(Formula):
  args: list[Formula]
  def __str__(self):
    return ' or '.join([str(arg) for arg in self.args])

# @dataclass
# class Compare(Formula):
#   op: str
#   args: list[Term]
#   def __str__(self):
#       return str(self.args[0]) + ' ' + self.op + ' ' + str(self.args[1])
  
@dataclass
class IfThen(Formula):
  premise: Formula
  conclusion : Formula
  def __str__(self):
    return 'if ' + str(self.premise) + ' then ' + str(self.conclusion)
  def __repr__(self):
    return str(self)

@dataclass
class All(Formula):
  vars: list[str]
  body: Formula

  def __str__(self):
    return 'all ' + ",".join(self.vars) + '. ' + str(self.body)

@dataclass
class Some(Formula):
  vars: list[str]
  body: Formula

@dataclass
class PVar(Proof):
  name: str

  def __str__(self):
      return str(self.name)
  
@dataclass
class PLet(Proof):
  label: str
  proved: Formula
  because: Proof
  body: Proof

  def __str__(self):
      return self.label + ': ' + str(self.proved) + ' because ' + str(self.because) + '; ' + str(self.body)

@dataclass
class PAnnot(Proof):
  claim: Formula
  reason: Proof

  def __str__(self):
      return 'have ' + str(self.claim) + ' because ' + str(self.reason)
  
@dataclass
class Cases(Proof):
  subject: Proof
  cases: List[Tuple[str,Proof]]

@dataclass
class Apply(Proof):
  implication: Proof
  arg: Proof

  def __str__(self):
      return 'apply ' + str(self.implication) + ' with ' + str(self.arg)

@dataclass
class ImpIntro(Proof):
  label: str
  premise: Formula
  body: Proof

  def __str__(self):
    return 'suppose ' + str(self.label) + ': ' + str(self.premise) + '{' + str(self.body) + '}'

@dataclass
class AllIntro(Proof):
  vars: List[str]
  body: Proof

  def __str__(self):
    return 'arbitrary ' + str(self.vars) + '{' + str(self.body) + '}'

@dataclass
class AllElim(Proof):
  univ: Proof
  args: List[Term]

  def __str__(self):
    return str(self.univ) + '[' + ','.join([str(arg) for arg in self.args]) + ']'


@dataclass
class PTuple(Proof):
  args: List[Proof]

  def __str__(self):
    return ', '.join([str(arg) for arg in self.args])
  
@dataclass
class PTrue(Proof):
  def __str__(self):
      return '.'

@dataclass
class PReflexive(Proof):
  def __str__(self):
      return 'reflexive'
  
@dataclass
class Theorem(Statement):
    name: str
    what: Formula
    proof: Proof

    def __str__(self):
      return 'theorem ' + self.name + ': ' + str(self.what) + '\nbegin\n' \
          + str(self.proof) + '\nend\n'

    def __repr__(self):
      return str(self)
    
@dataclass
class Constructor(Statement):
    name: str
    parameters: List[Type]
    
@dataclass
class Union(Statement):
    name: str
    alternatives: List[Constructor]

@dataclass
class Pattern(AST):
    pass

@dataclass
class PatternCons(Pattern):
  constructor : str
  parameters : List[str]

  def __str__(self):
      return self.constructor + '(' + ",".join(self.parameters) + ')'

  def __repr__(self):
      return str(self)
  
@dataclass
class FunCase(AST):
  pattern: Pattern
  parameters: List[str]
  body: Term

  def __str__(self):
      return '(' + str(self.pattern) + ',' + ",".join(self.parameters) \
          + ') = ' + str(self.body)

  def __repr__(self):
      return str(self)
  
@dataclass
class RecFun(Statement):
    name: str
    params: List[Type]
    returns: Type
    cases: List[FunCase]

    def __str__(self):
      return '`' + self.name + '`'

    def __repr__(self):
      return str(self)
    
@dataclass
class Define(Statement):
  name: str
  body: Term
