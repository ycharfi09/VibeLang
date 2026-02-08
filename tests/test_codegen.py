import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.codegen import CodeGenerator, CodeGenError


def generate(source: str) -> str:
    """Helper: lex, parse, and generate Python code from VibeLang source."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    return CodeGenerator().generate(program)


def assert_valid_python(code: str):
    """Assert that the generated code is valid Python."""
    compile(code, "<test>", "exec")


# ------------------------------------------------------------------
# Literal generation
# ------------------------------------------------------------------

class TestLiteralGeneration:
    def test_integer_literal(self):
        code = generate("define f() -> Int\ngiven\n  42")
        assert_valid_python(code)
        assert "42" in code

    def test_float_literal(self):
        code = generate("define f() -> Float\ngiven\n  3.14")
        assert_valid_python(code)
        assert "3.14" in code

    def test_string_literal(self):
        code = generate('define f() -> String\ngiven\n  "hello"')
        assert_valid_python(code)
        assert "'hello'" in code

    def test_bool_true(self):
        code = generate("define f() -> Bool\ngiven\n  true")
        assert_valid_python(code)
        assert "True" in code

    def test_bool_false(self):
        code = generate("define f() -> Bool\ngiven\n  false")
        assert_valid_python(code)
        assert "False" in code


# ------------------------------------------------------------------
# Simple function generation
# ------------------------------------------------------------------

class TestFunctionGeneration:
    def test_simple_function(self):
        code = generate("define add(x: Int, y: Int) -> Int\ngiven\n  x + y")
        assert_valid_python(code)
        assert "def add(x, y):" in code
        assert "return" in code

    def test_no_params_function(self):
        code = generate("define hello() -> Unit\ngiven\n  0")
        assert_valid_python(code)
        assert "def hello():" in code

    def test_function_body_returns_last_expression(self):
        code = generate("define f() -> Int\ngiven\n  42")
        assert_valid_python(code)
        assert "result = 42" in code
        assert "return result" in code

    def test_generated_function_is_callable(self):
        code = generate("define add(x: Int, y: Int) -> Int\ngiven\n  x + y")
        ns = {}
        exec(code, ns)
        assert ns["add"](3, 4) == 7

    def test_generated_function_with_subtraction(self):
        code = generate("define sub(a: Int, b: Int) -> Int\ngiven\n  a - b")
        ns = {}
        exec(code, ns)
        assert ns["sub"](10, 3) == 7


# ------------------------------------------------------------------
# Binary operator translation
# ------------------------------------------------------------------

class TestBinaryOperators:
    def test_arithmetic_ops(self):
        for op in ["+", "-", "*"]:
            code = generate(f"define f(x: Int, y: Int) -> Int\ngiven\n  x {op} y")
            assert_valid_python(code)

    def test_comparison_ops(self):
        for op in ["==", "!=", "<", ">", "<=", ">="]:
            code = generate(f"define f(x: Int, y: Int) -> Bool\ngiven\n  x {op} y")
            assert_valid_python(code)

    def test_logical_and(self):
        code = generate("define f(a: Bool, b: Bool) -> Bool\ngiven\n  a && b")
        assert_valid_python(code)
        assert " and " in code

    def test_logical_or(self):
        code = generate("define f(a: Bool, b: Bool) -> Bool\ngiven\n  a || b")
        assert_valid_python(code)
        assert " or " in code

    def test_unary_not(self):
        code = generate("define f(a: Bool) -> Bool\ngiven\n  !a")
        assert_valid_python(code)
        assert "not " in code

    def test_unary_negate(self):
        code = generate("define f(x: Int) -> Int\ngiven\n  -x")
        assert_valid_python(code)
        assert "-x" in code

    def test_operator_execution(self):
        code = generate(
            "define f(a: Bool, b: Bool) -> Bool\ngiven\n  a && b"
        )
        ns = {}
        exec(code, ns)
        assert ns["f"](True, True) is True
        assert ns["f"](True, False) is False


# ------------------------------------------------------------------
# When/otherwise → if/else
# ------------------------------------------------------------------

class TestWhenOtherwise:
    def test_when_otherwise_generates_valid_python(self):
        source = (
            "define f(x: Int) -> Int\ngiven\n"
            "  when x > 0\n"
            "    1\n"
            "  otherwise\n"
            "    0"
        )
        code = generate(source)
        assert_valid_python(code)

    def test_when_otherwise_contains_if(self):
        source = (
            "define f(x: Int) -> Int\ngiven\n"
            "  when x > 0\n"
            "    1\n"
            "  otherwise\n"
            "    0"
        )
        code = generate(source)
        assert " if " in code

    def test_when_without_otherwise(self):
        source = (
            "define f(x: Int) -> Int\ngiven\n"
            "  when x > 0\n"
            "    1"
        )
        code = generate(source)
        assert_valid_python(code)


# ------------------------------------------------------------------
# Type declaration generation
# ------------------------------------------------------------------

class TestTypeDeclaration:
    def test_simple_type_alias(self):
        code = generate("type Money = Int")
        assert_valid_python(code)
        assert "class Money:" in code

    def test_type_with_invariant(self):
        code = generate("type PositiveMoney = Int\n  invariant value > 0")
        assert_valid_python(code)
        assert "class PositiveMoney:" in code
        assert "assert" in code

    def test_type_with_multiple_invariants(self):
        source = "type Money = Int\n  invariant value >= 0\n  invariant value <= 9999999999"
        code = generate(source)
        assert_valid_python(code)
        assert code.count("assert") >= 2

    def test_invariant_enforcement_at_runtime(self):
        code = generate("type PositiveInt = Int\n  invariant value > 0")
        ns = {}
        exec(code, ns)
        obj = ns["PositiveInt"](5)
        assert obj.value == 5
        with pytest.raises(AssertionError):
            ns["PositiveInt"](-1)


# ------------------------------------------------------------------
# Sum type generation
# ------------------------------------------------------------------

class TestSumTypeGeneration:
    def test_sum_type_base_class(self):
        source = (
            "type TransferError =\n"
            "  | InsufficientFunds\n"
            "  | AccountNotFound\n"
            "  | InvalidAmount"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "class TransferError:" in code

    def test_sum_type_variants(self):
        source = (
            "type TransferError =\n"
            "  | InsufficientFunds\n"
            "  | AccountNotFound"
        )
        code = generate(source)
        assert "class InsufficientFunds(TransferError):" in code
        assert "class AccountNotFound(TransferError):" in code

    def test_sum_type_variant_with_params(self):
        source = (
            "type Result =\n"
            "  | Ok(Int)\n"
            "  | Err(String)"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "__init__" in code

    def test_sum_type_runtime_isinstance(self):
        source = (
            "type Color =\n"
            "  | Red\n"
            "  | Green\n"
            "  | Blue"
        )
        code = generate(source)
        ns = {}
        exec(code, ns)
        r = ns["Red"]()
        assert isinstance(r, ns["Color"])

    def test_sum_type_variant_with_data(self):
        source = (
            "type MyResult =\n"
            "  | Ok(Int)\n"
            "  | Err(String)"
        )
        code = generate(source)
        ns = {}
        exec(code, ns)
        ok = ns["Ok"](42)
        assert ok.v0 == 42
        assert isinstance(ok, ns["MyResult"])


# ------------------------------------------------------------------
# Contract insertion (expect/ensure as assertions)
# ------------------------------------------------------------------

class TestContractGeneration:
    def test_precondition_assertion(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "given\n  x"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "assert" in code
        assert "Precondition" in code

    def test_postcondition_assertion(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  ensure result >= 0\n"
            "given\n  x"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "assert" in code
        assert "Postcondition" in code

    def test_precondition_enforcement_at_runtime(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "given\n  x"
        )
        code = generate(source)
        ns = {}
        exec(code, ns)
        assert ns["f"](5) == 5
        with pytest.raises(AssertionError):
            ns["f"](-1)

    def test_both_contracts(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "  ensure result >= 0\n"
            "given\n  x"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "Precondition" in code
        assert "Postcondition" in code

    def test_expect_comment_included(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "given\n  x"
        )
        code = generate(source)
        assert "# expect:" in code

    def test_ensure_comment_included(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  ensure result >= 0\n"
            "given\n  x"
        )
        code = generate(source)
        assert "# ensure:" in code


# ------------------------------------------------------------------
# Full program generation
# ------------------------------------------------------------------

class TestFullProgram:
    def test_type_and_function(self):
        source = (
            "type Money = Int\n\n"
            "define add(x: Int, y: Int) -> Int\n"
            "given\n  x + y"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "class Money:" in code
        assert "def add(x, y):" in code

    def test_imports_and_function(self):
        source = (
            "import std.io\n\n"
            "define f() -> Int\ngiven\n  42"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "import std.io" in code

    def test_sum_type_and_function(self):
        source = (
            "type Color =\n"
            "  | Red\n"
            "  | Green\n"
            "  | Blue\n\n"
            "define f() -> Int\ngiven\n  42"
        )
        code = generate(source)
        assert_valid_python(code)
        assert "class Color:" in code
        assert "def f():" in code

    def test_runtime_header_present(self):
        code = generate("define f() -> Int\ngiven\n  42")
        assert "_VL_Success" in code
        assert "_VL_Error" in code

    def test_full_program_executable(self):
        source = (
            "type PositiveInt = Int\n"
            "  invariant value > 0\n\n"
            "define double(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "given\n  x + x"
        )
        code = generate(source)
        ns = {}
        exec(code, ns)
        assert ns["double"](5) == 10
        p = ns["PositiveInt"](10)
        assert p.value == 10

    def test_multiple_functions(self):
        source = (
            "define add(x: Int, y: Int) -> Int\ngiven\n  x + y\n\n"
            "define sub(x: Int, y: Int) -> Int\ngiven\n  x - y"
        )
        code = generate(source)
        assert_valid_python(code)
        ns = {}
        exec(code, ns)
        assert ns["add"](3, 4) == 7
        assert ns["sub"](10, 3) == 7


# ------------------------------------------------------------------
# Additional expression coverage
# ------------------------------------------------------------------

class TestExpressionGeneration:
    def test_member_access(self):
        source = "define f() -> Int\ngiven\n  account.balance"
        code = generate(source)
        assert_valid_python(code)
        assert "account.balance" in code

    def test_function_call_generation(self):
        source = "define f() -> Int\ngiven\n  add(1, 2)"
        code = generate(source)
        assert_valid_python(code)
        assert "add(1, 2)" in code

    def test_nested_expression(self):
        source = "define f(x: Int, y: Int) -> Int\ngiven\n  (x + y) * 2"
        code = generate(source)
        assert_valid_python(code)
        ns = {}
        exec(code, ns)
        assert ns["f"](3, 4) == 14
