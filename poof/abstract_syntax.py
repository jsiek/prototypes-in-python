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

  def reduce(self):
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
    return str(self.value)

  def __eq__(self, other):
      if not isinstance(other, PrimitiveCall):
          return False
      return self.op == other.op \
          and all([arg1 == arg2 for arg1,arg2 in zip(self.args, other.args)])

  def reduce(self):
      return self

  def substitute(self, env):
      return PrimitiveCall(self.location, self.op,
                           [arg.substitute(env) for arg in self.args])
  
@dataclass
class Lambda(Term):
  vars: List[str]
  body: Term
  
  def __str__(self):
    return "λ" + ",".join([v for v in self.vars]) + "{" + str(self.body) + "}"

  def __repr__(self):
    return str(self.value)

  def __eq__(self, other):
      # to do: alpha-equivalence
      if not isinstance(other, Lambda):
          return False
      return self.vars == other.vars and self.body == other.body

  def reduce(self):
      return self

  def substitute(self, env):
      new_env = env.deepcopy()
      for p in self.vars:
          del new_env[p.ident]
      return Lambda(self.vars, self.body.substitute(new_env), name)
      
@dataclass
class Call(Term):
  rator: Term
  args: list[Term]

  def __str__(self):
    return str(self.rator) + "(" + ",".join([str(arg) for arg in self.args]) + ")"

  def __repr__(self):
    return str(self.value)

  def __eq__(self, other):
      if not isinstance(other, Call):
          return False
      return self.rator == other.rator \
          and all([arg1 == arg2 for arg1,arg2 in zip(self.args, other.args)])

  def reduce(self):
      fun = self.rator.reduce()
      args = [arg.reduce() for arg in self.args]
      match fun:
        case Lambda(loc,vars, body):
          return body.substitute({x:arg for (x,arg) in zip(vars, args)})
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
    return str(self.value)

@dataclass
class And(Formula):
  args: list[Formula]
  def __str__(self):
    return ' and '.join([str(arg) for arg in self.args])
  def __repr__(self):
    return str(self.value)

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
class Tuple(Proof):
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
    
