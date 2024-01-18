from abstract_syntax import *
from dataclasses import dataclass
from lark import Lark, Token, Tree, logger
from proof_checker import check_poof
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

def parse_tree_to_str_list(e):
    if e.data == 'empty':
        return tuple([])
    elif e.data == 'single':
        return tuple([str(e.children[0].value)])
    elif e.data == 'push':
        return tuple([str(e.children[0].value)]) \
            + parse_tree_to_str_list(e.children[1])
    else:
        raise Exception('parse_tree_to_str_list, unexpected ' + str(e))

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

def extract_and(frm):
    match frm:
      case And(loc, args):
        return args
      case _:
       return [frm]

def extract_or(frm):
    match frm:
      case Or(loc, args):
        return args
      case _:
       return [frm]

def parse_tree_to_formula(e):
    e.meta.filename = filename
    if e.data == 'nothing':
        return None
    elif e.data == 'true_formula':
        return Bool(e.meta, True)
    elif e.data == 'false_formula':
        return Bool(e.meta, False)
    elif e.data == 'term_formula':
        return parse_tree_to_ast(e.children[0])
    elif e.data == 'if_then_formula':
       return IfThen(e.meta,
                     parse_tree_to_formula(e.children[0]),
                     parse_tree_to_formula(e.children[1]))
    elif e.data == 'and_formula':
       left = parse_tree_to_formula(e.children[0])
       right = parse_tree_to_formula(e.children[1])
       return And(e.meta, extract_and(left) + extract_and(right))
    elif e.data == 'or_formula':
       left = parse_tree_to_formula(e.children[0])
       right = parse_tree_to_formula(e.children[1])
       return Or(e.meta, extract_or(left) + extract_or(right))
    elif e.data == 'all_formula':
        return All(e.meta,
                   parse_tree_to_str_list(e.children[0]),
                   parse_tree_to_formula(e.children[1]))
    elif e.data == 'some_formula':
        return Some(e.meta,
                   parse_tree_to_list(e.children[0]),
                   parse_tree_to_formula(e.children[1]))
    else:
        raise Exception('unrecognized formula ' + repr(e))
    


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
    
def extract_tuple(pf):
    match pf:
      case PTuple(loc, pfs):
        return pfs
      case _:
       return [pf]
   
def parse_tree_to_ast(e):
    if isinstance(e, Token):
        return e
    
    e.meta.filename = filename
    
    # types
    if e.data == 'type_name':
      return TypeName(e.meta, str(e.children[0].value))
    elif e.data == 'int_type':
      return IntType(e.meta)
    elif e.data == 'bool_type':
      return BoolType(e.meta)
    elif e.data == 'function_type':
      return FunctionType(e.meta,
                          parse_tree_to_list(e.children[0]),
                          parse_tree_to_ast(e.children[1]))
    # terms
    elif e.data == 'term_var':
        return TVar(e.meta, str(e.children[0].value))
    elif e.data == 'int':
        return Int(e.meta, int(e.children[0]))
    elif e.data == 'field_access':
        subject = parse_tree_to_ast(e.children[0])
        field_name = str(e.children[1].value)
        return FieldAccess(e.meta, subject, field_name)
    elif e.data == 'call':
        rator = parse_tree_to_ast(e.children[0])
        rands = parse_tree_to_list(e.children[1])
        return Call(e.meta, rator, rands)
    elif e.data == 'lambda':
        return Lambda(e.meta,
                      parse_tree_to_str_list(e.children[0]),
                      parse_tree_to_ast(e.children[1]))
    elif e.data in primitive_ops:
        return PrimitiveCall(e.meta, e.data,
                             [parse_tree_to_ast(c) for c in e.children])
    
    # proofs
    if e.data == 'proof_var':
        return PVar(e.meta, str(e.children[0].value))
    elif e.data == 'apply':
        e1, e2 = e.children
        return Apply(e.meta, parse_tree_to_ast(e1), parse_tree_to_ast(e2))
    elif e.data == 'true_proof':
        return PTrue(e.meta)
    elif e.data == 'refl_proof':
        return PReflexive(e.meta)
    elif e.data == 'paren':
        return parse_tree_to_ast(e.children[0])
    elif e.data == 'let':
        return PLet(e.meta,
                    str(e.children[0].value),
                    parse_tree_to_formula(e.children[1]),
                    parse_tree_to_ast(e.children[2]),
                    parse_tree_to_ast(e.children[3]))
    elif e.data == 'annot':
        return PAnnot(e.meta,
                      parse_tree_to_formula(e.children[0]),
                      parse_tree_to_ast(e.children[1]))
    elif e.data == 'tuple':
       left = parse_tree_to_ast(e.children[0])
       right = parse_tree_to_ast(e.children[1])
       return PTuple(e.meta, extract_tuple(left) + extract_tuple(right))
    elif e.data == 'imp_intro':
        label = str(e.children[0].value)
        body = parse_tree_to_ast(e.children[1])
        return ImpIntro(e.meta, label, None, body)
    elif e.data == 'all_intro':
        vars = parse_tree_to_str_list(e.children[0])
        body = parse_tree_to_ast(e.children[1])
        return AllIntro(e.meta, vars, body)
    elif e.data == 'all_elim':
        univ = parse_tree_to_ast(e.children[0])
        args = parse_tree_to_list(e.children[1])
        return AllElim(e.meta, univ, args)
    elif e.data == 'imp_intro_explicit':
        label = str(e.children[0].value)
        premise = parse_tree_to_formula(e.children[1])
        body = parse_tree_to_ast(e.children[2])
        return ImpIntro(e.meta, label, premise, body)
    elif e.data == 'cases':
        return Cases(e.meta,
                     parse_tree_to_ast(e.children[0]),
                     parse_tree_to_case_list(e.children[1]))

    # constructor declaratoin
    elif e.data == 'constr_id':
        return Constructor(e.meta, str(e.children[0].value), [])
    elif e.data == 'constr_apply':
        param_types = parse_tree_to_list(e.children[1])
        return Constructor(e.meta, str(e.children[0].value), param_types)
    
    # union definitions
    elif e.data == 'union':
        return Union(e.meta, str(e.children[0].value),
                     parse_tree_to_list(e.children[1]))
    
    # theorem definitions
    elif e.data == 'theorem':
        return Theorem(e.meta,
                       str(e.children[0].value),
                       parse_tree_to_formula(e.children[1]),
                       parse_tree_to_ast(e.children[2]))

    # patterns in function definitions
    elif e.data == 'pattern_id':
        return PatternCons(e.meta, str(e.children[0].value), [])
    elif e.data == 'pattern_apply':
        params = parse_tree_to_str_list(e.children[1])
        return PatternCons(e.meta, str(e.children[0].value), params)
    
    # case of a recursive function
    elif e.data == 'fun_case':
        pp = parse_tree_to_list(e.children[1])
        return FunCase(e.meta, pp[0], pp[1:],
                       parse_tree_to_ast(e.children[2]))
    # recursive functions
    elif e.data == 'rec_fun':
        return RecFun(e.meta, str(e.children[0].value),
                      parse_tree_to_list(e.children[1]),
                      parse_tree_to_ast(e.children[2]),
                      parse_tree_to_list(e.children[3]))

    # term definition
    elif e.data == 'define':
        return Define(e.meta, str(e.children[0].value),
                      parse_tree_to_ast(e.children[1]))
    
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
    ast = parse(p, trace=True)
    print(str(ast))
    try:
        check_poof(ast)
        print(filename + ' is valid')
    except Exception as e:
        print(str(e))
