import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.formatter import Formatter


def fmt(source: str) -> str:
    """Helper: lex, parse, and format source code."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    return Formatter().format(program)


class TestFormatterImports:
    def test_single_import(self):
        result = fmt("import std.io")
        assert "import std.io" in result

    def test_multiple_imports(self):
        result = fmt("import std.io\nimport std.math")
        assert "import std.io" in result
        assert "import std.math" in result


class TestFormatterTypeDeclarations:
    def test_simple_type_alias(self):
        result = fmt("type Money = Int")
        assert "type Money = Int" in result

    def test_type_with_invariant(self):
        result = fmt("type PositiveMoney = Int\n  invariant value > 0")
        assert "type PositiveMoney = Int" in result
        assert "  invariant value > 0" in result

    def test_type_with_multiple_invariants(self):
        source = "type Money = Int\n  invariant value >= 0\n  invariant value <= 9999999999"
        result = fmt(source)
        assert "invariant value >= 0" in result
        assert "invariant value <= 9999999999" in result

    def test_sum_type(self):
        source = "type TransferError =\n  | InsufficientFunds\n  | AccountNotFound\n  | InvalidAmount"
        result = fmt(source)
        assert "| InsufficientFunds" in result
        assert "| AccountNotFound" in result
        assert "| InvalidAmount" in result


class TestFormatterFunctionDeclarations:
    def test_simple_function(self):
        source = "define add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        result = fmt(source)
        assert "define add(x: Int, y: Int) -> Int" in result
        assert "given" in result
        assert "x + y" in result

    def test_function_with_contracts(self):
        source = "define add(x: Int, y: Int) -> Int\n  expect x >= 0\n  expect y >= 0\n  ensure result >= 0\ngiven\n  x + y"
        result = fmt(source)
        assert "expect x >= 0" in result
        assert "expect y >= 0" in result
        assert "ensure result >= 0" in result

    def test_function_with_result_return(self):
        source = "define safe_div(x: Int, y: Int) -> Result[Int, String]\ngiven\n  x"
        result = fmt(source)
        assert "Result[Int, String]" in result

    def test_no_params_function(self):
        source = "define hello() -> Unit\ngiven\n  0"
        result = fmt(source)
        assert "define hello() -> Unit" in result


class TestFormatterExpressions:
    def test_integer_literal(self):
        source = "define f() -> Int\ngiven\n  42"
        result = fmt(source)
        assert "42" in result

    def test_float_literal(self):
        source = "define f() -> Float\ngiven\n  3.14"
        result = fmt(source)
        assert "3.14" in result

    def test_string_literal(self):
        source = 'define f() -> String\ngiven\n  "hello"'
        result = fmt(source)
        assert '"hello"' in result

    def test_bool_literal(self):
        source = "define f() -> Bool\ngiven\n  true"
        result = fmt(source)
        assert "true" in result

    def test_binary_op(self):
        source = "define f() -> Int\ngiven\n  x + y"
        result = fmt(source)
        assert "x + y" in result

    def test_comparison(self):
        source = "define f() -> Bool\ngiven\n  x >= 0"
        result = fmt(source)
        assert "x >= 0" in result

    def test_function_call(self):
        source = "define f() -> Int\ngiven\n  add(1, 2)"
        result = fmt(source)
        assert "add(1, 2)" in result

    def test_member_access(self):
        source = "define f() -> Int\ngiven\n  account.balance"
        result = fmt(source)
        assert "account.balance" in result

    def test_unary_not(self):
        source = "define f() -> Bool\ngiven\n  !x"
        result = fmt(source)
        assert "!x" in result


class TestFormatterRoundTrip:
    def test_simple_function_round_trip(self):
        """Format, then re-parse to verify the result is valid VibeLang."""
        source = "define add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        formatted = fmt(source)
        # Should be parseable
        tokens = Lexer(formatted).tokenize()
        program = Parser(tokens).parse()
        assert len(program.declarations) == 1
        assert program.declarations[0].name == "add"

    def test_type_round_trip(self):
        source = "type Money = Int"
        formatted = fmt(source)
        tokens = Lexer(formatted).tokenize()
        program = Parser(tokens).parse()
        assert len(program.declarations) == 1
        assert program.declarations[0].name == "Money"

    def test_multiple_declarations_round_trip(self):
        source = "type Money = Int\n\ndefine add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        formatted = fmt(source)
        tokens = Lexer(formatted).tokenize()
        program = Parser(tokens).parse()
        assert len(program.declarations) == 2
