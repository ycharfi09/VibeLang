import pytest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.parser.ast_nodes import (
    Program, FunctionDeclaration,
    IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, WhenExpression,
    ExpressionStatement,
)
from compiler.optimizer import Optimizer


def optimize(source: str) -> Program:
    """Helper: lex, parse, then optimize source code."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    return Optimizer().optimize(program)


def get_expr(program: Program):
    """Extract the single expression from first function body."""
    func = program.declarations[0]
    stmt = func.body.statements[0]
    assert isinstance(stmt, ExpressionStatement)
    return stmt.expression


def opt_expr(source_expr: str):
    """Shorthand: wrap expression in a function, optimize, return expression."""
    source = f"define f() -> Int\ngiven\n  {source_expr}"
    return get_expr(optimize(source))


# =====================================================================
# Constant Folding — Arithmetic
# =====================================================================


class TestConstantFoldingArithmetic:
    def test_add(self):
        result = opt_expr("3 + 4")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 7

    def test_subtract(self):
        result = opt_expr("10 - 3")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 7

    def test_multiply(self):
        result = opt_expr("2 * 3")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 6

    def test_divide_exact(self):
        result = opt_expr("10 / 2")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 5

    def test_divide_fractional(self):
        result = opt_expr("7 / 2")
        assert isinstance(result, FloatLiteral)
        assert result.value == 3.5

    def test_modulo(self):
        result = opt_expr("10 % 3")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 1

    def test_nested_arithmetic(self):
        result = opt_expr("2 + 3 * 4")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 14

    def test_divide_by_zero_unchanged(self):
        result = opt_expr("10 / 0")
        assert isinstance(result, BinaryOp)
        assert result.operator == "/"


# =====================================================================
# Constant Folding — Float
# =====================================================================


class TestConstantFoldingFloat:
    def test_float_add(self):
        result = opt_expr("1.5 + 2.5")
        assert isinstance(result, FloatLiteral)
        assert result.value == 4.0

    def test_float_multiply(self):
        result = opt_expr("2.0 * 3.0")
        assert isinstance(result, FloatLiteral)
        assert result.value == 6.0

    def test_float_divide(self):
        result = opt_expr("7.0 / 2.0")
        assert isinstance(result, FloatLiteral)
        assert result.value == 3.5


# =====================================================================
# Constant Folding — Comparison
# =====================================================================


class TestConstantFoldingComparison:
    def test_greater_than_true(self):
        result = opt_expr("3 > 2")
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_greater_than_false(self):
        result = opt_expr("2 > 3")
        assert isinstance(result, BoolLiteral)
        assert result.value is False

    def test_less_than(self):
        result = opt_expr("2 < 3")
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_equal(self):
        result = opt_expr("5 == 5")
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_not_equal(self):
        result = opt_expr("5 != 5")
        assert isinstance(result, BoolLiteral)
        assert result.value is False

    def test_greater_equal(self):
        result = opt_expr("3 >= 3")
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_less_equal(self):
        result = opt_expr("4 <= 3")
        assert isinstance(result, BoolLiteral)
        assert result.value is False


# =====================================================================
# Constant Folding — Logical
# =====================================================================


class TestConstantFoldingLogical:
    def test_and_true_false(self):
        result = opt_expr("true && false")
        assert isinstance(result, BoolLiteral)
        assert result.value is False

    def test_and_true_true(self):
        result = opt_expr("true && true")
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_or_false_true(self):
        result = opt_expr("false || true")
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_or_false_false(self):
        result = opt_expr("false || false")
        assert isinstance(result, BoolLiteral)
        assert result.value is False


# =====================================================================
# Constant Folding — Unary
# =====================================================================


class TestConstantFoldingUnary:
    def test_negate_int(self):
        result = opt_expr("-5")
        assert isinstance(result, IntegerLiteral)
        assert result.value == -5

    def test_negate_float(self):
        result = opt_expr("-3.14")
        assert isinstance(result, FloatLiteral)
        assert result.value == -3.14

    def test_not_true(self):
        result = opt_expr("!true")
        assert isinstance(result, BoolLiteral)
        assert result.value is False

    def test_not_false(self):
        result = opt_expr("!false")
        assert isinstance(result, BoolLiteral)
        assert result.value is True


# =====================================================================
# Constant Folding — String Concatenation
# =====================================================================


class TestConstantFoldingString:
    def test_string_concat(self):
        result = opt_expr('"hello" + " world"')
        assert isinstance(result, StringLiteral)
        assert result.value == "hello world"

    def test_string_concat_empty(self):
        result = opt_expr('"hello" + ""')
        assert isinstance(result, StringLiteral)
        assert result.value == "hello"


# =====================================================================
# Dead Code Elimination
# =====================================================================


class TestDeadCodeElimination:
    def test_when_true(self):
        source = "define f() -> Int\ngiven\n  when true\n    42\n  otherwise\n    0"
        result = get_expr(optimize(source))
        assert isinstance(result, IntegerLiteral)
        assert result.value == 42

    def test_when_false(self):
        source = "define f() -> Int\ngiven\n  when false\n    42\n  otherwise\n    99"
        result = get_expr(optimize(source))
        assert isinstance(result, IntegerLiteral)
        assert result.value == 99

    def test_when_false_no_else(self):
        source = "define f() -> Int\ngiven\n  when false\n    42"
        result = get_expr(optimize(source))
        # With no else block, the dead when-false is replaced with 0 placeholder
        assert isinstance(result, IntegerLiteral)
        assert result.value == 0

    def test_when_non_literal_unchanged(self):
        source = "define f(x: Bool) -> Int\ngiven\n  when x\n    42\n  otherwise\n    0"
        result = get_expr(optimize(source))
        assert isinstance(result, WhenExpression)

    def test_when_with_folded_condition(self):
        # Condition folds to true, then dead code is eliminated
        source = "define f() -> Int\ngiven\n  when 1 > 0\n    42\n  otherwise\n    0"
        result = get_expr(optimize(source))
        assert isinstance(result, IntegerLiteral)
        assert result.value == 42


# =====================================================================
# Identity Simplification
# =====================================================================


class TestIdentitySimplification:
    def test_add_zero_right(self):
        result = opt_expr("x + 0")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_add_zero_left(self):
        result = opt_expr("0 + x")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_sub_zero(self):
        result = opt_expr("x - 0")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_mul_one_right(self):
        result = opt_expr("x * 1")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_mul_one_left(self):
        result = opt_expr("1 * x")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_mul_zero_right(self):
        result = opt_expr("x * 0")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 0

    def test_mul_zero_left(self):
        result = opt_expr("0 * x")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 0

    def test_double_negation(self):
        result = opt_expr("!!x")
        assert isinstance(result, Identifier)
        assert result.name == "x"


# =====================================================================
# Nested Optimizations
# =====================================================================


class TestNestedOptimizations:
    def test_nested_constant_fold(self):
        # (2 + 3) * (4 - 1) → 5 * 3 → 15
        result = opt_expr("(2 + 3) * (4 - 1)")
        assert isinstance(result, IntegerLiteral)
        assert result.value == 15

    def test_identity_after_fold(self):
        # x + (3 - 3) → x + 0 → x
        result = opt_expr("x + (3 - 3)")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_fold_in_function_call_args(self):
        result = opt_expr("add(2 + 3, 4 * 5)")
        from compiler.parser.ast_nodes import FunctionCall
        assert isinstance(result, FunctionCall)
        assert isinstance(result.arguments[0], IntegerLiteral)
        assert result.arguments[0].value == 5
        assert isinstance(result.arguments[1], IntegerLiteral)
        assert result.arguments[1].value == 20

    def test_fold_in_member_access(self):
        # Member access obj is optimized
        source = "define f() -> Int\ngiven\n  (1 + 2).value"
        result = get_expr(optimize(source))
        from compiler.parser.ast_nodes import MemberAccess
        assert isinstance(result, MemberAccess)
        assert isinstance(result.obj, IntegerLiteral)
        assert result.obj.value == 3


# =====================================================================
# Optimization Count Tracking
# =====================================================================


class TestOptimizationCount:
    def test_single_fold_counted(self):
        tokens = Lexer("define f() -> Int\ngiven\n  3 + 4").tokenize()
        program = Parser(tokens).parse()
        opt = Optimizer()
        opt.optimize(program)
        assert opt.optimizations_applied == 1

    def test_multiple_folds_counted(self):
        tokens = Lexer("define f() -> Int\ngiven\n  (2 + 3) * (4 - 1)").tokenize()
        program = Parser(tokens).parse()
        opt = Optimizer()
        opt.optimize(program)
        # 2+3 → 5, 4-1 → 3, 5*3 → 15 = 3 optimizations
        assert opt.optimizations_applied == 3

    def test_no_optimizations(self):
        tokens = Lexer("define f(x: Int) -> Int\ngiven\n  x").tokenize()
        program = Parser(tokens).parse()
        opt = Optimizer()
        opt.optimize(program)
        assert opt.optimizations_applied == 0

    def test_dead_code_counted(self):
        source = "define f() -> Int\ngiven\n  when true\n    42\n  otherwise\n    0"
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        opt = Optimizer()
        opt.optimize(program)
        assert opt.optimizations_applied >= 1


# =====================================================================
# Pass-through (no optimization needed)
# =====================================================================


class TestPassThrough:
    def test_identifier_unchanged(self):
        result = opt_expr("x")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_variable_binary_unchanged(self):
        result = opt_expr("x + y")
        assert isinstance(result, BinaryOp)
        assert isinstance(result.left, Identifier)
        assert isinstance(result.right, Identifier)

    def test_function_declaration_preserved(self):
        source = "define add(x: Int, y: Int) -> Int\ngiven\n  x + y"
        program = optimize(source)
        func = program.declarations[0]
        assert isinstance(func, FunctionDeclaration)
        assert func.name == "add"
        assert len(func.parameters) == 2


# =====================================================================
# Original AST not mutated
# =====================================================================


class TestNoMutation:
    def test_original_unchanged(self):
        source = "define f() -> Int\ngiven\n  3 + 4"
        tokens = Lexer(source).tokenize()
        original = Parser(tokens).parse()
        opt = Optimizer()
        optimized = opt.optimize(original)

        # Original should still have BinaryOp
        orig_expr = original.declarations[0].body.statements[0].expression
        assert isinstance(orig_expr, BinaryOp)
        assert orig_expr.operator == "+"

        # Optimized should have IntegerLiteral
        opt_expr_val = optimized.declarations[0].body.statements[0].expression
        assert isinstance(opt_expr_val, IntegerLiteral)
        assert opt_expr_val.value == 7
