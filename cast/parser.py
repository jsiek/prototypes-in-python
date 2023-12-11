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

from lark import logger
import logging
#logger.setLevel(logging.DEBUG)

filename = '???'

def set_filename(fname):
    global filename
    filename = fname

##################################################
# Concrete Syntax Parser
##################################################

lark_parser = Lark(open("./Cast.lark").read(), start='program', parser='lalr',
                   debug=True, propagate_positions=True)

##################################################
# Parsing Concrete to Abstract Syntax
##################################################

class Parser(parser.Parser):
  pass  

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
    return parse_tree
    # ast = parse_tree_to_ast(parse_tree)
    # if trace:
    #     print('abstract syntax tree: ')
    #     print(ast)
    #     print('')
    # return ast

if __name__ == "__main__":
    filename = sys.argv[1]
    file = open(filename, 'r')
    p = file.read()
    ast = parse(p, trace=True)
    #print(str(ast))
