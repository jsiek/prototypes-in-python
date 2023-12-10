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
class TVar(Term):
  name: str

  def __eq__(self, other):
      return self.name == other.name
  
  def __str__(self):
      return self.name
  
@dataclass
class Int(Term):
  value: int

  def __str__(self):
    return str(self.value)

@dataclass
class PrimitiveCall(Term):
    op: str
    args: list[Term]

@dataclass
class Bool(Formula):
  value: bool
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

@dataclass
class Compare(Formula):
  op: str
  args: list[Term]
  def __str__(self):
      return str(self.args[0]) + ' ' + self.op + ' ' + str(self.args[1])
  
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
    return 'all ' + ",".join(self.vars) + '.' + str(self.body)

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
    return 'suppose ' + str(self.label) + ':' + str(self.premise) + '{' + str(self.body) + '}'

@dataclass
class AllIntro(Proof):
  vars: List[str]
  body: Proof

  def __str__(self):
    return 'arbitrary ' + str(self.vars) + '{' + str(self.body) + '}'

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
      return 'refl'
  
@dataclass
class Theorem(Statement):
    name: str
    what: Formula
    proof: Proof

    def __str__(self):
      return 'theorem ' + self.name

    def __repr__(self):
      return 'theorem ' + self.name
    
