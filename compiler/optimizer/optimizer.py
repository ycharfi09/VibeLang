"""VibeLang AST Optimizer - performs AST-to-AST transformations."""

import copy
from typing import List, Union

from compiler.parser.ast_nodes import (
    ASTNode, Program, ImportStatement,
    TypeDeclaration, FunctionDeclaration, Parameter,
    Type,
    Expression, IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess,
    ArrayLiteral, RecordLiteral, WhenExpression, GivenExpression, PatternCase,
    Statement, Block, LetBinding, Assignment, ExpressionStatement,
)


class Optimizer:
    """Performs compile-time optimizations on VibeLang ASTs."""

    def __init__(self):
        self.optimizations_applied = 0

    def optimize(self, program: Program) -> Program:
        """Optimize a program AST, return optimized AST (original unchanged)."""
        tree = copy.deepcopy(program)
        tree.declarations = [self._optimize_declaration(d) for d in tree.declarations]
        return tree

    # ------------------------------------------------------------------
    # Declarations
    # ------------------------------------------------------------------

    def _optimize_declaration(
        self, decl: Union[TypeDeclaration, FunctionDeclaration]
    ) -> Union[TypeDeclaration, FunctionDeclaration]:
        if isinstance(decl, FunctionDeclaration):
            decl.preconditions = [self._optimize_expr(e) for e in decl.preconditions]
            decl.postconditions = [self._optimize_expr(e) for e in decl.postconditions]
            decl.body = self._optimize_block(decl.body)
        return decl

    # ------------------------------------------------------------------
    # Statements / blocks
    # ------------------------------------------------------------------

    def _optimize_block(self, block: Block) -> Block:
        block.statements = self._optimize_stmts(block.statements)
        return block

    def _optimize_stmts(self, stmts: List[Statement]) -> List[Statement]:
        result: List[Statement] = []
        for s in stmts:
            result.append(self._optimize_stmt(s))
        return result

    def _optimize_stmt(self, stmt: Statement) -> Statement:
        if isinstance(stmt, Block):
            return self._optimize_block(stmt)
        if isinstance(stmt, LetBinding):
            stmt.value = self._optimize_expr(stmt.value)
            return stmt
        if isinstance(stmt, Assignment):
            stmt.value = self._optimize_expr(stmt.value)
            return stmt
        if isinstance(stmt, ExpressionStatement):
            stmt.expression = self._optimize_expr(stmt.expression)
            return stmt
        return stmt

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _optimize_expr(self, expr: Expression) -> Expression:
        if isinstance(expr, BinaryOp):
            return self._optimize_binary(expr)
        if isinstance(expr, UnaryOp):
            return self._optimize_unary(expr)
        if isinstance(expr, FunctionCall):
            expr.arguments = [self._optimize_expr(a) for a in expr.arguments]
            return expr
        if isinstance(expr, MemberAccess):
            expr.obj = self._optimize_expr(expr.obj)
            return expr
        if isinstance(expr, ArrayLiteral):
            expr.elements = [self._optimize_expr(e) for e in expr.elements]
            return expr
        if isinstance(expr, RecordLiteral):
            expr.fields = [(n, self._optimize_expr(v)) for n, v in expr.fields]
            return expr
        if isinstance(expr, WhenExpression):
            return self._optimize_when(expr)
        if isinstance(expr, GivenExpression):
            expr.scrutinee = self._optimize_expr(expr.scrutinee)
            for case in expr.cases:
                case.expression = self._optimize_expr(case.expression)
            return expr
        # Literals and identifiers pass through
        return expr

    # ------------------------------------------------------------------
    # Binary operations: constant folding + identity simplification
    # ------------------------------------------------------------------

    def _optimize_binary(self, expr: BinaryOp) -> Expression:
        expr.left = self._optimize_expr(expr.left)
        expr.right = self._optimize_expr(expr.right)

        left, op, right = expr.left, expr.operator, expr.right

        # --- Constant folding ---
        folded = self._try_fold_binary(left, op, right, expr.line, expr.column)
        if folded is not None:
            self.optimizations_applied += 1
            return folded

        # --- Identity simplification ---
        simplified = self._try_simplify_identity(left, op, right, expr)
        if simplified is not None:
            self.optimizations_applied += 1
            return simplified

        return expr

    def _try_fold_binary(
        self, left: Expression, op: str, right: Expression,
        line: int, col: int,
    ) -> Expression | None:
        # Int op Int
        if isinstance(left, IntegerLiteral) and isinstance(right, IntegerLiteral):
            return self._fold_int(left.value, op, right.value, line, col)

        # Float op Float
        if isinstance(left, FloatLiteral) and isinstance(right, FloatLiteral):
            return self._fold_float(left.value, op, right.value, line, col)

        # Int op Float / Float op Int  →  promote to float
        if isinstance(left, (IntegerLiteral, FloatLiteral)) and isinstance(
            right, (IntegerLiteral, FloatLiteral)
        ):
            lv = float(left.value)
            rv = float(right.value)
            return self._fold_float(lv, op, rv, line, col)

        # String concatenation
        if isinstance(left, StringLiteral) and isinstance(right, StringLiteral) and op == "+":
            return StringLiteral(value=left.value + right.value, line=line, column=col)

        # Bool op Bool (logical)
        if isinstance(left, BoolLiteral) and isinstance(right, BoolLiteral):
            return self._fold_bool(left.value, op, right.value, line, col)

        return None

    def _fold_int(self, lv: int, op: str, rv: int, line: int, col: int) -> Expression | None:
        arith = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
                 "*": lambda a, b: a * b, "%": lambda a, b: a % b}
        cmp = {"==": lambda a, b: a == b, "!=": lambda a, b: a != b,
               "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
               ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}

        if op in arith:
            return IntegerLiteral(value=arith[op](lv, rv), line=line, column=col)
        if op == "/":
            if rv == 0:
                return None
            result = lv / rv
            if result == int(result):
                return IntegerLiteral(value=int(result), line=line, column=col)
            return FloatLiteral(value=result, line=line, column=col)
        if op in cmp:
            return BoolLiteral(value=cmp[op](lv, rv), line=line, column=col)
        return None

    def _fold_float(self, lv: float, op: str, rv: float, line: int, col: int) -> Expression | None:
        arith = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
                 "*": lambda a, b: a * b}
        cmp = {"==": lambda a, b: a == b, "!=": lambda a, b: a != b,
               "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
               ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}

        if op in arith:
            return FloatLiteral(value=arith[op](lv, rv), line=line, column=col)
        if op == "/":
            if rv == 0.0:
                return None
            return FloatLiteral(value=lv / rv, line=line, column=col)
        if op in cmp:
            return BoolLiteral(value=cmp[op](lv, rv), line=line, column=col)
        return None

    def _fold_bool(self, lv: bool, op: str, rv: bool, line: int, col: int) -> Expression | None:
        if op == "&&":
            return BoolLiteral(value=lv and rv, line=line, column=col)
        if op == "||":
            return BoolLiteral(value=lv or rv, line=line, column=col)
        if op == "==":
            return BoolLiteral(value=lv == rv, line=line, column=col)
        if op == "!=":
            return BoolLiteral(value=lv != rv, line=line, column=col)
        return None

    # --- Identity simplification ---

    def _try_simplify_identity(
        self, left: Expression, op: str, right: Expression, expr: BinaryOp,
    ) -> Expression | None:
        l_zero = self._is_int_literal(left, 0)
        r_zero = self._is_int_literal(right, 0)
        l_one = self._is_int_literal(left, 1)
        r_one = self._is_int_literal(right, 1)

        # x + 0 → x,  0 + x → x
        if op == "+" and r_zero:
            return left
        if op == "+" and l_zero:
            return right

        # x - 0 → x
        if op == "-" and r_zero:
            return left

        # x * 1 → x,  1 * x → x
        if op == "*" and r_one:
            return left
        if op == "*" and l_one:
            return right

        # x * 0 → 0,  0 * x → 0
        if op == "*" and r_zero:
            return IntegerLiteral(value=0, line=expr.line, column=expr.column)
        if op == "*" and l_zero:
            return IntegerLiteral(value=0, line=expr.line, column=expr.column)

        return None

    @staticmethod
    def _is_int_literal(expr: Expression, value: int) -> bool:
        return isinstance(expr, IntegerLiteral) and expr.value == value

    # ------------------------------------------------------------------
    # Unary operations: constant folding + double negation
    # ------------------------------------------------------------------

    def _optimize_unary(self, expr: UnaryOp) -> Expression:
        expr.operand = self._optimize_expr(expr.operand)
        op, operand = expr.operator, expr.operand

        # Constant folding
        if op == "-" and isinstance(operand, IntegerLiteral):
            self.optimizations_applied += 1
            return IntegerLiteral(value=-operand.value, line=expr.line, column=expr.column)
        if op == "-" and isinstance(operand, FloatLiteral):
            self.optimizations_applied += 1
            return FloatLiteral(value=-operand.value, line=expr.line, column=expr.column)
        if op == "!" and isinstance(operand, BoolLiteral):
            self.optimizations_applied += 1
            return BoolLiteral(value=not operand.value, line=expr.line, column=expr.column)

        # Double negation: !!x → x
        if op == "!" and isinstance(operand, UnaryOp) and operand.operator == "!":
            self.optimizations_applied += 1
            return operand.operand

        return expr

    # ------------------------------------------------------------------
    # When expression: dead code elimination
    # ------------------------------------------------------------------

    def _optimize_when(self, expr: WhenExpression) -> Expression:
        expr.condition = self._optimize_expr(expr.condition)
        expr.then_block = self._optimize_block(expr.then_block)
        if expr.else_block is not None:
            expr.else_block = self._optimize_block(expr.else_block)

        cond = expr.condition

        # when true → then_block contents
        if isinstance(cond, BoolLiteral) and cond.value is True:
            self.optimizations_applied += 1
            return self._block_to_expr(expr.then_block, expr.line, expr.column)

        # when false → else_block contents (or Unit-like)
        if isinstance(cond, BoolLiteral) and cond.value is False:
            self.optimizations_applied += 1
            if expr.else_block is not None:
                return self._block_to_expr(expr.else_block, expr.line, expr.column)
            # No else block — the when expression produces nothing useful;
            # return a placeholder IntegerLiteral(0) as Unit stand-in.
            return IntegerLiteral(value=0, line=expr.line, column=expr.column)

        return expr

    @staticmethod
    def _block_to_expr(block: Block, line: int, col: int) -> Expression:
        """Extract the meaningful expression from a single-statement block."""
        if len(block.statements) == 1:
            stmt = block.statements[0]
            if isinstance(stmt, ExpressionStatement):
                return stmt.expression
        # For multi-statement blocks or non-expression blocks, wrap in a
        # WhenExpression with a true condition so the block is preserved.
        return WhenExpression(
            condition=BoolLiteral(value=True, line=line, column=col),
            then_block=block,
            else_block=None,
            line=line,
            column=col,
        )
