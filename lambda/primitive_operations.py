from values import *
from ast_types import *
import math

compare_ops = {'less': lambda x, y: x < y,
               'less_equal': lambda x, y: x <= y,
               'greater': lambda x, y: x > y,
               'greater_equal': lambda x, y: x >= y}


# TODO: move most of these out into separate files.

def eval_prim(op, vals, machine, location):
    match op:
        case 'breakpoint':
            machine.pause = True
            set_debug(True)
            return Void()
        case 'exit':
            exit(vals[0])
        case 'input':
            return Number(int(input()))
        case 'print':
            print(vals[0])
            return Void()
        case 'copy':
            return vals[0].duplicate(1, location)
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
        case 'join':
            ptr1, ptr2 = vals
            ptr = ptr1.duplicate(1, location)
            ptr.transfer(1, ptr2, location)
            return ptr
        case 'permission':
            ptr = vals[0]
            if not isinstance(ptr, Pointer):
                error(location, "permission operation requires pointer, not "
                      + str(ptr))
            return Number(ptr.permission)
        case 'upgrade':
            ptr = vals[0]
            b = ptr.upgrade(location)
            return Boolean(b)
        case cmp if cmp in compare_ops.keys():
            left, right = vals
            l = to_number(left, location)
            r = to_number(right, location)
            return Boolean(compare_ops[cmp](l, r))
        case _:
            return get_primitive_interp(op)(vals, machine, location)


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


@dataclass
class PrimitiveCall(Exp):
    op: str
    args: list[Exp]
    __match_args__ = ("op", "args")

    def __str__(self):
        return self.op + \
               "(" + ", ".join([str(arg) for arg in self.args]) + ")"

    def __repr__(self):
        return str(self)

    def free_vars(self):
        return set().union(*[arg.free_vars() for arg in self.args])

    def type_check(self, env, ctx):
        if tracing_on():
            print("starting to type checking " + str(self))
        arg_types = []
        new_args = []
        for arg in self.args:
            arg_type, new_arg = arg.type_check(env, 'none')
            arg_types.append(arg_type)
            new_args.append(new_arg)
        if tracing_on():
            print("checking primitive " + str(self.op))
        ret, cast_args = type_check_prim(self.location, self.op, arg_types, new_args)
        if tracing_on():
            print("finished type checking " + str(self))
            print("type: " + str(ret))
        return ret, PrimitiveCall(self.location, self.op, cast_args)

