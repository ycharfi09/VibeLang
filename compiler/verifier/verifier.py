"""VibeLang Lightweight Symbolic Verifier.

Provides contract verification without requiring Z3. Reasons about simple
numeric contracts using constant evaluation, inequality reasoning, and
assumption propagation from preconditions to postconditions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, Union
from enum import Enum

from compiler.parser.ast_nodes import (
    Program, FunctionDeclaration, TypeDeclaration,
    Expression, BinaryOp, UnaryOp, Identifier, IntegerLiteral,
    FloatLiteral, BoolLiteral, StringLiteral, FunctionCall,
    MemberAccess,
)


class VerificationStatus(Enum):
    PROVEN = "proven"
    UNPROVEN = "unproven"
    VIOLATED = "violated"


@dataclass
class VerificationResult:
    function_name: str
    contract_type: str  # "precondition", "postcondition", "invariant"
    status: VerificationStatus
    message: str
    line: int
    column: int


# ---------------------------------------------------------------------------
# Symbolic value representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SymbolicBound:
    """Known bound for a symbolic variable: var OP constant."""
    var: str
    op: str   # ">=", ">", "<=", "<", "=="
    value: Union[int, float]


class SymbolicEvaluator:
    """Evaluate expressions symbolically under a set of assumptions."""

    def __init__(self, assumptions: Optional[List[SymbolicBound]] = None):
        self.assumptions: List[SymbolicBound] = list(assumptions or [])

    def add_assumption(self, bound: SymbolicBound):
        self.assumptions.append(bound)

    # ------------------------------------------------------------------
    # Constant folding
    # ------------------------------------------------------------------

    def try_eval_constant(self, expr: Expression) -> Optional[Union[int, float, bool]]:
        """Try to evaluate an expression to a constant value."""
        if isinstance(expr, IntegerLiteral):
            return expr.value
        if isinstance(expr, FloatLiteral):
            return expr.value
        if isinstance(expr, BoolLiteral):
            return expr.value

        if isinstance(expr, UnaryOp):
            operand = self.try_eval_constant(expr.operand)
            if operand is None:
                return None
            if expr.operator == "-" and isinstance(operand, (int, float)):
                return -operand
            if expr.operator == "!" and isinstance(operand, bool):
                return not operand
            return None

        if isinstance(expr, BinaryOp):
            left = self.try_eval_constant(expr.left)
            right = self.try_eval_constant(expr.right)
            if left is None or right is None:
                return None
            return self._eval_binary(left, expr.operator, right)

        return None

    @staticmethod
    def _eval_binary(left, op: str, right):
        """Evaluate a binary operation on constant values."""
        try:
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    return None
                return left / right if isinstance(left, float) or isinstance(right, float) else left // right
            if op == "%":
                if right == 0:
                    return None
                return left % right
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
            if op == "&&":
                return left and right
            if op == "||":
                return left or right
        except (TypeError, ZeroDivisionError):
            return None
        return None

    # ------------------------------------------------------------------
    # Symbolic truth checking
    # ------------------------------------------------------------------

    def check_truth(self, expr: Expression) -> Optional[bool]:
        """Determine the truth value of *expr* if possible.

        Returns True  – definitely true
                False – definitely false
                None  – unknown
        """
        const = self.try_eval_constant(expr)
        if const is not None:
            return bool(const)

        if isinstance(expr, BoolLiteral):
            return expr.value

        # Logical connectives
        if isinstance(expr, BinaryOp):
            if expr.operator == "&&":
                lt = self.check_truth(expr.left)
                rt = self.check_truth(expr.right)
                if lt is False or rt is False:
                    return False
                if lt is True and rt is True:
                    return True
                return None
            if expr.operator == "||":
                lt = self.check_truth(expr.left)
                rt = self.check_truth(expr.right)
                if lt is True or rt is True:
                    return True
                if lt is False and rt is False:
                    return False
                return None

            return self._check_comparison(expr)

        if isinstance(expr, UnaryOp) and expr.operator == "!":
            inner = self.check_truth(expr.operand)
            if inner is None:
                return None
            return not inner

        return None

    # ------------------------------------------------------------------
    # Comparison reasoning
    # ------------------------------------------------------------------

    def _check_comparison(self, expr: BinaryOp) -> Optional[bool]:
        """Reason about comparison expressions using assumptions."""
        op = expr.operator
        if op not in (">=", ">", "<=", "<", "==", "!="):
            return None

        # x OP x  (reflexive: x >= x, x <= x, x == x are true)
        if self._structurally_equal(expr.left, expr.right):
            if op in (">=", "<=", "=="):
                return True
            if op in (">", "<"):
                return False
            if op == "!=":
                return False

        # Simple var OP constant  checked against assumptions
        result = self._check_var_const(expr.left, op, expr.right)
        if result is not None:
            return result

        # constant OP var  – flip
        flipped_op = _flip_op(op)
        if flipped_op is not None:
            result = self._check_var_const(expr.right, flipped_op, expr.left)
            if result is not None:
                return result

        # x + y >= x  when y >= 0  (and similar)
        result = self._check_additive_pattern(expr)
        if result is not None:
            return result

        return None

    def _check_var_const(self, var_expr: Expression, op: str, const_expr: Expression) -> Optional[bool]:
        """Check  var OP constant  against assumptions."""
        if not isinstance(var_expr, Identifier):
            return None
        const = self.try_eval_constant(const_expr)
        if const is None:
            return None
        name = var_expr.name

        for a in self.assumptions:
            if a.var != name:
                continue
            result = _implies(a.op, a.value, op, const)
            if result is not None:
                return result

        return None

    def _check_additive_pattern(self, expr: BinaryOp) -> Optional[bool]:
        """Check patterns like  x + y >= x  when  y >= 0."""
        op = expr.operator
        if op not in (">=", ">", "<=", "<"):
            return None

        left = expr.left
        right = expr.right

        # Pattern: (a + b) >= a  or  (a + b) > a
        if isinstance(left, BinaryOp) and left.operator == "+":
            if self._structurally_equal(left.left, right):
                return self._check_addend_sign(left.right, op)
            if self._structurally_equal(left.right, right):
                return self._check_addend_sign(left.left, op)

        # Pattern: a <= (a + b)  or  a < (a + b)
        if isinstance(right, BinaryOp) and right.operator == "+":
            flipped = _flip_op(op)
            if flipped and self._structurally_equal(right.left, left):
                return self._check_addend_sign(right.right, flipped)
            if flipped and self._structurally_equal(right.right, left):
                return self._check_addend_sign(right.left, flipped)

        return None

    def _check_addend_sign(self, addend: Expression, op: str) -> Optional[bool]:
        """Given that the comparison reduces to  addend OP 0, decide truth."""
        if op == ">=" or op == "<=":
            target_op = ">=" if op == ">=" else "<="
        elif op == ">" or op == "<":
            target_op = ">" if op == ">" else "<"
        else:
            return None

        # Try constant value
        const = self.try_eval_constant(addend)
        if const is not None:
            if target_op == ">=":
                return const >= 0
            if target_op == ">":
                return const > 0
            if target_op == "<=":
                return const <= 0
            if target_op == "<":
                return const < 0

        # Check assumptions on the addend
        if isinstance(addend, Identifier):
            for a in self.assumptions:
                if a.var != addend.name:
                    continue
                result = _implies(a.op, a.value, target_op, 0)
                if result is not None:
                    return result

        return None

    # ------------------------------------------------------------------
    # Structural equality
    # ------------------------------------------------------------------

    @staticmethod
    def _structurally_equal(a: Expression, b: Expression) -> bool:
        """Shallow structural equality for expressions."""
        if type(a) is not type(b):
            return False
        if isinstance(a, Identifier):
            return a.name == b.name
        if isinstance(a, IntegerLiteral):
            return a.value == b.value
        if isinstance(a, FloatLiteral):
            return a.value == b.value
        if isinstance(a, BoolLiteral):
            return a.value == b.value
        if isinstance(a, StringLiteral):
            return a.value == b.value
        return False

    # ------------------------------------------------------------------
    # Extract assumptions from an expression
    # ------------------------------------------------------------------

    def extract_bounds(self, expr: Expression) -> List[SymbolicBound]:
        """Extract simple bounds from a contract expression."""
        bounds: List[SymbolicBound] = []

        if isinstance(expr, BinaryOp):
            if expr.operator == "&&":
                bounds.extend(self.extract_bounds(expr.left))
                bounds.extend(self.extract_bounds(expr.right))
                return bounds

            if expr.operator in (">=", ">", "<=", "<", "=="):
                b = self._extract_single_bound(expr.left, expr.operator, expr.right)
                if b:
                    bounds.append(b)
                # Also try the flipped direction
                flipped = _flip_op(expr.operator)
                if flipped:
                    b = self._extract_single_bound(expr.right, flipped, expr.left)
                    if b:
                        bounds.append(b)

        return bounds

    @staticmethod
    def _extract_single_bound(left: Expression, op: str, right: Expression) -> Optional[SymbolicBound]:
        """Extract a bound of the form  var OP constant."""
        if isinstance(left, Identifier):
            val: Optional[Union[int, float]] = None
            if isinstance(right, IntegerLiteral):
                val = right.value
            elif isinstance(right, FloatLiteral):
                val = right.value
            if val is not None:
                return SymbolicBound(var=left.name, op=op, value=val)
        return None


# ---------------------------------------------------------------------------
# Helper: implication between bounds
# ---------------------------------------------------------------------------

def _flip_op(op: str) -> Optional[str]:
    """Flip a comparison operator (swap operands)."""
    return {">=": "<=", "<=": ">=", ">": "<", "<": ">", "==": "==", "!=": "!="}.get(op)


def _implies(known_op: str, known_val, query_op: str, query_val) -> Optional[bool]:
    """Does  (var known_op known_val) imply (var query_op query_val)?

    Returns True/False/None.
    """
    # known: var >= K  =>  var >= Q  when K >= Q
    if known_op == ">=" and query_op == ">=":
        return True if known_val >= query_val else None
    if known_op == ">=" and query_op == ">":
        return True if known_val > query_val else None
    if known_op == ">" and query_op == ">=":
        return True if known_val >= query_val else None
    if known_op == ">" and query_op == ">":
        return True if known_val >= query_val else None

    if known_op == "<=" and query_op == "<=":
        return True if known_val <= query_val else None
    if known_op == "<=" and query_op == "<":
        return True if known_val < query_val else None
    if known_op == "<" and query_op == "<=":
        return True if known_val <= query_val else None
    if known_op == "<" and query_op == "<":
        return True if known_val <= query_val else None

    # Equality is very precise
    if known_op == "==":
        if query_op == "==":
            return known_val == query_val
        if query_op == "!=":
            return known_val != query_val
        if query_op == ">=":
            return known_val >= query_val
        if query_op == ">":
            return known_val > query_val
        if query_op == "<=":
            return known_val <= query_val
        if query_op == "<":
            return known_val < query_val

    # Contradiction detection
    if known_op == ">=" and query_op == "<":
        if known_val >= query_val:
            return False
    if known_op == ">" and query_op == "<=":
        if known_val >= query_val:
            return False
    if known_op == "<=" and query_op == ">":
        if known_val <= query_val:
            return False
    if known_op == "<" and query_op == ">=":
        if known_val <= query_val:
            return False

    return None


# ---------------------------------------------------------------------------
# Main Verifier
# ---------------------------------------------------------------------------

class Verifier:
    """Lightweight symbolic contract verifier for VibeLang programs."""

    def __init__(self):
        self.results: List[VerificationResult] = []

    def verify(self, program: Program) -> List[VerificationResult]:
        """Verify all contracts in a program."""
        self.results = []
        for decl in program.declarations:
            if isinstance(decl, FunctionDeclaration):
                self._verify_function(decl)
            elif isinstance(decl, TypeDeclaration):
                self._verify_type_invariants(decl)
        return list(self.results)

    # ------------------------------------------------------------------
    # Function verification
    # ------------------------------------------------------------------

    def _verify_function(self, func: FunctionDeclaration):
        evaluator = SymbolicEvaluator()

        # Verify each precondition in isolation (they must be satisfiable)
        for pre in func.preconditions:
            self._check_contract(
                evaluator, pre, func.name, "precondition",
            )

        # Build assumption set from preconditions
        pre_evaluator = SymbolicEvaluator()
        for pre in func.preconditions:
            for bound in pre_evaluator.extract_bounds(pre):
                pre_evaluator.add_assumption(bound)

        # Verify postconditions under the assumption of preconditions
        for post in func.postconditions:
            self._check_contract(
                pre_evaluator, post, func.name, "postcondition",
            )

    # ------------------------------------------------------------------
    # Type invariant verification
    # ------------------------------------------------------------------

    def _verify_type_invariants(self, td: TypeDeclaration):
        evaluator = SymbolicEvaluator()

        # Build cumulative assumptions as we go through invariants
        for inv in td.invariants:
            self._check_contract(
                evaluator, inv, td.name, "invariant",
            )
            for bound in evaluator.extract_bounds(inv):
                evaluator.add_assumption(bound)

    # ------------------------------------------------------------------
    # Core contract checking
    # ------------------------------------------------------------------

    def _check_contract(
        self,
        evaluator: SymbolicEvaluator,
        expr: Expression,
        name: str,
        contract_type: str,
    ):
        truth = evaluator.check_truth(expr)

        if truth is True:
            self.results.append(VerificationResult(
                function_name=name,
                contract_type=contract_type,
                status=VerificationStatus.PROVEN,
                message=f"{contract_type.capitalize()} is trivially true",
                line=expr.line,
                column=expr.column,
            ))
        elif truth is False:
            self.results.append(VerificationResult(
                function_name=name,
                contract_type=contract_type,
                status=VerificationStatus.VIOLATED,
                message=f"{contract_type.capitalize()} is trivially false",
                line=expr.line,
                column=expr.column,
            ))
        else:
            self.results.append(VerificationResult(
                function_name=name,
                contract_type=contract_type,
                status=VerificationStatus.UNPROVEN,
                message=f"{contract_type.capitalize()} could not be statically verified",
                line=expr.line,
                column=expr.column,
            ))
