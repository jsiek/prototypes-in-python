from dataclasses import dataclass
from ast_base import Type, AST, Exp
from typing import Any
from lark.tree import Meta


# Types

# Note: we use tuples instead of lists inside types because types need
# to be hashable, so they may only contain immutable values.

@dataclass(eq=True, frozen=True)
class IntType(Type):
    def __str__(self):
        return 'int'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, IntType)

@dataclass(eq=True, frozen=True)
class BoolType(Type):
    def __str__(self):
        return 'bool'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, BoolType)

@dataclass(eq=True, frozen=True)
class TupleType(Type):
    member_types: tuple[Type]
    __match_args__ = ("member_types",)

    def __str__(self):
        return '⟨' + ', '.join([str(t) for t in self.member_types]) + '⟩'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, TupleType) \
               and all([t1 == t2 for t1, t2 in zip(self.member_types,
                                                   other.member_types)])

@dataclass(eq=True, frozen=True)
class VariantType(Type):
    alternative_types: tuple[tuple[str, Type]]
    __match_args__ = ("alternative_types",)

    def __str__(self):
        return '(variant ' + '| '.join([x + ':' + str(t) \
                                        for x, t in self.alternative_types]) + ')'

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, TupleType) \
               and all([t1 == t2 for t1, t2 in zip(self.alternative_types,
                                                   other.alternative_types)])


@dataclass(eq=True, frozen=True)
class FunctionType(Type):
    type_params: tuple[str]
    param_types: tuple[tuple[str, Type]]
    return_type: Type
    requirements: list[AST]
    __match_args__ = ("type_params", "param_types", "return_type", "requirements")

    def __str__(self):
        return ('<' + ', '.join(self.type_params) + '>'
                if len(self.type_params) > 0 \
                    else '') \
               + '(' + ', '.join([k + ' ' + str(t) for k, t in self.param_types]) + ')' \
               + '->' + str(self.return_type) \
               + ' ' + ', '.join(str(req) for req in self.requirements)

    def __repr__(self):
        return str(self)



