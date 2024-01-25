from lark.tree import Meta
from Typing import Any

class Variable:
  location: Meta
  name: str
  index: int
  
  def increments(self):
    return Variable(self.location, self.name, self.index + 1)

  def decrement(self):
    return Variable(self.location, self.name, self.index - 1)

def increment(t):
  if isinstance(t, Variable):
    return t.increment()
  else:
    return t
  
class EnvNode:
  name: str
  value: Any
  next: EnvNode

  def __str__(self):
    return self.name + ": " + str(self.value)
  
  def lookup(var: Variable, loc: Meta):
    if var.index == 0:
      if self.value:
        return self.value
      else:
        return var
    elif self.next:
      return increment(self.next.lookup(var.decrement()))
    else:
      error(loc, 'could not find variable ' + var.name)
  
class Env:
  head: EnvNode

  def lookup(var: Variable, loc: Meta):
    if head:
      return head.lookup(var)
    else:
      error(loc, 'could not find variable ' + var.name)

  def define(name: str, value: Any):
    return Env(EnvNode(name, value, self.head))
    
  
