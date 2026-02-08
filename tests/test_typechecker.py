import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.parser.ast_nodes import (
    Program, IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    BinaryOp, UnaryOp, Identifier, FunctionCall, ArrayLiteral,
    PrimitiveType, ArrayType, FunctionDeclaration, TypeDeclaration,
)
from compiler.typechecker import TypeChecker, TypeCheckError


def check(source: str):
    """Helper: lex, parse, and type-check source code."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    checker = TypeChecker()
    errors = checker.check(program)
    return checker, errors


# ------------------------------------------------------------------
# Literal type inference
# ------------------------------------------------------------------

class TestLiteralInference:
    def test_integer_literal(self):
        tc = TypeChecker()
        expr = IntegerLiteral(line=1, column=1, value=42)
        assert tc.infer_type(expr, {}) == "Int"

    def test_float_literal(self):
        tc = TypeChecker()
        expr = FloatLiteral(line=1, column=1, value=3.14)
        assert tc.infer_type(expr, {}) == "Float"

    def test_string_literal(self):
        tc = TypeChecker()
        expr = StringLiteral(line=1, column=1, value="hello")
        assert tc.infer_type(expr, {}) == "String"

    def test_bool_literal(self):
        tc = TypeChecker()
        expr = BoolLiteral(line=1, column=1, value=True)
        assert tc.infer_type(expr, {}) == "Bool"


# ------------------------------------------------------------------
# Binary operation type checking
# ------------------------------------------------------------------

class TestBinaryOps:
    def _binop(self, left_type, op, right_type):
        """Create a binary op from literal types and infer result."""
        tc = TypeChecker()
        type_to_literal = {
            "Int": IntegerLiteral(1, 1, value=1),
            "Float": FloatLiteral(1, 1, value=1.0),
            "String": StringLiteral(1, 1, value="a"),
            "Bool": BoolLiteral(1, 1, value=True),
        }
        left = type_to_literal[left_type]
        right = type_to_literal[right_type]
        expr = BinaryOp(line=1, column=1, left=left, operator=op, right=right)
        return tc, tc.infer_type(expr, {})

    def test_int_add(self):
        _, t = self._binop("Int", "+", "Int")
        assert t == "Int"

    def test_int_sub(self):
        _, t = self._binop("Int", "-", "Int")
        assert t == "Int"

    def test_int_mul(self):
        _, t = self._binop("Int", "*", "Int")
        assert t == "Int"

    def test_int_div(self):
        _, t = self._binop("Int", "/", "Int")
        assert t == "Int"

    def test_int_mod(self):
        _, t = self._binop("Int", "%", "Int")
        assert t == "Int"

    def test_float_add(self):
        _, t = self._binop("Float", "+", "Float")
        assert t == "Float"

    def test_mixed_arithmetic(self):
        _, t = self._binop("Int", "+", "Float")
        assert t == "Float"

    def test_string_concat(self):
        _, t = self._binop("String", "+", "String")
        assert t == "String"

    def test_int_greater(self):
        _, t = self._binop("Int", ">", "Int")
        assert t == "Bool"

    def test_int_less_equal(self):
        _, t = self._binop("Int", "<=", "Int")
        assert t == "Bool"

    def test_int_equality(self):
        _, t = self._binop("Int", "==", "Int")
        assert t == "Bool"

    def test_bool_and(self):
        _, t = self._binop("Bool", "&&", "Bool")
        assert t == "Bool"

    def test_bool_or(self):
        _, t = self._binop("Bool", "||", "Bool")
        assert t == "Bool"

    def test_invalid_arithmetic_string_int(self):
        tc, t = self._binop("String", "-", "Int")
        assert len(tc.errors) == 1
        assert "Cannot apply" in tc.errors[0].message

    def test_invalid_logical_int(self):
        tc, t = self._binop("Int", "&&", "Int")
        assert len(tc.errors) == 2  # both operands flagged


# ------------------------------------------------------------------
# Unary ops
# ------------------------------------------------------------------

class TestUnaryOps:
    def test_not_bool(self):
        tc = TypeChecker()
        expr = UnaryOp(1, 1, operator="!", operand=BoolLiteral(1, 1, value=True))
        assert tc.infer_type(expr, {}) == "Bool"

    def test_negate_int(self):
        tc = TypeChecker()
        expr = UnaryOp(1, 1, operator="-", operand=IntegerLiteral(1, 1, value=5))
        assert tc.infer_type(expr, {}) == "Int"

    def test_not_on_int_error(self):
        tc = TypeChecker()
        expr = UnaryOp(1, 1, operator="!", operand=IntegerLiteral(1, 1, value=1))
        tc.infer_type(expr, {})
        assert len(tc.errors) == 1
        assert "Bool" in tc.errors[0].message


# ------------------------------------------------------------------
# Function declaration type checking
# ------------------------------------------------------------------

class TestFunctionDeclaration:
    def test_simple_function_no_errors(self):
        source = "define add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        tc, errors = check(source)
        assert errors == []
        assert "add" in tc.function_signatures
        assert tc.function_signatures["add"]["return_type"] == "Int"

    def test_function_return_type_mismatch(self):
        source = 'define f(x: Int) -> Int\ngiven\n  "hello"'
        _, errors = check(source)
        assert len(errors) == 1
        assert "does not match" in errors[0].message

    def test_function_bool_return(self):
        source = "define is_positive(x: Int) -> Bool\ngiven\n  x > 0"
        _, errors = check(source)
        assert errors == []

    def test_function_params_in_scope(self):
        source = "define double(x: Int) -> Int\ngiven\n  x + x"
        tc, errors = check(source)
        assert errors == []

    def test_function_call_arg_count_mismatch(self):
        source = (
            "define add(x: Int, y: Int) -> Int\ngiven\n  x + y\n\n"
            "define test() -> Int\ngiven\n  add(1)"
        )
        _, errors = check(source)
        assert len(errors) == 1
        assert "expects 2" in errors[0].message

    def test_function_call_arg_type_mismatch(self):
        source = (
            "define add(x: Int, y: Int) -> Int\ngiven\n  x + y\n\n"
            'define test() -> Int\ngiven\n  add(1, "hi")'
        )
        _, errors = check(source)
        assert len(errors) >= 1
        assert "expected Int" in errors[0].message


# ------------------------------------------------------------------
# Type declarations
# ------------------------------------------------------------------

class TestTypeDeclaration:
    def test_simple_alias(self):
        source = "type Money = Int"
        tc, errors = check(source)
        assert errors == []
        assert "Money" in tc.type_env
        assert tc.type_env["Money"] == "Int"

    def test_sum_type(self):
        source = (
            "type Color =\n"
            "  | Red\n"
            "  | Green\n"
            "  | Blue"
        )
        tc, errors = check(source)
        assert errors == []
        assert "Color" in tc.type_env
        assert tc.type_env["Red"] == "Color"

    def test_type_alias_compatibility(self):
        source = (
            "type Money = Int\n\n"
            "define getMoney() -> Money\ngiven\n  42"
        )
        tc, errors = check(source)
        assert errors == []


# ------------------------------------------------------------------
# Contract validation
# ------------------------------------------------------------------

class TestContracts:
    def test_precondition_must_be_bool(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "given\n  x"
        )
        _, errors = check(source)
        assert errors == []

    def test_precondition_non_bool_error(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  expect x + 1\n"
            "given\n  x"
        )
        _, errors = check(source)
        assert len(errors) == 1
        assert "Precondition must be Bool" in errors[0].message

    def test_postcondition_must_be_bool(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  ensure result >= 0\n"
            "given\n  x"
        )
        _, errors = check(source)
        assert errors == []

    def test_postcondition_non_bool_error(self):
        source = (
            "define f(x: Int) -> Int\n"
            "  ensure result + 1\n"
            "given\n  x"
        )
        _, errors = check(source)
        assert len(errors) == 1
        assert "Postcondition must be Bool" in errors[0].message


# ------------------------------------------------------------------
# Invariant validation
# ------------------------------------------------------------------

class TestInvariants:
    def test_invariant_bool_ok(self):
        source = "type PositiveInt = Int\n  invariant value > 0"
        _, errors = check(source)
        assert errors == []

    def test_invariant_non_bool_error(self):
        source = "type BadType = Int\n  invariant value + 1"
        _, errors = check(source)
        assert len(errors) == 1
        assert "Invariant must be Bool" in errors[0].message


# ------------------------------------------------------------------
# Identifier resolution
# ------------------------------------------------------------------

class TestIdentifiers:
    def test_undefined_identifier(self):
        tc = TypeChecker()
        expr = Identifier(line=1, column=1, name="unknown")
        tc.infer_type(expr, {})
        assert len(tc.errors) == 1
        assert "Undefined" in tc.errors[0].message

    def test_known_identifier(self):
        tc = TypeChecker()
        expr = Identifier(line=1, column=1, name="x")
        result = tc.infer_type(expr, {"x": "Int"})
        assert result == "Int"


# ------------------------------------------------------------------
# Array type inference
# ------------------------------------------------------------------

class TestArrayTypes:
    def test_array_literal_int(self):
        tc = TypeChecker()
        elems = [IntegerLiteral(1, 1, value=i) for i in range(3)]
        expr = ArrayLiteral(line=1, column=1, elements=elems)
        assert tc.infer_type(expr, {}) == "Array[Int]"

    def test_empty_array(self):
        tc = TypeChecker()
        expr = ArrayLiteral(line=1, column=1, elements=[])
        assert tc.infer_type(expr, {}) == "Array[Unknown]"

    def test_mixed_array_error(self):
        tc = TypeChecker()
        elems = [
            IntegerLiteral(1, 1, value=1),
            StringLiteral(1, 1, value="x"),
        ]
        expr = ArrayLiteral(line=1, column=1, elements=elems)
        tc.infer_type(expr, {})
        assert len(tc.errors) == 1
        assert "mismatch" in tc.errors[0].message


# ------------------------------------------------------------------
# Error location info
# ------------------------------------------------------------------

class TestErrorLocation:
    def test_error_has_line_and_column(self):
        err = TypeCheckError("test error", line=5, column=10)
        assert err.line == 5
        assert err.column == 10
        assert "5:10" in str(err)
