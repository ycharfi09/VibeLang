import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser, ParseError
from compiler.parser.ast_nodes import (
    Program, FunctionDeclaration, TypeDeclaration, ImportStatement,
    PrimitiveType, ArrayType, ResultType, NamedType,
    IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess,
    WhenExpression, Block, ExpressionStatement, SimpleType, SumType,
)


def parse(source: str) -> Program:
    """Helper: lex and parse source code."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class TestParserImports:
    def test_single_import(self):
        ast = parse("import std.io")
        assert len(ast.imports) == 1
        assert ast.imports[0].module_path == "std.io"

    def test_multiple_imports(self):
        ast = parse("import std.io\nimport std.math")
        assert len(ast.imports) == 2


class TestParserTypeDeclarations:
    def test_simple_type_alias(self):
        ast = parse("type Money = Int")
        assert len(ast.declarations) == 1
        td = ast.declarations[0]
        assert isinstance(td, TypeDeclaration)
        assert td.name == "Money"
        assert isinstance(td.definition, SimpleType)
        assert td.definition.name == "Int"

    def test_type_with_invariant(self):
        ast = parse("type PositiveMoney = Int\n  invariant value > 0")
        td = ast.declarations[0]
        assert td.name == "PositiveMoney"
        assert len(td.invariants) == 1

    def test_type_with_multiple_invariants(self):
        source = "type Money = Int\n  invariant value >= 0\n  invariant value <= 9999999999"
        ast = parse(source)
        td = ast.declarations[0]
        assert len(td.invariants) == 2

    def test_sum_type(self):
        source = "type TransferError =\n  | InsufficientFunds\n  | AccountNotFound\n  | InvalidAmount"
        ast = parse(source)
        td = ast.declarations[0]
        assert isinstance(td.definition, SumType)
        assert len(td.definition.variants) == 3
        assert td.definition.variants[0].name == "InsufficientFunds"


class TestParserFunctionDeclarations:
    def test_simple_function(self):
        source = "define add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        ast = parse(source)
        assert len(ast.declarations) == 1
        func = ast.declarations[0]
        assert isinstance(func, FunctionDeclaration)
        assert func.name == "add"
        assert len(func.parameters) == 2
        assert func.parameters[0].name == "x"
        assert isinstance(func.return_type, PrimitiveType)
        assert func.return_type.name == "Int"

    def test_function_with_contracts(self):
        source = "define add(x: Int, y: Int) -> Int\n  expect x >= 0\n  expect y >= 0\n  ensure result >= 0\ngiven\n  x + y"
        ast = parse(source)
        func = ast.declarations[0]
        assert len(func.preconditions) == 2
        assert len(func.postconditions) == 1

    def test_function_with_result_return_type(self):
        source = "define safe_div(x: Int, y: Int) -> Result[Int, String]\ngiven\n  x"
        ast = parse(source)
        func = ast.declarations[0]
        assert isinstance(func.return_type, ResultType)

    def test_function_with_array_param(self):
        source = "define sum(nums: Array[Int]) -> Int\ngiven\n  0"
        ast = parse(source)
        func = ast.declarations[0]
        assert isinstance(func.parameters[0].type_annotation, ArrayType)

    def test_no_params_function(self):
        source = "define hello() -> Unit\ngiven\n  0"
        ast = parse(source)
        func = ast.declarations[0]
        assert len(func.parameters) == 0


class TestParserExpressions:
    def test_integer_literal(self):
        source = "define f() -> Int\ngiven\n  42"
        ast = parse(source)
        func = ast.declarations[0]
        stmt = func.body.statements[0]
        assert isinstance(stmt, ExpressionStatement)
        assert isinstance(stmt.expression, IntegerLiteral)
        assert stmt.expression.value == 42

    def test_float_literal(self):
        source = "define f() -> Float\ngiven\n  3.14"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, FloatLiteral)
        assert expr.value == 3.14

    def test_string_literal(self):
        source = 'define f() -> String\ngiven\n  "hello"'
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, StringLiteral)
        assert expr.value == "hello"

    def test_bool_literal(self):
        source = "define f() -> Bool\ngiven\n  true"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, BoolLiteral)
        assert expr.value is True

    def test_binary_op_addition(self):
        source = "define f() -> Int\ngiven\n  x + y"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"

    def test_binary_op_precedence(self):
        source = "define f() -> Int\ngiven\n  a + b * c"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "*"

    def test_comparison(self):
        source = "define f() -> Bool\ngiven\n  x >= 0"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == ">="

    def test_logical_and(self):
        source = "define f() -> Bool\ngiven\n  a && b"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "&&"

    def test_unary_not(self):
        source = "define f() -> Bool\ngiven\n  !x"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, UnaryOp)
        assert expr.operator == "!"

    def test_function_call(self):
        source = "define f() -> Int\ngiven\n  add(1, 2)"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, FunctionCall)
        assert len(expr.arguments) == 2

    def test_member_access(self):
        source = "define f() -> Int\ngiven\n  account.balance"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, MemberAccess)
        assert expr.member == "balance"

    def test_parenthesized_expression(self):
        source = "define f() -> Int\ngiven\n  (a + b) * c"
        ast = parse(source)
        expr = ast.declarations[0].body.statements[0].expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "*"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "+"


class TestParserErrors:
    def test_unexpected_token(self):
        with pytest.raises(ParseError):
            parse("+ invalid")

    def test_missing_return_type(self):
        with pytest.raises(ParseError):
            parse("define f()\ngiven\n  0")


class TestParserMultipleDeclarations:
    def test_type_and_function(self):
        source = "type Money = Int\n\ndefine add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        ast = parse(source)
        assert len(ast.declarations) == 2
        assert isinstance(ast.declarations[0], TypeDeclaration)
        assert isinstance(ast.declarations[1], FunctionDeclaration)
