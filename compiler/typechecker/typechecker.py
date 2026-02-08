"""VibeLang Type Checker implementation."""

from typing import Dict, List, Optional

from compiler.parser.ast_nodes import (
    ASTNode, Program, TypeDeclaration, FunctionDeclaration,
    SimpleType, SumType, Variant, RefinedType,
    Parameter, PrimitiveType, ArrayType, ResultType, FunctionType, NamedType,
    Expression, IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess,
    ArrayLiteral, RecordLiteral, WhenExpression, GivenExpression,
    PatternCase, Block, LetBinding, Assignment, ExpressionStatement,
)

PRIMITIVE_TYPES = {"Int", "Float", "Bool", "String", "Byte", "Unit"}

ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}
COMPARISON_OPS = {"<", ">", "<=", ">="}
EQUALITY_OPS = {"==", "!="}
LOGICAL_OPS = {"&&", "||"}


class TypeCheckError(Exception):
    """A type checking error with source location."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Type error at {line}:{column}: {message}")


def _type_to_str(type_node) -> str:
    """Convert a Type AST node to a string representation."""
    if isinstance(type_node, PrimitiveType):
        return type_node.name
    if isinstance(type_node, ArrayType):
        return f"Array[{_type_to_str(type_node.element_type)}]"
    if isinstance(type_node, ResultType):
        return f"Result[{_type_to_str(type_node.success_type)}, {_type_to_str(type_node.error_type)}]"
    if isinstance(type_node, FunctionType):
        params = ", ".join(_type_to_str(p) for p in type_node.param_types)
        return f"({params}) -> {_type_to_str(type_node.return_type)}"
    if isinstance(type_node, NamedType):
        if type_node.type_args:
            args = ", ".join(_type_to_str(a) for a in type_node.type_args)
            return f"{type_node.name}[{args}]"
        return type_node.name
    if isinstance(type_node, SimpleType):
        if type_node.type_args:
            args = ", ".join(_type_to_str(a) for a in type_node.type_args)
            return f"{type_node.name}[{args}]"
        return type_node.name
    return "Unknown"


class TypeChecker:
    """Type checker for VibeLang programs."""

    def __init__(self):
        self.type_env: Dict[str, str] = {}
        self.type_declarations: Dict[str, TypeDeclaration] = {}
        self.function_signatures: Dict[str, dict] = {}
        self.errors: List[TypeCheckError] = []

    def _error(self, message: str, node: ASTNode):
        err = TypeCheckError(message, node.line, node.column)
        self.errors.append(err)

    def check(self, program: Program) -> List[TypeCheckError]:
        """Check a full program and return a list of type errors."""
        self.errors = []
        self.type_env = {}
        self.type_declarations = {}
        self.function_signatures = {}

        for decl in program.declarations:
            if isinstance(decl, TypeDeclaration):
                self.check_type_declaration(decl)
            elif isinstance(decl, FunctionDeclaration):
                self.check_function_declaration(decl)

        return self.errors

    # ------------------------------------------------------------------
    # Type declarations
    # ------------------------------------------------------------------

    def check_type_declaration(self, decl: TypeDeclaration):
        """Register a type declaration and validate its invariants."""
        self.type_declarations[decl.name] = decl

        if isinstance(decl.definition, SimpleType):
            resolved = self._resolve_simple_type(decl.definition)
            self.type_env[decl.name] = resolved
        elif isinstance(decl.definition, SumType):
            self.type_env[decl.name] = decl.name
            for variant in decl.definition.variants:
                self.type_env[variant.name] = decl.name
        elif isinstance(decl.definition, RefinedType):
            base = _type_to_str(decl.definition.base_type)
            self.type_env[decl.name] = base

        # Validate invariants evaluate to Bool
        for inv in decl.invariants:
            inv_env = {"value": self.type_env.get(decl.name, "Unknown")}
            inv_type = self.infer_type(inv, inv_env)
            if inv_type != "Bool":
                self._error(
                    f"Invariant must be Bool, got {inv_type}",
                    inv,
                )

    def _resolve_simple_type(self, st: SimpleType) -> str:
        """Resolve a SimpleType to a string."""
        if st.type_args:
            args = ", ".join(_type_to_str(a) for a in st.type_args)
            return f"{st.name}[{args}]"
        return st.name

    # ------------------------------------------------------------------
    # Function declarations
    # ------------------------------------------------------------------

    def check_function_declaration(self, decl: FunctionDeclaration):
        """Type-check a function declaration."""
        ret_type_str = _type_to_str(decl.return_type)

        param_types: Dict[str, str] = {}
        for param in decl.parameters:
            param_types[param.name] = _type_to_str(param.type_annotation)

        self.function_signatures[decl.name] = {
            "params": param_types,
            "return_type": ret_type_str,
        }
        # Also store in type_env so the function name can be referenced
        self.type_env[decl.name] = ret_type_str

        # Build local environment for the function body
        local_env = dict(self.type_env)
        local_env.update(param_types)

        # Validate preconditions are Bool
        for pre in decl.preconditions:
            pre_type = self.infer_type(pre, local_env)
            if pre_type != "Bool":
                self._error(
                    f"Precondition must be Bool, got {pre_type}",
                    pre,
                )

        # Validate postconditions are Bool
        post_env = dict(local_env)
        post_env["result"] = ret_type_str
        for post in decl.postconditions:
            post_type = self.infer_type(post, post_env)
            if post_type != "Bool":
                self._error(
                    f"Postcondition must be Bool, got {post_type}",
                    post,
                )

        # Check body
        body_type = self._check_block(decl.body, local_env)
        if body_type != "Unknown" and ret_type_str != "Unknown":
            if not self._types_compatible(body_type, ret_type_str):
                self._error(
                    f"Function '{decl.name}' body type {body_type} "
                    f"does not match return type {ret_type_str}",
                    decl,
                )

    # ------------------------------------------------------------------
    # Block / statement checking
    # ------------------------------------------------------------------

    def _check_block(self, block: Block, env: dict) -> str:
        """Check statements in a block, return type of last expression."""
        result_type = "Unit"
        local_env = dict(env)

        for stmt in block.statements:
            if isinstance(stmt, LetBinding):
                val_type = self.infer_type(stmt.value, local_env)
                if stmt.type_annotation is not None:
                    ann_type = _type_to_str(stmt.type_annotation)
                    if val_type != "Unknown" and not self._types_compatible(val_type, ann_type):
                        self._error(
                            f"Let binding '{stmt.name}' type {ann_type} "
                            f"does not match value type {val_type}",
                            stmt,
                        )
                    local_env[stmt.name] = ann_type
                else:
                    local_env[stmt.name] = val_type
                result_type = "Unit"
            elif isinstance(stmt, Assignment):
                val_type = self.infer_type(stmt.value, local_env)
                target_type = local_env.get(stmt.target)
                if target_type and val_type != "Unknown":
                    if not self._types_compatible(val_type, target_type):
                        self._error(
                            f"Cannot assign {val_type} to '{stmt.target}' of type {target_type}",
                            stmt,
                        )
                result_type = "Unit"
            elif isinstance(stmt, ExpressionStatement):
                result_type = self.infer_type(stmt.expression, local_env)
            elif isinstance(stmt, Block):
                result_type = self._check_block(stmt, local_env)

        return result_type

    # ------------------------------------------------------------------
    # Expression type inference
    # ------------------------------------------------------------------

    def infer_type(self, expr: Expression, env: dict) -> str:
        """Infer the type of an expression given an environment."""
        if isinstance(expr, IntegerLiteral):
            return "Int"
        if isinstance(expr, FloatLiteral):
            return "Float"
        if isinstance(expr, StringLiteral):
            return "String"
        if isinstance(expr, BoolLiteral):
            return "Bool"

        if isinstance(expr, Identifier):
            t = env.get(expr.name)
            if t is not None:
                return t
            # Check function signatures
            sig = self.function_signatures.get(expr.name)
            if sig:
                return sig["return_type"]
            self._error(f"Undefined identifier '{expr.name}'", expr)
            return "Unknown"

        if isinstance(expr, BinaryOp):
            return self._infer_binary_op(expr, env)

        if isinstance(expr, UnaryOp):
            return self._infer_unary_op(expr, env)

        if isinstance(expr, FunctionCall):
            return self._infer_function_call(expr, env)

        if isinstance(expr, MemberAccess):
            self.infer_type(expr.obj, env)
            return "Unknown"

        if isinstance(expr, ArrayLiteral):
            if not expr.elements:
                return "Array[Unknown]"
            elem_type = self.infer_type(expr.elements[0], env)
            for elem in expr.elements[1:]:
                et = self.infer_type(elem, env)
                if et != elem_type and et != "Unknown" and elem_type != "Unknown":
                    self._error(
                        f"Array element type mismatch: expected {elem_type}, got {et}",
                        elem,
                    )
            return f"Array[{elem_type}]"

        if isinstance(expr, RecordLiteral):
            return "Unknown"

        if isinstance(expr, WhenExpression):
            cond_type = self.infer_type(expr.condition, env)
            if cond_type != "Bool" and cond_type != "Unknown":
                self._error(
                    f"When condition must be Bool, got {cond_type}",
                    expr.condition,
                )
            then_type = self._check_block(expr.then_block, env)
            if expr.else_block:
                else_type = self._check_block(expr.else_block, env)
                if then_type != else_type and then_type != "Unknown" and else_type != "Unknown":
                    self._error(
                        f"When branches have different types: {then_type} vs {else_type}",
                        expr,
                    )
            return then_type

        if isinstance(expr, GivenExpression):
            self.infer_type(expr.scrutinee, env)
            case_types = []
            for case in expr.cases:
                case_type = self.infer_type(case.expression, env)
                case_types.append(case_type)
            if case_types:
                return case_types[0]
            return "Unknown"

        return "Unknown"

    def _infer_binary_op(self, expr: BinaryOp, env: dict) -> str:
        left_type = self.infer_type(expr.left, env)
        right_type = self.infer_type(expr.right, env)
        op = expr.operator

        if op in ARITHMETIC_OPS:
            if left_type == "Unknown" or right_type == "Unknown":
                return "Unknown"
            if left_type == "Int" and right_type == "Int":
                return "Int"
            if left_type == "Float" and right_type == "Float":
                return "Float"
            if {left_type, right_type} == {"Int", "Float"}:
                return "Float"
            if op == "+" and left_type == "String" and right_type == "String":
                return "String"
            self._error(
                f"Cannot apply '{op}' to {left_type} and {right_type}",
                expr,
            )
            return "Unknown"

        if op in COMPARISON_OPS:
            if left_type == "Unknown" or right_type == "Unknown":
                return "Bool"
            if left_type in ("Int", "Float") and right_type in ("Int", "Float"):
                return "Bool"
            self._error(
                f"Cannot apply '{op}' to {left_type} and {right_type}",
                expr,
            )
            return "Bool"

        if op in EQUALITY_OPS:
            return "Bool"

        if op in LOGICAL_OPS:
            if left_type != "Bool" and left_type != "Unknown":
                self._error(
                    f"Left operand of '{op}' must be Bool, got {left_type}",
                    expr,
                )
            if right_type != "Bool" and right_type != "Unknown":
                self._error(
                    f"Right operand of '{op}' must be Bool, got {right_type}",
                    expr,
                )
            return "Bool"

        return "Unknown"

    def _infer_unary_op(self, expr: UnaryOp, env: dict) -> str:
        operand_type = self.infer_type(expr.operand, env)
        if expr.operator == "!":
            if operand_type != "Bool" and operand_type != "Unknown":
                self._error(
                    f"Operand of '!' must be Bool, got {operand_type}",
                    expr,
                )
            return "Bool"
        if expr.operator == "-":
            if operand_type in ("Int", "Float", "Unknown"):
                return operand_type
            self._error(
                f"Operand of unary '-' must be numeric, got {operand_type}",
                expr,
            )
            return "Unknown"
        return "Unknown"

    def _infer_function_call(self, expr: FunctionCall, env: dict) -> str:
        if isinstance(expr.function, Identifier):
            fname = expr.function.name
            sig = self.function_signatures.get(fname)
            if sig:
                expected_params = list(sig["params"].values())
                if len(expr.arguments) != len(expected_params):
                    self._error(
                        f"Function '{fname}' expects {len(expected_params)} "
                        f"arguments, got {len(expr.arguments)}",
                        expr,
                    )
                else:
                    for i, (arg, expected) in enumerate(
                        zip(expr.arguments, expected_params)
                    ):
                        arg_type = self.infer_type(arg, env)
                        if arg_type != "Unknown" and not self._types_compatible(arg_type, expected):
                            self._error(
                                f"Argument {i + 1} of '{fname}': expected {expected}, got {arg_type}",
                                arg,
                            )
                return sig["return_type"]

        # Fallback: infer type of function expression
        self.infer_type(expr.function, env)
        for arg in expr.arguments:
            self.infer_type(arg, env)
        return "Unknown"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _types_compatible(self, actual: str, expected: str) -> bool:
        """Check if actual type is compatible with expected type."""
        if actual == expected:
            return True
        if actual == "Unknown" or expected == "Unknown":
            return True
        # Int is promotable to Float
        if actual == "Int" and expected == "Float":
            return True
        # Check if actual is a type alias for expected
        if actual in self.type_declarations:
            resolved = self.type_env.get(actual)
            if resolved and self._types_compatible(resolved, expected):
                return True
        if expected in self.type_declarations:
            resolved = self.type_env.get(expected)
            if resolved and self._types_compatible(actual, resolved):
                return True
        return False
