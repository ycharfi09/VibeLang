"""VibeLang Formatter - pretty-prints AST back to canonical source code."""

from compiler.parser.ast_nodes import (
    Program, ImportStatement,
    TypeDeclaration, SimpleType, SumType, Variant,
    FunctionDeclaration, Parameter,
    Type, PrimitiveType, ArrayType, ResultType, FunctionType, NamedType,
    Expression, IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess,
    ArrayLiteral, RecordLiteral, WhenExpression, GivenExpression, PatternCase,
    Pattern, ConstructorPattern, IdentifierPattern, LiteralPattern, WildcardPattern,
    Block, ExpressionStatement,
)


class Formatter:
    def __init__(self, indent_size: int = 2):
        self.indent_size = indent_size

    def _indent(self, level: int) -> str:
        return " " * (self.indent_size * level)

    # ------------------------------------------------------------------
    # Program
    # ------------------------------------------------------------------

    def format(self, program: Program) -> str:
        """Format a program AST back to VibeLang source code."""
        parts: list[str] = []

        for imp in program.imports:
            parts.append(self.format_import(imp))

        if program.imports and program.declarations:
            parts.append("")

        for i, decl in enumerate(program.declarations):
            if isinstance(decl, TypeDeclaration):
                parts.append(self.format_type_declaration(decl))
            elif isinstance(decl, FunctionDeclaration):
                parts.append(self.format_function_declaration(decl))
            if i < len(program.declarations) - 1:
                parts.append("")

        return "\n".join(parts) + "\n" if parts else ""

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def format_import(self, node: ImportStatement) -> str:
        return f"import {node.module_path}"

    # ------------------------------------------------------------------
    # Type declaration
    # ------------------------------------------------------------------

    def format_type_declaration(self, decl: TypeDeclaration) -> str:
        lines: list[str] = []
        header = f"type {decl.name}"
        if decl.type_params:
            header += "[" + ", ".join(decl.type_params) + "]"
        header += " = " + self.format_type_definition(decl.definition)
        lines.append(header)

        for inv in decl.invariants:
            lines.append(self._indent(1) + "invariant " + self.format_expression(inv))

        return "\n".join(lines)

    def format_type_definition(self, defn) -> str:
        if isinstance(defn, SumType):
            parts = []
            for v in defn.variants:
                part = "| " + v.name
                if v.parameters:
                    part += "(" + ", ".join(self.format_type(t) for t in v.parameters) + ")"
                parts.append(part)
            return "\n  ".join([""] + parts).strip() if len(parts) == 1 else "\n  " + "\n  ".join(parts)
        if isinstance(defn, SimpleType):
            s = defn.name
            if defn.type_args:
                s += "[" + ", ".join(self.format_type(t) for t in defn.type_args) + "]"
            return s
        return str(defn)

    # ------------------------------------------------------------------
    # Function declaration
    # ------------------------------------------------------------------

    def format_function_declaration(self, decl: FunctionDeclaration) -> str:
        lines: list[str] = []
        params = ", ".join(
            f"{p.name}: {self.format_type(p.type_annotation)}" for p in decl.parameters
        )
        sig = f"define {decl.name}({params}) -> {self.format_type(decl.return_type)}"
        lines.append(sig)

        for pre in decl.preconditions:
            lines.append(self._indent(1) + "expect " + self.format_expression(pre))
        for post in decl.postconditions:
            lines.append(self._indent(1) + "ensure " + self.format_expression(post))

        lines.append("given")
        lines.extend(self.format_block(decl.body, level=1))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Types
    # ------------------------------------------------------------------

    def format_type(self, t: Type) -> str:
        if isinstance(t, PrimitiveType):
            return t.name
        if isinstance(t, ArrayType):
            return f"Array[{self.format_type(t.element_type)}]"
        if isinstance(t, ResultType):
            return f"Result[{self.format_type(t.success_type)}, {self.format_type(t.error_type)}]"
        if isinstance(t, FunctionType):
            params = ", ".join(self.format_type(p) for p in t.param_types)
            return f"({params}) -> {self.format_type(t.return_type)}"
        if isinstance(t, NamedType):
            s = t.name
            if t.type_args:
                s += "[" + ", ".join(self.format_type(a) for a in t.type_args) + "]"
            return s
        return str(t)

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def format_expression(self, expr: Expression) -> str:
        if isinstance(expr, IntegerLiteral):
            return str(expr.value)
        if isinstance(expr, FloatLiteral):
            return str(expr.value)
        if isinstance(expr, StringLiteral):
            escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(expr, BoolLiteral):
            return "true" if expr.value else "false"
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, BinaryOp):
            left = self.format_expression(expr.left)
            right = self.format_expression(expr.right)
            return f"{left} {expr.operator} {right}"
        if isinstance(expr, UnaryOp):
            operand = self.format_expression(expr.operand)
            return f"{expr.operator}{operand}"
        if isinstance(expr, FunctionCall):
            func = self.format_expression(expr.function)
            args = ", ".join(self.format_expression(a) for a in expr.arguments)
            return f"{func}({args})"
        if isinstance(expr, MemberAccess):
            obj = self.format_expression(expr.obj)
            return f"{obj}.{expr.member}"
        if isinstance(expr, ArrayLiteral):
            elems = ", ".join(self.format_expression(e) for e in expr.elements)
            return f"[{elems}]"
        if isinstance(expr, RecordLiteral):
            fields = ", ".join(
                f"{name}: {self.format_expression(val)}" for name, val in expr.fields
            )
            return "{ " + fields + " }"
        if isinstance(expr, WhenExpression):
            return self._format_when_inline(expr)
        if isinstance(expr, GivenExpression):
            return self._format_given_inline(expr)
        return str(expr)

    def _format_when_inline(self, expr: WhenExpression) -> str:
        parts = ["when " + self.format_expression(expr.condition)]
        if expr.else_block:
            parts.append(" otherwise")
        return " ".join(parts)

    def _format_given_inline(self, expr: GivenExpression) -> str:
        return "given " + self.format_expression(expr.scrutinee)

    # ------------------------------------------------------------------
    # Patterns
    # ------------------------------------------------------------------

    def format_pattern(self, pat: Pattern) -> str:
        if isinstance(pat, ConstructorPattern):
            if pat.parameters:
                params = ", ".join(self.format_pattern(p) for p in pat.parameters)
                return f"{pat.constructor}({params})"
            return pat.constructor
        if isinstance(pat, IdentifierPattern):
            return pat.name
        if isinstance(pat, LiteralPattern):
            if isinstance(pat.value, str):
                return f'"{pat.value}"'
            if isinstance(pat.value, bool):
                return "true" if pat.value else "false"
            return str(pat.value)
        if isinstance(pat, WildcardPattern):
            return "_"
        return str(pat)

    # ------------------------------------------------------------------
    # Blocks / Statements
    # ------------------------------------------------------------------

    def format_block(self, block: Block, level: int = 1) -> list[str]:
        lines: list[str] = []
        for stmt in block.statements:
            if isinstance(stmt, ExpressionStatement):
                expr = stmt.expression
                if isinstance(expr, WhenExpression):
                    lines.extend(self._format_when_block(expr, level))
                elif isinstance(expr, GivenExpression):
                    lines.extend(self._format_given_block(expr, level))
                else:
                    lines.append(self._indent(level) + self.format_expression(expr))
            else:
                lines.append(self._indent(level) + str(stmt))
        return lines

    def _format_when_block(self, expr: WhenExpression, level: int) -> list[str]:
        lines = [self._indent(level) + "when " + self.format_expression(expr.condition)]
        lines.extend(self.format_block(expr.then_block, level + 1))
        if expr.else_block:
            lines.append(self._indent(level) + "otherwise")
            lines.extend(self.format_block(expr.else_block, level + 1))
        return lines

    def _format_given_block(self, expr: GivenExpression, level: int) -> list[str]:
        lines = [self._indent(level) + "given " + self.format_expression(expr.scrutinee)]
        for case in expr.cases:
            pat = self.format_pattern(case.pattern)
            body = self.format_expression(case.expression)
            lines.append(self._indent(level + 1) + f"{pat} -> {body}")
        return lines
