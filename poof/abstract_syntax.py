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
  
@dataclass
class Int(Term):
  value: int

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

@dataclass
class Compare(Formula):
  op: str
  args: list[Term]
  
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

@dataclass
class Some(Formula):
  vars: list[str]
  body: Formula

@dataclass
class PVar(Proof):
  name: str

@dataclass
class PLet(Proof):
  label: str
  proved: Formula
  because: Proof
  body: Proof
  
@dataclass
class Cases(Proof):
  cases: List[Tuple[str,Proof]]

@dataclass
class Apply(Proof):
  implication: Proof
  arg: Proof

@dataclass
class ImpIntro(Proof):
  label: str
  premise: Formula
  body: Proof
  
@dataclass
class Tuple(Proof):
  args: List[Proof]

@dataclass
class PTrue(Proof):
  pass
  
@dataclass
class Theorem(Statement):
    name: str
    what: Formula
    proof: Proof

    def __str__(self):
      return 'theorem ' + self.name

    def __repr__(self):
      return 'theorem ' + self.name
    
