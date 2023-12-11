from values import *
from ast_types import *
import math

compare_ops = {'less': lambda x, y: x < y,
               'less_equal': lambda x, y: x <= y,
               'greater': lambda x, y: x > y,
               'greater_equal': lambda x, y: x >= y}


# TODO: move most of these out into separate files.

def eval_prim(op, vals, location):
    match op:
        case 'exit':
            exit(vals[0])
        case 'input':
            return Number(int(input()))
        case 'print':
            print(vals[0])
            return Void()
        case 'equal':
            left, right = vals
            return Boolean(left.equals(right))
        case 'not_equal':
            left, right = vals
            return Boolean(not left.equals(right))
        case 'add':
            left, right = vals
            l = to_number(left, location)
            r = to_number(right, location)
            return Number(l + r)
        case 'sub':
            left = to_number(vals[0], location)
            right = to_number(vals[1], location)
            return Number(left - right)
        case 'mul':
            left = to_number(vals[0], location)
            right = to_number(vals[1], location)
            return Number(left * right)
        case 'div':
            left = to_number(vals[0], location)
            right = to_number(vals[1], location)
            return Number(Fraction(left, right))
        case 'int_div':
            left = to_number(vals[0], location)
            right = to_number(vals[1], location)
            return Number(left // right)
        case 'mod':
            left = to_number(vals[0], location)
            right = to_number(vals[1], location)
            return Number(left % right)
        case 'neg':
            val = to_number(vals[0], location)
            return Number(- val)
        case 'sqrt':
            val = to_number(vals[0], location)
            return Number(int(math.sqrt(val)))
        case 'and':
            left = to_boolean(vals[0], location)
            right = to_boolean(vals[1], location)
            return Boolean(left and right)
        case 'or':
            left = to_boolean(vals[0], location)
            right = to_boolean(vals[1], location)
            return Boolean(left or right)
        case 'not':
            val = to_boolean(vals[0], location)
            return Boolean(not val)
        case cmp if cmp in compare_ops.keys():
            left, right = vals
            l = to_number(left, location)
            r = to_number(right, location)
            return Boolean(compare_ops[cmp](l, r))
        case _:
            return get_primitive_interp(op)(vals, location)


prim_types = {'add': FunctionType(None, [], [IntType(None), IntType(None)], IntType(None), []),
              'sub': FunctionType(None, [], [IntType(None), IntType(None)], IntType(None), []),
              'mul': FunctionType(None, [], [IntType(None), IntType(None)], IntType(None), []),
              'div': FunctionType(None, [], [IntType(None), IntType(None)], IntType(None), []),
              'int_div': FunctionType(None, [], [IntType(None), IntType(None)], IntType(None), []),
              'mod': FunctionType(None, [], [IntType(None), IntType(None)], IntType(None), []),
              'neg': FunctionType(None, [], [IntType(None)], IntType(None), []),
              'sqrt': FunctionType(None, [], [IntType(None)], IntType(None), []),
              'and': FunctionType(None, [], [BoolType(None), BoolType(None)], BoolType(None), []),
              'or': FunctionType(None, [], [BoolType(None), BoolType(None)], BoolType(None), []),
              'not': FunctionType(None, [], [BoolType(None)], BoolType(None), [])}

