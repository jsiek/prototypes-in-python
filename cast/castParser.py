import sys
sys.path.append('..')
sys.path.append('../lam')
import parser
from abstract_syntax import *
from ast_types import *
from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
from lark import Lark, Token, logger
from cast_ast import *

from lark import logger
import logging
#logger.setLevel(logging.DEBUG)

##################################################
# Concrete Syntax Parser
##################################################

lark_parser = Lark(open("./Cast.lark").read(), start='program', parser='lalr',
                   debug=True, propagate_positions=True)

##################################################
# Parsing Concrete to Abstract Syntax
##################################################

class CastParser(parser.Parser):

  def __init__(self, prefix=''):
      self.castPrefix = prefix
      super().__init__('lambda__')
    
  def parse_tree_to_type(self, e):
      e.meta.filename = filename
      if e.data == self.castPrefix + 'dyn_type':
          return DynType(e.meta)
      else:
          return super().parse_tree_to_type(e)
          
  def parse_tree_to_ast(self, e):
      e.meta.filename = parser.get_filename()
      if e.data == self.castPrefix + 'cast':
          return Cast(e.meta,
                      self.parse_tree_to_ast(e.children[0]),
                      self.parse_tree_to_type(e.children[1]))
      else:
          return super().parse_tree_to_ast(e)

def parse(s, trace = False):
    lexed = lark_parser.lex(s)
    if trace:
        print('tokens: ')
        for word in lexed:
            print(repr(word))
        print('')
    parse_tree = lark_parser.parse(s)
    if trace:
        print('parse tree: ')
        print(parse_tree)
        print('')
    ast = CastParser().parse_tree_to_ast(parse_tree)
    if trace:
        print('abstract syntax tree: ')
        print(ast)
        print('')
    return ast

if __name__ == "__main__":
    filename = sys.argv[1]
    parser.set_filename(filename)
    file = open(filename, 'r')
    p = file.read()
    ast = parse(p, trace=True)
    print(str(ast))
