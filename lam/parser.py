from abstract_syntax import *
from ast_types import *
from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
import sys
sys.path.append('..')
from lark import Lark, Token, logger

from lark import logger
import logging
#logger.setLevel(logging.DEBUG)

filename = '???'

def set_filename(fname):
    global filename
    filename = fname

def get_filename():
    global filename
    return filename
    
##################################################
# Concrete Syntax Parser
##################################################

lark_parser = Lark(open("./Lambda.lark").read(), start='program', parser='lalr',
                   debug=True, propagate_positions=True)

##################################################
# Parsing Concrete to Abstract Syntax
##################################################

impl_num = 0

def next_impl_num():
    global impl_num
    ret = impl_num
    impl_num += 1
    return ret


class Parser:

  def __init__(self, prefix):
      self.prefix = prefix
    
  def primitive_ops(self):
      return {'add', 'sub', 'mul', 'div', 'int_div', 'mod', 'neg', 'sqrt',
              'and', 'or', 'not',
              'equal', 'not_equal',
              'less', 'greater', 'less_equal', 'greater_equal'}

  def parse_tree_to_list(self, e):
      if e.data == 'empty':
          return tuple([])
      elif e.data == 'single':
          return tuple([self.parse_tree_to_ast(e.children[0])])
      elif e.data == 'push':
          return tuple([self.parse_tree_to_ast(e.children[0])]) \
              + self.parse_tree_to_list(e.children[1])
      else:
          raise Exception('parse_tree_to_list, unexpected ' + str(e))
      
  def parse_tree_to_type(self, e):
      e.meta.filename = filename
      if e.data == 'nothing':
          return None
      elif e.data == self.prefix + 'int_type':
          return IntType(e.meta)
      elif e.data == self.prefix + 'bool_type':
          return BoolType(e.meta)
      elif e.data == self.prefix + 'tuple_type':
          return TupleType(e.meta,
                           self.parse_tree_to_type_list(e.children[0]))
      elif e.data == self.prefix + 'function_type':
         return FunctionType(e.meta,
                             tuple(), # TODO: add type parameters
                             self.parse_tree_to_param_type_list(e.children[0]),
                             self.parse_tree_to_type(e.children[1]),
                             tuple()) # TODO: add requirements
      elif e.data == self.prefix + 'variant_type':
          return VariantType(e.meta,
                             self.parse_tree_to_alt_list(e.children[0]))
      else:
          raise Exception('unrecognized type annotation ' + repr(e))

  def parse_tree_to_type_list(self, e):
      e.meta.filename = filename
      if e.data == 'empty':
          return ()
      elif e.data == 'single':
          return (self.parse_tree_to_type(e.children[0]),)
      elif e.data == 'push':
          return (self.parse_tree_to_type(e.children[0]),) \
              + self.parse_tree_to_type_list(e.children[1])
      else:
          raise Exception('unrecognized as a type list ' + repr(e))

  def parse_tree_to_param_type_list(self, e):
      e.meta.filename = filename
      if e.data == 'empty':
          return ()
      elif e.data == 'single':
          kind = str(e.children[0].data)
          ty = self.parse_tree_to_type(e.children[1])
          return ((kind, ty) ,)
      elif e.data == 'push':
          kind = str(e.children[0].data)
          ty = self.parse_tree_to_type(e.children[1])
          return ((kind, ty),) \
              + self.parse_tree_to_param_type_list(e.children[2])
      else:
          raise Exception('unrecognized as a type list ' + repr(e))

  def parse_tree_to_alt(self, e):
      return (str(e.children[0].value),
              self.parse_tree_to_type(e.children[1]))

  def parse_tree_to_alt_list(self, e):
      if e.data == 'empty':
          return ()
      elif e.data == 'single':
          return (self, parse_tree_to_alt(e.children[0]),)
      elif e.data == 'push':
          return (self.parse_tree_to_alt(e.children[0]),) \
              + self.parse_tree_to_alt_list(e.children[1])
      else:
          raise Exception('unrecognized as a type list ' + repr(e))

  def parse_tree_to_param(self, e):
    e.meta.filename = filename
    if e.data == 'empty' or e.data == 'nothing':
      return []
    elif e.data == 'just':
      return self.parse_tree_to_param(e.children[0])
    elif e.data == 'single':
      return [self.parse_tree_to_param(e.children[0])]
    elif e.data == 'push':
      return [self.parse_tree_to_param(e.children[0])] \
        + self.parse_tree_to_param(e.children[1])
    elif e.data == 'binding':
      return Param(e.meta, e.children[0].value,
                   self.parse_tree_to_type(e.children[1]))
    else:    
      raise Exception('unrecognized parameter ' + repr(e))

  def parse_tree_to_case(self, e):
      tag = str(e.children[0].value)
      var = self.parse_tree_to_param(e.children[1])
      body = self.parse_tree_to_ast(e.children[2])
      return (tag, var, body)

  def parse_tree_to_case_list(self, e):
      if e.data == 'single':
          return (self.parse_tree_to_case(e.children[0]),)
      elif e.data == 'push':
          return (self.parse_tree_to_case(e.children[0]),) \
              + self.parse_tree_to_case_list(e.children[1])
      else:
          raise Exception('unrecognized as a type list ' + repr(e))

  def parse_tree_to_ast(self, e):
      e.meta.filename = filename
      # expressions
      if e.data == 'var':
          return Var(e.meta, str(e.children[0].value))
      elif e.data == self.prefix + 'int':
          return Int(e.meta, int(e.children[0]))
      elif e.data == 'true':
          return Bool(e.meta, True)
      elif e.data == 'false':
          return Bool(e.meta, False)
      elif e.data in self.primitive_ops():
          return PrimitiveCall(e.meta, e.data,
                               [self.parse_tree_to_ast(c) for c in e.children])
      elif e.data == 'tuple':
          return TupleExp(e.meta, self.parse_tree_to_ast(e.children[0]))
      elif e.data == 'lambda':
          return Lambda(e.meta,
                        self.parse_tree_to_param(e.children[0]),
                        self.parse_tree_to_ast(e.children[1]),
                        'lambda')
      elif e.data == 'call':
          e1, e2 = e.children
          return Call(e.meta, self.parse_tree_to_ast(e1), self.parse_tree_to_ast(e2))
      elif e.data == 'index':
          e1, e2 = e.children
          return Index(e.meta, self.parse_tree_to_ast(e1), self.parse_tree_to_ast(e2))
      elif e.data == 'paren':
          return self.parse_tree_to_ast(e.children[0])
      elif e.data == 'variant_member':
          return VariantMember(e.meta,
                               self.parse_tree_to_ast(e.children[0]),
                               str(e.children[1].value))
      elif e.data == 'condition':
          return IfExp(e.meta,
                       self.parse_tree_to_ast(e.children[0]),
                       self.parse_tree_to_ast(e.children[1]),
                       self.parse_tree_to_ast(e.children[2]))
      elif e.data == 'let_exp':
          return LetExp(e.meta,
                        Param(e.meta, e.children[0].value,
                              self.parse_tree_to_type(e.children[1])),
                        self.parse_tree_to_ast(e.children[2]),
                        self.parse_tree_to_ast(e.children[3]))
      elif e.data == 'tag_variant':
          return TagVariant(e.meta,
                            str(e.children[0].value),
                            self.parse_tree_to_ast(e.children[1]),
                            self.parse_tree_to_type(e.children[2]))

      elif e.data == 'match':
          return Match(e.meta,
                       self.parse_tree_to_ast(e.children[0]),
                       self.parse_tree_to_case_list(e.children[1]))

      # lists
      elif e.data == 'single':
          return [self.parse_tree_to_ast(e.children[0])]
      elif e.data == 'push':
          return [self.parse_tree_to_ast(e.children[0])] \
              + self.parse_tree_to_ast(e.children[1])
      elif e.data == 'empty':
          return []
      # whole program
      elif e.data == 'program':
          return self.parse_tree_to_ast(e.children[0])
      else:
          raise Exception('unhandled parse tree', e)

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
    ast = Parser().parse_tree_to_ast(parse_tree)
    if trace:
        print('abstract syntax tree: ')
        print(ast)
        print('')
    return ast

if __name__ == "__main__":
    filename = sys.argv[1]
    file = open(filename, 'r')
    p = file.read()
    ast = parse(p)
    print(str(ast))
