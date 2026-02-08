"""VibeLang Code Generator - translates VibeLang AST to Python source code."""

from compiler.parser.ast_nodes import (
    Program, ImportStatement,
    TypeDeclaration, SimpleType, SumType, Variant, RefinedType,
    FunctionDeclaration, Parameter,
    Type, PrimitiveType, ArrayType, ResultType, FunctionType, NamedType,
    Expression, IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess,
    ArrayLiteral, RecordLiteral, WhenExpression, GivenExpression, PatternCase,
    Pattern, ConstructorPattern, IdentifierPattern, LiteralPattern, WildcardPattern,
    Statement, Block, LetBinding, Assignment, ExpressionStatement,
)


class CodeGenError(Exception):
    """Code generation error."""
    pass


# Operator translation from VibeLang to Python
_BINARY_OP_MAP = {
    "&&": "and",
    "||": "or",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "//",
    "%": "%",
    "==": "==",
    "!=": "!=",
    "<": "<",
    ">": ">",
    "<=": "<=",
    ">=": ">=",
}

_UNARY_OP_MAP = {
    "!": "not ",
    "-": "-",
}

_RUNTIME_HEADER = '''\
# --- VibeLang Runtime ---
class _VL_Success:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Success({self.value!r})"

class _VL_Error:
    def __init__(self, error):
        self.error = error
    def __repr__(self):
        return f"Error({self.error!r})"
# --- End Runtime ---
'''


class CodeGenerator:
    """Translates a VibeLang AST into Python source code."""

    def __init__(self):
        self.indent_level = 0
        self.output_lines = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, program: Program) -> str:
        """Generate Python code from a VibeLang Program AST."""
        self.indent_level = 0
        self.output_lines = []

        self._emit_raw(_RUNTIME_HEADER)

        for imp in program.imports:
            self._gen_import(imp)

        if program.imports:
            self._emit("")

        for decl in program.declarations:
            if isinstance(decl, TypeDeclaration):
                self._gen_type_declaration(decl)
            elif isinstance(decl, FunctionDeclaration):
                self._gen_function_declaration(decl)
            else:
                raise CodeGenError(f"Unknown declaration type: {type(decl).__name__}")
            self._emit("")

        return "\n".join(self.output_lines).rstrip("\n") + "\n"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _indent(self) -> str:
        return "    " * self.indent_level

    def _emit(self, line: str = ""):
        self.output_lines.append(self._indent() + line if line else "")

    def _emit_raw(self, text: str):
        for line in text.splitlines():
            self.output_lines.append(line)

    # ------------------------------------------------------------------
    # Imports
    # ------------------------------------------------------------------

    def _gen_import(self, node: ImportStatement):
        self._emit(f"import {node.module_path}")

    # ------------------------------------------------------------------
    # Type Declarations
    # ------------------------------------------------------------------

    def _gen_type_declaration(self, node: TypeDeclaration):
        if isinstance(node.definition, SumType):
            self._gen_sum_type(node.name, node.definition)
        elif isinstance(node.definition, SimpleType):
            self._gen_simple_type(node.name, node.definition, node.invariants)
        elif isinstance(node.definition, RefinedType):
            self._gen_refined_type(node.name, node.definition)
        else:
            raise CodeGenError(
                f"Unknown type definition: {type(node.definition).__name__}"
            )

    def _gen_sum_type(self, type_name: str, sum_type: SumType):
        # Base class
        self._emit(f"class {type_name}:")
        self.indent_level += 1
        self._emit("pass")
        self.indent_level -= 1
        self._emit("")

        # Variant subclasses
        for variant in sum_type.variants:
            self._gen_variant(type_name, variant)

    def _gen_variant(self, base_name: str, variant: Variant):
        self._emit(f"class {variant.name}({base_name}):")
        self.indent_level += 1
        if variant.parameters:
            params = ", ".join(f"v{i}" for i in range(len(variant.parameters)))
            self._emit(f"def __init__(self, {params}):")
            self.indent_level += 1
            for i in range(len(variant.parameters)):
                self._emit(f"self.v{i} = v{i}")
            self.indent_level -= 1
        else:
            self._emit("pass")
        self.indent_level -= 1
        self._emit("")

    def _gen_simple_type(self, name: str, simple: SimpleType, invariants):
        self._emit(f"class {name}:")
        self.indent_level += 1
        self._emit("def __init__(self, value):")
        self.indent_level += 1
        for inv in invariants:
            inv_code = self._gen_expr(inv)
            self._emit(f"assert {inv_code}, \"Invariant violated for {name}\"")
        self._emit("self.value = value")
        self.indent_level -= 1
        self.indent_level -= 1

    def _gen_refined_type(self, name: str, refined: RefinedType):
        self._emit(f"class {name}:")
        self.indent_level += 1
        self._emit("def __init__(self, value):")
        self.indent_level += 1
        cond = self._gen_expr(refined.condition)
        self._emit(f"assert {cond}, \"Refinement violated for {name}\"")
        self._emit("self.value = value")
        self.indent_level -= 1
        self.indent_level -= 1

    # ------------------------------------------------------------------
    # Function Declarations
    # ------------------------------------------------------------------

    def _gen_function_declaration(self, node: FunctionDeclaration):
        params = ", ".join(p.name for p in node.parameters)
        self._emit(f"def {node.name}({params}):")
        self.indent_level += 1

        # Preconditions (expect)
        for pre in node.preconditions:
            pre_code = self._gen_expr(pre)
            self._emit(f"# expect: {pre_code}")
            self._emit(f"assert {pre_code}, \"Precondition failed: {pre_code}\"")

        # Body
        self._gen_block_body(node.body)

        # Postconditions (ensure)
        if node.postconditions:
            for post in node.postconditions:
                post_code = self._gen_expr(post)
                self._emit(f"# ensure: {post_code}")
                self._emit(
                    f"assert {post_code}, \"Postcondition failed: {post_code}\""
                )

        self.indent_level -= 1

    # ------------------------------------------------------------------
    # Blocks / Statements
    # ------------------------------------------------------------------

    def _gen_block_body(self, block: Block):
        """Emit the statements inside a block (without changing indent)."""
        if not block.statements:
            self._emit("pass")
            return

        last_idx = len(block.statements) - 1
        for i, stmt in enumerate(block.statements):
            self._gen_statement(stmt, is_last=(i == last_idx))

    def _gen_statement(self, stmt: Statement, is_last: bool = False):
        if isinstance(stmt, LetBinding):
            val = self._gen_expr(stmt.value)
            self._emit(f"{stmt.name} = {val}")
        elif isinstance(stmt, Assignment):
            val = self._gen_expr(stmt.value)
            self._emit(f"{stmt.target} = {val}")
        elif isinstance(stmt, ExpressionStatement):
            expr_code = self._gen_expr(stmt.expression)
            if is_last:
                self._emit(f"result = {expr_code}")
                self._emit("return result")
            else:
                self._emit(expr_code)
        elif isinstance(stmt, Block):
            self._gen_block_body(stmt)
        else:
            raise CodeGenError(f"Unknown statement type: {type(stmt).__name__}")

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _gen_expr(self, expr: Expression) -> str:
        if isinstance(expr, IntegerLiteral):
            return str(expr.value)
        if isinstance(expr, FloatLiteral):
            return repr(expr.value)
        if isinstance(expr, StringLiteral):
            return repr(expr.value)
        if isinstance(expr, BoolLiteral):
            return "True" if expr.value else "False"
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, BinaryOp):
            return self._gen_binary_op(expr)
        if isinstance(expr, UnaryOp):
            return self._gen_unary_op(expr)
        if isinstance(expr, FunctionCall):
            return self._gen_function_call(expr)
        if isinstance(expr, MemberAccess):
            return f"{self._gen_expr(expr.obj)}.{expr.member}"
        if isinstance(expr, ArrayLiteral):
            elems = ", ".join(self._gen_expr(e) for e in expr.elements)
            return f"[{elems}]"
        if isinstance(expr, RecordLiteral):
            fields = ", ".join(
                f"{repr(k)}: {self._gen_expr(v)}" for k, v in expr.fields
            )
            return "{" + fields + "}"
        if isinstance(expr, WhenExpression):
            return self._gen_when_expr(expr)
        if isinstance(expr, GivenExpression):
            return self._gen_given_expr(expr)
        raise CodeGenError(f"Unknown expression type: {type(expr).__name__}")

    def _gen_binary_op(self, expr: BinaryOp) -> str:
        left = self._gen_expr(expr.left)
        right = self._gen_expr(expr.right)
        py_op = _BINARY_OP_MAP.get(expr.operator, expr.operator)
        return f"({left} {py_op} {right})"

    def _gen_unary_op(self, expr: UnaryOp) -> str:
        operand = self._gen_expr(expr.operand)
        py_op = _UNARY_OP_MAP.get(expr.operator, expr.operator)
        return f"({py_op}{operand})"

    def _gen_function_call(self, expr: FunctionCall) -> str:
        func = self._gen_expr(expr.function)
        args = ", ".join(self._gen_expr(a) for a in expr.arguments)
        return f"{func}({args})"

    def _gen_when_expr(self, expr: WhenExpression) -> str:
        """Generate a when/otherwise as an inline expression using a helper.

        For statement-level usage we emit if/else blocks instead.
        """
        cond = self._gen_expr(expr.condition)
        then_code = self._gen_block_return_expr(expr.then_block)
        if expr.else_block:
            else_code = self._gen_block_return_expr(expr.else_block)
            return f"({then_code} if {cond} else {else_code})"
        return f"({then_code} if {cond} else None)"

    def _gen_when_statement(self, expr: WhenExpression):
        """Emit when/otherwise as if/else statement blocks."""
        cond = self._gen_expr(expr.condition)
        self._emit(f"if {cond}:")
        self.indent_level += 1
        self._gen_block_body(expr.then_block)
        self.indent_level -= 1
        if expr.else_block:
            self._emit("else:")
            self.indent_level += 1
            self._gen_block_body(expr.else_block)
            self.indent_level -= 1

    def _gen_block_return_expr(self, block: Block) -> str:
        """Return the expression value of the last statement in a block."""
        if block.statements:
            last = block.statements[-1]
            if isinstance(last, ExpressionStatement):
                return self._gen_expr(last.expression)
        return "None"

    def _gen_given_expr(self, expr: GivenExpression) -> str:
        """Generate given/pattern-match as a helper lambda with chained ifs."""
        scrutinee = self._gen_expr(expr.scrutinee)
        parts = []
        for case in expr.cases:
            cond = self._gen_pattern_condition("_vl_scrutinee", case.pattern)
            val = self._gen_expr(case.expression)
            parts.append((cond, val))

        # Build a chained conditional expression
        if not parts:
            return "None"

        result = "None"
        for cond, val in reversed(parts):
            if cond == "True":
                result = val
            else:
                result = f"({val} if {cond} else {result})"

        return f"(lambda _vl_scrutinee: {result})({scrutinee})"

    def _gen_pattern_condition(self, var: str, pattern: Pattern) -> str:
        if isinstance(pattern, LiteralPattern):
            return f"{var} == {repr(pattern.value)}"
        if isinstance(pattern, IdentifierPattern):
            return "True"
        if isinstance(pattern, WildcardPattern):
            return "True"
        if isinstance(pattern, ConstructorPattern):
            return f"isinstance({var}, {pattern.constructor})"
        raise CodeGenError(f"Unknown pattern type: {type(pattern).__name__}")
