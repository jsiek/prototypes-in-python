from abstract_syntax import *
from dataclasses import dataclass
from lark import Lark, Token, logger
import sys

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

lark_parser = Lark(open("./Poof.lark").read(), start='program', parser='lalr',
                   debug=True, propagate_positions=True)

##################################################
# Parsing Concrete to Abstract Syntax
##################################################

def parse_tree_to_list(e):
    if e.data == 'empty':
        return tuple([])
    elif e.data == 'single':
        return tuple([parse_tree_to_ast(e.children[0])])
    elif e.data == 'push':
        return tuple([parse_tree_to_ast(e.children[0])]) \
            + parse_tree_to_list(e.children[1])
    else:
        raise Exception('parse_tree_to_str_list, unexpected ' + str(e))
    
def parse_tree_to_formula(e):
    e.meta.filename = filename
    if e.data == 'nothing':
        return None
    elif e.data == 'true_formula':
        return Bool(e.meta, True)
    elif e.data == 'false_formula':
        return Bool(e.meta, False)
    elif e.data == 'comparison_formula':
        return e
    elif e.data == 'if_then_formula':
       return IfThen(e.meta,
                     parse_tree_to_formula(e.children[0]),
                     parse_tree_to_formula(e.children[1]))
    elif e.data == 'all_formula':
        return All(e.meta,
                   parse_tree_to_list(e.children[0]),
                   parse_tree_to_formula(e.children[1]))
    elif e.data == 'some_formula':
        return Some(e.meta,
                   parse_tree_to_list(e.children[0]),
                   parse_tree_to_formula(e.children[1]))
    else:
        raise Exception('unrecognized type annotation ' + repr(e))
    


def parse_tree_to_case(e):
    tag = str(e.children[0].value)
    body = parse_tree_to_ast(e.children[1])
    return (tag, body)

def parse_tree_to_case_list(e):
    if e.data == 'single':
        return (parse_tree_to_case(e.children[0]),)
    elif e.data == 'push':
        return (parse_tree_to_case(e.children[0]),) \
            + parse_tree_to_case_list(e.children[1])
    else:
        raise Exception('unrecognized as a type list ' + repr(e))
    
primitive_ops = {'add', 'sub', 'mul', 'div', 'int_div', 'mod', 'neg', 'sqrt',
                 'and', 'or', 'not',
                 'equal', 'not_equal',
                 'less', 'greater', 'less_equal', 'greater_equal'}

impl_num = 0
def next_impl_num():
    global impl_num
    ret = impl_num
    impl_num += 1
    return ret
    
def parse_tree_to_ast(e):
    e.meta.filename = filename
    # terms
    if e.data == 'term_var':
        return TVar(e.meta, str(e.children[0].value))
    elif e.data == 'int':
        return Int(e.meta, int(e.children[0]))
    elif e.data in primitive_ops:
        return PrimitiveCall(e.meta, e.data,
                             [parse_tree_to_ast(c) for c in e.children])
    # formulas
    elif e.data == 'true':
        return Bool(e.meta, True)
    elif e.data == 'false':
        return Bool(e.meta, False)
    
    # proofs
    if e.data == 'proof_var':
        return PVar(e.meta, str(e.children[0].value))
    elif e.data == 'apply':
        e1, e2 = e.children
        return Apply(e.meta, parse_tree_to_ast(e1), parse_tree_to_ast(e2))
    elif e.data == 'true_proof':
        return PTrue(e.meta)
    elif e.data == 'paren':
        return parse_tree_to_ast(e.children[0])
    elif e.data == 'let':
        return PLet(e.meta,
                    str(e.children[0].value),
                    parse_tree_to_formula(e.children[1]),
                    parse_tree_to_ast(e.children[2]),
                    parse_tree_to_ast(e.children[3]))
    elif e.data == 'cases':
        return Cases(e.meta,
                     parse_tree_to_ast(e.children[0]),
                     parse_tree_to_case_list(e.children[1]))

    # lists
    elif e.data == 'single':
        return [parse_tree_to_ast(e.children[0])]
    elif e.data == 'push':
        return [parse_tree_to_ast(e.children[0])] \
            + parse_tree_to_ast(e.children[1])
    elif e.data == 'empty':
        return []

    elif e.data == 'theorem':
        return Theorem(e.meta,
                       str(e.children[0].value),
                       parse_tree_to_formula(e.children[1]),
                       parse_tree_to_ast(e.children[2]))
    # whole program
    elif e.data == 'program':
        return parse_tree_to_list(e.children[0])
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
    ast = parse_tree_to_ast(parse_tree)
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

