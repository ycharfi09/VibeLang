"""Tests for the VibeLang lightweight symbolic verifier."""

import pytest

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.verifier import Verifier, VerificationResult, VerificationStatus


def parse(source: str):
    """Helper: lex + parse source code into an AST."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def verify(source: str):
    """Helper: lex + parse + verify, return results."""
    program = parse(source)
    return Verifier().verify(program)


# -----------------------------------------------------------------------
# Trivially true contracts
# -----------------------------------------------------------------------

class TestTriviallyTrue:
    def test_bool_true_precondition(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect true\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert len(results) == 1
        assert results[0].status == VerificationStatus.PROVEN

    def test_constant_comparison_true(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect 1 > 0\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN

    def test_reflexive_geq(self):
        """x >= x is always true."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x >= x\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN

    def test_reflexive_eq(self):
        """x == x is always true."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x == x\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN

    def test_constant_arithmetic(self):
        """2 + 3 > 4 should be proven."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect 2 + 3 > 4\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN


# -----------------------------------------------------------------------
# Trivially false contracts
# -----------------------------------------------------------------------

class TestTriviallyFalse:
    def test_bool_false_precondition(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect false\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED

    def test_constant_contradiction(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect 1 > 2\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED

    def test_reflexive_strict_gt(self):
        """x > x is always false."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x > x\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED

    def test_reflexive_neq(self):
        """x != x is always false."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x != x\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED


# -----------------------------------------------------------------------
# Simple numeric verification with assumptions
# -----------------------------------------------------------------------

class TestNumericVerification:
    def test_precondition_implies_postcondition(self):
        """Given x >= 0, postcondition x >= 0 should be proven."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "  ensure x >= 0\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        # precondition is unproven (no info), postcondition should be proven
        pre = [r for r in results if r.contract_type == "precondition"]
        post = [r for r in results if r.contract_type == "postcondition"]
        assert len(post) == 1
        assert post[0].status == VerificationStatus.PROVEN

    def test_stronger_precondition_implies_weaker(self):
        """Given x >= 5, postcondition x >= 0 should be proven."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 5\n"
            "  ensure x >= 0\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        post = [r for r in results if r.contract_type == "postcondition"]
        assert post[0].status == VerificationStatus.PROVEN

    def test_sum_nonnegative(self):
        """Given x >= 0 and y >= 0, x + y >= x should be proven."""
        src = (
            "define f(x: Int, y: Int) -> Int\n"
            "  expect x >= 0\n"
            "  expect y >= 0\n"
            "  ensure x + y >= x\n"
            "given\n"
            "  x + y"
        )
        results = verify(src)
        post = [r for r in results if r.contract_type == "postcondition"]
        assert post[0].status == VerificationStatus.PROVEN

    def test_multiple_preconditions_build_context(self):
        """Both x >= 0 and y >= 0 are used together."""
        src = (
            "define f(x: Int, y: Int) -> Int\n"
            "  expect x >= 0\n"
            "  expect y >= 0\n"
            "  ensure y >= 0\n"
            "given\n"
            "  x + y"
        )
        results = verify(src)
        post = [r for r in results if r.contract_type == "postcondition"]
        assert post[0].status == VerificationStatus.PROVEN


# -----------------------------------------------------------------------
# Unproven / complex contracts
# -----------------------------------------------------------------------

class TestUnproven:
    def test_function_call_in_contract(self):
        """Contracts involving function calls cannot be statically verified."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect g(x) > 0\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.UNPROVEN

    def test_member_access_in_contract(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x.value > 0\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.UNPROVEN

    def test_unrelated_postcondition(self):
        """Postcondition about a variable not constrained by preconditions."""
        src = (
            "define f(x: Int, y: Int) -> Int\n"
            "  expect x >= 0\n"
            "  ensure y >= 0\n"
            "given\n"
            "  x + y"
        )
        results = verify(src)
        post = [r for r in results if r.contract_type == "postcondition"]
        assert post[0].status == VerificationStatus.UNPROVEN


# -----------------------------------------------------------------------
# Invariant verification
# -----------------------------------------------------------------------

class TestInvariants:
    def test_trivially_true_invariant(self):
        src = (
            "type PositiveInt = Int\n"
            "  invariant true"
        )
        results = verify(src)
        assert len(results) == 1
        assert results[0].status == VerificationStatus.PROVEN
        assert results[0].contract_type == "invariant"
        assert results[0].function_name == "PositiveInt"

    def test_trivially_false_invariant(self):
        src = (
            "type Bad = Int\n"
            "  invariant false"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED

    def test_constant_invariant(self):
        src = (
            "type Money = Int\n"
            "  invariant 0 >= 0"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN

    def test_unproven_invariant(self):
        src = (
            "type Money = Int\n"
            "  invariant value >= 0"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.UNPROVEN


# -----------------------------------------------------------------------
# Full function verification
# -----------------------------------------------------------------------

class TestFullFunctionVerification:
    def test_nonneg_add(self):
        """Complete function with preconditions implying postcondition."""
        src = (
            "define add(x: Int, y: Int) -> Int\n"
            "  expect x >= 0\n"
            "  expect y >= 0\n"
            "  ensure x + y >= x\n"
            "  ensure x + y >= y\n"
            "given\n"
            "  x + y"
        )
        results = verify(src)
        posts = [r for r in results if r.contract_type == "postcondition"]
        assert len(posts) == 2
        assert all(p.status == VerificationStatus.PROVEN for p in posts)

    def test_mixed_results(self):
        """Some contracts provable, some not."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "  ensure x >= 0\n"
            "  ensure x > 10\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        posts = [r for r in results if r.contract_type == "postcondition"]
        statuses = {p.message: p.status for p in posts}
        proven = [p for p in posts if p.status == VerificationStatus.PROVEN]
        unproven = [p for p in posts if p.status == VerificationStatus.UNPROVEN]
        assert len(proven) == 1
        assert len(unproven) == 1

    def test_no_contracts(self):
        """Function without contracts produces no results."""
        src = (
            "define f(x: Int) -> Int\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert len(results) == 0

    def test_line_column_info(self):
        """Verification results carry line/column info."""
        src = (
            "define f(x: Int) -> Int\n"
            "  expect x >= 0\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert len(results) == 1
        assert results[0].line > 0
        assert results[0].column > 0
        assert results[0].function_name == "f"


# -----------------------------------------------------------------------
# Multiple declarations
# -----------------------------------------------------------------------

class TestMultipleDeclarations:
    def test_type_and_function(self):
        src = (
            "type Money = Int\n"
            "  invariant value >= 0\n"
            "\n"
            "define add(x: Int, y: Int) -> Int\n"
            "  expect x >= 0\n"
            "  expect y >= 0\n"
            "  ensure x + y >= x\n"
            "given\n"
            "  x + y"
        )
        results = verify(src)
        inv = [r for r in results if r.contract_type == "invariant"]
        pre = [r for r in results if r.contract_type == "precondition"]
        post = [r for r in results if r.contract_type == "postcondition"]
        assert len(inv) == 1
        assert len(pre) == 2
        assert len(post) == 1


# -----------------------------------------------------------------------
# Logical connective contracts
# -----------------------------------------------------------------------

class TestLogicalConnectives:
    def test_and_true_true(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect true && true\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN

    def test_and_true_false(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect true && false\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED

    def test_or_false_true(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect false || true\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN

    def test_or_false_false(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect false || false\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.VIOLATED

    def test_negation(self):
        src = (
            "define f(x: Int) -> Int\n"
            "  expect !false\n"
            "given\n"
            "  x"
        )
        results = verify(src)
        assert results[0].status == VerificationStatus.PROVEN
