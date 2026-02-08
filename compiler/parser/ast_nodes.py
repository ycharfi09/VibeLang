"""VibeLang AST Node definitions."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union


# Base AST Node
@dataclass
class ASTNode:
    line: int
    column: int


# Program
@dataclass
class Program(ASTNode):
    imports: List['ImportStatement']
    declarations: List[Union['TypeDeclaration', 'FunctionDeclaration']]


# Import Statement
@dataclass
class ImportStatement(ASTNode):
    module_path: str


# Type Declarations
@dataclass
class TypeDeclaration(ASTNode):
    name: str
    type_params: List[str]
    definition: Union['SimpleType', 'SumType', 'RefinedType']
    invariants: List['Expression']


@dataclass
class SimpleType(ASTNode):
    name: str
    type_args: List['Type'] = field(default_factory=list)


@dataclass
class SumType(ASTNode):
    variants: List['Variant']


@dataclass
class Variant(ASTNode):
    name: str
    parameters: List['Type']


@dataclass
class RefinedType(ASTNode):
    base_type: 'Type'
    condition: 'Expression'


# Function Declarations
@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    parameters: List['Parameter']
    return_type: 'Type'
    preconditions: List['Expression']
    postconditions: List['Expression']
    body: 'Block'


@dataclass
class Parameter(ASTNode):
    name: str
    type_annotation: 'Type'


# Types
@dataclass
class Type(ASTNode):
    pass


@dataclass
class PrimitiveType(Type):
    name: str  # Int, Float, Bool, String, Byte, Unit


@dataclass
class ArrayType(Type):
    element_type: 'Type'


@dataclass
class ResultType(Type):
    success_type: 'Type'
    error_type: 'Type'


@dataclass
class FunctionType(Type):
    param_types: List['Type']
    return_type: 'Type'


@dataclass
class NamedType(Type):
    name: str
    type_args: List['Type'] = field(default_factory=list)


# Expressions
@dataclass
class Expression(ASTNode):
    pass


@dataclass
class IntegerLiteral(Expression):
    value: int


@dataclass
class FloatLiteral(Expression):
    value: float


@dataclass
class StringLiteral(Expression):
    value: str


@dataclass
class BoolLiteral(Expression):
    value: bool


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression


@dataclass
class FunctionCall(Expression):
    function: Expression
    arguments: List[Expression]


@dataclass
class MemberAccess(Expression):
    obj: Expression
    member: str


@dataclass
class ArrayLiteral(Expression):
    elements: List[Expression]


@dataclass
class RecordLiteral(Expression):
    fields: List[Tuple[str, Expression]]


@dataclass
class WhenExpression(Expression):
    condition: Expression
    then_block: 'Block'
    else_block: Optional['Block']


@dataclass
class GivenExpression(Expression):
    scrutinee: Expression
    cases: List['PatternCase']


@dataclass
class PatternCase(ASTNode):
    pattern: 'Pattern'
    expression: Expression


# Patterns
@dataclass
class Pattern(ASTNode):
    pass


@dataclass
class ConstructorPattern(Pattern):
    constructor: str
    parameters: List['Pattern']


@dataclass
class IdentifierPattern(Pattern):
    name: str


@dataclass
class LiteralPattern(Pattern):
    value: Union[int, float, str, bool]


@dataclass
class WildcardPattern(Pattern):
    pass


# Statements
@dataclass
class Statement(ASTNode):
    pass


@dataclass
class Block(Statement):
    statements: List[Statement]


@dataclass
class LetBinding(Statement):
    name: str
    type_annotation: Optional['Type']
    value: Expression


@dataclass
class Assignment(Statement):
    target: str
    value: Expression


@dataclass
class ExpressionStatement(Statement):
    expression: Expression
