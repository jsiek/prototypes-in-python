from dataclasses import dataclass
import numbers
from fractions import Fraction
from typing import Any
from utilities import *

@dataclass
class Number(Value):
    value: numbers.Number
    __match_args__ = ("value",)
    def equals(self, other):
      return self.value == other.value
    def __str__(self):
      return str(self.value)
    def __repr__(self):
      return str(self)
  
@dataclass
class Boolean(Value):
    value: bool
    __match_args__ = ("value",)
    def equals(self, other):
        return self.value == other.value
    def __str__(self):
        return repr(self.value).lower()
    def __repr__(self):
        return str(self)

def to_number(val, location):
    match val:
      case Number(value):
        return value
      case _:
        error(location, 'expected an number, not ' + str(val))

def to_integer(val, location):
    match val:
      case Number(value):
        return int(value)
      case _:
        error(location, 'expected an integer, not ' + str(val))
        
def to_boolean(val, location):
    match val:
      case Boolean(value):
        return value
      case _:
        error(location, 'expected a boolean, not ' + str(val))

